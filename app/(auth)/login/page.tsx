export default function LoginPage() {
  return (
    <main className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">Hospital Information System</h1>
        <a href="/api/auth/login" className="rounded bg-blue-600 px-6 py-2 text-white hover:bg-blue-700">
          Sign in with Keycloak
        </a>
      </div>
    </main>
  )
}
