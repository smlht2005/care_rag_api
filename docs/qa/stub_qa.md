# Stub 相關問答

## Q: 什麼是 Stub？

**A:** Stub（存根）是程式設計術語，指的是一個**簡化版本的函數或類別**，用於**模擬真實功能**，但**不實作完整邏輯**。

### 簡單類比

想像你在蓋房子：
- **真實實作** = 真正的牆壁、屋頂、水電系統
- **Stub** = 用紙板做的模型房子，看起來像房子，但不能真的住人

Stub 讓你可以：
- 測試房子的外觀和結構
- 檢查其他部分是否能正確連接
- 在真實材料到達前，先完成設計

---

## Q: 為什麼專案中使用 Stub？

**A:** 在開發階段使用 Stub 有以下優點：

### 1. 快速開發
- 不需要等待 API 設置完成
- 不需要申請 API Key
- 不需要配置外部服務

### 2. 易於測試
- 不需要網路連線
- 不需要支付 API 費用
- 測試結果可預測

### 3. 並行開發
- 不同開發者可以同時工作
- 不依賴外部服務的可用性

---

## Q: 專案中哪些服務是 Stub？

**A:** 目前有三個主要服務是 Stub：

### 1. LLMService（LLM 服務）

**Stub 版本**：
```python
async def generate(self, prompt: str) -> str:
    await asyncio.sleep(0.1)  # 模擬延遲
    return f"[Gemini] 回答: {prompt}\n\n這是模擬回答..."
```

**特點**：
- ❌ 沒有真正的 API 呼叫
- ❌ 返回固定文字，不是真正的 AI 回答
- ✅ 讓系統可以運行和測試

**真實版本（未來）**：
```python
async def generate(self, prompt: str) -> str:
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-pro')
    response = await model.generate_content_async(prompt)
    return response.text  # 真正的 AI 回答
```

### 2. CacheService（快取服務）

**Stub 版本**：
- 使用記憶體字典 `self.store = {}`
- 不是真正的 Redis

**真實版本（未來）**：
- 連接到 Redis 伺服器
- 支援分散式快取

### 3. VectorService（向量服務）

**Stub 版本**：
- 返回模擬的檢索結果
- 不是真正的向量資料庫（如 Pinecone、Weaviate）

**真實版本（未來）**：
- 連接到向量資料庫
- 執行真正的語義搜尋

---

## Q: Stub 和 Mock 有什麼不同？

**A:** 

### Stub
- **目的**：提供簡化的實作，讓系統可以運行
- **特點**：返回固定的、預設的值
- **使用場景**：開發階段、整合測試

### Mock
- **目的**：模擬對象行為，用於單元測試
- **特點**：可以設定期望的行為和返回值
- **使用場景**：單元測試、行為驗證

### 例子

**Stub**：
```python
class LLMService:
    def generate(self, prompt):
        return "固定回答"  # 總是返回相同值
```

**Mock**：
```python
from unittest.mock import Mock
llm_service = Mock()
llm_service.generate.return_value = "測試回答"  # 可以設定返回值
llm_service.generate.assert_called_once()  # 可以驗證呼叫
```

---

## Q: 何時應該替換 Stub？

**A:** 在以下時機應該替換為真實實作：

### 1. 功能開發完成
- 核心邏輯已經測試通過
- 架構設計已經驗證

### 2. 需要真實數據
- 需要測試真實的 AI 回答
- 需要驗證真實的效能

### 3. 準備上線
- 系統準備部署到生產環境
- 需要真實的功能支援

---

## Q: 如何替換 Stub？

**A:** 替換步驟：

### 1. 實作真實的 API 呼叫
```python
# 替換 Stub 方法
async def generate(self, prompt: str) -> str:
    # 真實的 API 呼叫
    response = await real_api_call(prompt)
    return response
```

### 2. 添加配置
- API Key 配置
- 端點 URL 配置
- 超時和重試設定

### 3. 添加錯誤處理
- API 錯誤處理
- 網路錯誤處理
- 重試邏輯

### 4. 測試整合
- 測試真實 API 的整合
- 驗證錯誤處理
- 效能測試

---

## Q: 使用 Stub 會有什麼問題？

**A:** 主要問題：

### 1. 功能不完整
- 不是真實功能
- 可能隱藏真實問題

### 2. 測試不充分
- 無法測試真實的 API 整合
- 無法測試錯誤處理

### 3. 需要後續替換
- 增加技術債務
- 需要額外時間替換

### 解決方案
- 明確標記 Stub 實作
- 建立替換計劃
- 定期檢查和更新

---

## Q: 為什麼 JSON 解析會失敗？

**A:** 因為 LLM 服務是 Stub，返回的不是 JSON 格式：

### 問題流程

1. **EntityExtractor 期望 JSON**：
   ```python
   # 期望 LLM 返回：
   [{"name": "張三", "type": "Person"}, ...]
   ```

2. **Stub 返回文字**：
   ```python
   # 實際返回：
   "[Gemini] 回答: {prompt}\n\n這是模擬回答..."
   ```

3. **解析失敗**：
   - 正則表達式可能匹配到 `[Gemini]` 這樣的文字
   - 嘗試 `json.loads("[Gemini]")` 會失敗
   - 產生錯誤：`Expecting value: line 1 column 2 (char 1)`

### 解決方案

1. **改進 JSON 提取**（已完成）
   - 使用更嚴格的正則表達式
   - 支援多種 JSON 格式

2. **改進錯誤處理**（已完成）
   - 區分 JSON 錯誤和其他錯誤
   - 使用降級方案

3. **替換為真實 LLM**（未來）
   - 實作真正的 LLM API 整合
   - 確保返回 JSON 格式

---

## 相關檔案

- `app/services/llm_service.py` - LLM 服務（Stub）
- `app/services/cache_service.py` - 快取服務（Stub）
- `app/services/vector_service.py` - 向量服務（Stub）
- `docs/stub_explanation.md` - 詳細說明文檔


