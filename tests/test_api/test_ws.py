"""
WebSocket 測試
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_websocket_chat():
    """測試 WebSocket 聊天端點"""
    with client.websocket_connect("/api/v1/ws/chat") as websocket:
        # 發送查詢
        websocket.send_json({"query": "測試問題"})
        
        # 接收回應
        data = websocket.receive_json()
        assert "chunk" in data or "error" in data

def test_websocket_query():
    """測試 WebSocket 查詢端點"""
    with client.websocket_connect("/api/v1/ws/query") as websocket:
        # 發送查詢
        websocket.send_json({"query": "測試問題"})
        
        # 接收回應
        data = websocket.receive_json()
        assert "type" in data
        assert data["type"] in ["start", "chunk", "done", "error"]

def test_websocket_empty_query():
    """測試空查詢的 WebSocket"""
    with client.websocket_connect("/api/v1/ws/query") as websocket:
        websocket.send_json({"query": ""})
        data = websocket.receive_json()
        assert "error" in data or data.get("type") == "error"

def test_websocket_multiple_messages():
    """測試多個訊息的 WebSocket"""
    with client.websocket_connect("/api/v1/ws/query") as websocket:
        # 發送第一個查詢
        websocket.send_json({"query": "第一個問題"})
        data1 = websocket.receive_json()
        assert "type" in data1
        
        # 發送第二個查詢
        websocket.send_json({"query": "第二個問題"})
        data2 = websocket.receive_json()
        assert "type" in data2


