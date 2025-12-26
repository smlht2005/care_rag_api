"""
統一錯誤處理工具
更新時間：2025-12-26 12:15
作者：AI Assistant
修改摘要：創建統一的錯誤處理裝飾器和工具函數
"""
from functools import wraps
from fastapi import HTTPException, status
from fastapi.responses import JSONResponse
from typing import Callable, Any
import logging

logger = logging.getLogger("ErrorHandler")


def handle_errors(func: Callable) -> Callable:
    """
    統一錯誤處理裝飾器
    
    處理各種異常類型並返回適當的 HTTP 回應：
    - HTTPException: 直接拋出
    - ValueError: 返回 400 Bad Request
    - KeyError: 返回 400 Bad Request
    - 其他異常: 返回 500 Internal Server Error
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            # FastAPI 的 HTTPException 直接拋出
            raise
        except ValueError as e:
            logger.warning(f"ValueError in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid input: {str(e)}"
            )
        except KeyError as e:
            logger.warning(f"KeyError in {func.__name__}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )
    return wrapper


def create_error_response(
    status_code: int,
    message: str,
    detail: Any = None
) -> JSONResponse:
    """
    創建標準錯誤回應
    
    Args:
        status_code: HTTP 狀態碼
        message: 錯誤訊息
        detail: 詳細錯誤資訊
    
    Returns:
        JSONResponse 物件
    """
    content = {
        "error": message,
        "status_code": status_code
    }
    
    if detail:
        content["detail"] = str(detail)
    
    return JSONResponse(
        status_code=status_code,
        content=content
    )


