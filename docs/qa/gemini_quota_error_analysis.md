# Gemini API 配額錯誤深度分析

**更新時間：2025-12-26 14:45**  
**作者：AI Assistant**  
**修改摘要：更新分析 - API Key 已升級到 Tier 1（付費層），但系統仍嘗試使用免費層配額**
**更新時間：2025-12-26 14:35**  
**作者：AI Assistant**  
**修改摘要：深度分析 Gemini API 429 配額錯誤，提供診斷和解決方案**

---

## ⚠️ 重要更新

根據 Google AI Studio 截圖確認：
- ✅ **API Key 狀態**: 已升級到 **Tier 1（付費層級）**
- ❌ **問題**: 系統仍嘗試使用 **免費層配額**（free_tier），導致配額限制為 0
- 🔍 **根本原因**: 付費層 API Key 不應該使用免費層配額，需要檢查 Google Cloud Console 的配額設定

---

## 錯誤現象

### 測試結果摘要

從 `scripts/test_gemini_llm.py` 測試結果：

```
✅ 通過: API Key 配置
✅ 通過: 模型初始化
❌ 失敗: 基本生成（429 配額錯誤）
❌ 失敗: 串流生成（429 配額錯誤）
❌ 失敗: LLMService 整合（429 配額錯誤）
✅ 通過: 可用模型（找到 34 個模型，gemini-2.0-flash 可用）

總計: 3/6 測試通過
```

### 錯誤訊息詳情

```
429 You exceeded your current quota, please check your plan and billing details.

* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0, model: gemini-2.0-flash
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0, model: gemini-2.0-flash

Please retry in 40.324391884s.
```

---

## 深度分析

### 1. 配額限制分析

**關鍵發現**：
- `free_tier_requests: limit: 0` - **免費層請求限制為 0**
- `free_tier_input_token_count: limit: 0` - **免費層 token 限制為 0**

**解讀**：
- ❌ **免費層配額為 0**，意味著：
  1. 該 API Key 可能沒有免費層配額
  2. 或免費層配額已完全用完
  3. 或 `gemini-2.0-flash` 模型不支援免費層

### 2. 模型可用性分析

**測試結果**：
- ✅ 模型 `gemini-2.0-flash` 在可用列表中（34 個模型中的一個）
- ✅ 模型初始化成功
- ❌ 但 API 呼叫時配額限制為 0

**推論**：
- 模型本身是可用的
- 但該模型可能**不支援免費層**，需要付費方案

### 3. API Key 狀態分析

**測試結果**：
- ✅ API Key 已配置且有效
- ✅ 可以成功初始化模型
- ✅ 可以查詢可用模型列表

**結論**：
- API Key 本身沒有問題
- 問題在於**配額限制**，而非 API Key 無效

### 4. 降級機制分析

**當前行為**：
- ✅ 系統正確檢測到 429 錯誤
- ✅ 自動降級到 Stub 模式
- ✅ 繼續處理（使用 rule-based 提取）

**評估**：
- 降級機制工作正常
- 但無法使用真實的 LLM API

---

## 根本原因

### 主要原因

1. **配額層級不匹配** ⚠️ **關鍵問題**
   - API Key 已升級到 **Tier 1（付費層級）**
   - 但錯誤訊息顯示嘗試使用 **免費層配額**（free_tier）
   - 付費層 API Key 應該使用付費層配額，而不是免費層

2. **Google Cloud Console 配額設定問題**
   - 可能需要在 Google Cloud Console 中啟用付費層配額
   - 或需要檢查專案的配額限制設定
   - 付費層可能有不同的配額限制和計費方式

3. **模型選擇問題**
   - `gemini-2.0-flash` 是較新的模型
   - 可能需要特定的配額設定或啟用特定功能

4. **缺少重試機制**
   - 當前實作直接降級，沒有等待配額重置
   - 沒有嘗試其他模型

---

## 解決方案

### 方案 1: 檢查並配置 Google Cloud Console 配額設定（優先推薦）⭐

**步驟**：
1. 訪問 Google Cloud Console：
   - https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - 或通過專案 ID: `gen-lang-client-0567547134`

2. 檢查配額設定：
   - 確認 **Tier 1** 配額已啟用
   - 檢查 `generate_content` 相關配額限制
   - 確認 `gemini-2.0-flash` 模型的配額設定

3. 啟用必要的配額：
   - 如果配額未啟用，點擊「啟用」或「申請增加配額」
   - 確認計費帳戶已正確連結

4. 重新運行測試：
   ```bash
   python scripts/test_gemini_llm.py
   ```

**優點**：
- ✅ 解決根本問題（配額層級不匹配）
- ✅ 可以使用付費層的所有功能
- ✅ 不需要修改代碼或切換模型

### 方案 2: 切換到其他模型（備選方案）

**步驟**：
1. 在 `.env` 檔案中設置：
   ```bash
   GEMINI_MODEL_NAME=gemini-1.5-flash
   ```
   或
   ```bash
   GEMINI_MODEL_NAME=gemini-1.0-pro
   ```

2. 重新運行測試：
   ```bash
   python scripts/test_gemini_llm.py
   ```

**優點**：
- ✅ 可能立即生效
- ✅ 不需要修改代碼
- ⚠️ 但這不是根本解決方案（配額層級問題仍然存在）

### 方案 2: 實現重試機制

**實作**：
- 檢測 429 錯誤
- 解析 `retry_delay`（建議等待時間）
- 等待後自動重試
- 如果多次重試失敗，再降級到 Stub

**優點**：
- ✅ 自動處理暫時性配額限制
- ✅ 提高成功率

**缺點**：
- ⚠️ 需要修改代碼
- ⚠️ 如果配額真的為 0，重試無效

### 方案 3: 檢查計費帳戶和專案設定

**步驟**：
1. 訪問 Google Cloud Console：
   - https://console.cloud.google.com/billing
   - 確認計費帳戶已啟用且有效

2. 檢查專案設定：
   - 專案 ID: `gen-lang-client-0567547134`
   - 確認專案已連結到正確的計費帳戶
   - 確認 API 已啟用

3. 檢查 API 啟用狀態：
   - https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - 確認 Generative Language API 已啟用

**優點**：
- ✅ 確保所有設定正確
- ✅ 解決可能的配置問題

**注意**：
- ⚠️ API Key 已升級到 Tier 1，但可能需要確認計費帳戶設定

### 方案 4: 使用多個 API Key 輪換

**實作**：
- 配置多個 API Key
- 當一個配額用完時，自動切換到另一個

**優點**：
- ✅ 提高可用性
- ✅ 分散配額使用

**缺點**：
- ⚠️ 需要多個 Google 帳號
- ⚠️ 實作較複雜

---

## 建議的修復步驟

### 立即行動（推薦順序）

#### 步驟 1: 檢查 Google Cloud Console 配額設定（最重要）⭐

1. **訪問配額管理頁面**：
   - URL: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - 專案 ID: `gen-lang-client-0567547134`
   - 或直接搜索：`generativelanguage.googleapis.com quotas`

2. **檢查配額項目**：
   - 查找 `generate_content` 相關配額
   - 確認是否有 **Tier 1** 或 **Paid Tier** 配額
   - 檢查 `gemini-2.0-flash` 模型的配額限制
   - **關鍵**: 確認不是只顯示 `free_tier` 配額

3. **啟用或申請配額**：
   - 如果 Tier 1 配額未啟用，點擊「啟用」或「申請增加配額」
   - 確認配額限制不為 0

#### 步驟 2: 檢查計費帳戶

1. **訪問計費頁面**：
   - URL: https://console.cloud.google.com/billing
   - 確認計費帳戶已啟用且狀態正常

2. **確認專案連結**：
   - 確認專案 `gen-lang-client-0567547134` 已連結到計費帳戶
   - 如果未連結，需要連結計費帳戶

#### 步驟 3: 檢查 API 啟用狀態

1. **訪問 API 庫**：
   - URL: https://console.cloud.google.com/apis/library/generativelanguage.googleapis.com
   - 確認 Generative Language API 狀態為「已啟用」

2. **檢查 API 詳細資訊**：
   - 確認 API 已啟用且未受限
   - 檢查是否有任何限制或警告

#### 步驟 4: 重新測試

```bash
python scripts/test_gemini_llm.py
```

#### 步驟 5: 如果仍然失敗

1. **檢查錯誤訊息**：
   - 如果仍顯示 `free_tier`，表示配額層級設定有問題
   - 可能需要聯繫 Google Cloud 支援

2. **臨時解決方案**：
   - 嘗試切換到 `gemini-1.5-flash` 模型
   - 但這不是根本解決方案

### 長期優化

1. **實現重試機制**：
   - 添加指數退避重試
   - 解析 retry_delay 並等待

2. **模型自動切換**：
   - 當一個模型配額用完時，自動嘗試其他模型

3. **配額監控**：
   - 記錄配額使用情況
   - 提前警告配額即將用完

---

## 測試驗證

### 驗證步驟

1. **切換模型後測試**：
   ```bash
   python scripts/test_gemini_llm.py
   ```

2. **檢查測試結果**：
   - 如果基本生成測試通過 → 模型切換成功
   - 如果仍然失敗 → 需要檢查配額設定

3. **處理 PDF**：
   ```bash
   python scripts/process_pdf_to_graph.py your_document.pdf
   ```
   - 檢查是否還出現 429 錯誤
   - 確認是否使用真實 API

---

## 相關文檔

- `docs/qa/llm_real_api_implementation_guide.md` - LLM 真實 API 實作指南
- `docs/qa/api_startup_errors_qa.md` - API 啟動錯誤處理
- `scripts/test_gemini_llm.py` - Gemini LLM 測試腳本

---

## 總結

### 當前狀態

- ✅ **API Key**: 有效且已升級到 **Tier 1（付費層級）**
- ✅ **模型初始化**: 成功
- ✅ **模型可用性**: gemini-2.0-flash 可用
- ❌ **API 呼叫**: 429 配額錯誤（**免費層限制為 0**）
- ⚠️ **關鍵問題**: API Key 是付費層，但系統嘗試使用免費層配額

### 根本原因

**配額層級不匹配**：
- API Key 已升級到 **Tier 1（付費層級）**
- 但錯誤訊息顯示嘗試使用 **免費層配額**（free_tier）
- 需要在 Google Cloud Console 中檢查並配置付費層配額

### 推薦解決方案

**優先檢查 Google Cloud Console 配額設定**：
1. 訪問配額管理頁面
2. 確認 Tier 1 配額已啟用
3. 檢查 `generate_content` 相關配額限制
4. 確認計費帳戶已正確連結

### 下一步

1. 修改 `.env` 檔案：`GEMINI_MODEL_NAME=gemini-1.5-flash`
2. 重新運行測試腳本驗證
3. 如果成功，繼續處理 PDF 文檔

