# DateTime JSON 序列化錯誤

**更新時間：2025-12-26 18:03**  
**作者：AI Assistant**  
**修改摘要：記錄 datetime JSON 序列化錯誤和修復方案**

---

## 問題描述

當調用包含 `datetime` 欄位的 API 端點時，返回 `500 Internal Server Error`，錯誤訊息為：

```json
{
    "error": "Internal server error",
    "detail": "Object of type datetime is not JSON serializable"
}
```

## 受影響的端點

以下端點受到影響：

1. `GET /api/v1/admin/stats` - 系統統計
2. `GET /api/v1/admin/graph/stats` - 圖結構統計
3. `POST /api/v1/admin/cache/clear` - 清除快取
4. `POST /api/v1/knowledge/ingest` - 知識庫攝取

## 錯誤詳情

### 根本原因

Pydantic 的 `model_dump()` 方法預設返回 Python 原生物件，包括 `datetime` 物件。當使用 `JSONResponse(content=response.model_dump())` 時，FastAPI 嘗試將字典序列化為 JSON，但 Python 的 `datetime` 物件無法直接序列化為 JSON。

### 錯誤代碼範例

```python
# ❌ 錯誤的使用方式
response = SystemStatsResponse(
    timestamp=datetime.now()
)
return JSONResponse(content=response.model_dump())
# 導致：Object of type datetime is not JSON serializable
```

## 解決方案

### 方法 1：使用 `model_dump(mode='json')`（推薦）

Pydantic 的 `model_dump(mode='json')` 會將所有欄位轉換為 JSON 可序列化的格式：

```python
# ✅ 正確的使用方式
response = SystemStatsResponse(
    timestamp=datetime.now()
)
return JSONResponse(content=response.model_dump(mode='json'))
```

### 方法 2：直接返回 Pydantic 模型（更簡單）

FastAPI 會自動處理 Pydantic 模型的序列化，包括 `datetime`：

```python
# ✅ 更簡單的方式（推薦）
@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(...):
    response = SystemStatsResponse(
        timestamp=datetime.now()
    )
    return response  # FastAPI 自動序列化
```

### 方法 3：配置 Pydantic 的 JSON 編碼器

在 Pydantic 模型中配置 JSON 編碼器：

```python
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class SystemStatsResponse(BaseModel):
    model_config = ConfigDict(
        json_encoders={
            datetime: lambda v: v.isoformat()
        }
    )
    timestamp: datetime
```

## 修復內容

### 已修復的檔案

1. **`app/api/v1/endpoints/admin.py`**：
   - `get_system_stats()` - 使用 `model_dump(mode='json')`
   - `clear_cache()` - 使用 `model_dump(mode='json')`
   - `get_graph_stats()` - 使用 `model_dump(mode='json')`

2. **`app/api/v1/endpoints/knowledge.py`**：
   - `ingest_knowledge()` - 使用 `model_dump(mode='json')`

### 修復前後對比

**修復前：**
```python
return JSONResponse(content=response.model_dump())
```

**修復後：**
```python
return JSONResponse(content=response.model_dump(mode='json'))
```

## 測試驗證

修復後，使用 Postman 或 curl 測試：

```bash
# 測試系統統計
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: test-api-key"

# 測試圖結構統計
curl -X GET "http://localhost:8000/api/v1/admin/graph/stats" \
  -H "X-API-Key: test-api-key"

# 測試知識庫攝取
curl -X POST "http://localhost:8000/api/v1/knowledge/ingest" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "測試內容",
    "source": "api"
  }'
```

應該返回 `200 OK` 和正確的 JSON 回應，其中 `datetime` 欄位被序列化為 ISO 8601 格式字符串（例如：`"2025-12-26T18:03:00.123456"`）。

## 最佳實踐

### 1. 優先使用 FastAPI 自動序列化

如果端點使用 `response_model`，直接返回 Pydantic 模型即可：

```python
@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(...):
    return SystemStatsResponse(...)  # FastAPI 自動處理序列化
```

### 2. 手動序列化時使用 `mode='json'`

如果需要手動控制序列化（例如使用 `JSONResponse`），務必使用 `mode='json'`：

```python
return JSONResponse(content=response.model_dump(mode='json'))
```

### 3. 統一處理方式

在專案中統一使用一種方式處理 `datetime` 序列化，避免混用導致不一致。

## 相關文件

- [Pydantic Model Serialization](https://docs.pydantic.dev/latest/concepts/serialization/)
- [FastAPI Response Models](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Python datetime ISO Format](https://docs.python.org/3/library/datetime.html#datetime.datetime.isoformat)

---

## 更新歷史

- **2025-12-26 18:03**: 記錄 datetime JSON 序列化錯誤和修復方案

