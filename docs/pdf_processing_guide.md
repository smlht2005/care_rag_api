# PDF 文件處理和圖構建指南

## 概述

`scripts/process_pdf_to_graph.py` 腳本可以從 PDF 文件提取文字內容，自動構建 GraphRAG 圖結構，並新增到向量資料庫。

## 功能

1. **PDF 文字提取**：使用 pdfplumber（優先）或 PyPDF2 提取文字
2. **實體提取**：使用 LLM 從文字中提取實體（Person, Organization, Location, Concept, Document, Policy）
3. **關係提取**：提取實體間的關係
4. **圖構建**：自動構建圖結構並儲存到 SQLite
5. **向量儲存**：新增到向量資料庫

## 使用方式

### 基本用法

```powershell
# 使用預設 PDF 文件（data/example/1051219長期照護2.0核定本.pdf）
python scripts\process_pdf_to_graph.py

# 指定 PDF 文件路徑
python scripts\process_pdf_to_graph.py "data/example/your_file.pdf"

# 指定文件 ID
python scripts\process_pdf_to_graph.py --doc-id "long_term_care_2.0"

# 指定分塊大小（預設 2000 字元）
python scripts\process_pdf_to_graph.py --chunk-size 3000
```

### 使用批次檔（Windows）

```cmd
scripts\process_pdf.bat
```

## 處理流程

```
PDF 文件
  ↓
[步驟 1] 提取 PDF 文字內容
  ↓
[步驟 2] 初始化服務（GraphStore, EntityExtractor, GraphBuilder）
  ↓
[步驟 3] 生成文件 ID
  ↓
[步驟 4] 處理文件內容
  ├─→ 如果文字過長：分塊處理
  │   ├─→ 每個區塊提取實體和關係
  │   └─→ 建立主文件實體
  └─→ 如果文字適中：單一區塊處理
  ↓
[步驟 5] 新增到向量資料庫
  ↓
完成
```

## 輸出結果

腳本會顯示：
- PDF 總頁數
- 提取的文字長度
- 處理的區塊數（如果分塊）
- 提取的實體數
- 提取的關係數
- 文件 ID

## 檢查結果

處理完成後，可以使用以下命令檢查圖結構：

```powershell
# 檢查資料庫狀態
python scripts\check_db.py

# 查詢特定實體
python -c "import asyncio; from app.core.graph_store import SQLiteGraphStore; from app.config import settings; async def check(): store = SQLiteGraphStore(settings.GRAPH_DB_PATH); await store.initialize(); entities = await store.get_entities_by_type('Document'); print('Documents:', [e.name for e in entities]); await store.close(); asyncio.run(check())"
```

## 注意事項

1. **PDF 處理庫**：
   - 優先使用 `pdfplumber`（更好的中文支援）
   - 降級使用 `PyPDF2`
   - 如果都沒有安裝，會提示安裝

2. **文字長度**：
   - 如果文字超過 `chunk_size`，會自動分塊處理
   - 每個區塊獨立提取實體和關係
   - 建議 `chunk_size` 設定為 2000-3000 字元

3. **LLM 使用**：
   - 實體和關係提取需要呼叫 LLM API
   - 大量文字可能需要較長時間
   - 建議先測試小文件

4. **資料庫**：
   - 確保已執行 `python scripts\init_graph_db.py` 初始化資料庫
   - 圖結構儲存在 `./data/graph.db`

## 範例

### 處理長期照護 PDF

```powershell
# 處理預設的長期照護 PDF
python scripts\process_pdf_to_graph.py

# 輸出範例：
# ============================================================
# PDF 文件處理和圖構建
# ============================================================
# 
# [步驟 1/5] 提取 PDF 文字內容...
# 文件路徑: C:\...\1051219長期照護2.0核定本.pdf
# PDF 總頁數: 191
#   已處理 10 頁...
#   已處理 20 頁...
#   ...
# ✅ 文字提取完成，總長度: 125000 字元
# 
# [步驟 2/5] 初始化服務...
# ✅ 服務初始化完成
# 
# [步驟 3/5] 文件 ID: doc_1051219長期照護2.0核定本_a1b2c3d4
# 
# [步驟 4/5] 處理文件內容...
# 文字過長 (125000 字元)，進行分塊處理...
# 分為 63 個區塊
# 
# 處理區塊 1/63...
#   ✅ 區塊 1 完成: 15 實體, 8 關係
# ...
```

## 故障排除

### 問題：PDF 文字提取失敗

**解決方案**：
1. 確認 PDF 文件路徑正確
2. 確認已安裝 PDF 處理庫：`pip install pdfplumber PyPDF2`
3. 檢查 PDF 是否為掃描檔（需要 OCR）

### 問題：實體提取失敗

**解決方案**：
1. 檢查 LLM 服務是否正常
2. 檢查網路連線
3. 嘗試減少 `chunk_size`

### 問題：資料庫錯誤

**解決方案**：
1. 確認資料庫已初始化：`python scripts\init_graph_db.py`
2. 檢查資料庫檔案權限
3. 確認 `data` 目錄存在

## 相關檔案

- `scripts/process_pdf_to_graph.py` - PDF 處理腳本
- `scripts/init_graph_db.py` - 資料庫初始化腳本
- `scripts/check_db.py` - 資料庫檢查腳本
- `app/core/graph_store.py` - 圖儲存系統
- `app/core/entity_extractor.py` - 實體提取器
- `app/services/graph_builder.py` - 圖構建服務


