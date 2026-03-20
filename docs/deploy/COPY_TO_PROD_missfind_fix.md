<!--
  更新時間：2026-03-20 13:33
  作者：AI Assistant
  修改摘要：missfind（graph 假陽性）修復—複製到正式機之檔案清單與路徑對照
-->

# 複製到正式區（Prod）— missfind / graph 關鍵字修復

**專案根目錄（本機開發）：**  
`C:\Development\langChain\source\care_rag\care_rag_api`

**請在正式機上覆蓋相同相對路徑**（與你 prd 上的 `care_rag_api` 根目錄對齊）。

---

## 必備（執行期程式，一定要複製）

| # | 相對路徑（自 `care_rag_api` 起） |
|---|----------------------------------|
| 1 | `app/core/graph_store.py` |
| 2 | `app/services/vector_service.py` |

---

## 建議一併複製（測試／驗證／文件）

| # | 相對路徑 |
|---|----------|
| 3 | `tests/test_core/test_graph_store_search_entities.py` |
| 4 | `scripts/verify_missfind_graph_fallback.py` |
| 5 | `docs/bug/missfind.md` |
| 6 | `docs/deploy/COPY_TO_PROD_missfind_fix.md`（本清單，可選） |
| 7 | `dev_readme.md` |

---

## 不需要因本修復而替換的檔案

- `data/graph.db`、`data/qa_vectors.db`：無 schema 變更，除非你要整包換資料再另案處理。
- `.env`：沿用 prd 既有設定。

---

## Windows 快速複製範例（在本機開發機執行）

將 `PROD_ROOT` 改成正式機上專案根目錄（例如 `\\172.31.6.123\share\care_rag_api` 或本機暫存路徑）：

```bat
set SRC=C:\Development\langChain\source\care_rag\care_rag_api
set PROD_ROOT=\\172.31.6.123\你的共用資料夾\care_rag_api

copy /Y "%SRC%\app\core\graph_store.py"            "%PROD_ROOT%\app\core\"
copy /Y "%SRC%\app\services\vector_service.py"     "%PROD_ROOT%\app\services\"
copy /Y "%SRC%\tests\test_core\test_graph_store_search_entities.py" "%PROD_ROOT%\tests\test_core\"
copy /Y "%SRC%\scripts\verify_missfind_graph_fallback.py" "%PROD_ROOT%\scripts\"
copy /Y "%SRC%\docs\bug\missfind.md"               "%PROD_ROOT%\docs\bug\"
copy /Y "%SRC%\docs\deploy\COPY_TO_PROD_missfind_fix.md" "%PROD_ROOT%\docs\deploy\"
copy /Y "%SRC%\dev_readme.md"                      "%PROD_ROOT%\"
```

若 `docs\deploy` 在 prd 不存在，請先建立資料夾再 copy。

---

## 複製後於正式機

1. 重啟服務（例如 NSSM：`net stop care_rag_api` → `net start care_rag_api`）。
2. 確認 `uvicorn` 為 `--host 0.0.0.0 --port 8002`（或你的 prd 埠）。
3. 驗證：`GET http://<prd>:8002/docs`；可選執行 `python scripts\verify_missfind_graph_fallback.py`。

---

## 變更摘要（對照用）

- `search_entities(..., include_type_match=False)` 時僅比對 **實體 name**；預設 `True` 維持舊行為。
- `_search_from_graph` 使用 `include_type_match=False`；graph 來源 `score=0.35`、`metadata.score_source=graph_keyword`。
- SQLite `search_entities` 增加 **`ORDER BY name`**（較穩定順序）。
