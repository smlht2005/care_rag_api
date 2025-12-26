# 重置 GraphRAG 資料庫指南

**更新時間：2025-12-26 16:32**  
**作者：AI Assistant**  
**修改摘要：創建重置 GraphRAG 資料庫的完整指南**

---

## 問題

當資料庫中有重複或髒數據時，需要重置資料庫並重新導入 PDF。

## 解決方案

### 方法 1：使用重置腳本（推薦）

**腳本位置**：`scripts/reset_graph_db.py`

**使用方法**：

```bash
# 1. 重置資料庫（會提示確認）
python scripts/reset_graph_db.py

# 2. 自動確認重置（跳過確認提示）
python scripts/reset_graph_db.py --confirm

# 3. 重新導入 PDF
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"
```

**功能**：
- 顯示當前資料庫統計信息（實體數、關係數等）
- 安全刪除現有資料庫文件
- 創建全新的乾淨資料庫
- 驗證新資料庫是否正確創建

**範例輸出**：
```
============================================================
重置 GraphRAG 資料庫
============================================================

發現現有資料庫: ./data/graph.db
文件大小: 20.00 MB

當前數據統計:
  實體總數: 2194
  關係總數: 3995
  實體類型: {'Document': 66, 'Concept': 1500, 'Person': 200, ...}
  關係類型: {'CONTAINS': 2000, 'RELATED_TO': 1500, ...}

✅ 已刪除資料庫文件: ./data/graph.db

創建新的資料庫...
✅ 新資料庫創建成功
  實體總數: 0
  關係總數: 0

============================================================
重置完成！
============================================================

現在可以使用以下命令重新導入 PDF:
  python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"
```

### 方法 2：手動刪除資料庫文件

**步驟**：

1. **停止所有正在運行的服務**（如果有）

2. **刪除資料庫文件**：
   ```bash
   # Windows
   del data\graph.db
   
   # Linux/Mac
   rm data/graph.db
   ```

3. **重新導入 PDF**：
   ```bash
   python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"
   ```

**注意**：資料庫會在第一次使用時自動創建。

### 方法 3：使用 --overwrite 選項（部分清理）

如果只想清理特定 PDF 的數據，可以使用 `--overwrite` 選項：

```bash
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf" --overwrite
```

這會：
- 只刪除相同來源的 PDF 數據
- 保留其他 PDF 的數據
- 適合多個 PDF 文件的場景

## 完整重置流程

### 步驟 1：重置資料庫

```bash
python scripts/reset_graph_db.py --confirm
```

### 步驟 2：重新導入 PDF

```bash
# 使用預設文件
python scripts/process_pdf_to_graph.py

# 或指定文件路徑
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf"

# 如果需要指定文件 ID
python scripts/process_pdf_to_graph.py "data/example/your_file.pdf" --doc-id "my_document_id"
```

### 步驟 3：驗證數據

```bash
python scripts/check_db.py
```

## 常見問題

### Q1: 資料庫文件被鎖定，無法刪除

**錯誤訊息**：
```
❌ 刪除資料庫文件失敗: [WinError 32] 程序無法存取檔案，因為檔案正由另一個程序使用。
```

**原因**：
- API 服務（uvicorn）正在運行並鎖定資料庫
- 其他 Python 腳本正在使用資料庫
- 資料庫連接未正確關閉

**解決方案**：

1. **停止所有 API 服務**：
   ```bash
   # 找到並停止 uvicorn 進程
   # Windows: 在任務管理器中結束 Python 進程
   # Linux/Mac: killall python 或 pkill -f uvicorn
   ```

2. **檢查是否有其他進程使用資料庫**：
   ```bash
   # Windows
   tasklist | findstr python
   
   # Linux/Mac
   ps aux | grep python
   ```

3. **等待幾秒後重試**：
   - 腳本會自動重試 3 次，每次等待時間遞增
   - 如果仍失敗，請手動停止所有相關進程

### Q2: Ctrl+C 無法停止腳本

**原因**：
- 在 Windows 上，`input()` 函數可能無法立即響應 Ctrl+C
- 資料庫操作可能阻塞了信號處理

**解決方案**：

1. **使用 `--confirm` 選項跳過確認提示**：
   ```bash
   python scripts/reset_graph_db.py --confirm
   ```

2. **如果腳本卡住，強制終止**：
   - Windows: 在任務管理器中結束 Python 進程
   - Linux/Mac: 使用 `kill -9 <PID>` 強制終止

3. **腳本已改進**：
   - 添加了更好的信號處理
   - 添加了資料庫鎖定檢查
   - 添加了重試機制

## 注意事項

1. **備份數據**：
   - 重置前建議備份 `data/graph.db` 文件
   - 如果數據很重要，可以先複製到其他位置

2. **向量資料庫**：
   - 重置腳本只清理圖資料庫（graph.db）
   - 向量資料庫（如果使用）需要單獨清理
   - 向量資料庫通常位於 `data/vector_store/` 目錄

3. **服務狀態**：
   - 重置前確保沒有其他進程正在使用資料庫
   - 如果有 API 服務運行，建議先停止：
     ```bash
     # 停止 uvicorn 服務
     # 按 Ctrl+C 或關閉終端窗口
     ```

4. **資料庫位置**：
   - 預設位置：`./data/graph.db`
   - 可在 `app/config.py` 中修改 `GRAPH_DB_PATH`

5. **資料庫鎖定檢查**：
   - 腳本會自動檢查資料庫是否被鎖定
   - 如果被鎖定，會顯示詳細的錯誤信息和解決方案
   - 腳本會自動重試 3 次，每次等待時間遞增（1秒、2秒、4秒）

## 相關文件

- [重置腳本](../scripts/reset_graph_db.py)
- [PDF 處理腳本](../scripts/process_pdf_to_graph.py)
- [PDF 重複處理行為分析](./pdf_repeat_processing_data_behavior.md)
- [資料庫配置](../app/config.py)

## 更新歷史

- **2025-12-26 16:45**: 添加資料庫鎖定和 Ctrl+C 問題的解決方案
- **2025-12-26 16:32**: 創建重置資料庫指南

