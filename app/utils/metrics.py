"""
Prometheus 指標監控
"""
from prometheus_client import Counter, Histogram, Gauge, start_http_server
from app.config import settings
import logging

logger = logging.getLogger("Metrics")

# 請求指標
REQUEST_COUNTER = Counter(
    "care_rag_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"]
)

REQUEST_LATENCY = Histogram(
    "care_rag_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"]
)

# 查詢指標
QUERY_COUNTER = Counter(
    "care_rag_queries_total",
    "Total number of queries",
    ["provider", "status"]
)

QUERY_LATENCY = Histogram(
    "care_rag_query_latency_seconds",
    "Query latency in seconds",
    ["provider"]
)

# 快取指標
CACHE_HITS = Counter("care_rag_cache_hits_total", "Total cache hits")
CACHE_MISSES = Counter("care_rag_cache_misses_total", "Total cache misses")

# WebSocket 指標
WEBSOCKET_CONNECTIONS = Gauge(
    "care_rag_websocket_connections",
    "Current number of WebSocket connections"
)

# 文件指標
DOCUMENTS_TOTAL = Gauge(
    "care_rag_documents_total",
    "Total number of documents in vector store"
)

def init_metrics_server(port: int = None):
    """初始化 Prometheus 指標伺服器"""
    port = port or settings.METRICS_PORT
    try:
        start_http_server(port)
        logger.info(f"Prometheus metrics server started on port {port}")
        logger.info(f"Metrics available at http://localhost:{port}/metrics")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {str(e)}")
        raise

