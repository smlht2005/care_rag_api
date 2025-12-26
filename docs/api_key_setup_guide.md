# API Key 設置指南

**更新時間：2025-12-26 17:47**  
**作者：AI Assistant**  
**修改摘要：創建完整的 API Key 設置指南**

---

## 概述

Care RAG API 使用 `X-API-Key` 請求頭進行身份驗證。某些管理端點（Admin）需要有效的 API Key 才能訪問。

---

## 1. API 服務端設置

### 方法 1：使用環境變數（推薦）

在 `.env` 文件中設置：

```bash
API_KEY=your-secret-api-key-here
```

或者在系統環境變數中設置：

```bash
# Windows PowerShell
$env:API_KEY="your-secret-api-key-here"

# Linux/Mac
export API_KEY="your-secret-api-key-here"
```

### 方法 2：修改配置文件

編輯 `app/config.py`：

```python
class Settings(BaseSettings):
    # API Key 設定
    API_KEY: Optional[str] = "your-secret-api-key-here"  # 修改這裡
    API_KEY_HEADER: str = "X-API-Key"
```

**注意**：修改配置文件後需要重啟 API 服務。

### 預設值

如果未設置 `API_KEY`，系統將使用預設值：`test-api-key`

---

## 2. Postman 設置

### 方法 1：使用集合變數（已配置）

Postman 集合已預設包含 `api_key` 變數，值為 `test-api-key`。

**查看集合變數：**
1. 在 Postman 中打開 **Care RAG API** 集合
2. 點擊集合名稱右側的 **...** 選單
3. 選擇 **Edit**
4. 切換到 **Variables** 標籤
5. 可以看到 `api_key` 變數，當前值為 `test-api-key`

**修改集合變數：**
1. 在 **Variables** 標籤中
2. 修改 `api_key` 的 **Current Value** 為你的實際 API Key
3. 點擊 **Save**

### 方法 2：使用環境變數（推薦用於多環境）

1. 在 Postman 中點擊右上角的 **Environments**
2. 選擇或創建環境（如 **Care RAG API - Local**）
3. 添加變數：
   - **Variable**: `api_key`
   - **Initial Value**: `test-api-key`
   - **Current Value**: `your-actual-api-key`
4. 確保環境已啟用（右上角下拉選單）

**在請求中使用環境變數：**
- 請求頭中的 `{{api_key}}` 會自動替換為環境變數的值

---

## 3. 哪些端點需要 API Key？

### 需要 API Key 的端點（Admin）

以下管理端點**必須**提供有效的 API Key：

- `GET /api/v1/admin/stats` - 取得系統統計資訊
- `GET /api/v1/admin/graph/stats` - 取得圖資料庫統計資訊
- `POST /api/v1/admin/cache/clear` - 清除快取

**請求範例：**
```bash
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: test-api-key"
```

### 不需要 API Key 的端點

以下端點**不需要** API Key（但可以選擇性提供）：

- `GET /` - 根端點
- `GET /api/v1/health` - 健康檢查
- `GET /api/v1/health/ready` - 就緒檢查
- `GET /api/v1/health/live` - 存活檢查
- `POST /api/v1/query` - RAG 查詢
- `GET /api/v1/query/stream` - SSE 串流查詢
- `POST /api/v1/documents` - 新增文件
- `POST /api/v1/documents/batch` - 批量新增文件
- `DELETE /api/v1/documents/{document_id}` - 刪除文件
- `POST /api/v1/knowledge/query` - 知識庫查詢
- `GET /api/v1/knowledge/sources` - 取得知識來源
- `POST /api/v1/knowledge/ingest` - 知識庫攝取

---

## 4. 測試 API Key 設置

### 使用 curl 測試

```bash
# 測試健康檢查（不需要 API Key）
curl "http://localhost:8000/api/v1/health"

# 測試管理端點（需要 API Key）
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: test-api-key"

# 測試錯誤的 API Key（應該返回 401）
curl -X GET "http://localhost:8000/api/v1/admin/stats" \
  -H "X-API-Key: wrong-key"
```

### 使用 Postman 測試

1. **測試健康檢查：**
   - 選擇 **Health Check > Health Check**
   - 點擊 **Send**
   - 應該返回 `200 OK`

2. **測試管理端點：**
   - 選擇 **Admin > Get System Stats**
   - 確認請求頭包含 `X-API-Key: {{api_key}}`
   - 點擊 **Send**
   - 應該返回 `200 OK` 和系統統計資訊

3. **測試錯誤的 API Key：**
   - 在請求頭中將 `{{api_key}}` 改為 `wrong-key`
   - 點擊 **Send**
   - 應該返回 `401 Unauthorized`

---

## 5. 常見錯誤和解決方案

### 錯誤 1：`{"detail": "API Key is required"}`

**原因**：請求頭中缺少 `X-API-Key`

**解決方案：**
1. 確認請求頭包含 `X-API-Key`
2. 在 Postman 中檢查 **Headers** 標籤，確認 `X-API-Key` 已啟用

### 錯誤 2：`{"detail": "Invalid API Key"}`

**原因**：API Key 不正確

**解決方案：**
1. 確認 API Key 與服務端配置一致
2. 檢查環境變數或配置文件中的 `API_KEY` 值
3. 確認 Postman 中的 `api_key` 變數值正確

### 錯誤 3：Postman 變數未替換

**原因**：變數語法錯誤或環境未啟用

**解決方案：**
1. 確認使用 `{{api_key}}` 而不是 `{api_key}` 或 `api_key`
2. 確認環境已啟用（右上角下拉選單）
3. 確認變數名稱拼寫正確

---

## 6. 安全建議

### 生產環境

1. **使用強密碼**：API Key 應該是一個長且隨機的字串
   ```bash
   # 生成隨機 API Key（Linux/Mac）
   openssl rand -hex 32
   
   # 生成隨機 API Key（PowerShell）
   -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
   ```

2. **不要提交到版本控制**：
   - 將 `.env` 添加到 `.gitignore`
   - 不要在代碼中硬編碼 API Key

3. **使用環境變數**：
   - 在生產環境中使用系統環境變數
   - 不要將 API Key 寫入配置文件

4. **定期輪換**：
   - 定期更換 API Key
   - 通知所有使用者更新 API Key

### 開發環境

- 可以使用預設的 `test-api-key` 進行開發和測試
- 確保開發環境與生產環境使用不同的 API Key

---

## 7. 配置檢查清單

- [ ] API 服務端已設置 `API_KEY`（環境變數或配置文件）
- [ ] Postman 集合變數 `api_key` 已設置
- [ ] Postman 環境變數（如使用）已設置並啟用
- [ ] 請求頭 `X-API-Key` 已正確添加到需要認證的請求中
- [ ] 測試健康檢查端點成功（不需要 API Key）
- [ ] 測試管理端點成功（需要 API Key）
- [ ] 測試錯誤的 API Key 返回 401 錯誤

---

## 8. 相關文檔

- [Postman 集合使用指南](./postman/README.md) - Postman 使用詳細說明
- [API 查詢範例](./api_query_examples.md) - 完整的 API 查詢範例
- [API 啟動錯誤處理](./qa/api_startup_errors_qa.md) - API 啟動相關問題

---

## 更新歷史

- **2025-12-26 17:47**: 創建 API Key 設置指南

