# 基於 Neo4j 的醫療 GraphRAG API 設計計劃

## 重要架構決策

### 資料庫分離策略

**醫療知識圖譜：全新的獨立 Neo4j 資料庫**
- 創建全新的 `Neo4jGraphStore`，專門用於醫療知識圖譜
- 使用 Neo4j Python Driver
- 支援 Cypher 查詢語言
- 完全獨立於現有 SQLite GraphStore

**通用知識庫：現有 SQLite GraphStore（完全不動）**
- 現有 SQLite GraphStore 完全保留
- 現有通用知識庫端點完全保留
- 現有 GraphOrchestrator 完全保留
- 不修改任何現有代碼

### 架構分離原則

```
┌─────────────────────────────────────────┐
│         通用知識庫（現有）               │
│  - SQLiteGraphStore                     │
│  - GraphOrchestrator                    │
│  - /api/v1/knowledge/*                  │
│  - /api/v1/query                        │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│         醫療知識圖譜（全新）             │
│  - Neo4jGraphStore                      │
│  - MedicalGraphOrchestrator             │
│  - /api/v1/medical/*                    │
└─────────────────────────────────────────┘
```

## 新 API 端點設計

### 1. 醫療 FHIR 資料攝取端點

**POST /api/v1/medical/fhir/ingest**

功能：攝取 FHIR 格式的住院病歷資料，構建 Neo4j 醫療知識圖譜

請求體範例：
```json
{
  "patient": {
    "id": "P001",
    "name": "王小明",
    "age": 65,
    "gender": "M"
  },
  "encounter": {
    "id": "E001",
    "type": "Inpatient",
    "admit_date": "2024-01-01",
    "discharge_date": "2024-01-07"
  },
  "diagnoses": [
    {
      "id": "D001",
      "icd10": "J18.9",
      "display": "Community-acquired pneumonia",
      "role": "Primary"
    }
  ],
  "medications": [
    {
      "drug_code": "J01CA04",
      "drug_name": "Antibiotic A",
      "start_day": 1,
      "end_day": 3
    }
  ],
  "events": [
    {
      "id": "EV001",
      "type": "AKI",
      "description": "Acute kidney injury",
      "date": "2024-01-03",
      "cause": "Antibiotic A"
    }
  ],
  "procedures": [],
  "lab_results": []
}
```

### 2. 醫療知識圖譜查詢端點

**GET /api/v1/medical/graph/encounter/{encounter_id}/primary-diagnosis**

功能：查詢特定住院的主診斷

**GET /api/v1/medical/graph/encounter/{encounter_id}/complications**

功能：查詢併發症及原因

**GET /api/v1/medical/graph/encounter/{encounter_id}/treatments**

功能：查詢治療轉折

**GET /api/v1/medical/graph/encounter/{encounter_id}/timeline**

功能：查詢時間軸事件

### 3. 住院摘要生成端點

**POST /api/v1/medical/summaries/generate**

功能：基於 GraphRAG 生成住院摘要

請求體：
```json
{
  "encounter_id": "E001",
  "summary_type": "inpatient",  // inpatient | discharge | clinical_narrative
  "include_evidence": true,
  "language": "zh-TW"  // zh-TW | en
}
```

### 4. 批次摘要生成端點

**POST /api/v1/medical/summaries/batch**

功能：批次生成多個住院摘要

請求體：
```json
{
  "encounter_ids": ["E001", "E002", "E003"],
  "summary_type": "inpatient",
  "output_format": "json"  // json | pdf
}
```

### 5. PDF 報告生成端點

**POST /api/v1/medical/reports/pdf**

功能：生成 PDF 格式的住院摘要報告

請求體：
```json
{
  "encounter_ids": ["E001", "E002"],
  "report_type": "inpatient_summary",
  "include_prompt_context": true,
  "include_timeline": true
}
```

### 6. 臨床驗證端點

**POST /api/v1/medical/validation/clinical-guardrail**

功能：驗證生成的摘要是否符合臨床規則

## 實作計劃

### Phase 1: Neo4j 醫療資料庫基礎架構（1-2週）

1. **Neo4j 連線配置**
   - 在 `app/config.py` 添加 Neo4j 配置（URI, 用戶名, 密碼）
   - 環境變數：`NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`

2. **創建 Neo4jGraphStore**
   - 新建 `app/core/neo4j_graph_store.py`
   - 實現 `GraphStore` 抽象介面
   - 使用 Neo4j Python Driver
   - 支援醫療實體和關係的 CRUD 操作
   - 實現 Cypher 查詢方法

3. **醫療實體和關係定義**
   - 新建 `app/core/medical_entities.py`
   - 定義醫療實體類型：Patient, Encounter, Diagnosis, Medication, ClinicalEvent, Procedure, LabResult
   - 定義醫療關係類型：HAS_ENCOUNTER, HAS_DIAGNOSIS, TREATED_BY, CAUSES, RESULTS_IN, OCCURRED_ON, FOLLOWED_BY

4. **FHIR 資料適配器**
   - 新建 `app/services/fhir_adapter.py`
   - FHIR 格式到 Neo4j 節點/關係的轉換邏輯

### Phase 2: 醫療 GraphRAG Orchestrator（1-2週）

1. **醫療 GraphBuilder**
   - 新建 `app/core/medical_graph_builder.py`
   - 使用 Neo4jGraphStore
   - 從 FHIR 資料構建醫療知識圖譜
   - 建立時間軸關係

2. **醫療 EntityExtractor**
   - 新建 `app/services/medical_entity_extractor.py`
   - 醫療實體提取邏輯（可復用部分現有 LLM 邏輯）

3. **醫療 GraphRAG Orchestrator**
   - 新建 `app/services/medical_orchestrator.py`
   - 實現醫療查詢方法：
     - `get_primary_diagnosis(encounter_id)`
     - `get_complications(encounter_id)`
     - `get_treatments(encounter_id)`
     - `get_timeline(encounter_id)`
   - Prompt Assembly（Jinja2 模板）
   - Clinical Guardrail 驗證

### Phase 3: API 端點實作（1週）

1. **醫療 API Schemas**
   - 新建 `app/api/v1/schemas/medical.py`
   - Pydantic 模型定義

2. **醫療 API 端點**
   - 新建 `app/api/v1/endpoints/medical.py`
   - 實作所有醫療端點
   - 註冊到路由：`app/api/v1/router.py`

3. **依賴注入**
   - 在 `app/api/v1/dependencies.py` 添加醫療服務依賴

### Phase 4: 摘要生成與 PDF 報告（1週）

1. **摘要生成服務**
   - 新建 `app/services/summary_generator.py`
   - 使用醫療 Orchestrator 生成摘要

2. **PDF 報告生成**
   - 新建 `app/services/pdf_report_generator.py`
   - 使用 reportlab 或 fpdf 生成 PDF

3. **Clinical Guardrail**
   - 新建 `app/core/clinical_guardrail.py`
   - 臨床規則驗證邏輯

### Phase 5: 整合測試與優化（1週）

1. 端到端測試
2. 效能優化
3. 文檔完善

## 技術棧

- **醫療圖資料庫**：Neo4j（全新，獨立）
- **Neo4j Driver**：neo4j Python package
- **通用圖資料庫**：SQLiteGraphStore（現有，完全不動）
- **Prompt 模板**：Jinja2
- **PDF 生成**：reportlab 或 fpdf
- **驗證**：Pydantic 模型驗證 + 自訂臨床規則

## 檔案結構

```
app/
├── api/v1/endpoints/
│   ├── medical.py                    # 新增：醫療專用端點
│   └── ...                          # 現有端點完全不動
├── api/v1/schemas/
│   ├── medical.py                    # 新增：醫療 API Schemas
│   └── ...
├── core/
│   ├── neo4j_graph_store.py          # 新增：Neo4j 圖儲存（醫療專用）
│   ├── medical_entities.py           # 新增：醫療實體定義
│   ├── medical_graph_builder.py      # 新增：醫療圖構建（使用 Neo4j）
│   ├── clinical_guardrail.py         # 新增：臨床驗證
│   ├── graph_store.py                # 現有：SQLiteGraphStore（完全保留，不修改）
│   └── orchestrator.py               # 現有：GraphOrchestrator（完全保留，不修改）
├── services/
│   ├── medical_orchestrator.py       # 新增：醫療 GraphRAG Orchestrator（使用 Neo4j）
│   ├── medical_entity_extractor.py   # 新增：醫療實體提取器
│   ├── fhir_adapter.py               # 新增：FHIR 資料適配器
│   ├── summary_generator.py          # 新增：摘要生成服務
│   ├── pdf_report_generator.py       # 新增：PDF 報告生成
│   ├── graph_builder.py              # 現有：GraphBuilder（完全保留，不修改）
│   └── ...
└── config.py                         # 修改：添加 Neo4j 配置
```

## 配置更新

在 `app/config.py` 中添加：

```python
# Neo4j 醫療資料庫設定（全新）
NEO4J_URI: str = "bolt://localhost:7687"
NEO4J_USER: str = "neo4j"
NEO4J_PASSWORD: Optional[str] = None
NEO4J_DATABASE: str = "neo4j"  # 可選：指定資料庫名稱
```

## 依賴更新

在 `requirements.txt` 中添加：

```
neo4j>=5.0.0          # Neo4j Python Driver
jinja2>=3.0.0         # Prompt 模板引擎
reportlab>=4.0.0      # PDF 生成（或使用 fpdf）
```

## 成功標準

1. ✅ Neo4j 資料庫連線成功
2. ✅ 可以攝取 FHIR 格式資料並構建 Neo4j 醫療知識圖譜
3. ✅ 可以查詢主診斷、併發症、治療轉折
4. ✅ 可以生成結構化的住院摘要
5. ✅ 可以批次處理多個住院摘要
6. ✅ 可以生成 PDF 格式報告
7. ✅ 通過臨床驗證檢查
8. ✅ 現有 SQLite GraphStore 和通用 API 完全不受影響

## 關鍵設計原則

1. **完全分離**：醫療 Neo4j 資料庫與通用 SQLite 資料庫完全獨立
2. **不破壞現有功能**：所有現有代碼和 API 端點保持不變
3. **獨立擴展**：醫療 API 可以獨立開發、測試、部署
4. **清晰邊界**：醫療和通用知識庫有明確的功能邊界

## 實作待辦事項

- [ ] 在 config.py 中添加 Neo4j 連線配置（URI, 用戶名, 密碼），更新 requirements.txt 添加 neo4j 依賴
- [ ] 創建全新的 Neo4jGraphStore 類別，實現 GraphStore 抽象介面，專門用於醫療知識圖譜（不修改現有 SQLiteGraphStore）
- [ ] 設計醫療實體類型（Patient, Encounter, Diagnosis, Medication, ClinicalEvent, Procedure, LabResult）
- [ ] 設計醫療關係類型（HAS_ENCOUNTER, HAS_DIAGNOSIS, TREATED_BY, CAUSES, RESULTS_IN, OCCURRED_ON, FOLLOWED_BY）
- [ ] 建立 FHIR 資料適配器，將 FHIR 格式轉換為 Neo4j 節點和關係
- [ ] 建立醫療專用 GraphBuilder（使用 Neo4jGraphStore）
- [ ] 建立醫療專用 EntityExtractor
- [ ] 建立醫療 GraphRAG Orchestrator（使用 Neo4j），實現查詢主診斷、併發症、治療轉折等方法
- [ ] 建立住院摘要 Prompt 模板（Jinja2）
- [ ] 建立臨床驗證服務（Clinical Guardrail）
- [ ] 建立摘要生成服務
- [ ] 建立 PDF 報告生成服務（reportlab 或 fpdf）
- [ ] 建立醫療 API Pydantic Schemas
- [ ] 建立醫療 API 端點（FHIR 攝取、圖譜查詢、摘要生成、PDF 報告）並註冊路由
- [ ] 進行端到端整合測試，確保 Neo4j 醫療 API 正常運作且不影響現有 SQLite 系統
- [ ] 撰寫醫療 API 文檔和使用指南

---

**建立時間**：2025-01-03  
**基礎文檔**：基於 ChatGPT 對話記錄（checkorg.md）中的 GraphRAG 醫療架構設計  
**架構決策**：使用獨立的 Neo4j 資料庫，與現有 SQLite GraphStore 完全分離

