FROM python:3.11-slim

# 設定工作目錄
WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 複製依賴檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 複製應用程式檔案
COPY ./app ./app

# 建立資料目錄
RUN mkdir -p /app/data

# 複製預建資料庫（Graph/QA/Vector）
COPY ./data/graph_qa.db ./data/graph.db ./data/qa_vectors.db /app/data/

# 暴露端口
EXPOSE 8002 8001

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; r=httpx.get('http://127.0.0.1:8002/api/v1/health'); r.raise_for_status()" || exit 1

# 啟動命令
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8002}"]

