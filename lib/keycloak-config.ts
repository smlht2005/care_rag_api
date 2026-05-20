function requireEnv(name: string): string {
  const val = process.env[name]
  if (!val) throw new Error(`Missing required environment variable: ${name}`)
  return val
}

export const keycloakConfig = {
  url:          requireEnv('KEYCLOAK_URL'),
  realm:        requireEnv('KEYCLOAK_REALM'),
  clientId:     requireEnv('KEYCLOAK_CLIENT_ID'),
  clientSecret: requireEnv('KEYCLOAK_CLIENT_SECRET'),
  redirectUri:  `${requireEnv('NEXTJS_URL')}/api/auth/callback`,
}
const base = `${keycloakConfig.url}/realms/${keycloakConfig.realm}/protocol/openid-connect`
export const keycloakUrls = {
  authEndpoint:     `${base}/auth`,
  tokenEndpoint:    `${base}/token`,
  logoutEndpoint:   `${base}/logout`,
  jwksUri:          `${base}/certs`,
  userInfoEndpoint: `${base}/userinfo`,
  issuer:           `${keycloakConfig.url}/realms/${keycloakConfig.realm}`,
}
