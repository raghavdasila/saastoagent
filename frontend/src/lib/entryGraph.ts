export type AuthIntent = 'login' | 'register'
export type AuthStep = 'intent' | 'display_name' | 'email' | 'password' | 'done'
export type WorkspaceLaunchStep = 'ask_job' | 'confirm' | 'done'

export function detectAuthIntent(value: string): AuthIntent | null {
  const normalized = value.trim().toLowerCase()
  if (!normalized) return null

  if (
    /\b(sign\s?in|log\s?in|login|access|enter)\b/.test(normalized) &&
    !/\b(sign\s?up|register|create account|new account)\b/.test(normalized)
  ) {
    return 'login'
  }

  if (/\b(sign\s?up|register|create account|new account|join)\b/.test(normalized)) {
    return 'register'
  }

  return null
}

export function wantsSkip(value: string): boolean {
  return /^(skip|none|no name|anonymous|without one)$/i.test(value.trim())
}

export function wantsConfirm(value: string): boolean {
  return /^(launch|create|yes|y|go|continue|ship|open|do it)$/i.test(value.trim())
}

export function isValidEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value.trim())
}

export function toSlug(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .trim()
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
}

const OPERATOR_PREFIX = 'SaaSToAgent Operator'

export function normalizeWorkspaceName(value: string): string {
  const cleaned = value
    .replace(/^(create|launch|make|start|open)\s+/i, '')
    .replace(/\s+/g, ' ')
    .trim()

  if (!cleaned) {
    return ''
  }

  const titled = cleaned
    .split(' ')
    .map((part) => (part ? part[0].toUpperCase() + part.slice(1) : part))
    .join(' ')

  if (new RegExp(OPERATOR_PREFIX, 'i').test(titled)) {
    return titled.slice(0, 80)
  }

  return `${OPERATOR_PREFIX} - ${titled}`.slice(0, 80)
}