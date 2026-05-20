# Next.js + Keycloak RBAC

> **Stack:** Next.js 14 App Router · iron-session · jose · Keycloak 24 · Docker / Kubernetes (on-prem)

## Architecture

```
Browser → /api/auth/login (PKCE) → Keycloak → /api/auth/callback
→ iron-session cookie → BFF API Route (requireRoles) → Microservice
```

## Roles

| Role    | patient:read | patient:write | patient:delete | admin:all |
|---------|:---:|:---:|:---:|:---:|
| admin   | ✅ | ✅ | ✅ | ✅ |
| doctor  | ✅ | ✅ | ❌ | ❌ |
| nurse   | ✅ | ❌ | ❌ | ❌ |
| viewer  | ✅ | ❌ | ❌ | ❌ |

## Quick Start

```bash
cp .env.example .env.local
# Fill in KEYCLOAK_CLIENT_SECRET and SESSION_SECRET

docker compose up -d
```

App: http://localhost:3000  
Keycloak Admin: http://localhost:8080 (admin/admin)

## Project Structure

```
app/api/auth/          # OIDC login, callback, logout
app/api/bff/           # Role-guarded microservice proxies
lib/auth-guard.ts      # requireAuth / requireRoles
lib/session.ts         # iron-session encrypted cookie
lib/jwt-verify.ts      # JWKS remote verification (jose)
k8s/                   # Kubernetes manifests + Keycloak realm config
```

## Adding a New BFF Route

```typescript
// app/api/bff/orders/route.ts
export async function GET(req: NextRequest) {
  const { accessToken } = await requireRoles(['admin', 'doctor'])
  // proxy to upstream...
}
```

## Keycloak Group Setup

1. Keycloak Admin → Realm `hospital` → Groups
2. Create groups: `admin-group`, `doctor-group`, `nurse-group`, `viewer-group`
3. Assign realm roles to each group
4. Add users to groups → roles propagate to JWT automatically

## Deployment (K8s)

```bash
kubectl apply -f k8s/deployment.yaml
kubectl create secret generic nextjs-rbac-secrets \
  --from-literal=keycloak-client-secret=<secret> \
  --from-literal=session-secret=<32-char-secret> \
  -n hospital
```

## Design Decisions

| Decision | Rationale |
|---|---|
| `iron-session` | Encrypted httpOnly cookie; refresh_token never exposed to JS |
| Role check in BFF API Route | Middleware runs at Edge; `jose` JWKS needs Node.js runtime |
| JWKS cached via `createRemoteJWKSet` | Avoids Keycloak round-trip per request |
| Keycloak Groups → Roles | Scalable; assign user to group → roles propagate automatically |
| PKCE S256 enforced at KC client | Prevents code_challenge=plain downgrade |
