<!--
  更新時間：2026-04-01 15:02
  作者：AI Assistant
  修改摘要：新增以 robocopy 將 care_rag_api 原始碼同步至 Windows Server（c$ 管理分享）的 SOP，含備份、同步、重啟與驗證清單
-->

# Robocopy 部署 SOP（Windows Server / 管理分享 c$）

## 目的

將本機開發機（新版）`care_rag_api` 的 Python 原始碼同步到 Windows Server：

- 目的地：`\\172.31.6.123\c$\sites\app\care_rag_api\src`

並確保同步後可由 NSSM/Service 正常啟動、可驗證 API 服務已上線。

---

## 重要路徑對應（避免多一層資料夾）

本機 repo（來源）：

- `C:\Development\langChain\source\care_rag\care_rag_api\app\...`

Windows Server（目的地）預期結構：

- `C:\sites\app\care_rag_api\src\app\main.py`

因此同步時要以「資料夾內容對應」方式：

- `SRC\app\*` → `DST\app\*`（不是把整個 repo 根目錄直接丟到 `src`）

---

## 0) 前置條件

- 你在開發機上有權限存取 `\\172.31.6.123\c$`（Local Admin/Domain Admin 常見）
- Windows Server 上已存在：
  - `C:\sites\app\care_rag_api\src`
  - （建議）NSSM 服務 `care_rag_api`，且 `AppDirectory` 指到 `C:\sites\app\care_rag_api\src`
- 不要把開發機 `.env` 覆蓋到正式機（沿用正式機設定）

---

## 1) 連線檢查（開發機執行）

### 1.1 驗證分享可達

PowerShell：

```powershell
Test-Path "\\172.31.6.123\c$"
Test-Path "\\172.31.6.123\c$\sites\app\care_rag_api\src"
```

### 1.2 需要帳密時先掛載（選用）

CMD：

```bat
net use \\172.31.6.123\c$ /user:.\Administrator *
```

### 1.3 取得時間戳（記錄用）

CMD（依規範）：

```bat
echo %date% %time%
```

---

## 2) 備份 + 同步（開發機執行）

### 2.1 設定變數

CMD：

```bat
set SRC=C:\Development\langChain\source\care_rag\care_rag_api
set DST=\\172.31.6.123\c$\sites\app\care_rag_api\src
set LOGDIR=%SRC%\logs_deploy
if not exist "%LOGDIR%" mkdir "%LOGDIR%"
```

### 2.2 先備份目的地（強烈建議）

請自行把 `src_backup_YYYYMMDD_HHMMSS` 改成當下時間戳記。

```bat
set BKP=\\172.31.6.123\c$\sites\app\care_rag_api\src_backup_YYYYMMDD_HHMMSS
robocopy "%DST%" "%BKP%" /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /NFL /NDL /LOG+:"%LOGDIR%\backup_src.log"
```

> 備份建議不要用 `/MIR`，避免意外刪除目的地額外檔案。

### 2.3 同步 `app/`（主程式）

```bat
robocopy "%SRC%\app" "%DST%\app" /E /XO /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /TEE /LOG+:"%LOGDIR%\deploy_app.log" ^
  /XD __pycache__ .pytest_cache .mypy_cache .ruff_cache ^
  /XF *.pyc
```

### 2.4 同步 `scripts/`（建議：方便在 server 端驗證）

```bat
robocopy "%SRC%\scripts" "%DST%\scripts" /E /XO /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /TEE /LOG+:"%LOGDIR%\deploy_scripts.log" ^
  /XD __pycache__ .pytest_cache ^
  /XF *.pyc
```

### 2.5（選用）同步 `docs/`

```bat
robocopy "%SRC%\docs" "%DST%\docs" /E /XO /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /TEE /LOG+:"%LOGDIR%\deploy_docs.log"
```

### 2.6（選用）同步 `requirements.txt`

```bat
copy /Y "%SRC%\requirements.txt" "%DST%\requirements.txt"
```

---

## 3) Server 端重啟服務（在 Windows Server 執行）

### 3.1 使用 Service Control（常用）

```bat
sc stop care_rag_api
sc start care_rag_api
sc query care_rag_api
```

### 3.2 使用 NSSM（如果你們用 NSSM 管）

```bat
C:\nssm\nssm.exe stop care_rag_api
C:\nssm\nssm.exe start care_rag_api
```

---

## 4) 驗證清單（在 Windows Server 執行）

### 4.1 確認 port listening（常見 8002）

```bat
netstat -ano | findstr :8002
```

### 4.2 確認 API 回應

```bat
curl http://127.0.0.1:8002/api/v1/health
curl http://127.0.0.1:8002/docs
```

### 4.3 從同網段其他機器確認對外可達

- `http://172.31.6.123:8002/docs`

---

## 5) 常見錯誤與排查

### 5.1 `ModuleNotFoundError: No module named 'app'`

通常是 `AppDirectory` 沒有指到 `C:\sites\app\care_rag_api\src`。

```bat
C:\nssm\nssm.exe set care_rag_api AppDirectory "C:\sites\app\care_rag_api\src"
sc stop care_rag_api
sc start care_rag_api
```

### 5.2 Port 被占用（WinError 10048）

```bat
netstat -ano | findstr :8002
tasklist /fi "PID eq <PID>"
```

### 5.3 服務狀態看似正常但沒有在聽 port

- 看 NSSM stderr log（若有設定）
- 或直接用 `sc query care_rag_api` + `netstat` 交叉確認

