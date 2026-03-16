# QA 匯入測試指南

**更新時間**：2026-01-13 15:20  
**作者**：AI Assistant  
**修改摘要**：更新標頭註解日期

**更新時間**：2025-12-30 10:30  
**目的**：說明如何測試新匯入的 QA 資料

## 快速測試步驟

### 1. 列出所有文件

查看資料庫中所有已匯入的文件：

```bash
py scripts/test_qa_import.py --list-docs
```

**輸出範例**：
```
============================================================
所有文件列表
============================================================

1. 掛號QA.md
   ID: registration_qa
   類型: qa_markdown
   QA 數量: 20

2. TAMIS 衛材與供應中心管理系統操作指南15qa.md
   ID: material_supply_qa
   類型: qa_markdown
   QA 數量: 15
```

### 2. 測試特定文件的 QA

驗證特定文件的 QA 是否正確匯入：

```bash
py scripts/test_qa_import.py --doc-id registration_qa
```

**測試內容**：
- ✅ 文件是否存在
- ✅ QA 實體數量是否正確
- ✅ QA 欄位完整性（question, answer, keywords, metadata 等）
- ✅ 文件與 QA 的關係是否正確

**輸出範例**：
```
============================================================
測試文件: registration_qa
============================================================

[文件資訊]
  名稱: 掛號QA.md
  ID: registration_qa
  類型: qa_markdown
  問答對數量: 20

[查詢 QA 實體]
  找到 20 個 QA 實體

[驗證 QA 完整性]
  完整 QA: 20/20

[QA 範例 (前 3 個)]
  1. QA #1: 登入掛號管理系統
     問題: 我要怎麼登入掛號系統開始作業？
     答案: 請依序輸入系統授權的帳號與密碼...
     關鍵字: 登入, 使用者帳號, 密碼, 掛號管理系統。
     分類: 系統登入

[檢查關係]
  文件到 QA 的關係: 20 個
  [OK] 關係數量與 QA 數量一致
```

### 3. 搜尋 QA

測試搜尋功能，查找相關的問答對：

```bash
# 搜尋英文關鍵詞
py scripts/test_qa_import.py --search F1 --limit 5

# 搜尋中文關鍵詞（可能會有編碼問題，建議使用英文）
py scripts/test_qa_import.py --search 掛號 --limit 5
```

**搜尋範圍**：
- 問題內容
- 答案內容
- 關鍵字列表

### 4. 使用查詢腳本（完整統計）

查看完整的資料庫統計資訊：

```bash
py scripts/query_qa_graph.py
```

**輸出內容**：
- 文件數量
- 問答對數量
- 知識點數量
- 實體和關係統計
- 文件列表
- 問答對範例

## 測試檢查清單

匯入新 QA 後，請檢查以下項目：

### ✅ 基本檢查

- [ ] 文件是否成功建立
- [ ] QA 數量是否正確
- [ ] 每個 QA 都有完整的欄位（question, answer, keywords, metadata）
- [ ] 文件與 QA 的關係是否正確建立

### ✅ 內容檢查

- [ ] 問題內容是否正確提取
- [ ] 答案內容是否完整
- [ ] 關鍵字是否正確
- [ ] Metadata 是否包含所有必要資訊（product, category, user_role, source）

### ✅ 功能檢查

- [ ] 搜尋功能是否正常
- [ ] 可以通過關鍵字找到相關 QA
- [ ] 可以通過文件 ID 查詢所有 QA

## 常見問題

### Q: 測試時顯示 "找不到文件"

**A:** 檢查文件 ID 是否正確：
```bash
# 先列出所有文件
py scripts/test_qa_import.py --list-docs

# 使用正確的文件 ID
py scripts/test_qa_import.py --doc-id <正確的文件ID>
```

### Q: QA 數量與預期不符

**A:** 可能的原因：
1. Markdown 檔案格式不符合預期
2. 正則表達式無法匹配某些 QA 格式
3. 某些 QA 被過濾（太短或格式不正確）

**解決方法**：
- 檢查 Markdown 檔案格式
- 查看腳本輸出中的解析日誌
- 手動檢查未匯入的 QA

### Q: 搜尋功能找不到結果

**A:** 可能的原因：
1. 關鍵詞拼寫錯誤
2. 中文編碼問題（Windows 終端）
3. 關鍵詞不在問題、答案或關鍵字中

**解決方法**：
- 使用英文關鍵詞測試
- 檢查 QA 的關鍵字列表
- 使用部分匹配（例如 "F1" 而不是 "F1 功能鍵"）

## 測試腳本參數說明

### test_qa_import.py

```bash
py scripts/test_qa_import.py [選項]

選項:
  --list-docs          列出所有文件
  --doc-id ID          測試特定文件
  --search KEYWORD     搜尋關鍵詞
  --db-path PATH       資料庫路徑（預設: ./data/graph_qa.db）
  --limit N            搜尋結果數量限制（預設: 5）
```

### query_qa_graph.py

```bash
py scripts/query_qa_graph.py [選項]

選項:
  --db-path PATH       資料庫路徑（預設: ./data/graph_qa.db）
  --search KEYWORD     搜尋關鍵詞
  --limit N            搜尋結果數量限制（預設: 10）
```

## 完整測試流程範例

```bash
# 1. 匯入新的 QA 檔案
py scripts/parse_qa_markdown_to_graph.py --md-file "docs/example/新QA.md" --doc-id "new_qa"

# 2. 列出所有文件，確認新文件已匯入
py scripts/test_qa_import.py --list-docs

# 3. 測試新文件的 QA
py scripts/test_qa_import.py --doc-id new_qa

# 4. 搜尋測試
py scripts/test_qa_import.py --search "關鍵詞" --limit 5

# 5. 查看完整統計
py scripts/query_qa_graph.py
```

## 相關文件

- `scripts/parse_qa_markdown_to_graph.py` - QA 匯入腳本
- `scripts/test_qa_import.py` - QA 測試腳本
- `scripts/query_qa_graph.py` - QA 查詢腳本
- `docs/clinic_manual_qa_graph_guide.md` - QA 圖譜建立指南
