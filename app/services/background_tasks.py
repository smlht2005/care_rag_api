"""
背景任務服務
"""
import asyncio
import logging
from typing import Callable, Any
from app.services.vector_service import VectorService

class BackgroundTaskService:
    """背景任務服務"""

    def __init__(self):
        self.tasks = []
        self.logger = logging.getLogger("BackgroundTaskService")

    async def add_task(self, func: Callable, *args, **kwargs):
        """新增背景任務"""
        task = asyncio.create_task(func(*args, **kwargs))
        self.tasks.append(task)
        self.logger.info(f"Background task added: {func.__name__}")
        return task

    async def process_documents(self, documents: list):
        """處理文件（背景任務）"""
        vector_service = VectorService()
        try:
            result = await vector_service.add_documents(documents)
            self.logger.info(f"Background document processing completed: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Background task error: {str(e)}")
            raise

    async def cleanup_old_cache(self):
        """清理舊快取（背景任務）"""
        # stub 實作
        self.logger.info("Background cache cleanup started")
        await asyncio.sleep(1)
        self.logger.info("Background cache cleanup completed")


