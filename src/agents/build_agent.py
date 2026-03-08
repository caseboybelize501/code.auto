"""Build Agent - Actual build pipeline for multiple languages"""

import subprocess
import os
import json
import time
from typing import Dict, List, Any
from config import config


def build_project(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Run build/compilation pipeline for the generated project.
    
    Args:
        files: List of generated files
        
    Returns:
        Build results with success status, errors, warnings, and metrics
    """
    workspace = config.work_dir
    
    result = {
        "success": False,
        "compile_errors": [],
        "warnings": [],
        "build_time": 0.0,
        "size": "0MB",
        "artifacts": [],
        "logs": ""
    }
    
    start_time = time.time()
    
    try:
        # Detect project type and run appropriate build
        project_type = detect_project_type(workspace)
        
        if project_type == "python":
            build_result = build_python(workspace)
        elif project_type == "node":
            build_result = build_node(workspace)
        elif project_type == "rust":
            build_result = build_rust(workspace)
        elif project_type == "go":
            build_result = build_go(workspace)
        elif project_type == "java":
            build_result = build_java(workspace)
        else:
            build_result = {
                "success": True,
                "errors": [],
                "warnings": [],
                "logs": f"No build required for {project_type} project"
            }
        
        result.update(build_result)
        
    except Exception as e:
        result["compile_errors"].append(str(e))
        result["logs"] = f"Build failed: {str(e)}"
    
    result["build_time"] = time.time() - start_time
    
    # Calculate build size
    result["size"] = calculate_build_size(workspace)
    
    return result


def detect_project_type(workspace: str) -> str:
    """Detect project type from files"""
    
    if os.path.exists(os.path.join(workspace, "Cargo.toml")):
        return "rust"
    elif os.path.exists(os.path.join(workspace, "go.mod")):
        return "go"
    elif os.path.exists(os.path.join(workspace, "pom.xml")) or os.path.exists(os.path.join(workspace, "build.gradle")):
        return "java"
    elif os.path.exists(os.path.join(workspace, "package.json")):
        return "node"
    elif os.path.exists(os.path.join(workspace, "requirements.txt")) or \
         os.path.exists(os.path.join(workspace, "setup.py")) or \
         os.path.exists(os.path.join(workspace, "pyproject.toml")):
        return "python"
    else:
        # Check file extensions
        for root, dirs, files in os.walk(workspace):
            for f in files:
                if f.endswith(".py"):
                    return "python"
                elif f.endswith(".js") or f.endswith(".ts"):
                    return "node"
                elif f.endswith(".rs"):
                    return "rust"
                elif f.endswith(".go"):
                    return "go"
                elif f.endswith(".java"):
                    return "java"
    
    return "unknown"


def build_python(workspace: str) -> Dict[str, Any]:
    """Build Python project (install dependencies, validate syntax)"""

    result = {
        "success": True,
        "compile_errors": [],
        "warnings": [],
        "logs": ""
    }

    logs = []

    # Install dependencies
    if os.path.exists(os.path.join(workspace, "requirements.txt")):
        logs.append("=== Installing dependencies ===")
        try:
            cmd = ["pip", "install", "-r", "requirements.txt"]
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=config.build_timeout
            )
            logs.append(proc.stdout)
            if proc.returncode != 0:
                # Don't fail completely - just warn and continue
                result["warnings"].append(f"Dependency installation had issues: {proc.stderr[:500]}")
                logs.append(f"Warning: Some dependencies may not have installed. Continuing...")
                
                # Try to install key packages individually
                logs.append("\n=== Attempting to install key packages ===")
                key_packages = ["fastapi", "uvicorn", "pydantic"]
                for pkg in key_packages:
                    try:
                        proc_pkg = subprocess.run(
                            ["pip", "install", pkg],
                            capture_output=True,
                            text=True,
                            timeout=60
                        )
                        if proc_pkg.returncode == 0:
                            logs.append(f"  ✓ {pkg} installed")
                        else:
                            logs.append(f"  ✗ {pkg} failed: {proc_pkg.stderr[:200]}")
                    except:
                        logs.append(f"  ✗ {pkg} failed")
                        
        except subprocess.TimeoutExpired:
            result["warnings"].append("Dependency installation timed out - continuing anyway")
            logs.append("Warning: Installation timed out. Continuing with available packages...")
        except Exception as e:
            result["warnings"].append(f"Error installing dependencies: {str(e)}")
            logs.append(f"Warning: Installation error. Continuing...")

    # Validate Python syntax
    logs.append("\n=== Validating Python syntax ===")
    syntax_errors = validate_python_syntax(workspace)
    if syntax_errors:
        result["compile_errors"].extend(syntax_errors)
        logs.extend(syntax_errors)
        # Syntax errors are critical - fail the build
        result["success"] = False
    else:
        logs.append("All Python files have valid syntax")

    # Run mypy if available
    try:
        subprocess.run(["mypy", "--version"], capture_output=True, check=False)
        logs.append("\n=== Running type checking (mypy) ===")
        proc = subprocess.run(
            ["mypy", ".", "--ignore-missing-imports"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=60
        )
        logs.append(proc.stdout)
        if proc.stderr:
            logs.append(proc.stderr)
        if proc.returncode != 0 and "Success" not in proc.stdout:
            result["warnings"].append("Type checking found issues (non-blocking)")
    except:
        logs.append("\nNote: mypy not installed, skipping type checking")

    result["logs"] = "\n".join(logs)
    return result


def validate_python_syntax(workspace: str) -> List[str]:
    """Validate Python syntax for all .py files"""
    errors = []
    
    for root, dirs, files in os.walk(workspace):
        # Skip test directories for syntax validation
        if "test" in root or "__pycache__" in root:
            continue
            
        for f in files:
            if f.endswith(".py"):
                filepath = os.path.join(root, f)
                try:
                    with open(filepath, "r", encoding="utf-8") as file:
                        compile(file.read(), filepath, "exec")
                except SyntaxError as e:
                    errors.append(f"Syntax error in {f}: {e.msg} at line {e.lineno}")
                except Exception as e:
                    errors.append(f"Error reading {f}: {str(e)}")
    
    return errors


def build_node(workspace: str) -> Dict[str, Any]:
    """Build Node.js project"""
    
    result = {
        "success": True,
        "compile_errors": [],
        "warnings": [],
        "logs": ""
    }
    
    logs = []
    
    # Install dependencies
    logs.append("=== Installing npm dependencies ===")
    try:
        cmd = ["npm", "install"]
        proc = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        logs.append(proc.stdout)
        if proc.returncode != 0:
            result["success"] = False
            result["compile_errors"].append(f"npm install failed: {proc.stderr}")
    except subprocess.TimeoutExpired:
        result["success"] = False
        result["compile_errors"].append("npm install timed out")
    except Exception as e:
        result["success"] = False
        result["compile_errors"].append(f"Error installing dependencies: {str(e)}")
    
    # Run build script if defined
    if result["success"]:
        try:
            with open(os.path.join(workspace, "package.json"), "r") as f:
                package_json = json.load(f)
            
            if "scripts" in package_json and "build" in package_json["scripts"]:
                logs.append("\n=== Running build script ===")
                proc = subprocess.run(
                    ["npm", "run", "build"],
                    cwd=workspace,
                    capture_output=True,
                    text=True,
                    timeout=config.build_timeout
                )
                logs.append(proc.stdout)
                if proc.returncode != 0:
                    result["success"] = False
                    result["compile_errors"].append(f"Build script failed: {proc.stderr}")
        except Exception as e:
            result["success"] = False
            result["compile_errors"].append(f"Error running build: {str(e)}")
    
    result["logs"] = "\n".join(logs)
    return result


def build_rust(workspace: str) -> Dict[str, Any]:
    """Build Rust project with cargo"""
    
    result = {
        "success": True,
        "compile_errors": [],
        "warnings": [],
        "logs": ""
    }
    
    logs = []
    
    try:
        cmd = ["cargo", "build", "--release"]
        proc = subprocess.run(
            cmd,
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        logs.append(proc.stdout)
        
        if proc.returncode != 0:
            result["success"] = False
            result["compile_errors"].append(proc.stderr)
        elif "warning" in proc.stdout.lower():
            result["warnings"].append("Compilation warnings detected")
            
    except subprocess.TimeoutExpired:
        result["success"] = False
        result["compile_errors"].append("Cargo build timed out")
    except Exception as e:
        result["success"] = False
        result["compile_errors"].append(f"Error building Rust project: {str(e)}")
    
    result["logs"] = "\n".join(logs)
    return result


def build_go(workspace: str) -> Dict[str, Any]:
    """Build Go project"""
    
    result = {
        "success": True,
        "compile_errors": [],
        "warnings": [],
        "logs": ""
    }
    
    logs = []
    
    try:
        # Download dependencies
        logs.append("=== Downloading Go dependencies ===")
        proc = subprocess.run(
            ["go", "mod", "download"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        logs.append(proc.stdout)
        
        # Build
        logs.append("\n=== Building Go project ===")
        proc = subprocess.run(
            ["go", "build", "-v", "./..."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        logs.append(proc.stdout)
        
        if proc.returncode != 0:
            result["success"] = False
            result["compile_errors"].append(proc.stderr)
            
    except subprocess.TimeoutExpired:
        result["success"] = False
        result["compile_errors"].append("Go build timed out")
    except Exception as e:
        result["success"] = False
        result["compile_errors"].append(f"Error building Go project: {str(e)}")
    
    result["logs"] = "\n".join(logs)
    return result


def build_java(workspace: str) -> Dict[str, Any]:
    """Build Java project with Maven or Gradle"""
    
    result = {
        "success": True,
        "compile_errors": [],
        "warnings": [],
        "logs": ""
    }
    
    logs = []
    
    # Detect build tool
    if os.path.exists(os.path.join(workspace, "pom.xml")):
        # Maven
        try:
            cmd = ["mvn", "clean", "compile", "-q"]
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=config.build_timeout
            )
            logs.append(proc.stdout)
            if proc.returncode != 0:
                result["success"] = False
                result["compile_errors"].append(proc.stderr)
        except Exception as e:
            result["success"] = False
            result["compile_errors"].append(f"Maven build failed: {str(e)}")
    
    elif os.path.exists(os.path.join(workspace, "build.gradle")):
        # Gradle
        try:
            cmd = ["gradle", "build", "-x", "test"]
            proc = subprocess.run(
                cmd,
                cwd=workspace,
                capture_output=True,
                text=True,
                timeout=config.build_timeout
            )
            logs.append(proc.stdout)
            if proc.returncode != 0:
                result["success"] = False
                result["compile_errors"].append(proc.stderr)
        except Exception as e:
            result["success"] = False
            result["compile_errors"].append(f"Gradle build failed: {str(e)}")
    
    result["logs"] = "\n".join(logs)
    return result


def calculate_build_size(workspace: str) -> str:
    """Calculate total size of build artifacts"""
    total_size = 0
    
    # Count sizes of common build artifact directories
    artifact_dirs = ["dist", "build", "target", "out", "bin", "node_modules", "__pycache__"]
    
    for root, dirs, files in os.walk(workspace):
        # Skip hidden directories
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        
        for f in files:
            filepath = os.path.join(root, f)
            try:
                total_size += os.path.getsize(filepath)
            except:
                pass
    
    # Convert to human readable
    if total_size < 1024:
        return f"{total_size}B"
    elif total_size < 1024 * 1024:
        return f"{total_size / 1024:.1f}KB"
    elif total_size < 1024 * 1024 * 1024:
        return f"{total_size / (1024 * 1024):.1f}MB"
    else:
        return f"{total_size / (1024 * 1024 * 1024):.1f}GB"
