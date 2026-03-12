@echo off
REM 批次匯入 QA Markdown 檔案到乾淨的資料庫
REM 只包含 QA Markdown 資料，不包含其他混雜資料

echo ========================================
echo 批次匯入 QA Markdown 檔案
echo ========================================
echo.

REM 設定編碼
set PYTHONIOENCODING=utf-8

REM 執行批次匯入
python scripts/import_qa_markdown_batch.py --qa-dir docs/example/qa

echo.
echo ========================================
echo 匯入完成！
echo ========================================
echo.
echo 可以使用以下命令測試:
echo   python scripts/test_qa_import.py --list-docs
echo   python scripts/query_qa_graph.py
echo.
pause
