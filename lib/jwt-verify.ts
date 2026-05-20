import { createRemoteJWKSet, jwtVerify, JWTPayload } from 'jose'
import { keycloakConfig, keycloakUrls } from './keycloak-config'
const JWKS = createRemoteJWKSet(new URL(keycloakUrls.jwksUri))
export interface KeycloakJWTPayload extends JWTPayload {
  realm_access?: { roles: string[] }
  preferred_username?: string
  email?: string
  name?: string
}
export async function verifyAccessToken(token: string): Promise<KeycloakJWTPayload> {
  const { payload } = await jwtVerify(token, JWKS, {
    issuer:   keycloakUrls.issuer,
    audience: keycloakConfig.clientId,
  })
  return payload as KeycloakJWTPayload
}
