import type { ChangeEvent, Dispatch, ReactNode, SetStateAction } from 'react'
import {
  BookOpen,
  Boxes,
  Brain,
  ClipboardCheck,
  Database,
  GraduationCap,
  Home,
  Play,
  Plug,
  Sparkles,
  User,
  Wrench,
} from 'lucide-react'
import {
  isRouteDeckOperationDispatchable,
  routeDeckOperationInteraction,
  type RouteDeckOperation,
  type RouteDeckProjection,
} from '@routedeck/react'

import type { CorpusProposal } from '@/types/corpus'
import { corpusOperationIds } from './corpusRouteDeckCatalog'

export interface ProposalField {
  key: string
  label: string
  field_type?: 'text' | 'password' | 'select' | 'url' | 'textarea'
  required?: boolean
  placeholder?: string | null
  default?: unknown
  options?: Array<{ value: string; label: string }> | null
  sensitive?: boolean
}

export interface CorpusQuickAction {
  operation: RouteDeckOperation
  label: string
  description?: string | null
  icon: ReactNode
  tone: 'primary' | 'tonal' | 'outline'
}

export function corpusQuickActions(projection: RouteDeckProjection): CorpusQuickAction[] {
  return projection.legal_operations
    .filter((operation) => !isInternalRouteOperation(operation))
    .filter((operation) => operation.id !== corpusOperationIds.navigateHome)
    .filter((operation) => {
      const interaction = operation.invocation_kind || routeDeckOperationInteraction(operation)
      if (operation.can_dispatch_now && isRouteDeckOperationDispatchable(operation)) return true
      return interaction === 'form' || interaction === 'surface'
    })
    .slice(0, 5)
    .map(operationToQuickAction)
}

function isInternalRouteOperation(operation: RouteDeckOperation): boolean {
  return operation.id.startsWith('route.') || operation.invocation_kind === 'hidden'
}

export function operationToQuickAction(operation: RouteDeckOperation): CorpusQuickAction {
  return {
    operation,
    label: corpusActionLabel(operation),
    description: operation.description,
    icon: operationIcon(operation.id),
    tone: operation.emphasis === 'primary' ? 'primary' : operation.execution_mode === 'review' ? 'outline' : 'tonal',
  }
}

export function operationToProposal(operation: RouteDeckOperation): CorpusProposal {
  return {
    operation_id: operation.id,
    label: corpusActionLabel(operation),
    description: operation.description,
    args: operation.payload || {},
    execution_mode: operation.execution_mode || 'review',
    safety_class: operation.safety_class,
    input_schema: operation.input_schema,
    target_node: operation.target_node,
  }
}

export function corpusActionLabel(operation: RouteDeckOperation) {
  const labels: Record<string, string> = {
    'auth.sign_in': 'Sign in',
    'auth.register': 'Create account',
    [corpusOperationIds.createSaaSAgent]: 'Create SaaS Agent',
    [corpusOperationIds.openSaaSAgent]: 'Open SaaS Agent',
    'navigate.connection_configure': 'Connect API',
    'connection.preview': 'Preview schema',
    'connection.activate': 'Activate API',
    'catalog.open': 'Catalog',
    'entities.open': 'Entities',
    'actions.open': 'Actions',
    'execution.open': 'Execution',
    'execution.plan': 'Plan execution',
    'knowledge.open': 'Knowledge',
    'memory.open': 'Memory',
    'learning.open': 'Learning',
    'qa.open': 'Run QA',
  }
  return labels[operation.id] || operation.label
}

export function operationIcon(operationId: string): ReactNode {
  if (operationId.includes('auth')) return <User className="h-4 w-4" />
  if (operationId.includes(corpusOperationIds.createSaaSAgent)) return <PlusCircleIcon />
  if (operationId.includes(corpusOperationIds.openSaaSAgent)) return <Home className="h-4 w-4" />
  if (operationId.includes('connection')) return <Plug className="h-4 w-4" />
  if (operationId.includes('catalog')) return <Database className="h-4 w-4" />
  if (operationId.includes('entities')) return <Boxes className="h-4 w-4" />
  if (operationId.includes('actions')) return <ListIcon />
  if (operationId.includes('execution')) return <Play className="h-4 w-4" />
  if (operationId.includes('knowledge')) return <BookOpen className="h-4 w-4" />
  if (operationId.includes('memory')) return <Brain className="h-4 w-4" />
  if (operationId.includes('learning')) return <GraduationCap className="h-4 w-4" />
  if (operationId.includes('qa')) return <ClipboardCheck className="h-4 w-4" />
  return <Sparkles className="h-4 w-4" />
}

function PlusCircleIcon() {
  return <Sparkles className="h-4 w-4" />
}

function ListIcon() {
  return <Wrench className="h-4 w-4" />
}

export function proposalFields(proposal: CorpusProposal): ProposalField[] {
  const fields = proposal.input_schema?.fields
  return Array.isArray(fields) ? (fields as ProposalField[]) : []
}

export function proposalDefaults(proposal: CorpusProposal) {
  const values = { ...(proposal.args || {}) }
  for (const field of proposalFields(proposal)) {
    if (!(field.key in values) && field.default !== undefined) {
      values[field.key] = field.default
    }
  }
  return values
}

export function handleProposalFieldChange(
  key: string,
  event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  setValues: Dispatch<SetStateAction<Record<string, unknown>>>,
) {
  setValues((current) => ({ ...current, [key]: event.target.value }))
}
