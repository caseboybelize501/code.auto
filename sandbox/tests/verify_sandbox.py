"""
Sandbox Self-Verification Test Suite

Tests the sandbox's ability to execute code across all supported languages
and verify the 32-slot concurrent execution capability.
"""

import asyncio
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add sandbox to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.executor.code_executor import get_executor, execute_code
from engine.validator.llm_code_validator import get_validator, validate_code
from engine.sandbox.runtime_pool import get_runtime_pool


# ============================================================================
# Test Cases by Language
# ============================================================================

import sys

TEST_CASES = {
    "python": [
        {
            "name": "hello_world",
            "code": "print('Hello from Python sandbox!')",
            "expected": "Hello from Python sandbox!",
            "timeout": 5
        },
        {
            "name": "math_operations",
            "code": "print(sum(range(1000)))",
            "expected": "499500",
            "timeout": 5
        },
        {
            "name": "list_comprehension",
            "code": "print([x**2 for x in range(10)])",
            "expected": "[0, 1, 4, 9, 16, 25, 36, 49, 64, 81]",
            "timeout": 5
        },
        {
            "name": "fibonacci",
            "code": """
def fib(n):
    if n <= 1:
        return n
    return fib(n-1) + fib(n-2)

print([fib(i) for i in range(10)])
""",
            "expected": "[0, 1, 1, 2, 3, 5, 8, 13, 21, 34]",
            "timeout": 10
        },
        {
            "name": "timeout_test",
            "code": "import time\nwhile True: time.sleep(0.1)",
            "should_timeout": True,
            "timeout": 2
        }
    ],
    
    "node": [
        {
            "name": "hello_world",
            "code": "console.log('Hello from Node.js sandbox!')",
            "expected": "Hello from Node.js sandbox!",
            "timeout": 5
        },
        {
            "name": "array_operations",
            "code": "console.log([1,2,3,4,5].map(x => x*2).join(','))",
            "expected": "2,4,6,8,10",
            "timeout": 5
        },
        {
            "name": "promise_test",
            "code": """
const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
async function test() {
    await delay(100);
    console.log('Promise resolved!');
}
test();
""",
            "expected": "Promise resolved!",
            "timeout": 5
        }
    ],
    
    "bash": [
        {
            "name": "hello_world",
            "code": "echo 'Hello from Bash sandbox!'",
            "expected": "Hello from Bash sandbox!",
            "timeout": 5,
            "wsl": True  # Use WSL on Windows
        },
        {
            "name": "loop_test",
            "code": "for i in 1 2 3 4 5; do echo $i; done",
            "expected": "1\n2\n3\n4\n5",
            "timeout": 5,
            "wsl": True
        }
    ]
}


# ============================================================================
# Test Runner
# ============================================================================

class SandboxTestRunner:
    """Runs comprehensive tests on the sandbox"""
    
    def __init__(self):
        self.executor = None
        self.validator = None
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "timeouts": 0,
            "errors": 0,
            "by_language": {},
            "details": []
        }
    
    async def initialize(self):
        """Initialize executor and validator"""
        print("Initializing sandbox test environment...")
        self.executor = await get_executor()
        self.validator = await get_validator()
        print("[OK] Sandbox initialized\n")
    
    async def run_single_test(self, language: str, test: dict) -> dict:
        """Run a single test case"""
        test_name = f"{language}/{test['name']}"
        self.results["total"] += 1
        
        start_time = time.time()
        
        try:
            # Execute code
            result = await execute_code(
                code=test["code"],
                language=language,
                timeout=test.get("timeout", 10)
            )
            
            elapsed = time.time() - start_time
            
            # Check result
            test_result = {
                "test": test_name,
                "elapsed_ms": elapsed * 1000,
                "runtime_ms": result.runtime_ms,
                "slot_id": result.slot_id,
                "exit_code": result.exit_code,
                "timed_out": result.timed_out
            }
            
            # Validate expected output
            if test.get("should_timeout"):
                if result.timed_out:
                    test_result["status"] = "PASS"
                    self.results["passed"] += 1
                    self.results["timeouts"] += 1
                else:
                    test_result["status"] = "FAIL"
                    test_result["reason"] = "Expected timeout but execution completed"
                    self.results["failed"] += 1
            
            elif result.exit_code == 0 and not result.timed_out:
                if "expected" in test:
                    if test["expected"] in result.stdout:
                        test_result["status"] = "PASS"
                        self.results["passed"] += 1
                    else:
                        test_result["status"] = "FAIL"
                        test_result["reason"] = f"Output mismatch. Expected: {test['expected']}, Got: {result.stdout.strip()}"
                        self.results["failed"] += 1
                else:
                    test_result["status"] = "PASS"
                    self.results["passed"] += 1
            else:
                test_result["status"] = "FAIL"
                test_result["reason"] = result.stderr or f"Exit code: {result.exit_code}"
                self.results["failed"] += 1
                if result.timed_out:
                    self.results["timeouts"] += 1
            
            # Track by language
            if language not in self.results["by_language"]:
                self.results["by_language"][language] = {"total": 0, "passed": 0}
            self.results["by_language"][language]["total"] += 1
            if test_result["status"] == "PASS":
                self.results["by_language"][language]["passed"] += 1
            
            self.results["details"].append(test_result)
            return test_result
            
        except Exception as e:
            elapsed = time.time() - start_time
            self.results["errors"] += 1
            self.results["failed"] += 1
            
            test_result = {
                "test": test_name,
                "status": "ERROR",
                "error": str(e),
                "elapsed_ms": elapsed * 1000
            }
            
            self.results["details"].append(test_result)
            return test_result
    
    async def run_all_tests(self):
        """Run all test cases"""
        print("=" * 70)
        print("SANDBOX CAPABILITY VERIFICATION")
        print("=" * 70)
        
        # Run tests by language
        for language, tests in TEST_CASES.items():
            print(f"\n[{language.upper()}] Running {len(tests)} tests...")
            
            for test in tests:
                result = await self.run_single_test(language, test)
                status_icon = "[PASS]" if result["status"] == "PASS" else "[FAIL]"
                print(f"  {status_icon} {test['name']} ({result.get('elapsed_ms', 0):.1f}ms)")
                
                if result["status"] == "FAIL" and "reason" in result:
                    print(f"      Reason: {result['reason'][:100]}")
                elif result["status"] == "ERROR":
                    print(f"      Error: {result.get('error', 'Unknown')[:100]}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("TEST SUMMARY")
        print("=" * 70)
        
        pass_rate = (self.results["passed"] / self.results["total"] * 100) if self.results["total"] > 0 else 0
        
        print(f"Total Tests:  {self.results['total']}")
        print(f"Passed:       {self.results['passed']} ({pass_rate:.1f}%)")
        print(f"Failed:       {self.results['failed']}")
        print(f"Timeouts:     {self.results['timeouts']}")
        print(f"Errors:       {self.results['errors']}")
        
        print("\nBy Language:")
        for lang, stats in self.results["by_language"].items():
            lang_pass_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {lang:10s}: {stats['passed']}/{stats['total']} ({lang_pass_rate:.1f}%)")
        
        # Save results
        results_file = Path(__file__).parent.parent / "results" / f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        results_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(results_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "results": self.results
            }, f, indent=2)
        
        print(f"\nResults saved to: {results_file}")
        print("=" * 70)
    
    async def run_concurrency_test(self, num_tasks: int = 320):
        """Test 32-slot concurrent execution"""
        print("\n" + "=" * 70)
        print(f"CONCURRENCY TEST: {num_tasks} tasks (32 slots × 10 iterations)")
        print("=" * 70)
        
        # Create test tasks
        test_code = "print(sum(range(1000)))"
        tasks = []
        
        for i in range(num_tasks):
            tasks.append(self.executor.execute(test_code, "python", timeout=10))
        
        print(f"Starting {num_tasks} concurrent executions...")
        start_time = time.time()
        
        # Run all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = time.time() - start_time
        
        # Analyze results
        successful = sum(1 for r in results if isinstance(r, object) and hasattr(r, 'exit_code') and r.exit_code == 0)
        failed = num_tasks - successful
        
        # Calculate metrics
        throughput = num_tasks / elapsed
        avg_runtime = sum(r.runtime_ms for r in results if hasattr(r, 'runtime_ms')) / len(results)
        
        # Get slot distribution
        slot_ids = [r.slot_id for r in results if hasattr(r, 'slot_id')]
        unique_slots = len(set(slot_ids))
        
        print(f"\nResults:")
        print(f"  Successful:    {successful}/{num_tasks}")
        print(f"  Failed:        {failed}")
        print(f"  Total time:    {elapsed:.2f}s")
        print(f"  Throughput:    {throughput:.1f} tasks/sec")
        print(f"  Avg runtime:   {avg_runtime:.1f}ms")
        print(f"  Slots used:    {unique_slots}/32")
        
        if throughput >= 30:
            print(f"\n[OK] CONCURRENCY TEST PASSED ({throughput:.1f} tasks/sec)")
        else:
            print(f"\n[FAIL] CONCURRENCY TEST FAILED (expected >=30 tasks/sec)")
        
        return {
            "total_tasks": num_tasks,
            "successful": successful,
            "failed": failed,
            "elapsed_seconds": elapsed,
            "throughput": throughput,
            "avg_runtime_ms": avg_runtime,
            "unique_slots": unique_slots
        }


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Main test runner"""
    runner = SandboxTestRunner()
    
    # Initialize
    await runner.initialize()
    
    # Run capability tests
    await runner.run_all_tests()
    
    # Run concurrency test
    await runner.run_concurrency_test(320)
    
    # Get final stats
    pool = await get_runtime_pool()
    print("\n" + "=" * 70)
    print("FINAL POOL STATISTICS")
    print("=" * 70)
    print(json.dumps(pool.get_stats(), indent=2))
    
    print("\n[OK] Sandbox verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
