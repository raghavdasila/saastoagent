import {
  Bot,
  Brain,
  Database,
  FileSearch,
  FlaskConical,
  GitBranch,
  LogIn,
  MessageSquareText,
  Paperclip,
  PlugZap,
  Shield,
  UserPlus,
  type LucideIcon,
} from 'lucide-react'

import type { WorkspaceView } from '@/stores/workspaceStore'
import type { EntryActionCard, OperatorExperienceMode, OperatorSidebarItem } from '@/types/entry'
import type { WorkspaceStats } from '@/types/domain'

export type CapabilityState = 'ready' | 'needs_setup' | 'locked' | 'running' | 'needs_approval' | 'has_findings'

export interface OperatorCapabilityDefinition {
  id: OperatorSidebarItem
  mode: OperatorExperienceMode
  workspaceView?: WorkspaceView
  label: string
  shortLabel: string
  description: string
  icon: LucideIcon
  actionId?: string
  authRequired?: boolean
  enabled: boolean
  emptyState: string
  failureState: string
  evidenceSurface: string
}

export interface CapabilityRuntimeContext {
  busy: boolean
  hasWorkspace: boolean
  isAuthenticated: boolean
  stats?: WorkspaceStats
  operatorError?: string | null
}

export const entryCapabilities: OperatorCapabilityDefinition[] = [
  {
    id: 'chat',
    mode: 'entry',
    label: 'Intent Spine',
    shortLabel: 'Chat',
    description: 'Ask questions, describe the job, or continue setup.',
    icon: MessageSquareText,
    enabled: true,
    emptyState: 'Start by describing the SaaS job this operator should own.',
    failureState: 'Entry stream failed or is waiting for a valid graph response.',
    evidenceSurface: 'Entry graph stage, selected action, and setup draft.',
  },
  {
    id: 'learn',
    mode: 'entry',
    label: 'Platform Lens',
    shortLabel: 'Learn',
    description: 'Understand what SaaStoAgent can operate and where the boundaries are.',
    icon: Brain,
    actionId: 'entry.learn.platform',
    enabled: true,
    emptyState: 'Ask a platform question to populate this lens.',
    failureState: 'Platform answer is unavailable; use the chat spine to retry.',
    evidenceSurface: 'Platform citations and overview widgets.',
  },
  {
    id: 'setup',
    mode: 'entry',
    label: 'Setup Draft',
    shortLabel: 'Setup',
    description: 'Capture the workspace job and REST API details before auth.',
    icon: Database,
    actionId: 'entry.learn.setup',
    enabled: true,
    emptyState: 'Describe the API or product you want this operator to run.',
    failureState: 'Setup draft is incomplete or needs user correction.',
    evidenceSurface: 'Draft workspace job, API fields, and setup checklist.',
  },
  {
    id: 'signin',
    mode: 'entry',
    label: 'Sign In',
    shortLabel: 'Sign In',
    description: 'Authenticate without leaving the operator shell.',
    icon: LogIn,
    actionId: 'intent.sign_in',
    enabled: true,
    emptyState: 'Use when an existing account should own the workspace.',
    failureState: 'Authentication failed; deterministic auth stages own retry.',
    evidenceSurface: 'Auth stage and masked credential events.',
  },
  {
    id: 'register',
    mode: 'entry',
    label: 'Create Account',
    shortLabel: 'Create',
    description: 'Create an account while preserving the setup draft.',
    icon: UserPlus,
    actionId: 'intent.register',
    enabled: true,
    emptyState: 'Use when a new workspace owner should be created.',
    failureState: 'Registration failed; deterministic auth stages own retry.',
    evidenceSurface: 'Auth stage and preserved entry draft.',
  },
]

export const workspaceCapabilities: OperatorCapabilityDefinition[] = [
  {
    id: 'chat',
    mode: 'operator',
    workspaceView: 'chat',
    label: 'Intent Spine',
    shortLabel: 'Chat',
    description: 'Primary work direction surface for this operator.',
    icon: MessageSquareText,
    enabled: true,
    emptyState: 'Ask what the operator can do or what should be set up next.',
    failureState: 'Workspace chat stream failed or is waiting for recovery.',
    evidenceSurface: 'Agent session, handoff context, tool calls, and citations.',
  },
  {
    id: 'connect',
    mode: 'operator',
    workspaceView: 'connect',
    label: 'Connections',
    shortLabel: 'Connect',
    description: 'REST setup, activation, and readiness.',
    icon: PlugZap,
    enabled: true,
    emptyState: 'Connect the first REST API before action execution can be useful.',
    failureState: 'Connection activation failed or needs corrected REST details.',
    evidenceSurface: 'Connection draft, activation state, generated tools, and provider metadata.',
  },
  {
    id: 'attachments',
    mode: 'operator',
    workspaceView: 'attachments',
    label: 'Knowledge Base',
    shortLabel: 'Knowledge',
    description: 'Workspace documents and searchable context.',
    icon: Paperclip,
    authRequired: true,
    enabled: true,
    emptyState: 'Upload reference files when the operator needs private context.',
    failureState: 'Document upload or embedding failed.',
    evidenceSurface: 'Documents, chunks, embeddings, and source citations.',
  },
  {
    id: 'admin',
    mode: 'operator',
    workspaceView: 'admin',
    label: 'Sessions & Memory',
    shortLabel: 'Sessions',
    description: 'Inspect conversations, memories, and admin evidence.',
    icon: Shield,
    authRequired: true,
    enabled: true,
    emptyState: 'Sessions and memories appear after the operator is used.',
    failureState: 'Admin access is missing or session evidence could not load.',
    evidenceSurface: 'Session messages, memories, document chunks, and stats.',
  },
  {
    id: 'entities',
    mode: 'operator',
    workspaceView: 'entities',
    label: 'Entities',
    shortLabel: 'Entities',
    description: 'REST entity understanding from activated APIs.',
    icon: GitBranch,
    enabled: false,
    emptyState: 'Entities unlock after REST activation and inference.',
    failureState: 'Entity inference is not available yet.',
    evidenceSurface: 'Entity candidates, source schema, and action paths.',
  },
  {
    id: 'actions',
    mode: 'operator',
    workspaceView: 'actions',
    label: 'Actions',
    shortLabel: 'Actions',
    description: 'Generated REST action tools and execution readiness.',
    icon: Bot,
    enabled: false,
    emptyState: 'Actions unlock after generated tool binding.',
    failureState: 'No generated tools are bound to chat execution yet.',
    evidenceSurface: 'Tool candidates, parameters, risks, approvals, and execution trace.',
  },
  {
    id: 'qa',
    mode: 'operator',
    workspaceView: 'qa',
    label: 'QA & Learnings',
    shortLabel: 'QA',
    description: 'Failure capture, evaluation, tuning, and governed learnings.',
    icon: FlaskConical,
    enabled: false,
    emptyState: 'QA unlocks after execution is available.',
    failureState: 'QA cannot run until the operator can execute REST workflows.',
    evidenceSurface: 'Runs, failures, tuning candidates, approvals, and saved learnings.',
  },
]

export function capabilityStateFor(definition: OperatorCapabilityDefinition, context: CapabilityRuntimeContext): CapabilityState {
  if (context.busy && definition.id === 'chat') return 'running'
  if (context.operatorError && definition.id === 'chat') return 'has_findings'
  if (definition.mode === 'operator' && !context.hasWorkspace) return 'locked'
  if (definition.authRequired && !context.isAuthenticated) return 'needs_approval'
  if (!definition.enabled) return 'locked'
  if (definition.id === 'connect') {
    return (context.stats?.connections_count ?? 0) > 0 ? 'ready' : 'needs_setup'
  }
  if (definition.id === 'actions') {
    return (context.stats?.tools_count ?? 0) > 0 ? 'ready' : 'locked'
  }
  if (definition.id === 'qa') {
    return (context.stats?.tools_count ?? 0) > 0 ? 'needs_setup' : 'locked'
  }
  return 'ready'
}

export function isCapabilitySelectable(definition: OperatorCapabilityDefinition, context: CapabilityRuntimeContext): boolean {
  if (definition.mode === 'entry') return true
  if (!definition.enabled) return false
  if (!context.hasWorkspace) return false
  if (definition.authRequired && !context.isAuthenticated) return false
  return definition.id === 'chat' || context.isAuthenticated || definition.id === 'connect'
}

export function stateLabel(state: CapabilityState): string {
  switch (state) {
    case 'ready':
      return 'Ready'
    case 'needs_setup':
      return 'Needs setup'
    case 'locked':
      return 'Locked'
    case 'running':
      return 'Running'
    case 'needs_approval':
      return 'Needs approval'
    case 'has_findings':
      return 'Has findings'
  }
}

export function stateTone(state: CapabilityState): string {
  switch (state) {
    case 'ready':
      return 'bg-emerald-500'
    case 'needs_setup':
      return 'bg-amber-500'
    case 'locked':
      return 'bg-slate-300 dark:bg-slate-700'
    case 'running':
      return 'bg-sky-500'
    case 'needs_approval':
      return 'bg-orange-500'
    case 'has_findings':
      return 'bg-red-500'
  }
}

export function pickNextBestAction(actions: EntryActionCard[], mode: OperatorExperienceMode): EntryActionCard | null {
  const candidates = actions.filter((action) => action.kind !== 'form' && !action.disabled_reason)
  if (candidates.length === 0) return null
  const primary = candidates.find((action) => action.emphasis === 'primary')
  if (primary) return primary
  const setup = candidates.find((action) => action.id.includes('setup') || action.id.includes('connection'))
  if (setup) return setup
  const auth = candidates.find((action) => action.id.includes('sign_in') || action.id.includes('register'))
  if (mode === 'entry' && auth) return auth
  return candidates[0]
}

export const evidenceIcon = FileSearch
