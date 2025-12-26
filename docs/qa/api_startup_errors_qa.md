# API 啟動錯誤處理問答

**更新時間：2025-12-26 13:48**  
**作者：AI Assistant**  
**修改摘要：總結 API 啟動過程中遇到的常見錯誤及解決方案**

---

## 概述

本文檔記錄了 Care RAG API 在啟動和運行過程中遇到的常見錯誤，以及對應的解決方案。這些錯誤主要涉及依賴套件、配置驗證、異步處理和資源清理等方面。

---

## 錯誤 1: email-validator 版本不足

### 錯誤訊息

```
ImportError: email-validator version >= 2.0 required, run pip install -U email-validator
```

### 錯誤位置

```
File "C:\...\pydantic\networks.py", line 969, in import_email_validator
    raise ImportError('email-validator version >= 2.0 required, run pip install -U email-validator')
```

### 根本原因

- **Pydantic 2.0+ 需要 `email-validator>=2.0.0`** 來支援 Email 驗證
- `requirements.txt` 中缺少此依賴
- 系統中安裝的是舊版本 `email-validator 1.3.1`

### 解決方案

#### 步驟 1: 更新 requirements.txt

在 `requirements.txt` 中添加：

```txt
email-validator>=2.0.0
```

#### 步驟 2: 安裝套件

```bash
pip install email-validator>=2.0.0
```

### 驗證

重新啟動 API 服務，應該不再出現此錯誤。

### 注意事項

如果系統中同時安裝了 `flask-appbuilder`（需要 `email-validator<2`），可能會出現警告，但不影響 FastAPI 的運行。

---

## 錯誤 2: _stub_generate 方法異步問題

### 錯誤訊息

```python
SyntaxError: 'await' outside async function
```

或運行時錯誤：

```
RuntimeError: coroutine 'GeminiLLM._stub_generate' was never awaited
```

### 錯誤位置

`app/services/llm_service.py` 中的 `_stub_generate` 方法

### 根本原因

- `_stub_generate` 方法被定義為**同步方法**（`def`）
- 但方法內部使用了 `await asyncio.sleep(0.1)`
- 在異步方法中調用時沒有使用 `await`

### 解決方案

#### 步驟 1: 將方法改為異步

```python
# 修復前
def _stub_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
    await asyncio.sleep(0.1)  # ❌ 錯誤：同步方法不能使用 await
    return f"[Gemini Stub] 回答: {prompt}..."

# 修復後
async def _stub_generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
    await asyncio.sleep(0.1)  # ✅ 正確：異步方法可以使用 await
    return f"[Gemini Stub] 回答: {prompt}..."
```

#### 步驟 2: 在所有調用處添加 await

```python
# 修復前
return self._stub_generate(prompt, max_tokens, temperature)

# 修復後
return await self._stub_generate(prompt, max_tokens, temperature)
```

### 影響範圍

需要修復三個 LLM 類別：
- `GeminiLLM._stub_generate`
- `OpenAILLM._stub_generate`
- `DeepSeekLLM._stub_generate`

每個類別有 2 處調用需要添加 `await`，共 6 處。

### 驗證

- 語法檢查通過
- 所有 `_stub_generate` 方法已改為異步
- 所有調用處已正確使用 `await`

---

## 錯誤 3: GOOGLE_API_KEY 配置驗證錯誤

### 錯誤訊息

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
GOOGLE_API_KEY
  Extra inputs are not permitted [type=extra_forbidden, input_value='AIzaSy...', input_type=str]
```

### 錯誤位置

```
File "app/config.py", line 59, in <module>
    settings = Settings()
```

### 根本原因

- `.env` 檔案中定義了 `GOOGLE_API_KEY` 環境變數
- `Settings` 類別中只定義了 `GEMINI_API_KEY`，沒有 `GOOGLE_API_KEY`
- **Pydantic 預設不允許額外的欄位**（`extra_forbidden`），導致驗證失敗

### 解決方案

#### 步驟 1: 在 Settings 中添加 GOOGLE_API_KEY 欄位

```python
# app/config.py
class Settings(BaseSettings):
    # ...
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None  # 別名，與 GEMINI_API_KEY 互換使用
    # ...
```

#### 步驟 2: 更新 LLM 服務以支援兩個欄位

```python
# app/services/llm_service.py
class GeminiLLM(BaseLLM):
    def __init__(self, api_key: Optional[str] = None):
        # 優先使用傳入的 api_key，否則使用 GEMINI_API_KEY 或 GOOGLE_API_KEY
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.GOOGLE_API_KEY
        # ...
```

### 配置建議

- **推薦**：在 `.env` 中使用 `GEMINI_API_KEY`
- **也支援**：使用 `GOOGLE_API_KEY`（向後相容）
- **優先順序**：如果兩個都配置，優先使用 `GEMINI_API_KEY`

### 驗證

重新啟動 API 服務，應該不再出現 Pydantic 驗證錯誤。

---

## 錯誤 4: Ctrl+C 無法停止服務

### 錯誤訊息

```
asyncio.exceptions.CancelledError
KeyboardInterrupt
```

### 錯誤位置

按 Ctrl+C 時，服務無法正常停止，出現異常堆疊。

### 根本原因

1. **使用舊的 `@app.on_event` 裝飾器**，對異步上下文清理支援不足
2. **未正確處理異步任務的取消**
3. **GraphStore 連接在關閉時未正確清理**

### 解決方案

#### 步驟 1: 改用 lifespan context manager

```python
# 修復前（舊方式）
@app.on_event("startup")
async def startup_event():
    # 啟動邏輯
    pass

@app.on_event("shutdown")
async def shutdown_event():
    # 關閉邏輯
    pass

# 修復後（推薦方式）
@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動階段
    logger.info("Care RAG API starting up...")
    # ... 初始化資源 ...
    
    yield  # 應用程式運行階段
    
    # 關閉階段
    logger.info("Care RAG API shutting down...")
    # ... 清理資源 ...

app = FastAPI(
    # ...
    lifespan=lifespan
)
```

#### 步驟 2: 正確清理資源

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 啟動階段
    graph_store = None
    try:
        from app.api.v1.dependencies import get_graph_store
        graph_store = get_graph_store()
        await graph_store.initialize()
        logger.info("GraphStore initialized")
    except Exception as e:
        logger.warning(f"GraphStore initialization failed: {str(e)}")
    
    yield  # 應用程式運行階段
    
    # 關閉階段
    logger.info("Care RAG API shutting down...")
    
    # 清理 GraphStore 連接
    if graph_store:
        try:
            if hasattr(graph_store, 'close'):
                await graph_store.close()
            logger.info("GraphStore closed")
        except Exception as e:
            logger.warning(f"Error closing GraphStore: {str(e)}")
    
    logger.info("Care RAG API shutdown complete")
```

### 優點

- ✅ **更好的異步上下文管理**：`lifespan` context manager 會正確處理異步上下文的啟動和清理
- ✅ **優雅的關閉**：資源清理更完整，減少異常
- ✅ **FastAPI 推薦方式**：符合 FastAPI 最佳實踐

### 驗證

重新啟動 API 服務，按 Ctrl+C 應該可以正常停止服務。

---

## 常見問題

### Q1: 為什麼會出現這些錯誤？

**A**: 這些錯誤主要是在實作真實 LLM API 整合和改善系統穩定性過程中遇到的：

1. **依賴管理問題**：缺少必要的依賴套件或版本不匹配
2. **異步處理問題**：同步和異步方法混用
3. **配置驗證問題**：Pydantic 嚴格驗證環境變數
4. **資源清理問題**：使用舊的 API 導致資源清理不完整

### Q2: 如何避免這些錯誤？

**A**: 建議遵循以下最佳實踐：

1. **依賴管理**：
   - 定期更新 `requirements.txt`
   - 使用虛擬環境隔離依賴
   - 測試新依賴的相容性

2. **異步處理**：
   - 明確區分同步和異步方法
   - 使用 `async def` 定義異步方法
   - 在調用異步方法時使用 `await`

3. **配置管理**：
   - 在 Settings 中定義所有需要的環境變數
   - 使用 `Optional[str] = None` 允許可選配置
   - 提供清晰的配置文檔

4. **資源清理**：
   - 使用 FastAPI 的 `lifespan` context manager
   - 在 shutdown 階段正確清理資源
   - 處理清理過程中的異常

### Q3: 這些錯誤會影響生產環境嗎？

**A**: 

- ✅ **錯誤 1 (email-validator)**：會阻止服務啟動，必須修復
- ✅ **錯誤 2 (_stub_generate)**：會導致運行時錯誤，必須修復
- ✅ **錯誤 3 (GOOGLE_API_KEY)**：會阻止服務啟動，必須修復
- ⚠️ **錯誤 4 (Ctrl+C)**：不會影響正常運行，但會影響優雅關閉，建議修復

### Q4: 如何驗證修復是否成功？

**A**: 

1. **錯誤 1-3**：重新啟動 API 服務，檢查是否還有錯誤訊息
2. **錯誤 4**：啟動服務後按 Ctrl+C，檢查是否能正常停止

---

## 相關文檔

- `docs/qa/llm_real_api_implementation_guide.md` - LLM 真實 API 實作指南
- `docs/qa/llm_fallback_warning_qa.md` - LLM 降級警告說明
- `app/config.py` - 配置檔案
- `app/services/llm_service.py` - LLM 服務實作
- `app/main.py` - 主應用程式

---

## 總結

### 修復清單

- ✅ **錯誤 1**: 添加 `email-validator>=2.0.0` 到 `requirements.txt`
- ✅ **錯誤 2**: 將 `_stub_generate` 方法改為異步，並在所有調用處添加 `await`
- ✅ **錯誤 3**: 在 Settings 中添加 `GOOGLE_API_KEY` 欄位，並更新 LLM 服務
- ✅ **錯誤 4**: 改用 `lifespan` context manager，並正確清理資源

### 經驗教訓

1. **依賴管理很重要**：定期檢查和更新依賴套件
2. **異步處理要謹慎**：明確區分同步和異步方法
3. **配置驗證要完整**：在 Settings 中定義所有環境變數
4. **資源清理要優雅**：使用現代 API 和最佳實踐

### 下一步

- 繼續監控系統運行狀態
- 收集更多錯誤案例並更新本文檔
- 建立自動化測試來預防類似錯誤

---

**結論**: 所有錯誤已修復，API 服務現在可以正常啟動和運行。建議定期檢查依賴套件和配置，確保系統穩定性。

