# 一般問答

## Q: 什麼是 GraphRAG？

**A:** GraphRAG（Graph-based Retrieval-Augmented Generation）是一種結合圖結構和 RAG 的技術：

### 核心概念

1. **圖結構儲存**
   - 將文件內容轉換為圖結構（實體和關係）
   - 使用圖資料庫儲存

2. **圖查詢增強**
   - 向量檢索 + 圖查詢
   - 利用實體間的關係增強檢索結果

3. **LLM 生成**
   - 使用增強後的上下文生成回答
   - 包含向量結果和圖結構資訊

---

## Q: 專案架構是什麼？

**A:** 專案採用分層架構：

```
API 層 (FastAPI)
  ↓
核心層 (GraphOrchestrator, GraphStore)
  ↓
服務層 (RAGService, LLMService, VectorService)
  ↓
儲存層 (SQLite, Vector DB, Redis)
```

### 主要組件

1. **GraphStore**: 圖結構儲存（SQLite + Memory）
2. **EntityExtractor**: 實體和關係提取
3. **GraphBuilder**: 從文件構建圖結構
4. **GraphOrchestrator**: 統籌查詢流程
5. **RAGService**: RAG 查詢服務

---

## Q: 如何開始使用？

**A:** 步驟：

### 1. 初始化資料庫

```powershell
python scripts\init_graph_db.py
```

### 2. 處理 PDF 文件

```powershell
python scripts\process_pdf_to_graph.py
```

### 3. 啟動 API 服務

```powershell
uvicorn app.main:app --reload --port 8080
```

### 4. 測試查詢

```powershell
curl -X POST "http://localhost:8080/api/v1/query" `
  -H "Content-Type: application/json" `
  -d '{"query": "測試問題", "top_k": 3}'
```

---

## Q: 如何檢查系統狀態？

**A:** 使用診斷工具：

### 1. 檢查虛擬環境

```powershell
python scripts\check_venv.py
```

### 2. 檢查資料庫

```powershell
python scripts\check_db.py
```

### 3. 快速檢查依賴

```powershell
python scripts\quick_check.py
```

---

## Q: 常見問題和解決方案

### 問題 1: 模組找不到

**解決方案**：
```powershell
python -m pip install -r requirements.txt
```

### 問題 2: 虛擬環境問題

**解決方案**：
- 確認虛擬環境已啟用（終端顯示 `(Langchain312)`）
- 使用 `python -m pip` 而不是 `pip`

### 問題 3: JSON 解析錯誤

**解決方案**：
- 這是預期的（LLM 服務是 Stub）
- 已改進錯誤處理，不會影響功能

---

## Q: 如何貢獻或報告問題？

**A:** 

1. **檢查現有文檔**
   - `docs/` 目錄包含各種指南
   - `docs/qa/` 目錄包含問答

2. **查看錯誤修復記錄**
   - `docs/error_fixes.md`
   - `docs/troubleshooting.md`

3. **檢查開發記錄**
   - `dev_readme.md` 包含開發歷史

---

## 相關文檔

- `docs/graphrag_implementation_plan.md` - 完整實作計劃
- `docs/pdf_processing_guide.md` - PDF 處理指南
- `docs/venv_setup_guide.md` - 虛擬環境設置指南
- `README.md` - 專案概述


