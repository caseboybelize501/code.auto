"""
Phase 1: Sandbox Topology Builder

Detects available isolation method and creates 32 sandbox slot configs.
Isolation priority: docker (rootless) > bubblewrap > subprocess (fallback)
"""

import json
import os
import subprocess
import shutil
from typing import Dict, List, Any, Optional
from pathlib import Path


class TopologyBuilder:
    """Builds sandbox topology configuration for 32 parallel execution slots"""
    
    def __init__(self, config_path: str = "config/sandbox_topology.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.sandbox_count = self.config.get("sandbox_count", 32)
        self.ram_per_sandbox_mb = self.config.get("ram_per_sandbox_mb", 2048)
        self.nvme_drives = self.config.get("nvme_drives", 4)
        self.sandboxes_per_drive = self.config.get("sandboxes_per_drive", 8)
        
    def _load_config(self) -> Dict:
        """Load base configuration"""
        if self.config_path.exists():
            with open(self.config_path, "r") as f:
                return json.load(f)
        return {}
    
    def detect_isolation_method(self) -> str:
        """
        Detect available isolation method.
        Priority: docker (rootless) > bubblewrap > subprocess
        """
        # Check for Docker (rootless)
        if self._check_docker():
            return "docker"
        
        # Check for bubblewrap
        if self._check_bubblewrap():
            return "bubblewrap"
        
        # Fallback to subprocess
        print("Warning: No containerization available. Using subprocess isolation.")
        return "subprocess"
    
    def _check_docker(self) -> bool:
        """Check if rootless Docker is available"""
        try:
            # Check docker command
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode != 0:
                return False
            
            # Check if docker works without sudo
            result = subprocess.run(
                ["docker", "run", "--rm", "hello-world"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
            
        except Exception:
            return False
    
    def _check_bubblewrap(self) -> bool:
        """Check if bubblewrap is available"""
        try:
            result = subprocess.run(
                ["bwrap", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def detect_nvme_drives(self) -> List[str]:
        """Detect available NVMe drives for temp directory distribution"""
        nvme_paths = []
        
        # Common NVMe mount points
        potential_drives = [
            "/nvme0", "/nvme1", "/nvme2", "/nvme3",
            "/mnt/nvme0", "/mnt/nvme1", "/mnt/nvme2", "/mnt/nvme3",
            "/tmp", "/var/tmp"  # Fallbacks
        ]
        
        for drive in potential_drives:
            if os.path.exists(drive) and os.path.isdir(drive):
                # Check if writable
                test_file = Path(drive) / ".write_test"
                try:
                    test_file.touch()
                    test_file.unlink()
                    nvme_paths.append(drive)
                    if len(nvme_paths) >= self.nvme_drives:
                        break
                except:
                    continue
        
        # Ensure at least one drive
        if not nvme_paths:
            nvme_paths = ["/tmp"]
        
        return nvme_paths[:self.nvme_drives]
    
    def detect_available_runtimes(self) -> Dict[str, str]:
        """Detect available programming language runtimes"""
        runtimes = {}
        
        runtime_checks = {
            "python": ["python3", "--version"],
            "python3": ["python3", "--version"],
            "node": ["node", "--version"],
            "deno": ["deno", "--version"],
            "bash": ["bash", "--version"],
            "go": ["go", "version"],
            "rust": ["rustc", "--version"],
            "g++": ["g++", "--version"],
            "gcc": ["gcc", "--version"],
        }
        
        for name, cmd in runtime_checks.items():
            try:
                result = subprocess.run(
                    ["which" if os.name != "nt" else "where", cmd[0]],
                capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    # Get version
                    version_result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    version = version_result.stdout.split("\n")[0].strip()
                    runtimes[name] = version
            except Exception:
                continue
        
        return runtimes
    
    def build_topology(self) -> Dict[str, Any]:
        """Build complete sandbox topology"""
        isolation_method = self.detect_isolation_method()
        nvme_drives = self.detect_nvme_drives()
        available_runtimes = self.detect_available_runtimes()
        
        # Get CPU info
        cpu_count = os.cpu_count() or 32
        
        # Create sandbox slots
        slots = []
        for i in range(self.sandbox_count):
            # CPU pinning - round-robin across logical cores
            cpu_core = i % cpu_count
            
            # NVMe drive assignment - round-robin across drives
            drive_index = i % len(nvme_drives)
            nvme_drive = nvme_drives[drive_index]
            
            # Temp directory for this slot
            temp_dir = f"{nvme_drive}/tmp/sandbox_slot_{i}"
            
            slot_config = {
                "slot_id": i,
                "cpu_core": cpu_core,
                "cpu_pin_command": f"taskset -c {cpu_core}",
                "ram_limit_mb": self.ram_per_sandbox_mb,
                "ram_limit_bytes": self.ram_per_sandbox_mb * 1024 * 1024,
                "temp_dir": temp_dir,
                "nvme_drive": nvme_drive,
                "network_disabled": True,
                "isolation": isolation_method,
                "status": "initialized"
            }
            
            # Add isolation-specific config
            if isolation_method == "docker":
                slot_config["docker_config"] = {
                    "memory": f"{self.ram_per_sandbox_mb}m",
                    "memory_swap": f"{self.ram_per_sandbox_mb}m",
                    "network": "none",
                    "cpuset_cpus": str(cpu_core),
                    "read_only": True,
                    "tmpfs": {
                        "/tmp": f"size={self.ram_per_sandbox_mb}m"
                    }
                }
            elif isolation_method == "bubblewrap":
                slot_config["bubblewrap_config"] = {
                    "unshare-all": True,
                    "share-network": False,
                    "bind-ro": ["/usr", "/etc"],
                    "tmpfs": ["/tmp", f"size={self.ram_per_sandbox_mb}m"],
                    "die-with-parent": True
                }
            
            slots.append(slot_config)
        
        # Create topology document
        topology = {
            "hardware": self.config.get("hardware", {}),
            "isolation_method": isolation_method,
            "nvme_drives": nvme_drives,
            "available_runtimes": available_runtimes,
            "cpu_cores": cpu_count,
            "sandbox_count": self.sandbox_count,
            "slots": slots,
            "created_at": subprocess.run(
                ["date", "-Iseconds"],
                capture_output=True,
                text=True
            ).stdout.strip() if os.name != "nt" else "N/A"
        }
        
        return topology
    
    def create_temp_directories(self, slots: List[Dict]) -> None:
        """Create temp directories for all sandbox slots"""
        for slot in slots:
            temp_dir = slot["temp_dir"]
            try:
                Path(temp_dir).mkdir(parents=True, exist_ok=True)
                # Create subdirectories for different file types
                (Path(temp_dir) / "src").mkdir(exist_ok=True)
                (Path(temp_dir) / "out").mkdir(exist_ok=True)
                (Path(temp_dir) / "cache").mkdir(exist_ok=True)
                slot["status"] = "ready"
            except Exception as e:
                print(f"Failed to create temp dir {temp_dir}: {e}")
                slot["status"] = "error"
    
    def save_topology(self, topology: Dict) -> str:
        """Save topology to config file"""
        output_path = self.config_path.parent / "sandbox_topology.json"
        with open(output_path, "w") as f:
            json.dump(topology, f, indent=2)
        return str(output_path)
    
    def build_and_save(self) -> Dict:
        """Build complete topology and save"""
        print("Building sandbox topology...")
        print(f"  Sandboxes: {self.sandbox_count}")
        print(f"  RAM per sandbox: {self.ram_per_sandbox_mb}MB")
        print(f"  Total RAM budget: {self.sandbox_count * self.ram_per_sandbox_mb / 1024:.1f}GB")
        
        topology = self.build_topology()
        
        print(f"\nIsolation method: {topology['isolation_method']}")
        print(f"NVMe drives: {topology['nvme_drives']}")
        print(f"Available runtimes: {', '.join(topology['available_runtimes'].keys())}")
        
        # Create temp directories
        print("\nCreating sandbox directories...")
        self.create_temp_directories(topology["slots"])
        
        # Save topology
        output_path = self.save_topology(topology)
        print(f"\nTopology saved to: {output_path}")
        
        ready_count = sum(1 for s in topology["slots"] if s["status"] == "ready")
        print(f"Ready sandboxes: {ready_count}/{self.sandbox_count}")
        
        return topology


def main():
    """Main entry point"""
    builder = TopologyBuilder()
    topology = builder.build_and_save()
    
    # Print summary
    print("\n" + "=" * 60)
    print("SANDBOX TOPOLOGY SUMMARY")
    print("=" * 60)
    print(f"Isolation:      {topology['isolation_method']}")
    print(f"CPU Cores:      {topology['cpu_cores']}")
    print(f"Sandbox Slots:  {len(topology['slots'])}")
    print(f"NVMe Drives:    {len(topology['nvme_drives'])}")
    print(f"Runtimes:       {', '.join(topology['available_runtimes'].keys())}")
    print("=" * 60)
    
    return topology


if __name__ == "__main__":
    main()
