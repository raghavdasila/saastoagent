import { formatSaaSAgentDisplayName } from '@/lib/entryGraph'
import type { SaaSAgent, SaaSAgentStats } from '@/types/domain'

function lineBreaks(lines: string[]) {
  return lines.join('\n\n')
}

export function buildInitialAgentMessage(saasAgent?: SaaSAgent, stats?: SaaSAgentStats) {
  const saasAgentName = formatSaaSAgentDisplayName(saasAgent?.name) || 'this saasAgent'
  const hasConnections = (stats?.connections_count ?? 0) > 0

  if (hasConnections) {
    return lineBreaks([
      `I am your agent for ${saasAgentName}. Tell me the outcome you want and I will use the connected REST sources to find actions, plan the path, and get the work done.`,
      'You can ask me to inspect available actions, explain what I can do for a request, or prepare a workflow before execution is enabled.',
    ])
  }

  return lineBreaks([
    `I am your agent for ${saasAgentName}. Tell me what work you want done, even before the API is connected.`,
    'I will translate that goal into the setup I need: which SaaS product to connect, which actions I will look for, and how I will handle execution and QA once the saasAgent is ready.',
  ])
}

export function buildShellAgentReply(input: string, saasAgent?: SaaSAgent, stats?: SaaSAgentStats) {
  const text = input.trim()
  const normalized = text.toLowerCase()
  const saasAgentName = formatSaaSAgentDisplayName(saasAgent?.name) || 'this saasAgent'
  const hasConnections = (stats?.connections_count ?? 0) > 0

  if (!hasConnections) {
    if (/(connect|openapi|swagger|rest api|api url|spec)/.test(normalized)) {
      return lineBreaks([
        'Good. The next milestone is connecting the first REST API for this saasAgent.',
        'Once that lands, I will activate the OpenAPI source, inspect the generated action catalog, infer entities from the response shapes, and come back here ready to help with tasks instead of setup.',
      ])
    }

    if (/(what can you do|capabilit|help me|how will you work)/.test(normalized)) {
      return lineBreaks([
        'Once connected, I work in a loop: understand the goal, select relevant API actions, execute the right path, and feed failures into QA and learnings.',
        'That means this chat is not just search. It becomes the place where you give me outcomes and I turn them into action.',
      ])
    }

    if (/(qa|learn|improve|failure|trace|tune)/.test(normalized)) {
      return lineBreaks([
        'After execution is live, I will keep a lightweight improvement loop for this saasAgent: capture failures, inspect traces, tune prompts or tool exposure, and persist validated learnings.',
        'That is how this stays agentic instead of becoming a one-shot chat toy.',
      ])
    }

    return lineBreaks([
      `To get ${text ? `"${text}"` : 'that work'} done in ${saasAgentName}, I need the REST API for the product you want me to operate.`,
      'Tell me which SaaS product or OpenAPI schema this saasAgent should connect to first, and I will frame setup around that API surface.',
    ])
  }

  if (/(what can you do|capabilit|available|actions|entities)/.test(normalized)) {
    return lineBreaks([
      `This saasAgent already has connected sources, so the next step is to inspect actions and entities that matter for your request in ${saasAgentName}.`,
      'Ask for an outcome and I will narrow the action space before execution lands.',
    ])
  }

  return lineBreaks([
    `I understand the goal: ${text}.`,
    'The next slices will let me choose the best matching actions, execute the REST workflow, and show you the trace here in the same conversation.',
  ])
}
