import { getIronSession, IronSession } from 'iron-session'
import { cookies } from 'next/headers'
export interface SessionData {
  accessToken?:  string
  refreshToken?: string
  idToken?:      string
  expiresAt?:    number
  codeVerifier?: string
  state?:        string
}
const sessionOptions = {
  password:    process.env.SESSION_SECRET!,
  cookieName:  'hospital_session',
  cookieOptions: {
    secure:   true,
    httpOnly: true,
    sameSite: 'strict' as const,
    maxAge:   60 * 60,
  },
}
export async function getSession(): Promise<IronSession<SessionData>> {
  const cookieStore = await cookies()
  return getIronSession<SessionData>(cookieStore, sessionOptions)
}
