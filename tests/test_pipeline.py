"""
Test script to verify JARVIS pipeline components
Run this to test the system without starting the full API server
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from src.bootstrap.system_scanner import scan_system
from src.planner.dev_planner import plan_project
from src.agents.code_agent import generate_code
from src.agents.test_agent import run_tests
from src.agents.build_agent import build_project
from src.agents.learn_agent import update_learning_memory
from src.memory.memory_store import memory_store, get_memory_stats


def test_system_scan():
    """Test system scanning"""
    print("\n=== Testing System Scan ===")
    try:
        profile = scan_system()
        compilers = profile.get("toolchain", {}).get("compilers", {})
        print(f"[OK] Found {len(compilers)} compiler(s)")
        for name, version in compilers.items():
            print(f"  - {name}: {version}")
        return True
    except Exception as e:
        print(f"[FAIL] System scan failed: {e}")
        return False


def test_planner():
    """Test project planning"""
    print("\n=== Testing Project Planner ===")
    try:
        requirements = "Build a REST API for a todo application"
        plan = plan_project(requirements)
        print(f"[OK] Plan created")
        print(f"  Architecture: {plan.get('architecture')}")
        print(f"  Language: {plan.get('language')}")
        print(f"  Framework: {plan.get('framework')}")
        return True
    except Exception as e:
        print(f"[FAIL] Planning failed: {e}")
        return False


def test_code_generation():
    """Test code generation (fallback mode)"""
    print("\n=== Testing Code Generation ===")
    try:
        plan = {
            "requirements": "Test API",
            "language": "python",
            "framework": "fastapi",
            "architecture": "monolithic"
        }
        files = generate_code(plan)
        print(f"[OK] Generated {len(files)} file(s)")
        for f in files[:3]:  # Show first 3
            print(f"  - {f.get('name', 'unknown')}")
        return True, files
    except Exception as e:
        print(f"[FAIL] Code generation failed: {e}")
        return False, []


def test_build():
    """Test build process"""
    print("\n=== Testing Build Process ===")
    try:
        files = [
            {"name": "main.py", "path": "main.py", "content": "print('hello')"},
            {"name": "requirements.txt", "path": "requirements.txt", "content": ""}
        ]
        result = build_project(files)
        print(f"[OK] Build completed")
        print(f"  Success: {result.get('success')}")
        print(f"  Build time: {result.get('build_time', 0):.2f}s")
        return True
    except Exception as e:
        print(f"[FAIL] Build failed: {e}")
        return False


def test_memory():
    """Test memory storage"""
    print("\n=== Testing Memory System ===")
    try:
        stats = get_memory_stats()
        print(f"[OK] Memory stats retrieved")
        print(f"  Stats: {stats}")
        return True
    except Exception as e:
        print(f"[FAIL] Memory test failed: {e}")
        return False


def test_full_pipeline():
    """Test a simplified pipeline without LLM"""
    print("\n=== Testing Full Pipeline (Fallback Mode) ===")
    
    memory = {
        "bug_patterns": [],
        "architecture_graph": [],
        "algorithm_library": [],
        "meta_learning_index": []
    }
    
    try:
        # Plan
        plan = plan_project("Build a simple REST API")
        print(f"[OK] Planning: {plan['language']}/{plan['framework']}")
        
        # Generate code (will use fallback)
        files = generate_code(plan)
        print(f"[OK] Code generation: {len(files)} files")
        
        # Build
        build_result = build_project(files)
        print(f"[OK] Build: {'success' if build_result['success'] else 'failed'}")
        
        # Update memory
        memory = update_learning_memory(
            memory, plan,
            {"passed": True, "logs": "", "coverage": 80},
            build_result,
            {"latency": "50ms", "throughput": "100 req/s"}
        )
        print(f"[OK] Memory updated")
        
        return True
    except Exception as e:
        print(f"[FAIL] Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("JARVIS Pipeline Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("System Scan", test_system_scan()))
    results.append(("Planner", test_planner()))
    results.append(("Code Generation", test_code_generation()[0]))
    results.append(("Build", test_build()))
    results.append(("Memory", test_memory()))
    results.append(("Full Pipeline", test_full_pipeline()))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\nAll tests passed! JARVIS is ready.")
        print("\nNext steps:")
        print("1. Run: python -m uvicorn src.main:app --reload")
        print("2. Open http://localhost:8000/docs")
    else:
        print("\nSome tests failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
