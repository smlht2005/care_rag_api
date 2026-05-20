import { NextRequest, NextResponse } from 'next/server'
import { getSession } from '@/lib/session'
import { exchangeCodeForTokens } from '@/lib/token-exchange'
export async function GET(req: NextRequest) {
  const { searchParams } = req.nextUrl
  const code = searchParams.get('code'); const state = searchParams.get('state'); const error = searchParams.get('error')
  if (error || !code || !state) return NextResponse.redirect(new URL('/login', req.url))
  const session = await getSession()
  if (state !== session.state || !session.codeVerifier) { await session.destroy(); return NextResponse.redirect(new URL('/login', req.url)) }
  try {
    const tokens = await exchangeCodeForTokens(code, session.codeVerifier)
    const now = Math.floor(Date.now() / 1000)
    session.accessToken = tokens.access_token; session.refreshToken = tokens.refresh_token
    session.idToken = tokens.id_token; session.expiresAt = now + tokens.expires_in
    session.codeVerifier = undefined; session.state = undefined
    await session.save()
    return NextResponse.redirect(new URL('/dashboard', req.url))
  } catch (err) { console.error('[callback] token exchange error:', err instanceof Error ? err.message : 'unknown'); await session.destroy(); return NextResponse.redirect(new URL('/login', req.url)) }
}
