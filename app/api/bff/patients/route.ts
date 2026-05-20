import { NextRequest, NextResponse } from 'next/server'
import { requireRoles } from '@/lib/auth-guard'
const UPSTREAM = process.env.PATIENT_SERVICE_URL!
export async function GET(req: NextRequest) {
  const { accessToken } = await requireRoles(['admin', 'doctor', 'nurse', 'viewer'])
  const upstream = new URL('/patients', UPSTREAM); upstream.search = req.nextUrl.search
  const res = await fetch(upstream, { headers: { Authorization: `Bearer ${accessToken}` } })
  return NextResponse.json(await res.json(), { status: res.status })
}
export async function POST(req: NextRequest) {
  const { accessToken } = await requireRoles(['admin', 'doctor'])
  const res = await fetch(new URL('/patients', UPSTREAM), { method: 'POST', headers: { Authorization: `Bearer ${accessToken}`, 'Content-Type': 'application/json' }, body: JSON.stringify(await req.json()) })
  return NextResponse.json(await res.json(), { status: res.status })
}
export async function DELETE(req: NextRequest) {
  const { accessToken } = await requireRoles(['admin'])
  const id = req.nextUrl.searchParams.get('id')
  const res = await fetch(new URL(`/patients/${id}`, UPSTREAM), { method: 'DELETE', headers: { Authorization: `Bearer ${accessToken}` } })
  return NextResponse.json(await res.json(), { status: res.status })
}
