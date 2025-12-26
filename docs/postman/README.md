# Postman 集合使用指南

**更新時間：2025-12-26 17:35**  
**作者：AI Assistant**  
**修改摘要：創建 Postman 集合使用指南**

---

## 導入 Postman 集合

### 方法 1：導入集合文件

1. 打開 Postman
2. 點擊左上角的 **Import** 按鈕
3. 選擇 `Care_RAG_API.postman_collection.json` 文件
4. 點擊 **Import**

### 方法 2：導入環境變數（可選）

1. 在 Postman 中點擊右上角的 **Environments**
2. 點擊 **Import**
3. 選擇 `Care_RAG_API.postman_environment.json` 文件
4. 選擇導入的環境：**Care RAG API - Local**

---

## 環境變數設定

### 預設環境變數

集合包含以下環境變數：

- `base_url`: `http://localhost:8000`（API 基礎 URL）
- `api_key`: `test-api-key`（API Key）

### 修改環境變數

1. 在 Postman 中選擇環境：**Care RAG API - Local**
2. 點擊 **Edit** 按鈕
3. 修改變數值：
   - `base_url`: 修改為實際的 API 地址
   - `api_key`: 修改為實際的 API Key

---

## 集合結構

### 1. Health Check（健康檢查）

- **Health Check** - 基本健康檢查
- **Readiness Check** - 就緒檢查
- **Liveness Check** - 存活檢查

### 2. Query（查詢）

- **REST Query - 長期照護** - 查詢長期照護相關內容
- **REST Query - World Health Organization** - 查詢 WHO 相關政策
- **REST Query - 政策和組織關係** - 查詢政策和組織關係
- **REST Query - 自訂參數** - 使用自訂參數的查詢
- **SSE Stream Query** - SSE 串流查詢

### 3. Documents（文件管理）

- **Add Document** - 新增單一文件
- **Batch Add Documents** - 批量新增文件
- **Delete Document** - 刪除文件

### 4. Knowledge（知識庫）

- **Knowledge Query** - 知識庫查詢（包含圖結構資訊）
- **Get Knowledge Sources** - 取得知識來源列表
- **Ingest Knowledge** - 知識庫攝取

### 5. Admin（管理）

- **Get System Stats** - 取得系統統計資訊（需要 API Key）
- **Get Graph Stats** - 取得圖資料庫統計資訊（需要 API Key）
- **Clear Cache** - 清除快取（需要 API Key）

---

## 使用範例

### 1. 執行基本查詢

1. 展開 **Query** 資料夾
2. 選擇 **REST Query - 長期照護**
3. 點擊 **Send** 按鈕
4. 查看回應結果

### 2. 修改查詢參數

1. 選擇任意查詢請求
2. 在 **Body** 標籤中修改 JSON 內容
3. 例如修改 `query` 欄位：
   ```json
   {
     "query": "你的自訂問題",
     "top_k": 5
   }
   ```
4. 點擊 **Send**

### 3. 查看圖資料庫統計

1. 展開 **Admin** 資料夾
2. 選擇 **Get Graph Stats**
3. 確認請求頭包含 `X-API-Key: test-api-key`
4. 點擊 **Send**
5. 查看回應中的實體和關係統計

---

## 注意事項

1. **API Key**：管理端點（Admin）需要 API Key，請確保請求頭包含 `X-API-Key`
2. **端口號**：預設使用端口 8000，如果 API 運行在不同端口，請修改環境變數 `base_url`
3. **SSE 查詢**：SSE 串流查詢在 Postman 中可能無法完整顯示，建議使用 curl 或程式化方式測試
4. **WebSocket**：Postman 支援 WebSocket，但建議使用專用的 WebSocket 客戶端進行測試

---

## 故障排除

### 問題 1：連接被拒絕

**錯誤**：`Error: connect ECONNREFUSED 127.0.0.1:8000`

**解決方案**：
1. 確認 API 服務已啟動：`uvicorn app.main:app --reload --port 8000`
2. 檢查環境變數 `base_url` 是否正確

### 問題 2：401 Unauthorized

**錯誤**：`{"detail": "API Key is required"}`

**解決方案**：
1. 確認請求頭包含 `X-API-Key`
2. 檢查環境變數 `api_key` 是否正確
3. 確認 API Key 與服務配置一致

### 問題 3：422 Unprocessable Entity

**錯誤**：`{"detail": [...]}`

**解決方案**：
1. 檢查請求體格式是否正確（JSON）
2. 確認必填欄位已提供
3. 檢查欄位值是否符合驗證規則（如 `top_k` 必須在 1-10 之間）

---

## 相關文檔

- [API Key 設置指南](../api_key_setup_guide.md) - **完整的 API Key 設置說明**
- [API 查詢範例](../api_query_examples.md) - 完整的 API 查詢範例文檔
- [API 啟動錯誤處理](../qa/api_startup_errors_qa.md) - API 啟動相關問題
- [資料庫查詢問答](../qa/database_query_qa.md) - 資料庫查詢相關問題

---

## 更新歷史

- **2025-12-26 17:35**: 創建 Postman 集合使用指南

