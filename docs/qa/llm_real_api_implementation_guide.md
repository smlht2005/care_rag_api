# LLM 真實 API 實作指南

**更新時間：2025-12-26 13:28**  
**作者：AI Assistant**  
**修改摘要：建立完整的 LLM 真實 API 實作指南，包含 Gemini、OpenAI、DeepSeek 三種 provider 的配置和使用說明**

---

## 概述

本指南說明如何將 Care RAG API 的 LLM 服務從 **Stub 模式**切換到**真實 API 模式**，以獲得更好的實體和關係提取準確度。

### 當前狀態

- ✅ **已實作**：真實 API 整合（Gemini、OpenAI、DeepSeek）
- ✅ **已實作**：自動降級機制（API 失敗時自動使用 Stub）
- ✅ **已實作**：串流支援（SSE 和 WebSocket）
- ⚠️ **需要配置**：API Key 和依賴套件

---

## 快速開始

### 步驟 1: 安裝依賴套件

```bash
pip install google-generativeai openai httpx
```

或使用 requirements.txt：

```bash
pip install -r requirements.txt
```

### 步驟 2: 配置 API Key

在 `.env` 檔案中添加對應的 API Key：

```bash
# 選擇一個 provider（gemini, openai, deepseek）
LLM_PROVIDER=gemini

# Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# OpenAI API Key（可選）
OPENAI_API_KEY=your_openai_api_key_here

# DeepSeek API Key（可選）
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

### 步驟 3: 重啟服務

```bash
# 重啟 FastAPI 服務
uvicorn app.main:app --reload
```

---

## 詳細配置說明

### Gemini API

#### 1. 獲取 API Key

1. 訪問 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 登入 Google 帳號
3. 點擊「Create API Key」
4. 複製 API Key

#### 2. 配置環境變數

```bash
# .env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your_key_here
```

#### 3. 驗證配置

系統啟動時會檢查：
- ✅ 如果 `google-generativeai` 已安裝且 `GEMINI_API_KEY` 已配置 → 使用真實 API
- ⚠️ 如果缺少任一條件 → 自動降級到 Stub 模式（會記錄警告）

#### 4. 日誌確認

查看啟動日誌，應該看到：

```
INFO: GeminiLLM: Gemini API initialized with real API key
```

如果看到：

```
WARNING: GeminiLLM: google-generativeai not installed, using stub mode
WARNING: GeminiLLM: GEMINI_API_KEY not configured, using stub mode
```

表示仍在使用 Stub 模式。

---

### OpenAI API

#### 1. 獲取 API Key

1. 訪問 [OpenAI Platform](https://platform.openai.com/)
2. 登入帳號
3. 前往「API Keys」頁面
4. 點擊「Create new secret key」
5. 複製 API Key

#### 2. 配置環境變數

```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...your_key_here
```

#### 3. 驗證配置

系統啟動時會檢查：
- ✅ 如果 `openai` SDK 已安裝且 `OPENAI_API_KEY` 已配置 → 使用真實 API
- ⚠️ 如果缺少任一條件 → 自動降級到 Stub 模式

#### 4. 日誌確認

查看啟動日誌，應該看到：

```
INFO: OpenAILLM: OpenAI API initialized with real API key
```

---

### DeepSeek API

#### 1. 獲取 API Key

1. 訪問 [DeepSeek Platform](https://platform.deepseek.com/)
2. 登入帳號
3. 前往「API Keys」頁面
4. 創建新的 API Key
5. 複製 API Key

#### 2. 配置環境變數

```bash
# .env
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-...your_key_here
```

#### 3. 驗證配置

系統啟動時會檢查：
- ✅ 如果 `httpx` 已安裝且 `DEEPSEEK_API_KEY` 已配置 → 使用真實 API
- ⚠️ 如果缺少任一條件 → 自動降級到 Stub 模式

#### 4. 日誌確認

查看啟動日誌，應該看到：

```
INFO: DeepSeekLLM: DeepSeek API initialized with real API key
```

---

## 功能對比

### Stub 模式 vs 真實 API 模式

| 功能 | Stub 模式 | 真實 API 模式 |
|------|----------|-------------|
| **實體提取** | 規則基礎（簡單） | LLM 提取（準確） |
| **關係提取** | 共現關係（有限） | LLM 提取（豐富） |
| **準確度** | 低 | 高 |
| **關係類型** | 少 | 多 |
| **中文支援** | 基本 | 完整 |
| **API Key** | 不需要 | 需要 |
| **費用** | 免費 | 按使用量計費 |
| **網路連線** | 不需要 | 需要 |

---

## 使用場景建議

### 開發和測試階段

**推薦：Stub 模式**
- ✅ 不需要 API Key
- ✅ 不需要網路連線
- ✅ 快速測試功能
- ⚠️ 準確度較低，但足夠測試流程

### 生產環境

**推薦：真實 API 模式**
- ✅ 高準確度
- ✅ 豐富的關係類型
- ✅ 完整的中文支援
- ⚠️ 需要 API Key 和網路連線
- ⚠️ 可能產生費用

---

## 降級機制

系統內建自動降級機制，確保穩定性：

### 觸發條件

1. **API Key 未配置** → 自動使用 Stub
2. **依賴套件未安裝** → 自動使用 Stub
3. **API 呼叫失敗** → 自動降級到 Stub
4. **網路連線問題** → 自動降級到 Stub

### 日誌範例

```
WARNING: GeminiLLM: GEMINI_API_KEY not configured, using stub mode
ERROR: GeminiLLM: Gemini API call failed: Connection timeout, falling back to stub
```

### 優點

- ✅ 系統永遠不會因為 API 問題而崩潰
- ✅ 開發階段可以無 API Key 運行
- ✅ 生產環境 API 故障時自動降級

---

## 測試真實 API

### 1. 測試實體提取

```python
# 測試腳本
from app.services.llm_service import LLMService

llm = LLMService(provider="gemini")
prompt = "從以下文本提取實體：長期照護2.0政策包含居家服務、日間照顧等項目。"
result = await llm.generate(prompt)
print(result)
```

### 2. 測試關係提取

```python
prompt = "從以下文本提取關係：長期照護政策包含居家服務。"
result = await llm.generate(prompt)
print(result)
```

### 3. 處理 PDF 文檔

```bash
python scripts/process_pdf_to_graph.py data/example/your_document.pdf
```

**預期結果**：
- ✅ 實體數量大幅增加
- ✅ 關係數量大幅增加
- ✅ 關係類型更豐富
- ✅ 不再出現 "LLM entity extraction returned empty" 警告

---

## 常見問題

### Q1: 為什麼還是看到 "LLM entity extraction returned empty" 警告？

**A**: 這表示：
1. API Key 未配置或無效
2. 依賴套件未安裝
3. 系統自動降級到 Stub 模式

**解決方案**：
1. 檢查 `.env` 檔案中的 API Key
2. 確認已安裝 `google-generativeai` 或 `openai`
3. 查看啟動日誌確認 API 初始化狀態

### Q2: 如何確認正在使用真實 API？

**A**: 檢查日誌：
- ✅ 看到 `"API initialized with real API key"` → 使用真實 API
- ⚠️ 看到 `"using stub mode"` → 使用 Stub

### Q3: API 呼叫失敗怎麼辦？

**A**: 系統會自動降級到 Stub 模式，不會崩潰。檢查：
1. API Key 是否有效
2. 網路連線是否正常
3. API 服務是否可用
4. 查看錯誤日誌了解具體原因

### Q4: 可以同時配置多個 API Key 嗎？

**A**: 可以，但一次只能使用一個 provider。透過 `LLM_PROVIDER` 環境變數切換。

### Q5: 如何切換 provider？

**A**: 修改 `.env` 檔案：

```bash
# 切換到 OpenAI
LLM_PROVIDER=openai

# 切換到 DeepSeek
LLM_PROVIDER=deepseek

# 切換到 Gemini
LLM_PROVIDER=gemini
```

然後重啟服務。

---

## 成本考量

### Gemini API

- **免費額度**：每月 60 次請求（免費層級）
- **付費方案**：按 token 計費
- **參考**：https://ai.google.dev/pricing

### OpenAI API

- **免費額度**：無（需要付費）
- **付費方案**：按 token 計費
- **參考**：https://openai.com/pricing

### DeepSeek API

- **免費額度**：有限額度
- **付費方案**：按 token 計費
- **參考**：https://platform.deepseek.com/pricing

---

## 最佳實踐

### 1. 開發階段

- ✅ 使用 Stub 模式進行功能開發
- ✅ 不需要 API Key，快速迭代

### 2. 測試階段

- ✅ 使用真實 API 測試準確度
- ✅ 驗證實體和關係提取品質

### 3. 生產環境

- ✅ 使用真實 API 獲得最佳準確度
- ✅ 監控 API 使用量和成本
- ✅ 設定 API 呼叫限制和錯誤處理

### 4. 錯誤處理

- ✅ 依賴系統內建的降級機制
- ✅ 監控日誌中的 API 錯誤
- ✅ 設定告警通知

---

## 相關文檔

- `docs/qa/llm_fallback_warning_qa.md` - LLM 降級警告說明
- `docs/relation_extraction_issue_analysis.md` - 關係提取問題分析
- `app/services/llm_service.py` - LLM 服務實作
- `app/config.py` - 配置檔案

---

## 總結

**實作完成**：✅ 真實 LLM API 整合已實作

**使用方式**：
1. 安裝依賴：`pip install google-generativeai openai httpx`
2. 配置 API Key：在 `.env` 檔案中添加對應的 Key
3. 重啟服務：系統會自動檢測並使用真實 API

**降級機制**：✅ 自動降級確保系統穩定性

**下一步**：配置 API Key 並測試真實 API 的實體和關係提取效果！

