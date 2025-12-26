# Stub 是什麼？

## 定義

**Stub（存根）** 是一個程式設計術語，指的是：
- 一個**簡化版本的函數或類別**
- 用於**模擬真實功能**，但**不實作完整邏輯**
- 通常返回**預設值**或**模擬數據**
- 目的是讓系統能夠**編譯和運行**，即使真實功能尚未實作

## 簡單類比

想像你在蓋房子：

- **真實實作** = 真正的牆壁、屋頂、水電系統
- **Stub** = 用紙板做的模型房子，看起來像房子，但不能真的住人

Stub 讓你可以：
- 測試房子的外觀和結構
- 檢查其他部分是否能正確連接
- 在真實材料到達前，先完成設計

## 在我們的專案中

### LLMService 的 Stub 實作

讓我們看看 `app/services/llm_service.py`：

```python
class LLMService:
    async def generate(self, prompt: str, ...) -> str:
        # 模擬 API 呼叫延遲
        await asyncio.sleep(0.1)
        
        if self.provider == "gemini":
            return f"[Gemini] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答..."
        elif self.provider == "openai":
            return f"[OpenAI] 回答: {prompt}\n\n這是一個基於 OpenAI 模型的回答..."
        # ...
```

### 這是 Stub 的原因

1. **沒有真正的 API 呼叫**
   - 沒有連接到 Google Gemini API
   - 沒有連接到 OpenAI API
   - 只是返回固定的文字字串

2. **返回模擬數據**
   - 不是真正的 AI 回答
   - 只是根據 provider 名稱返回不同的文字

3. **讓系統可以運行**
   - 其他部分（如 `EntityExtractor`）可以呼叫這個服務
   - 系統不會因為缺少 LLM 服務而無法啟動
   - 可以測試整體架構和流程

## Stub vs 真實實作

### Stub 版本（當前）

```python
async def generate(self, prompt: str) -> str:
    await asyncio.sleep(0.1)  # 模擬延遲
    return f"[Gemini] 回答: {prompt}\n\n這是模擬回答..."
```

**特點**：
- ✅ 快速（不需要網路請求）
- ✅ 不需要 API Key
- ✅ 不需要費用
- ✅ 可以立即測試
- ❌ 不是真正的 AI 回答
- ❌ 不會提取真實的實體和關係

### 真實實作版本（未來）

```python
async def generate(self, prompt: str) -> str:
    # 真正的 API 呼叫
    import google.generativeai as genai
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    
    response = await model.generate_content_async(prompt)
    return response.text
```

**特點**：
- ✅ 真正的 AI 回答
- ✅ 可以提取真實的實體和關係
- ❌ 需要 API Key
- ❌ 需要網路連線
- ❌ 可能產生費用
- ❌ 需要處理 API 錯誤

## 為什麼使用 Stub？

### 1. 開發階段

在開發初期，使用 Stub 可以：
- **快速開發**：不需要等待 API 設置完成
- **測試架構**：驗證系統設計是否正確
- **並行開發**：不同開發者可以同時工作

### 2. 測試階段

使用 Stub 可以：
- **單元測試**：不需要真實 API，測試更快
- **整合測試**：可以測試錯誤處理、重試邏輯等
- **CI/CD**：自動化測試不需要 API Key

### 3. 降級方案

當真實 API 失敗時，可以使用 Stub 作為降級方案。

## 實際例子

### 例子 1: 測試流程

```python
# 使用 Stub 測試整個流程
llm_service = LLMService()  # Stub 版本
extractor = EntityExtractor(llm_service)

# 可以測試提取邏輯，即使沒有真實 LLM
entities = await extractor.extract_entities("測試文字")
```

### 例子 2: 開發新功能

```python
# 開發 GraphBuilder 時
# 不需要等待 LLM API 設置
# 可以使用 Stub 先完成功能開發
graph_builder = GraphBuilder(graph_store, entity_extractor)
result = await graph_builder.build_graph_from_text(text, doc_id)
```

## 何時替換 Stub？

### 替換時機

1. **功能開發完成**：核心邏輯已經測試通過
2. **需要真實數據**：需要測試真實的 AI 回答
3. **準備上線**：系統準備部署到生產環境

### 如何替換

1. **實作真實的 API 呼叫**
2. **添加 API Key 配置**
3. **添加錯誤處理和重試邏輯**
4. **添加速率限制和成本控制**
5. **測試真實 API 的整合**

## 其他常見的 Stub 例子

### 1. 資料庫 Stub

```python
# Stub 版本
class DatabaseService:
    def get_user(self, user_id):
        return {"id": user_id, "name": "測試用戶"}

# 真實版本
class DatabaseService:
    def get_user(self, user_id):
        return self.db.query("SELECT * FROM users WHERE id = ?", user_id)
```

### 2. 檔案系統 Stub

```python
# Stub 版本
class FileService:
    def read_file(self, path):
        return "模擬檔案內容"

# 真實版本
class FileService:
    def read_file(self, path):
        with open(path, 'r') as f:
            return f.read()
```

### 3. 外部 API Stub

```python
# Stub 版本
class PaymentService:
    def process_payment(self, amount):
        return {"status": "success", "transaction_id": "test_123"}

# 真實版本
class PaymentService:
    def process_payment(self, amount):
        response = requests.post("https://payment-api.com/charge", ...)
        return response.json()
```

## 總結

**Stub = 簡化版的實作，用於模擬真實功能**

在我們的專案中：
- `LLMService` 是 Stub，返回模擬的 AI 回答
- 這讓系統可以運行和測試，即使沒有真實的 LLM API
- 未來可以替換為真實的 LLM API 整合

**優點**：
- 快速開發
- 不需要外部依賴
- 易於測試

**缺點**：
- 不是真實功能
- 需要後續替換

## 相關檔案

- `app/services/llm_service.py` - LLM 服務（當前是 Stub）
- `app/services/cache_service.py` - 快取服務（也是 Stub，使用記憶體）
- `app/services/vector_service.py` - 向量服務（也是 Stub，返回模擬數據）


