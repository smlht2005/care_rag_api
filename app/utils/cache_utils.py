"""
快取工具函數
更新時間：2025-12-26 12:15
作者：AI Assistant
修改摘要：創建安全的快取鍵生成函數
"""
import hashlib
import json
from typing import Any, Dict, Optional


def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    生成安全的快取鍵
    
    使用 MD5 雜湊確保鍵的唯一性和安全性，避免特殊字元衝突
    
    Args:
        prefix: 快取鍵前綴
        *args: 位置參數
        **kwargs: 關鍵字參數
    
    Returns:
        格式化的快取鍵: {prefix}:{hash}
    
    Example:
        >>> generate_cache_key("graphrag_query", "測試問題", top_k=3)
        'graphrag_query:a1b2c3d4e5f6...'
    """
    # 構建鍵數據
    key_data: Dict[str, Any] = {}
    
    # 添加位置參數
    if args:
        key_data["args"] = list(args)
    
    # 添加關鍵字參數
    if kwargs:
        key_data.update(kwargs)
    
    # 轉換為 JSON 字串並排序鍵以確保一致性
    key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
    
    # 生成 MD5 雜湊
    key_hash = hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    return f"{prefix}:{key_hash}"


