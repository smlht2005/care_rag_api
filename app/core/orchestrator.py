"""
GraphRAG 編排器
更新時間：2026-04-01 10:24
作者：AI Assistant
修改摘要：在最終 sources 合併後統一以 QA_MIN_SCORE 過濾所有路徑（含 graph keyword / 圖增強），避免低分來源繞過門檻仍被送進 LLM 產出答案
更新時間：2026-03-11
作者：AI Assistant
修改摘要：有圖時改為「只檢索不生成」+ 圖增強後一次 LLM，避免 RAG 先生成再圖增強又生成的重複呼叫
更新時間：2026-03-09
作者：AI Assistant
修改摘要：僅依 RAG 來源回答；無來源時回傳「未找到」，有來源時依合併來源重新生成答案
更新時間：2025-12-26 12:30
作者：AI Assistant
修改摘要：修復圖查詢邏輯錯誤，添加實體語義匹配、關係查詢、並行處理、動態權重計算
"""
import logging
import asyncio
from typing import Dict, List, Optional, Any, TypedDict, Set
from app.services.rag_service import (
    RAGService,
    NO_MATCH_MESSAGE,
    _is_stub_response,
    _fallback_answer_from_sources,
)
from app.services.cache_service import CacheService
from app.core.graph_store import GraphStore, Entity, Relation
from app.utils.cache_utils import generate_cache_key
from app.config import settings


class GraphEnhancementResult(TypedDict):
    """圖增強結果類型定義"""
    sources: List[Dict[str, Any]]
    entities: List[Entity]
    relations: List[Relation]

class GraphOrchestrator:
    """統籌 GraphRAG 查詢流程"""

    def __init__(
        self,
        rag_service: RAGService,
        graph_store: Optional[GraphStore] = None,
        cache_service: Optional[CacheService] = None
    ):
        self.rag_service = rag_service
        self.graph_store = graph_store
        self.cache_service = cache_service
        self.logger = logging.getLogger("GraphOrchestrator")

    async def query(self, query_text: str, top_k: int = 3, skip_cache: bool = False) -> Dict:
        """
        執行 GraphRAG 查詢
        
        流程：
        1. 檢查快取（skip_cache 時略過）-> 2. 向量檢索 -> 3. 圖查詢 -> 4. 結果融合 -> 5. LLM生成 -> 6. 快取結果（skip_cache 時不寫入）
        """
        try:
            self.logger.debug(f"GraphRAG query started: {query_text[:100]}..., skip_cache={skip_cache}")
            
            # 1. 檢查快取（chkgpt 設計，在 GraphRAG 層級快取完整結果）
            if self.cache_service and not skip_cache:
                cache_key = generate_cache_key("graphrag_query", query_text, top_k=top_k)
                cached = await self.cache_service.get(cache_key)
                if cached:
                    self.logger.debug(f"GraphRAG cache hit for query: {query_text[:50]}...")
                    return cached
                else:
                    self.logger.debug(f"GraphRAG cache miss for query: {query_text[:50]}...")
            
            # 2. 有圖時只做檢索（不呼叫 LLM）；無圖時走完整 RAG（檢索 + 一次 LLM），避免圖增強後重複呼叫 LLM
            if self.graph_store:
                result = await self.rag_service.retrieve(query_text, top_k=top_k)
            else:
                result = await self.rag_service.query(query_text, top_k=top_k, skip_cache=skip_cache)
            
            # 3. 圖查詢增強（僅當 GraphStore 可用）
            graph_enhanced_sources = []
            graph_entities = []
            graph_relations = []
            
            if self.graph_store:
                try:
                    graph_results = await self._enhance_with_graph(
                        query_text,
                        result.get("sources", [])
                    )
                    graph_enhanced_sources = graph_results.get("sources", [])
                    graph_entities = graph_results.get("entities", [])
                    graph_relations = graph_results.get("relations", [])
                except Exception as e:
                    # 錯誤恢復：降級到純向量檢索
                    self.logger.warning(
                        f"Graph enhancement failed, falling back to vector search: {str(e)}",
                        exc_info=True
                    )
                    graph_results = GraphEnhancementResult(
                        sources=[],
                        entities=[],
                        relations=[]
                    )
            
            # 4. 融合結果並排序
            if graph_enhanced_sources:
                # 合併向量和圖結果，去重
                all_sources = result.get("sources", [])
                source_ids: Set[str] = {s.get("id") for s in all_sources if s.get("id")}
                
                for graph_source in graph_enhanced_sources:
                    if graph_source.get("id") not in source_ids:
                        all_sources.append(graph_source)
                        source_ids.add(graph_source.get("id"))
                
                # 按分數排序（問題 8）
                all_sources.sort(key=lambda x: x.get("score", 0.0), reverse=True)
                result["sources"] = all_sources[:top_k]  # 只返回 top_k
                result["graph_enhanced"] = True
            
            # 4.1 統一以 QA_MIN_SCORE 過濾所有路徑的低分來源（含 graph keyword / 圖增強）
            final_sources = result.get("sources", [])
            final_sources = [s for s in final_sources if s.get("score", 0.0) >= settings.QA_MIN_SCORE]
            result["sources"] = final_sources

            # 4.2 設定 answer：無來源則「未找到」；有圖時為 retrieve 路徑，只在此呼叫一次 LLM
            if not final_sources:
                result["answer"] = NO_MATCH_MESSAGE
            elif self.graph_store:
                # 有圖：本次為 retrieve 路徑，尚未呼叫 LLM，在此只呼叫一次
                result["answer"] = await self.rag_service.generate_answer_from_sources(
                    final_sources, query_text
                )
            # 無圖：result 來自 rag.query()，已含 answer，不重複呼叫

            # 安全網：若最終 answer 仍為 Stub 回應（例如 RAG 層未替換），改從來源擷取
            if final_sources and _is_stub_response(result.get("answer", "")):
                self.logger.warning("Orchestrator 偵測到 Stub 回應，改從來源擷取答案")
                result["answer"] = _fallback_answer_from_sources(final_sources, query_text)
            
            # 添加圖結構資訊
            if graph_entities:
                result["graph_entities"] = [e.to_dict() if hasattr(e, 'to_dict') else e for e in graph_entities]
            if graph_relations:
                result["graph_relations"] = [r.to_dict() if hasattr(r, 'to_dict') else r for r in graph_relations]
            
            # 5. 快取結果（在 GraphRAG 層級；skip_cache 時不寫入）
            if self.cache_service and not skip_cache:
                cache_key = generate_cache_key("graphrag_query", query_text, top_k=top_k)
                await self.cache_service.set(cache_key, result, ttl=settings.GRAPH_CACHE_TTL)
            
            self.logger.info(
                f"GraphRAG query completed: {len(result.get('sources', []))} sources, "
                f"graph_enhanced={bool(graph_enhanced_sources)}"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"GraphRAG orchestration error: {str(e)}")
            raise

    async def _enhance_with_graph(
        self,
        query_text: str,
        vector_sources: List[Dict[str, Any]]
    ) -> GraphEnhancementResult:
        """
        使用圖結構增強檢索結果
        
        修復邏輯：
        1. 從向量結果提取文檔 ID（不是實體 ID）
        2. 通過 CONTAINS 關係找到文檔中的實體
        3. 使用查詢文本進行實體語義搜索
        4. 並行查詢實體和關係
        5. 動態計算權重
        """
        try:
            graph_sources = []
            graph_entities: List[Entity] = []
            graph_relations: List[Relation] = []
            entity_set: Set[str] = set()  # 用於去重
            
            # 1. 從向量結果中提取文檔 ID（問題 1 修復）
            doc_ids = [s.get("id", "") for s in vector_sources if s.get("id")]
            
            if not doc_ids:
                return GraphEnhancementResult(
                    sources=[],
                    entities=[],
                    relations=[]
                )
            
            # 2 + 3. 同步建立所有協程（不 await），然後一次 gather 真正並行執行
            all_doc_tasks: List[Any] = []
            for doc_id in doc_ids[:settings.GRAPH_QUERY_MAX_ENTITIES]:
                all_doc_tasks.append(self.graph_store.get_entity(doc_id))
                all_doc_tasks.append(
                    self.graph_store.get_neighbors(
                        doc_id,
                        relation_type="CONTAINS",
                        direction="outgoing",
                    )
                )

            # 4. 所有任務（search_entities + doc 查詢）同時發起
            all_results = await asyncio.gather(
                self.graph_store.search_entities(
                    query_text,
                    limit=settings.GRAPH_QUERY_MAX_ENTITIES,
                ),
                *all_doc_tasks,
                return_exceptions=True,
            )

            first = all_results[0]
            query_entities = first if isinstance(first, list) else []
            doc_results = all_results[1:]
            
            # 處理文檔實體結果（每兩個結果為一對：doc_entity, contains_entities）
            doc_entities: List[Entity] = []
            for i in range(0, len(doc_results), 2):
                # 文檔實體
                if i < len(doc_results):
                    doc_entity = doc_results[i]
                    if isinstance(doc_entity, Entity):
                        doc_entities.append(doc_entity)
                
                # 文檔包含的實體
                if i + 1 < len(doc_results):
                    contains_entities = doc_results[i + 1]
                    if isinstance(contains_entities, list):
                        doc_entities.extend(contains_entities)
            
            # 5. 合併實體（去重）
            all_entities = query_entities + doc_entities
            for entity in all_entities:
                if entity.id not in entity_set:
                    graph_entities.append(entity)
                    entity_set.add(entity.id)
            
            if not graph_entities:
                return GraphEnhancementResult(
                    sources=[],
                    entities=[],
                    relations=[]
                )
            
            # 6. 並行查詢實體的鄰居和關係（問題 4：並行處理）
            max_entities = settings.GRAPH_QUERY_MAX_ENTITIES
            max_neighbors = settings.GRAPH_QUERY_MAX_NEIGHBORS
            
            neighbor_tasks = []
            relation_tasks = []
            
            for entity in graph_entities[:max_entities]:
                # 查詢鄰居
                neighbor_tasks.append(
                    self.graph_store.get_neighbors(
                        entity.id,
                        direction="both"
                    )
                )
                # 查詢關係（問題 3：關係提取使用）
                relation_tasks.append(
                    self.graph_store.get_relations_by_entity(
                        entity.id,
                        direction="both"
                    )
                )
            
            # 並行執行
            neighbors_results = await asyncio.gather(
                *neighbor_tasks,
                return_exceptions=True
            )
            relations_results = await asyncio.gather(
                *relation_tasks,
                return_exceptions=True
            )
            
            # 7. 處理鄰居結果並計算動態權重（問題 5：動態權重）
            for neighbors in neighbors_results:
                if isinstance(neighbors, list):
                    for neighbor in neighbors[:max_neighbors]:
                        if neighbor.id not in entity_set:
                            graph_entities.append(neighbor)
                            entity_set.add(neighbor.id)
                            
                            # 計算動態權重
                            score = self._calculate_entity_score(neighbor, query_text)
                            # 圖來源 content：實體名稱 + properties 內文字，供 LLM 有足夠上下文回答（避免僅名稱時回「未找到」）
                            content_parts = [neighbor.name]
                            if neighbor.properties:
                                for v in neighbor.properties.values():
                                    if isinstance(v, str) and v.strip():
                                        content_parts.append(v.strip())
                                    elif isinstance(v, (list, dict)) and str(v).strip():
                                        content_parts.append(str(v)[:1500])
                            graph_content = "\n".join(content_parts) or neighbor.name
                            
                            graph_sources.append({
                                "id": neighbor.id,
                                "content": graph_content,
                                "score": score,  # 動態權重
                                "metadata": {
                                    "source": "graph",
                                    "type": neighbor.type,
                                    "properties": neighbor.properties
                                }
                            })
            
            # 8. 處理關係結果（問題 3：關係提取使用）
            for relations in relations_results:
                if isinstance(relations, list):
                    for relation in relations:
                        if relation not in graph_relations:
                            graph_relations.append(relation)
            
            return GraphEnhancementResult(
                sources=graph_sources,
                entities=graph_entities,
                relations=graph_relations
            )
            
        except Exception as e:
            self.logger.warning(f"Graph enhancement failed: {str(e)}", exc_info=True)
            return GraphEnhancementResult(
                sources=[],
                entities=[],
                relations=[]
            )
    
    def _calculate_entity_score(
        self,
        entity: Entity,
        query_text: str
    ) -> float:
        """
        計算實體與查詢的相關性分數（問題 5：動態權重計算）
        
        Args:
            entity: 實體
            query_text: 查詢文本
        
        Returns:
            相關性分數 (0.0 - 1.0)
        """
        query_lower = query_text.lower()
        entity_name_lower = entity.name.lower()
        entity_type_lower = entity.type.lower()
        
        # 完全匹配名稱
        if query_lower == entity_name_lower:
            return 0.95
        
        # 查詢包含在實體名稱中
        if query_lower in entity_name_lower:
            return 0.85
        
        # 實體名稱包含在查詢中
        if entity_name_lower in query_lower:
            return 0.80
        
        # 單詞匹配
        query_words = set(query_lower.split())
        entity_words = set(entity_name_lower.split())
        common_words = query_words.intersection(entity_words)
        
        if common_words:
            match_ratio = len(common_words) / max(len(query_words), 1)
            return 0.6 + (match_ratio * 0.2)  # 0.6 - 0.8
        
        # 類型匹配
        if query_lower in entity_type_lower or entity_type_lower in query_lower:
            return 0.65
        
        # 屬性匹配
        if entity.properties:
            for prop_value in entity.properties.values():
                if isinstance(prop_value, str) and query_lower in prop_value.lower():
                    return 0.70
        
        # 預設分數（圖結果的基礎權重）
        return 0.55

    async def stream_query(self, query_text: str):
        """串流 GraphRAG 查詢"""
        try:
            self.logger.debug(f"GraphRAG stream query started: {query_text[:100]}...")
            
            async for chunk in self.rag_service.stream_query(query_text):
                yield chunk
                
            self.logger.debug("GraphRAG stream query completed")
            
        except Exception as e:
            self.logger.error(f"GraphRAG stream orchestration error: {str(e)}")
            raise
