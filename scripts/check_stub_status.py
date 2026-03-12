"""
檢查目前 Embedding 與 LLM 是否使用 Stub（假實作）。
執行方式：在專案根目錄執行 python -m scripts.check_stub_status
更新時間：2026-03-10
作者：AI Assistant
修改摘要：新增腳本，用於檢查 get_default_embedding_service 與 LLMService 是否為 Stub
"""
import os
import sys

# 確保專案根目錄在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.services.embedding_service import (
    get_default_embedding_service,
    GoogleGenAIEmbeddingService,
    StubEmbeddingService,
)
from app.services.llm_service import LLMService, GeminiLLM


def check_embedding():
    """檢查 Embedding 服務是否為 Stub。"""
    svc = get_default_embedding_service()
    is_stub = isinstance(svc, StubEmbeddingService)
    detail = ""
    if isinstance(svc, GoogleGenAIEmbeddingService):
        usable = getattr(svc, "_usable", False)
        if not usable:
            is_stub = True
            detail = " (GoogleGenAI 初始化失敗或未設定 GOOGLE_API_KEY，實際行為等同 Stub)"
        else:
            detail = f" (模型: {getattr(svc, 'model_name', '?')})"
    elif isinstance(svc, StubEmbeddingService):
        detail = " (假向量，相似度搜尋不具語意)"
    return is_stub, svc.__class__.__name__, detail


def check_llm():
    """檢查 LLM 服務是否為 Stub。"""
    llm_svc = LLMService()
    client = llm_svc.client
    # 本專案無 StubLLM 類別；GeminiLLM 在 _use_real_api=False 或 API 失敗時會用 _stub_generate
    is_stub = False
    detail = ""
    if isinstance(client, GeminiLLM):
        use_real = getattr(client, "_use_real_api", False)
        if not use_real:
            is_stub = True
            detail = " (未設定 GOOGLE_API_KEY 或 google-genai 不可用，實際使用 Stub 回應)"
        else:
            detail = f" (模型: {getattr(client, '_model_name', '?')})"
    else:
        detail = f" (provider={client.__class__.__name__})"
    return is_stub, client.__class__.__name__, detail


def main():
    print("=" * 60)
    print("Stub 狀態檢查 (Embedding / LLM)")
    print("=" * 60)
    print(f"  LLM_PROVIDER: {settings.LLM_PROVIDER}")
    print(f"  GOOGLE_API_KEY (Settings): {'已配置' if settings.GOOGLE_API_KEY else '未配置'}")
    print(f"  GEMINI_EMBEDDING_MODEL: {getattr(settings, 'GEMINI_EMBEDDING_MODEL', None)}")
    print()

    # Embedding
    emb_stub, emb_class, emb_detail = check_embedding()
    emb_status = "STUB" if emb_stub else "真實 API"
    print(f"Embedding: {emb_status} ({emb_class}){emb_detail}")

    # LLM
    llm_stub, llm_class, llm_detail = check_llm()
    llm_status = "STUB" if llm_stub else "真實 API"
    print(f"LLM:       {llm_status} ({llm_class}){llm_detail}")

    print()
    if emb_stub or llm_stub:
        print("結論: 目前有使用 Stub，問答/檢索可能非真實語意或為固定回應。")
        if emb_stub:
            print("  - 請確認 GOOGLE_API_KEY 已設定且 google-genai 已安裝，以使用真實 Embedding。")
        if llm_stub:
            print("  - 請確認 GOOGLE_API_KEY 已設定且 Gemini API 呼叫成功，以使用真實 LLM。")
    else:
        print("結論: Embedding 與 LLM 皆為真實 API，未使用 Stub。")
    print("=" * 60)


if __name__ == "__main__":
    main()
