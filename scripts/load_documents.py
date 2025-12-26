"""
載入文件到向量資料庫腳本
"""
import asyncio
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_service import VectorService
from app.services.cache_service import CacheService
from app.services.llm_service import LLMService
from app.services.rag_service import RAGService

async def load_sample_documents():
    """載入範例文件"""
    vector_service = VectorService()
    
    sample_documents = [
        {
            "id": "doc_1",
            "content": "這是第一個範例文件內容",
            "metadata": {"source": "sample1.pdf", "page": 1},
            "source": "sample1.pdf"
        },
        {
            "id": "doc_2",
            "content": "這是第二個範例文件內容",
            "metadata": {"source": "sample2.pdf", "page": 1},
            "source": "sample2.pdf"
        },
        {
            "id": "doc_3",
            "content": "這是第三個範例文件內容",
            "metadata": {"source": "sample3.pdf", "page": 1},
            "source": "sample3.pdf"
        }
    ]
    
    print("正在載入範例文件...")
    result = await vector_service.add_documents(sample_documents)
    print(f"載入完成: {result}")
    
    return result

async def main():
    """主函數"""
    try:
        await load_sample_documents()
        print("文件載入腳本執行完成！")
    except Exception as e:
        print(f"錯誤: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

