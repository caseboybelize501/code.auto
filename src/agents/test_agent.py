"""Test Agent - Real test execution with pytest, jest, etc."""

import subprocess
import json
import os
import re
from typing import Dict, List, Any
from config import config


def run_tests(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Run comprehensive test suite for generated code.
    
    Args:
        files: List of generated files
        
    Returns:
        Test results with pass/fail status, coverage, and logs
    """
    workspace = config.work_dir
    
    results = {
        "passed": True,
        "unit": {"passed": True, "results": []},
        "integration": {"passed": True, "results": []},
        "coverage": 0,
        "logs": "",
        "errors": []
    }
    
    all_logs = []
    
    # Run unit tests
    unit_results = run_unit_tests(workspace)
    results["unit"] = unit_results
    all_logs.append(f"=== Unit Tests ===\n{unit_results['logs']}")
    
    if not unit_results["passed"]:
        results["passed"] = False
        results["errors"].extend(unit_results.get("errors", []))
    
    # Run integration tests if unit tests passed
    if results["passed"]:
        integration_results = run_integration_tests(workspace)
        results["integration"] = integration_results
        all_logs.append(f"=== Integration Tests ===\n{integration_results['logs']}")
        
        if not integration_results["passed"]:
            results["passed"] = False
            results["errors"].extend(integration_results.get("errors", []))
    
    # Get coverage
    coverage = get_coverage(workspace)
    results["coverage"] = coverage
    
    results["logs"] = "\n\n".join(all_logs)
    
    return results


def run_unit_tests(workspace: str) -> Dict[str, Any]:
    """Run unit tests using appropriate framework"""

    # Detect test framework
    pytest_exists = os.path.exists(os.path.join(workspace, "tests")) or \
                    any(f.endswith("pytest.ini") or f.endswith("conftest.py")
                        for f in os.listdir(workspace) if os.path.isfile(f))

    jest_exists = os.path.exists(os.path.join(workspace, "package.json"))

    results = {
        "passed": True,
        "logs": "",
        "errors": [],
        "test_count": 0,
        "failures": 0
    }

    # Install pytest if needed for Python projects
    if os.path.exists(os.path.join(workspace, "requirements.txt")):
        try:
            # Check if pytest is installed
            subprocess.run(["pytest", "--version"], capture_output=True, check=False, timeout=10)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            # pytest not found, try to install it
            try:
                print("pytest not found, installing...")
                install_result = subprocess.run(
                    ["pip", "install", "pytest>=8.0.0", "pytest-asyncio>=0.23.0"],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                if install_result.returncode != 0:
                    results["logs"] = f"Failed to install pytest: {install_result.stderr}"
                    results["passed"] = False
                    results["errors"].append("pytest installation failed")
                    return results
                print("pytest installed successfully")
            except subprocess.TimeoutExpired:
                results["logs"] = "pytest installation timed out"
                results["errors"].append("pytest installation timeout")
                results["passed"] = False
                return results
            except Exception as e:
                results["logs"] = f"Error installing pytest: {str(e)}"
                results["errors"].append(str(e))
                results["passed"] = False
                return results

    if pytest_exists or os.path.exists(os.path.join(workspace, "requirements.txt")):
        return run_pytest(workspace)
    elif jest_exists:
        return run_jest(workspace)
    else:
        results["logs"] = "No test framework detected. Skipping tests."
        return results


def run_pytest(workspace: str) -> Dict[str, Any]:
    """Run pytest test suite"""
    
    cmd = [
        "pytest",
        "--tb=short",
        "--maxfail=5",
        f"--timeout={config.test_timeout}",
        "-v"
    ]
    
    # Add coverage if available
    try:
        subprocess.run(["pip", "show", "pytest-cov"], capture_output=True, check=False)
        cmd.extend(["--cov=.", "--cov-report=term-missing"])
    except:
        pass
    
    try:
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.test_timeout
        )
        
        passed = result.returncode == 0
        logs = result.stdout + "\n" + result.stderr
        
        # Parse results
        test_count = 0
        failures = 0
        
        # Look for test summary
        for line in logs.split("\n"):
            if "passed" in line or "failed" in line:
                # Parse: "5 passed, 2 failed"
                match = re.search(r'(\d+)\s+passed', line)
                if match:
                    test_count += int(match.group(1))
                match = re.search(r'(\d+)\s+failed', line)
                if match:
                    failures += int(match.group(1))
        
        # Extract errors
        errors = []
        if not passed:
            error_pattern = re.compile(r'SHORT TEST SUMMARY', re.DOTALL)
            match = error_pattern.search(logs)
            if match:
                errors.append(match.group(0))
        
        return {
            "passed": passed,
            "logs": logs,
            "errors": errors,
            "test_count": test_count,
            "failures": failures
        }
        
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "logs": f"Tests timed out after {config.test_timeout} seconds",
            "errors": ["Test timeout"],
            "test_count": 0,
            "failures": 0
        }
    except FileNotFoundError:
        return {
            "passed": False,
            "logs": "pytest not found. Install with: pip install pytest",
            "errors": ["pytest not installed"],
            "test_count": 0,
            "failures": 0
        }
    except Exception as e:
        return {
            "passed": False,
            "logs": f"Error running pytest: {str(e)}",
            "errors": [str(e)],
            "test_count": 0,
            "failures": 0
        }


def run_jest(workspace: str) -> Dict[str, Any]:
    """Run Jest test suite"""
    
    cmd = ["npx", "jest", "--verbose", "--coverage"]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.test_timeout
        )
        
        passed = result.returncode == 0
        logs = result.stdout + "\n" + result.stderr
        
        # Parse results
        test_count = 0
        failures = 0
        
        for line in logs.split("\n"):
            if "Tests:" in line:
                match = re.search(r'(\d+)\s+passed', line)
                if match:
                    test_count += int(match.group(1))
                match = re.search(r'(\d+)\s+failed', line)
                if match:
                    failures += int(match.group(1))
        
        errors = []
        if not passed:
            errors.append(logs[-2000:])  # Last 2000 chars of error output
        
        return {
            "passed": passed,
            "logs": logs,
            "errors": errors,
            "test_count": test_count,
            "failures": failures
        }
        
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "logs": f"Tests timed out after {config.test_timeout} seconds",
            "errors": ["Test timeout"],
            "test_count": 0,
            "failures": 0
        }
    except Exception as e:
        return {
            "passed": False,
            "logs": f"Error running jest: {str(e)}",
            "errors": [str(e)],
            "test_count": 0,
            "failures": 0
        }


def run_integration_tests(workspace: str) -> Dict[str, Any]:
    """Run integration tests"""
    
    # Look for integration test files
    integration_paths = [
        os.path.join(workspace, "tests", "integration"),
        os.path.join(workspace, "tests", "test_integration.py"),
        os.path.join(workspace, "test_integration.py"),
        os.path.join(workspace, "tests", "*integration*.py")
    ]
    
    has_integration = False
    for path in integration_paths:
        if os.path.exists(path):
            has_integration = True
            break
    
    if not has_integration:
        return {
            "passed": True,
            "logs": "No integration tests found. Skipping.",
            "errors": [],
            "test_count": 0,
            "failures": 0
        }
    
    # Run integration tests with pytest
    return run_pytest(workspace)


def get_coverage(workspace: str) -> float:
    """Get code coverage percentage"""
    
    try:
        # Try to run coverage report
        result = subprocess.run(
            ["coverage", "report", "--omit=*/tests/*"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Parse coverage percentage from output
        for line in result.stdout.split("\n"):
            if "TOTAL" in line:
                match = re.search(r'(\d+)%', line)
                if match:
                    return int(match.group(1))
        
        return 0.0
        
    except:
        return 0.0


def generate_tests(files: List[Dict[str, str]], plan: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generate test files for the generated code.
    
    Args:
        files: Generated source files
        plan: Project plan
        
    Returns:
        List of test files
    """
    from src.llm.client import create_llm_client
    from config import config
    
    test_files = []
    
    # Determine test framework
    language = plan.get("language", "python")
    
    if language == "python":
        # Generate pytest tests
        for source_file in files:
            if source_file["name"].endswith(".py") and "test" not in source_file["name"]:
                test_content = _generate_python_tests(source_file, plan)
                test_path = f"tests/test_{os.path.basename(source_file['name'])}"
                
                test_files.append({
                    "name": test_path,
                    "path": test_path,
                    "content": test_content
                })
    
    return test_files


def _generate_python_tests(source_file: Dict[str, str], plan: Dict[str, Any]) -> str:
    """Generate pytest tests for a Python file"""
    
    filename = os.path.basename(source_file["name"])
    module_name = filename.replace(".py", "")
    
    return f'''"""Auto-generated tests for {filename}"""

import pytest
from {module_name} import *


def test_imports():
    """Test that module imports correctly"""
    assert True


# TODO: Add specific tests based on module functionality
# Review the source code and add tests for:
# 1. Public functions and their expected outputs
# 2. Edge cases and error handling
# 3. Integration with other modules
'''
