export type AppRole = 'admin' | 'doctor' | 'nurse' | 'viewer'

export const ROLE_PERMISSIONS: Record<AppRole, string[]> = {
  admin:  ['patient:read', 'patient:write', 'patient:delete', 'admin:all'],
  doctor: ['patient:read', 'patient:write', 'order:write'],
  nurse:  ['patient:read', 'vitals:write'],
  viewer: ['patient:read'],
}
