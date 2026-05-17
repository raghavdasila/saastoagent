export type AuthIntent = 'login' | 'register'
export type AuthStep = 'intent' | 'display_name' | 'email' | 'password' | 'done'
export type SaaSAgentLaunchStep = 'ask_job' | 'confirm' | 'done'

export const PRODUCT_NAME = 'SaaSToAgent'
export const OPERATOR_NAME = 'Corpus'
export const PRODUCT_MONOGRAM = 'STA'

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

export function normalizeSaaSAgentName(value: string): string {
  const cleaned = value
    .replace(/^(create|launch|make|start|open)\s+/i, '')
    .replace(/^(i\s+(want|need)\s+)?(it|this operator|the operator)\s+(will|should|can|needs to|is going to|to)\s+/i, '')
    .replace(/^(talk|speak|connect)\s+(to|with)\s+my\s+/i, 'my ')
    .replace(/\s+/g, ' ')
    .trim()

  if (!cleaned) {
    return ''
  }

  if (/^(my\s+)?(saas|app|application|platform|product)$/i.test(cleaned)) {
    return 'SaaS Operations SaaS Agent'
  }

  const titled = cleaned
    .split(' ')
    .map((part) => {
      const lowered = part.toLowerCase()
      if (lowered === 'saas') return 'SaaS'
      if (lowered === 'api') return 'API'
      if (['crm', 'erp'].includes(lowered)) return lowered.toUpperCase()
      return part ? part[0].toUpperCase() + part.slice(1) : part
    })
    .join(' ')

  if (/(saas agent|operator)$/i.test(titled)) {
    return titled.slice(0, 80)
  }

  return `${titled} SaaS Agent`.slice(0, 80)
}

export function formatSaaSAgentDisplayName(value?: string | null): string {
  const trimmed = value?.trim().replace(/\s+/g, ' ') ?? ''
  if (!trimmed) {
    return ''
  }

  const legacyPrefixes = [
    `${PRODUCT_NAME} Operator - `,
    `${PRODUCT_NAME} Operator: `,
    `${PRODUCT_NAME} Operator | `,
    `${PRODUCT_NAME} - `,
    `${PRODUCT_NAME}: `,
    `${PRODUCT_NAME} | `,
    `${OPERATOR_NAME} Operator - `,
    `${OPERATOR_NAME} Operator: `,
    `${OPERATOR_NAME} Operator | `,
    `${OPERATOR_NAME} - `,
    `${OPERATOR_NAME}: `,
    `${OPERATOR_NAME} | `,
  ]

  const legacyPrefix = legacyPrefixes.find((prefix) =>
    trimmed.toLowerCase().startsWith(prefix.toLowerCase()),
  )
  const withoutLegacyPrefix = legacyPrefix ? trimmed.slice(legacyPrefix.length).trim() : trimmed

  if (
    /^(?:i\s+(?:want|need)\s+)?(?:it|this operator|the operator)\s+(?:will|should|can|needs to|is going to|to)\s+/i.test(withoutLegacyPrefix) ||
    /^(?:talk|speak|connect)\s+(?:to|with)\s+my\s+/i.test(withoutLegacyPrefix) ||
    /^(?:my\s+)?(?:saas|app|application|platform|product)$/i.test(withoutLegacyPrefix)
  ) {
    return normalizeSaaSAgentName(withoutLegacyPrefix)
  }

  return withoutLegacyPrefix
}
