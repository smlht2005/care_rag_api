"""
LINE webhook proxy：簽章驗證 + 轉呼叫 + Reply API 回覆。

更新時間：2026-03-31 11:53
作者：AI Assistant
修改摘要：新增單元測試，驗證正確簽章時會呼叫 LINE Reply API；reply 失敗不影響 webhook 200。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings


client = TestClient(app)


def _sign(raw: bytes, secret: str) -> str:
    mac = hmac.new(secret.encode("utf-8"), raw, hashlib.sha256).digest()
    return base64.b64encode(mac).decode("utf-8")


def _payload(text: str = "查詢掛號紀錄", reply_token: str = "rt") -> dict:
    return {
        "events": [
            {
                "type": "message",
                "replyToken": reply_token,
                "source": {"type": "user", "userId": "U123"},
                "timestamp": 1234567890,
                "message": {"type": "text", "id": "1", "text": text},
            }
        ]
    }


@pytest.fixture(autouse=True)
def _settings_defaults(monkeypatch):
    # 避免污染其他測試
    monkeypatch.setattr(settings, "LINE_WEBHOOK_REQUIRE_SIGNATURE", True)
    monkeypatch.setattr(settings, "LINE_CHANNEL_SECRET", "s")
    monkeypatch.setattr(settings, "LINE_PROXY_QUERY_ENDPOINT", "https://example.com/api/v1/query")
    monkeypatch.setattr(settings, "LINE_PROXY_TARGET_AUDIENCE", "https://example.com")
    monkeypatch.setattr(settings, "LINE_PROXY_INVOKER_SERVICE_ACCOUNT", None)
    monkeypatch.setattr(settings, "LINE_PROXY_X_API_KEY", "k")
    monkeypatch.setattr(settings, "LINE_REPLY_ENABLED", True)
    monkeypatch.setattr(settings, "LINE_CHANNEL_ACCESS_TOKEN", "t")
    monkeypatch.setattr(settings, "API_KEY_HEADER", "X-API-Key")


def test_line_webhook_signed_triggers_reply_and_forward(monkeypatch):
    body = _payload()
    import json

    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = _sign(raw, settings.LINE_CHANNEL_SECRET)

    class _Resp:
        def __init__(self, status_code: int, json_body=None, text: str = ""):
            self.status_code = status_code
            self._json_body = json_body
            self.text = text

        def json(self):
            return self._json_body

    with patch("app.api.v1.endpoints.webhook.CloudRunAuthService.get_id_token", return_value="idtoken"), patch(
        "app.api.v1.endpoints.webhook.httpx.AsyncClient"
    ) as mock_client:
        inst = mock_client.return_value.__aenter__.return_value
        proxy_resp = _Resp(200, {"answer": "ANS"})
        reply_resp = _Resp(200, None, "")
        inst.post = AsyncMock(side_effect=[proxy_resp, reply_resp])

        r = client.post(
            "/api/v1/webhook/line/query",
            data=raw,
            headers={"Content-Type": "application/json", "X-Line-Signature": sig},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["forwarded"] is True
        assert data["query_status"] == 200
        assert data["answer"] == "ANS"
        # reply_status should be set (200)
        assert data["reply_status"] == 200


def test_line_webhook_reply_failure_does_not_break(monkeypatch):
    body = _payload()
    import json

    raw = json.dumps(body, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    sig = _sign(raw, settings.LINE_CHANNEL_SECRET)

    class _Resp:
        def __init__(self, status_code: int, json_body=None, text: str = ""):
            self.status_code = status_code
            self._json_body = json_body
            self.text = text

        def json(self):
            return self._json_body

    with patch("app.api.v1.endpoints.webhook.CloudRunAuthService.get_id_token", return_value="idtoken"), patch(
        "app.api.v1.endpoints.webhook.httpx.AsyncClient"
    ) as mock_client:
        inst = mock_client.return_value.__aenter__.return_value
        proxy_resp = _Resp(200, {"answer": "ANS"})
        reply_resp = _Resp(500, None, "fail")
        inst.post = AsyncMock(side_effect=[proxy_resp, reply_resp])

        r = client.post(
            "/api/v1/webhook/line/query",
            data=raw,
            headers={"Content-Type": "application/json", "X-Line-Signature": sig},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["forwarded"] is True
        assert data["query_status"] == 200
        assert data["reply_status"] == 500
        assert "fail" in (data["reply_detail"] or "")

