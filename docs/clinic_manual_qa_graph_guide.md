# 衛生所操作手冊問答知識圖譜建立指南

**更新時間**：2025-12-29 15:05  
**目的**：從衛生所操作手冊 PDF 建立專門的問答知識圖譜

## 概述

本指南說明如何使用腳本解析衛生所操作手冊 PDF 文件，並建立專門的問答知識圖譜資料庫 `graph_qa.db`。

## 文件結構

```
care_rag_api/
├── data/
│   ├── example/
│   │   └── clinic his/
│   │       ├── 衛生所版簡易操作手冊-批價.pdf
│   │       ├── 衛生所版簡易操作手冊-病歷、掛號.pdf
│   │       └── 衛生所版簡易操作手冊-醫令.pdf
│   └── graph_qa.db          # 問答知識圖譜資料庫
├── scripts/
│   ├── parse_clinic_manual_pdfs_to_qa_graph.py  # PDF 解析腳本
│   ├── query_qa_graph.py                        # 圖譜查詢腳本
│   └── process_clinic_manuals.bat              # Windows 批次檔
└── docs/
    └── clinic_manual_qa_graph_guide.md          # 本指南
```

## 快速開始

### 方法一：使用批次檔（Windows）

```bash
# 在專案根目錄執行
scripts\process_clinic_manuals.bat
```

### 方法二：使用 Python 腳本

```bash
# 處理目錄中的所有 PDF
python scripts/parse_clinic_manual_pdfs_to_qa_graph.py --pdf-dir "data/example/clinic his"

# 處理單個 PDF
python scripts/parse_clinic_manual_pdfs_to_qa_graph.py --pdf-file "data/example/clinic his/衛生所版簡易操作手冊-批價.pdf"

# 指定自訂資料庫路徑
python scripts/parse_clinic_manual_pdfs_to_qa_graph.py --pdf-dir "data/example/clinic his" --db-path "./data/custom_qa.db"
```

## 功能說明

### 1. PDF 解析腳本 (`parse_clinic_manual_pdfs_to_qa_graph.py`)

#### 主要功能

1. **PDF 文字提取**
   - 支援 `pdfplumber`（推薦，更好的中文支援）
   - 降級使用 `PyPDF2`
   - 保留頁碼資訊

2. **問答對提取**
   - 模式1: `Q: ... A: ...` 格式
   - 模式2: `問題：... 答案：...` 格式
   - 模式3: 標題作為問題，後續段落作為答案

3. **知識點提取**
   - 章節標題提取
   - 關鍵操作術語提取
   - LLM 輔助實體提取

4. **圖結構建立**
   - 文件實體（Document）
   - 問答實體（QA）
   - 知識點實體（KnowledgePoint）
   - 實體關係（CONTAINS_QA, CONTAINS_KNOWLEDGE, CONTAINS_ENTITY）

#### 命令列參數

```bash
--pdf-dir PATH         # PDF 文件目錄（預設: data/example/clinic his）
--pdf-file PATH        # 單個 PDF 文件路徑
--db-path PATH         # 圖資料庫路徑（預設: ./data/graph_qa.db）
```

### 2. 圖譜查詢腳本 (`query_qa_graph.py`)

#### 主要功能

1. **統計資訊查詢**
   - 文件數量
   - 問答對數量
   - 知識點數量
   - 實體和關係統計

2. **問答對搜尋**
   - 關鍵詞搜尋
   - 問題和答案內容匹配

#### 使用範例

```bash
# 查看統計資訊
python scripts/query_qa_graph.py

# 搜尋問答對
python scripts/query_qa_graph.py --search "批價"
python scripts/query_qa_graph.py --search "掛號" --limit 5
```

## 資料庫結構

### 實體類型

1. **Document** - 文件實體
   - `id`: 文件 ID
   - `name`: 文件名稱
   - `properties`:
     - `source`: PDF 文件路徑
     - `type`: "clinic_manual"
     - `total_pages`: 總頁數
     - `total_length`: 總字元數
     - `qa_pairs_count`: 問答對數量
     - `knowledge_points_count`: 知識點數量

2. **QA** - 問答對實體
   - `id`: 問答 ID
   - `name`: 問題摘要
   - `properties`:
     - `question`: 問題內容
     - `answer`: 答案內容
     - `source`: 提取來源（qa_pattern1, qa_pattern2, title_pattern）
     - `qa_index`: 問答對索引

3. **KnowledgePoint** - 知識點實體
   - `id`: 知識點 ID
   - `name`: 知識點主題
   - `properties`:
     - `topic`: 主題
     - `content`: 內容
     - `keywords`: 關鍵詞列表
     - `type`: 類型（section, keywords, general）

### 關係類型

1. **CONTAINS_QA** - 文件包含問答對
   - `source_id`: 文件 ID
   - `target_id`: 問答 ID
   - `properties`: `qa_index`

2. **CONTAINS_KNOWLEDGE** - 文件包含知識點
   - `source_id`: 文件 ID
   - `target_id`: 知識點 ID
   - `properties`: `kp_index`

3. **CONTAINS_ENTITY** - 文件包含實體
   - `source_id`: 文件 ID
   - `target_id`: 實體 ID

## 處理流程

```
1. PDF 文件
   ↓
2. 文字提取（pdfplumber/PyPDF2）
   ↓
3. 問答對提取（正則表達式模式匹配）
   ↓
4. 知識點提取（章節標題、關鍵詞）
   ↓
5. LLM 實體提取（可選）
   ↓
6. 建立圖結構
   ├── Document 實體
   ├── QA 實體
   ├── KnowledgePoint 實體
   └── 關係（CONTAINS_QA, CONTAINS_KNOWLEDGE, CONTAINS_ENTITY）
   ↓
7. 儲存到 graph_qa.db
```

## 注意事項

1. **PDF 處理庫**
   - 推薦安裝 `pdfplumber`（更好的中文支援）
   - 備選 `PyPDF2`

2. **LLM 服務**
   - 需要配置 LLM API key（Gemini 或 OpenAI）
   - 如果 LLM 服務不可用，仍可進行基本的問答對和知識點提取

3. **資料庫路徑**
   - 預設路徑：`./data/graph_qa.db`
   - 與主圖資料庫 `graph.db` 分離

4. **處理時間**
   - 取決於 PDF 大小和 LLM 處理時間
   - 大型 PDF 可能需要較長時間

## 故障排除

### 問題：PDF 文字提取失敗

**解決方案**：
- 確認已安裝 `pdfplumber` 或 `PyPDF2`
- 檢查 PDF 文件是否損壞
- 嘗試使用不同的 PDF 處理庫

### 問題：問答對提取數量為 0

**解決方案**：
- 檢查 PDF 內容格式
- 調整正則表達式模式
- 手動檢查 PDF 文字內容

### 問題：LLM 實體提取失敗

**解決方案**：
- 檢查 LLM API key 配置
- 確認網路連線
- LLM 失敗不影響基本問答對提取

## 後續擴展

1. **問答對品質提升**
   - 使用 LLM 進行問答對驗證和優化
   - 自動生成問題（如果 PDF 中沒有明確的問答格式）

2. **知識圖譜增強**
   - 建立問答對之間的關係
   - 建立知識點之間的層級關係
   - 建立跨文件的知識關聯

3. **查詢功能增強**
   - 語義搜尋（使用向量相似度）
   - 問答對推薦
   - 知識點導航

4. **API 整合**
   - 提供 RESTful API 查詢問答圖譜
   - 整合到現有的 Care RAG API

## 相關文件

- `scripts/process_pdf_to_graph.py` - 通用 PDF 處理腳本
- `scripts/init_graph_db.py` - 圖資料庫初始化腳本
- `docs/pdf_processing_guide.md` - PDF 處理指南

