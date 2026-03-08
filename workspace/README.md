# Build an ML inference serving platform with model versioning, A/B testing, canary deployments, request batching, GPU scheduling, auto-scaling, latency monitoring, and cost optimization. Support multiple model formats (ONNX, PyTorch, TensorFlow) and rate limiting per API key.

Auto-generated FastAPI application.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python main.py
```

3. Access the API:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

- `GET /items` - List all items
- `GET /items/{id}` - Get item by ID
- `POST /items` - Create new item
