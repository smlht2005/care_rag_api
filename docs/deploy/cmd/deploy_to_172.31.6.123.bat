@echo off
setlocal enabledelayedexpansion

REM ============================================================
REM 更新時間：2026-04-01 15:05
REM 作者：AI Assistant
REM 修改摘要：以 robocopy 備份並同步 care_rag_api 原始碼到 \\172.31.6.123\c$\sites\app\care_rag_api\src
REM ============================================================

REM ---- 基本參數（可自行調整） ----
set "SERVER=172.31.6.123"
set "DST=\\%SERVER%\c$\sites\app\care_rag_api\src"

REM 來源：此 .bat 所在位置為 docs\deploy\cmd\
REM 往上回到 repo 根目錄：docs\deploy\cmd\..\..\.. = repo root
set "REPO_ROOT=%~dp0..\..\.."
for %%I in ("%REPO_ROOT%") do set "REPO_ROOT=%%~fI"

set "SRC=%REPO_ROOT%"
set "LOGDIR=%REPO_ROOT%\logs_deploy"

REM 備份目的地：在 server 上同層建立 src_backup_YYYYMMDD_HHMMSS
REM 產生時間戳（YYYYMMDD_HHMMSS）：使用 WMIC，避免 %date% 受語系影響
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value 2^>nul') do set "ldt=%%I"
if not defined ldt (
  echo [ERROR] WMIC 無法取得時間戳，請確認系統允許 wmic 或改用手動 BKP 名稱。
  exit /b 1
)
set "TS=%ldt:~0,8%_%ldt:~8,6%"
set "BKP=\\%SERVER%\c$\sites\app\care_rag_api\src_backup_%TS%"

REM ---- 顯示關鍵資訊 ----
echo.
echo === Deploy care_rag_api source via robocopy ===
echo SRC      = "%SRC%"
echo DST      = "%DST%"
echo BKP      = "%BKP%"
echo LOGDIR   = "%LOGDIR%"
echo (Windows cmd timestamp) %date% %time%
echo.

REM ---- 檢查必要路徑 ----
if not exist "%SRC%\app\" (
  echo [ERROR] 找不到來源 "%SRC%\app\"。請確認你是從 repo 內執行此 .bat。
  exit /b 1
)

if not exist "%LOGDIR%\" (
  mkdir "%LOGDIR%" >nul 2>&1
)

REM ---- 檢查目的地可達 ----
if not exist "%DST%\" (
  echo [ERROR] 找不到目的地 "%DST%\"。
  echo - 若需要帳密：先執行 net use \\%SERVER%\c$ /user:... *
  echo - 或確認 server 路徑 C:\sites\app\care_rag_api\src 是否存在
  exit /b 1
)

REM ============================================================
REM Step 1) 先備份目的地（不使用 /MIR，避免誤刪）
REM ============================================================
echo.
echo [1/3] Backup destination src -> "%BKP%"
robocopy "%DST%" "%BKP%" /E /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /NFL /NDL /LOG+:"%LOGDIR%\backup_src_%TS%.log"
set "RC=!ERRORLEVEL!"
if !RC! GEQ 8 (
  echo [ERROR] 備份失敗（robocopy exit code=!RC!）。請查看 log："%LOGDIR%\backup_src_%TS%.log"
  exit /b !RC!
)

REM ============================================================
REM Step 2) 同步 app/
REM ============================================================
echo.
echo [2/3] Deploy app/ -> "%DST%\app"
robocopy "%SRC%\app" "%DST%\app" /E /XO /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /TEE /LOG+:"%LOGDIR%\deploy_app_%TS%.log" ^
  /XD __pycache__ .pytest_cache .mypy_cache .ruff_cache ^
  /XF *.pyc
set "RC=!ERRORLEVEL!"
if !RC! GEQ 8 (
  echo [ERROR] 同步 app/ 失敗（robocopy exit code=!RC!）。請查看 log："%LOGDIR%\deploy_app_%TS%.log"
  exit /b !RC!
)

REM ============================================================
REM Step 3) 同步 scripts/（建議）
REM ============================================================
echo.
echo [3/3] Deploy scripts/ -> "%DST%\scripts"
if exist "%SRC%\scripts\" (
  robocopy "%SRC%\scripts" "%DST%\scripts" /E /XO /COPY:DAT /DCOPY:DAT /R:2 /W:2 /Z /NP /TEE /LOG+:"%LOGDIR%\deploy_scripts_%TS%.log" ^
    /XD __pycache__ .pytest_cache ^
    /XF *.pyc
  set "RC=!ERRORLEVEL!"
  if !RC! GEQ 8 (
    echo [ERROR] 同步 scripts/ 失敗（robocopy exit code=!RC!）。請查看 log："%LOGDIR%\deploy_scripts_%TS%.log"
    exit /b !RC!
  )
) else (
  echo [WARN] 來源沒有 scripts/，略過。
)

echo.
echo [OK] 檔案同步完成。
echo.
echo === Next steps (run on Windows Server) ===
echo - Restart service:
echo     sc stop care_rag_api ^& sc start care_rag_api ^& sc query care_rag_api
echo - Verify:
echo     netstat -ano ^| findstr :8002
echo     curl http://127.0.0.1:8002/api/v1/health
echo     curl http://127.0.0.1:8002/docs
echo.

exit /b 0

