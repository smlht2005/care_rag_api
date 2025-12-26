# 環境變數優先順序分析

**更新時間：2025-12-26 15:35**  
**作者：AI Assistant**  
**修改摘要：分析 .env 檔案和環境變數的優先順序問題**

---

## 當前代碼邏輯

### 1. `app/config.py` 中的載入順序

```python
from dotenv import load_dotenv

# 確保 .env 檔案在 Settings 初始化前已載入（與 care_rag 一致）
load_dotenv()

class Settings(BaseSettings):
    GOOGLE_API_KEY: Optional[str] = None
    class Config:
        env_file = ".env"
```

**說明**：
- `load_dotenv()` 會將 `.env` 檔案中的變數載入到 `os.environ`
- `Settings` 類別會從 `os.environ` 讀取變數（因為 `env_file = ".env"`）

### 2. `app/services/llm_service.py` 中的優先順序

```python
self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
```

**當前優先順序**：
1. `api_key` 參數（如果提供）
2. `os.getenv("GOOGLE_API_KEY")` - **環境變數優先**
3. `settings.GOOGLE_API_KEY` - **Settings 其次**

---

## 問題分析

### 問題 1：環境變數優先於 .env 檔案

**當前行為**：
- 如果系統環境變數 `GOOGLE_API_KEY` 已設置，`.env` 檔案中的值會被忽略
- 這可能導致專案配置不一致

**範例場景**：
```bash
# 系統環境變數（全局）
export GOOGLE_API_KEY=AIzaSyCmzp...7F0M  # 未啟用計費的專案

# .env 檔案（專案特定）
GOOGLE_API_KEY=AIzaSyC6a0...HbUA  # 已啟用計費的專案

# 結果：使用系統環境變數（AIzaSyCmzp...7F0M），.env 檔案被忽略
```

### 問題 2：終端輸出證據

從終端輸出可以看到：
- **第一次運行**：使用 `AIzaSyCmzp...7F0M`（系統環境變數）→ 免費層配額錯誤
- **第二次運行**：使用 `AIzaSyC6a0...HbUA`（可能是 .env 或 Settings）→ 正常工作

**這證實了優先順序問題**：
- 第一次運行時，系統環境變數優先，使用了未啟用計費的 API Key
- 第二次運行時，可能環境變數被清除或修改，使用了 `.env` 檔案中的值

---

## 建議的優先順序

### 正確的優先順序應該是：

1. **`.env` 檔案優先**（專案特定配置）
2. **系統環境變數其次**（系統級配置）

**理由**：
- `.env` 檔案是專案特定的配置，應該優先
- 系統環境變數是全局配置，作為後備
- 這樣可以確保專案配置的一致性

### 建議的修改

#### 方案 1：修改 `llm_service.py`（推薦）

```python
# 優先使用 .env 檔案（Settings），其次使用環境變數
self.api_key = api_key or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
```

**優點**：
- `.env` 檔案優先，確保專案配置一致性
- 環境變數作為後備，保持靈活性

#### 方案 2：修改 `config.py` 中的 `load_dotenv()` 行為

```python
# 不覆蓋現有環境變數，但優先從 .env 檔案讀取
load_dotenv(override=False)  # 不覆蓋系統環境變數

# 然後在 Settings 中優先讀取 .env 檔案
class Settings(BaseSettings):
    GOOGLE_API_KEY: Optional[str] = None
    
    @classmethod
    def from_env_file(cls):
        """優先從 .env 檔案讀取"""
        from dotenv import dotenv_values
        env_values = dotenv_values(".env")
        return env_values.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")
```

**優點**：
- 更明確的優先順序控制
- 可以分別處理 `.env` 檔案和環境變數

---

## 當前代碼的問題

### 問題 1：優先順序不一致

**當前邏輯**：
```python
os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY
```

**問題**：
- `os.getenv()` 會優先讀取系統環境變數
- 即使 `.env` 檔案中有正確的值，也會被系統環境變數覆蓋
- 這導致專案配置不一致

### 問題 2：與 `care_rag` 專案不一致

**`care_rag` 專案的邏輯**：
```python
# care_rag/main.py
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
```

**說明**：
- `care_rag` 專案直接使用 `os.getenv()`，依賴環境變數
- 如果環境變數未設置，會失敗
- 這與 `care_rag_api` 的邏輯不同

---

## 建議的解決方案

### 方案 1：修改優先順序（推薦）

**修改 `app/services/llm_service.py`**：

```python
def __init__(self, api_key: Optional[str] = None):
    # 優先使用 .env 檔案（Settings），其次使用環境變數
    # 這樣可以確保專案配置的一致性
    self.api_key = api_key or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
```

**優點**：
- `.env` 檔案優先，確保專案配置一致性
- 環境變數作為後備，保持靈活性
- 簡單直接，不需要修改其他代碼

### 方案 2：明確的優先順序控制

**修改 `app/services/llm_service.py`**：

```python
def __init__(self, api_key: Optional[str] = None):
    if api_key:
        self.api_key = api_key
    elif settings.GOOGLE_API_KEY:
        # 優先使用 .env 檔案（Settings）
        self.api_key = settings.GOOGLE_API_KEY
        self.logger.debug("Using GOOGLE_API_KEY from Settings (.env file)")
    elif os.getenv("GOOGLE_API_KEY"):
        # 其次使用環境變數
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.logger.debug("Using GOOGLE_API_KEY from environment variable")
    else:
        self.api_key = None
```

**優點**：
- 明確的優先順序控制
- 可以記錄使用的來源
- 更容易調試

---

## 驗證方法

### 1. 檢查當前優先順序

運行檢查腳本：
```bash
python scripts/check_env_priority.py
```

### 2. 測試不同場景

**場景 1：只有 .env 檔案**
```bash
# 清除環境變數
unset GOOGLE_API_KEY  # Linux/macOS
set GOOGLE_API_KEY=  # Windows CMD
$env:GOOGLE_API_KEY = $null  # Windows PowerShell

# 運行測試
python scripts/test_gemini_llm.py
```

**場景 2：環境變數和 .env 檔案都有**
```bash
# 設置不同的值
export GOOGLE_API_KEY=AIzaSyCmzp...7F0M  # 系統環境變數
# .env 檔案中：GOOGLE_API_KEY=AIzaSyC6a0...HbUA

# 運行測試，檢查使用的值
python scripts/test_gemini_llm.py
```

---

## 總結

### 當前問題

1. **優先順序錯誤**：環境變數優先於 `.env` 檔案
2. **配置不一致**：專案配置可能被系統環境變數覆蓋
3. **終端輸出證據**：兩次運行使用了不同的 API Key

### 建議修改

**優先順序應該改為**：
1. `.env` 檔案（專案特定配置）優先
2. 系統環境變數（系統級配置）其次

**修改代碼**：
```python
# 從
self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or settings.GOOGLE_API_KEY

# 改為
self.api_key = api_key or settings.GOOGLE_API_KEY or os.getenv("GOOGLE_API_KEY")
```

這樣可以確保專案配置的一致性，避免被系統環境變數覆蓋。

---

## 相關文檔

- [Gemini API Key 差異根本原因分析](./gemini_api_key_difference_root_cause.md)
- [環境變數優先順序檢查腳本](../scripts/check_env_priority.py)

