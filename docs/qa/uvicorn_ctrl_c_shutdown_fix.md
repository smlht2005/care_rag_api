# Uvicorn Ctrl+C 無法停止服務問題修復

**更新時間：2025-12-26 16:50**  
**作者：AI Assistant**  
**修改摘要：修復 uvicorn 服務無法通過 Ctrl+C 停止的根本原因**

---

## 問題描述

當運行 `uvicorn app.main:app --reload` 時，按 Ctrl+C 無法停止服務，出現以下錯誤：

```
ERROR:    Traceback (most recent call last):
  File "...\asyncio\runners.py", line 118, in run
    return self._loop.run_until_complete(task)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "...\asyncio\base_events.py", line 687, in run_until_complete
    return future.result()
           ^^^^^^^^^^^^^^^
asyncio.exceptions.CancelledError
...
  File "...\starlette\routing.py", line 699, in lifespan
    await receive()
  File "...\uvicorn\lifespan\on.py", line 137, in receive
    return await self.receive_queue.get()
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "...\asyncio\queues.py", line 158, in get
    await getter
asyncio.exceptions.CancelledError
```

## 根本原因分析

### 問題 1：Lifespan Shutdown 階段沒有正確處理 CancelledError

**位置**：`app/main.py` 的 `lifespan` 函數

**問題**：
- 當 Ctrl+C 被按下時，會觸發 `KeyboardInterrupt`，然後轉換為 `asyncio.CancelledError`
- 在 shutdown 階段，`await graph_store.close()` 可能阻塞
- 異常處理只捕獲了 `Exception`，沒有捕獲 `CancelledError`
- 導致 `CancelledError` 被吞掉，無法正常退出

### 問題 2：GraphStore.close() 可能阻塞

**位置**：`app/core/graph_store.py` 的 `close()` 方法

**問題**：
- `await self.conn.close()` 可能因為資料庫操作而阻塞
- 沒有設置超時機制
- 沒有處理 `CancelledError`

### 問題 3：缺少超時保護

**問題**：
- shutdown 階段的清理操作沒有超時保護
- 如果清理操作阻塞，會導致無法響應 Ctrl+C

---

## 解決方案

### 修復 1：改進 Lifespan Shutdown 處理

**文件**：`app/main.py`

**修改內容**：

1. **使用 `try-finally` 確保清理執行**：
   ```python
   try:
       yield  # 應用程式運行階段
   finally:
       # 關閉階段（確保在異常情況下也能執行）
   ```

2. **明確捕獲 `CancelledError` 並重新拋出**：
   ```python
   except asyncio.CancelledError:
       logger.info("Shutdown cancelled by user (Ctrl+C)")
       raise  # 重新拋出 CancelledError，讓上層處理
   ```

3. **為清理操作設置超時**：
   ```python
   await asyncio.wait_for(
       graph_store.close(),
       timeout=2.0
   )
   ```

4. **處理超時和取消**：
   ```python
   except asyncio.TimeoutError:
       logger.warning("GraphStore close timeout, forcing shutdown")
   except asyncio.CancelledError:
       logger.info("GraphStore close cancelled, continuing shutdown")
       raise
   ```

### 修復 2：改進 GraphStore.close() 方法

**文件**：`app/core/graph_store.py`

**修改內容**：

1. **處理 `CancelledError`**：
   ```python
   except asyncio.CancelledError:
       # 如果被取消，嘗試強制關閉連接
       if self.conn:
           try:
               # 嘗試同步關閉（如果可能）
               if hasattr(self.conn, '_conn') and self.conn._conn:
                   self.conn._conn.close()
           except:
               pass
           self.conn = None
       raise  # 重新拋出 CancelledError
   ```

2. **確保連接被清理**：
   ```python
   await self.conn.close()
   self.conn = None  # 確保引用被清除
   ```

---

## 修復效果

### 修復前

- ❌ Ctrl+C 無法停止服務
- ❌ 需要強制終止進程（taskkill /F）
- ❌ 錯誤堆疊顯示 `CancelledError` 被吞掉

### 修復後

- ✅ Ctrl+C 可以正常停止服務
- ✅ 清理操作有超時保護（2秒）
- ✅ 正確處理 `CancelledError` 並允許退出
- ✅ 日誌記錄清晰的關閉過程

---

## 測試方法

### 測試 1：正常啟動和停止

```bash
# 啟動服務
uvicorn app.main:app --reload

# 按 Ctrl+C 停止
# 應該看到：
# INFO: Shutting down
# INFO: Care RAG API shutting down...
# INFO: GraphStore closed
# INFO: Care RAG API shutdown complete
# INFO: Application shutdown complete.
```

### 測試 2：快速停止（測試超時）

```bash
# 啟動服務
uvicorn app.main:app --reload

# 立即按 Ctrl+C（在服務完全啟動前）
# 應該能快速退出，不會卡住
```

### 測試 3：強制終止（如果仍有問題）

```bash
# Windows
tasklist | findstr python
taskkill /F /PID <PID>

# Linux/Mac
ps aux | grep uvicorn
kill -9 <PID>
```

---

## 技術要點

### 1. asyncio.CancelledError 處理原則

- **不要吞掉 `CancelledError`**：應該重新拋出，讓上層處理
- **在 finally 中執行清理**：確保即使被取消也能執行清理
- **設置超時**：避免清理操作無限阻塞

### 2. FastAPI Lifespan 最佳實踐

- **使用 `try-finally`**：確保 shutdown 階段總會執行
- **明確處理 `CancelledError`**：不要讓它被 `Exception` 捕獲
- **快速清理**：清理操作應該快速完成，或設置超時

### 3. 資料庫連接關閉

- **設置超時**：避免關閉操作阻塞
- **處理取消**：如果被取消，嘗試強制關閉
- **清理引用**：確保連接引用被清除

---

## 相關文件

- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)
- [asyncio CancelledError](https://docs.python.org/3/library/asyncio-task.html#asyncio.CancelledError)
- [Uvicorn Shutdown](https://www.uvicorn.org/settings/#shutdown-timeout)

---

## 更新歷史

- **2025-12-26 16:50**: 修復 Ctrl+C 無法停止服務的問題
- **2025-12-26 13:45**: 改用 lifespan context manager（初始實現）

