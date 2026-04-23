"""
向量檢索服務
更新時間：2026-04-23 16:15
作者：AI Assistant
修改摘要：新增 IC alias 正規化：將「IC錯誤01 / IC卡錯誤01 / IC 01」改寫為標準「IC卡 [01]」，讓既有 IC QA 守衛可正確放行並命中對應 QA
更新時間：2026-04-22 15:16
作者：AI Assistant
修改摘要：新增 QA embedding 命中追蹤 log：輸出 query / QA_MIN_SCORE / top hits（entity_id、score、code、question），協助定位「非 IC 查詢卻命中 IC 錯誤 QA」等誤匹配來源
更新時間：2026-03-20 12:10
作者：AI Assistant
修改摘要：_search_from_graph 改呼叫 search_entities(..., include_type_match=False) 僅比對實體 name，避免 Organization 等 token 命中 type 假陽性；graph 來源 score 改為較低常數並於 metadata 標示 score_source=graph_keyword（見 docs/bug/missfind.md）
更新時間：2026-03-11 10:30
作者：AI Assistant
修改摘要：重構 IC 代碼查詢邏輯，新增 _extract_ic_code() 統一前處理器，以「IC 卡上下文 + 代碼格式」為唯一判斷依據，完全移除對中文語境詞彙的依賴，修正 AD61 裸碼不同說法查詢失敗問題
更新時間：2026-03-11 10:05
作者：AI Assistant
修改摘要：Fix 1 _try_get_ic_field_qa_source 移除「欄位」文字守衛，支援 [D12]/<D12>/裸碼 D12；Fix 2 _try_get_ic_error_qa_source 加入 MDHVE 欄位碼守衛；Fix 3 新增裸碼錯誤代碼偵測（如 AD61）
更新時間：2026-03-10
作者：AI Assistant
修改摘要：查詢含 IC 錯誤代碼如 [01] / [C001] 時，優先從 graph 取得對應 doc_thisqa_ic_error_qa_{CODE} 並置頂，確保正確答案在檢索結果中；entity id 與建圖腳本統一改為以錯誤碼為主（非序號）
更新時間：2026-03-09 17:40
作者：AI Assistant
修改摘要：VectorService.search 改為優先使用 QAEmbeddingIndex + EmbeddingService 進行語意檢索，再 fallback graph keyword / stub
更新時間：2026-03-09 15:22
作者：AI Assistant
修改摘要：新增 QA 向量索引 stub（依 QA Entity token 相似度檢索），優先用於 /api/v1/query，再保留 graph keyword 檢索與 stub 後備
更新時間：2026-03-09
作者：AI Assistant
修改摘要：無真實向量庫時改由 GraphStore 檢索，回傳圖實體作為來源，解決 stub 導致一律「未找到」
"""
import asyncio
import logging
import re
from typing import List, Dict, Optional, Any

from app.services.embedding_service import get_default_embedding_service, BaseEmbeddingService
from app.services.qa_embedding_index import QAEmbeddingIndex
from app.config import settings

# IC 錯誤代碼 QA 實體 id 前綴（與 process_thisqa_to_graph.py / 設定檔一致）
IC_ERROR_QA_ID_PREFIX = settings.GRAPH_IC_ERROR_QA_ENTITY_ID_PREFIX

# 預先編譯的正則（模組級別，只編譯一次）
_IC_CONTEXT_RE = re.compile(r"IC\s*卡|IC卡", re.IGNORECASE)
_CODE_BRACKET_RE = re.compile(r"\[\s*([A-Za-z0-9]+)\s*\]")
_CODE_ANGLE_RE = re.compile(r"<\s*([A-Za-z0-9]+)\s*>")
_CODE_BARE_RE = re.compile(r"\b([A-Za-z]{1,2}\d{2,4}|\d{2,4})\b")
_FIELD_CODE_RE = re.compile(r"^[MDHVE]\d{2}$", re.IGNORECASE)
_IC_ALIAS_CONTEXT_RE = re.compile(r"(IC\s*錯誤|IC錯誤|IC\s*error|ICerror|\bIC\b)", re.IGNORECASE)
_IC_ALIAS_CODE_RE = re.compile(r"([A-Za-z]{1,2}\d{2,4}|\d{1,4})", re.IGNORECASE)


def _extract_ic_code(query: str) -> tuple:
    """
    從 IC 相關查詢中提取代碼並分類。
    前提：查詢需含 IC 卡上下文（'IC卡' / 'IC 卡'）。
    返回 (code, code_type)：
      - code_type = 'field'  → 欄位代碼（MDHVE + 2位數字，如 D12、M01）
      - code_type = 'error'  → 錯誤代碼（其他格式，如 AD61、01、C001）
      - code_type = ''       → 未找到代碼或無 IC 卡上下文
    代碼格式偵測優先順序：[CODE] > <CODE> > 裸碼
    """
    if not query or not _IC_CONTEXT_RE.search(query):
        return None, ""
    m = (
        _CODE_BRACKET_RE.search(query)
        or _CODE_ANGLE_RE.search(query)
        or _CODE_BARE_RE.search(query)
    )
    if not m:
        return None, ""
    code = re.sub(r"\s+", "", m.group(1)).upper()
    if not code:
        return None, ""
    code_type = "field" if _FIELD_CODE_RE.match(code) else "error"
    return code, code_type


def _normalize_ic_alias_query(query: str) -> tuple[str, Optional[str]]:
    """
    IC alias 正規化（方案 3-B）：將常見輸入改寫為標準格式，避免守衛誤擋。

    例：
    - IC錯誤01 / IC卡錯誤01 / IC 01  -> IC卡 [01]
    - IC錯誤D039                    -> IC卡 [D039]

    僅在「看起來是 IC 類 query 且能抽出代碼」時改寫；否則保持原樣。
    回傳 (normalized_query, reason)。reason=None 表示未改寫。
    """
    raw = (query or "").strip()
    if not raw:
        return raw, None
    # 若已含標準 IC 卡上下文，交給既有 _extract_ic_code()，不重複改寫
    if _IC_CONTEXT_RE.search(raw):
        return raw, None
    # 只在「明顯是 IC 類」時才嘗試（避免誤改寫）
    if not _IC_ALIAS_CONTEXT_RE.search(raw):
        return raw, None
    # 必須能抽出代碼才改寫（避免把「IC卡錯誤」但無代碼的句子改壞）
    m = _CODE_BRACKET_RE.search(raw) or _CODE_ANGLE_RE.search(raw) or _IC_ALIAS_CODE_RE.search(raw)
    if not m:
        return raw, None
    code = re.sub(r"\s+", "", m.group(1)).upper()
    if not code:
        return raw, None
    return f"IC卡 [{code}]", f"ic_alias:{code}"


class VectorService:
    """向量檢索：優先使用 QA embedding 索引，其次使用圖實體 keyword 檢索，最後回退 stub。"""

    def __init__(self, graph_store: Optional[Any] = None):
        self.logger = logging.getLogger("VectorService")
        self.graph_store = graph_store
        # 真正的 QA 向量索引 + EmbeddingService
        self._embedding: BaseEmbeddingService = get_default_embedding_service()
        self._qa_index = QAEmbeddingIndex("data/qa_vectors.db")

    async def _try_get_ic_error_qa_source(self, query: str) -> Optional[Dict[str, Any]]:
        """
        若查詢含「IC 卡」上下文且含錯誤代碼格式（如 [01]、[C001]、[AD61]、裸碼 AD61），
        從 graph 取得對應 IC QA 實體（doc_thisqa_ic_error_qa_01 等）並轉成 RAG 來源。
        判斷邏輯由 _extract_ic_code() 統一處理，不依賴中文語境詞彙。
        """
        if not self.graph_store or not query:
            return None
        code, code_type = _extract_ic_code(query)
        if not code or code_type != "error":
            return None
        entity_id = f"{IC_ERROR_QA_ID_PREFIX}{code}"
        try:
            e = await self.graph_store.get_entity(entity_id)
        except Exception:
            return None
        if not e:
            return None
        props = getattr(e, "properties", {}) or {}
        parts = []
        if isinstance(props.get("question"), str) and props["question"].strip():
            parts.append(props["question"].strip())
        if isinstance(props.get("answer"), str) and props["answer"].strip():
            parts.append(props["answer"].strip())
        content = "\n".join(parts).strip() or e.name
        return {
            "id": e.id,
            "content": content,
            "score": 1.0,
            "metadata": {"source": "ic_error_qa", "type": e.type, "properties": props},
        }

    async def _try_get_ic_field_qa_source(self, query: str) -> Optional[Dict[str, Any]]:
        """
        若查詢含「IC 卡」上下文且含欄位代碼格式（如 [D12]、<D12>、裸碼 D12），
        從 graph 取得對應欄位 QA1 實體（doc_thisqa_ic_field_D12 等）並轉成 RAG 來源。
        判斷邏輯由 _extract_ic_code() 統一處理，不依賴中文語境詞彙。
        """
        if not self.graph_store or not query:
            return None
        code, code_type = _extract_ic_code(query)
        if not code or code_type != "field":
            return None
        entity_id = f"doc_thisqa_ic_field_{code}"
        try:
            e = await self.graph_store.get_entity(entity_id)
        except Exception:
            return None
        if not e:
            return None
        props = getattr(e, "properties", {}) or {}
        parts = []
        if isinstance(props.get("question"), str) and props["question"].strip():
            parts.append(props["question"].strip())
        if isinstance(props.get("answer"), str) and props["answer"].strip():
            parts.append(props["answer"].strip())
        content = "\n".join(parts).strip() or e.name
        return {
            "id": e.id,
            "content": content,
            "score": 1.0,
            "metadata": {"source": "ic_field_qa", "type": e.type, "properties": props},
        }

    async def search(self, query: str, top_k: int = 3) -> List[Dict]:
        """檢索：若查詢含 IC 錯誤代碼或欄位代碼則優先帶回對應 QA1；其餘依 QA embedding / graph keyword / stub。"""
        normalized, reason = _normalize_ic_alias_query(query)
        if reason:
            self.logger.info("Normalized IC alias query: raw=%r normalized=%r reason=%s", (query or "")[:200], normalized, reason)
        query = normalized

        ic_error_source: Optional[Dict[str, Any]] = None
        ic_field_source: Optional[Dict[str, Any]] = None
        if query and self.graph_store:
            ic_error_source = await self._try_get_ic_error_qa_source(query)
            ic_field_source = await self._try_get_ic_field_qa_source(query)
        if ic_error_source:
            self.logger.info(f"Vector search: found IC error QA for query, prepending entity {ic_error_source.get('id')}")
        if ic_field_source:
            self.logger.info(f"Vector search: found IC field QA for query, candidate entity {ic_field_source.get('id')}")

        # 1) QA embedding 檢索
        try:
            if query and self.graph_store:
                qa_results = await self._search_from_qa_embeddings(query, top_k)
                if qa_results or ic_error_source or ic_field_source:
                    merged: List[Dict[str, Any]] = []
                    seen = set()
                    # 優先錯誤碼 QA1，再來欄位 QA1，最後是 embedding 結果
                    for src in (ic_error_source, ic_field_source):
                        if src and src.get("id") not in seen:
                            seen.add(src["id"])
                            merged.append(src)
                    for r in qa_results:
                        rid = r.get("id")
                        if rid not in seen:
                            seen.add(rid)
                            merged.append(r)
                    if merged:
                        merged = merged[:top_k]
                        self.logger.info(f"Vector search (qa_embedding + ic_special_qa): {len(merged)} results")
                        return merged
        except Exception as e:
            self.logger.warning(f"QA embedding search failed, fallback to graph/stub: {e}")

        # 2) graph keyword 檢索（若有 IC 來源也一併帶回）
        if self.graph_store:
            try:
                results = await self._search_from_graph(query, top_k)
                if ic_error_source or ic_field_source:
                    seen = set()
                    merged: List[Dict[str, Any]] = []
                    for src in (ic_error_source, ic_field_source):
                        if src and src.get("id") not in seen:
                            seen.add(src["id"])
                            merged.append(src)
                    for r in results:
                        rid = r.get("id")
                        if rid not in seen:
                            seen.add(rid)
                            merged.append(r)
                    results = merged[:top_k]
                self.logger.info(f"Vector search (graph): {len(results)} results")
                return results
            except Exception as e:
                self.logger.warning(f"Graph keyword search failed, fallback to stub: {e}")

        # 3) 僅有 IC 特殊來源時也直接回傳
        if ic_error_source or ic_field_source:
            results: List[Dict[str, Any]] = []
            for src in (ic_error_source, ic_field_source):
                if src:
                    results.append(src)
            return results[:top_k]

        # 4) stub
        return await self._stub_search(top_k)

    async def _search_from_qa_embeddings(self, query: str, top_k: int) -> List[Dict]:
        """使用 embedding + QAEmbeddingIndex 進行語意檢索，回傳 QA Entity 來源。"""
        # 產生 query embedding
        embs = await self._embedding.embed([query])
        if not embs or not embs[0]:
            return []
        query_emb = embs[0]

        # 從 QA 向量索引搜尋 entity_id + score + metadata（帶相似度門檻過濾低相關結果）
        hits = self._qa_index.search(query_emb, top_k=top_k, min_score=settings.QA_MIN_SCORE)
        if not hits:
            return []

        if not self.graph_store:
            return []

        has_ic_context = bool(query and _IC_CONTEXT_RE.search(query))
        ic_code, ic_code_type = _extract_ic_code(query or "")
        results: List[Dict[str, Any]] = []
        for entity_id, score, meta in hits:
            try:
                e = await self.graph_store.get_entity(entity_id)
            except Exception:
                e = None
            if not e:
                continue
            props = getattr(e, "properties", {}) or {}
            parts = []
            q = props.get("question")
            a = props.get("answer")
            if isinstance(q, str) and q.strip():
                parts.append(q.strip())
            if isinstance(a, str) and a.strip():
                parts.append(a.strip())
            content = "\n".join(parts).strip() or e.name
            results.append(
                {
                    "id": e.id,
                    "content": content,
                    "score": float(score),
                    "metadata": {"source": "qa_embedding", "type": e.type, "properties": props, **meta},
                }
            )

        # 方案 C：必須「IC 上下文 + 明確代碼」才允許 IC error/field QA（避免非 IC 查詢誤命中 IC QA）
        if results and not ic_code:
            before = len(results)
            results = [
                r
                for r in results
                if not (
                    str(r.get("id") or "").startswith("doc_thisqa_ic_error_qa_")
                    or str(r.get("id") or "").startswith("doc_thisqa_ic_field_")
                )
            ]
            filtered = before - len(results)
            if filtered > 0:
                self.logger.warning(
                    "QA embedding IC-guard filtered=%s query=%r (has_ic_context=%s, ic_code=%r, ic_code_type=%r)",
                    filtered,
                    (query or "")[:200],
                    has_ic_context,
                    ic_code,
                    ic_code_type,
                )

        if results:
            # Debug / observability：輸出 top hits，便於定位為何命中某筆 QA（尤其是非 IC 查詢卻命中 IC 錯誤 QA）
            preview = []
            for r in results[: min(5, len(results))]:
                p = (r.get("metadata") or {}).get("properties") or {}
                preview.append(
                    {
                        "id": r.get("id"),
                        "score": r.get("score"),
                        "code": p.get("code"),
                        "question": (str(p.get("question") or "")[:80] if p else "") or None,
                    }
                )
            self.logger.info(
                "QA embedding hits: query=%r qa_min_score=%s has_ic_context=%s top=%s",
                (query or "")[:200],
                settings.QA_MIN_SCORE,
                has_ic_context,
                preview,
            )
            # 非 IC 查詢卻命中 IC error QA：這通常代表 embedding 被「簽章/上傳/錯誤」語意吸引，需人工判斷是否該加守衛/別名/資料補強
            if not has_ic_context:
                top_id = str(results[0].get("id") or "")
                if top_id.startswith(f"{IC_ERROR_QA_ID_PREFIX}") or top_id.startswith("doc_thisqa_ic_error_qa_"):
                    top_props = ((results[0].get("metadata") or {}).get("properties") or {})
                    self.logger.warning(
                        "Non-IC query matched IC error QA: query=%r top_id=%s top_code=%s top_question=%r score=%s",
                        (query or "")[:200],
                        top_id,
                        top_props.get("code"),
                        str(top_props.get("question") or "")[:120],
                        results[0].get("score"),
                    )
        return results

    async def _search_from_graph(self, query: str, top_k: int) -> List[Dict]:
        """從 graph 依關鍵字搜尋實體，組成 RAG 來源格式。"""
        # 關鍵字：中文與英文/數字，取前幾個以增加命中
        keywords = re.findall(r"[\u4e00-\u9fff\w]+", query)
        if not keywords:
            keywords = [query[:20]] if query else []
        seen_ids: set = set()
        results: List[Dict] = []
        for kw in keywords[:5]:
            if len(results) >= top_k:
                break
            entities = await self.graph_store.search_entities(
                kw, limit=top_k, include_type_match=False
            )
            for e in entities:
                if e.id in seen_ids:
                    continue
                seen_ids.add(e.id)
                content_parts = [e.name]
                if e.properties:
                    for v in e.properties.values():
                        if isinstance(v, str) and v.strip():
                            content_parts.append(v.strip())
                        elif isinstance(v, (list, dict)) and str(v).strip():
                            content_parts.append(str(v)[:1500])
                content = "\n".join(content_parts) or e.name
                # 非向量相似度，僅供排序用；勿解讀為語意信心度
                results.append({
                    "id": e.id,
                    "content": content,
                    "score": 0.35,
                    "metadata": {
                        "source": "graph",
                        "score_source": "graph_keyword",
                        "type": e.type,
                        "properties": e.properties,
                    },
                })
                if len(results) >= top_k:
                    break
        return results[:top_k]

    async def _stub_search(self, top_k: int) -> List[Dict]:
        """Stub：模擬檢索結果（無真實向量庫且無 graph 時）。"""
        await asyncio.sleep(0.05)
        results = [
            {
                "id": f"doc_{i}",
                "content": f"相關文件內容 {i}",
                "score": 0.9 - (i * 0.1),
                "metadata": {"source": f"source_{i}.pdf", "page": i + 1},
            }
            for i in range(top_k)
        ]
        self.logger.info(f"Vector search (stub) returned {len(results)} results")
        return results

    async def add_documents(self, documents: List[Dict]):
        """新增文件到向量資料庫（stub）。"""
        self.logger.info(f"Adding {len(documents)} documents to vector store")
        await asyncio.sleep(0.1)
        return {"status": "success", "count": len(documents)}

    async def delete_documents(self, document_ids: List[str]):
        """刪除文件（stub）。"""
        self.logger.info(f"Deleting {len(document_ids)} documents")
        await asyncio.sleep(0.1)
        return {"status": "success", "count": len(document_ids)}
