"""
Embedding 服務抽象層
更新時間：2026-03-13
作者：AI Assistant
修改摘要：GoogleGenAIEmbeddingService.embed() 依 API 上限每批最多 100 筆分批呼叫 embed_content，再合併結果，避免 IC 檔 329 筆 QA 一次送出導致 400 INVALID_ARGUMENT
更新時間：2026-03-11 14:30
作者：AI Assistant
修改摘要：StubEmbeddingService 改用 hashlib.sha256 確保跨進程 deterministic（修正 Python hash randomization 問題）
更新時間：2026-03-10 12:20
作者：AI Assistant
修改摘要：完全移除 google.generativeai 依賴，只保留新 SDK google.genai + StubEmbeddingService
更新時間：2026-03-09 20:05
作者：AI Assistant
修改摘要：抑制舊版 google.generativeai 的 FutureWarning（棄用提示）
更新時間：2026-03-09 19:55
作者：AI Assistant
修改摘要：移除 embed_content 的 output_dimensionality 參數（部分 google-genai 版本不支援）；改為取得向量後本地截斷至 VECTOR_DIMENSION
更新時間：2026-03-09 19:45
作者：AI Assistant
修改摘要：若 .env 設 GEMINI_EMBEDDING_MODEL=text-embedding-004，新 SDK 自動改為 gemini-embedding-001 並 log 警告（避免 v1beta 404）
更新時間：2026-03-09 19:35
作者：AI Assistant
修改摘要：新 SDK 預設改為 gemini-embedding-001（Gemini API v1beta 支援），修復 text-embedding-004 的 404；並傳 output_dimensionality=768
更新時間：2026-03-09 19:25
作者：AI Assistant
修改摘要：修正 model is required. 根因：GEMINI_EMBEDDING_MODEL 未設時 getattr 回傳 None，改為 ... or None or 預設值 確保必有 model
更新時間：2026-03-09 19:15
作者：AI Assistant
修改摘要：舊版 GeminiEmbeddingService 改為逐筆傳 content（單一 str），避免傳 list 觸發 Invalid input type (str, Model, or TunedModel)
更新時間：2026-03-09 19:00
作者：AI Assistant
修改摘要：新增 GoogleGenAIEmbeddingService（新 SDK google.genai），支援 text-embedding-004；可透過 USE_GOOGLE_GENAI_SDK 切換
更新時間：2026-03-09 18:30
作者：AI Assistant
修改摘要：預設模型改為 models/embedding-001（舊版 google.generativeai 支援），避免 text-embedding-004 在 v1beta 回 404
更新時間：2026-03-09 17:40
作者：AI Assistant
修改摘要：新增 EmbeddingService 抽象與 Gemini/Stub 實作，提供文字轉向量介面供 QA 檢索使用
"""
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional

from app.config import settings

logger = logging.getLogger("EmbeddingService")

# Google GenAI API 單批最多 100 筆（at most 100 requests can be in one batch），超過會 400 INVALID_ARGUMENT
_GENAI_EMBED_BATCH_SIZE = 100

# 新版 SDK（google.genai）
try:
    from google import genai as genai_new  # type: ignore

    GENAI_NEW_AVAILABLE = True
except ImportError:  # pragma: no cover
    genai_new = None  # type: ignore
    GENAI_NEW_AVAILABLE = False


class BaseEmbeddingService(ABC):
    """Embedding 基底抽象類別"""

    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """將多個文字轉換為向量表示"""
        raise NotImplementedError


class GoogleGenAIEmbeddingService(BaseEmbeddingService):
    """
    使用新 SDK google.genai 的 embedding 實作。

    - 套件：pip install google-genai
    - 金鑰：settings.GOOGLE_API_KEY 或環境變數 GOOGLE_API_KEY
    - 模型：預設 gemini-embedding-001（Gemini API v1beta 支援；text-embedding-004 僅 Vertex/部分端點）
    - 維度：依 settings.VECTOR_DIMENSION（預設 768）傳入 output_dimensionality
    - 啟用：在 .env 設定 USE_GOOGLE_GENAI_SDK=true 即可優先使用本實作
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None) -> None:
        self.api_key = api_key or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
        # 若 .env 未設 GEMINI_EMBEDDING_MODEL，getattr 會得到 None；預設用 Gemini API v1beta 支援的模型
        raw_model = (
            model_name
            or getattr(settings, "GEMINI_EMBEDDING_MODEL", None)
            or "gemini-embedding-001"
        )
        # Gemini API (api_key) v1beta 不支援 text-embedding-004，會 404；強制改用 gemini-embedding-001
        if raw_model in ("text-embedding-004", "models/text-embedding-004"):
            logger.warning(
                "text-embedding-004 在 Gemini API v1beta 不支援，已改為 gemini-embedding-001"
            )
            self.model_name = "gemini-embedding-001"
        else:
            self.model_name = raw_model
        self._output_dim = getattr(settings, "VECTOR_DIMENSION", 768)
        self._client = None
        self._usable = False

        if not GENAI_NEW_AVAILABLE:
            logger.warning("google-genai 未安裝，請執行: pip install google-genai")
            return
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY 未設定，EmbeddingService 將降級為 stub")
            return
        try:
            self._client = genai_new.Client(api_key=self.api_key)
            self._usable = True
            logger.info(f"GoogleGenAIEmbeddingService 初始化完成，模型：{self.model_name}")
        except Exception as e:  # pragma: no cover
            logger.warning(f"初始化 GoogleGenAIEmbeddingService 失敗，降級為 stub：{e}")
            self._usable = False

    async def embed(self, texts: List[str]) -> List[List[float]]:
        if not self._usable or not texts or not self._client:
            return []

        import asyncio

        def _embed_batch(batch: List[str]) -> List[List[float]]:
            try:
                result = self._client.models.embed_content(
                    model=self.model_name,
                    contents=batch,
                )
                if result and hasattr(result, "embeddings") and result.embeddings:
                    vectors = [list(e.values) for e in result.embeddings]
                    # 部分 google-genai 版本不支援 output_dimensionality，改為本地截斷至 VECTOR_DIMENSION
                    if self._output_dim and vectors and len(vectors[0]) > self._output_dim:
                        vectors = [v[: self._output_dim] for v in vectors]
                    return vectors
            except Exception as e:  # pragma: no cover
                logger.warning(f"Google GenAI embedding 發生錯誤，降級為 stub：{e}")
            return []

        # API 單批最多 100 筆，超過會 400；分批呼叫再合併結果
        all_vectors: List[List[float]] = []
        for i in range(0, len(texts), _GENAI_EMBED_BATCH_SIZE):
            sub_batch = texts[i : i + _GENAI_EMBED_BATCH_SIZE]
            chunk_vectors = await asyncio.to_thread(_embed_batch, sub_batch)
            if not chunk_vectors or len(chunk_vectors) != len(sub_batch):
                return []
            all_vectors.extend(chunk_vectors)
        return all_vectors


class StubEmbeddingService(BaseEmbeddingService):
    """
    簡易 stub：使用 deterministic hash 將文字映射到固定長度向量。
    目的在於維持介面與流程正確，未真正提供語意能力。
    """

    def __init__(self, dim: int = 64) -> None:
        self.dim = dim
        self._logger = logging.getLogger("StubEmbeddingService")
        self._logger.info(f"使用 StubEmbeddingService，dim={dim}")

    async def embed(self, texts: List[str]) -> List[List[float]]:
        import hashlib
        import math
        import struct

        vectors: List[List[float]] = []
        for t in texts:
            # 使用 sha256 確保跨進程 / 跨啟動 deterministic（避免 Python hash randomization 問題）
            digest = hashlib.sha256(t.encode("utf-8", errors="replace")).digest()
            # 從 digest bytes 逐步展開至 dim 維向量（重複雜湊填充，保持 deterministic）
            extended = bytearray()
            seed = digest
            while len(extended) < self.dim * 4:
                seed = hashlib.sha256(seed).digest()
                extended += seed
            raw_ints = struct.unpack_from(f"<{self.dim}I", bytes(extended[: self.dim * 4]))
            # 歸一化至 [-1, 1]
            vec = [math.sin(float(v)) for v in raw_ints]
            vectors.append(vec)
        return vectors


def get_default_embedding_service() -> BaseEmbeddingService:
    """
    取得預設的 EmbeddingService：
    - **優先**使用新 SDK GoogleGenAIEmbeddingService（google.genai, gemini-embedding-001）；
    - 若新 SDK 不可用或初始化失敗，則直接回傳 StubEmbeddingService。

    備註：
    - 舊版 google.generativeai 的 GeminiEmbeddingService 僅保留為手動注入／測試用途，
      不再由此函式自動選取，避免 model name / API 版本差異帶來的錯誤。
    """
    if GENAI_NEW_AVAILABLE:
        service = GoogleGenAIEmbeddingService()
        if isinstance(service, GoogleGenAIEmbeddingService) and service._usable:  # type: ignore[attr-defined]
            return service
        logger.warning("GoogleGenAIEmbeddingService 初始化失敗，將使用 StubEmbeddingService 作為後備 embedding。")
    else:
        logger.warning("google-genai 套件不可用，將使用 StubEmbeddingService 作為後備 embedding。")
    return StubEmbeddingService()

