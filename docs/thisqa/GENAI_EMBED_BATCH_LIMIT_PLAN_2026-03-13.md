# 修復 Google GenAI embedding 單批超過 100 筆導致 400 錯誤

更新時間：2026-03-13
作者：AI Assistant
修改摘要：計畫存檔於 docs/thisqa，供實作與查閱。

---

## 根因說明

錯誤訊息：

```text
BatchEmbedContentsRequest.requests: at most 100 requests can be in one batch
```

- **觸發檔案**：`IC卡資料上傳錯誤對照.txt` — IC 欄位 89 + IC 錯誤碼 240 = **329** 個 QA 區塊，一次全部傳給 `embed()`。
- **呼叫點**：`scripts/process_thisqa_to_graph.py` 第 561–565 行：`embeddings = await embedding_service.embed(qa_texts)`，未對 `qa_texts` 做分批。
- **實際送 API 處**：`app/services/embedding_service.py` 第 116–120 行：`GoogleGenAIEmbeddingService.embed()` 將整份 `texts` 一次傳給 `embed_content(..., contents=batch)`，未遵守「單批最多 100 筆」的限制。

因此根因是：**在 embedding 服務層單次呼叫送了超過 100 筆，違反 Gemini 的 batch 上限**。

---

## 建議修復方式（單一改動點）

在 **embedding 服務** 內做分批，讓所有呼叫端都自動符合 API 限制。

### 修改檔案：app/services/embedding_service.py

- **位置**：`GoogleGenAIEmbeddingService.embed(self, texts: List[str])`（約 110–131 行）。
- **100 的來源與設定位置**：
  - **100 是 Google GenAI API 的硬性上限**（錯誤訊息：`at most 100 requests can be in one batch`），不是專案自訂的預設值；實作時單批不可超過 100。
  - **建議**：在 `embedding_service.py` 內定義**模組常數**即可，例如 `_GENAI_EMBED_BATCH_SIZE = 100`，不從 config / .env 讀取，避免誤設大於 100 導致再度 400。
- **調整**：
  1. 使用常數作為每批上限。
  2. 將 `texts` 依序切成每段最多該上限的子列表（例如 `texts[0:100]`, `texts[100:200]`, ...）。
  3. 對每一子列表呼叫一次 `_embed_batch(sub_batch)`，收集回傳的 `List[List[float]]`。
  4. 若某次 `_embed_batch` 失敗（回傳 `[]`），整段 `embed()` 回傳 `[]` 並保留現有 log（呼叫端會降級 Stub）。
  5. 將各批的向量列表依序合併成一個 `List[List[float]]` 回傳，順序與輸入 `texts` 一致。

如此一來，當 `process_thisqa_to_graph.py` 對 IC 檔傳入 329 筆時，服務會自動分成 4 批（100+100+100+29）呼叫 API，不再觸發 400。

### 不需改動的檔案

- **scripts/process_thisqa_to_graph.py**：維持 `embedding_service.embed(qa_texts)` 單一呼叫即可。
- **app/services/qa_embedding_index.py**、**vector_service.py**：僅使用單一查詢或小量文字，無大批次需求。

---

## 小結

| 項目 | 說明 |
|------|------|
| 根因 | Gemini `embed_content` 單批最多 100 筆，IC 檔一次送 329 筆導致 400。 |
| 修復 | 在 `GoogleGenAIEmbeddingService.embed()` 內，將 `texts` 以每批 ≤100 分批呼叫 `embed_content`，再合併結果。 |
| 影響範圍 | 僅 embedding 服務實作；呼叫端與建圖腳本無需改動。 |
