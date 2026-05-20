import type { Metadata } from 'next'
export const metadata: Metadata = { title: 'HIS RBAC', description: 'Hospital Information System' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return <html lang="zh-TW"><body>{children}</body></html>
}
