# JARVIS Code Generation: Complete Deep Dive

## Overview

JARVIS generates code through a **9-stage pipeline** that transforms natural language requirements into deployed, tested, production-ready applications.

```
User Requirements
       ↓
┌──────────────────────────────────────────────────────────────┐
│  1. PLAN → 2. GENERATE → 3. TEST → 4. BUILD → 5. DEPLOY     │
│                                                              │
│  9. LEARN ← 8. DEBUG ← 7. MONITOR ← 6. RUNTIME              │
└──────────────────────────────────────────────────────────────┘
       ↓
Production Application + Learning Memory
```

---

## Stage 1: Project Planning

**File:** `src/planner/dev_planner.py`

### Input
```json
{
  "requirements": "Build a REST API for a todo application with user authentication"
}
```

### Process Flow

```python
def plan_project(requirements: str) -> Dict[str, Any]:
    # Step 1.1: Check if LLM is available
    if has_llm_configured():
        # Use LLM (llama.cpp local or cloud API)
        plan = plan_with_llm(requirements)
    else:
        # Fallback: rule-based planning
        plan = plan_with_rules(requirements)
    
    # Step 1.2: Check memory for similar past projects
    similar_projects = memory_store.get_similar_projects(requirements, limit=3)
    
    # Step 1.3: Return final plan
    return plan
```

### LLM Planning (if available)

**Prompt sent to LLM:**
```
You are an expert software architect. Create a detailed project plan.

Requirements: Build a REST API for a todo application with user authentication

Respond with JSON:
{
    "requirements": "...",
    "architecture": "monolithic|microservices|serverless|event-driven",
    "language": "python|javascript|typescript|go|rust|java",
    "framework": "...",
    "database": "postgresql|mongodb|redis|sqlite|mysql",
    "testing_strategy": "...",
    "deployment_strategy": "docker|kubernetes|serverless|vm",
    "performance_target": "low_latency|high_throughput|balanced"
}
```

### Rule-Based Planning (fallback)

If no LLM is configured, uses keyword matching:

```python
def plan_with_rules(requirements: str) -> Dict[str, Any]:
    requirements_lower = requirements.lower()
    
    # Detect architecture
    if "microservice" in requirements_lower:
        architecture = "microservices"
    elif "serverless" in requirements_lower:
        architecture = "serverless"
    else:
        architecture = "monolithic"  # default
    
    # Detect language
    if "python" in requirements_lower:
        language = "python"
        framework = "fastapi"  # for APIs
    elif "node" in requirements_lower:
        language = "javascript"
        framework = "express"
    else:
        language = "python"  # default
        framework = "fastapi"
    
    return {
        "architecture": architecture,
        "language": language,
        "framework": framework,
        "database": "postgresql",  # default
        "deployment_strategy": "docker",
        ...
    }
```

### Output

```json
{
  "requirements": "REST API for todo app with authentication",
  "architecture": "monolithic",
  "language": "python",
  "framework": "fastapi",
  "database": "postgresql",
  "testing_strategy": "unit/integration/e2e",
  "deployment_strategy": "docker",
  "performance_target": "balanced",
  "estimated_complexity": "medium"
}
```

---

## Stage 2: Code Generation

**File:** `src/agents/code_agent.py`

### Input
The plan from Stage 1

### Process Flow

```python
def generate_code(plan: Dict[str, Any]) -> List[Dict[str, str]]:
    # Step 2.1: Check if LLM is available
    if not has_llm():
        return _generate_fallback_code(plan)
    
    try:
        # Step 2.2: Get LLM client
        llm = _get_llm()
        
        # Step 2.3: Build prompts
        system_prompt = """You are an expert software engineer. 
        Generate production-ready code..."""
        
        prompt = f"""Generate a complete project structure:
        
        Requirements: {plan.get('requirements')}
        Language: {plan.get('language')}
        Framework: {plan.get('framework')}
        
        Respond with JSON where keys are file paths and values are contents."""
        
        # Step 2.4: Call LLM
        files_dict = llm.generate_json(prompt, system_prompt, temperature=0.7)
        
        # Step 2.5: Write files to workspace
        written_files = _write_files(files_dict)
        
        return written_files
        
    except Exception as e:
        # Fallback if LLM fails
        return _generate_fallback_code(plan)
```

### LLM Client Selection

```python
def _get_llm():
    # Priority 1: Local llama.cpp (no API cost)
    if config.local_llm_enabled:
        if check_llama_cpp_available(config.local_llm_base_url):
            return create_llm_client(
                "llama-cpp",
                base_url="http://localhost:8080",
                model="local-model"
            )
    
    # Priority 2: OpenAI (commercial)
    if config.openai_api_key:
        return create_llm_client("openai", api_key, model)
    
    # Priority 3: Anthropic (commercial)
    if config.anthropic_api_key:
        return create_llm_client("anthropic", api_key, model)
```

### Fallback Code Generation

When LLM is unavailable, uses built-in templates:

```python
def _generate_fallback_code(plan: Dict) -> List[Dict]:
    if plan["language"] == "python":
        if plan["framework"] == "fastapi":
            return _generate_fastapi_fallback(plan)
        elif plan["framework"] == "flask":
            return _generate_flask_fallback(plan)
    
    # Templates include:
    # - main.py (Full CRUD API)
    # - requirements.txt
    # - config.py
    # - utils.py
    # - README.md
    # - tests/test_main.py
```

### File Writing

```python
def _write_files(files: List[Dict]) -> List[Dict]:
    workspace = config.work_dir  # "./workspace"
    
    for file_info in files:
        filepath = os.path.join(workspace, file_info["path"])
        
        # Create directories
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write file
        with open(filepath, "w") as f:
            f.write(file_info["content"])
    
    return files
```

### Output

```json
[
  {
    "name": "main.py",
    "path": "main.py",
    "content": "from fastapi import FastAPI...\napp = FastAPI()...\n",
    "full_path": "./workspace/main.py"
  },
  {
    "name": "requirements.txt",
    "path": "requirements.txt",
    "content": "fastapi==0.104.1\nuvicorn==0.24.0\n..."
  },
  ...
]
```

---

## Stage 3: Test Generation & Execution

**File:** `src/agents/test_agent.py`

### Test Generation

```python
def generate_tests(files: List[Dict], plan: Dict) -> List[Dict]:
    test_files = []
    
    for source_file in files:
        if source_file["name"].endswith(".py") and "test" not in source_file["name"]:
            # Generate pytest tests
            test_content = _generate_python_tests(source_file, plan)
            test_path = f"tests/test_{source_file['name']}"
            
            test_files.append({
                "name": test_path,
                "path": test_path,
                "content": test_content
            })
    
    return test_files
```

### Test Execution

```python
def run_tests(files: List[Dict]) -> Dict[str, Any]:
    workspace = config.work_dir
    
    # Detect test framework
    if os.path.exists(os.path.join(workspace, "tests")):
        return run_pytest(workspace)
    elif os.path.exists(os.path.join(workspace, "package.json")):
        return run_jest(workspace)
    
    return {"passed": True, "logs": "No tests found"}
```

### Pytest Execution

```python
def run_pytest(workspace: str) -> Dict:
    cmd = [
        "pytest",
        "--tb=short",
        "--maxfail=5",
        f"--timeout={config.test_timeout}",
        "-v",
        "--cov=.",
        "--cov-report=term-missing"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=workspace,
        capture_output=True,
        text=True,
        timeout=config.test_timeout
    )
    
    return {
        "passed": result.returncode == 0,
        "logs": result.stdout + result.stderr,
        "coverage": parse_coverage(result.stdout),
        "test_count": parse_test_count(result.stdout)
    }
```

### Output

```json
{
  "passed": true,
  "unit": {"passed": true, "results": []},
  "integration": {"passed": true, "results": []},
  "coverage": 85,
  "logs": "=== Unit Tests ===\n5 passed...",
  "errors": [],
  "test_count": 5,
  "failures": 0
}
```

---

## Stage 4: Build Process

**File:** `src/agents/build_agent.py`

### Process

```python
def build_project(files: List[Dict]) -> Dict[str, Any]:
    workspace = config.work_dir
    
    # Step 4.1: Detect project type
    project_type = detect_project_type(workspace)
    
    # Step 4.2: Run appropriate build
    if project_type == "python":
        return build_python(workspace)
    elif project_type == "node":
        return build_node(workspace)
    elif project_type == "rust":
        return build_rust(workspace)
    # etc.
```

### Python Build

```python
def build_python(workspace: str) -> Dict:
    result = {"success": True, "errors": [], "warnings": [], "logs": ""}
    
    # Install dependencies
    if os.path.exists("requirements.txt"):
        proc = subprocess.run(
            ["pip", "install", "-r", "requirements.txt"],
            cwd=workspace,
            capture_output=True,
            text=True,
            timeout=config.build_timeout
        )
        
        if proc.returncode != 0:
            result["success"] = False
            result["errors"].append(proc.stderr)
    
    # Validate syntax
    syntax_errors = validate_python_syntax(workspace)
    if syntax_errors:
        result["success"] = False
        result["errors"].extend(syntax_errors)
    
    result["build_time"] = elapsed_time
    result["size"] = calculate_build_size(workspace)
    
    return result
```

### Output

```json
{
  "success": true,
  "compile_errors": [],
  "warnings": [],
  "build_time": 12.5,
  "size": "15.3MB",
  "artifacts": ["dist/app.whl"],
  "logs": "=== Installing dependencies ===\nSuccessfully installed..."
}
```

---

## Stage 5: Deployment

**File:** `src/agents/deploy_agent.py`

### Process

```python
def deploy_project(files: List[Dict]) -> Dict[str, Any]:
    workspace = config.work_dir
    
    # Step 5.1: Check Docker availability
    if is_docker_available():
        return deploy_with_docker(workspace)
    else:
        return deploy_locally(workspace)
```

### Docker Deployment

```python
def deploy_with_docker(workspace: str) -> Dict:
    # Generate Dockerfile
    if not os.path.exists("Dockerfile"):
        generate_dockerfile(workspace)
    
    # Build image
    image_name = f"code-auto-app:{timestamp}"
    build_result = subprocess.run(
        ["docker", "build", "-t", image_name, "."],
        cwd=workspace
    )
    
    # Run container
    container_result = subprocess.run(
        ["docker", "run", "-d", "-p", "8000:8000", image_name],
        capture_output=True,
        text=True
    )
    
    container_id = container_result.stdout.strip()
    
    # Health check
    time.sleep(3)
    health = check_health(8000)
    
    return {
        "success": health["healthy"],
        "container_id": container_id,
        "url": "http://localhost:8000",
        "service_health": "healthy" if health["healthy"] else "unhealthy"
    }
```

### Output

```json
{
  "success": true,
  "startup_success": true,
  "service_health": "healthy",
  "dependency_resolution": true,
  "url": "http://localhost:8000",
  "container_id": "abc123...",
  "logs": "=== Building Docker image ===\n..."
}
```

---

## Stage 6: Runtime Monitoring

**File:** `src/agents/runtime_agent.py`

### Process

```python
def monitor_runtime(deployment: Dict) -> Dict[str, Any]:
    url = deployment.get("url")
    
    # Collect system metrics
    system_metrics = collect_system_metrics()
    
    # Benchmark latency
    latency_results = benchmark_latency(url)
    
    # Benchmark throughput
    throughput_results = benchmark_throughput(url)
    
    # Check error rate
    error_results = check_error_rate(url)
    
    return {
        **system_metrics,
        **latency_results,
        **throughput_results,
        **error_results
    }
```

### Latency Benchmark

```python
def benchmark_latency(url: str, num_requests: int = 10) -> Dict:
    latencies = []
    
    for _ in range(num_requests):
        start = time.time()
        response = requests.get(url, timeout=5)
        elapsed = (time.time() - start) * 1000  # ms
        latencies.append(elapsed)
    
    latencies.sort()
    n = len(latencies)
    
    return {
        "latency": f"{sum(latencies)/n:.1f}ms",
        "p50_latency": f"{latencies[int(n*0.50)]:.1f}ms",
        "p95_latency": f"{latencies[int(n*0.95)]:.1f}ms",
        "p99_latency": f"{latencies[int(n*0.99)]:.1f}ms"
    }
```

### Output

```json
{
  "cpu_usage": "15%",
  "memory_usage": "256MB",
  "latency": "45ms",
  "throughput": "850 req/sec",
  "error_rate": "0.1%",
  "uptime": "99.9%",
  "p50_latency": "42ms",
  "p95_latency": "78ms",
  "p99_latency": "120ms"
}
```

---

## Stage 7: Debug Analysis (if needed)

**File:** `src/agents/debug_agent.py`

### Triggered When Tests Fail

```python
if not test_results.get("passed", True):
    debug_result = debug_failure(
        test_results.get("logs", ""),
        {"project_id": project_id}
    )
```

### Debug Process

```python
def debug_failure(logs: str, context: Dict) -> Dict:
    # Parse error logs
    parsed_errors = parse_error_logs(logs)
    
    # Use LLM for analysis (if available)
    if has_llm_configured():
        return analyze_with_llm(logs, parsed_errors)
    else:
        return analyze_with_rules(logs, parsed_errors)
```

### LLM Debug Analysis

```python
def analyze_with_llm(logs: str, errors: List) -> Dict:
    llm = get_llm_client()
    
    prompt = f"""Analyze these error logs:
    
    {logs[:5000]}
    
    Parsed errors: {json.dumps(errors)}
    
    Respond with JSON:
    {{
        "root_cause": "...",
        "error_type": "...",
        "affected_files": ["..."],
        "fix": "...",
        "confidence": 0.85,
        "regression_risk": 0.2
    }}"""
    
    return llm.generate_json(prompt)
```

### Output

```json
{
  "root_cause": "Missing dependency - 'requests' module not installed",
  "error_type": "dependency_error",
  "affected_files": ["main.py"],
  "fix": "Add 'requests' to requirements.txt and run: pip install -r requirements.txt",
  "confidence": 0.9,
  "regression_risk": 0.1,
  "suggested_changes": [...]
}
```

---

## Stage 8: Learning Memory Update

**File:** `src/agents/learn_agent.py`

### Process

```python
def update_learning_memory(
    memory: Dict,
    plan: Dict,
    test_results: Dict,
    build_result: Dict,
    runtime_metrics: Dict
) -> Dict:
    # Store in ChromaDB (vector memory)
    
    # 1. Bug patterns (if tests failed)
    if not test_results["passed"]:
        memory_store.add_bug_pattern(
            bug_type="test_failure",
            language=plan["language"],
            framework=plan["framework"],
            fix="See debug logs",
            context={"logs": test_results["logs"][:1000]}
        )
    
    # 2. Architecture performance
    memory_store.add_architecture_pattern(
        architecture=plan["architecture"],
        performance=runtime_metrics,
        language=plan["language"],
        framework=plan["framework"]
    )
    
    # 3. Update in-memory structures
    memory["bug_patterns"].append({...})
    memory["architecture_graph"].append({...})
    memory["algorithm_library"].append({...})
    memory["meta_learning_index"].append({...})
    
    return memory
```

### Memory Layers

1. **Bug Pattern Memory** - What went wrong and how it was fixed
2. **Architecture Performance Graph** - How different architectures perform
3. **Algorithm Efficiency Library** - Which algorithms work best
4. **Meta Learning Index** - Overall project outcomes

### Output

```json
{
  "bug_patterns": [...],
  "architecture_graph": [...],
  "algorithm_library": [...],
  "meta_learning_index": [...],
  "chroma_stats": {
    "bug_patterns": 5,
    "architecture": 12,
    "algorithms": 8,
    "projects": 3
  }
}
```

---

## Stage 9: API Response

**File:** `src/main.py`

### Final Response to User

```python
@app.post("/api/project/start")
async def start_project(request: ProjectRequest):
    result = await jarvis.start_project(request)
    return result
```

### Complete Response

```json
{
  "status": "completed",
  "project_id": "a1b2c3d4",
  "plan": {
    "architecture": "monolithic",
    "language": "python",
    "framework": "fastapi",
    ...
  },
  "files": [
    {"name": "main.py", "path": "main.py"},
    {"name": "requirements.txt", "path": "requirements.txt"},
    ...
  ],
  "test_results": {
    "passed": true,
    "coverage": 85,
    "test_count": 5
  },
  "build_result": {
    "success": true,
    "build_time": 12.5
  },
  "deployment": {
    "success": true,
    "url": "http://localhost:8000",
    "container_id": "abc123..."
  },
  "metrics": {
    "latency": "45ms",
    "throughput": "850 req/sec",
    "cpu_usage": "15%"
  },
  "memory": {
    "stats": {...}
  }
}
```

---

## Complete Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER REQUEST                             │
│  "Build a REST API for a todo application with authentication"  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: PLANNING (src/planner/dev_planner.py)                 │
│  - Check LLM availability (llama.cpp local or cloud)            │
│  - Generate architecture plan                                   │
│  - Check memory for similar projects                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Plan JSON Object
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 2: CODE GENERATION (src/agents/code_agent.py)            │
│  - Build LLM prompt with plan details                           │
│  - Call LLM (or use fallback templates)                         │
│  - Write files to ./workspace/                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    List of Generated Files
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 3: TESTING (src/agents/test_agent.py)                    │
│  - Generate test files                                          │
│  - Run pytest/jest                                              │
│  - Collect coverage metrics                                     │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Test Results (pass/fail)
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 4: BUILD (src/agents/build_agent.py)                     │
│  - Detect project type (python/node/rust/go/java)               │
│  - Install dependencies                                         │
│  - Validate syntax                                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Build Result (success/errors)
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 5: DEPLOYMENT (src/agents/deploy_agent.py)               │
│  - Check Docker availability                                    │
│  - Generate Dockerfile                                          │
│  - Build image and run container                                │
│  - Health check                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Deployment Info (URL, container_id)
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 6: MONITORING (src/agents/runtime_agent.py)              │
│  - Collect CPU/memory metrics                                   │
│  - Benchmark latency (p50, p95, p99)                            │
│  - Measure throughput                                           │
│  - Check error rate                                             │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Runtime Metrics
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 7: DEBUG (if tests failed)                               │
│  - Parse error logs                                             │
│  - LLM-powered root cause analysis                              │
│  - Generate fix recommendations                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
                    Debug Report
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 8: LEARNING (src/agents/learn_agent.py)                  │
│  - Store bug patterns in ChromaDB                               │
│  - Record architecture performance                              │
│  - Update algorithm library                                     │
│  - Save project outcomes                                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 9: API RESPONSE                                          │
│  Return complete results to user                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Configuration Points

### LLM Selection (config.py)

```python
# Default: use local llama.cpp (no API cost)
llm_provider = "llama-cpp"
local_llm_enabled = True
local_llm_base_url = "http://localhost:8080"

# For commercial deployments (customers)
# openai_api_key = "sk-..."
# anthropic_api_key = "sk-ant-..."
```

### Workspace Location

```python
work_dir = "./workspace"  # Generated code goes here
logs_dir = "./logs"       # Build/test logs
```

### Timeouts

```python
build_timeout = 300   # 5 minutes for build
test_timeout = 600    # 10 minutes for tests
```

---

## Error Handling at Each Stage

| Stage | Error Handling |
|-------|---------------|
| Planning | LLM fails → rule-based fallback |
| Code Gen | LLM fails → template fallback |
| Testing | Tests fail → debug agent triggered |
| Build | Syntax errors → returned in build_result |
| Deploy | Docker unavailable → local deployment |
| Monitor | Service down → simulated metrics |
| Debug | Analysis fails → rule-based diagnosis |

---

## Summary

JARVIS transforms natural language into production code through:

1. **Intelligent Planning** - LLM or rule-based architecture decisions
2. **AI Code Generation** - llama.cpp local or cloud APIs + fallback templates
3. **Automated Testing** - pytest/jest with coverage
4. **Multi-Language Build** - Python, Node, Rust, Go, Java
5. **Docker Deployment** - Containerized or local
6. **Performance Monitoring** - Real metrics collection
7. **Debug Analysis** - LLM-powered error diagnosis
8. **Continuous Learning** - ChromaDB memory for improvement
9. **Complete Feedback** - Full pipeline results returned to user

The system works **fully offline** with local llama.cpp, or can use commercial APIs for customer deployments.
