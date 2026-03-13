---
name: Thisqa_QA_GraphRAG_Vectorization
overview: 在現有 graph.db 的基礎上，把 Thisqa 的 QA block 轉成圖實體並建立向量索引，讓 /api/v1/query 能以語意方式召回正確 QA，同時保留 GraphRAG 結構優勢。
---

# Thisqa QA GraphRAG + 向量化 設計與實作計畫

## 目標

- **短期**：讓 `POST /api/v1/query` 對 Thisqa 類問題（例如「批價作業如何搜尋病患資料？」）能正確召回對應 QA 內容並產生回答，而不是一律「未找到」。
- **中期**：把每個 QA block 變成 `Entity(type="QA")`，並為這些 QA 實體建立向量索引，實現「Graph + Vector 雙索引」的 GraphRAG。

---

## 現況簡述

- `data/Thisqa/*.md` 已包含結構良好的 QA block：`## Q: ...` / `**Answer**: ...` 等。
- `scripts/process_thisqa_to_graph.py`：
  - 讀取 Thisqa 檔案 → 依 QA / 段落切塊 → `GraphBuilder.build_graph_from_text` → 寫入 `graph.db`。
  - 目前只建立 `Document` 實體與一般抽出實體，**沒有專門的 QA Entity**。
- `graph.db` 結構由 `app/core/graph_store.py` 管理，`Entity` / `Relation` 已穩定運作。
- `POST /api/v1/query`：
  - 由 `app/api/v1/endpoints/query.py` → `GraphOrchestrator` (`app/core/orchestrator.py`) → `RAGService` (`app/services/rag_service.py`)。
  - 目前檢索來源：`VectorService.search` + `GraphStore._enhance_with_graph`，**VectorService 只針對 Entity 做 keyword 檢索，沒有真正的 QA 向量索引**。

---

## 設計方案概覽

### 1. QA Entity schema 設計

- 在 `graph_store.Entity` 上新增一種邏輯類型 `type="QA"`，其 `properties` 約定結構：
  - `question`: 原始問題文字（`## Q: ...` 的內容）。
  - `answer`: 對應 Answer 段落全文（含重點與步驟）。
  - `keywords`: 從 Thisqa block 解析的關鍵字列表。
  - `document_id`: 所屬手冊檔的 Document 實體 ID（例如 `doc_thisqa_billing`）。
  - 其他可選欄位：`section`, `order_index`, `source_file`, `qa_id` 等。

### 2. 向量索引設計（QA Vector Store）

- 新增一個「QA 向量索引」層，與 `graph.db` 並存：
  - 每個 QA Entity 對應一筆向量紀錄：
    - `id` / `entity_id`: 對應 graph 的 `Entity.id`。
    - `text`: 用於 embedding 的文字（例如 `question + "\n" + answer + "\n" + ','.join(keywords)`）。
    - `embedding`: 由現有 LLM provider 支援的 embedding 模型產生（若 Gemini 有 embedding API，可優先使用，否則可暫時用本地簡單模型或留 stub）。
    - `metadata`: `{ "type": "QA", "document_id": ..., "source_file": ... }`。
- 實作方式：
  - **簡化版**：用 sqlite 或檔案（JSONL / Parquet）+ in-memory index + cosine similarity；
  - 介面由 `VectorService` 封裝，維持目前 `search(query, top_k)` 簽章不變。

### 3. 建圖流程調整：從 Thisqa 產生 QA Entity + 向量

- 修改 `scripts/process_thisqa_to_graph.py`：
  1. 在切 QA block 時，同時取得：`question_text`, `answer_text`, `keywords`, 所屬 `document_id`。
  2. 對每個 QA block：
    - 建立 `Entity(type="QA", name=question_text 或精簡版, properties={...})`，寫入 `graph_store.add_entity`。
    - 呼叫 `VectorService.add_documents([{"id": qa_entity.id, "content": question+answer+keywords, "metadata": {...}}])`，更新 QA 向量索引。
  3. 保持現有 `Document` 實體與一般實體抽取邏輯不變（不破壞現有 graph）。

### 4. VectorService 擴充：支援 QA 向量檢索

- 在 `app/services/vector_service.py` 中：
  - 現有的 `VectorService.search` 已改為可從 graph 檢索實體；再擴充為：
    - **模式 A：QA 向量檢索**（預設用於 `/api/v1/query`）：
      - 將 query embed → 在 QA 向量索引中搜尋 → 拿到一組 `entity_id` + score。
      - 回到 `graph_store.get_entity(entity_id)` 取得 QA Entity → 組成 RAG `sources`（`content = answer 或 question+answer`）。
    - **模式 B：Graph Entity keyword 檢索**（保留目前 graph-only 檢索行為，必要時作 fallback）。
  - 透過 metadata 或簡單旗標（例如只在 QA 向量索引中搜尋 `type="QA"`）來控制檢索範圍。

### 5. GraphOrchestrator / RAGService 與 QA 向量的整合

- `GraphOrchestrator.query`：
  - 目前流程：`RAGService.query` → `graph_enhancement` → sources 合併。
  - 新增行為（維持介面不變）：
    - `RAGService.query` 的內部改為優先使用 QA 向量索引（透過 `VectorService.search`），取得 QA 型 sources；
    - Graph 增強階段可選擇：
      - 針對 QA 所屬的 Document / Concept 再拉 neighbors 進來，增加 context；
      - 或對 QA Entity 做 graph walk（例如：同一 Document 其他相近 QA）。
- `RAGService` 仍維持「**只依來源回答 / 無來源則未找到**」的策略，只是現在能更容易召回與 query 語意接近的 QA。

### 6. 設定與測試

- 設定：
  - `.env` / `Settings` 中新增向量索引相關設定：
    - `QA_VECTOR_DB_PATH` 或簡易 persistent 路徑。
    - 需要時的 embedding 模型名稱。
- 測試：
  1. 重新跑 `process_thisqa_to_graph.py --reset`，確保 QA Entity + 向量索引都建好。
  2. 使用 `check_db.py` 和新增的 QA 向量檢查腳本（如 `verify_thisqa_qa_vector.py`）確認：
    - QA Entity 數量與預期相符；
    - 向量索引能對 `"批價作業如何搜尋病患資料？"` 召回正確 QA Entity。
  3. 重跑 `scripts/test_graph_llm_qa.py`，觀察：
    - `VectorService` 日誌從 `(graph)` / `(stub)` 變成 QA 向量檢索；
    - `sources` 不再為空；
    - `answer` 能合理引用 Thisqa QA 的 Answer 內容；
    - 無來源時仍只回「未找到」。

---

## 後續可選擴充

- 給 QA Entity 加上更多圖關係（例如 ErrorCode、WorkFlowStep），讓 GraphRAG 能針對某個 QA 問「相關操作 / 相關錯誤」。
- 在 QA 向量索引中同時儲存簡短摘要（summary），讓 LLM prompt 更精簡。
- 視需求把同一 QA 的多語系版本（若未來有）也掛在同一 QA Entity 下，以 `language` 屬性區分。

