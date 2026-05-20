import { NextRequest, NextResponse } from 'next/server'
const PUBLIC_PATHS  = new Set(['/login', '/unauthorized', '/favicon.ico'])
const PUBLIC_PREFIX = ['/api/auth/', '/_next/']
export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl
  if (PUBLIC_PATHS.has(pathname) || PUBLIC_PREFIX.some(p => pathname.startsWith(p))) return NextResponse.next()
  if (!req.cookies.has('hospital_session')) return NextResponse.redirect(new URL('/api/auth/login', req.url))
  return NextResponse.next()
}
export const config = { matcher: ['/((?!_next/static|_next/image|favicon\\.ico).*)'] }
