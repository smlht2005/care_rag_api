@echo off
REM 從 care_rag_api 目錄啟動 API，避免從錯誤目錄啟動導致 GET / 與 POST /api/v1/query 回 404
REM 更新時間：2026-03-09
cd /d "%~dp0.."
echo Starting Care RAG API from: %CD%
uvicorn app.main:app --host 0.0.0.0 --port 8000
