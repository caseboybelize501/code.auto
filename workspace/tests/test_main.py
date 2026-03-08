"""Auto-generated tests for Build an ML inference serving platform with model versioning, A/B testing, canary deployments, request batching, GPU scheduling, auto-scaling, latency monitoring, and cost optimization. Support multiple model formats (ONNX, PyTorch, TensorFlow) and rate limiting per API key."""

import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_list_items():
    response = client.get("/items")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_item():
    data = {"name": "Test Item", "description": "A test item"}
    response = client.post("/items", json=data)
    assert response.status_code == 201
    assert response.json()["id"] is not None
