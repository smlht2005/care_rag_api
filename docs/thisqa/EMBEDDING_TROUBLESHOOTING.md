# Embedding 故障排除總結

**更新時間：** 2026-03-09  
**適用：** Thisqa QA 向量檢索（graph.db + qa_vectors.db）、`process_thisqa_to_graph.py` 建圖

---

## 1. 問題與根因總覽

| 現象 | 根因 | 解法 |
|------|------|------|
| `404 NOT_FOUND: models/text-embedding-004 is not found for API version v1beta` | **Gemini API**（GOOGLE_API_KEY / generativelanguage.googleapis.com）的 **v1beta** 不支援 `text-embedding-004`，僅支援 `gemini-embedding-001` | 新 SDK 預設改為 `gemini-embedding-001`；若 .env 設 `text-embedding-004` 則程式自動改為 `gemini-embedding-001` 並 log 警告 |
| `model is required.` | `.env` 未設 `GEMINI_EMBEDDING_MODEL` 時，config 為 `None`；`getattr(settings, "GEMINI_EMBEDDING_MODEL", "text-embedding-004")` 因「屬性存在但值為 None」回傳 `None`，未使用預設值 | 改為 `... or getattr(..., None) or "gemini-embedding-001"`，確保一定有 model 字串 |
| `Invalid input type. Expected one of: str, Model, or TunedModel` | **舊版** `google.generativeai` 的 `embed_content(content=...)` 只接受**單一字串**，傳 list 會觸發錯誤 | 舊版 `GeminiEmbeddingService` 改為逐筆呼叫 `embed_content(content=單一 str)`，再彙整結果 |
| `embed_content() got an unexpected keyword argument 'output_dimensionality'` | 部分 **google-genai** 版本不支援 `output_dimensionality` 參數 | 不再傳該參數；取得回傳向量後在本地截斷至 `VECTOR_DIMENSION`（768）維 |
| `.env` 設 `GEMINI_EMBEDDING_MODEL=text-embedding-004` 仍 404 | 環境變數覆寫預設，程式依設定使用 text-embedding-004，而該模型在 Gemini API v1beta 不存在 | 將 .env 改為 `gemini-embedding-001`；程式內若偵測到 `text-embedding-004` 強制改用 `gemini-embedding-001` |
| `FutureWarning: google.generativeai ... Please switch to google.genai` | 舊套件已棄用，import 時會發出警告 | 在 `llm_service.py` 與 `embedding_service.py` 的 import 前以 `warnings.filterwarnings` 抑制該 FutureWarning |

---

## 2. 建議環境設定（.env）

- **使用新 SDK（推薦）**：`USE_GOOGLE_GENAI_SDK=true`  
- **Embedding 模型**：`GEMINI_EMBEDDING_MODEL=gemini-embedding-001`（或省略，使用程式預設）  
- **勿在 Gemini API 情境使用**：`text-embedding-004`（僅 Vertex/部分端點支援，會 404）

---

## 3. 相關檔案

- **Embedding 服務**：`app/services/embedding_service.py`  
  - `GoogleGenAIEmbeddingService`（新 SDK，預設 `gemini-embedding-001`，向量截斷至 768）  
  - `GeminiEmbeddingService`（舊 SDK，逐筆 content，預設 `models/embedding-001`）  
  - `get_default_embedding_service()`：依 `USE_GOOGLE_GENAI_SDK` 選擇新/舊，不可用時 Stub  
- **設定**：`app/config.py`（`USE_GOOGLE_GENAI_SDK`、`GEMINI_EMBEDDING_MODEL`、`VECTOR_DIMENSION`）  
- **建圖**：`scripts/process_thisqa_to_graph.py`（embed 失敗時改 Stub 寫入 QA 索引，確保流程完成）

---

## 4. 驗證步驟

1. 建圖：`python scripts/process_thisqa_to_graph.py --reset`（不應再出現 embedding 404 / model is required / output_dimensionality 錯誤）  
2. 驗證 QA 向量：`python scripts/verify_thisqa_qa_vector.py --query "批價作業如何搜尋病患資料？"`  
3. 問答：`python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"` 或直接呼叫 `POST /api/v1/query`
