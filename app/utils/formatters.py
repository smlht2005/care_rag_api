"""
格式化工具函數
"""
from typing import Dict, Any, List
from datetime import datetime

def format_query_response(result: Dict[str, Any]) -> Dict[str, Any]:
    """格式化查詢回應"""
    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "query": result.get("query", ""),
        "timestamp": datetime.now().isoformat()
    }

def format_error_response(error: str, detail: str = None) -> Dict[str, Any]:
    """格式化錯誤回應"""
    return {
        "error": error,
        "detail": detail,
        "timestamp": datetime.now().isoformat()
    }

def format_sources(sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """格式化來源列表"""
    return [
        {
            "id": src.get("id", ""),
            "content": src.get("content", ""),
            "score": src.get("score", 0.0),
            "metadata": src.get("metadata", {})
        }
        for src in sources
    ]


