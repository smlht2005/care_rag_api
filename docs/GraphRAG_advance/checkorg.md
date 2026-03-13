這是 ChatGPT 和匿名之間的對話副本。


你說：
這是一個非常前沿且重要的話題，我們一起來深入了解！簡單來說，兩者都是為了讓大型語言模型（LLM）能夠使用它訓練資料以外的私有數據，但在**檢索方式**和**對數據的理解深度**上有著根本的區別。
 
 
- ​**標準 RAG (Retrieval-Augmented Generation)**：主要依賴**向量相似度（Vector Similarity）**。它將文檔切成小塊，當你提問時，它會去尋找與你的問題在語意上最接近的那些片段，然後丟給 LLM 整理答案。這就像在圖書館裡根據關鍵字快速翻找特定的幾頁書。
 
- ​**GraphRAG**：則是在此基礎上引入了**知識圖譜（Knowledge Graph）**。它會先將數據構建成一個包含「實體」與「關係」的網絡結構。這讓它不僅能找到相似的片段，還能理解概念之間的關聯性，甚至回答跨越多個文檔的複雜問題。
 

 
​為了更精準地幫助你理解它們的差異，你想從哪個角度切入？
 
 
1. ​**核心機制與比喻 🔍** 深入探討「向量搜索」與「圖譜遍歷」的具體運作差異，我們可以用「點與線」的概念來視覺化這個過程。
 
2. ​**解決的痛點與應用場景 🎯** 了解為什麼標準 RAG 在回答「這份數據集的總結是什麼？」這類宏觀問題時會表現不佳，以及 GraphRAG 如何解決這個「見樹不見林」的問題。
 
3. ​**成本與效率的權衡 ⚖️** GraphRAG 聽起來很強大，但它的構建成本、速度與標準 RAG 相比如何？這對於實際落地非常關鍵。

你是LLM RAG專家，受眾HlS IT要做医療的住院病歷摘要檢，要如何簡别其技術差異
ChatGPT 說：
很好，這個問題問得非常到位，而且情境也選得很專業。我會用「HIS IT／醫療住院病歷摘要檢索」這個真實落地場景，幫你一眼就能分辨「標準 RAG」與「GraphRAG」在技術本質、能力邊界、是否值得導入上的差異。

一句話先給結論（給主管／決策者用）
如果只是「找相關病歷內容來幫醫師看」，用標準 RAG 就夠；
如果要「理解整個住院過程、病因關聯、跨科整合與時間脈絡」，一定要 GraphRAG。

一、用「住院病歷摘要」來直觀對比
🎯 醫師實際會問的問題長這樣
「請摘要這位病人本次住院的主要問題、處置重點、併發症與後續追蹤建議」

這個問題，看似簡單，其實非常難。

二、標準 RAG：適合「片段式查找」
🔧 技術本質（用 IT 能秒懂的說法）
資料處理方式

病歷 → 切 chunk → 向量化 → 存 Vector DB

查詢方式

問題 → 向量化 → 找最相似的病歷片段（Top-K）

LLM 任務

把「撿回來的幾段文字」拼成一段話

🏥 套用在住院病歷會發生什麼事？
它擅長的問題
✔「病人有沒有糖尿病？」
✔「住院期間使用了哪些抗生素？」
✔「出院診斷是什麼？」

👉 因為這些都是局部事實檢索

它不擅長的問題（重點來了）
❌「這次住院的**主軸問題是什麼？」
❌「併發症與原始診斷的因果關係？」
❌「治療策略為何在中途改變？」

⚠️ 原因只有一個：

RAG 只知道「哪段文字像」，不知道「哪件事比較重要、誰導致誰」

📌 用一句比喻給醫療 IT
標準 RAG = 把病歷當成「一堆便條紙」來找

三、GraphRAG：適合「醫療敘事與因果理解」
🔧 技術本質（這裡是關鍵差異）
GraphRAG 多了一個結構化理解層：

病人
 ├─ 診斷
 │    ├─ 主診斷
 │    └─ 次要診斷
 ├─ 處置
 │    ├─ 手術
 │    └─ 用藥
 ├─ 事件
 │    ├─ 併發症
 │    └─ 感染
 └─ 時間軸
每一個節點都有「關係」：

因果（導致、引發）

時間（之前、之後）

隸屬（主要／次要）

跨科別

🏥 套用在住院病歷摘要會發生什麼？
GraphRAG 能回答的問題
✔「本次住院的主問題是什麼？」
✔「哪些併發症影響了治療策略？」
✔「治療調整的原因與時間點？」
✔「出院建議是根據哪些事件？」

👉 因為它不是撿片段，而是走關係圖

📌 給醫療 IT 的一句話比喻
GraphRAG = 把病歷變成「一個可推理的住院故事」

四、關鍵技術差異速覽表（給簡報用）
面向	標準 RAG	GraphRAG
資料單位	文字片段	醫療實體＋關係
檢索方式	向量相似度	圖譜遍歷 + 向量
時間軸理解	幾乎沒有	原生支援
因果推理	❌	✅
跨文件整合	弱	強
住院摘要品質	普通	接近主治醫師
建置成本	低	中～高
五、給 HIS IT 的「導入判斷準則」
✅ 先用標準 RAG 的情境
病歷全文檢索

輔助醫師快速看資料

法遵／查詢型需求

POC、快速上線

🚀 一定要 GraphRAG 的情境
自動住院病歷摘要

DRG / DPC 分析

病程敘事（Clinical Narrative）

AI 輔助出院摘要

醫療品質指標解釋

六、實務建議（最重要）
醫療不是「問答系統」，而是「病程推理系統」

👉 實戰架構最佳解是：

GraphRAG（結構與關係）
   + 
標準 RAG（細節補充）
   →
LLM 生成「住院摘要」
如果你願意，下一步我可以直接幫你做：

🧠「住院病歷 Graph Schema（診斷／處置／事件）」

📄「GraphRAG vs RAG 的醫療簡報版 5 頁」

🏗「HIS 架構圖（怎麼跟 EMR / FHIR 接）」

🤖「住院摘要 Prompt + 驗證規則（防幻覺）」

你想往技術設計、簡報說服主管，還是實際 PoC 架構哪一個方向？

你說：
用python 以住院病歷Example舉例比較二者技術差異
ChatGPT 說：
很好，這個需求非常適合用「最小可懂的 Python 範例」來說清楚差異。
下面我會用同一份「住院病歷範例」，用 標準 RAG 與 GraphRAG 各做一次，讓 HIS / 醫療 IT 一看就知道：

👉 差異不在 LLM，而在「你讓 LLM 看的是碎片，還是病程結構」

🏥 住院病歷範例（簡化版）
病人：王小明，65 歲

Day 1:
因肺炎入院，發燒、呼吸困難
診斷：社區型肺炎
給予抗生素 A

Day 3:
病人出現腎功能惡化
懷疑與抗生素 A 有關
停用抗生素 A，改用抗生素 B

Day 7:
症狀改善，腎功能回復
準備出院
一、標準 RAG（Vector Similarity）
🧠 思維模式
把病歷「切碎」

找「語意最像問題的段落」

交給 LLM 拼答案

1️⃣ 建立病歷 chunks（模擬）
documents = [
    "65歲男性因肺炎入院，發燒與呼吸困難",
    "診斷為社區型肺炎，給予抗生素A",
    "住院第三天腎功能惡化",
    "懷疑與抗生素A相關，改用抗生素B",
    "症狀改善，腎功能回復，準備出院"
]
2️⃣ 向量檢索（簡化模擬）
def vector_search(question, docs):
    # 實務中會用 embedding + FAISS
    return docs[:3]  # 假設找回最像的三段
3️⃣ 生成摘要
question = "請摘要本次住院的重點"
context = vector_search(question, documents)

summary = f"""
根據病歷內容：
{context}

本次住院與肺炎及其治療相關。
"""
print(summary)
❌ 標準 RAG 的問題（醫療場景）
❌ 不知道哪個是「主問題」

❌ 腎功能惡化只是「其中一段文字」

❌ 不知道「因果」：藥 → 腎衰竭

❌ 只是「拼段落」

📌 它看不到「病程結構」

二、GraphRAG（醫療事件 + 關係）
🧠 思維模式
病歷 → 醫療實體（Entity）

建立 因果 / 時間 / 主從關係

用「圖」來推理

1️⃣ 建立知識圖譜（簡化版）
patient_graph = {
    "Patient": "王小明",
    "AdmissionReason": "肺炎",
    "Diagnoses": [
        {"name": "社區型肺炎", "type": "Primary"},
        {"name": "急性腎功能惡化", "type": "Complication"}
    ],
    "Treatments": [
        {"drug": "抗生素A", "day": 1},
        {"drug": "抗生素B", "day": 3}
    ],
    "CausalRelations": [
        {"cause": "抗生素A", "effect": "腎功能惡化"}
    ],
    "Outcome": "症狀改善，準備出院"
}
2️⃣ Graph Query（關鍵差異）
def summarize_hospitalization(graph):
    primary_dx = graph["Diagnoses"][0]["name"]
    complication = graph["Diagnoses"][1]["name"]
    cause = graph["CausalRelations"][0]

    return f"""
本次住院主因為{primary_dx}。
治療期間使用{cause['cause']}後出現{complication}，
經停藥並調整治療後病情改善，
病人狀況穩定，安排出院。
"""
print(summarize_hospitalization(patient_graph))
✅ GraphRAG 的優勢（醫師會點頭）
✅ 明確 主診斷

✅ 清楚 併發症

✅ 有 因果關係

✅ 有 治療決策理由

✅ 是「住院故事」，不是拼字

三、核心差異一眼表（給技術評估用）
面向	標準 RAG	GraphRAG
資料型態	文字 chunks	醫療實體＋關係
推理能力	幾乎沒有	因果 / 時間
住院摘要品質	普通	接近醫師
醫療合理性	不穩定	高
適合用在	查詢	病程摘要
四、HIS IT 的「關鍵認知」
住院病歷摘要不是 NLP 問題，而是「臨床推理問題」

👉 沒有 Graph，就沒有真正的摘要

五、實戰建議（醫療系統）
最佳落地架構
EMR / FHIR
   ↓
病歷解析（NER / Rule）
   ↓
醫療 Graph（診斷、處置、事件）
   ↓
GraphRAG（摘要主軸）
   + RAG（補細節）
   ↓
LLM 生成住院摘要
如果你願意，我可以下一步直接幫你：

🧬 設計「住院病歷 Graph Schema（FHIR 對應）」

📘 提供「真實 HIS 病歷 → GraphRAG pipeline」

🧪 PoC 程式（Python + Neo4j / NetworkX）

🏥 醫院用「住院摘要 Prompt + 驗證規則」

你想繼續深化在哪一層？
👉 架構設計 / 實際可跑 PoC / 醫療合規設計

你說：
架構設計
ChatGPT 說：
很好，既然你選的是**「架構設計」，我會用醫療 HIS IT 架構師**能直接拿去畫圖、寫規格、做 PoC 的方式來說明。
目標很清楚：

🎯 打造一個「可解釋、可驗證、可擴充」的住院病歷摘要 GraphRAG 架構

以下內容不是學術架構圖，而是醫院能落地的系統設計。

一、整體架構總覽（HIS / EMR 導向）
┌──────────────────────────┐
│   HIS / EMR / LIS / RIS   │
│  (住院病歷 / 醫囑 / 用藥) │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   資料抽取與正規化層     │
│  • FHIR Adapter          │
│  • 非結構病歷解析 NLP    │
│  • 醫療代碼對應(ICD/ATC) │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   醫療知識建模層         │
│  • Entity Extraction     │
│  • Relation Inference    │
│  • Time-line Builder     │
└───────────┬──────────────┘
            │
     ┌──────┴─────────┐
     ▼                ▼
┌─────────────┐  ┌────────────────┐
│ Knowledge   │  │ Vector Store   │
│ Graph (KG)  │  │ (RAG Chunk)    │
│ Neo4j       │  │ FAISS / PGV    │
└─────┬───────┘  └───────┬────────┘
      │                  │
      └──────┬───────────┘
             ▼
┌──────────────────────────┐
│   GraphRAG Orchestrator  │
│  • Graph Query           │
│  • Context Assembly      │
│  • Prompt Controller     │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│     LLM (私有化)         │
│  • 摘要生成              │
│  • 解釋與引用            │
└───────────┬──────────────┘
            │
            ▼
┌──────────────────────────┐
│   驗證與治理層           │
│  • Clinical Rule Check   │
│  • Hallucination Guard   │
│  • Audit Log             │
└──────────────────────────┘
二、每一層「為什麼存在」（這是重點）
1️⃣ 資料抽取與正規化層（沒有這層，醫療一定翻車）
輸入資料來源
EMR 住院病歷（SOAP、Progress note）

醫囑（Order）

用藥（Medication）

檢驗（LIS）

影像報告（RIS）

關鍵設計
FHIR R4 為內部標準模型

ICD-10 / ATC / LOINC 正規化

非結構文字 → 結構化事件

📌 這層決定「醫療正確性上限」

2️⃣ 醫療知識建模層（GraphRAG 核心）
Entity（實體）
類型	範例
Patient	王小明
Diagnosis	肺炎
Medication	抗生素A
Event	腎功能惡化
Procedure	插管
Lab	Creatinine
Relation（關係）
CAUSES（藥物 → 副作用）

TREATED_BY

OCCURRED_ON

PRIMARY_DIAGNOSIS

FOLLOWED_BY

📌 這層讓 AI「理解病程」而非讀文字

3️⃣ Knowledge Graph（Neo4j）
為何不是關聯式 DB？
病程是「網狀＋時間軸」

關係查詢是核心需求

範例查詢（Cypher）
MATCH (p:Patient)-[:HAS_DIAGNOSIS]->(d:Diagnosis {type:"Primary"})
MATCH (d)<-[:CAUSES]-(m:Medication)
RETURN p, d, m
📌 這不是搜尋，是推理

4️⃣ Vector Store（保留 RAG 的價值）
Graph 不取代 RAG，而是補強

存什麼？
Progress note 原文

出院病摘全文

手術記錄細節

用途
Graph 找「主軸」

RAG 補「細節證據」

5️⃣ GraphRAG Orchestrator（關鍵中樞）
核心責任
先問 Graph：

主診斷？

併發症？

治療轉折？

再補 RAG：

找支持文字

組 Prompt（有結構）

{
  "primary_diagnosis": "...",
  "complications": [...],
  "treatment_changes": [...],
  "evidence": [...]
}
📌 LLM 不再自由發揮，而是「被約束生成」

6️⃣ LLM 層（一定要私有化）
建議
Azure OpenAI (Private)

on-prem LLM（LLaMA / Qwen）

不直連公網

Prompt 特性
Template 化

禁止新增未提供事實

強制引用 Graph / Evidence ID

7️⃣ 驗證與治理層（醫療 AI 成敗關鍵）
必備
臨床規則檢查（Rule Engine）

不合理摘要攔截

全流程 Audit Log

📌 這層是醫院法遵與風控的底線

三、給 HIS IT 的落地建議（務實）
Phase 1（2–4 週）
FHIR Adapter

標準 RAG

人工檢查摘要

Phase 2（1–2 月）
診斷 / 用藥 Graph

住院摘要 GraphRAG

Phase 3（進階）
DRG / 品質指標

醫療解釋型 AI

四、你現在可以直接拿走的成果
✔ 一套可畫架構圖的藍本
✔ 可寫標案 / PoC / 規格書
✔ 對醫師、法遵、IT 都說得通

下一步我可以直接幫你做哪一個？
1️⃣ Neo4j 醫療 Graph Schema（FHIR 對照）
2️⃣ GraphRAG Orchestrator Python PoC
3️⃣ 醫療摘要 Prompt & 防幻覺規範
4️⃣ 醫院簡報版（5–7 頁）

你只要選一個，我直接往「可交付」層級下去。

你說：
1
ChatGPT 說：
非常好，選 ① Neo4j 醫療 Graph Schema（FHIR 對照） 是正確且專業的第一步。
下面我會直接給你一套 「醫院可落地、HIS IT 能實作、GraphRAG 可直接用」 的設計，不講空泛概念。

🏥 住院病歷 Graph Schema（FHIR 對照版）
🎯 目標
把 EMR / FHIR 資料 →「可推理的住院病程圖」
支援：

住院摘要

併發症分析

治療轉折解釋

GraphRAG 查詢

一、設計原則（醫療一定要守）
FHIR 對齊（不是自己發明）

主診斷 / 併發症要能分

時間軸是第一級公民

因果關係要可追溯

Graph ≠ 全病歷，只存「推理關鍵點」

二、核心節點（Node Types）
1️⃣ Patient（FHIR: Patient）
(:Patient)
- patient_id
- gender
- birth_date
📌 一切關係的起點

2️⃣ Encounter（FHIR: Encounter）
(:Encounter)
- encounter_id
- type = "Inpatient"
- admit_date
- discharge_date
📌 非常重要：
👉 Graph 推理一定要以「一次住院」為單位

3️⃣ Diagnosis（FHIR: Condition）
(:Diagnosis)
- diagnosis_id
- icd10
- display
- role = Primary | Secondary | Complication
📌 role 是 GraphRAG 成敗關鍵

4️⃣ Medication（FHIR: MedicationRequest）
(:Medication)
- drug_code (ATC)
- drug_name
5️⃣ ClinicalEvent（自定義，FHIR 組合）
(:ClinicalEvent)
- event_id
- type = LabAbnormal | Infection | AKI | ICUTransfer
- description
- event_date
📌 併發症、轉折點一定是 Event

6️⃣ Procedure（FHIR: Procedure）
(:Procedure)
- procedure_code
- name
- date
7️⃣ LabResult（FHIR: Observation）
(:LabResult)
- loinc
- test_name
- value
- unit
- abnormal = true/false
- date
三、核心關係（Relation Types）
🧠 住院結構
(Patient)-[:HAS_ENCOUNTER]->(Encounter)
(Encounter)-[:HAS_DIAGNOSIS]->(Diagnosis)
🧠 診斷與處置
(Diagnosis)-[:TREATED_BY]->(Medication)
(Diagnosis)-[:REQUIRES]->(Procedure)
🧠 併發症與因果（GraphRAG 關鍵）
(Medication)-[:CAUSES]->(ClinicalEvent)
(ClinicalEvent)-[:RESULTS_IN]->(Diagnosis {role:"Complication"})
👉 這一條，讓 AI 能說出：

「因使用 X 藥物，導致 Y 併發症」

🧠 時間軸（一定要）
(ClinicalEvent)-[:OCCURRED_ON]->(Encounter)
(ClinicalEvent)-[:FOLLOWED_BY]->(ClinicalEvent)
四、Neo4j Schema 實例（可直接用）
1️⃣ 建立節點
CREATE (p:Patient {patient_id:"P001"})
CREATE (e:Encounter {
  encounter_id:"E001",
  type:"Inpatient",
  admit_date:"2024-01-01",
  discharge_date:"2024-01-07"
})
CREATE (d1:Diagnosis {
  diagnosis_id:"D001",
  icd10:"J18.9",
  display:"Community-acquired pneumonia",
  role:"Primary"
})
CREATE (m:Medication {
  drug_code:"J01CA04",
  drug_name:"Antibiotic A"
})
CREATE (ev:ClinicalEvent {
  event_id:"EV001",
  type:"AKI",
  description:"Acute kidney injury",
  event_date:"2024-01-03"
})
2️⃣ 建立關係
MATCH (p:Patient {patient_id:"P001"}),
      (e:Encounter {encounter_id:"E001"})
CREATE (p)-[:HAS_ENCOUNTER]->(e)

MATCH (e),(d1)
CREATE (e)-[:HAS_DIAGNOSIS]->(d1)

MATCH (d1),(m)
CREATE (d1)-[:TREATED_BY]->(m)

MATCH (m),(ev)
CREATE (m)-[:CAUSES]->(ev)
五、GraphRAG 查詢範例（關鍵）
🩺 1️⃣ 查主診斷（摘要主軸）
MATCH (e:Encounter)-[:HAS_DIAGNOSIS]->(d:Diagnosis {role:"Primary"})
WHERE e.encounter_id = $encounter_id
RETURN d
⚠️ 2️⃣ 查併發症與原因
MATCH (m:Medication)-[:CAUSES]->(ev:ClinicalEvent)
MATCH (ev)-[:RESULTS_IN]->(d:Diagnosis {role:"Complication"})
RETURN m, ev, d
🧠 3️⃣ 組 Graph Context 給 LLM
{
  "primary_diagnosis": "Community-acquired pneumonia",
  "complications": [
    {
      "name": "Acute kidney injury",
      "cause": "Antibiotic A",
      "date": "2024-01-03"
    }
  ]
}
📌 LLM 只負責「表達」，不是「推理」

六、這套 Schema 能解決什麼（務實）
✔ 自動住院病歷摘要
✔ 為什麼換藥？（可解釋）
✔ DRG / 品質指標解釋
✔ 防幻覺（因為有來源）
✔ GraphRAG 可擴充

七、下一步（你可以選）
2️⃣ GraphRAG Orchestrator（Python，Neo4j + RAG）
3️⃣ 醫療住院摘要 Prompt（可交付醫師審）
4️⃣ FHIR → Graph Mapping Spec（寫標案用）

👉 你直接選編號，我往「可跑、可交付」層級繼續。

你說：
2 GraphRAG Orchestrator
ChatGPT 說：
太好了，② GraphRAG Orchestrator 正是整個系統「讓 Graph 真的變成 AI 推理引擎」的核心。
我會用HIS IT 可實作、Python 可直接 PoC、未來可上線的層級來說明。

🧠 GraphRAG Orchestrator（醫療住院摘要）
🎯 角色定位
GraphRAG Orchestrator =「臨床推理控制器」

決定 先問誰（Graph or Vector）

決定 哪些資料能給 LLM

防止 LLM 自行幻想病程

一、Orchestrator 的責任分工
使用者請求
   │
   ▼
GraphRAG Orchestrator
 ├─ Graph Query（病程骨架）
 ├─ Clinical Logic（醫療判斷）
 ├─ RAG Retrieval（補充證據）
 ├─ Prompt Assembly（結構化上下文）
 ├─ Guardrail & Validation
   │
   ▼
LLM
📌 LLM 永遠不直接碰資料庫

二、模組化架構（可維護）
graphrag/
├─ orchestrator.py
├─ graph/
│   ├─ diagnosis.py
│   ├─ complication.py
│   └─ timeline.py
├─ rag/
│   └─ retriever.py
├─ prompt/
│   └─ inpatient_summary.jinja
├─ validator/
│   └─ clinical_rules.py
三、Graph Query Layer（Neo4j）
1️⃣ 取得主診斷
def get_primary_diagnosis(tx, encounter_id):
    query = """
    MATCH (e:Encounter)-[:HAS_DIAGNOSIS]->(d:Diagnosis {role:"Primary"})
    WHERE e.encounter_id = $encounter_id
    RETURN d.display AS diagnosis
    """
    return tx.run(query, encounter_id=encounter_id).single()
2️⃣ 取得併發症 + 原因
def get_complications(tx, encounter_id):
    query = """
    MATCH (e:Encounter {encounter_id:$encounter_id})
          -[:HAS_DIAGNOSIS]->(:Diagnosis {role:"Primary"})
          -[:TREATED_BY]->(m:Medication)
          -[:CAUSES]->(ev:ClinicalEvent)
    RETURN ev.description AS complication,
           m.drug_name AS cause,
           ev.event_date AS date
    """
    return [r.data() for r in tx.run(query, encounter_id=encounter_id)]
3️⃣ 治療轉折（為何換藥）
def get_treatment_changes(tx, encounter_id):
    query = """
    MATCH (e:Encounter {encounter_id:$encounter_id})
          -[:HAS_DIAGNOSIS]->(d:Diagnosis)
          -[:TREATED_BY]->(m:Medication)
    RETURN d.display, m.drug_name
    """
    return [r.data() for r in tx.run(query, encounter_id=encounter_id)]
四、RAG Layer（補文字證據）
def retrieve_evidence(encounter_id, query):
    # 實務用 FAISS / PGVector
    return [
        "Day 3: Patient developed acute kidney injury, suspected drug-related.",
        "Antibiotic A was discontinued and switched to B."
    ]
📌 RAG 只能補「證據文字」，不能定義病程

五、Prompt Assembly（關鍵）
Jinja Template（摘要結構已被約束）
住院摘要：

主診斷：
{{ primary_diagnosis }}

併發症與處理：
{% for c in complications %}
- {{ c.complication }}，原因：{{ c.cause }}（{{ c.date }}）
{% endfor %}

治療轉折：
{% for t in treatments %}
- {{ t.drug_name }}
{% endfor %}

請僅根據上述資訊撰寫摘要，不得新增未提供的醫療事實。
六、Orchestrator 主流程（Python）
def generate_inpatient_summary(encounter_id, graph_driver):
    with graph_driver.session() as session:
        primary = session.read_transaction(
            get_primary_diagnosis, encounter_id
        )
        complications = session.read_transaction(
            get_complications, encounter_id
        )
        treatments = session.read_transaction(
            get_treatment_changes, encounter_id
        )

    evidence = retrieve_evidence(encounter_id, "inpatient course")

    context = {
        "primary_diagnosis": primary["diagnosis"],
        "complications": complications,
        "treatments": treatments,
        "evidence": evidence
    }

    prompt = render_prompt("inpatient_summary.jinja", context)
    return call_llm(prompt)
七、Clinical Guardrail（防醫療幻覺）
def validate_summary(summary, context):
    if context["primary_diagnosis"] not in summary:
        raise ValueError("主診斷缺失")

    for c in context["complications"]:
        if c["complication"] not in summary:
            raise ValueError("併發症遺漏")
📌 這層讓 AI「不敢亂寫」

八、為什麼這套 Orchestrator 很醫療
特性	說明
Graph-first	病程由 Graph 定義
Explainable	每句話都有來源
Audit-ready	可追溯 Query
可擴充	可加 DRG / 品質指標
合規	不暴露 PHI 給 LLM
九、真實落地建議
Phase 1
Neo4j + Python Driver

不接真 LLM，先輸出 context JSON

Phase 2
接私有 LLM

加 Prompt & Rule

Phase 3
醫師 Review UI

Feedback 回寫 Graph

🔜 下一步你可以選
3️⃣ 醫療住院摘要 Prompt（臨床可審）
4️⃣ FHIR → Graph Mapping Spec（寫標案用）

👉 你選一個，我直接幫你做到「可交付文件等級」。

你說：
3
ChatGPT 說：
完美，我們進入 ③ 醫療住院摘要 Prompt（臨床可審） 層級，這是 GraphRAG 與 LLM 結合的最後一環，也是醫師可以直接審核的部分。
我會給你 可直接落地、結構化、法遵友好、HIS 可用 的 Prompt 設計。

🏥 GraphRAG LLM 住院摘要 Prompt 設計（臨床可審）
🎯 目標

LLM 只根據 GraphRAG 提供的資訊生成摘要

防止醫療幻覺

結構化，方便審核與存檔

可直接用於住院病歷摘要、出院摘要生成

一、Prompt 結構（模版化）
你是一位專業臨床醫師助手。
請根據以下提供的病歷圖譜資訊生成住院摘要：
- 主診斷 (Primary Diagnosis)
- 併發症及原因 (Complications & Cause)
- 治療轉折 (Treatment Changes)
- 相關證據文字 (Evidence)

要求：
1. 只使用提供的資訊，不得新增任何未提供的醫療事實。
2. 摘要需包含病程主要事件、併發症與治療調整。
3. 每個併發症需標明原因與發生日期。
4. 條列式或段落式皆可，但需結構清晰。
5. 摘要需可供醫師快速審核與簽核。

提供資訊：
主診斷: {{ primary_diagnosis }}

併發症:
{% for c in complications %}
- {{ c.complication }}，原因：{{ c.cause }}（{{ c.date }}）
{% endfor %}

治療轉折:
{% for t in treatments %}
- {{ t.drug_name }}
{% endfor %}

證據:
{% for e in evidence %}
- {{ e }}
{% endfor %}

請生成住院摘要：
二、Python 渲染範例
from jinja2 import Template

def render_prompt(template_str, context):
    template = Template(template_str)
    return template.render(**context)

# 範例 context
context = {
    "primary_diagnosis": "Community-acquired pneumonia",
    "complications": [
        {"complication":"Acute kidney injury", "cause":"Antibiotic A", "date":"2024-01-03"}
    ],
    "treatments":[{"drug_name":"Antibiotic A"}, {"drug_name":"Antibiotic B"}],
    "evidence":[
        "Day 3: Patient developed acute kidney injury, suspected drug-related.",
        "Antibiotic A was discontinued and switched to B."
    ]
}

prompt_str = """<上面 Jinja 模板字串>"""
final_prompt = render_prompt(prompt_str, context)
print(final_prompt)
三、示例生成結果（LLM 輸出範例）
住院摘要：

主診斷：
Community-acquired pneumonia

併發症與處理：
- Acute kidney injury，原因：Antibiotic A（2024-01-03）

治療轉折：
- Antibiotic A
- Antibiotic B

病程摘要：
病人因 Community-acquired pneumonia 入院，住院期間使用 Antibiotic A，於 Day 3 出現 Acute kidney injury，懷疑與藥物相關，因此停用 Antibiotic A 並改用 Antibiotic B，病情後續改善。摘要基於提供的證據生成，可供醫師審核。
四、設計重點（臨床可審）
特性	說明
GraphRAG 作為事實來源	確保 LLM 摘要只使用結構化事實
證據引用	每段文字可對應原始病歷或 Lab Result
條列與段落混合	條列清楚事件、段落敘述主軸
防幻覺	LLM 被限制只能依 context 生成，不可自由編造
臨床可審	醫師可快速核對主診斷、併發症、治療轉折
五、進階建議
加入時間軸排序：GraphRAG 提供事件順序，LLM 根據事件時間生成更精準摘要。

加入臨床規則檢查：生成後自動比對 Rule Engine，確保摘要合乎醫療邏輯。

多語系支援：HIS 可選中 / 英文版本，Prompt 只需替換模板語言。

自動生成 Review Log：每條摘要都可回寫 Neo4j 或 HIS，方便審核追蹤。

如果你願意，我可以幫你做下一步 「完整 PoC Pipeline：FHIR → Graph → GraphRAG Orchestrator → LLM 摘要 → 驗證」，直接用 Python + Neo4j + 模擬 LLM 生成一條可跑的完整範例。

你想我直接幫你做這個整合 PoC 嗎？

你說：
Yes
ChatGPT 說：
太好了！我們來做 完整 PoC Pipeline，把 FHIR → Graph → GraphRAG Orchestrator → LLM 摘要 → 驗證 一條龍整合成 Python 可跑範例，模擬醫療住院病歷摘要生成。

這個 PoC 完全可落地，HIS IT 可以直接改成連接真實 EMR / Neo4j / 私有 LLM。

1️⃣ 需求與目標
需求場景：

患者入院病歷（簡化版）

生成「住院摘要」

LLM 摘要 只使用 GraphRAG 提供的事實

確保臨床可審、可追溯

PoC 功能：

模擬 FHIR 病歷資料

將資料建 Graph（Neo4j 模擬）

GraphRAG Orchestrator 查詢 Graph + RAG 補文字

組 Prompt → 模擬 LLM 生成摘要

驗證摘要完整性（主診斷、併發症）

2️⃣ Python PoC 代碼
from jinja2 import Template

# -------------------------
# Step 1: 模擬 FHIR 病歷
# -------------------------
fhir_data = {
    "patient": {"id":"P001","name":"王小明","age":65},
    "encounter": {"id":"E001","type":"Inpatient","admit_date":"2024-01-01","discharge_date":"2024-01-07"},
    "diagnoses":[
        {"id":"D001","name":"Community-acquired pneumonia","role":"Primary"},
        {"id":"D002","name":"Acute kidney injury","role":"Complication"}
    ],
    "medications":[
        {"drug_name":"Antibiotic A","start_day":1,"end_day":3},
        {"drug_name":"Antibiotic B","start_day":3,"end_day":7}
    ],
    "events":[
        {"id":"EV001","type":"AKI","description":"Acute kidney injury","date":"2024-01-03","cause":"Antibiotic A"}
    ],
    "evidence":[
        "Day 3: Patient developed acute kidney injury, suspected drug-related.",
        "Antibiotic A was discontinued and switched to B."
    ]
}

# -------------------------
# Step 2: 建立 GraphRAG Context
# -------------------------
graph_context = {
    "primary_diagnosis": fhir_data["diagnoses"][0]["name"],
    "complications": [
        {"complication": fhir_data["events"][0]["description"],
         "cause": fhir_data["events"][0]["cause"],
         "date": fhir_data["events"][0]["date"]}
    ],
    "treatments": fhir_data["medications"],
    "evidence": fhir_data["evidence"]
}

# -------------------------
# Step 3: Prompt Template
# -------------------------
prompt_template = """
住院摘要：

主診斷：
{{ primary_diagnosis }}

併發症與處理：
{% for c in complications %}
- {{ c.complication }}，原因：{{ c.cause }}（{{ c.date }}）
{% endfor %}

治療轉折：
{% for t in treatments %}
- {{ t.drug_name }}
{% endfor %}

證據:
{% for e in evidence %}
- {{ e }}
{% endfor %}

請生成住院摘要：
"""

def render_prompt(template_str, context):
    template = Template(template_str)
    return template.render(**context)

final_prompt = render_prompt(prompt_template, graph_context)

# -------------------------
# Step 4: 模擬 LLM 生成摘要
# -------------------------
def call_llm(prompt):
    # 這裡模擬 LLM，實務可改成 OpenAI/私有模型呼叫
    summary = f"""
病人因 {graph_context['primary_diagnosis']} 入院，住院期間使用 {graph_context['treatments'][0]['drug_name']}，
於 {graph_context['complications'][0]['date']} 出現 {graph_context['complications'][0]['complication']}，
懷疑與藥物 {graph_context['complications'][0]['cause']} 相關，因此停用 {graph_context['treatments'][0]['drug_name']} 並改用 {graph_context['treatments'][1]['drug_name']}，
病情後續改善。摘要基於提供的證據生成，可供醫師審核。
"""
    return summary.strip()

summary = call_llm(final_prompt)

# -------------------------
# Step 5: Clinical Guardrail 驗證
# -------------------------
def validate_summary(summary, context):
    errors = []
    if context["primary_diagnosis"] not in summary:
        errors.append("主診斷缺失")
    for c in context["complications"]:
        if c["complication"] not in summary:
            errors.append(f"併發症 {c['complication']} 遺漏")
    return errors

errors = validate_summary(summary, graph_context)

# -------------------------
# Step 6: 輸出結果
# -------------------------
print("===== Prompt =====")
print(final_prompt)
print("\n===== LLM 摘要 =====")
print(summary)
print("\n===== 驗證結果 =====")
print(errors if errors else "摘要完整")
3️⃣ PoC 流程說明
步驟	功能
1️⃣ FHIR 病歷	模擬 EMR 資料，包含診斷、藥物、事件、證據
2️⃣ GraphRAG Context	從 Graph 取得主診斷、併發症、治療轉折
3️⃣ Prompt Template	結構化模板，約束 LLM 生成
4️⃣ call_llm	模擬 LLM 摘要生成（實務可換 OpenAI 或私有模型）
5️⃣ Guardrail	確保主診斷、併發症完整，不漏關鍵資訊
6️⃣ Output	提供 Prompt、生成摘要、驗證結果
4️⃣ PoC 執行效果（示例輸出）
Prompt：

住院摘要：

主診斷：
Community-acquired pneumonia

併發症與處理：
- Acute kidney injury，原因：Antibiotic A（2024-01-03）

治療轉折：
- Antibiotic A
- Antibiotic B

證據:
- Day 3: Patient developed acute kidney injury, suspected drug-related.
- Antibiotic A was discontinued and switched to B.

請生成住院摘要：
LLM 摘要：

病人因 Community-acquired pneumonia 入院，住院期間使用 Antibiotic A，
於 2024-01-03 出現 Acute kidney injury，
懷疑與藥物 Antibiotic A 相關，因此停用 Antibiotic A 並改用 Antibiotic B，
病情後續改善。摘要基於提供的證據生成，可供醫師審核。
驗證結果：

摘要完整
✅ PoC 特性與優勢
完整流程：FHIR → Graph → GraphRAG → LLM → Guardrail

臨床可審：主診斷、併發症、治療轉折清楚

防幻覺：LLM 不得自由編造

可擴展：增加 DRG / 品質指標 / 多病人

HIS 可直接落地：Python + Neo4j + 私有 LLM

如果你需要，我可以下一步幫你做 「連接 Neo4j + 私有 LLM，完整多病歷批次摘要生成的可跑 PoC」，直接把多個病歷自動生成摘要，並輸出 Excel / PDF 結構化報告，醫師可直接審核。

你希望我直接幫你做這個嗎？

你說：
Yes , pdf 格式
ChatGPT 說：
完美，我們來做 完整多病歷批次摘要生成 PoC + PDF 輸出。
目標是 HIS IT 可直接使用、醫師可審核 的格式化報告。

1️⃣ 方案概覽
流程：

FHIR 病歷（多患者） → GraphRAG Orchestrator → LLM 摘要生成 → PDF 報告
特點：

支援多病歷批次

GraphRAG 約束 LLM 不幻想

PDF 結構化報告（主診斷、併發症、治療轉折、證據）

可直接交給醫師審核

2️⃣ Python PoC 代碼（含 PDF 輸出）
我們使用 jinja2 生成文本內容，reportlab 或 fpdf 生成 PDF（這裡用 fpdf 簡單示範）

from jinja2 import Template
from fpdf import FPDF

# -------------------------
# Step 1: 模擬多患者 FHIR 病歷
# -------------------------
patients_data = [
    {
        "patient_id": "P001",
        "name": "王小明",
        "age": 65,
        "diagnoses":[
            {"name":"Community-acquired pneumonia","role":"Primary"},
            {"name":"Acute kidney injury","role":"Complication"}
        ],
        "medications":[
            {"drug_name":"Antibiotic A"},
            {"drug_name":"Antibiotic B"}
        ],
        "events":[
            {"description":"Acute kidney injury","cause":"Antibiotic A","date":"2024-01-03"}
        ],
        "evidence":[
            "Day 3: Patient developed acute kidney injury, suspected drug-related.",
            "Antibiotic A was discontinued and switched to B."
        ]
    },
    {
        "patient_id": "P002",
        "name": "李小華",
        "age": 72,
        "diagnoses":[
            {"name":"Heart Failure","role":"Primary"}
        ],
        "medications":[
            {"drug_name":"Diuretic A"}
        ],
        "events":[],
        "evidence":[
            "Patient admitted with dyspnea, started on Diuretic A."
        ]
    }
]

# -------------------------
# Step 2: Prompt Template
# -------------------------
prompt_template = """
住院摘要：

患者: {{ patient_name }}，年齡 {{ age }}

主診斷：
{{ primary_diagnosis }}

併發症與處理：
{% if complications %}
{% for c in complications %}
- {{ c.description }}，原因：{{ c.cause }}（{{ c.date }}）
{% endfor %}
{% else %}
- 無
{% endif %}

治療轉折：
{% for t in treatments %}
- {{ t.drug_name }}
{% endfor %}

證據:
{% for e in evidence %}
- {{ e }}
{% endfor %}

請生成住院摘要：
"""

def render_prompt(template_str, context):
    template = Template(template_str)
    return template.render(**context)

# -------------------------
# Step 3: 模擬 LLM 生成摘要
# -------------------------
def call_llm(context):
    # 這裡簡單模擬 LLM 輸出
    primary = context['primary_diagnosis']
    treatments = context['treatments']
    if context['complications']:
        comp = context['complications'][0]
        comp_text = f"於 {comp['date']} 出現 {comp['description']}，懷疑與藥物 {comp['cause']} 相關"
    else:
        comp_text = "住院期間無併發症"
    summary = f"病人因 {primary} 入院，{comp_text}，治療使用 " + ", ".join([t['drug_name'] for t in treatments]) + "，病情後續改善。摘要基於提供的證據生成，可供醫師審核。"
    return summary

# -------------------------
# Step 4: 生成多患者摘要
# -------------------------
summaries = []
for p in patients_data:
    context = {
        "patient_name": p['name'],
        "age": p['age'],
        "primary_diagnosis": p['diagnoses'][0]['name'],
        "complications": [{"description": e['description'], "cause": e['cause'], "date": e['date']} for e in p['events']],
        "treatments": p['medications'],
        "evidence": p['evidence']
    }
    prompt_text = render_prompt(prompt_template, context)
    summary_text = call_llm(context)
    summaries.append({
        "patient_name": p['name'],
        "summary": summary_text,
        "prompt": prompt_text
    })

# -------------------------
# Step 5: 生成 PDF
# -------------------------
pdf = FPDF()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", size=12)

for s in summaries:
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"患者: {s['patient_name']} - 住院摘要", ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, s['summary'])
    pdf.ln(5)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 6, "=== Prompt Context ===\n" + s['prompt'])

# 儲存 PDF
pdf.output("inpatient_summaries.pdf")
print("PDF 已生成: inpatient_summaries.pdf")
3️⃣ PoC 功能與特性
功能	說明
批次摘要	多患者病歷一次生成
GraphRAG 約束	LLM 只使用提供的 Graph + RAG context
Prompt 可審	PDF 中保留 Prompt 方便醫師追溯
結構化報告	包含主診斷、併發症、治療轉折、證據
可落地	Python + fpdf，可接真 Neo4j + 私有 LLM
4️⃣ PDF 輸出示例
每頁內容：

患者: 王小明 - 住院摘要

病人因 Community-acquired pneumonia 入院，於 2024-01-03 出現 Acute kidney injury，懷疑與藥物 Antibiotic A 相關，治療使用 Antibiotic A, Antibiotic B，病情後續改善。摘要基於提供的證據生成，可供醫師審核。

=== Prompt Context ===
住院摘要：

患者: 王小明，年齡 65
...
每位患者各佔一頁，醫師可以快速審核摘要並對照 Prompt context。

如果你願意，我可以幫你做 下一步進階版：

連接 真實 Neo4j + 私有 LLM

可自動從 HIS FHIR 資料抓取多病歷

PDF 報告包含 時間軸圖、併發症高亮、DRG 代碼

這樣可以做成 HIS 可落地自動化住院摘要系統。

你想我直接做這個嗎？

你說：
Yes
ChatGPT 說：
太好了，我們可以做 HIS 可落地自動化住院摘要系統 PoC（Neo4j + 私有 LLM + PDF）。我給你一個完整設計與 Python 實作方案，方便直接落地。

1️⃣ 系統架構總覽
FHIR / EMR (HIS)
        │
        ▼
   ETL / Data Normalization
        │
        ▼
     Neo4j Graph
        │
        ▼
GraphRAG Orchestrator
  ├─ Graph Query (主診斷、併發症、治療)
  ├─ RAG Retrieval (補充文字證據)
  ├─ Prompt Assembly
  ├─ Clinical Guardrail
        │
        ▼
     私有化 LLM
        │
        ▼
   PDF Report Generator
2️⃣ Python PoC 設計
重點：

從 Neo4j 查 GraphRAG context

模擬私有 LLM 生成摘要

批次多病歷生成 PDF

可加上臨床 Guardrail 驗證

2.1 安裝依賴
pip install neo4j fpdf jinja2
2.2 連接 Neo4j 並抓取 Graph Context
from neo4j import GraphDatabase

class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def get_patient_context(self, patient_id):
        with self.driver.session() as session:
            primary = session.read_transaction(self.get_primary_diagnosis, patient_id)
            complications = session.read_transaction(self.get_complications, patient_id)
            treatments = session.read_transaction(self.get_treatments, patient_id)
            evidence = session.read_transaction(self.get_evidence, patient_id)
        return {
            "primary_diagnosis": primary,
            "complications": complications,
            "treatments": treatments,
            "evidence": evidence
        }

    @staticmethod
    def get_primary_diagnosis(tx, patient_id):
        q = """
        MATCH (p:Patient {patient_id:$pid})-[:HAS_ENCOUNTER]->(:Encounter)
              -[:HAS_DIAGNOSIS]->(d:Diagnosis {role:'Primary'})
        RETURN d.display AS diagnosis
        """
        result = tx.run(q, pid=patient_id).single()
        return result["diagnosis"] if result else "Unknown"

    @staticmethod
    def get_complications(tx, patient_id):
        q = """
        MATCH (p:Patient {patient_id:$pid})-[:HAS_ENCOUNTER]->(:Encounter)
              -[:HAS_DIAGNOSIS]->(:Diagnosis {role:'Primary'})
              -[:TREATED_BY]->(m:Medication)-[:CAUSES]->(ev:ClinicalEvent)
        RETURN ev.description AS description, m.drug_name AS cause, ev.event_date AS date
        """
        return [r.data() for r in tx.run(q, pid=patient_id)]

    @staticmethod
    def get_treatments(tx, patient_id):
        q = """
        MATCH (p:Patient {patient_id:$pid})-[:HAS_ENCOUNTER]->(:Encounter)
              -[:HAS_DIAGNOSIS]->(d:Diagnosis)
              -[:TREATED_BY]->(m:Medication)
        RETURN m.drug_name AS drug_name
        """
        return [r.data() for r in tx.run(q, pid=patient_id)]

    @staticmethod
    def get_evidence(tx, patient_id):
        q = """
        MATCH (p:Patient {patient_id:$pid})-[:HAS_ENCOUNTER]->(:Encounter)-[:HAS_NOTE]->(n:Note)
        RETURN n.text AS note
        """
        return [r["note"] for r in tx.run(q, pid=patient_id)]
2.3 GraphRAG Orchestrator + Prompt Template
from jinja2 import Template

prompt_template = """
住院摘要：

主診斷：
{{ primary_diagnosis }}

併發症與處理：
{% if complications %}
{% for c in complications %}
- {{ c.description }}，原因：{{ c.cause }}（{{ c.date }}）
{% endfor %}
{% else %}
- 無
{% endif %}

治療轉折：
{% for t in treatments %}
- {{ t.drug_name }}
{% endfor %}

證據:
{% for e in evidence %}
- {{ e }}
{% endfor %}

請生成住院摘要：
"""

def render_prompt(context):
    template = Template(prompt_template)
    return template.render(**context)
2.4 模擬 LLM（可換私有 LLM API）
def call_llm(context):
    primary = context["primary_diagnosis"]
    treatments = ", ".join([t["drug_name"] for t in context["treatments"]])
    if context["complications"]:
        comp = context["complications"][0]
        comp_text = f"於 {comp['date']} 出現 {comp['description']}，懷疑與藥物 {comp['cause']} 相關"
    else:
        comp_text = "住院期間無併發症"
    summary = f"病人因 {primary} 入院，{comp_text}，治療使用 {treatments}，病情後續改善。摘要基於提供的證據生成，可供醫師審核。"
    return summary
2.5 PDF 報告生成
from fpdf import FPDF

def generate_pdf(summaries, output_file="inpatient_summaries.pdf"):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for s in summaries:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"患者: {s['patient_name']} - 住院摘要", ln=True)
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 8, s['summary'])
        pdf.ln(5)
        pdf.set_font("Arial", "I", 10)
        pdf.multi_cell(0, 6, "=== Prompt Context ===\n" + s['prompt'])

    pdf.output(output_file)
    print(f"PDF 已生成: {output_file}")
2.6 批次摘要生成流程
# 假設多個患者 ID
patient_ids = ["P001", "P002"]

neo_handler = Neo4jHandler(uri="bolt://localhost:7687", user="neo4j", password="password")
summaries = []

for pid in patient_ids:
    context = neo_handler.get_patient_context(pid)
    prompt_text = render_prompt(context)
    summary_text = call_llm(context)
    summaries.append({
        "patient_name": pid,
        "summary": summary_text,
        "prompt": prompt_text
    })

neo_handler.close()

# 生成 PDF
generate_pdf(summaries)
3️⃣ PoC 特性
功能	說明
多病歷批次	可一次生成多個患者住院摘要
GraphRAG 驅動	LLM 只使用 Graph + RAG context 生成摘要
臨床可審	PDF 包 Prompt 與生成摘要，醫師可追溯
可換私有 LLM	模擬 LLM 可替換為院內私有模型
落地 HIS	Python + Neo4j + PDF，可直接整合 HIS FHIR
這樣就完成 HIS 可落地 GraphRAG + LLM 自動住院摘要 PDF 系統 PoC。

我可以幫你下一步再加上 時間軸可視化 + 併發症高亮 + DRG 代碼整合，生成更完整臨床報告 PDF，醫師審核更直觀。

你希望我直接加這個嗎？




未選擇任何檔案未選擇任何檔案
ChatGPT 可能會出錯。請查核重要資訊。
