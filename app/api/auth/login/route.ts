import { NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { generateCodeVerifier, generateCodeChallenge, generateState } from '@/lib/pkce'
import { keycloakConfig, keycloakUrls } from '@/lib/keycloak-config'
export async function GET() {
  const session = await getSession()
  const codeVerifier = generateCodeVerifier()
  const codeChallenge = generateCodeChallenge(codeVerifier)
  const state = generateState()
  session.codeVerifier = codeVerifier; session.state = state
  await session.save()
  const params = new URLSearchParams({ response_type: 'code', client_id: keycloakConfig.clientId, redirect_uri: keycloakConfig.redirectUri, scope: 'openid profile email', state, code_challenge: codeChallenge, code_challenge_method: 'S256' })
  return NextResponse.redirect(`${keycloakUrls.authEndpoint}?${params}`)
}
