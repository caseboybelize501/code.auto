# 32-Thread Concurrent Code Execution Sandbox

High-performance sandboxed code execution system designed for validating LLM-generated code at scale.

## Hardware Target

```
GPU:     NVIDIA RTX 5090 — 32GB VRAM
CPU:     AMD Ryzen 9 7950X — 16C/32T @ 4.5GHz
RAM:     128GB DDR5-5600
STORAGE: 16TB NVMe (4 drives × 4TB)
MODEL:   qwen3-coder:30b via ollama
```

## Features

- **32 Parallel Execution Slots** - One per logical CPU core
- **CPU Pinning** - Each slot pinned to dedicated core via `taskset`
- **RAM Limits** - 2GB per slot (64GB total budget)
- **NVMe Isolation** - Round-robin temp dirs across 4 drives
- **Network Disabled** - Complete isolation
- **Multi-Language** - Python, Node.js, Bash, Go, Rust, C++
- **Timeout Enforcement** - Hard SIGKILL on timeout
- **Resource Monitoring** - CPU/memory tracking via psutil

## Quick Start

### 1. Install Dependencies

```bash
cd sandbox
pip install -r requirements.txt
```

### 2. Initialize Sandbox

```bash
python scripts/run_sandbox.py init
```

### 3. Start Server

```bash
python scripts/run_sandbox.py serve
```

Server runs on **http://localhost:7332**

## API Endpoints

### Execute Code

```bash
POST /execute
Content-Type: application/json

{
  "code": "print('Hello from sandbox!')",
  "language": "python",
  "timeout": 10
}
```

Response:
```json
{
  "stdout": "Hello from sandbox!\n",
  "stderr": "",
  "exit_code": 0,
  "runtime_ms": 45.2,
  "cpu_usage_pct": 12.5,
  "mem_peak_mb": 8.3,
  "timed_out": false,
  "slot_id": 7
}
```

### Validate LLM Code

```bash
POST /validate
Content-Type: application/json

{
  "prompt": "Print hello world",
  "code": "print('Hello, World!')",
  "expected_output": "Hello, World!"
}
```

### Get Statistics

```bash
GET /stats
```

### Get Topology

```bash
GET /topology
```

## CLI Commands

### Serve
```bash
python scripts/run_sandbox.py serve
```

### Validate Batch
```bash
python scripts/run_sandbox.py validate --input pairs.jsonl --output results/
```

### Benchmark
```bash
python scripts/run_sandbox.py benchmark
```

### Initialize
```bash
python scripts/run_sandbox.py init
```

## Architecture

```
sandbox/
├── config/
│   └── sandbox_topology.json    # 32 slot configurations
├── state/
│   └── validation_stats.json    # Validation statistics
├── engine/
│   ├── sandbox/
│   │   ├── topology_builder.py  # Phase 1: Detect & configure
│   │   └── runtime_pool.py      # Phase 2: Runtime pool
│   ├── executor/
│   │   └── code_executor.py     # Phase 3: Execution engine
│   └── validator/
│       └── llm_code_validator.py # Phase 4: Validation
├── scripts/
│   └── run_sandbox.py           # CLI entry point
├── server.py                     # FastAPI server
└── requirements.txt
```

## Isolation Methods

Priority order (auto-detected):

1. **Docker (rootless)** - Full container isolation
2. **Bubblewrap** - Lightweight namespace isolation
3. **Subprocess** - Process-level isolation (fallback)

## Supported Languages

| Language | Command | Test |
|----------|---------|------|
| Python 3 | `python3 -c` | `print('ok')` |
| Node.js | `node` | `console.log('ok')` |
| Deno | `deno run` | `console.log('ok')` |
| Bash | `bash -c` | `echo ok` |
| Go | `go run` | - |
| Rust | `rustc` + run | - |
| C++ | `g++ -O2` + run | - |

## Performance

Expected throughput on target hardware:
- **320 tasks in ~10 seconds** (32 tasks/sec)
- **Latency**: 50-200ms per execution
- **Memory**: 64GB max (2GB × 32 slots)

## Integration with JARVIS

This sandbox serves as the validation layer for JARVIS-generated code:

```python
from sandbox.engine.executor import execute_code
from sandbox.engine.validator import validate_code

# Execute generated code
result = await execute_code(
    code="print('Hello from JARVIS!')",
    language="python",
    timeout=10
)

# Validate with expected output
validation = await validate_code(
    prompt="Print greeting",
    code=result.stdout,
    expected_output="Hello from JARVIS!"
)
```

## Security Considerations

- Network access disabled for all slots
- Filesystem is read-only except temp dir
- Process tree killed on timeout
- RAM limits enforced
- CPU pinning prevents resource contention

## Troubleshooting

**"No available sandbox slots"**
- All 32 slots are busy
- Increase timeout or check for stuck processes

**"Execution timed out"**
- Code exceeded timeout limit
- Increase timeout or optimize code

**"Memory limit exceeded"**
- Process exceeded 2GB limit
- Optimize memory usage

## License

Proprietary - Same as JARVIS project
