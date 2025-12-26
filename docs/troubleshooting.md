# GraphRAG 故障排除指南

## 問題：aiosqlite 導入錯誤

### 錯誤訊息
```
錯誤: aiosqlite is required for SQLiteGraphStore. Install it with: pip install aiosqlite
```

### 可能原因

1. **虛擬環境未啟用**
   - 確保在正確的虛擬環境中執行腳本
   - 檢查終端提示符是否顯示虛擬環境名稱（如 `(Langchain312)`）

2. **aiosqlite 安裝在錯誤的環境**
   - 確認當前 Python 環境與安裝 aiosqlite 的環境一致

3. **Python 路徑問題**
   - 腳本使用的 Python 與 pip 安裝的 Python 不同

### 解決方案

#### 方案 1：確認虛擬環境

```powershell
# 1. 確認虛擬環境已啟用
# 終端應該顯示 (Langchain312) 或其他虛擬環境名稱

# 2. 確認 Python 路徑
python -c "import sys; print(sys.executable)"

# 3. 確認 aiosqlite 已安裝
pip list | findstr aiosqlite

# 4. 如果未安裝，重新安裝
pip install aiosqlite>=0.19.0

# 5. 測試導入
python -c "import aiosqlite; print('OK')"
```

#### 方案 2：使用 requirements.txt 安裝所有依賴

```powershell
# 確保在專案根目錄
cd C:\Development\langChain\source\care_rag\care_rag_api

# 安裝所有依賴
pip install -r requirements.txt

# 驗證安裝
pip list | findstr aiosqlite
```

#### 方案 3：直接測試腳本

```powershell
# 測試導入
python scripts\test_import.py

# 如果導入成功，執行初始化
python scripts\init_graph_db.py
```

### 驗證步驟

1. **檢查 Python 環境**
   ```powershell
   python --version
   python -c "import sys; print(sys.executable)"
   ```

2. **檢查 aiosqlite**
   ```powershell
   python -c "import aiosqlite; print(aiosqlite.__version__)"
   ```

3. **測試 GraphStore 導入**
   ```powershell
   python -c "from app.core.graph_store import SQLiteGraphStore; print('OK')"
   ```

4. **執行初始化腳本**
   ```powershell
   python scripts\init_graph_db.py
   ```

### 如果問題仍然存在

1. **重新建立虛擬環境**
   ```powershell
   # 停用當前環境
   deactivate
   
   # 建立新環境
   python -m venv venv
   
   # 啟用環境
   .\venv\Scripts\Activate.ps1
   
   # 安裝依賴
   pip install -r requirements.txt
   ```

2. **檢查專案路徑**
   - 確保在正確的專案目錄中執行腳本
   - 檢查 `sys.path` 是否包含專案根目錄

3. **手動測試**
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
   
   # 測試導入
   try:
       import aiosqlite
       print(f"aiosqlite version: {aiosqlite.__version__}")
   except ImportError as e:
       print(f"Import error: {e}")
   ```

### 常見問題

**Q: 為什麼 pip install 成功但導入失敗？**
A: 可能是 Python 環境不一致。確認 `python` 和 `pip` 使用相同的 Python 解釋器。

**Q: 如何確認虛擬環境已啟用？**
A: 終端提示符應該顯示虛擬環境名稱，如 `(Langchain312) PS C:\...`

**Q: Windows PowerShell 執行腳本失敗？**
A: 使用 `python scripts\init_graph_db.py` 而不是 `python scripts/init_graph_db.py`


