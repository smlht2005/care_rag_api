import { redirect } from 'next/navigation'
import { getSession } from '@/lib/session'
export default async function ProtectedLayout({ children }: { children: React.ReactNode }) {
  const session = await getSession()
  if (!session.accessToken) redirect('/login')
  return <>{children}</>
}
