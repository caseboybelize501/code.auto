import asyncio
import sys
from pathlib import Path

# Add sandbox to path
sandbox_path = Path(__file__).parent.parent
sys.path.insert(0, str(sandbox_path))

from engine.executor.code_executor import execute_code
from engine.sandbox.runtime_pool import get_runtime_pool

async def test():
    print("Testing Python execution...")
    result = await execute_code('print("Hello from sandbox!")', 'python', timeout=5)
    print(f"stdout: {result.stdout.strip()}")
    print(f"exit_code: {result.exit_code}")
    print(f"runtime_ms: {result.runtime_ms:.1f}")
    
    print("\nTesting Node.js execution...")
    result = await execute_code('console.log("Hello from Node!")', 'node', timeout=5)
    print(f"stdout: {result.stdout.strip()}")
    print(f"exit_code: {result.exit_code}")
    
    print("\nTesting math...")
    result = await execute_code('print(sum(range(100)))', 'python', timeout=5)
    print(f"stdout: {result.stdout.strip()}")
    
    pool = await get_runtime_pool()
    print(f"\nPool stats: {pool.get_stats()}")

asyncio.run(test())
