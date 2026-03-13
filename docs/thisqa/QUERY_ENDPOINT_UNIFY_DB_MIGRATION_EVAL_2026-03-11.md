## `/api/v1/query` 與 `graph_qa.db` 合併評估（2026-03-11）

**更新時間：2026-03-11**  
**作者：AI Assistant**  
**摘要：** 評估是否將 `/api/v1/qa/search` 的關鍵字搜尋行為與資料，全面整合到單一查詢端點 `/api/v1/query` 與單一圖資料庫 `graph.db`。結論：**本階段僅做「API 行為統一」規劃，不合併 DB，保留 `graph_qa.db`，將 DB 合併視為下一階段風險較高的重構。**

---

### 1. 現況整理

- **`graph.db`**
  - 用途：主線 GraphRAG（`/api/v1/query` + `GraphOrchestrator` + `VectorService`）。
  - 來源：`scripts/process_thisqa_to_graph.py` 等，從 Thisqa 操作手冊與 IC 欄位/錯誤建圖。
  - 行為：向量檢索 + 圖增強 + LLM。

- **`graph_qa.db`**
  - 用途：結構化 QA 查詢（`/api/v1/qa/search`, `/api/v1/qa/documents`, `/api/v1/qa/by-document`）。
  - 來源：`import_thisqa_markdown_batch.py`、`import_ic_error_spec_to_qa_graph.py`、`parse_qa_markdown_to_graph.py` 等。
  - 行為：多欄位、多關鍵字 AND 匹配，直接回傳 QA 列表（可依 QUERY_TYPE=rag 再組 context + LLM）。

兩顆 DB 使用相同的 `entities` / `relations` schema，但在物理上完全分離，腳本與 API 也各自綁定固定路徑（`graph.db` vs `graph_qa.db`）。

---

### 2. 需求與方向

1. **介面整合（API 行為）**
   - 用單一入口 `/api/v1/query`，搭配 `QUERY_TYPE` 控制行為：
     - `QUERY_TYPE=sql`：執行「純關鍵字 QA 搜尋」，等價於目前 `/api/v1/qa/search` 的 SQL 邏輯。
     - `QUERY_TYPE=rag`：維持現有 GraphRAG + LLM 流程。
   - 最終目標是讓呼叫端只需要理解 `/api/v1/query` + `QUERY_TYPE`，不再需要額外理解 `/api/v1/qa/search` 的存在與定位。

2. **儲存整合（DB 合併）**
   - 理想終態：用 **一顆 `graph.db`** 存所有圖（主 RAG 圖 + QA 圖），靠 `properties.subgraph` 或命名規則區分不同子圖。
   - 目前評估：這是一個**高風險、影響面廣**的重構，暫不在本階段執行。

---

### 3. DB 合併的風險評估（為何暫緩）

**優點（若成功合併）：**

- **部署與維運簡化**：
  - 只需要管理一顆 DB：備份、遷移、reset pipeline 都更單純。
  - QA 查詢與 GraphRAG 查詢可以在同一顆圖上 cross-usage（例如 RAG 直接引用 QA 實體當作 context）。

- **邏輯一致性**：
  - 之後任何與圖有關的新功能（例如 IC 子圖、QA 子圖）都在同一張圖上演進。

**風險與成本：**

- **腳本與 API 變更範圍大**：
  - 目前所有 QA 相關腳本與 API 都直接寫死 `./data/graph_qa.db`：
    - `reset_graph_qa_db.py`, `import_thisqa_markdown_batch.py`, `import_ic_error_spec_to_qa_graph.py`,
      `parse_qa_markdown_to_graph.py`, `query_qa_graph.py`, `app/api/v1/endpoints/qa.py` 等。
  - 合併後路徑都要改成 `graph.db`，同時要避免誤刪/誤動主 RAG 圖資料。

- **邏輯隔離轉為「僅邏輯」**：
  - 現在 QA 圖與主圖是物理隔離（兩顆檔案），reset QA 不會動到主圖。
  - 合併後，需要靠：
    - `properties.subgraph = "qa" | "main" | "ic_error"` 或
    - 嚴格的 doc_id/type 命名規則  
    來區分子圖，所有查詢與 reset 腳本都必須帶上正確的子圖條件，否則有資料污染風險。

- **查詢效能與複雜度**：
  - QA 的簡單 AND 關鍵字搜尋若沒有明確限制子圖，可能掃到整顆圖，效能與結果都不可預期。

- **回滾難度**：
  - 一旦把 graph_qa 的資料 merge 進 graph.db 並改動腳本/端點，要回滾到「兩顆 DB」架構將變得困難。

