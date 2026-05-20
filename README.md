# Next.js + Keycloak 角色存取控制（RBAC）

> **技術棧：** Next.js 14 App Router · iron-session · jose · Keycloak 24 · Docker / Kubernetes（地端部署）

## 系統架構

```
瀏覽器 → /api/auth/login（PKCE）→ Keycloak → /api/auth/callback
       → iron-session Cookie → BFF API Route（requireRoles）→ 微服務
```

驗證流程採用 **PKCE S256** 授權碼流程，存取令牌（Access Token）與更新令牌（Refresh Token）皆儲存於加密的 httpOnly Cookie 中，永不暴露給前端 JavaScript。

## 角色與權限對照表

| 角色    | patient:read | patient:write | patient:delete | user:manage | config:write | audit:read |
|---------|:---:|:---:|:---:|:---:|:---:|:---:|
| admin   | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| doctor  | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| nurse   | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| viewer  | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |

## 快速開始

### 1. 設定環境變數

```bash
cp .env.example .env.local
```

開啟 `.env.local`，填入以下必要欄位：

| 變數 | 說明 |
|---|---|
| `KEYCLOAK_CLIENT_SECRET` | 從 Keycloak Admin 取得的用戶端密鑰 |
| `SESSION_SECRET` | 至少 32 字元的隨機字串（用於加密 Cookie） |
| `POSTGRES_PASSWORD` | PostgreSQL 資料庫密碼 |
| `KEYCLOAK_ADMIN_PASSWORD` | Keycloak 管理員密碼 |

產生安全的 SESSION_SECRET：
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

### 2. 啟動服務

```bash
docker compose up -d
```

| 服務 | 網址 |
|---|---|
| 應用程式 | http://localhost:3000 |
| Keycloak 管理後台 | http://localhost:8080 |

### 3. 安裝相依套件（本機開發）

```bash
npm install
npm run dev
```

## 專案結構

```
.
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx          # 登入頁面
│   │   └── unauthorized/page.tsx   # 無權限頁面
│   ├── (protected)/
│   │   ├── layout.tsx              # 受保護路由的版型（驗證守衛）
│   │   ├── dashboard/page.tsx      # 儀表板（所有已登入用戶）
│   │   └── admin/page.tsx          # 管理員頁面（限 admin 角色）
│   ├── api/
│   │   ├── auth/
│   │   │   ├── login/route.ts      # 發起 PKCE 授權碼流程
│   │   │   ├── callback/route.ts   # Keycloak 回調處理
│   │   │   └── logout/route.ts     # 登出並清除 Session
│   │   └── bff/
│   │       ├── patients/route.ts   # 病患服務代理（含角色驗證）
│   │       └── admin/route.ts      # 管理服務代理（限 admin）
│   └── layout.tsx                  # 根版型
├── lib/
│   ├── auth-guard.ts               # requireAuth / requireRoles 守衛函數
│   ├── jwt-verify.ts               # 使用 JWKS 遠端驗證 JWT
│   ├── keycloak-config.ts          # Keycloak 設定與端點 URL
│   ├── pkce.ts                     # PKCE code_verifier / code_challenge 產生
│   ├── session.ts                  # iron-session 加密 Cookie 設定
│   └── token-exchange.ts           # 授權碼換取令牌 / 更新令牌
├── types/
│   └── auth.ts                     # AppRole 型別與權限對照表
├── k8s/
│   ├── deployment.yaml             # Kubernetes 部署、Service、Ingress、HPA、PDB
│   └── keycloak-realm-config.json  # Keycloak Realm 匯入設定
├── Dockerfile                      # 多階段 Docker 建置（非 root 用戶）
├── docker-compose.yml              # 本地開發環境（PostgreSQL + Keycloak + Next.js）
└── .env.example                    # 環境變數範本
```

## Keycloak 群組設定

1. 進入 **Keycloak Admin** → 選擇 Realm `hospital` → **Groups**
2. 建立以下群組：

   | 群組名稱 | 對應角色 |
   |---|---|
   | `admin-group`  | admin  |
   | `doctor-group` | doctor |
   | `nurse-group`  | nurse  |
   | `viewer-group` | viewer |

3. 將 Realm 角色指派給對應群組
4. 將用戶加入群組 → 角色自動傳播至 JWT `realm_access.roles`

## 新增 BFF 路由

```typescript
// app/api/bff/orders/route.ts
import { NextRequest, NextResponse } from 'next/server'
import { requireRoles } from '@/lib/auth-guard'

const UPSTREAM = process.env.ORDER_SERVICE_URL!

export async function GET(req: NextRequest) {
  // 只允許 admin 與 doctor 存取
  const { accessToken } = await requireRoles(['admin', 'doctor'])

  const res = await fetch(new URL('/orders', UPSTREAM), {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return NextResponse.json(await res.json(), { status: res.status })
}
```

## Kubernetes 部署

```bash
# 建立 Namespace 與 Secret
kubectl create secret generic nextjs-rbac-secrets \
  --from-literal=keycloak-client-secret=<從-Keycloak-Admin-取得> \
  --from-literal=session-secret=<至少32字元的隨機字串> \
  -n hospital

# 部署所有資源（Deployment、Service、Ingress、HPA、PDB）
kubectl apply -f k8s/deployment.yaml

# 確認部署狀態
kubectl rollout status deployment/nextjs-rbac -n hospital
```

> **注意：** `k8s/deployment.yaml` 中的映像檔標籤為 `v1.0.0`，請在 CI/CD 流程中替換為實際版本號。

## 安全設計決策

| 決策 | 理由 |
|---|---|
| `iron-session` 加密 Cookie | `refresh_token` 永不暴露給前端 JS；httpOnly + Secure + SameSite=Strict 防禦 XSS 與 CSRF |
| 角色驗證在 BFF API Route | Middleware 執行於 Edge Runtime；jose JWKS 驗證需要 Node.js Runtime |
| `createRemoteJWKSet` 快取 | 避免每次請求都向 Keycloak 查詢公鑰，降低延遲 |
| Keycloak Groups → Roles | 可擴展性高；將用戶加入群組即可自動取得角色，無需逐一設定 |
| PKCE S256 強制啟用 | 防止 `code_challenge_method=plain` 降級攻擊 |
| JWT Audience 驗證 | 確保令牌只對本應用程式有效，拒絕其他用戶端簽發的令牌 |
| 令牌刷新後重新驗證 | 刷新後立即驗證新令牌簽章，防止惡意端點注入偽造令牌 |
| 非 root 容器用戶 | Dockerfile 建立 `nextjs`（uid 1001）用戶，遵循最小權限原則 |

## 環境變數說明

| 變數 | 必填 | 說明 |
|---|:---:|---|
| `KEYCLOAK_URL` | ✅ | Keycloak 伺服器位址（例：`https://keycloak.hospital.internal`） |
| `KEYCLOAK_REALM` | ✅ | Realm 名稱（例：`hospital`） |
| `KEYCLOAK_CLIENT_ID` | ✅ | 用戶端 ID（例：`nextjs-bff`） |
| `KEYCLOAK_CLIENT_SECRET` | ✅ | 用戶端密鑰（從 Keycloak Admin 取得） |
| `NEXTJS_URL` | ✅ | 應用程式對外網址（例：`https://his.hospital.internal`） |
| `SESSION_SECRET` | ✅ | Cookie 加密金鑰（最少 32 字元隨機字串） |
| `PATIENT_SERVICE_URL` | ✅ | 病患微服務內部位址 |
| `ADMIN_SERVICE_URL` | ✅ | 管理微服務內部位址 |
| `POSTGRES_PASSWORD` | ✅ | PostgreSQL 密碼（Docker Compose 使用） |
| `KEYCLOAK_ADMIN_PASSWORD` | ✅ | Keycloak 管理員密碼（Docker Compose 使用） |
