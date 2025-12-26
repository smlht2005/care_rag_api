"""
Server-Sent Events (SSE) 測試
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_sse_stream():
    """測試 SSE 串流端點"""
    response = client.get("/api/v1/query/stream?query=測試問題")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    # 讀取串流內容
    content = response.text
    assert "data:" in content

def test_sse_stream_empty_query():
    """測試空查詢的 SSE"""
    response = client.get("/api/v1/query/stream?query=")
    assert response.status_code == 200

def test_sse_stream_format():
    """測試 SSE 格式"""
    response = client.get("/api/v1/query/stream?query=測試")
    assert response.status_code == 200
    
    # 檢查 SSE 格式
    lines = response.text.split("\n")
    data_lines = [line for line in lines if line.startswith("data:")]
    assert len(data_lines) > 0


