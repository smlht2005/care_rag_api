一、整條請求在後端怎麼走
POST /api/v1/query 收到 body：query + top_k。
Orchestrator 會呼叫 VectorService.search(query, top_k) 做檢索。
檢索結果當成 RAG 的 sources，再交給 LLM 依「使用者問題 + 這些來源」產生 answer。
所以：只要檢索先給錯文件／錯實體，後面 LLM 就很容易跟著跑偏（尤其來源很短、只有一個標題時）。

二、VectorService.search 的優先順序（重點）
邏輯大意是：

IC 卡特殊規則（錯誤碼／欄位碼）— 你的問題與 IC 無關，會跳過。
_search_from_qa_embeddings
把整句 query 做 embedding，到 QAEmbeddingIndex（qa_vectors.db）做相似度搜尋。
只有 分數 ≥ QA_MIN_SCORE（設定在 config） 的命中才會留下。
你的問題是 WHO + 長照政策，圖裡多半是 衛生所 HIS／批價／掛號 這類 QA，語意上通常對不齊 → 常見情況是：沒有任何一筆超過門檻 → 回傳空列表。
若 embedding 路徑 沒有可用結果（或發生例外被 catch），就進下一步。
_search_from_graph：用關鍵字去圖資料庫的 entities 做 LIKE，把找到的實體當成來源。
再不行才 stub（與你這次案例無關，因為你已經看到 source: graph）。
你回應裡 metadata.source 是 "graph"，代表這次 最後是走第 4 步 graph 關鍵字，不是 qa_embedding。

三、Graph 關鍵字是怎麼從句子「切」出來的？
_search_from_graph 用這個正則：

[\u4e00-\u9fff\w]+
一段連續的中文（中間沒空格）通常會變成 一個大 token。
英文則多半依空白拆成多個 token。
以類似你截圖的句子為例（結構上）：

會得到類似：World、Health、Organization、在長期照護方面有什麼政策（一整段中文一個 token，視標點略有差異）。
然後程式只取 前 5 個 token 去搜，每個 token 都會呼叫一次 search_entities(kw)。

四、為什麼「Organization」會釀成大災難？
search_entities（SQLite 版）條件是：

name LIKE '%關鍵字%' 或
type LIKE '%關鍵字%'
建圖時（例如 EntityExtractor / LLM 標註），很多實體會被標成圖譜裡的固定類型名，例如：

Person、Organization、Document、Concept、Policy…
因此當關鍵字是英文 Organization 時：

type LIKE '%Organization%' 會命中 所有 type 欄位字串裡含有 Organization 的列。
對多數資料來說，就是 所有被標成「Organization」這種類型的節點，數量可能很多。
這和使用者心里想的 「World Health Organization（機構）」 完全不是同一回事：
程式只是在比對 資料庫欄位字串，沒有做「專有名詞 / 機構名」的語意理解。

五、為什麼會變成「批價管理系統」這一筆？
在實際的 graph.db 裡可以觀察到：

存在 名稱就是「批價管理系統」（或與選單／章節標題相關）的實體。
其中有些列的 type 恰好是 Organization（LLM 把「系統／單位／模組」類名稱標成 Organization 很常見）。
所以當搜尋 Organization 時：

這一筆會和 其他所有 type=Organization 的節點一起 滿足 LIKE。
SQL 是 SELECT ... LIMIT ?，沒有 ORDER BY。
在 SQLite 裡，這種查詢的回傳順序不保證與「和問題最相關」有關，比較像「哪幾列先被掃到」。
因此 出現「批價管理系統」當其中一筆命中 是合理現象，不是「圖裡剛好有一條 WHO 長照連到批價」。
六、score: 0.85 為什麼不能當「信心度」？
在 _search_from_graph 裡，每個命中都寫死：

"score": 0.85
這不是向量相似度、也不是 rerank 分數，只是「讓 RAG 結構裡有個數字」的常數。
所以在 Postman 看到 0.85 會以為「很準」，其實 與問題是否相關無關。

七、LLM 為什麼最後答案也變成短短一句？
檢索若只給 很短的 content（例如實體名稱「批價管理系統」加上少量屬性），且與 WHO 長照無關：

模型有時會 過度依賴唯一來源，輸出接近來源標題的短句；
或在指令設計下 無法憑空講 WHO 政策（知識庫裡根本沒有），卻仍被要求回答，就會出現 怪異的濃縮句。
所以：根因在檢索（graph 假命中 + 固定分數）；LLM 是放大／呈現了這個錯誤上下文。

八、和「QA 向量」路徑的關係（對照用）
若 _search_from_qa_embeddings 有命中且過門檻，metadata 通常會帶 source: qa_embedding，且 score 會是浮點相似度（不是寫死 0.85）。
你這次是 graph + 0.85，兩件事一起佐證：embedding 沒留下合格命中，落到 graph 關鍵字。

九、一句話總結（較完整版）
「World Health Organization」被拆成獨立英文 token，其中的 Organization 透過 type LIKE '%Organization%' 與圖譜裡大量 type=Organization 的節點發生假命中；在無 ORDER BY 的 LIMIT 下可能先撈到「批價管理系統」這類節點；再套上寫死的 0.85 分，看起來像高信心檢索，最後 LLM 依錯誤來源產生不合理答案。

若你接下來要改行為（例如：關鍵字不搜 type、過濾 schema 類名、無命中時回「未涵蓋」等），屬於業務邏輯變更，依你的規則需要你明確指定方案後再動程式。

---

## 十、解法（已實作，2026-03-20）

對應 **T1 預授權**（`.cursor/rules/care-rag-change-governance.mdc`）之檢索假陽性／誤導分數，已落地如下：

### 1. Graph 關鍵字 fallback 僅比對 **實體名稱 `name`**

- `GraphStore.search_entities(..., include_type_match=False)`：`WHERE name LIKE` only（SQLite / `MemoryGraphStore` 皆實作）。
- `VectorService._search_from_graph` 改呼叫 **`include_type_match=False`**，不再因英文 token `Organization` 命中 `type = Organization` 而撈到「批價管理系統」等無關節點。
- **預設** `include_type_match=True`：`Orchestrator` 等既有呼叫維持 **name OR type** 行為不變。

### 2. 分數與 metadata（避免誤解為語意信心度）

- graph keyword 來源之 `score` 由 **0.85 改為 0.35**（仍僅供排序，非 embedding 相似度）。
- `metadata` 增加 **`score_source: "graph_keyword"`**，與 `qa_embedding` 之真實相似度區分。

### 3. 預期 API 行為（WHO／長照類、知識庫未涵蓋）

- 若 QA embedding 無合格命中，且 **name** 關鍵字亦無合理命中 → `sources` 為空 → 編排器回 **`未找到`**（見 `NO_MATCH_MESSAGE`），**不再**用錯誤 graph 節點硬答。

### 4. 相關程式位置

- `app/core/graph_store.py`：`search_entities` 簽章與 SQLite / Memory 實作。
- `app/services/vector_service.py`：`_search_from_graph`。

### 5. 驗證建議

- Postman：`POST /api/v1/query`，body 與當初問題類似（WHO + 長照），預期 **answer 為「未找到」** 或無不當之 HIS 標題，且不應再出現 **僅因 `Organization` 而來的 graph 假命中**（`metadata.score_source` 若為 graph 路徑應為 `graph_keyword`）。

### 6. 本機開發怎麼測（dev）

**A. 單元測試（不依賴真實 LLM／graph.db）**

在專案根目錄 `care_rag_api`（與 `app/` 同層）執行：

```bash
python -m pytest tests/test_core/test_graph_store_search_entities.py -v
```

預期：**3 passed**（驗證 `include_type_match=False` 不會因 `type=Organization` 命中）。

**A2. 輕量整合腳本（MemoryGraphStore + `_search_from_graph`）**

```bash
python scripts/verify_missfind_graph_fallback.py
```

預期終端輸出 **`graph keyword hits: 0`** 與 **`OK: zero hits`**（結束碼 0）。

**B. 啟動 API**

- Windows：於 `care_rag_api` 下執行 `scripts\run_api.bat`（預設 **http://0.0.0.0:8000**）。
- 或手動（同樣需在 `care_rag_api` 根目錄，讓 `import app` 正確）：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**C. 手動打 `/api/v1/query`**

- **Postman**：`POST {{base_url}}/api/v1/query`，`Content-Type: application/json`，body 範例：

```json
{
  "query": "World Health Organization 在長期照護方面有什麼政策？",
  "top_k": 5
}
```

- **PowerShell**（`baseUrl` 改成你的位址）：

```powershell
$body = @{ query = "World Health Organization 在長期照護方面有什麼政策？"; top_k = 5 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/query" -Method Post -Body $body -ContentType "application/json; charset=utf-8"
```

**預期（修復後）**

- `answer` 常為 **`未找到`**（知識庫無對應內容時）；**不應**再出現僅因 `Organization` 而回的 **「批價管理系統」**。
- 若仍有 graph 來源，檢查 `sources[].metadata.score_source`：**`graph_keyword`** 且 `score` 約 **0.35**（非舊版 0.85 假高信心）。

**D. 對照：應仍能命中的 HIS／中文關鍵字**

改用知識庫內有的詞（例如含 **「批價」**、具體操作句），應仍可能透過 **name** 子字串或 **qa_embedding** 命中；可用來確認沒有「全面搜不到」。

**E. 日誌（可選）**

啟動後看主控台：`Vector search (qa_embedding + ic_special_qa)` vs `Vector search (graph): N results`；WHO 類問題在修復後常見 **graph 為 0 筆** 再交編排器回「未找到」。

