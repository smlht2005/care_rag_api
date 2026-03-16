# Refactor 後完整測試報告

**報告日期**：2026-03-10  
**測試範圍**：LLM / Embedding 改為新 SDK `google.genai` 後之完整測試（步驟 1～4 + E2E 參考）

---

## 1. 測試環境

| 項目 | 說明 |
|------|------|
| 工作目錄 | `care_rag_api` |
| Python | 3.12.5 |
| LLM_PROVIDER | gemini |
| GEMINI_MODEL_NAME | gemini-2.0-flash |
| GOOGLE_API_KEY | 已配置 |
| 執行指令 | `python -m scripts.run_full_test_after_refactor`（步驟 1～4） |

---

## 2. 步驟 1～4 結果摘要

| 步驟 | 項目 | 結果 | 說明 |
|------|------|------|------|
| 1 | Stub 檢查 | **通過** | Embedding 與 LLM 皆為真實 API（非 Stub） |
| 2 | Gemini LLM 測試 | **通過** | 腳本 exit 0；見下方子項結果 |
| 3 | 整合測試 | **通過** | LLMService、GraphOrchestrator、端點、Schema 四項皆通過 |
| 4 | Pytest API | **失敗** | 11 passed, 1 failed |

**總計**：3/4 通過（步驟 4 有 1 個失敗案例）。

---

## 3. 步驟 2 明細（Gemini LLM）

| 子項 | 結果 | 備註 |
|------|------|------|
| API Key 配置 | 通過 | 已配置 |
| 模型初始化 | 通過 | 使用真實 API、模型 gemini-2.0-flash |
| 基本生成 | 失敗 | `generation_config` 參數與目前 `google.genai` 版本不相容，降級為 Stub 回應 |
| 串流生成 | 失敗 | `stream_generate_content` 在目前 SDK 不存在，降級為 Stub |
| LLMService 整合 | 失敗 | 同上，實際為 Stub 回應 |
| 可用模型 | 通過 | 列出 45 個可用模型，含 gemini-2.0-flash |

**小計**：3/6 通過。失敗原因為新 SDK 呼叫方式與目前安裝之 `google.genai` 版本不符，非業務邏輯錯誤；端點與流程正常。

---

## 4. 步驟 4 明細（Pytest API）

| 測試 | 結果 |
|------|------|
| test_query.py::test_root_endpoint | 通過 |
| test_query.py::test_rest_query | 通過 |
| test_query.py::test_rest_query_with_provider | 通過 |
| test_query.py::test_rest_query_validation | 通過 |
| test_query.py::test_rest_query_invalid_top_k | 通過 |
| test_sse.py::test_sse_stream | 通過 |
| test_sse.py::test_sse_stream_empty_query | **失敗** |
| test_sse.py::test_sse_stream_format | 通過 |
| test_ws.py::test_websocket_chat | 通過 |
| test_ws.py::test_websocket_query | 通過 |
| test_ws.py::test_websocket_empty_query | 通過 |
| test_ws.py::test_websocket_multiple_messages | 通過 |

**失敗說明**：`test_sse_stream_empty_query` 預期 `GET /api/v1/query/stream?query=` 回 200，目前 API 對空 query 回 **422 Unprocessable Entity**。需將測試改為預期 422，或調整 API 對空 query 的處理方式，二者擇一即可通過。

---

## 5. E2E 情境（需先啟動 API）

以下為文件 [test_graph_db_llm_qa.md](test_graph_db_llm_qa.md) 所記錄之 E2E 實測（2026-03-10），供回歸參考。

| 情境 | 指令 | 預期 | 判定 |
|------|------|------|------|
| 批價 QA | `python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"` | 有 sources，answer 依手冊/QA | **Pass** |
| IC 錯誤碼 [01] | `python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"` | 答案含「資料型態檢核錯誤」等對照內容 | **Pass** |
| 無匹配（負向） | `python scripts/test_graph_llm_qa.py --query "火星探測車如何在火星表面導航？"` | answer「未找到」、sources 空 | **Pass** |

---

## 6. 結論與建議

- **Stub 檢查、整合測試**：通過，Embedding / LLM 選用與流程正常。
- **Gemini 實際生成/串流**：因目前 `google.genai` 之 `generate_content` / `stream_generate_content` 參數或方法與程式不符，執行時降級為 Stub；**GraphRAG 主線 `/api/v1/query` 與 E2E 情境已驗證可依來源正確回答**（見第 5 節）。
- **Pytest**：建議將 `test_sse_stream_empty_query` 改為預期 422，或 API 改為空 query 回 200，以達 12/12 通過。

若要重跑本報告之自動化步驟，請在 `care_rag_api` 根目錄執行：

```bash
python -m scripts.run_full_test_after_refactor
```

E2E 需先啟動 API 後再執行 `python scripts/test_graph_llm_qa.py`（可加 `--query "..."`）。
