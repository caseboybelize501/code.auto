"""
Phase 3: Execution Engine

High-performance code executor with resource monitoring and isolation.
"""

import asyncio
import os
import re
import subprocess
import sys
import time
import signal
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

# Try to import psutil for resource monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Import from sibling module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from sandbox.runtime_pool import get_runtime_pool, SandboxSlot


@dataclass
class ExecutionResult:
    """Result of code execution"""
    stdout: str = ""
    stderr: str = ""
    exit_code: int = -1
    runtime_ms: float = 0.0
    cpu_usage_pct: float = 0.0
    mem_peak_mb: float = 0.0
    timed_out: bool = False
    slot_id: int = -1
    language: str = ""
    code_hash: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "runtime_ms": self.runtime_ms,
            "cpu_usage_pct": self.cpu_usage_pct,
            "mem_peak_mb": self.mem_peak_mb,
            "timed_out": self.timed_out,
            "slot_id": self.slot_id,
            "language": self.language,
            "code_hash": self.code_hash
        }
    
    def is_success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


class CodeExecutor:
    """
    High-performance code executor with 32-slot concurrency.
    Features:
    - CPU pinning per slot
    - RAM limits enforcement
    - Resource usage monitoring
    - Timeout handling with hard kill
    - Output sanitization
    """
    
    MAX_OUTPUT_SIZE_KB = 64
    MAX_OUTPUT_BYTES = MAX_OUTPUT_SIZE_KB * 1024
    
    def __init__(self):
        self._pool = None
        self._execution_count = 0
        self._stats = {
            "total_executions": 0,
            "successful": 0,
            "failed": 0,
            "timeouts": 0,
            "total_runtime_ms": 0.0
        }
    
    async def initialize(self):
        """Initialize the executor"""
        self._pool = await get_runtime_pool()
    
    async def execute(
        self,
        code: str,
        language: str,
        stdin: str = "",
        timeout: int = 10,
        ram_limit_mb: int = 2048
    ) -> ExecutionResult:
        """
        Execute code in sandboxed environment.
        
        Args:
            code: Source code to execute
            language: Programming language (python, node, bash, go, rust, etc.)
            stdin: Standard input to provide
            timeout: Maximum execution time in seconds
            ram_limit_mb: RAM limit in megabytes
            
        Returns:
            ExecutionResult with stdout, stderr, metrics
        """
        start_time = time.time()
        self._execution_count += 1
        self._stats["total_executions"] += 1
        
        # Acquire sandbox slot
        slot = await self._pool.acquire_slot(timeout=30.0)
        if slot is None:
            return ExecutionResult(
                stderr="No available sandbox slots",
                exit_code=-1,
                runtime_ms=(time.time() - start_time) * 1000
            )
        
        try:
            result = await self._execute_in_slot(
                slot, code, language, stdin, timeout, ram_limit_mb
            )
            
            # Update stats
            if result.is_success():
                self._stats["successful"] += 1
            else:
                self._stats["failed"] += 1
            
            if result.timed_out:
                self._stats["timeouts"] += 1
            
            self._stats["total_runtime_ms"] += result.runtime_ms
            
            return result
            
        finally:
            await self._pool.release_slot(slot)
    
    async def _execute_in_slot(
        self,
        slot: SandboxSlot,
        code: str,
        language: str,
        stdin: str,
        timeout: int,
        ram_limit_mb: int
    ) -> ExecutionResult:
        """Execute code in a specific slot with resource monitoring"""
        
        import hashlib
        code_hash = hashlib.md5(code.encode()).hexdigest()[:8]
        
        # Write code to temp file
        ext_map = {
            "python": ".py", "python3": ".py",
            "node": ".js", "deno": ".ts",
            "bash": ".sh",
            "go": ".go",
            "rust": ".rs",
            "g++": ".cpp", "gcc": ".c"
        }
        ext = ext_map.get(language, ".txt")
        
        src_dir = Path(slot.temp_dir) / "src"
        src_dir.mkdir(parents=True, exist_ok=True)
        
        src_file = src_dir / f"exec_{slot.slot_id}_{code_hash}{ext}"
        src_file.write_text(code)
        
        # Build command
        cmd = self._build_command(language, src_file)
        if not cmd:
            return ExecutionResult(
                stderr=f"Unsupported language: {language}",
                exit_code=-1,
                language=language,
                code_hash=code_hash,
                slot_id=slot.slot_id
            )
        
        # Add CPU pinning (Linux only)
        if os.name != "nt":
            cmd = ["taskset", "-c", str(slot.cpu_core)] + cmd
        
        # Execute with resource monitoring
        start_time = time.time()
        cpu_samples: List[float] = []
        mem_samples: List[float] = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if stdin else None,
                cwd=slot.temp_dir
            )
            
            slot.current_process = process
            
            # Start resource monitoring
            monitor_task = asyncio.create_task(
                self._monitor_resources(process.pid, cpu_samples, mem_samples, ram_limit_mb)
            )
            
            try:
                stdin_bytes = stdin.encode() if stdin else None
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(input=stdin_bytes),
                    timeout=timeout
                )
                
                runtime_ms = (time.time() - start_time) * 1000
                
                # Cancel monitoring
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                
                # Sanitize output
                stdout_str = self._sanitize_output(stdout.decode("utf-8", errors="replace"))
                stderr_str = self._sanitize_output(stderr.decode("utf-8", errors="replace"))
                
                return ExecutionResult(
                    stdout=stdout_str,
                    stderr=stderr_str,
                    exit_code=process.returncode,
                    runtime_ms=runtime_ms,
                    cpu_usage_pct=sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
                    mem_peak_mb=max(mem_samples) if mem_samples else 0.0,
                    timed_out=False,
                    slot_id=slot.slot_id,
                    language=language,
                    code_hash=code_hash
                )
                
            except asyncio.TimeoutError:
                # Hard kill on timeout
                await self._kill_process_tree(process)
                
                runtime_ms = (time.time() - start_time) * 1000
                
                # Cancel monitoring
                monitor_task.cancel()
                try:
                    await monitor_task
                except asyncio.CancelledError:
                    pass
                
                return ExecutionResult(
                    stdout="",
                    stderr="Execution timed out",
                    exit_code=-1,
                    runtime_ms=runtime_ms,
                    cpu_usage_pct=sum(cpu_samples) / len(cpu_samples) if cpu_samples else 0.0,
                    mem_peak_mb=max(mem_samples) if mem_samples else 0.0,
                    timed_out=True,
                    slot_id=slot.slot_id,
                    language=language,
                    code_hash=code_hash
                )
                
        except Exception as e:
            return ExecutionResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                runtime_ms=(time.time() - start_time) * 1000,
                timed_out=False,
                slot_id=slot.slot_id,
                language=language,
                code_hash=code_hash
            )
        finally:
            slot.current_process = None
    
    def _build_command(self, language: str, src_file: Path) -> Optional[List[str]]:
        """Build execution command for given language"""
        
        # Get the current Python executable for child processes
        current_python = sys.executable
        
        # Convert Windows path to WSL path for bash execution
        def to_wsl_path(path: Path) -> str:
            if os.name == "nt":
                # Convert D:\path\to\file to /mnt/d/path/to/file
                win_path = str(path)
                # Get drive letter
                drive = win_path[0].lower()
                # Remove drive and backslashes, convert to forward slashes
                rest = win_path[3:].replace('\\', '/')
                return f"/mnt/{drive}/{rest}"
            return str(path)
        
        # Windows-compatible commands
        if os.name == "nt":
            commands = {
                "python": [current_python, "-u", str(src_file)],
                "python3": [current_python, "-u", str(src_file)],
                "node": ["node", str(src_file)],
                "deno": ["deno", "run", "--allow-all", str(src_file)],
                "bash": ["wsl", "bash", to_wsl_path(src_file)],  # Use WSL with converted path
                "go": ["go", "run", str(src_file)],
                "wsl-bash": ["wsl", "bash", to_wsl_path(src_file)]
            }
        else:
            commands = {
                "python": ["python3", "-u", str(src_file)],
                "python3": ["python3", "-u", str(src_file)],
                "node": ["node", str(src_file)],
                "deno": ["deno", "run", "--allow-all", str(src_file)],
                "bash": ["bash", str(src_file)],
                "go": ["go", "run", str(src_file)],
            }

        # Compiled languages need special handling
        if language in ["rust", "g++", "gcc"]:
            return self._build_compile_run_command(language, src_file)

        return commands.get(language)
    
    def _build_compile_run_command(
        self,
        language: str,
        src_file: Path
    ) -> List[str]:
        """Build compile + run command for compiled languages"""
        
        compilers = {
            "rust": ["rustc", "-O", "-o"],
            "g++": ["g++", "-O2", "-o"],
            "gcc": ["gcc", "-O2", "-o"]
        }
        
        compiler = compilers.get(language)
        if not compiler:
            return []
        
        binary_path = src_file.with_suffix("")
        compile_cmd = compiler + [str(binary_path), str(src_file)]
        
        # Return compile command (run happens after)
        # For simplicity, we'll compile and run in sequence
        return ["bash", "-c", f"{' '.join(compile_cmd)} && {binary_path}"]
    
    async def _monitor_resources(
        self,
        pid: int,
        cpu_samples: List[float],
        mem_samples: List[float],
        ram_limit_mb: int
    ):
        """Monitor CPU and memory usage of process"""
        if not HAS_PSUTIL:
            return
        
        try:
            process = psutil.Process(pid)
            
            while True:
                try:
                    # Get CPU usage
                    cpu = process.cpu_percent(interval=0.1)
                    cpu_samples.append(cpu)
                    
                    # Get memory usage
                    mem_mb = process.memory_info().rss / (1024 * 1024)
                    mem_samples.append(mem_mb)
                    
                    # Check RAM limit
                    if mem_mb > ram_limit_mb:
                        # Kill process if exceeds limit
                        process.kill()
                        break
                    
                    await asyncio.sleep(0.1)
                    
                except psutil.NoSuchProcess:
                    break
                    
        except Exception:
            pass
    
    async def _kill_process_tree(self, process: asyncio.subprocess.Process):
        """Kill process and all children"""
        try:
            if os.name != "nt":
                # Send SIGKILL to process group
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                process.kill()
            
            await process.wait()
        except Exception:
            pass
    
    def _sanitize_output(self, output: str) -> str:
        """Sanitize output: strip ANSI, truncate if too large"""
        # Strip ANSI escape codes
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]')
        output = ansi_pattern.sub('', output)
        
        # Truncate if too large
        if len(output.encode('utf-8')) > self.MAX_OUTPUT_BYTES:
            output = output[:self.MAX_OUTPUT_BYTES // 2] + "\n... [truncated]"
        
        return output
    
    def get_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        avg_runtime = (
            self._stats["total_runtime_ms"] / self._stats["total_executions"]
            if self._stats["total_executions"] > 0 else 0
        )
        
        return {
            **self._stats,
            "avg_runtime_ms": avg_runtime,
            "success_rate": (
                self._stats["successful"] / self._stats["total_executions"]
                if self._stats["total_executions"] > 0 else 0
            )
        }


# Global executor instance
_executor: Optional[CodeExecutor] = None


async def get_executor() -> CodeExecutor:
    """Get or create global executor"""
    global _executor
    if _executor is None:
        _executor = CodeExecutor()
        await _executor.initialize()
    return _executor


async def execute_code(
    code: str,
    language: str,
    stdin: str = "",
    timeout: int = 10
) -> ExecutionResult:
    """Convenience function for code execution"""
    executor = await get_executor()
    return await executor.execute(code, language, stdin, timeout)


if __name__ == "__main__":
    async def main():
        executor = await get_executor()
        
        # Test Python execution
        print("Testing Python execution...")
        result = await executor.execute(
            "print('Hello from sandbox!')\nprint(2 + 2)",
            "python",
            timeout=5
        )
        print(f"  stdout: {result.stdout.strip()}")
        print(f"  exit_code: {result.exit_code}")
        print(f"  runtime_ms: {result.runtime_ms:.1f}")
        print(f"  mem_peak_mb: {result.mem_peak_mb:.1f}")
        
        # Test timeout
        print("\nTesting timeout...")
        result = await executor.execute(
            "import time\nwhile True: time.sleep(0.1)",
            "python",
            timeout=2
        )
        print(f"  timed_out: {result.timed_out}")
        
        # Stats
        print("\nExecutor stats:", executor.get_stats())
    
    asyncio.run(main())
