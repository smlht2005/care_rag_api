"""
整合測試腳本
更新時間：2025-12-26 12:08
作者：AI Assistant
修改摘要：測試整合後的新功能
"""
import sys
import os
import asyncio

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_llm_service():
    """測試 LLMService 重構"""
    print("=" * 60)
    print("測試 LLMService 重構")
    print("=" * 60)
    
    try:
        from app.services.llm_service import LLMService, BaseLLM, GeminiLLM, DeepSeekLLM, OpenAILLM
        
        # 測試 BaseLLM 抽象類別
        print("✅ BaseLLM 抽象類別導入成功")
        
        # 測試各 provider 實作
        gemini = GeminiLLM()
        deepseek = DeepSeekLLM()
        openai = OpenAILLM()
        print("✅ 各 provider 實作創建成功")
        
        # 測試 LLMService
        llm_service = LLMService()
        print(f"✅ LLMService 創建成功，當前 provider: {llm_service.provider}")
        
        # 測試 generate 方法
        result = await llm_service.generate("測試問題", max_tokens=100)
        print(f"✅ generate 方法測試成功: {result[:50]}...")
        
        # 測試 set_provider
        llm_service.set_provider("deepseek")
        print(f"✅ set_provider 測試成功，新 provider: {llm_service.provider}")
        
        # 測試 generate_chunk
        chunks = []
        async for chunk in llm_service.generate_chunk("測試問題"):
            chunks.append(chunk)
        print(f"✅ generate_chunk 測試成功，產生 {len(chunks)} 個片段")
        
        print("\n✅ LLMService 重構測試通過！\n")
        return True
        
    except Exception as e:
        print(f"❌ LLMService 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_orchestrator():
    """測試 GraphOrchestrator 改進"""
    print("=" * 60)
    print("測試 GraphOrchestrator 改進")
    print("=" * 60)
    
    try:
        from app.core.orchestrator import GraphOrchestrator
        from app.services.rag_service import RAGService
        from app.services.cache_service import CacheService
        from app.services.llm_service import LLMService
        from app.services.vector_service import VectorService
        
        # 創建服務
        llm = LLMService()
        cache = CacheService()
        vector = VectorService()
        rag = RAGService(llm, cache, vector)
        
        # 測試 GraphOrchestrator 創建（不包含 graph_store）
        orchestrator = GraphOrchestrator(rag, None, cache)
        print("✅ GraphOrchestrator 創建成功（無 graph_store）")
        
        # 測試 query 方法
        result = await orchestrator.query("測試查詢", top_k=3)
        print(f"✅ query 方法測試成功")
        print(f"   答案: {result.get('answer', '')[:50]}...")
        print(f"   來源數: {len(result.get('sources', []))}")
        print(f"   圖增強: {result.get('graph_enhanced', False)}")
        
        print("\n✅ GraphOrchestrator 改進測試通過！\n")
        return True
        
    except Exception as e:
        print(f"❌ GraphOrchestrator 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_endpoints():
    """測試新端點導入"""
    print("=" * 60)
    print("測試新端點導入")
    print("=" * 60)
    
    try:
        from app.api.v1.endpoints import knowledge, webhook, admin
        print("✅ knowledge 端點導入成功")
        print("✅ webhook 端點導入成功")
        print("✅ admin 端點導入成功")
        
        # 測試 router 導入
        from app.api.v1.router import router
        print("✅ router 導入成功")
        
        print("\n✅ 新端點導入測試通過！\n")
        return True
        
    except Exception as e:
        print(f"❌ 端點導入測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_schemas():
    """測試新 Schema 導入"""
    print("=" * 60)
    print("測試新 Schema 導入")
    print("=" * 60)
    
    try:
        from app.api.v1.schemas.knowledge import (
            KnowledgeQueryRequest,
            KnowledgeQueryResponse,
            KnowledgeIngestRequest
        )
        print("✅ knowledge schemas 導入成功")
        
        from app.api.v1.schemas.webhook import (
            WebhookEventRequest,
            WebhookEventResponse
        )
        print("✅ webhook schemas 導入成功")
        
        from app.api.v1.schemas.admin import (
            SystemStatsResponse,
            CacheClearResponse,
            GraphStatsResponse
        )
        print("✅ admin schemas 導入成功")
        
        print("\n✅ 新 Schema 導入測試通過！\n")
        return True
        
    except Exception as e:
        print(f"❌ Schema 導入測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("整合測試開始")
    print("=" * 60 + "\n")
    
    results = []
    
    # 執行各項測試
    results.append(await test_llm_service())
    results.append(await test_orchestrator())
    results.append(await test_endpoints())
    results.append(await test_schemas())
    
    # 總結
    print("=" * 60)
    print("整合測試總結")
    print("=" * 60)
    print(f"總測試數: {len(results)}")
    print(f"通過數: {sum(results)}")
    print(f"失敗數: {len(results) - sum(results)}")
    
    if all(results):
        print("\n✅ 所有整合測試通過！")
        return 0
    else:
        print("\n❌ 部分測試失敗，請檢查錯誤訊息")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


