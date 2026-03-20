export function createId(): string {
  const c: any = (globalThis as any)?.crypto;
  if (c?.randomUUID && typeof c.randomUUID === "function") {
    return c.randomUUID();
  }

  // Fallback: 충분唯一성(세션 범위)용. 보안 목적 아님.
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

