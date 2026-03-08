# llama.cpp Integration Guide

## For Owner Use (Local Offline AI)

JARVIS is configured to use your local llama.cpp server by default - no API keys needed.

### Quick Setup

1. **Start llama.cpp server:**
   ```bash
   llama-server -m your-model.gguf --port 8080 --ctx-size 8192
   ```

2. **Verify it's running:**
   ```bash
   curl http://localhost:8080/health
   ```

3. **Run JARVIS:**
   ```bash
   python -m uvicorn src.main:app --reload
   ```

### Configuration Options

In `.env`:

```env
# Enable local llama.cpp
CODE_AUTO_LOCAL_LLM_ENABLED=true

# Server URL
CODE_AUTO_LOCAL_LLM_URL=http://localhost:8080

# Model name (for reference)
CODE_AUTO_LOCAL_LLM_MODEL=local-model

# Context size (match your server)
CODE_AUTO_LOCAL_LLM_CONTEXT=8192
```

### Supported llama.cpp Servers

- **llama.cpp** (official)
- **koboldcpp** (with OpenAI compatibility)
- **oobabooga text-generation-webui** (with API enabled)
- **Any OpenAI-compatible local server**

### Recommended Models for Code Generation

- **CodeLlama** (7B-34B) - Specialized for code
- **DeepSeek Coder** - Excellent code generation
- **Llama 3.x** - Good general purpose
- **Mistral** - Fast and capable

### Troubleshooting

**"llama.cpp server not responding"**
- Check server is running: `curl http://localhost:8080/health`
- Verify port matches your `.env` setting
- Check firewall isn't blocking port 8080

**Slow code generation**
- Use a smaller model (7B instead of 70B)
- Reduce context size: `--ctx-size 4096`
- Use GPU offloading: `-ngl 99`

**Out of memory**
- Reduce context size
- Use smaller model
- Enable GPU offloading

---

## For Customer Deployments

### Option 1: Customer Uses Local llama.cpp (Recommended)

Same setup as owner use - customer runs their own llama.cpp server.
No ongoing API costs.

### Option 2: Customer Uses Commercial APIs

Customer provides their own API keys:

```env
CODE_AUTO_LLM_PROVIDER=openai
CODE_AUTO_OPENAI_API_KEY=sk-...
```

Or:

```env
CODE_AUTO_LLM_PROVIDER=anthropic
CODE_AUTO_ANTHROPIC_API_KEY=sk-ant-...
```

### Option 3: You Host the LLM

You run a central llama.cpp server and customers connect to it:

```env
CODE_AUTO_LLM_PROVIDER=llama-cpp
CODE_AUTO_LOCAL_LLM_URL=https://your-llm-server.com
```

---

## API Endpoints for llama.cpp

The client supports these llama.cpp endpoints:

1. **OpenAI-compatible** (preferred):
   - `POST /v1/chat/completions`

2. **Legacy** (fallback):
   - `POST /completion`

3. **Health check**:
   - `GET /health`
   - `GET /v1/models`

---

## Example llama.cpp Commands

### Basic Server
```bash
llama-server -m codellama-7b.gguf --port 8080 --ctx-size 8192
```

### With GPU Offloading
```bash
llama-server -m codellama-7b.gguf --port 8080 --ctx-size 8192 -ngl 99
```

### Multi-GPU
```bash
llama-server -m codellama-7b.gguf --port 8080 --ctx-size 8192 -ngl 99 --split-mode row --main-gpu 0 --tensor-split 0,1
```

### With Authentication (for customer hosting)
```bash
llama-server -m codellama-7b.gguf --port 8080 --ctx-size 8192 --api-key your-secret-key
```

---

## Performance Tips

1. **Use GGUF format** - Quantized models are faster
2. **GPU offloading** - Set `-ngl 99` to offload all layers
3. **Batch size** - Adjust `--batch-size` for your VRAM
4. **Context size** - Match to your needs (8192 default)
5. **Threads** - Set `--threads` to CPU core count

## Testing Connection

```python
from src.llm.client import LlamaCppClient

client = LlamaCppClient("http://localhost:8080")

if client.health_check():
    print("llama.cpp is ready!")
    response = client.generate("Write a Python function to add two numbers")
    print(response)
else:
    print("llama.cpp server not responding")
```
