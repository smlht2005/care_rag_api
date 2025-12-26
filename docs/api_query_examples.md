# Care RAG API 查詢範例

**更新時間：2025-12-26 17:34**  
**作者：AI Assistant**  
**修改摘要：創建完整的 API 查詢範例文檔，包含 REST、SSE、WebSocket 三種方式的實際查詢範例**

---

## 基礎資訊

### API 基礎 URL

```
http://localhost:8000
```

**重要**：實際運行端口為 **8000**，而非配置文件的 8080。

### 資料庫狀態

- **實體總數**：1273 個
- **關係總數**：2227 個
- **實體類型分布**：
  - Concept: 887 個
  - Organization: 108 個
  - Document: 85 個
  - Location: 85 個
  - Person: 68 個
  - Policy: 40 個

### API Key

預設 API Key：`test-api-key`（可在 `.env` 文件中配置）

請求頭格式：
```
X-API-Key: test-api-key
```

---

## 1. REST API 查詢範例

### 1.1 基本查詢

**端點**：`POST /api/v1/query`

**請求格式**：
```json
{
  "query": "查詢問題",
  "top_k": 3,
  "provider": "gemini",
  "max_tokens": 2000,
  "temperature": 0.7
}
```

#### 範例 1：查詢長期照護相關內容

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "什麼是長期照護2.0？",
    "top_k": 3,
    "provider": "gemini"
  }'
```

**Python 範例**：
```python
import requests

url = "http://localhost:8000/api/v1/query"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key"
}
data = {
    "query": "什麼是長期照護2.0？",
    "top_k": 3,
    "provider": "gemini"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

**預期回應**：
```json
{
  "answer": "長期照護2.0是...",
  "sources": [
    {
      "content": "...",
      "metadata": {...}
    }
  ],
  "query": "什麼是長期照護2.0？",
  "provider": "gemini"
}
```

#### 範例 2：查詢 World Health Organization 相關資訊

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "World Health Organization 在長期照護方面有什麼政策？",
    "top_k": 5
  }'
```

**Python 範例**：
```python
import requests

url = "http://localhost:8000/api/v1/query"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "test-api-key"
}
data = {
    "query": "World Health Organization 在長期照護方面有什麼政策？",
    "top_k": 5
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

#### 範例 3：查詢政策和組織關係

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "哪些組織實施了長期照護政策？",
    "top_k": 3
  }'
```

#### 範例 4：查詢概念和實體關係

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護與健康老化有什麼關係？",
    "top_k": 3
  }'
```

#### 範例 5：查詢地點和人員

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護服務在哪些地點提供？",
    "top_k": 3
  }'
```

#### 範例 6：指定 LLM Provider（OpenAI）

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護的核心概念是什麼？",
    "provider": "openai",
    "top_k": 3,
    "temperature": 0.8
  }'
```

#### 範例 7：自訂參數（max_tokens, temperature）

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "請詳細說明長期照護2.0的實施策略",
    "top_k": 5,
    "max_tokens": 3000,
    "temperature": 0.7
  }'
```

#### 範例 8：查詢多個相關概念

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護、健康老化、社區照護之間的關係是什麼？",
    "top_k": 5
  }'
```

#### 範例 9：查詢特定政策文件

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "The Global strategy and action plan on ageing and health 的主要內容是什麼？",
    "top_k": 3
  }'
```

#### 範例 10：查詢照護服務類型

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護包含哪些類型的服務？",
    "top_k": 3
  }'
```

#### 範例 11：查詢實施策略

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "如何實施長期照護2.0計劃？",
    "top_k": 5
  }'
```

#### 範例 12：查詢評估和驗證方法

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{
    "query": "長期照護服務的評估和驗證方法是什麼？",
    "top_k": 3
  }'
```

---

## 2. SSE 串流查詢範例

### 2.1 基本 SSE 查詢

**端點**：`GET /api/v1/query/stream`

**參數**：
- `query`：查詢問題（1-1000 字元，必填）

#### 範例 1：基本串流查詢

**curl 命令**：
```bash
curl -N "http://localhost:8000/api/v1/query/stream?query=什麼是長期照護2.0？" \
  -H "X-API-Key: test-api-key"
```

**Python 範例**：
```python
import requests

url = "http://localhost:8000/api/v1/query/stream"
headers = {
    "X-API-Key": "test-api-key"
}
params = {
    "query": "什麼是長期照護2.0？"
}

response = requests.get(url, params=params, headers=headers, stream=True)

for line in response.iter_lines():
    if line:
        decoded_line = line.decode('utf-8')
        if decoded_line.startswith('data: '):
            data = decoded_line[6:]  # 移除 'data: ' 前綴
            if data == '[DONE]':
                break
            print(data)
```

**JavaScript 範例**：
```javascript
const eventSource = new EventSource(
  'http://localhost:8000/api/v1/query/stream?query=什麼是長期照護2.0？',
  {
    headers: {
      'X-API-Key': 'test-api-key'
    }
  }
);

eventSource.onmessage = function(event) {
  const data = event.data;
  if (data === '[DONE]') {
    eventSource.close();
  } else {
    console.log(data);
  }
};

eventSource.onerror = function(error) {
  console.error('SSE error:', error);
  eventSource.close();
};
```

#### 範例 2：查詢組織政策（串流）

**curl 命令**：
```bash
curl -N "http://localhost:8000/api/v1/query/stream?query=World Health Organization 的長期照護政策是什麼？" \
  -H "X-API-Key: test-api-key"
```

#### 範例 3：查詢複雜問題（串流）

**curl 命令**：
```bash
curl -N "http://localhost:8000/api/v1/query/stream?query=請詳細說明長期照護2.0的實施策略和評估方法" \
  -H "X-API-Key: test-api-key"
```

---

## 3. WebSocket 查詢範例

### 3.1 WebSocket 聊天端點

**端點**：`WebSocket /api/v1/ws/chat`

**請求格式**：
```json
{
  "query": "查詢問題"
}
```

**回應格式**：
```json
{
  "chunk": "回應片段",
  "index": 0,
  "done": false
}
```

#### 範例 1：基本 WebSocket 查詢

**Python 範例**：
```python
import asyncio
import websockets
import json

async def websocket_query():
    uri = "ws://localhost:8000/api/v1/ws/chat"
    headers = {
        "X-API-Key": "test-api-key"
    }
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        # 發送查詢
        query = {
            "query": "什麼是長期照護2.0？"
        }
        await websocket.send(json.dumps(query))
        
        # 接收回應
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("done"):
                print("查詢完成")
                break
            
            print(f"Chunk {data['index']}: {data['chunk']}")

# 執行
asyncio.run(websocket_query())
```

**JavaScript 範例**：
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/chat');

ws.onopen = function() {
  ws.send(JSON.stringify({
    query: "什麼是長期照護2.0？"
  }));
};

ws.onmessage = function(event) {
  const data = JSON.parse(event.data);
  
  if (data.done) {
    console.log("查詢完成");
    ws.close();
  } else {
    console.log(`Chunk ${data.index}: ${data.chunk}`);
  }
};

ws.onerror = function(error) {
  console.error('WebSocket error:', error);
};
```

#### 範例 2：WebSocket 查詢端點

**端點**：`WebSocket /api/v1/ws/query`

**請求格式**：
```json
{
  "query": "查詢問題"
}
```

**回應格式**：
```json
{
  "type": "chunk",
  "chunk": "回應片段",
  "index": 0,
  "done": false
}
```

**Python 範例**：
```python
import asyncio
import websockets
import json

async def websocket_query_v2():
    uri = "ws://localhost:8000/api/v1/ws/query"
    
    async with websockets.connect(uri) as websocket:
        # 發送查詢
        query = {
            "query": "World Health Organization 的長期照護政策是什麼？"
        }
        await websocket.send(json.dumps(query))
        
        # 接收回應
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("type") == "done":
                print("查詢完成")
                break
            elif data.get("type") == "chunk":
                print(f"Chunk {data['index']}: {data['chunk']}")
            elif data.get("type") == "error":
                print(f"錯誤: {data['error']}")
                break

# 執行
asyncio.run(websocket_query_v2())
```

---

## 4. 其他有用端點

### 4.1 健康檢查

**端點**：`GET /api/v1/health`

**curl 命令**：
```bash
curl "http://localhost:8000/api/v1/health"
```

**回應**：
```json
{
  "success": true,
  "message": "Care RAG API is healthy",
  "data": {
    "status": "healthy",
    "timestamp": "2025-12-26T17:34:00",
    "version": "1.0.0"
  }
}
```

### 4.2 就緒檢查

**端點**：`GET /api/v1/health/ready`

**curl 命令**：
```bash
curl "http://localhost:8000/api/v1/health/ready"
```

### 4.3 存活檢查

**端點**：`GET /api/v1/health/live`

**curl 命令**：
```bash
curl "http://localhost:8000/api/v1/health/live"
```

### 4.4 圖資料庫統計

**端點**：`GET /api/v1/admin/graph/stats`

**需要 API Key**

**curl 命令**：
```bash
curl "http://localhost:8000/api/v1/admin/graph/stats" \
  -H "X-API-Key: test-api-key"
```

**回應**：
```json
{
  "total_entities": 1273,
  "total_relations": 2227,
  "entity_types": {
    "Concept": 887,
    "Organization": 108,
    "Document": 85,
    "Location": 85,
    "Person": 68,
    "Policy": 40
  },
  "relation_types": {
    "CONTAINS": 1239,
    "RELATED_TO": 956,
    "LOCATED_IN": 7,
    "AUTHORED_BY": 6,
    "IMPLEMENTS": 3,
    "IS_A": 3,
    "ADDRESSED_BY": 2,
    "MANAGES": 2,
    "ABOUT": 1,
    "COORDINATES_WITH": 1,
    "LOCATED_AT": 1,
    "MENTIONS": 1,
    "PART_OF": 1,
    "PUBLISHED_AT": 1,
    "PUBLISHED_ON": 1,
    "SYNONYM": 1,
    "TARGETS": 1
  },
  "timestamp": "2025-12-26T17:34:00"
}
```

### 4.5 系統統計

**端點**：`GET /api/v1/admin/stats`

**需要 API Key**

**curl 命令**：
```bash
curl "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: test-api-key"
```

### 4.6 清除快取

**端點**：`POST /api/v1/admin/cache/clear`

**需要 API Key**

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/admin/cache/clear" \
  -H "X-API-Key: test-api-key"
```

---

## 5. 文件管理端點

### 5.1 新增單一文件

**端點**：`POST /api/v1/documents`

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "這是文件內容...",
    "metadata": {
      "title": "範例文件",
      "author": "AI Assistant"
    },
    "source": "example.pdf"
  }'
```

### 5.2 批量新增文件

**端點**：`POST /api/v1/documents/batch`

**curl 命令**：
```bash
curl -X POST "http://localhost:8000/api/v1/documents/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "content": "文件1內容...",
        "source": "doc1.pdf"
      },
      {
        "content": "文件2內容...",
        "source": "doc2.pdf"
      }
    ]
  }'
```

### 5.3 刪除文件

**端點**：`DELETE /api/v1/documents/{document_id}`

**curl 命令**：
```bash
curl -X DELETE "http://localhost:8000/api/v1/documents/{document_id}"
```

---

## 6. 錯誤處理範例

### 6.1 無效查詢（空查詢）

**請求**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": ""
  }'
```

**回應**（422 Unprocessable Entity）：
```json
{
  "detail": [
    {
      "loc": ["body", "query"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

### 6.2 缺少 API Key

**請求**：
```bash
curl "http://localhost:8000/api/v1/admin/graph/stats"
```

**回應**（401 Unauthorized）：
```json
{
  "detail": "API Key is required"
}
```

### 6.3 無效 API Key

**請求**：
```bash
curl "http://localhost:8000/api/v1/admin/graph/stats" \
  -H "X-API-Key: invalid-key"
```

**回應**（401 Unauthorized）：
```json
{
  "detail": "Invalid API Key"
}
```

### 6.4 服務未啟動

**錯誤訊息**：
```
curl: (7) Failed to connect to localhost port 8000: Connection refused
```

**解決方案**：
1. 確認 API 服務已啟動：`uvicorn app.main:app --reload --port 8000`
2. 檢查端口是否被占用
3. 檢查防火牆設定

### 6.5 參數錯誤（top_k 超出範圍）

**請求**：
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "測試",
    "top_k": 20
  }'
```

**回應**（422 Unprocessable Entity）：
```json
{
  "detail": [
    {
      "loc": ["body", "top_k"],
      "msg": "ensure this value is less than or equal to 10",
      "type": "value_error.number.not_le"
    }
  ]
}
```

---

## 7. 完整 Python 範例腳本

```python
"""
Care RAG API 完整查詢範例
"""
import requests
import asyncio
import websockets
import json

BASE_URL = "http://localhost:8000"
API_KEY = "test-api-key"
HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def rest_query_example():
    """REST API 查詢範例"""
    url = f"{BASE_URL}/api/v1/query"
    data = {
        "query": "什麼是長期照護2.0？",
        "top_k": 3,
        "provider": "gemini"
    }
    
    response = requests.post(url, json=data, headers=HEADERS)
    print("REST 查詢結果：")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def sse_query_example():
    """SSE 串流查詢範例"""
    url = f"{BASE_URL}/api/v1/query/stream"
    params = {
        "query": "什麼是長期照護2.0？"
    }
    
    response = requests.get(url, params=params, headers={"X-API-Key": API_KEY}, stream=True)
    
    print("\nSSE 串流查詢結果：")
    for line in response.iter_lines():
        if line:
            decoded_line = line.decode('utf-8')
            if decoded_line.startswith('data: '):
                data = decoded_line[6:]
                if data == '[DONE]':
                    break
                print(data)

async def websocket_query_example():
    """WebSocket 查詢範例"""
    uri = "ws://localhost:8000/api/v1/ws/chat"
    headers = {
        "X-API-Key": API_KEY
    }
    
    async with websockets.connect(uri, extra_headers=headers) as websocket:
        query = {
            "query": "什麼是長期照護2.0？"
        }
        await websocket.send(json.dumps(query))
        
        print("\nWebSocket 查詢結果：")
        while True:
            response = await websocket.recv()
            data = json.loads(response)
            
            if data.get("done"):
                break
            
            print(f"Chunk {data['index']}: {data['chunk']}")

def health_check_example():
    """健康檢查範例"""
    url = f"{BASE_URL}/api/v1/health"
    response = requests.get(url)
    print("\n健康檢查結果：")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def graph_stats_example():
    """圖資料庫統計範例"""
    url = f"{BASE_URL}/api/v1/admin/graph/stats"
    response = requests.get(url, headers={"X-API-Key": API_KEY})
    print("\n圖資料庫統計：")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    # REST 查詢
    rest_query_example()
    
    # SSE 串流查詢
    sse_query_example()
    
    # WebSocket 查詢
    asyncio.run(websocket_query_example())
    
    # 健康檢查
    health_check_example()
    
    # 圖資料庫統計
    graph_stats_example()
```

---

## 8. 常見問題

### Q1: 如何確認 API 服務是否正常運行？

A: 使用健康檢查端點：
```bash
curl "http://localhost:8000/api/v1/health"
```

### Q2: 如何查看資料庫統計資訊？

A: 使用圖資料庫統計端點（需要 API Key）：
```bash
curl "http://localhost:8000/api/v1/admin/graph/stats" \
  -H "X-API-Key: test-api-key"
```

### Q3: 查詢回應很慢怎麼辦？

A: 
1. 檢查 `top_k` 參數是否過大（建議 3-5）
2. 使用 SSE 或 WebSocket 串流查詢以獲得即時回應
3. 檢查 LLM Provider 的 API 連線狀態

### Q4: 如何處理中文查詢？

A: API 完全支援中文查詢，直接使用中文即可：
```json
{
  "query": "什麼是長期照護2.0？"
}
```

### Q5: 如何切換不同的 LLM Provider？

A: 在請求中指定 `provider` 參數：
```json
{
  "query": "查詢問題",
  "provider": "gemini"  // 或 "openai" 或 "deepseek"
}
```

---

## 9. 相關文檔

- [API 啟動錯誤處理](qa/api_startup_errors_qa.md)
- [LLM 真實 API 實作指南](qa/llm_real_api_implementation_guide.md)
- [資料庫查詢問答](qa/database_query_qa.md)
- [Postman 集合](../postman/Care_RAG_API.postman_collection.json)

---

## 更新歷史

- **2025-12-26 17:34**: 創建完整的 API 查詢範例文檔

