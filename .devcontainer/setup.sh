#!/bin/sh
set -e

echo "=================================================="
echo " 開發環境初始化中..."
echo "=================================================="

# ── 偵測執行環境 ──────────────────────────────────────
if [ -n "$CODESPACE_NAME" ] && [ -n "$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN" ]; then
  KEYCLOAK_URL="https://${CODESPACE_NAME}-8080.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  NEXTJS_URL="https://${CODESPACE_NAME}-3000.${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN}"
  echo "✅ GitHub Codespaces 環境偵測成功"
  echo "   Next.js  : $NEXTJS_URL"
  echo "   Keycloak : $KEYCLOAK_URL"
else
  KEYCLOAK_URL="http://localhost:8080"
  NEXTJS_URL="http://localhost:3000"
  echo "ℹ️  本機開發環境"
fi

# ── 產生隨機 SESSION_SECRET ───────────────────────────
SESSION_SECRET=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")

# ── 建立 .env.local ───────────────────────────────────
cat > /workspace/.env.local << EOF
# ── Keycloak ──────────────────────────────────────────
KEYCLOAK_URL=${KEYCLOAK_URL}
KEYCLOAK_REALM=hospital
KEYCLOAK_CLIENT_ID=nextjs-bff
# 開發用固定密鑰，與 keycloak-realm-config.dev.json 一致
KEYCLOAK_CLIENT_SECRET=dev-secret-not-for-production

# ── Next.js ───────────────────────────────────────────
NEXTJS_URL=${NEXTJS_URL}
SESSION_SECRET=${SESSION_SECRET}

# ── 上游微服務（開發時可用 mock 或留空）──────────────
PATIENT_SERVICE_URL=http://localhost:8081
ADMIN_SERVICE_URL=http://localhost:8082
EOF

echo "✅ .env.local 建立完成"

# ── 安裝 npm 套件 ─────────────────────────────────────
echo "📦 安裝 npm 套件中..."
cd /workspace && npm install
echo "✅ npm install 完成"

# ── 完成訊息 ──────────────────────────────────────────
echo ""
echo "=================================================="
echo " 環境初始化完成！"
echo ""
echo " 🌐 應用程式  : $NEXTJS_URL"
echo " 🔐 Keycloak  : ${KEYCLOAK_URL}/admin"
echo "    帳號      : admin"
echo "    密碼      : devpassword123"
echo ""
echo " ⚠️  Keycloak 需約 30~60 秒完成啟動"
echo "    確認指令  : docker logs -f <keycloak-container>"
echo ""
echo " ▶️  開發伺服器將自動啟動（postStartCommand）"
echo "    或手動執行 : npm run dev"
echo "=================================================="
