"""
Cloud Run S2S 認證：取得 ID token（支援直接簽發與 impersonation）。

更新時間：2026-03-31 11:53
作者：AI Assistant
修改摘要：新增 Cloud Run 服務對服務呼叫所需的 ID token 取得工具，供 LINE webhook proxy 轉呼叫 care-rag-api。
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Optional, Tuple

import google.auth
from google.auth import impersonated_credentials
from google.auth.transport.requests import Request
from google.oauth2 import id_token

logger = logging.getLogger("CloudRunAuthService")

# ID tokens are valid for 1 hour; refresh 5 minutes before expiry
_TOKEN_TTL_SECONDS = 3600
_TOKEN_REFRESH_MARGIN_SECONDS = 300

# Module-level cache: key = (target_audience, invoker_service_account), value = (token, expiry_ts)
_token_cache: dict[Tuple[str, Optional[str]], Tuple[str, float]] = {}
_cache_lock = threading.Lock()


class CloudRunAuthService:
    """集中處理 Cloud Run S2S ID token 取得流程。"""

    def get_id_token(self, target_audience: str, invoker_service_account: Optional[str] = None) -> str:
        """
        取得 Cloud Run ID token（帶快取，每小時自動更新）。

        - invoker_service_account 有值：先 impersonate 再簽 ID token
        - invoker_service_account 無值：使用目前執行身分直接簽 ID token
        """
        cache_key: Tuple[str, Optional[str]] = (target_audience, invoker_service_account)
        now = time.monotonic()

        with _cache_lock:
            cached = _token_cache.get(cache_key)
            if cached and cached[1] > now:
                logger.debug("Using cached Cloud Run ID token for audience=%s", target_audience)
                return cached[0]

        token = self._mint_token(target_audience, invoker_service_account)
        expiry = now + _TOKEN_TTL_SECONDS - _TOKEN_REFRESH_MARGIN_SECONDS

        with _cache_lock:
            _token_cache[cache_key] = (token, expiry)

        return token

    def _mint_token(self, target_audience: str, invoker_service_account: Optional[str]) -> str:
        request = Request()

        if invoker_service_account:
            source_creds, _ = google.auth.default()
            target_creds = impersonated_credentials.Credentials(
                source_credentials=source_creds,
                target_principal=invoker_service_account,
                target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
                lifetime=3600,
            )
            id_creds = impersonated_credentials.IDTokenCredentials(
                target_credentials=target_creds,
                target_audience=target_audience,
                include_email=True,
            )
            id_creds.refresh(request)
            token = id_creds.token
        else:
            token = id_token.fetch_id_token(request, target_audience)

        if not token:
            raise RuntimeError("Failed to mint Cloud Run ID token")

        logger.debug("Minted Cloud Run ID token prefix=%s..., len=%s", token[:20], len(token))
        return token

