"""
RAG 查詢服務
更新時間：2026-03-10
作者：AI Assistant
修改摘要：偵測 Stub 回應（[Gemini Stub] 等），改從來源擷取答案，使 IC [01] 等正確回傳「資料型態檢核錯誤」
更新時間：2026-03-10
作者：AI Assistant
修改摘要：有來源但 LLM 回「未找到」時，改從檢索來源擷取答案（fallback），修正 IC 錯誤碼等有來源卻回未找到
更新時間：2026-03-09
作者：AI Assistant
修改摘要：新增 RAG context 日誌（sources 數、prompt 長度、first_source_preview）方便排查有來源卻回未找到
更新時間：2026-03-09
作者：AI Assistant
修改摘要：僅依 RAG 來源回答；無匹配來源時回傳「未找到」，不讓 LLM 泛答
更新時間：2025-12-26 12:30
作者：AI Assistant
修改摘要：修復快取鍵生成，使用安全的快取鍵工具函數
"""
import asyncio
import logging
import re
from typing import Dict, List, Any
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.vector_service import VectorService
from app.utils.cache_utils import generate_cache_key

# 無匹配來源時的回應文案（不可由 LLM 泛答）
NO_MATCH_MESSAGE = "未找到"

# Stub 回應特徵（LLM 降級時回傳整段 prompt + 固定文案，非真正答案）
_STUB_MARKERS = ("[Gemini Stub]", "[OpenAI Stub]", "[DeepSeek Stub]")


def _is_stub_response(answer: str) -> bool:
    """判斷是否為 Stub 回應（非真實 LLM 答案，應改從來源擷取）。"""
    if not answer or not answer.strip():
        return False
    return any(m in answer for m in _STUB_MARKERS)


def _fallback_answer_from_sources(sources: List[Dict[str, Any]], query: str) -> str:
    """
    當 LLM 回「未找到」但有來源時，從檢索結果擷取答案。
    優先使用 QA 的 answer 欄位；若查詢含錯誤代碼如 [01]，遍歷來源找對應行或 answer。
    """
    if not sources:
        return NO_MATCH_MESSAGE
    code_match = re.search(r"\[\s*(\d+)\s*\]", query)
    code = code_match.group(1) if code_match else None
    if code:
        for s in sources:
            meta = s.get("metadata") or {}
            props = meta.get("properties") or {}
            if isinstance(props.get("answer"), str) and props["answer"].strip():
                q = str(props.get("question") or "")
                if code in q or "[" + code + "]" in q:
                    return props["answer"].strip()
            content = _source_to_text(s)
            for line in content.split("\n"):
                line = line.strip()
                if re.match(r"\[\s*" + re.escape(code) + r"\s*\]\s*[:：]", line) or (
                    "[" + code + "]" in line and ("：" in line or ":" in line)
                ):
                    return line
    first = sources[0]
    meta = first.get("metadata") or {}
    props = meta.get("properties") or {}
    if isinstance(props.get("answer"), str) and props["answer"].strip():
        return props["answer"].strip()
    content = _source_to_text(first)
    if not content:
        return NO_MATCH_MESSAGE
    lines = [ln.strip() for ln in content.split("\n") if ln.strip()]
    if lines:
        return lines[0][:500] if len(lines[0]) > 500 else lines[0]
    return content[:500].strip() or NO_MATCH_MESSAGE


def _source_to_text(s: Dict[str, Any]) -> str:
    """從單一 source 取得用於上下文的文字。"""
    if isinstance(s.get("content"), str):
        return (s.get("content") or "").strip()
    if isinstance(s.get("text"), str):
        return (s.get("text") or "").strip()
    return str(s)[:2000]

def _build_context_prompt(sources: List[Dict[str, Any]], query: str) -> str:
    """依參考資料與問題組出僅依來源回答的 prompt。"""
    parts = []
    for i, s in enumerate(sources, 1):
        text = _source_to_text(s)
        if text:
            parts.append(f"[參考 {i}]\n{text}")
    context = "\n\n---\n\n".join(parts) if parts else ""
    return (
        "請僅根據以下「參考資料」回答問題。若參考資料中沒有與問題相關的內容，請只回答「未找到」，不要推測或泛答。\n\n"
        "參考資料：\n" + context + "\n\n"
        "問題：" + query + "\n\n"
        "回答："
    )

class RAGService:
    """RAG 查詢服務"""

    def __init__(
        self, 
        llm_service: LLMService, 
        cache_service: CacheService,
        vector_service: VectorService = None
    ):
        self.llm = llm_service
        self.cache = cache_service
        self.vector = vector_service
        self.logger = logging.getLogger("RAGService")

    async def query(self, query: str, top_k: int = 3, skip_cache: bool = False) -> Dict:
        """查詢 RAG：僅在有來源時依來源生成回答，無來源則回傳「未找到」。"""
        try:
            # 檢查快取（使用安全的快取鍵生成；skip_cache 時略過）
            if not skip_cache:
                cache_key = generate_cache_key("rag_query", query, top_k=top_k)
                cached = await self.cache.get(cache_key)
                if cached:
                    self.logger.debug(f"RAG cache hit for query: {query[:50]}...")
                    return cached

            # 向量檢索（如果可用）
            sources = []
            if self.vector:
                sources = await self.vector.search(query, top_k=top_k)
            
            await asyncio.sleep(0.1)
            
            # 無來源時僅回傳「未找到」，不呼叫 LLM
            if not sources:
                result = {
                    "answer": NO_MATCH_MESSAGE,
                    "sources": [],
                    "query": query
                }
                if not skip_cache:
                    cache_key = generate_cache_key("rag_query", query, top_k=top_k)
                    await self.cache.set(cache_key, result, ttl=3600)
                return result
            
            # 有來源時依參考資料生成回答（日誌：來源 id 列表與預覽，方便排查「有來源卻未找到」根因）
            source_ids = [s.get("id") for s in sources]
            prompt = _build_context_prompt(sources, query)
            first_content = _source_to_text(sources[0]) if sources else ""
            self.logger.info(
                f"RAG context: {len(sources)} sources, source_ids={source_ids}, prompt_len={len(prompt)}, "
                f"first_source_preview={repr(first_content[:250])}"
            )
            answer = await self.llm.generate(prompt, max_tokens=2000)
            answer = answer.strip() or NO_MATCH_MESSAGE
            if sources and (answer == NO_MATCH_MESSAGE or _is_stub_response(answer)):
                if _is_stub_response(answer):
                    self.logger.warning(
                        f"RAG 偵測到 Stub 回應，source_ids={source_ids}，改從來源擷取答案"
                    )
                else:
                    self.logger.warning(
                        f"RAG 有來源但 LLM 回「未找到」，source_ids={source_ids}，將嘗試從來源擷取 fallback"
                    )
                answer = _fallback_answer_from_sources(sources, query)
            result = {
                "answer": answer,
                "sources": sources,
                "query": query
            }
            if not skip_cache:
                cache_key = generate_cache_key("rag_query", query, top_k=top_k)
                await self.cache.set(cache_key, result, ttl=3600)
            return result
            
        except Exception as e:
            self.logger.error(f"RAG query error: {str(e)}")
            raise

    async def retrieve(self, query: str, top_k: int = 3) -> Dict:
        """僅做向量檢索，不回傳 answer、不呼叫 LLM。供編排器在圖增強前取得來源，合併後只呼叫一次 LLM。"""
        sources = []
        if self.vector:
            sources = await self.vector.search(query, top_k=top_k)
        return {"sources": sources, "query": query}

    async def generate_answer_from_sources(
        self, sources: List[Dict[str, Any]], query: str
    ) -> str:
        """依合併後的 RAG 來源生成回答；僅用於編排器在合併圖與向量來源後呼叫。"""
        if not sources:
            return NO_MATCH_MESSAGE
        prompt = _build_context_prompt(sources, query)
        answer = await self.llm.generate(prompt, max_tokens=2000)
        answer = answer.strip() or NO_MATCH_MESSAGE
        if sources and (answer == NO_MATCH_MESSAGE or _is_stub_response(answer)):
            answer = _fallback_answer_from_sources(sources, query)
        return answer

    async def stream_query(self, query: str):
        """串流查詢 RAG"""
        try:
            # 模擬串流生成
            chunks = [
                f"這是關於「{query}」的回答片段 1",
                f"這是關於「{query}」的回答片段 2",
                f"這是關於「{query}」的回答片段 3"
            ]
            
            for chunk in chunks:
                await asyncio.sleep(0.2)
                yield chunk
                
        except Exception as e:
            self.logger.error(f"Stream query error: {str(e)}")
            raise

