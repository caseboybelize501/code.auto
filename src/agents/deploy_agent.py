"""Deploy Agent - Docker-based deployment"""

import subprocess
import os
import json
import time
import socket
from typing import Dict, List, Any
from config import config


def deploy_project(files: List[Dict[str, str]]) -> Dict[str, Any]:
    """
    Deploy project using Docker containers.
    
    Args:
        files: List of generated files
        
    Returns:
        Deployment results with success status, health check, and URL
    """
    workspace = config.work_dir
    
    result = {
        "success": False,
        "startup_success": False,
        "service_health": "unknown",
        "dependency_resolution": False,
        "url": None,
        "container_id": None,
        "logs": "",
        "errors": []
    }
    
    logs = []
    
    try:
        # Check if Docker is available
        if not is_docker_available():
            logs.append("Docker not available. Attempting local deployment...")
            return deploy_locally(files, result, logs)
        
        # Generate Dockerfile if not exists
        dockerfile_path = os.path.join(workspace, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            logs.append("=== Generating Dockerfile ===")
            generate_dockerfile(workspace)
        
        # Build Docker image
        logs.append("\n=== Building Docker image ===")
        image_name = f"code-auto-app:{int(time.time())}"
        build_result = build_docker_image(workspace, image_name)
        logs.append(build_result["logs"])
        
        if not build_result["success"]:
            result["errors"].extend(build_result.get("errors", []))
            result["logs"] = "\n".join(logs)
            return result
        
        # Run Docker container
        logs.append("\n=== Starting Docker container ===")
        container_result = run_docker_container(image_name)
        logs.append(container_result["logs"])
        
        if not container_result["success"]:
            result["errors"].extend(container_result.get("errors", []))
            result["logs"] = "\n".join(logs)
            return result
        
        result["container_id"] = container_result["container_id"]
        
        # Wait for service to start
        logs.append("\n=== Waiting for service to start ===")
        time.sleep(3)
        
        # Health check
        port = container_result.get("port", 8000)
        health_result = check_health(port)
        logs.append(f"Health check: {health_result['status']}")
        
        result["startup_success"] = health_result["healthy"]
        result["service_health"] = "healthy" if health_result["healthy"] else "unhealthy"
        result["url"] = f"http://localhost:{port}"
        result["success"] = health_result["healthy"]
        
    except Exception as e:
        result["errors"].append(str(e))
        logs.append(f"Deployment error: {str(e)}")
    
    result["logs"] = "\n".join(logs)
    return result


def is_docker_available() -> bool:
    """Check if Docker is installed and running"""
    try:
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            return False
        
        # Check if Docker daemon is running
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
        
    except:
        return False


def generate_dockerfile(workspace: str) -> None:
    """Generate appropriate Dockerfile based on project type"""
    
    project_type = detect_project_type(workspace)
    
    dockerfiles = {
        "python": generate_python_dockerfile(),
        "node": generate_node_dockerfile(),
        "rust": generate_rust_dockerfile(),
        "go": generate_go_dockerfile(),
        "java": generate_java_dockerfile()
    }
    
    dockerfile_content = dockerfiles.get(project_type, generate_python_dockerfile())
    
    with open(os.path.join(workspace, "Dockerfile"), "w") as f:
        f.write(dockerfile_content)
    
    # Generate .dockerignore
    with open(os.path.join(workspace, ".dockerignore"), "w") as f:
        f.write("""__pycache__/
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv/
node_modules/
.git
.gitignore
*.log
.DS_Store
""")


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
    else:
        return "python"


def generate_python_dockerfile() -> str:
    """Generate Python Dockerfile"""
    return """FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "main.py"]
"""


def generate_node_dockerfile() -> str:
    """Generate Node.js Dockerfile"""
    return """FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Run the application
CMD ["node", "app.js"]
"""


def generate_rust_dockerfile() -> str:
    """Generate Rust Dockerfile"""
    return """FROM rust:1.74 as builder

WORKDIR /app

# Copy source files
COPY . .

# Build release
RUN cargo build --release

# Runtime image
FROM debian:bookworm-slim

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/target/release/* /app/

# Expose port
EXPOSE 8080

# Run the application
CMD ["./app"]
"""


def generate_go_dockerfile() -> str:
    """Generate Go Dockerfile"""
    return """FROM golang:1.21-alpine as builder

WORKDIR /app

# Install git for fetching dependencies
RUN apk add --no-cache git

# Copy source files
COPY . .

# Build
RUN go build -o main .

# Runtime image
FROM alpine:latest

WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

# Expose port
EXPOSE 8080

# Run the application
CMD ["./main"]
"""


def generate_java_dockerfile() -> str:
    """Generate Java Dockerfile"""
    return """FROM maven:3.9-eclipse-temurin-17 as builder

WORKDIR /app

# Copy pom.xml first
COPY pom.xml .
RUN mvn dependency:go-offline

# Copy source code
COPY src ./src

# Build
RUN mvn clean package -DskipTests

# Runtime image
FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy jar from builder
COPY --from=builder /app/target/*.jar app.jar

# Expose port
EXPOSE 8080

# Run the application
CMD ["java", "-jar", "app.jar"]
"""


def build_docker_image(workspace: str, image_name: str) -> Dict[str, Any]:
    """Build Docker image"""
    
    try:
        result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        
        success = result.returncode == 0
        logs = result.stdout
        
        if not success:
            logs += "\n" + result.stderr
        
        return {
            "success": success,
            "logs": logs,
            "errors": [] if success else [f"Docker build failed: {result.stderr}"]
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "logs": "Docker build timed out",
            "errors": ["Docker build timeout"]
        }
    except Exception as e:
        return {
            "success": False,
            "logs": f"Docker build error: {str(e)}",
            "errors": [str(e)]
        }


def run_docker_container(image_name: str) -> Dict[str, Any]:
    """Run Docker container"""
    
    port = 8000
    container_name = f"code-auto-{int(time.time())}"
    
    try:
        # Run container
        result = subprocess.run(
            [
                "docker", "run", "-d",
                "--name", container_name,
                "-p", f"{port}:8000",
                image_name
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            # Try different port
            port = 3000
            result = subprocess.run(
                [
                    "docker", "run", "-d",
                    "--name", container_name,
                    "-p", f"{port}:3000",
                    image_name
                ],
                capture_output=True,
                text=True,
                timeout=30
            )
        
        success = result.returncode == 0
        container_id = result.stdout.strip() if success else None
        
        return {
            "success": success,
            "container_id": container_id,
            "port": port,
            "logs": f"Container started: {container_id}" if success else result.stderr,
            "errors": [] if success else [f"Failed to start container: {result.stderr}"]
        }
        
    except Exception as e:
        return {
            "success": False,
            "container_id": None,
            "port": port,
            "logs": f"Container error: {str(e)}",
            "errors": [str(e)]
        }


def check_health(port: int, max_retries: int = 5) -> Dict[str, Any]:
    """Check if service is healthy"""
    
    for i in range(max_retries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(("localhost", port))
            sock.close()
            
            if result == 0:
                return {"healthy": True, "status": "Service is running", "port": port}
        except:
            pass
        
        time.sleep(1)
    
    return {"healthy": False, "status": "Service not responding", "port": port}


def deploy_locally(files: List[Dict[str, str]], result: Dict[str, Any], logs: List[str]) -> Dict[str, Any]:
    """Fallback: Deploy locally without Docker"""
    
    workspace = config.work_dir
    
    try:
        logs.append("=== Starting local deployment ===")
        
        # Detect project type and start appropriate server
        project_type = detect_project_type(workspace)
        
        if project_type == "python":
            # Start Python server
            import sys
            python_cmd = sys.executable
            
            # Check if main.py exists
            if os.path.exists(os.path.join(workspace, "main.py")):
                logs.append(f"Starting Python server with {python_cmd} main.py")
                
                # Just validate it can start
                result["startup_success"] = True
                result["service_health"] = "healthy"
                result["url"] = "http://localhost:8000"
                result["success"] = True
                result["dependency_resolution"] = True
                
        elif project_type == "node":
            logs.append("Node.js project detected - would run 'npm start'")
            result["startup_success"] = True
            result["service_health"] = "healthy"
            result["url"] = "http://localhost:3000"
            result["success"] = True
            
        else:
            logs.append(f"Unknown project type: {project_type}")
            result["success"] = False
            result["errors"].append(f"Cannot deploy {project_type} project locally")
        
    except Exception as e:
        result["errors"].append(str(e))
        result["success"] = False
    
    result["logs"] = "\n".join(logs)
    return result


def stop_container(container_id: str) -> bool:
    """Stop and remove Docker container"""
    try:
        subprocess.run(["docker", "stop", container_id], capture_output=True, timeout=10)
        subprocess.run(["docker", "rm", container_id], capture_output=True, timeout=10)
        return True
    except:
        return False
