# 如何建立更多 LLM 實體和關係

**更新時間**：2025-12-29 19:00  
**目的**：說明如何優化查詢以建立 50 個 LLM 實體和 128 個關係

## 當前限制

### 1. 文字長度限制

在 `parse_clinic_manual_pdfs_to_qa_graph.py` 中，LLM 實體提取目前限制為前 5000 字元：

```python
entities = await entity_extractor.extract_entities(
    full_text[:5000],  # 限制長度以避免過長
    entity_types=["Concept", "Process", "Function", "Document", "Policy", "Procedure"]
)
```

### 2. LLM Token 限制

在 `entity_extractor.py` 中，`max_tokens` 設定為 1000：

```python
response = await self.llm_service.generate(prompt, max_tokens=1000)
```

### 3. 規則基礎降級限制

如果 LLM 提取失敗，降級到規則基礎提取時，最多返回 50 個實體：

```python
return entities[:50]  # 最多返回50個實體
```

## 優化方案

### 方案 1：增加文字處理長度（推薦）

修改 `parse_clinic_manual_pdfs_to_qa_graph.py`，增加處理的文字長度：

```python
# 修改前
entities = await entity_extractor.extract_entities(
    full_text[:5000],  # 限制長度
    entity_types=["Concept", "Process", "Function", "Document", "Policy", "Procedure"]
)

# 修改後 - 增加處理長度
entities = await entity_extractor.extract_entities(
    full_text[:20000],  # 增加到 20000 字元
    entity_types=["Concept", "Process", "Function", "Document", "Policy", "Procedure"]
)
```

### 方案 2：分批處理（處理大型 PDF）

對於大型 PDF，可以分批處理：

```python
# 5.3 使用 LLM 提取更多實體和關係（分批處理）
print(f"\n[步驟 5.3/6] 使用 LLM 提取實體和關係（分批處理）...")
chunk_size = 10000  # 每批處理 10000 字元
all_entities = []
all_relations = []

for i in range(0, len(full_text), chunk_size):
    chunk = full_text[i:i + chunk_size]
    print(f"  處理區塊 {i//chunk_size + 1}...")
    
    try:
        # 提取實體
        chunk_entities = await entity_extractor.extract_entities(
            chunk,
            entity_types=["Concept", "Process", "Function", "Document", "Policy", "Procedure"]
        )
        all_entities.extend(chunk_entities)
        
        # 提取關係（需要基於已提取的實體）
        if chunk_entities:
            chunk_relations = await entity_extractor.extract_relations(
                chunk,
                chunk_entities
            )
            all_relations.extend(chunk_relations)
    except Exception as e:
        print(f"  ⚠️ 區塊 {i//chunk_size + 1} 處理失敗: {str(e)}")
        continue

# 去重實體
from app.core.entity_extractor import EntityExtractor
entities = entity_extractor._deduplicate_entities(all_entities)
print(f"✅ LLM 提取到 {len(entities)} 個實體（去重後）")
print(f"✅ LLM 提取到 {len(all_relations)} 個關係")
```

### 方案 3：增加 LLM Token 限制

修改 `entity_extractor.py`，增加 `max_tokens`：

```python
# 修改前
response = await self.llm_service.generate(prompt, max_tokens=1000)

# 修改後 - 增加 token 限制
response = await self.llm_service.generate(prompt, max_tokens=2000)  # 增加到 2000
```

### 方案 4：優化 Prompt（提高提取品質）

修改 `_build_entity_extraction_prompt` 方法，要求 LLM 提取更多實體：

```python
def _build_entity_extraction_prompt(
    self,
    text: str,
    entity_types: Optional[List[str]] = None
) -> str:
    """構建實體提取提示詞（優化版）"""
    entity_types_str = ", ".join(entity_types) if entity_types else "Person, Document, Concept, Location, Organization, Event"
    
    prompt = f"""請從以下文字中提取所有實體，並以 JSON 格式返回。

實體類型：{entity_types_str}

**重要要求**：
1. 盡可能提取所有相關實體（目標：50+ 個實體）
2. 包括所有重要的概念、流程、功能、政策、程序
3. 不要遺漏任何重要的實體

文字內容：
{text}

請返回 JSON 陣列，每個實體包含以下欄位：
- name: 實體名稱
- type: 實體類型
- properties: 其他屬性（字典格式）

範例回應：
[
  {{"name": "張三", "type": "Person", "properties": {{"role": "醫生"}}}},
  {{"name": "醫院", "type": "Organization", "properties": {{"location": "台北"}}}}
]

只返回 JSON，不要其他文字："""
    
    return prompt
```

### 方案 5：調整實體類型

使用更多實體類型，可以提取更多實體：

```python
entities = await entity_extractor.extract_entities(
    full_text[:20000],
    entity_types=[
        "Concept", "Process", "Function", "Document", "Policy", "Procedure",
        "Person", "Organization", "Location", "Event", "System", "Service",
        "Rule", "Regulation", "Method", "Tool", "Technology"
    ]
)
```

## 完整優化範例

以下是完整的優化版本：

```python
# 5.3 使用 LLM 提取更多實體和關係（優化版）
print(f"\n[步驟 5.3/6] 使用 LLM 提取實體和關係（優化版）...")

# 增加處理長度
text_for_llm = full_text[:20000]  # 增加到 20000 字元

try:
    # 擴展實體類型
    entity_types = [
        "Concept", "Process", "Function", "Document", "Policy", "Procedure",
        "Person", "Organization", "Location", "Event", "System", "Service",
        "Rule", "Regulation", "Method", "Tool", "Technology"
    ]
    
    # 提取實體
    entities = await entity_extractor.extract_entities(
        text_for_llm,
        entity_types=entity_types
    )
    print(f"✅ LLM 提取到 {len(entities)} 個實體")
    
    # 提取關係
    if entities:
        relations = await entity_extractor.extract_relations(
            text_for_llm,
            entities
        )
        print(f"✅ LLM 提取到 {len(relations)} 個關係")
    else:
        relations = []
        print(f"⚠️ 沒有實體，無法提取關係")
        
except Exception as e:
    print(f"⚠️ LLM 實體提取失敗: {str(e)}，繼續處理...")
    entities = []
    relations = []
```

## 檢查和驗證

### 1. 檢查 LLM 服務配置

確保 LLM API key 已正確配置：

```bash
# 檢查環境變數
echo $GEMINI_API_KEY  # 或 $OPENAI_API_KEY
```

### 2. 檢查提取結果

執行腳本後，檢查輸出：

```bash
python scripts/parse_clinic_manual_pdfs_to_qa_graph.py
```

應該看到類似輸出：
```
✅ LLM 提取到 50 個實體
✅ LLM 提取到 128 個關係
```

### 3. 查詢資料庫驗證

使用查詢腳本驗證：

```bash
python scripts/query_qa_graph.py
```

## 常見問題

### Q1: 為什麼只提取到少量實體？

**A:** 可能原因：
1. 文字長度限制（只處理前 5000 字元）
2. LLM Token 限制（max_tokens=1000）
3. LLM 服務配置問題
4. PDF 文字提取品質不佳

**解決方案：**
- 增加文字處理長度
- 增加 max_tokens
- 檢查 LLM API key
- 檢查 PDF 文字提取結果

### Q2: 如何確保提取到 50+ 實體和 128+ 關係？

**A:** 建議步驟：
1. 增加文字處理長度到 20000+ 字元
2. 增加 max_tokens 到 2000+
3. 使用分批處理（對於大型 PDF）
4. 擴展實體類型列表
5. 優化 Prompt 要求更多實體

### Q3: LLM 提取失敗怎麼辦？

**A:** 系統會自動降級到規則基礎提取：
- 規則基礎提取最多返回 50 個實體
- 關係提取基於實體共現和模式匹配
- 檢查 `.cursor/debug.log` 了解失敗原因

## 總結

要建立 50 個 LLM 實體和 128 個關係，建議：

1. ✅ **增加文字處理長度**：從 5000 增加到 20000 字元
2. ✅ **增加 Token 限制**：從 1000 增加到 2000
3. ✅ **擴展實體類型**：使用更多實體類型
4. ✅ **分批處理**：對於大型 PDF，使用分批處理
5. ✅ **優化 Prompt**：明確要求提取更多實體

按照以上方案優化後，應該能夠建立足夠的 LLM 實體和關係。

