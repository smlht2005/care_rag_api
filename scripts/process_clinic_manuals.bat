@echo off
REM 批次處理衛生所操作手冊 PDF 文件
REM 建立問答知識圖譜 graph_qa.db

echo ========================================
echo 衛生所操作手冊 PDF 處理腳本
echo ========================================
echo.

REM 切換到腳本目錄
cd /d %~dp0\..

REM 執行 Python 腳本
python scripts/parse_clinic_manual_pdfs_to_qa_graph.py --pdf-dir "data/example/clinic his" --db-path "./data/graph_qa.db"

echo.
echo ========================================
echo 處理完成！
echo ========================================
echo.
echo 查詢圖譜: python scripts/query_qa_graph.py
echo 搜尋問答: python scripts/query_qa_graph.py --search "批價"
pause

