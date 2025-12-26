@echo off
REM 處理 PDF 文件並構建圖結構
REM 使用方式: scripts\process_pdf.bat [PDF路徑]

echo 處理 PDF 文件並構建圖結構...
python scripts\process_pdf_to_graph.py %*

pause


