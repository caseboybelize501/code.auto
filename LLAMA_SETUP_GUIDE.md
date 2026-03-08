# llama.cpp Configuration for JARVIS

This folder contains configuration files for running llama.cpp with your local models.

## Files Created

1. **llama_models_config.json** - Complete model registry with all your GGUF models
2. **.env.llama** - Environment variables for llama.cpp configuration
3. **start_llama_server.bat** - Easy startup script for launching the server
4. **LLAMA_SETUP_GUIDE.md** - This file

## Your Models

Found **15 GGUF models** across your system:

### Code Generation Models (Recommended for JARVIS)
| Model | Size | Location |
|-------|------|----------|
| qwen2.5-coder-7b | 7B | D:\models\ |
| qwen3-coder-30b-q4 | 30B (Q4) | D:\models\ |
| qwen2.5-coder-32b | 32B | D:\Users\CASE\models\ |
| qwen3.5-9b | 9B | D:\Users\CASE\models\ |
| qwen3.5-27b | 27B | D:\Users\CASE\models\ |
| qwen3.5-35b | 35B | D:\Users\CASE\models\ |
| qwen3.5-35b-a3b | 35B (A3B) | D:\Users\CASE\models\ |
| qwen3-coder-30b-instruct-q8 | 30B (Q8) | goose\data\models\ |

### General Purpose Models
| Model | Size | Location |
|-------|------|----------|
| mistral-7b-instruct-v0.2 | 7B (Q4) | D:\AI\models\ |
| mistral-small-24b-instruct | 24B (Q4) | goose\data\models\ |
| glm-4.7-flash | 4.7B | D:\Users\CASE\models\ |
| nemotron-3-nano-30b | 30B | D:\Users\CASE\models\ |

### Embedding Models
| Model | Type | Location |
|-------|------|----------|
| nomic-embed-text-v1.5 | Embedding | .lmstudio\bundled-models\ |

## Quick Start

### Option 1: Using the Batch Script (Easiest)

```bash
# Start with default model (qwen2.5-coder-7b)
start_llama_server.bat

# Start with a specific model
start_llama_server.bat qwen3-coder-30b-q4

# Start with custom port
start_llama_server.bat mistral-7b 8081
```

### Option 2: Manual Command

```bash
python -m llama_cpp.server --model D:\models\qwen2.5-coder-7b.gguf --port 8080 --ctx-size 8192
```

### Option 3: Using Python API

```python
from llama_cpp import Llama

llm = Llama(
    model_path="D:\\models\\qwen2.5-coder-7b.gguf",
    n_ctx=8192,
    n_gpu_layers=99  # Set to 0 for CPU only
)

output = llm("Write a Python function to add two numbers", max_tokens=256)
print(output)
```

## Model Recommendations

### For Code Generation (JARVIS)
1. **qwen2.5-coder-7b** - Best balance of speed and quality (DEFAULT)
2. **qwen3-coder-30b-q4** - Higher quality, slower (quantized)
3. **qwen3.5-9b** - Fast response for quick tasks

### For General Chat
1. **mistral-7b-instruct-v0.2** - Good all-rounder
2. **mistral-small-24b-instruct** - Higher quality conversations

### For Embeddings
1. **nomic-embed-text-v1.5** - Use for RAG/vector search

## Configuration Options

### Environment Variables (.env)
```env
CODE_AUTO_LOCAL_LLM_URL=http://localhost:8080
CODE_AUTO_LOCAL_LLM_CONTEXT=8192
```

### Server Parameters
- `--port 8080` - Server port
- `--ctx-size 8192` - Context window size
- `--n-gpu-layers 99` - GPU offloading (set to 0 for CPU only)
- `--batch-size 512` - Batch size for processing
- `--threads 8` - CPU threads to use

## Testing the Server

Once started, test with:

```bash
# Health check
curl http://localhost:8080/health

# List models
curl http://localhost:8080/v1/models

# Generate text
curl http://localhost:8080/v1/chat/completions ^
  -H "Content-Type: application/json" ^
  -d "{\"messages\": [{\"role\": \"user\", \"content\": \"Hello!\"}]}"
```

## Integrating with JARVIS

Update your `.env` file:

```env
CODE_AUTO_LLM_PROVIDER=llama-cpp
CODE_AUTO_LOCAL_LLM_ENABLED=true
CODE_AUTO_LOCAL_LLM_URL=http://localhost:8080
CODE_AUTO_LOCAL_LLM_MODEL=qwen2.5-coder-7b
```

Then start the JARVIS API server:

```bash
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Troubleshooting

### "Out of Memory"
- Use a smaller model (7B or 9B)
- Reduce context size: `--ctx-size 4096`
- Reduce GPU layers: `--n-gpu-layers 50`

### "Model not found"
- Check the path in `llama_models_config.json`
- Ensure the file exists at the specified location

### "Server won't start"
- Check if port 8080 is already in use
- Try a different port: `start_llama_server.bat qwen2.5-coder-7b 8081`
- Verify llama_cpp_python is installed: `pip show llama_cpp_python`

### Slow Generation
- Use GPU offloading: `--n-gpu-layers 99`
- Use a smaller/quantized model (Q4 instead of full)
- Reduce batch size: `--batch-size 256`

## Available Models Reference

Run `start_llama_server.bat` without arguments to see all available model shortcuts:

```
Available models:
  qwen2.5-coder-7b          - Qwen2.5 Coder 7B (default, recommended for code)
  qwen3-coder-30b-q4        - Qwen3 Coder 30B quantized
  qwen2.5-coder-32b         - Qwen2.5 Coder 32B
  qwen3.5-9b                - Qwen3.5 9B (fast)
  qwen3.5-27b               - Qwen3.5 27B
  qwen3.5-35b               - Qwen3.5 35B
  qwen3.5-35b-a3b           - Qwen3.5 35B A3B
  glm-4.7-flash             - GLM-4.7 Flash
  nemotron-30b              - Nemotron-3 Nano 30B
  mistral-7b                - Mistral 7B Instruct
  mistral-small-24b         - Mistral Small 24B Instruct
  qwen3-coder-30b-instruct-q8 - Qwen3 Coder 30B Instruct Q8
  nomic-embed               - Nomic Embed (embedding model)
```
