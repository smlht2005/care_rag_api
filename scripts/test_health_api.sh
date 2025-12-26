#!/bin/bash
# 健康檢查 API 測試腳本
# 更新時間：2025-12-26 17:46

echo "=========================================="
echo "Care RAG API 健康檢查測試"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

echo "1. 測試根端點 (/)"
curl -s "${BASE_URL}/" | python -m json.tool
echo ""
echo ""

echo "2. 測試健康檢查端點 (/api/v1/health)"
curl -s "${BASE_URL}/api/v1/health" | python -m json.tool
echo ""
echo ""

echo "3. 測試就緒檢查端點 (/api/v1/health/ready)"
curl -s "${BASE_URL}/api/v1/health/ready" | python -m json.tool
echo ""
echo ""

echo "4. 測試存活檢查端點 (/api/v1/health/live)"
curl -s "${BASE_URL}/api/v1/health/live" | python -m json.tool
echo ""
echo ""

echo "=========================================="
echo "測試完成"
echo "=========================================="

