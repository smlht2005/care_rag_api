@echo off
REM Care RAG API - 一鍵建立 ZIP 打包腳本 (Windows Batch)
REM 使用方式: scripts\create_zip.bat

echo 正在建立 ZIP 打包檔案...
powershell -ExecutionPolicy Bypass -File "%~dp0create_zip.ps1"
pause


