export type AppRole = 'admin' | 'doctor' | 'nurse' | 'viewer'

export const ROLE_PERMISSIONS: Record<AppRole, string[]> = {
  admin:  ['patient:read', 'patient:write', 'patient:delete', 'user:manage', 'config:write', 'audit:read'],
  doctor: ['patient:read', 'patient:write', 'order:write'],
  nurse:  ['patient:read', 'vitals:write'],
  viewer: ['patient:read'],
}
