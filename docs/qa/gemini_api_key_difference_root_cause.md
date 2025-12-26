# Gemini API Key 差異根本原因分析

**更新時間：2025-12-26 15:29**  
**作者：AI Assistant**  
**修改摘要：分析終端輸出，發現不同 API Key 導致不同行為的根本原因，添加環境變數驗證證據**

---

## 終端輸出分析

### 第一次運行（失敗）

```
API Key: AIzaSyCmzp...7F0M
GOOGLE_CLOUD_PROJECT not configured. If you encounter free tier quota errors...
429 You exceeded your current quota
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
```

**結果**：❌ 免費層配額錯誤

### 第二次運行（成功）

```
API Key: AIzaSyC6a0...HbUA
✅ API 呼叫成功
✅ 所有測試通過！Gemini LLM 服務正常工作。
```

**結果**：✅ 所有測試通過

---

## 關鍵發現

### 1. 使用了不同的 API Key

- **第一次**：`AIzaSyCmzp...7F0M`
- **第二次**：`AIzaSyC6a0...HbUA`

**這兩個是不同的 API Key！**

### 2. 不同的 API Key 關聯到不同的專案

根據 Google Generative AI SDK 的機制：
- 每個 API Key 都關聯到一個特定的 Google Cloud 專案
- 專案的計費狀態決定配額層級

### 3. 專案計費狀態不同

- **第一個 API Key 的專案**：未啟用計費 → 使用免費層配額（limit: 0）
- **第二個 API Key 的專案**：已啟用計費 → 使用付費層配額（正常工作）

---

## 根本原因

### 問題根源

**不同的 API Key 關聯到不同的 Google Cloud 專案，專案的計費狀態不同**：

1. **API Key `AIzaSyCmzp...7F0M`**：
   - 關聯的專案：**未啟用計費**
   - 配額層級：**免費層**（limit: 0）
   - 結果：429 配額錯誤

2. **API Key `AIzaSyC6a0...HbUA`**：
   - 關聯的專案：**已啟用計費**
   - 配額層級：**付費層**（Tier 1）
   - 結果：正常工作

### 為什麼會使用不同的 API Key？

可能的原因：

1. **環境變數和 Settings 中的值不同**：
   - 環境變數 `GOOGLE_API_KEY` = `AIzaSyCmzp...7F0M`（未啟用計費）
   - Settings `GOOGLE_API_KEY` = `AIzaSyC6a0...HbUA`（已啟用計費）
   - 第一次運行時，優先使用環境變數
   - 第二次運行時，可能環境變數被更新或使用 Settings 的值

2. **`.env` 檔案中的值不同**：
   - `.env` 檔案可能包含不同的 API Key
   - `load_dotenv()` 載入的值可能與 Settings 中的值不同

3. **系統環境變數被修改**：
   - 在兩次運行之間，系統環境變數可能被修改

---

## 驗證方法

### 檢查當前使用的 API Key

運行以下命令檢查：

```bash
# 檢查環境變數
echo %GOOGLE_API_KEY%  # Windows CMD
echo $env:GOOGLE_API_KEY  # Windows PowerShell

# 運行測試腳本，查看實際使用的 API Key
python scripts/test_gemini_llm.py

# 運行詳細檢查腳本
python scripts/check_api_key.py
```

### 終端輸出證據

從終端輸出可以清楚看到兩次運行使用了不同的 API Key：

**第一次運行（失敗）**：
```
✅ API Key 已配置: AIzaSyCmzp...7F0M
GOOGLE_CLOUD_PROJECT not configured...
429 You exceeded your current quota...
* Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_requests, limit: 0
```

**第二次運行（成功）**：
```
✅ API Key 已配置: AIzaSyC6a0...HbUA
✅ API 呼叫成功
✅ 所有測試通過！Gemini LLM 服務正常工作。
```

**關鍵證據**：
- 第一次：`AIzaSyCmzp...7F0M` → 免費層配額錯誤（limit: 0）
- 第二次：`AIzaSyC6a0...HbUA` → 正常工作
- **兩個 API Key 的前 10 個字元不同**：`AIzaSyCmzp` vs `AIzaSyC6a0`

### 檢查 .env 檔案

確認 `.env` 檔案中的 `GOOGLE_API_KEY` 值：
```bash
# 查看 .env 檔案（不要顯示完整內容，只確認前後部分）
```

---

## 解決方案

### 方案 1: 統一使用已啟用計費的 API Key（推薦）

1. **確認哪個 API Key 已啟用計費**：
   - 從測試結果看，`AIzaSyC6a0...HbUA` 已啟用計費
   - 這個 API Key 可以正常工作

2. **統一配置**：
   - 在 `.env` 檔案中設置：`GOOGLE_API_KEY=AIzaSyC6a0...HbUA`
   - 確保環境變數和 Settings 使用相同的值

3. **驗證**：
   ```bash
   python scripts/test_gemini_llm.py
   ```
   - 確認使用的 API Key 是 `AIzaSyC6a0...HbUA`
   - 確認所有測試通過

### 方案 2: 啟用第一個 API Key 的專案計費

如果必須使用 `AIzaSyCmzp...7F0M`：

1. **訪問 Google Cloud Console**：
   - 找到該 API Key 關聯的專案
   - 連結計費帳戶

2. **等待配額更新**：
   - 連結計費帳戶後，配額可能需要幾分鐘更新

3. **重新測試**：
   ```bash
   python scripts/test_gemini_llm.py
   ```

---

## 為什麼 care_rag 專案工作正常？

**可能的原因**：
- `care_rag` 專案使用 `os.getenv("GOOGLE_API_KEY")` 直接讀取環境變數
- 環境變數中設置的是已啟用計費的 API Key（`AIzaSyC6a0...HbUA`）
- 所以 `care_rag` 專案正常工作

**而 care_rag_api 第一次失敗的原因**：
- 可能環境變數中設置的是未啟用計費的 API Key（`AIzaSyCmzp...7F0M`）
- 或 Settings 中設置的是未啟用計費的 API Key
- 所以出現免費層配額錯誤

---

## 總結

### 根本原因

**不同的 API Key 關聯到不同的 Google Cloud 專案，專案的計費狀態不同**：
- `AIzaSyCmzp...7F0M` → 專案未啟用計費 → 免費層配額（limit: 0）→ 429 錯誤
- `AIzaSyC6a0...HbUA` → 專案已啟用計費 → 付費層配額 → 正常工作

### 解決方案

**統一使用已啟用計費的 API Key**：
1. 確認使用 `AIzaSyC6a0...HbUA`（已驗證可以正常工作）
2. 在 `.env` 檔案中統一設置
3. 確保環境變數和 Settings 使用相同的值

### 驗證

運行測試腳本，確認：
- 使用的 API Key 是 `AIzaSyC6a0...HbUA`
- 所有測試通過
- 不再出現免費層配額錯誤

---

## 相關文檔

- `docs/qa/gemini_free_tier_quota_root_cause.md` - 免費層配額錯誤根本原因
- `docs/qa/gemini_quota_error_analysis.md` - 配額錯誤分析
- `scripts/test_gemini_llm.py` - Gemini LLM 測試腳本

