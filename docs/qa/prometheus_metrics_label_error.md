# Prometheus 指標標籤缺失錯誤

**更新時間：2025-12-26 17:52**  
**作者：AI Assistant**  
**修改摘要：記錄 Prometheus 指標標籤缺失導致的 500 錯誤**

---

## 問題描述

當調用 `/api/v1/query` 端點時，返回 `500 Internal Server Error`，錯誤訊息為：

```
ValueError: counter metric is missing label values
ValueError: histogram metric is missing label values
```

## 錯誤詳情

### 錯誤堆疊

```
File "app/api/v1/endpoints/query.py", line 27, in query_endpoint
    REQUEST_COUNTER.inc()
ValueError: counter metric is missing label values

File "app/api/v1/endpoints/query.py", line 26, in query_endpoint
    with REQUEST_LATENCY.time():
ValueError: histogram metric is missing label values
```

### 根本原因

在 `app/utils/metrics.py` 中，`REQUEST_COUNTER` 和 `REQUEST_LATENCY` 定義時包含了標籤：

```python
REQUEST_COUNTER = Counter(
    "care_rag_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]  # 需要 3 個標籤
)

REQUEST_LATENCY = Histogram(
    "care_rag_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]  # 需要 2 個標籤
)
```

但在 `app/api/v1/endpoints/query.py` 中使用時，沒有提供標籤值：

```python
# ❌ 錯誤的使用方式
with REQUEST_LATENCY.time():  # 缺少 method 和 endpoint 標籤
    REQUEST_COUNTER.inc()  # 缺少 method、endpoint、status 標籤
```

## 解決方案

### 修正後的代碼

```python
@router.post("/query", response_model=QueryResponse)
async def query_endpoint(
    request: Request,
    query_request: QueryRequest,
    orchestrator: GraphOrchestrator = Depends(get_orchestrator)
):
    """REST 查詢端點"""
    endpoint_path = "/api/v1/query"
    method = request.method
    
    # ✅ 正確的使用方式：提供所有必需的標籤
    with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
        try:
            # 執行查詢
            result = await orchestrator.query(...)
            
            # 記錄成功指標（200）
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
            
            return JSONResponse(content=response.model_dump())
            
        except Exception as e:
            # 記錄錯誤指標（500）
            REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
            return JSONResponse(status_code=500, ...)
```

### 關鍵修改點

1. **REQUEST_LATENCY**：
   - ❌ `REQUEST_LATENCY.time()`
   - ✅ `REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time()`

2. **REQUEST_COUNTER**：
   - ❌ `REQUEST_COUNTER.inc()`
   - ✅ `REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()`

3. **狀態碼追蹤**：
   - 成功時記錄 `status="200"`
   - 錯誤時記錄 `status="500"`

## 參考範例

其他端點的正確使用方式（`app/api/v1/endpoints/knowledge.py`）：

```python
with REQUEST_LATENCY.labels(method="POST", endpoint="/api/v1/knowledge/query").time():
    REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/knowledge/query", status="200").inc()
    
    try:
        # 處理請求
        ...
    except Exception as e:
        REQUEST_COUNTER.labels(method="POST", endpoint="/api/v1/knowledge/query", status="500").inc()
```

## 測試驗證

修復後，使用 Postman 或 curl 測試：

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "什麼是長期照護2.0？",
    "top_k": 3,
    "provider": "gemini"
  }'
```

應該返回 `200 OK` 而不是 `500 Internal Server Error`。

## 預防措施

### 檢查清單

在添加新的 Prometheus 指標時，確保：

- [ ] 檢查指標定義中的標籤列表
- [ ] 使用 `.labels()` 提供所有必需的標籤值
- [ ] 根據實際 HTTP 狀態碼設置 `status` 標籤
- [ ] 參考其他端點的正確使用方式
- [ ] 測試端點確保指標正常工作

### 最佳實踐

1. **統一指標使用模式**：
   ```python
   endpoint_path = "/api/v1/your-endpoint"
   method = request.method
   
   with REQUEST_LATENCY.labels(method=method, endpoint=endpoint_path).time():
       try:
           # 處理邏輯
           REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="200").inc()
           return success_response
       except Exception as e:
           REQUEST_COUNTER.labels(method=method, endpoint=endpoint_path, status="500").inc()
           return error_response
   ```

2. **動態獲取方法**：
   - 使用 `request.method` 而不是硬編碼 `"POST"` 或 `"GET"`

3. **統一端點路徑**：
   - 定義常量或從路由中獲取，避免硬編碼錯誤

## 相關文件

- [Prometheus 指標定義](../app/utils/metrics.py)
- [查詢端點實作](../app/api/v1/endpoints/query.py)
- [知識庫端點範例](../app/api/v1/endpoints/knowledge.py)

---

## 更新歷史

- **2025-12-26 17:52**: 記錄 Prometheus 指標標籤缺失錯誤和修復方案

