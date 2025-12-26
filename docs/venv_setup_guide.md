# 虛擬環境設置指南

## 問題：prometheus_client 在虛擬環境中找不到

### 錯誤訊息
```
ModuleNotFoundError: No module named 'prometheus_client'
```

### 根本原因

虛擬環境 `Langchain312` 中沒有安裝 `prometheus_client`，雖然系統 Python 環境有安裝，但虛擬環境是獨立的。

### 解決方案

#### 方案 1：在虛擬環境中安裝依賴（推薦）

```powershell
# 1. 確認虛擬環境已啟用
# 終端應該顯示 (Langchain312)

# 2. 安裝所有依賴
pip install -r requirements.txt

# 3. 或單獨安裝 prometheus_client
pip install prometheus_client>=0.19.0

# 4. 驗證安裝
python -c "from prometheus_client import Counter; print('OK')"
```

#### 方案 2：檢查虛擬環境狀態

```powershell
# 執行診斷腳本
python scripts\check_venv.py

# 這會顯示：
# - Python 路徑
# - 是否在虛擬環境中
# - 已安裝的依賴
# - 缺少的依賴
```

#### 方案 3：重新建立虛擬環境（如果問題持續）

```powershell
# 1. 停用當前環境
deactivate

# 2. 刪除舊環境（可選）
# Remove-Item -Recurse -Force Langchain312

# 3. 建立新環境
python -m venv Langchain312

# 4. 啟用環境
.\Langchain312\Scripts\Activate.ps1

# 5. 升級 pip
python -m pip install --upgrade pip

# 6. 安裝所有依賴
pip install -r requirements.txt

# 7. 驗證
python scripts\check_venv.py
```

### 驗證步驟

```powershell
# 1. 檢查 Python 路徑（應該指向虛擬環境）
python -c "import sys; print(sys.executable)"
# 應該類似: C:\...\Langchain312\Scripts\python.exe

# 2. 檢查 prometheus_client
python -c "from prometheus_client import Counter; print('✅ 成功')"

# 3. 檢查所有依賴
pip list | findstr -i "prometheus fastapi uvicorn aiosqlite"
```

### 常見問題

**Q: 為什麼 pip install 顯示已安裝，但導入失敗？**
A: 可能是 `pip` 和 `python` 使用不同的 Python 環境。使用 `python -m pip install` 確保使用相同的 Python。

**Q: 如何確認虛擬環境已正確啟用？**
A: 
- 終端提示符應該顯示 `(Langchain312)`
- `python -c "import sys; print(sys.executable)"` 應該指向虛擬環境目錄

**Q: 虛擬環境在哪裡？**
A: 通常在專案目錄或使用者目錄中。檢查 `sys.executable` 可以找到確切位置。

### 快速修復命令

```powershell
# 一行命令修復
python -m pip install -r requirements.txt && python -c "from prometheus_client import Counter; print('✅ 修復成功')"
```


