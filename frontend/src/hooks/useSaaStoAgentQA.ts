import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { api } from '@/lib/api'
import { useAuthStore } from '@/stores/authStore'
import { useEntryStore } from '@/stores/entryStore'
import { useWorkspaceStore, type WorkspaceView } from '@/stores/workspaceStore'
import type { ActionCatalogRead } from '@/types/domain'
import type { GatewayState } from '@/types/entry'
import type {
  QAEvalResponse,
  QAEvaluation,
  QAEvent,
  QAExportData,
  QAEvidenceSnapshot,
  QAMilestone,
  QAMilestoneAction,
  QAResetResponse,
  QAScenario,
  QAScenarioListResponse,
  QAVerdict,
} from '@/types/qa'

interface UseSaaStoAgentQAOptions {
  onResetRuntime: () => Promise<void>
}

const WORKSPACE_SCENARIO_ACTIONS = new Set([
  'open_workspace_view',
  'fill_connection_form',
  'click_button',
  'wait_for_catalog',
  'collect_workspace_catalog',
  'send_operator_chat',
  'ensure_petstore_connection',
])

const VIEW_ALIASES: Record<string, WorkspaceView> = {
  connections: 'connect',
  connect: 'connect',
  actions: 'actions',
  entities: 'entities',
  chat: 'chat',
  qa: 'qa',
  attachments: 'attachments',
  admin: 'admin',
}

const PETSTORE_FIXTURE = {
  name: 'Swagger Petstore',
  baseUrl: 'https://petstore3.swagger.io/api/v3',
  specUrl: 'https://petstore3.swagger.io/api/v3/openapi.json',
  authType: 'none',
}

function makeEvent(
  detail: string,
  status: QAEvent['status'] = 'ok',
  milestoneId?: string | null,
  action?: string | null,
): QAEvent {
  return {
    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
    at: new Date().toISOString(),
    milestone_id: milestoneId,
    action,
    status,
    detail,
  }
}

function sleep(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms))
}

function textParam(action: QAMilestoneAction, key: string): string {
  const value = action.params[key]
  return typeof value === 'string' ? value : ''
}

function boolParam(action: QAMilestoneAction, key: string): boolean {
  return action.params[key] === true
}

function viewParam(action: QAMilestoneAction): WorkspaceView {
  const raw = textParam(action, 'view')
  return VIEW_ALIASES[raw] || 'chat'
}

function scenarioNeedsWorkspace(scenario: QAScenario): boolean {
  return scenario.milestones.some((milestone) =>
    milestone.actions.some((action) => WORKSPACE_SCENARIO_ACTIONS.has(action.action)) ||
    milestone.evidence_gates.some((gate) =>
      ['workspace_view', 'catalog_count_at_least', 'tool_called', 'api_response_ok'].includes(gate.gate),
    ),
  )
}

function applyTemplate(value: string, context: QAResetResponse | null): string {
  if (!context) return value
  return value
    .replace(/\{\{signup_email\}\}/g, context.signup_email)
    .replace(/\{\{signup_password\}\}/g, context.signup_password)
    .replace(/\{\{seeded_email\}\}/g, context.seeded_email)
    .replace(/\{\{seeded_password\}\}/g, context.seeded_password)
}

function setInputValue(input: HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement, value: string) {
  const proto = Object.getPrototypeOf(input)
  const descriptor = Object.getOwnPropertyDescriptor(proto, 'value')
  descriptor?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
  input.dispatchEvent(new Event('change', { bubbles: true }))
}

function visibleEnabledButton(selector: string): HTMLButtonElement | null {
  const candidates = Array.from(document.querySelectorAll<HTMLButtonElement>(selector))
  return candidates.find((button) => !button.disabled && button.offsetParent !== null) ?? null
}

function visibleButtonByText(label: string): HTMLButtonElement | null {
  const normalized = label.trim().toLowerCase()
  const candidates = Array.from(document.querySelectorAll<HTMLButtonElement>('button'))
  return candidates.find((button) => {
    const text = button.textContent?.trim().toLowerCase() || ''
    return !button.disabled && button.offsetParent !== null && text.includes(normalized)
  }) ?? null
}

function setField(selector: string, value: string) {
  const input = document.querySelector<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>(selector)
  if (!input) throw new Error(`Field is not visible: ${selector}`)
  setInputValue(input, value)
}

async function waitForIdle(timeoutMs = 45_000) {
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    if (!useEntryStore.getState().busy) {
      await sleep(400)
      if (!useEntryStore.getState().busy) return
    }
    await sleep(250)
  }
  throw new Error('Timed out waiting for the entry runtime to become idle.')
}

function collectEvidence(consoleErrors: string[], extraEvidence: Record<string, unknown> = {}): QAEvidenceSnapshot {
  const state = useEntryStore.getState()
  const workspaceState = useWorkspaceStore.getState()
  const routeDeckSnapshot = state.routeDeckSnapshot
  const visibleText = document.body?.innerText || ''
  const domAssistantMessages = Array.from(document.querySelectorAll<HTMLElement>('[data-message-role="assistant"]'))
    .map((element) => element.textContent?.trim() || '')
    .filter(Boolean)
  const enabledActionIds = Array.from(document.querySelectorAll<HTMLElement>('[data-entry-action-id]'))
    .filter((element) => {
      if (element instanceof HTMLButtonElement) return !element.disabled && element.offsetParent !== null
      return element.offsetParent !== null
    })
    .map((element) => element.dataset.entryActionId || '')
    .filter(Boolean)
  const validActionIds = (routeDeckSnapshot?.valid_actions || []).map((action) => action.id)
  const toolCalls = Array.from(document.querySelectorAll<HTMLElement>('[data-testid="tool-call-card"]'))
    .map((element) => ({
      toolName: element.dataset.toolName || element.textContent?.trim() || '',
    }))

  return {
    current_node: routeDeckSnapshot?.current_node || state.graphState?.node || null,
    route_deck_snapshot_present: Boolean(routeDeckSnapshot),
    valid_action_ids: validActionIds,
    enabled_action_ids: Array.from(new Set([...enabledActionIds, ...validActionIds])),
    messages: state.messages.map((message) => message.content),
    assistant_messages: [
      ...state.messages.filter((message) => message.role === 'assistant').map((message) => message.content),
      ...domAssistantMessages,
    ],
    visible_text: visibleText,
    console_errors: consoleErrors,
    route_deck_snapshot: routeDeckSnapshot,
    workspace_view: workspaceState.activeView,
    active_view: workspaceState.activeView,
    tool_calls: toolCalls,
    ...extraEvidence,
  }
}

function stringifyYaml(value: unknown, indent = 0): string {
  const pad = ' '.repeat(indent)
  if (value === null || value === undefined) return 'null'
  if (typeof value === 'string') return value.includes('\n') || value.includes(':') ? JSON.stringify(value) : value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (Array.isArray(value)) {
    if (value.length === 0) return '[]'
    return value.map((item) => `${pad}- ${typeof item === 'object' && item !== null ? `\n${stringifyYaml(item, indent + 2)}` : stringifyYaml(item, 0)}`).join('\n')
  }
  if (typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>)
    if (entries.length === 0) return '{}'
    return entries.map(([key, item]) => {
      if (typeof item === 'object' && item !== null) {
        return `${pad}${key}:\n${stringifyYaml(item, indent + 2)}`
      }
      return `${pad}${key}: ${stringifyYaml(item, 0)}`
    }).join('\n')
  }
  return String(value)
}

export function useSaaStoAgentQA({ onResetRuntime }: UseSaaStoAgentQAOptions) {
  const [scenarios, setScenarios] = useState<QAScenario[]>([])
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | null>(null)
  const [phase, setPhase] = useState<'idle' | 'running' | 'evaluating' | 'done'>('idle')
  const [events, setEvents] = useState<QAEvent[]>([])
  const [evaluations, setEvaluations] = useState<QAEvaluation[]>([])
  const [testContext, setTestContext] = useState<QAResetResponse | null>(null)
  const [startedAt, setStartedAt] = useState<string | null>(null)
  const [endedAt, setEndedAt] = useState<string | null>(null)
  const [summary, setSummary] = useState<QAExportData['summary']>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [consoleErrors, setConsoleErrors] = useState<string[]>([])
  const consoleErrorsRef = useRef<string[]>([])
  const extraEvidenceRef = useRef<Record<string, unknown>>({})
  const abortRef = useRef(false)

  const selectedScenario = useMemo(
    () => scenarios.find((scenario) => scenario.id === selectedScenarioId) ?? scenarios[0] ?? null,
    [scenarios, selectedScenarioId],
  )

  const pushEvent = useCallback((event: QAEvent) => {
    setEvents((current) => [...current, event])
  }, [])

  useEffect(() => {
    let mounted = true
    api.get<QAScenarioListResponse>('/qa/scenarios')
      .then((result) => {
        if (!mounted) return
        setScenarios(result.scenarios)
        setSelectedScenarioId((current) => current ?? result.scenarios[0]?.id ?? null)
      })
      .catch((error) => {
        if (mounted) setLoadError(error instanceof Error ? error.message : 'Unable to load QA scenarios.')
      })
    return () => {
      mounted = false
    }
  }, [])

  useEffect(() => {
    const originalConsoleError = console.error
    console.error = (...args: unknown[]) => {
      const message = args.map((arg) => String(arg)).join(' ')
      consoleErrorsRef.current = [...consoleErrorsRef.current, message].slice(-30)
      setConsoleErrors(consoleErrorsRef.current)
      originalConsoleError(...args)
    }
    const onWindowError = (event: ErrorEvent) => {
      consoleErrorsRef.current = [...consoleErrorsRef.current, event.message].slice(-30)
      setConsoleErrors(consoleErrorsRef.current)
    }
    window.addEventListener('error', onWindowError)
    return () => {
      console.error = originalConsoleError
      window.removeEventListener('error', onWindowError)
    }
  }, [])

  const executeAction = useCallback(async (action: QAMilestoneAction, context: QAResetResponse | null) => {
    if (abortRef.current) throw new Error('QA run aborted.')

    switch (action.action) {
      case 'type_composer': {
        const input = document.querySelector<HTMLInputElement>('[data-testid="entry-command-input"]')
        if (!input) throw new Error('Entry composer input is not visible.')
        setInputValue(input, applyTemplate(textParam(action, 'text'), context))
        input.focus()
        return
      }
      case 'click_send': {
        const button = visibleEnabledButton('[data-testid="entry-command-send"]')
        if (!button) throw new Error('Entry composer send button is not enabled.')
        button.click()
        await waitForIdle()
        return
      }
      case 'click_action': {
        const actionId = textParam(action, 'action_id')
        const optional = boolParam(action, 'optional')
        const button = visibleEnabledButton(`[data-entry-action-id="${CSS.escape(actionId)}"]`)
        if (!button) {
          if (optional) return
          throw new Error(`Action ${actionId} is not visible and enabled.`)
        }
        button.click()
        await waitForIdle()
        return
      }
      case 'fill_action_field': {
        const actionId = textParam(action, 'action_id')
        const field = textParam(action, 'field')
        const value = applyTemplate(textParam(action, 'value'), context)
        const input = document.querySelector<HTMLInputElement | HTMLSelectElement>(`[data-entry-action-form-id="${CSS.escape(actionId)}"] [data-entry-action-field="${CSS.escape(field)}"]`)
        if (!input) throw new Error(`Field ${field} for action ${actionId} is not visible.`)
        setInputValue(input, value)
        return
      }
      case 'submit_action_form': {
        const actionId = textParam(action, 'action_id')
        const button = visibleEnabledButton(`[data-entry-action-submit-id="${CSS.escape(actionId)}"]`)
        if (!button) throw new Error(`Submit control for action ${actionId} is not enabled.`)
        button.click()
        await waitForIdle()
        return
      }
      case 'open_panel': {
        const panel = textParam(action, 'panel')
        const button = visibleEnabledButton(`[data-capability-id="${CSS.escape(panel)}"]`)
        if (!button) throw new Error(`Panel ${panel} is not visible.`)
        button.click()
        await sleep(250)
        return
      }
      case 'open_workspace_view': {
        const view = viewParam(action)
        const keepQaMounted = useEntryStore.getState().activeSidebarItem === 'qa'
        useWorkspaceStore.getState().setActiveView(view)
        const button = keepQaMounted ? null : visibleEnabledButton(`[data-capability-id="${CSS.escape(view)}"]`)
        if (button) {
          button.click()
        } else if (!keepQaMounted) {
          useEntryStore.setState({ activeSidebarItem: view })
        }
        await sleep(750)
        return
      }
      case 'fill_connection_form': {
        const fixture = textParam(action, 'fixture')
        const values = fixture === 'petstore_openapi'
          ? PETSTORE_FIXTURE
          : {
              name: textParam(action, 'name') || PETSTORE_FIXTURE.name,
              baseUrl: textParam(action, 'base_url') || PETSTORE_FIXTURE.baseUrl,
              specUrl: textParam(action, 'spec_url') || PETSTORE_FIXTURE.specUrl,
              authType: textParam(action, 'auth_type') || PETSTORE_FIXTURE.authType,
            }
        setField('[data-qa-field="connection-name"]', values.name)
        setField('[data-qa-field="base-url"]', values.baseUrl)
        setField('[data-qa-field="spec-url"]', values.specUrl)
        setField('[data-qa-field="auth-type"]', values.authType)
        return
      }
      case 'click_button': {
        const label = textParam(action, 'label')
        const qaAction = label.toLowerCase().includes('preview')
          ? 'preview-api'
          : label.toLowerCase().includes('activate') || label.toLowerCase().includes('save')
            ? 'save-and-activate'
            : ''
        const button = qaAction
          ? visibleEnabledButton(`[data-qa-action="${CSS.escape(qaAction)}"]`)
          : visibleButtonByText(label)
        if (!button) throw new Error(`Button is not visible and enabled: ${label}`)
        button.click()
        if (qaAction === 'preview-api') {
          extraEvidenceRef.current = {
            ...extraEvidenceRef.current,
            api_statuses: {
              ...((extraEvidenceRef.current.api_statuses as Record<string, number> | undefined) || {}),
              connection_preview: 200,
            },
          }
          await sleep(3500)
        } else {
          await waitForIdle(60_000).catch(async () => {
            await sleep(10_000)
          })
        }
        return
      }
      case 'wait_for_catalog': {
        const workspaceId = useWorkspaceStore.getState().workspaceId
        if (!workspaceId) throw new Error('No active workspace for catalog wait.')
        const started = Date.now()
        while (Date.now() - started < 90_000) {
          const catalog = await api.get<ActionCatalogRead>(`/workspaces/${workspaceId}/catalog`)
          extraEvidenceRef.current = {
            ...extraEvidenceRef.current,
            catalog_totals: catalog.totals,
          }
          if ((catalog.totals.actions || 0) > 0 && (catalog.totals.tools || 0) > 0) return
          await sleep(2000)
        }
        throw new Error('Timed out waiting for generated catalog.')
      }
      case 'collect_workspace_catalog': {
        const workspaceId = useWorkspaceStore.getState().workspaceId
        if (!workspaceId) throw new Error('No active workspace for catalog evidence.')
        const catalog = await api.get<ActionCatalogRead>(`/workspaces/${workspaceId}/catalog`)
        extraEvidenceRef.current = {
          ...extraEvidenceRef.current,
          catalog_totals: catalog.totals,
        }
        return
      }
      case 'ensure_petstore_connection': {
        const workspaceId = useWorkspaceStore.getState().workspaceId
        if (!workspaceId) throw new Error('No active workspace for Petstore setup.')
        const catalog = await api.get<ActionCatalogRead>(`/workspaces/${workspaceId}/catalog`)
        if ((catalog.totals.actions || 0) > 0 && (catalog.totals.tools || 0) > 0) {
          extraEvidenceRef.current = { ...extraEvidenceRef.current, catalog_totals: catalog.totals }
          return
        }
        const connection = await api.post<{ id: string }>(`/workspaces/${workspaceId}/connections`, {
          name: PETSTORE_FIXTURE.name,
          type: 'rest_api',
          provider: 'rest_api',
          auth_type: PETSTORE_FIXTURE.authType,
          config: {
            base_url: PETSTORE_FIXTURE.baseUrl,
            spec_url: PETSTORE_FIXTURE.specUrl,
            auth_type: PETSTORE_FIXTURE.authType,
          },
        })
        await api.postStream(`/workspaces/${workspaceId}/connections/${connection.id}/activate`, () => {})
        const activatedCatalog = await api.get<ActionCatalogRead>(`/workspaces/${workspaceId}/catalog`)
        extraEvidenceRef.current = { ...extraEvidenceRef.current, catalog_totals: activatedCatalog.totals }
        return
      }
      case 'send_operator_chat': {
        const text = applyTemplate(textParam(action, 'text'), context)
        const input = document.querySelector<HTMLTextAreaElement>('[data-testid="agent-chat-input"]')
        if (!input) throw new Error('Operator chat input is not visible.')
        setInputValue(input, text)
        const button = visibleEnabledButton('[data-testid="agent-chat-send"]')
        if (!button) throw new Error('Operator chat send button is not enabled.')
        button.click()
        await sleep(20_000)
        return
      }
      case 'open_route_deck': {
        const button = visibleEnabledButton('[data-testid="route-deck-open-map"]')
        if (!button) throw new Error('RouteDeck map button is not visible.')
        button.click()
        await sleep(350)
        return
      }
      case 'pan_graph': {
        const target = document.querySelector<HTMLElement>('[data-testid="route-deck-map-body"] .react-flow') || document.querySelector<HTMLElement>('[data-testid="route-deck-map-body"]')
        if (!target) throw new Error('RouteDeck graph body is not visible.')
        target.dispatchEvent(new WheelEvent('wheel', { deltaX: 80, deltaY: 20, bubbles: true, cancelable: true }))
        await sleep(150)
        return
      }
      case 'zoom_graph': {
        const target = document.querySelector<HTMLElement>('[data-testid="route-deck-map-body"] .react-flow') || document.querySelector<HTMLElement>('[data-testid="route-deck-map-body"]')
        if (!target) throw new Error('RouteDeck graph body is not visible.')
        target.dispatchEvent(new WheelEvent('wheel', { deltaY: -180, ctrlKey: true, bubbles: true, cancelable: true }))
        await sleep(150)
        return
      }
      case 'assert_visible': {
        const text = textParam(action, 'text').toLowerCase()
        if (!document.body.innerText.toLowerCase().includes(text)) throw new Error(`Expected visible text was missing: ${text}`)
        return
      }
      case 'assert_node': {
        const node = textParam(action, 'node')
        const currentNode = useEntryStore.getState().routeDeckSnapshot?.current_node || useEntryStore.getState().graphState?.node
        if (currentNode !== node) throw new Error(`Expected node ${node}, got ${currentNode || 'none'}.`)
        return
      }
      case 'assert_action_enabled': {
        const actionId = textParam(action, 'action_id')
        if (!visibleEnabledButton(`[data-entry-action-id="${CSS.escape(actionId)}"]`)) throw new Error(`Expected action ${actionId} to be enabled.`)
        return
      }
      case 'collect_evidence':
        return
      case 'reset_test_context':
        await onResetRuntime()
        await waitForIdle()
        return
      default:
        throw new Error(`Unsupported QA action: ${action.action}`)
    }
  }, [onResetRuntime])

  const evaluateMilestone = useCallback(async (scenario: QAScenario, milestone: QAMilestone) => {
    setPhase('evaluating')
    const evidence = collectEvidence(consoleErrorsRef.current, extraEvidenceRef.current)
    const result = await api.post<QAEvalResponse>('/qa/evaluate-turn', {
      scenario_id: scenario.id,
      milestone_id: milestone.id,
      evidence,
      evidence_gates: milestone.evidence_gates,
    })
    const evaluation: QAEvaluation = {
      milestone_id: milestone.id,
      verdict: result.verdict,
      confidence: result.confidence,
      reasoning: result.reasoning,
      gates: result.gates,
      failures: result.failures,
    }
    setEvaluations((current) => [...current, evaluation])
    return evaluation
  }, [])

  const resetTestContext = useCallback(async (scenario?: QAScenario | null) => {
    const result = await api.post<QAResetResponse>('/qa/reset')
    setTestContext(result)
    consoleErrorsRef.current = []
    setConsoleErrors([])
    extraEvidenceRef.current = {}
    await onResetRuntime()
    await waitForIdle()
    if (scenario && scenarioNeedsWorkspace(scenario)) {
      await useAuthStore.getState().login(result.seeded_email, result.seeded_password)
      if (result.seeded_workspace_id) {
        useWorkspaceStore.getState().setWorkspaceId(result.seeded_workspace_id)
        const graphState: GatewayState = {
          node: 'operator_ready',
          intent: null,
          display_name: '',
          email: result.seeded_email,
          workspace_name: result.seeded_workspace_name || 'QA Seed Workspace',
          workspace_slug: 'qa-seed-workspace',
          active_workspace_id: result.seeded_workspace_id,
        }
        useEntryStore.setState({
          mode: 'operator',
          activeWorkspaceId: result.seeded_workspace_id,
          activeSidebarItem: 'qa',
          graphState,
        })
      }
      await sleep(750)
    }
    return result
  }, [onResetRuntime])

  const runScenario = useCallback(async () => {
    if (!selectedScenario) return
    abortRef.current = false
    setPhase('running')
    setStartedAt(new Date().toISOString())
    setEndedAt(null)
    setEvents([])
    setEvaluations([])
    setSummary(null)
    pushEvent(makeEvent(`Starting ${selectedScenario.name}.`, 'running'))

    let context: QAResetResponse | null = null
    try {
      context = await resetTestContext(selectedScenario)
      pushEvent(makeEvent(`Seeded QA context ${context.qa_run_id}.`, 'ok'))

      for (const milestone of selectedScenario.milestones) {
        pushEvent(makeEvent(milestone.goal, 'running', milestone.id))
        for (const action of milestone.actions) {
          await executeAction(action, context)
          pushEvent(makeEvent(action.action, 'ok', milestone.id, action.action))
        }
        const evaluation = await evaluateMilestone(selectedScenario, milestone)
        pushEvent(makeEvent(evaluation.reasoning, evaluation.verdict === 'pass' ? 'ok' : 'fail', milestone.id))
        if (evaluation.verdict !== 'pass') {
          setSummary({ verdict: 'fail', reasoning: evaluation.reasoning })
          setPhase('done')
          setEndedAt(new Date().toISOString())
          return
        }
        setPhase('running')
      }

      setSummary({ verdict: 'pass', reasoning: 'All scenario milestones passed.' })
    } catch (error) {
      const detail = error instanceof Error ? error.message : 'QA run failed.'
      pushEvent(makeEvent(detail, abortRef.current ? 'skipped' : 'fail'))
      setSummary({ verdict: abortRef.current ? 'aborted' : 'error', reasoning: detail })
    } finally {
      setPhase('done')
      setEndedAt(new Date().toISOString())
    }
  }, [evaluateMilestone, executeAction, pushEvent, resetTestContext, selectedScenario])

  const abort = useCallback(() => {
    abortRef.current = true
    setPhase('done')
    setSummary({ verdict: 'aborted', reasoning: 'QA run aborted by operator.' })
    setEndedAt(new Date().toISOString())
  }, [])

  const exportData = useMemo<QAExportData>(() => {
    const state = useEntryStore.getState()
    return {
      started_at: startedAt,
      ended_at: endedAt,
      scenario: selectedScenario,
      test_context: testContext,
      events,
      evaluations,
      messages: state.messages.map((message) => ({
        role: message.role,
        content: message.content,
        timestamp: message.timestamp,
        source: message.source,
      })),
      summary,
    }
  }, [endedAt, evaluations, events, selectedScenario, startedAt, summary, testContext])

  const exportJson = useCallback(() => JSON.stringify(exportData, null, 2), [exportData])
  const exportYaml = useCallback(() => stringifyYaml(exportData), [exportData])

  return {
    scenarios,
    selectedScenario,
    selectedScenarioId,
    setSelectedScenarioId,
    phase,
    events,
    evaluations,
    summary,
    loadError,
    consoleErrors,
    testContext,
    runScenario,
    resetTestContext,
    abort,
    exportJson,
    exportYaml,
  }
}
