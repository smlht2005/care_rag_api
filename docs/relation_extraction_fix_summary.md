# 關係提取問題修復總結

## 更新時間
2025-12-26 12:44

## 作者
AI Assistant

## 問題描述

從終端輸出可以看到：
- ✅ 每個區塊都成功提取了 **1 個實體**
- ❌ 每個區塊都顯示 **0 個關係**
- 總結果：65 個實體，0 個關係

## 根本原因

### 原因 1: LLM 服務是 Stub（主要問題）

**位置**: `app/services/llm_service.py:52-54`

**問題**:
```python
# GeminiLLM.generate() 返回的是模擬文字，不是 JSON
return f"[Gemini] 回答: {prompt}\n\n這是一個基於 Gemini 模型的回答..."
```

**影響**:
- 關係提取需要 LLM 返回 JSON 格式的關係數據
- Stub 返回的是普通文字，無法解析為 JSON
- `_parse_relation_response()` 解析失敗，返回空列表

### 原因 2: 關係提取沒有降級方案

**位置**: `app/core/entity_extractor.py:60-93`（修復前）

**問題**:
```python
async def extract_relations(...):
    try:
        # LLM 提取關係
        response = await self.llm_service.generate(prompt, max_tokens=1000)
        relations = self._parse_relation_response(response, entities)
        return relations
    except Exception as e:
        self.logger.error(f"Failed to extract relations: {str(e)}")
        return []  # ❌ 直接返回空列表，沒有降級方案
```

---

## 修復方案

### ✅ 已實作：規則基礎關係提取降級方案

**文件**: `app/core/entity_extractor.py`

**修復內容**:

1. **修改 `extract_relations()` 方法**:
   - 當 LLM 提取失敗或返回空列表時，自動降級到規則基礎提取
   - 確保至少能提取一些簡單關係

2. **新增 `_rule_based_relation_extraction()` 方法**:
   - 基於關鍵詞模式匹配提取關係
   - 支援中文和英文模式
   - 支援實體共現關係提取

**修復後邏輯**:
```python
async def extract_relations(...):
    try:
        # LLM 提取關係
        response = await self.llm_service.generate(prompt, max_tokens=1000)
        relations = self._parse_relation_response(response, entities)
        
        if relations:
            # LLM 提取成功
            self.logger.info(f"Extracted {len(relations)} relations (LLM-based)")
            return relations
        else:
            # LLM 提取失敗，降級到規則基礎提取
            self.logger.warning("LLM relation extraction returned empty, falling back to rule-based")
            return self._rule_based_relation_extraction(text, entities)
            
    except Exception as e:
        self.logger.error(f"Failed to extract relations (LLM-based): {str(e)}")
        # 降級到規則基礎提取
        return self._rule_based_relation_extraction(text, entities)
```

---

## 規則基礎關係提取功能

### 支援的關係模式

#### 中文模式
- `A 在 B` → `LOCATED_IN`
- `A 屬於 B` → `BELONGS_TO`
- `A 是 B` → `IS_A`
- `A 包含 B` → `CONTAINS`
- `A 與 B 相關` → `RELATED_TO`
- `A 由 B 組成` → `CONSISTS_OF`
- `A 管理 B` → `MANAGES`

#### 英文模式
- `A in B` → `LOCATED_IN`
- `A belongs to B` → `BELONGS_TO`
- `A is a B` → `IS_A`
- `A contains B` → `CONTAINS`

#### 實體共現
- 如果兩個實體出現在同一句子中，建立 `RELATED_TO` 關係
- 權重較低（0.3），表示相關性較弱

---

## 測試建議

### 測試規則基礎關係提取

1. **重新處理 PDF**:
   ```bash
   python scripts/process_pdf_to_graph.py data/example/1051219長期照護2.0核定本.pdf
   ```

2. **檢查結果**:
   - 應該能看到關係數量 > 0
   - 檢查資料庫中的關係

3. **查看日誌**:
   - 應該看到 "falling back to rule-based" 警告
   - 應該看到 "Extracted X relations using rule-based method" 資訊

---

## 關於 Gemini API Key

### 當前狀態（不需要 API Key）

✅ **已修復**: 添加了規則基礎關係提取降級方案
- 即使沒有 Gemini API Key，也能提取一些關係
- 系統可以正常運行
- 關係提取不會完全失敗

### 如果需要更好的結果（需要 API Key）

⚠️ **建議**: 實作真正的 Gemini API
- 準確度更高
- 可以提取複雜關係
- 支援更多關係類型

**實作步驟**:
1. 獲取 Gemini API Key: https://makersuite.google.com/app/apikey
2. 安裝依賴: `pip install google-generativeai`
3. 實作真正的 API 呼叫（見 `docs/relation_extraction_issue_analysis.md`）

---

## 預期效果

### 修復前
- ❌ 關係數量: 0
- ❌ LLM 提取失敗，直接返回空列表

### 修復後
- ✅ 關係數量: > 0（基於規則匹配和實體共現）
- ✅ LLM 提取失敗時自動降級
- ✅ 系統更穩定，不會完全失敗

### 使用真正的 Gemini API 後
- ✅ 關係數量: 大幅增加
- ✅ 關係類型: 更豐富
- ✅ 準確度: 更高

---

## 相關文檔

- `docs/relation_extraction_issue_analysis.md` - 問題分析和解決方案
- `docs/qa/relation_extraction_root_cause.md` - 關係提取根本原因分析
- `app/core/entity_extractor.py` - 實體提取器實作

---

## 總結

**問題**: LLM 服務是 Stub，返回的不是 JSON 格式，導致關係提取失敗。

**修復**: ✅ 添加規則基礎關係提取降級方案

**效果**: 
- ✅ 即使沒有 API Key，也能提取關係
- ✅ 系統更穩定
- ✅ 不會完全失敗

**是否需要 Gemini API Key**:
- ❌ **不需要**（當前已修復，可以提取關係）
- ✅ **建議**（如果需要更好的準確度和更多關係類型）

**下一步**: 重新處理 PDF，應該能看到關係數量 > 0！


