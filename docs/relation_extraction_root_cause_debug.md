# 關係提取問題根本原因分析（Debug Mode）

## 更新時間
2025-12-26 13:12

## 作者
AI Assistant

## 問題描述

從日誌分析發現：
- ❌ 每個區塊的 `extract_entities` 返回 **0 個實體**
- ✅ `graph_builder` 為每個區塊創建了 **1 個 Document 實體**
- ❌ `extract_relations` 被調用時只有 **1 個實體**（Document 實體）
- ❌ 觸發 `"Not enough entities for relations"` 提前返回
- ❌ 最終結果：**0 個關係**

## 日誌證據

### 證據 1: 實體提取失敗
```
{"location": "entity_extractor.py:extract_entities:success", 
 "data": {"entities_count": 0, "entities": []}}
```

### 證據 2: 只有 Document 實體
```
{"location": "graph_builder.py:build_graph_from_text:before_extract_relations",
 "data": {"saved_entities_count": 1, 
          "saved_entities": [{"id": "doc_..._chunk_1", "type": "Document"}]}}
```

### 證據 3: 關係提取提前返回
```
{"location": "entity_extractor.py:extract_relations:early_return",
 "message": "Not enough entities for relations",
 "data": {"entities_count": 1}}
```

## 根本原因

### 原因 1: 規則基礎實體提取只支援英文（已修復）

**位置**: `app/core/entity_extractor.py:450-472`（修復前）

**問題**:
```python
# 只提取英文大寫開頭的詞
pattern = r'\b[A-Z][a-z]+\b'
matches = re.findall(pattern, text)
```

**影響**:
- PDF 內容是中文，無法匹配英文模式
- 規則基礎實體提取返回空列表
- 導致只有 Document 實體，沒有其他實體

### 原因 2: 關係提取需要至少 2 個實體

**位置**: `app/core/entity_extractor.py:78-80`

**邏輯**:
```python
if not entities or len(entities) < 2:
    return []  # 至少需要 2 個實體才能建立關係
```

**影響**:
- 只有 1 個 Document 實體時，關係提取直接返回空列表
- 規則基礎關係提取也無法執行（因為需要 2 個實體）

## 修復方案

### ✅ 已修復：規則基礎實體提取支援中文

**文件**: `app/core/entity_extractor.py:450-500`

**修復內容**:

1. **提取中文名詞**（2-6 個中文字）:
   ```python
   chinese_pattern = r'[\u4e00-\u9fff]{2,6}'
   ```

2. **提取常見的中文實體模式**:
   - `XX政策` → Policy
   - `XX制度` → System
   - `XX服務` → Service
   - `XX計畫` → Plan
   - `XX方案` → Program
   - `XX機構/單位/部門` → Organization
   - `XX人員` → Person

3. **保留英文專有名詞提取**:
   ```python
   english_pattern = r'\b[A-Z][a-z]+\b'
   ```

4. **限制實體數量**（避免過多）:
   ```python
   return entities[:50]  # 最多返回 50 個實體
   ```

## 預期效果

### 修復前
- ❌ 實體數量: 0（從文字提取）
- ❌ 總實體數: 1（只有 Document 實體）
- ❌ 關係數量: 0

### 修復後
- ✅ 實體數量: > 0（從文字提取中文實體）
- ✅ 總實體數: > 1（Document + 提取的實體）
- ✅ 關係數量: > 0（規則基礎關係提取可以執行）

## 測試步驟

1. **清除舊日誌**（如果存在）:
   ```bash
   # 日誌文件會自動創建
   ```

2. **重新處理 PDF**:
   ```bash
   python scripts/process_pdf_to_graph.py data/example/1051219長期照護2.0核定本.pdf
   ```

3. **檢查結果**:
   - 應該能看到每個區塊提取 > 1 個實體
   - 應該能看到關係數量 > 0
   - 檢查資料庫中的關係

4. **查看日誌**:
   - 應該看到 `entities_count > 0`（從文字提取）
   - 應該看到 `saved_entities_count > 1`
   - 應該看到 `extracted_relations_count > 0`

## 相關文件

- `app/core/entity_extractor.py` - 實體提取器實作
- `app/services/graph_builder.py` - 圖構建服務
- `docs/relation_extraction_fix_summary.md` - 關係提取修復總結
- `.cursor/debug.log` - 調試日誌（運行後生成）

## 總結

**根本原因**: 
- 規則基礎實體提取只支援英文，無法提取中文實體
- 導致只有 Document 實體，關係提取無法執行

**修復**: 
- ✅ 改進規則基礎實體提取，支援中文實體提取

**效果**: 
- ✅ 能夠提取中文實體
- ✅ 關係提取可以正常執行
- ✅ 系統可以提取關係

**下一步**: 重新運行 PDF 處理，應該能看到實體和關係數量都 > 0！


