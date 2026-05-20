import { requireAuth } from '@/lib/auth-guard'
export default async function DashboardPage() {
  const { username, roles } = await requireAuth()
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Welcome, {username}</h1>
      <p className="mt-2 text-gray-600">Roles: {roles.join(', ')}</p>
    </main>
  )
}
