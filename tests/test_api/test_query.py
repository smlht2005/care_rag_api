"""
REST API 查詢測試
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_rest_query():
    """測試 REST 查詢端點"""
    response = client.post(
        "/api/v1/query",
        json={"query": "測試問題", "top_k": 3}
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "sources" in data
    assert "query" in data

def test_rest_query_with_provider():
    """測試指定 LLM provider"""
    response = client.post(
        "/api/v1/query",
        json={
            "query": "測試問題",
            "provider": "openai",
            "top_k": 3
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "provider" in data

def test_rest_query_validation():
    """測試查詢驗證"""
    # 空查詢
    response = client.post(
        "/api/v1/query",
        json={"query": ""}
    )
    assert response.status_code == 422  # Validation error

def test_rest_query_invalid_top_k():
    """測試無效的 top_k 參數"""
    response = client.post(
        "/api/v1/query",
        json={"query": "測試", "top_k": 0}
    )
    assert response.status_code == 422  # Validation error
