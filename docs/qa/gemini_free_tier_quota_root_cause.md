# Gemini API 免費層配額錯誤根本原因分析

**更新時間：2025-12-26 14:50**  
**作者：AI Assistant**  
**修改摘要：深度分析為什麼已升級到付費層級（Tier 1）的 API Key 仍會出現免費層配額錯誤**

---

## 問題描述

**現象**：
- ✅ API Key 在 Google AI Studio 中顯示為 **Tier 1（付費層級）**
- ✅ 專案 ID: `gen-lang-client-0567547134`
- ❌ 但 API 呼叫時仍出現 `free_tier_requests: limit: 0` 錯誤

**錯誤訊息**：
```
429 You exceeded your current quota
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0
```

---

## 根本原因分析

### 關鍵發現

**Google Generative AI SDK 的配額機制**：
1. SDK 會自動使用 **API Key 關聯的 Google Cloud 專案** 的配額
2. 如果專案**未啟用計費**，系統會使用**免費層配額**
3. 如果專案**已啟用計費**，系統會使用**付費層配額**

### 為什麼會出現免費層配額錯誤？

**可能原因 1: API Key 關聯的專案未啟用計費** ⚠️ **最可能**

- API Key 在 AI Studio 中顯示為 Tier 1，但這**不代表專案已啟用計費**
- AI Studio 的 Tier 1 標記可能只是表示「可以升級」，而不是「已啟用計費」
- 如果專案 `gen-lang-client-0567547134` **未連結計費帳戶**，系統仍會使用免費層配額

**可能原因 2: 專案有計費帳戶，但配額設定有問題**

- 專案已連結計費帳戶，但配額設定未正確更新
- 可能需要手動啟用付費層配額

**可能原因 3: API Key 關聯到錯誤的專案**

- API Key 可能關聯到另一個未啟用計費的專案
- 需要確認 API Key 實際關聯的專案 ID

---

## 診斷步驟

### 步驟 1: 確認 API Key 關聯的專案

1. **訪問 Google Cloud Console**：
   - URL: https://console.cloud.google.com/apis/credentials
   - 找到您的 API Key

2. **檢查 API Key 詳細資訊**：
   - 點擊 API Key 查看詳細資訊
   - 確認「專案」欄位顯示的專案 ID
   - **關鍵**: 確認是否為 `gen-lang-client-0567547134`

### 步驟 2: 確認專案是否啟用計費

1. **訪問計費頁面**：
   - URL: https://console.cloud.google.com/billing
   - 選擇專案 `gen-lang-client-0567547134`

2. **檢查計費狀態**：
   - 確認專案是否已連結到計費帳戶
   - 確認計費帳戶狀態為「已啟用」
   - **如果未連結，需要連結計費帳戶**

### 步驟 3: 檢查配額設定

1. **訪問配額管理頁面**：
   - URL: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - 選擇專案 `gen-lang-client-0567547134`

2. **檢查配額項目**：
   - 查找 `generate_content` 相關配額
   - 確認是否有 **Tier 1** 或 **Paid Tier** 配額
   - **關鍵**: 如果只顯示 `free_tier` 配額，表示專案未啟用計費

### 步驟 4: 驗證 API Key 的實際行為

運行測試腳本並檢查錯誤訊息：
```bash
python scripts/test_gemini_llm.py
```

**如果錯誤訊息仍顯示 `free_tier`**：
- 確認專案未啟用計費（最可能）
- 或配額設定有問題

---

## 解決方案

### 方案 1: 啟用專案計費（最重要）⭐

1. **連結計費帳戶**：
   - 訪問：https://console.cloud.google.com/billing
   - 選擇專案 `gen-lang-client-0567547134`
   - 點擊「連結帳單帳戶」
   - 選擇或建立計費帳戶

2. **確認計費帳戶狀態**：
   - 確認計費帳戶已啟用且有效
   - 確認沒有未支付的費用

3. **等待配額更新**：
   - 連結計費帳戶後，配額可能需要幾分鐘更新
   - 重新運行測試腳本驗證

### 方案 2: 檢查並啟用付費層配額

1. **訪問配額管理頁面**：
   - URL: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
   - 選擇專案 `gen-lang-client-0567547134`

2. **啟用付費層配額**：
   - 查找 `generate_content` 相關配額
   - 如果只有免費層配額，點擊「申請增加配額」或「啟用」
   - 選擇 Tier 1 或 Paid Tier

### 方案 3: 確認 API Key 關聯正確

1. **檢查 API Key 專案關聯**：
   - 訪問：https://console.cloud.google.com/apis/credentials
   - 確認 API Key 關聯的專案是 `gen-lang-client-0567547134`

2. **如果關聯錯誤**：
   - 重新生成 API Key
   - 確保新 API Key 關聯到已啟用計費的專案

---

## 代碼層面的說明

### 當前實作

```python
genai.configure(api_key=self.api_key)
self._model = genai.GenerativeModel(model_name)
```

**說明**：
- `genai.configure()` 會自動使用 API Key 關聯的專案配額
- **無法在代碼中明確指定使用付費層或免費層**
- 配額層級由**專案的計費狀態**決定

### 為什麼無法在代碼中指定？

- Google Generative AI SDK **不提供**明確指定配額層級的參數
- 配額層級由 **API Key 關聯的專案** 自動決定
- 如果專案未啟用計費，系統會自動使用免費層配額

---

## 驗證步驟

### 1. 確認專案計費狀態

```bash
# 訪問 Google Cloud Console
# 檢查專案 gen-lang-client-0567547134 是否已連結計費帳戶
```

### 2. 重新測試

```bash
python scripts/test_gemini_llm.py
```

### 3. 檢查錯誤訊息

**如果錯誤訊息仍顯示 `free_tier`**：
- ❌ 專案未啟用計費（最可能）
- ❌ 或配額設定有問題

**如果錯誤訊息不再顯示 `free_tier`**：
- ✅ 問題已解決
- ✅ 系統現在使用付費層配額

---

## 總結

### 根本原因

**API Key 關聯的 Google Cloud 專案未啟用計費**，導致系統使用免費層配額。

### 關鍵要點

1. **AI Studio 的 Tier 1 標記 ≠ 專案已啟用計費**
   - Tier 1 可能只是表示「可以升級」
   - 需要確認專案實際的計費狀態

2. **配額層級由專案決定，不是 API Key**
   - API Key 本身不決定配額層級
   - 專案的計費狀態決定配額層級

3. **無法在代碼中明確指定配額層級**
   - SDK 會自動使用專案的配額
   - 必須在 Google Cloud Console 中啟用計費

### 解決方案

**優先步驟**：
1. ✅ 確認專案 `gen-lang-client-0567547134` 已連結計費帳戶
2. ✅ 確認計費帳戶已啟用且有效
3. ✅ 檢查配額設定，確認有付費層配額
4. ✅ 重新測試 API 呼叫

---

## 相關文檔

- `docs/qa/gemini_quota_error_analysis.md` - 配額錯誤分析
- `scripts/test_gemini_llm.py` - Gemini LLM 測試腳本
- Google Cloud Console: https://console.cloud.google.com/

