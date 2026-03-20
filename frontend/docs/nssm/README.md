更新時間：2026-03-18 17:47
作者：AI Assistant
修改摘要：整理 Windows Server 使用 nssm 將 FastAPI(Uvicorn) 與 Nginx 服務化的設定方式、log 方案與常見錯誤排查（含 ModuleNotFoundError: app 的修正）

## 目的

在 Windows Server 上把以下程式改成「可開機自動啟動」且「可被服務管理」：

- FastAPI / Uvicorn（本專案：`uvicorn app.main:app ...`）
- Nginx（反向代理與靜態檔服務）

本文件假設你已有：
- Nginx：`C:\nginx`
- 專案：`C:\sites\app\care_rag_api`
- venv：`C:\sites\app\care_rag_api\env`
- 後端啟動目標：listen `8002`

---

## 0) 重要概念：AppDirectory（工作目錄）會影響 Python import

本專案在 Windows Server 的目錄結構為：
- `C:\sites\app\care_rag_api\src\app\main.py`

因此 `uvicorn app.main:app` 需要在 `PYTHONPATH` 能找到 `app` 套件。

最簡單方式就是把 nssm 的 **AppDirectory** 設為：

- `C:\sites\app\care_rag_api\src`

若 AppDirectory 設錯，常見錯誤是：

```text
ModuleNotFoundError: No module named 'app'
```

---

## 1) 建立 Uvicorn 服務（服務名：care_rag_api）

### 1.1 確認 uvicorn.exe 路徑

通常在 venv 內：

```bat
dir C:\sites\app\care_rag_api\env\Scripts\uvicorn.exe
```

### 1.2 安裝服務（建議使用 venv 的 uvicorn.exe）

（以下假設 nssm 在 `C:\nssm\nssm.exe`）

```bat
C:\nssm\nssm.exe install care_rag_api "C:\sites\app\care_rag_api\env\Scripts\uvicorn.exe" app.main:app --host 0.0.0.0 --port 8002
```

### 1.3 設定 AppDirectory（修正 No module named 'app' 的關鍵）

```bat
C:\nssm\nssm.exe set care_rag_api AppDirectory "C:\sites\app\care_rag_api\src"
```

### 1.4 設定自動啟動

```bat
C:\nssm\nssm.exe set care_rag_api Start SERVICE_AUTO_START
```

### 1.5 啟動/停止/查看

```bat
sc start care_rag_api
sc stop care_rag_api
sc query care_rag_api
```

期望狀態：
- `STATE : 4 RUNNING`

---

## 2) 建立 Nginx 服務（建議服務名：care_rag_nginx）

```bat
C:\nssm\nssm.exe install care_rag_nginx "C:\nginx\nginx.exe"
C:\nssm\nssm.exe set care_rag_nginx AppDirectory "C:\nginx"
C:\nssm\nssm.exe set care_rag_nginx Start SERVICE_AUTO_START
sc start care_rag_nginx
```

---

## 3) 建議：將 stdout/stderr 轉存檔案（debug 必備）

建立 log 目錄：

```bat
mkdir C:\sites\app\care_rag_api\logs
```

設定 Uvicorn log：

```bat
C:\nssm\nssm.exe set care_rag_api AppStdout "C:\sites\app\care_rag_api\logs\uvicorn-stdout.log"
C:\nssm\nssm.exe set care_rag_api AppStderr "C:\sites\app\care_rag_api\logs\uvicorn-stderr.log"
```

（選用）輪替：

```bat
C:\nssm\nssm.exe set care_rag_api AppRotateFiles 1
C:\nssm\nssm.exe set care_rag_api AppRotateOnline 1
C:\nssm\nssm.exe set care_rag_api AppRotateBytes 10485760
```

設定完請重啟服務：

```bat
sc stop care_rag_api
sc start care_rag_api
```

查看錯誤（最常用）：

```bat
type C:\sites\app\care_rag_api\logs\uvicorn-stderr.log
```

---

## 4) 驗證清單（服務是否真的有跑）

### 4.1 檢查 port 是否 LISTENING

```bat
netstat -ano | findstr :8002
```

### 4.2 檢查 API 是否回應

```bat
curl http://127.0.0.1:8002/docs
```

（或用瀏覽器打開 `http://127.0.0.1:8002/docs`）

---

## 5) 常見錯誤與排查

### 5.1 `ModuleNotFoundError: No module named 'app'`

原因：
- `AppDirectory` 設錯（不在 `...\src`）導致找不到 `app` 套件。

修正：

```bat
C:\nssm\nssm.exe set care_rag_api AppDirectory "C:\sites\app\care_rag_api\src"
sc stop care_rag_api
sc start care_rag_api
```

### 5.2 `STATE : 7 PAUSED` 且 `netstat` 看不到 port

含意：
- 服務名義上存在，但底層程式並未成功啟動（常見是啟動後立即 crash）。

作法：
- 看 `uvicorn-stderr.log` 取得真正錯誤原因（例如 import/module、權限、缺套件、port 被占用）。

### 5.3 Port 被占用（常見 Win32 error 10048）

先查：

```bat
netstat -ano | findstr :8002
tasklist /fi "PID eq <PID>"
```

---

## 6) 參考：讀取 nssm 服務設定（確認是否設對）

```bat
C:\nssm\nssm.exe get care_rag_api Application
C:\nssm\nssm.exe get care_rag_api AppParameters
C:\nssm\nssm.exe get care_rag_api AppDirectory
```

