import { requireRoles } from '@/lib/auth-guard'
export default async function AdminPage() {
  await requireRoles(['admin'])
  return (
    <main className="p-8">
      <h1 className="text-2xl font-bold">Admin Panel</h1>
    </main>
  )
}
