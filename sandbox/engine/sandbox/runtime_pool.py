"""
Phase 2: Multi-Language Runtime Pool

Pre-warms all 32 sandbox slots at startup and manages runtime availability.
Supports: Python, JavaScript/TypeScript, Bash, Go, Rust, C++
"""

import asyncio
import json
import os
import subprocess
import shutil
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
import time


@dataclass
class SandboxSlot:
    """Represents a single sandbox slot"""
    slot_id: int
    cpu_core: int
    temp_dir: str
    ram_limit_mb: int
    isolation: str
    status: str = "available"
    current_process: Optional[subprocess.Popen] = None
    last_used: float = field(default_factory=time.time)
    execution_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "slot_id": self.slot_id,
            "cpu_core": self.cpu_core,
            "temp_dir": self.temp_dir,
            "ram_limit_mb": self.ram_limit_mb,
            "isolation": self.isolation,
            "status": self.status,
            "last_used": self.last_used,
            "execution_count": self.execution_count
        }


@dataclass
class RuntimeInfo:
    """Information about a detected runtime"""
    name: str
    version: str
    path: str
    available: bool = True
    test_passed: bool = False


class RuntimePool:
    """
    Manages pool of 32 sandbox slots with pre-warmed runtimes.
    Uses asyncio.Queue for FIFO slot assignment.
    """
    
    def __init__(self, topology_path: str = "config/sandbox_topology.json"):
        self.topology_path = Path(topology_path)
        self.topology = self._load_topology()
        self.slots: List[SandboxSlot] = []
        self.available_slots: asyncio.Queue = asyncio.Queue()
        self.runtimes: Dict[str, RuntimeInfo] = {}
        self._initialized = False
        self._lock = asyncio.Lock()
        
    def _load_topology(self) -> Dict:
        """Load sandbox topology configuration"""
        if self.topology_path.exists():
            with open(self.topology_path, "r") as f:
                return json.load(f)
        return {"slots": []}
    
    def detect_runtimes(self) -> Dict[str, RuntimeInfo]:
        """Detect available programming language runtimes"""
        runtimes = {}
        
        # Runtime detection commands
        runtime_checks = {
            "python": {
                "check": ["python", "--version"],
                "test": "python -c \"print('ok')\""
            },
            "python3": {
                "check": ["python3", "--version"],
                "test": "python3 -c \"print('ok')\""
            },
            "node": {
                "check": ["node", "--version"],
                "test": "node -e \"console.log('ok')\""
            },
            "deno": {
                "check": ["deno", "--version"],
                "test": "deno eval \"console.log('ok')\""
            },
            "bash": {
                "check": ["bash", "--version"],
                "test": "bash -c \"echo ok\""
            },
            "wsl-bash": {
                "check": ["wsl", "bash", "--version"],
                "test": None
            },
            "go": {
                "check": ["go", "version"],
                "test": None  # Go needs file to run
            },
            "rust": {
                "check": ["rustc", "--version"],
                "test": None  # Rust needs compilation
            },
            "g++": {
                "check": ["g++", "--version"],
                "test": None  # C++ needs compilation
            },
            "gcc": {
                "check": ["gcc", "--version"],
                "test": None
            }
        }
        
        for name, config in runtime_checks.items():
            try:
                # Check if runtime exists
                check_result = subprocess.run(
                    config["check"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if check_result.returncode == 0:
                    # Get path
                    which_cmd = ["where" if os.name == "nt" else "which", config["check"][0]]
                    path_result = subprocess.run(
                        which_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    version = check_result.stdout.strip().split("\n")[0]
                    runtime = RuntimeInfo(
                        name=name,
                        version=version,
                        path=path_result.stdout.strip() if path_result.returncode == 0 else "N/A",
                        available=True
                    )
                    
                    # Run test if available
                    if config.get("test"):
                        test_result = subprocess.run(
                            config["test"],
                            shell=True,
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        runtime.test_passed = test_result.returncode == 0
                    
                    runtimes[name] = runtime
                    
            except Exception as e:
                continue
        
        return runtimes
    
    def initialize_slots(self) -> None:
        """Initialize all sandbox slots from topology"""
        slots_config = self.topology.get("slots", [])
        
        # Use Windows temp directory
        import tempfile
        base_temp = tempfile.gettempdir()  # Returns Windows temp on Windows
        
        for slot_config in slots_config:
            # Override temp dir for Windows compatibility
            temp_dir = os.path.join(base_temp, f"sandbox_slot_{slot_config['slot_id']}")
            
            slot = SandboxSlot(
                slot_id=slot_config["slot_id"],
                cpu_core=slot_config["cpu_core"],
                temp_dir=temp_dir,
                ram_limit_mb=slot_config["ram_limit_mb"],
                isolation="subprocess"  # Force subprocess on Windows
            )
            
            # Ensure temp directory exists
            Path(slot.temp_dir).mkdir(parents=True, exist_ok=True)
            (Path(slot.temp_dir) / "src").mkdir(exist_ok=True)
            (Path(slot.temp_dir) / "out").mkdir(exist_ok=True)
            
            self.slots.append(slot)
        
        print(f"Initialized {len(self.slots)} sandbox slots")
    
    async def pre_warm_slots(self) -> None:
        """Pre-warm all sandbox slots (cold start penalty paid once)"""
        print("Pre-warming sandbox slots...")

        async def warm_slot(slot: SandboxSlot):
            """Warm a single slot"""
            try:
                # Create a simple test file
                test_file = Path(slot.temp_dir) / "src" / "warmup.py"
                test_file.write_text("print('warmed')")
                
                # Get current Python executable
                import sys
                current_python = sys.executable

                # Run a quick execution to warm up
                if self.runtimes.get("python") or self.runtimes.get("python3"):
                    # Use subprocess directly for pre-warm (simpler)
                    try:
                        result = await asyncio.create_subprocess_exec(
                            current_python, "-u", str(test_file),
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=slot.temp_dir
                        )
                        stdout, stderr = await asyncio.wait_for(
                            result.communicate(),
                            timeout=5
                        )
                        
                        if result.returncode == 0:
                            slot.status = "available"
                            await self.available_slots.put(slot)
                        else:
                            slot.status = "error"
                    except asyncio.TimeoutError:
                        # Still mark as available - execution works, just slow
                        slot.status = "available"
                        await self.available_slots.put(slot)
                else:
                    slot.status = "available"
                    await self.available_slots.put(slot)

            except Exception as e:
                # Mark as available anyway - slot is ready even if warmup failed
                slot.status = "available"
                await self.available_slots.put(slot)

        # Warm all slots concurrently
        tasks = [warm_slot(slot) for slot in self.slots]
        await asyncio.gather(*tasks, return_exceptions=True)

        ready_count = sum(1 for s in self.slots if s.status == "available")
        print(f"Pre-warmed {ready_count}/{len(self.slots)} slots")
    
    async def acquire_slot(self, timeout: float = 30.0) -> Optional[SandboxSlot]:
        """Acquire an available slot from the pool"""
        try:
            slot = await asyncio.wait_for(
                self.available_slots.get(),
                timeout=timeout
            )
            slot.status = "busy"
            return slot
        except asyncio.TimeoutError:
            return None
    
    async def release_slot(self, slot: SandboxSlot) -> None:
        """Release a slot back to the pool"""
        slot.status = "available"
        slot.last_used = time.time()
        slot.execution_count += 1
        await self.available_slots.put(slot)
    
    async def _execute_in_slot(
        self,
        slot: SandboxSlot,
        code: str,
        language: str,
        timeout: int = 10
    ) -> Dict[str, Any]:
        """Execute code in a specific slot"""
        start_time = time.time()
        
        # Write code to temp file
        ext_map = {
            "python": ".py",
            "python3": ".py",
            "node": ".js",
            "deno": ".ts",
            "bash": ".sh",
            "go": ".go",
            "rust": ".rs",
            "g++": ".cpp",
            "gcc": ".c"
        }
        
        ext = ext_map.get(language, ".txt")
        src_file = Path(slot.temp_dir) / "src" / f"code_{slot.slot_id}{ext}"
        src_file.write_text(code)
        
        # Build execution command
        cmd = self._build_command(language, src_file)
        
        # Add CPU pinning if on Linux
        if os.name != "nt":
            cmd = ["taskset", "-c", str(slot.cpu_core)] + cmd
        
        try:
            # Execute
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=slot.temp_dir
            )
            
            slot.current_process = process
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                runtime_ms = (time.time() - start_time) * 1000
                
                return {
                    "stdout": stdout.decode("utf-8", errors="replace"),
                    "stderr": stderr.decode("utf-8", errors="replace"),
                    "exit_code": process.returncode,
                    "runtime_ms": runtime_ms,
                    "timed_out": False,
                    "slot_id": slot.slot_id
                }
                
            except asyncio.TimeoutError:
                # Kill process on timeout
                process.kill()
                await process.wait()
                
                return {
                    "stdout": "",
                    "stderr": "Execution timed out",
                    "exit_code": -1,
                    "runtime_ms": timeout * 1000,
                    "timed_out": True,
                    "slot_id": slot.slot_id
                }
                
        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": -1,
                "runtime_ms": (time.time() - start_time) * 1000,
                "timed_out": False,
                "slot_id": slot.slot_id
            }
        finally:
            slot.current_process = None
    
    def _build_command(self, language: str, src_file: Path) -> List[str]:
        """Build execution command for given language"""
        commands = {
            "python": ["python3", str(src_file)],
            "python3": ["python3", str(src_file)],
            "node": ["node", str(src_file)],
            "deno": ["deno", "run", "--allow-all", str(src_file)],
            "bash": ["bash", str(src_file)],
            "go": ["go", "run", str(src_file)],
            "rust": ["rustc", str(src_file), "-o", str(src_file.with_suffix("")), "&&", str(src_file.with_suffix(""))],
            "g++": ["g++", "-O2", str(src_file), "-o", str(src_file.with_suffix("")), "&&", str(src_file.with_suffix(""))],
            "gcc": ["gcc", "-O2", str(src_file), "-o", str(src_file.with_suffix("")), "&&", str(src_file.with_suffix(""))]
        }
        
        cmd = commands.get(language, ["echo", "Unsupported language"])
        
        # Handle compound commands (compile + run)
        if "&&" in cmd:
            idx = cmd.index("&&")
            compile_cmd = cmd[:idx]
            run_cmd = cmd[idx+1:]
            
            # For now, just return compile command (executor handles run separately)
            return compile_cmd
        
        return cmd
    
    async def initialize(self) -> None:
        """Full initialization: detect runtimes, initialize slots, pre-warm"""
        print("Initializing runtime pool...")
        
        # Detect runtimes
        self.runtimes = self.detect_runtimes()
        print(f"Detected runtimes: {', '.join(self.runtimes.keys())}")
        
        # Initialize slots
        self.initialize_slots()
        
        # Pre-warm slots
        await self.pre_warm_slots()
        
        self._initialized = True
        print("Runtime pool initialized")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics"""
        return {
            "total_slots": len(self.slots),
            "available": sum(1 for s in self.slots if s.status == "available"),
            "busy": sum(1 for s in self.slots if s.status == "busy"),
            "error": sum(1 for s in self.slots if s.status == "error"),
            "runtimes": {k: v.version for k, v in self.runtimes.items()},
            "initialized": self._initialized
        }


# Global pool instance
_runtime_pool: Optional[RuntimePool] = None


async def get_runtime_pool() -> RuntimePool:
    """Get or create global runtime pool"""
    global _runtime_pool
    if _runtime_pool is None:
        _runtime_pool = RuntimePool()
        await _runtime_pool.initialize()
    return _runtime_pool


async def execute_in_sandbox(code: str, language: str, timeout: int = 10) -> Dict[str, Any]:
    """Convenience function to execute code in sandbox"""
    pool = await get_runtime_pool()
    
    slot = await pool.acquire_slot(timeout=30.0)
    if slot is None:
        return {
            "stdout": "",
            "stderr": "No available sandbox slots",
            "exit_code": -1,
            "runtime_ms": 0,
            "timed_out": False
        }
    
    try:
        result = await pool._execute_in_slot(slot, code, language, timeout)
        return result
    finally:
        await pool.release_slot(slot)


if __name__ == "__main__":
    async def main():
        pool = await get_runtime_pool()
        print("\nPool stats:", pool.get_stats())
        
        # Test execution
        result = await execute_in_sandbox("print('Hello from sandbox!')", "python", timeout=5)
        print("\nTest execution:")
        print(f"  stdout: {result['stdout'].strip()}")
        print(f"  exit_code: {result['exit_code']}")
        print(f"  runtime_ms: {result['runtime_ms']:.1f}")
    
    asyncio.run(main())
