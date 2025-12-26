# 問答集 (QA)

本目錄包含專案相關的常見問答，方便快速查找問題和解決方案。

## 文檔索引

### 1. [Stub 相關問答](stub_qa.md)
- 什麼是 Stub？
- 為什麼使用 Stub？
- 專案中哪些服務是 Stub？
- Stub 和 Mock 的區別
- 何時替換 Stub？

### 2. [JSON 解析錯誤問答](json_parse_error_qa.md)
- 為什麼會出現 JSON 解析錯誤？
- 錯誤會影響系統運行嗎？
- 如何修復錯誤？
- 如何調試 JSON 解析問題？

### 3. [一般問答](general_qa.md)
- 什麼是 GraphRAG？
- 專案架構是什麼？
- 如何開始使用？
- 如何檢查系統狀態？
- 常見問題和解決方案

### 4. [資料庫查詢問答](database_query_qa.md)
- 如何查看 PDF 處理後的實體數據？
- 如何驗證實體數據是否正確？
- 如何查詢特定實體的詳細資訊？
- 如何查詢實體間的關係？

### 5. [關係提取失敗根本原因](relation_extraction_root_cause.md)
- 為什麼沒有關係？
- 是數據問題還是代碼問題？
- 關係提取為什麼依賴實體提取？
- 如何解決關係提取失敗的問題？

### 6. [關係提取問題故障排除完整記錄](relation_extraction_troubleshooting.md)
- 完整的故障排除過程
- Debug Mode 診斷方法
- 根本原因分析和修復
- 修復前後對比
- 經驗教訓和後續建議

### 7. [LLM 降級警告信息說明](llm_fallback_warning_qa.md)
- "LLM extraction returned empty" 是錯誤嗎？
- 降級機制說明
- 如何消除警告信息
- 當前系統狀態

### 8. [Prometheus 指標標籤缺失錯誤](prometheus_metrics_label_error.md) ⭐ 新增
- 500 錯誤：counter metric is missing label values
- Prometheus 指標標籤使用錯誤
- 修復方案和最佳實踐
- 預防措施和檢查清單

### 9. [DateTime JSON 序列化錯誤](datetime_json_serialization_error.md) ⭐ 新增
- 500 錯誤：Object of type datetime is not JSON serializable
- Pydantic model_dump() 序列化問題
- 修復方案（使用 mode='json'）
- 最佳實踐和測試驗證

### 10. [LLM 真實 API 實作指南](llm_real_api_implementation_guide.md) ⭐ 新增
- 如何配置真實的 Gemini/OpenAI/DeepSeek API
- 安裝依賴和配置 API Key
- 驗證真實 API 是否正常工作
- 降級機制說明
- 成本考量和最佳實踐

### 11. [API 啟動錯誤處理問答](api_startup_errors_qa.md) ⭐ 新增
- email-validator 版本不足錯誤
- _stub_generate 異步問題
- GOOGLE_API_KEY 配置驗證錯誤
- Ctrl+C 無法停止服務問題
- 完整的錯誤診斷和解決方案

### 12. [Gemini API 配額錯誤深度分析](gemini_quota_error_analysis.md) ⭐ 新增
- 429 配額錯誤深度分析
- 免費層配額限制問題
- 模型選擇建議
- 重試機制實作
- 完整的診斷和解決方案

### 13. [Gemini API Key 差異根本原因分析](gemini_api_key_difference_root_cause.md) ⭐ 新增
- 不同 API Key 導致不同行為的根本原因
- 終端輸出證據分析
- 環境變數和 Settings 比較
- 專案計費狀態差異說明
- 解決方案和驗證方法

### 14. [環境變數優先順序分析](env_priority_analysis.md) ⭐ 新增
- .env 檔案和環境變數的優先順序問題
- 當前代碼邏輯分析
- 建議的優先順序（.env 優先，環境變數其次）
- 修改方案和驗證方法

### 15. [LLM 關係提取返回空結果分析](llm_relation_extraction_empty_analysis.md) ⭐ 新增
- 為什麼 LLM 關係提取會返回空結果
- 實體名稱不匹配問題
- JSON 解析問題
- 改善方案和診斷方法

### 16. [正則表達式：貪婪匹配 vs 非貪婪匹配詳細說明](regex_greedy_vs_non_greedy_explanation.md) ⭐ 新增
- 貪婪匹配和非貪婪匹配的基本概念
- 在當前代碼中的問題分析
- 詳細對比範例
- 為什麼非貪婪匹配會導致解析失敗
- 解決方案和最佳實踐

### 17. [JSON 解析問題修復總結](json_parsing_fixes_summary.md) ⭐ 新增
- JSON 解析問題的完整修復總結
- 根本原因分析（正則表達式、變數作用域、日誌記錄）
- 修復方案詳解
- 預期效果和測試建議

### 18. [PDF 重複處理時的數據行為分析](pdf_repeat_processing_data_behavior.md) ⭐ 新增
- 重複轉換 PDF 時數據是追加還是覆蓋？
- INSERT OR REPLACE 行為分析
- 文件 ID、實體 ID、關係 ID 生成邏輯
- 不同場景下的實際行為
- 改進建議（確定性 ID、清理選項、模糊匹配）

### 19. [重置 GraphRAG 資料庫指南](reset_graph_db_guide.md) ⭐ 新增

### 20. [Uvicorn Ctrl+C 無法停止服務問題修復](uvicorn_ctrl_c_shutdown_fix.md) ⭐ 新增
- 為什麼 Ctrl+C 無法停止 uvicorn 服務？
- 根本原因分析（CancelledError 處理）
- 解決方案（超時保護、正確的異常處理）
- 測試方法和技術要點
- 如何重置資料庫清理所有數據
- 使用重置腳本的方法
- 手動刪除資料庫文件的方法
- 完整重置和重新導入流程
- 注意事項和最佳實踐

## 快速查找

### 按主題查找

**Stub 相關**：
- [什麼是 Stub？](stub_qa.md#q-什麼是-stub)
- [為什麼使用 Stub？](stub_qa.md#q-為什麼專案中使用-stub)
- [如何替換 Stub？](stub_qa.md#q-如何替換-stub)

**錯誤處理**：
- [JSON 解析錯誤](json_parse_error_qa.md#q-為什麼會出現-failed-to-parse-relation-response-錯誤)
- [API 啟動錯誤](api_startup_errors_qa.md) ⭐ 新增
- [虛擬環境問題](general_qa.md#問題-2-虛擬環境問題)
- [模組找不到](general_qa.md#問題-1-模組找不到)

**使用指南**：
- [如何開始使用？](general_qa.md#q-如何開始使用)
- [如何檢查系統狀態？](general_qa.md#q-如何檢查系統狀態)
- [如何配置真實 LLM API？](llm_real_api_implementation_guide.md) ⭐ 新增

## 相關文檔

- [完整實作計劃](../graphrag_implementation_plan.md)
- [PDF 處理指南](../pdf_processing_guide.md)
- [虛擬環境設置指南](../venv_setup_guide.md)
- [故障排除指南](../troubleshooting.md)
- [錯誤修復記錄](../error_fixes.md)

## 更新記錄

- **2025-12-26 16:32** - 添加重置 GraphRAG 資料庫指南 ⭐ 新增
  - 如何重置資料庫清理所有數據
  - 使用重置腳本的方法
  - 完整重置和重新導入流程

- **2025-12-26 16:20** - 添加 PDF 重複處理時的數據行為分析 ⭐ 新增
  - 分析重複轉換 PDF 時數據是追加還是覆蓋
  - INSERT OR REPLACE 行為詳解
  - 文件 ID、實體 ID、關係 ID 生成邏輯
  - 不同場景下的實際行為和改進建議

- **2025-12-26 16:15** - 添加 JSON 解析問題修復總結和正則表達式說明 ⭐ 新增
  - JSON 解析問題的完整修復總結
  - 正則表達式：貪婪匹配 vs 非貪婪匹配詳細說明
  - 修復方案詳解（正則表達式、變數作用域、日誌記錄、完整性驗證）
  - 預期效果和測試建議

- **2025-12-26 15:43** - 添加 LLM 關係提取返回空結果分析 ⭐ 新增
  - 為什麼 LLM 關係提取會返回空結果
  - 實體名稱不匹配問題診斷
  - JSON 解析問題分析
  - 改善方案（模糊匹配）和診斷方法

- **2025-12-26 15:35** - 添加環境變數優先順序分析 ⭐ 新增
  - .env 檔案和環境變數的優先順序問題
  - 當前代碼邏輯分析
  - 建議的優先順序（.env 優先，環境變數其次）
  - 修改方案和驗證方法

- **2025-12-26 15:29** - 添加 Gemini API Key 差異根本原因分析 ⭐ 新增
  - 不同 API Key 導致不同行為的根本原因
  - 終端輸出證據分析
  - 環境變數和 Settings 比較
  - 專案計費狀態差異說明
  - 解決方案和驗證方法

- **2025-12-26 14:37** - 添加 Gemini API 配額錯誤深度分析 ⭐ 新增
  - 429 配額錯誤深度分析
  - 免費層配額限制問題診斷
  - 模型選擇建議和解決方案
  - 重試機制實作說明

- **2025-12-26 16:50** - 添加 Uvicorn Ctrl+C 無法停止服務問題修復 ⭐ 新增
  - 根本原因分析（CancelledError 處理問題）
  - 解決方案（超時保護、正確的異常處理）
  - 測試方法和技術要點

- **2025-12-26 13:51** - 添加 API 啟動錯誤處理問答 ⭐ 新增
  - email-validator 版本不足錯誤處理
  - _stub_generate 異步問題修復
  - GOOGLE_API_KEY 配置驗證錯誤處理
  - Ctrl+C 無法停止服務問題修復（初步修復）
  - 完整的錯誤診斷和解決方案

- **2025-12-26 13:28** - 添加 LLM 真實 API 實作指南 ⭐ 新增
  - 完整的 Gemini/OpenAI/DeepSeek API 配置指南
  - 安裝依賴和配置 API Key 步驟
  - 驗證和測試方法
  - 降級機制和最佳實踐

- **2025-12-26 13:20** - 添加 LLM 降級警告信息說明
  - 解釋 "LLM extraction returned empty" 警告
  - 說明降級機制
  - 如何消除警告信息

- **2025-12-26 13:18** - 添加關係提取故障排除完整記錄
  - 完整的故障排除過程
  - Debug Mode 診斷方法
  - 根本原因分析和修復
  - 修復驗證（3270 實體，7579 關係）

- **2025-12-26 11:33** - 建立 QA 文檔集
  - Stub 相關問答
  - JSON 解析錯誤問答
  - 一般問答

