export default function UnauthorizedPage() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h1>
        <p className="text-gray-600 mb-4">Insufficient role permissions.</p>
        <a href="/dashboard" className="text-blue-600 underline">Back to Dashboard</a>
      </div>
    </main>
  )
}
