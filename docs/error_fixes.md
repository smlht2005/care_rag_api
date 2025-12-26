# 錯誤修復記錄

## 錯誤 1: ModuleNotFoundError: No module named 'prometheus_client'

### 錯誤訊息
```
File "app\utils\metrics.py", line 4, in <module>
    from prometheus_client import Counter, Histogram, Gauge, start_http_server
ModuleNotFoundError: No module named 'prometheus_client'
```

### 根本原因
- uvicorn 在虛擬環境 `Langchain312` 中運行
- `prometheus_client` 沒有安裝在該虛擬環境中
- 雖然系統 Python 環境有安裝，但虛擬環境是獨立的

### 解決方案
```powershell
# 確保在虛擬環境中
# 終端應該顯示 (Langchain312)

# 安裝所有依賴
pip install -r requirements.txt

# 或單獨安裝
pip install prometheus_client>=0.19.0
```

### 驗證
```powershell
# 檢查是否安裝成功
pip list | findstr prometheus

# 應該顯示：
# prometheus-client    0.19.0
```

---

## 錯誤 2: NameError: name 'Entity' is not defined

### 錯誤訊息
```
File "scripts\process_pdf_to_graph.py", line 175, in process_pdf_to_graph
    main_doc_entity = Entity(
                      ^^^^^^
NameError: name 'Entity' is not defined
```

### 根本原因
- 在 `process_pdf_to_graph.py` 中使用了 `Entity` 類別
- 但沒有從 `app.core.graph_store` 導入 `Entity`

### 解決方案
**檔案**: `scripts/process_pdf_to_graph.py`

**修改前**:
```python
from app.core.graph_store import SQLiteGraphStore
```

**修改後**:
```python
from app.core.graph_store import SQLiteGraphStore, Entity
```

### 驗證
```powershell
# 測試導入
python -c "from app.core.graph_store import Entity; print('OK')"
```

---

## 預防措施

### 1. 確保虛擬環境一致性
- 所有依賴都應該安裝在虛擬環境中
- 使用 `requirements.txt` 統一管理依賴

### 2. 檢查導入
- 使用 IDE 的導入檢查功能
- 執行 `python -m py_compile` 檢查語法錯誤

### 3. 測試腳本
- 在執行前先測試導入
- 使用 `python -c "import module"` 驗證

---

## 相關檔案

- `requirements.txt` - 依賴清單
- `scripts/process_pdf_to_graph.py` - PDF 處理腳本（已修復）
- `app/utils/metrics.py` - Prometheus 指標（需要依賴）


