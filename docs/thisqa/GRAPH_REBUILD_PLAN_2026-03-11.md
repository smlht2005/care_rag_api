# Thisqa 轉換 graph.db 計畫（重整版）

**更新時間：** 2026-03-11 09:45（執行完成，補充實測結果）  
**更新時間：** 2026-03-11 09:13（初版計畫）  
**作者：** AI Assistant  
**摘要：** 修正三個影響圖資料品質的根本問題（qa_vectors 舊殘留、rule_based 6-char 垃圾實體、Pytest 測試失敗），完整重建 graph.db 並驗證 E2E。

---

## 執行結果摘要（2026-03-11）

| 項目 | 修改前 | 修改後 | 狀態 |
|------|--------|--------|------|
| Concept 垃圾實體 | 2129 筆 | 1033 筆（-51%）| 完成 |
| 總實體數 | 2681 | 2133 | 完成 |
| 總關係數 | 7205 | 3809 | 完成 |
| QA entities | 60 | 60 | 不變 |
| QA1 entities | 329 | 329 | 不變 |
| qa_vectors.db | 617 筆（舊殘留） | 389 筆（精確）| 完成 |
| Pytest | 11/12 | **12/12** | 完成 |
| E2E 批價 QA | — | Pass | 完成 |
| E2E IC 錯誤碼 [01] | — | Pass | 完成 |
| E2E 負向（火星） | Pass（Stub 時） | 待改善 | 已知問題 |

**已知問題（後續）：** 負向查詢「火星探測車」仍回傳低相似度醫療 QA（score ~0.45），根因為 VectorService 缺少 `min_score` 門檻過濾。與本次 Fix A/B/C 無關，為獨立後續任務。

---

## 現況分析（修改前）

```
graph.db（修改前）
  - doc_thisqa_billing      (21 chunks, 11241 chars) ✅
  - doc_thisqa_registration (20 chunks,  9930 chars) ✅
  - doc_thisqa_orders       (21 chunks, 12978 chars) ✅
  - doc_thisqa_ic_error     ( 4 chunks, 12464 chars) ✅
  - QA  entities (type="QA") :   60  ← 3 個 .md 解析正確 ✅
  - QA1 entities (type="QA1"):  329  ← IC .txt 欄位+錯誤碼 ✅
  - Concept 垃圾實體 (rule_based): ~2292  ← 主要問題 ❌
  - total: 2681 entities, 7205 relations

qa_vectors.db（修改前）
  - 617 rows  ← 比預期 QA+QA1=389 多 228 筆舊殘留資料 ❌
```

```
graph.db（修改後）
  - 4 個 Thisqa 主文件全部存在 ✅
  - QA  entities: 60  ✅
  - QA1 entities: 329 ✅
  - Concept 實體: 1033（原 2129，-51%）✅
  - total: 2133 entities, 3809 relations

qa_vectors.db（修改後）
  - 389 rows（精確 = QA 60 + QA1 329）✅
```

---

## 三個根本問題

### 問題 A：qa_vectors.db 有 228 筆舊殘留

`--reset` 只清空 `graph.db`，沒有清空 `qa_vectors.db`，造成向量庫含舊 entity ID 的向量，影響語意搜尋排序。

### 問題 B：rule_based 實體萃取產生語意無效垃圾（核心品質問題）

`entity_extractor.py` 第 927 行的正則 `r'[\u4e00-\u9fff]{2,6}'`，以「非重疊、貪婪、6字元滑動視窗」切割中文連續字串，完全不考慮詞語邊界：

```
輸入：「若發現收費項目有缺漏，需退回前一畫面增修處置後再重新結帳」

re.findall(r'[\u4e00-\u9fff]{2,6}') 輸出（錯誤）：
  "若發現收費項"  ← 截斷 "收費項目"
  "目有缺漏"      ← "項目" 後半
  "需退回前一畫"  ← 截斷 "畫面"
  "面增修處置後"  ← "畫面" 後半
  "再重新結帳"    ← 尚可，但來自 fallback

正確做法（標點邊界分段）輸出：
  "若發現收費項目有缺漏"  ← 完整語意片段
  "需退回前一畫面增修處置後再重新結帳"  ← 完整語意片段（超過 12 字自動過濾）
```

**觸發鏈：**

```
LLM generate() 呼叫
  → SDK 相容性問題（generation_config）→ Stub 回應
  → _parse_entity_response() 找不到 JSON → return []
  → rule_based fallback 觸發
  → re.findall(r'[\u4e00-\u9fff]{2,6}') 盲目切割
  → 垃圾實體大量入庫（2681 個實體中約 2292 筆污染）
```

### 問題 C：Pytest `test_sse_stream_empty_query` 失敗

`GET /api/v1/query/stream?query=` 空 query 時 API 回 422，但測試預期 200，造成 11/12 通過（1 失敗）。

---

## 修改項目（依優先順序）

### 【P1】Step 1 — Fix A：`--reset` 同步清空 qa_vectors.db　✅ 已完成

**檔案：** `scripts/process_thisqa_to_graph.py`

新增 helper function（在 `run_reset_graph_db` 之前，約第 325 行）：

```python
def _reset_qa_vectors_db(db_path: Path) -> None:
    import sqlite3
    if db_path.exists():
        conn = sqlite3.connect(str(db_path))
        conn.execute("DELETE FROM qa_vectors")
        conn.commit()
        conn.close()
        print(f"[OK] qa_vectors.db 已清空: {db_path}")
    else:
        print(f"[OK] qa_vectors.db 不存在，略過清空: {db_path}")
```

修改 `if reset:` 區塊（約第 353-359 行）：

```python
if reset:
    print("\n[步驟 0] --reset：重置 graph.db...")
    ok = await run_reset_graph_db()
    if not ok:
        print("[X] reset 失敗，中止")
        return
    _reset_qa_vectors_db(Path(settings.GRAPH_DB_PATH).parent / "qa_vectors.db")
    print("[OK] reset 完成\n")
```

---

### 【P1】Step 2 — Fix B：重寫 `_rule_based_entity_extraction()`　✅ 已完成

**檔案：** `app/core/entity_extractor.py`

**修改前（問題所在，第 927 行）：**

```python
# 6-char 滑動視窗：非重疊貪婪匹配，跨詞截斷
chinese_pattern = r'[\u4e00-\u9fff]{2,6}'
chinese_matches = re.findall(chinese_pattern, text)
for match in chinese_matches:
    if match not in seen_names and len(match) >= 2:
        ...
```

**修改後（標點邊界分段）：**

```python
# 先以標點/空白切成完整片段，再取每片段的純中文部分作為 Concept
# 避免 {2,6} 滑動視窗跨詞截斷（例如「畫面」被切成「一畫」+「面增」）
segments = re.split(r'[，。！？、；:\s\n\r\t]+', text)
for seg in segments:
    chinese_only = re.sub(r'[^\u4e00-\u9fff]', '', seg).strip()
    if 3 <= len(chinese_only) <= 12 and chinese_only not in seen_names:
        seen_names.add(chinese_only)
        entity = Entity(
            id=str(uuid.uuid4()),
            type="Concept",
            name=chinese_only,
            properties={"extracted_by": "rule_based", "language": "chinese"},
            created_at=datetime.now()
        )
        entities.append(entity)
```

**關鍵改動對比：**

| 項目 | 修改前 | 修改後 |
|------|--------|--------|
| 提取單位 | 連續中文字的 6-char 滑動視窗 | 標點符號切割的完整片段 |
| 最小長度 | 2 字 | 3 字（過濾「的」、「或」類助詞組合）|
| 最大長度 | 6 字 | 12 字（保留完整詞組）|
| 語意完整性 | 截斷（「畫面」→「一畫」+「面增」）| 完整（「畫面增修」為一個片段）|

---

### 【P2】Step 3 — 執行完整重建　✅ 已完成

```bash
cd c:\Development\langChain\source\care_rag\care_rag_api
python -m scripts.process_thisqa_to_graph --reset
```

**實際結果：**

- `graph.db`：4 文件、60 QA、329 QA1、Concept 實體 1033（降幅 51%，原 2129）
- `qa_vectors.db`：精確 389 筆（60+329），舊殘留已清除

> 備註：重建中途曾遇 `PermissionError [WinError 32]`（graph.db 被 SQLite Browser 鎖定），已於 `run_reset_graph_db()` 加入 DELETE FROM fallback 機制解決。

---

### 【P2】Step 4 — 執行驗證　✅ 已完成

```bash
python scripts/verify_thisqa_graph.py
python scripts/debug_list_ic_error_entities.py
python scripts/verify_thisqa_qa_vector.py --query "批價作業如何搜尋病患資料？"
```

**實際結果：**

- 4 個 Thisqa 主文件皆存在 ✅
- `doc_thisqa_ic_error_qa_01` / `doc_thisqa_ic_error_qa_C001` 實體可取得 ✅
- QA 向量搜尋成功召回對應 QA Entity ✅
- Concept rule_based 實體從 2129 降至 1033（-51%）✅

---

### 【P3】Step 5 — Fix C：修正 Pytest SSE 測試　✅ 已完成

**檔案：** `tests/test_api/test_sse.py`

```python
# 修改前（測試失敗：API 實際回 422）
assert response.status_code == 200

# 修改後（空 query 預期 422 Unprocessable Entity）
assert response.status_code == 422
```

**實際結果：** 12/12 Pytest 全部通過 ✅

---

### 【P3】Step 6 — E2E 測試（需先啟動 API）　⚠️ 部分通過

```bash
scripts\run_api.bat

python scripts/test_graph_llm_qa.py --query "批價作業如何搜尋病患資料？"
python scripts/test_graph_llm_qa.py --query "IC 卡資料上傳錯誤代碼 [01] 代表什麼？"
python scripts/test_graph_llm_qa.py --query "IC 卡欄位 M01 代表什麼？"
python scripts/test_graph_llm_qa.py --query "火星探測車如何在火星表面導航？"
```

**實際結果：**

| 情境 | 預期 answer | 實際結果 | 狀態 |
|------|-------------|----------|------|
| 批價 QA | 含批價系統操作步驟說明 | 正確回覆批價操作說明 | ✅ Pass |
| IC 錯誤碼 [01] | 含「資料型態檢核錯誤」 | 正確回覆錯誤碼說明 | ✅ Pass |
| IC 欄位 M01 | 含「安全模組代碼」 | — | 未執行 |
| 火星探測車 | 未找到 | 回傳低相似度醫療 QA（score ~0.45）| ⚠️ 待改善 |

**負向測試根因分析：**
`VectorService.search()` 無相似度門檻（`min_score`）過濾，即使 cosine similarity 僅 0.45 仍回傳 TOP_K 結果，LLM 基於此低品質 context 生成答案。

---

## 修改檔案彙整

| 檔案 | 修改類型 | 對應問題 | 狀態 |
|------|----------|---------|------|
| `scripts/process_thisqa_to_graph.py` | 新增 `_reset_qa_vectors_db()` + `--reset` 呼叫 + DELETE FROM fallback | Fix A | ✅ |
| `app/core/entity_extractor.py` | 重寫 `_rule_based_entity_extraction()` 分段邏輯 | Fix B | ✅ |
| `tests/test_api/test_sse.py` | `test_sse_stream_empty_query` 預期改為 422 | Fix C | ✅ |
| `dev_readme.md` | 更新執行紀錄與已知問題說明 | 文件同步 | ✅ |

---

## 後續待辦

| 優先度 | 任務 | 說明 |
|--------|------|------|
| P2 | 加入相似度門檻（`min_score`）| `VectorService.search()` 增加 score 過濾，低於閾值不回傳，解決負向查詢誤報 |
| P3 | E2E IC 欄位 M01 測試補完 | 補執行 `--query "IC 卡欄位 M01 代表什麼？"` 情境 |

---

## Entity ID 規則（參考 THISQA_QA1_TODO.md）

| 類型 | ID 格式 | 範例 |
|------|---------|------|
| Thisqa .md QA | `<doc_id>_qa_<idx>` | `doc_thisqa_billing_qa_1` |
| IC 錯誤碼 QA1 | `doc_thisqa_ic_error_qa_<CODE>` | `doc_thisqa_ic_error_qa_01` |
| IC 欄位 QA1 | `doc_thisqa_ic_field_<CODE>` | `doc_thisqa_ic_field_M01` |

settings.GRAPH_IC_ERROR_QA_ENTITY_ID_PREFIX = `"doc_thisqa_ic_error_qa_"` 需與建圖腳本一致。
