export const keycloakConfig = {
  url:          process.env.KEYCLOAK_URL!,
  realm:        process.env.KEYCLOAK_REALM!,
  clientId:     process.env.KEYCLOAK_CLIENT_ID!,
  clientSecret: process.env.KEYCLOAK_CLIENT_SECRET!,
  redirectUri:  `${process.env.NEXTJS_URL}/api/auth/callback`,
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
