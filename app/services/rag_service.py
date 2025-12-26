"""
RAG 查詢服務
更新時間：2025-12-26 12:30
作者：AI Assistant
修改摘要：修復快取鍵生成，使用安全的快取鍵工具函數
"""
import asyncio
import logging
from typing import Dict, List
from app.services.llm_service import LLMService
from app.services.cache_service import CacheService
from app.services.vector_service import VectorService
from app.utils.cache_utils import generate_cache_key

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

    async def query(self, query: str, top_k: int = 3) -> Dict:
        """查詢 RAG"""
        try:
            # 檢查快取（使用安全的快取鍵生成）
            cache_key = generate_cache_key("rag_query", query, top_k=top_k)
            cached = await self.cache.get(cache_key)
            if cached:
                self.logger.debug(f"RAG cache hit for query: {query[:50]}...")
                return cached
            
            # 向量檢索（如果可用）
            sources = []
            if self.vector:
                sources = await self.vector.search(query, top_k=top_k)
            
            # 模擬向量檢索延遲
            await asyncio.sleep(0.1)
            
            # LLM 生成回答
            answer = await self.llm.generate(query, max_tokens=2000)
            
            result = {
                "answer": answer,
                "sources": sources,
                "query": query
            }
            
            # 存入快取（使用相同的快取鍵）
            await self.cache.set(cache_key, result, ttl=3600)
            
            return result
            
        except Exception as e:
            self.logger.error(f"RAG query error: {str(e)}")
            raise

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

