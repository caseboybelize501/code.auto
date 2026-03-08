#!/usr/bin/env python3
"""
Sandbox CLI - Run sandbox server, validate code, or benchmark

Usage:
    python run_sandbox.py serve       # Start FastAPI server on port 7332
    python run_sandbox.py validate    # Validate code pairs from JSONL file
    python run_sandbox.py benchmark   # Run throughput benchmark
"""

import argparse
import asyncio
import json
import sys
import os
import time
from pathlib import Path

# Add sandbox to path
sandbox_path = Path(__file__).parent.parent
sys.path.insert(0, str(sandbox_path))

from engine.sandbox.topology_builder import TopologyBuilder
from engine.sandbox.runtime_pool import get_runtime_pool
from engine.executor.code_executor import get_executor, execute_code
from engine.validator.llm_code_validator import get_validator


async def cmd_serve():
    """Start FastAPI server"""
    import uvicorn
    from server import app
    
    print("Starting sandbox server on http://0.0.0.0:7332")
    print("Endpoints:")
    print("  POST /execute   - Execute code in sandbox")
    print("  POST /validate  - Validate LLM-generated code")
    print("  GET  /stats     - Get statistics")
    print("  GET  /topology  - Get sandbox topology")
    print()
    
    # Use uvicorn's asyncio-compatible run
    config = uvicorn.Config(app, host="0.0.0.0", port=7332, loop="asyncio")
    server = uvicorn.Server(config)
    await server.serve()


async def cmd_validate(input_file: str, output_dir: str):
    """Validate code pairs from JSONL file"""
    
    # Load input pairs
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_file}")
        return
    
    pairs = []
    with open(input_path, "r") as f:
        for line in f:
            if line.strip():
                pairs.append(json.loads(line))
    
    print(f"Loaded {len(pairs)} code pairs from {input_file}")
    
    # Initialize validator
    validator = await get_validator()
    
    # Run validation
    results = await validator.validate_batch(pairs, output_dir)
    
    # Print summary
    passed = sum(1 for r in results if r.result.value == "PASS")
    print(f"\nValidation complete:")
    print(f"  Passed: {passed}/{len(results)}")
    print(f"  Failed: {len(results) - passed}/{len(results)}")
    print(f"  Pass rate: {passed/len(results)*100:.1f}%")


async def cmd_benchmark():
    """Run throughput benchmark - 320 tasks (10 per slot)"""
    
    print("=" * 60)
    print("SANDBOX THROUGHPUT BENCHMARK")
    print("=" * 60)
    print("Tasks: 320 (10 per slot)")
    print("Expected: ~32 concurrent executions")
    print()
    
    # Initialize executor
    executor = await get_executor()
    
    # Test code (simple Python)
    test_code = "print(sum(range(1000)))"
    
    # Create 320 tasks
    tasks = []
    for i in range(320):
        tasks.append(executor.execute(test_code, "python", timeout=10))
    
    # Run all tasks concurrently
    print("Starting benchmark...")
    start_time = time.time()
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    elapsed = time.time() - start_time
    
    # Analyze results
    successful = sum(1 for r in results if isinstance(r, object) and hasattr(r, 'exit_code') and r.exit_code == 0)
    failed = len(results) - successful
    
    # Calculate metrics
    throughput = len(results) / elapsed
    avg_runtime = sum(r.runtime_ms for r in results if hasattr(r, 'runtime_ms')) / len(results)
    
    print()
    print("=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)
    print(f"Total tasks:     {len(results)}")
    print(f"Successful:      {successful}")
    print(f"Failed:          {failed}")
    print(f"Total time:      {elapsed:.2f}s")
    print(f"Throughput:      {throughput:.1f} tasks/sec")
    print(f"Avg runtime:     {avg_runtime:.1f}ms")
    print(f"Concurrency:     ~32 slots")
    print("=" * 60)
    
    # Get pool stats
    pool = await get_runtime_pool()
    print("\nPool stats:", pool.get_stats())


async def cmd_init():
    """Initialize sandbox topology"""
    builder = TopologyBuilder()
    topology = builder.build_and_save()
    
    print("\nSandbox initialized!")
    print(f"  Isolation: {topology['isolation_method']}")
    print(f"  Slots: {len(topology['slots'])}")
    print(f"  Runtimes: {', '.join(topology['available_runtimes'].keys())}")


def main():
    parser = argparse.ArgumentParser(
        description="Concurrent Sandbox CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_sandbox.py serve
  python run_sandbox.py validate --input pairs.jsonl
  python run_sandbox.py benchmark
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start FastAPI server")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate code pairs")
    validate_parser.add_argument("--input", "-i", required=True, help="Input JSONL file")
    validate_parser.add_argument("--output", "-o", default="results", help="Output directory")
    
    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Run throughput benchmark")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize sandbox topology")
    
    args = parser.parse_args()
    
    if args.command == "serve":
        asyncio.run(cmd_serve())
    elif args.command == "validate":
        asyncio.run(cmd_validate(args.input, args.output))
    elif args.command == "benchmark":
        asyncio.run(cmd_benchmark())
    elif args.command == "init":
        asyncio.run(cmd_init())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
