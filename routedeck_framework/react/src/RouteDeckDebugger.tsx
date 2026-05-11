import { useMemo, useState } from 'react'

import type { RouteDeckManifest, RouteDeckManifestAction, RouteDeckManifestEdge, RouteDeckManifestNode, RouteDeckRuntimeSnapshot } from './types'

export interface RouteDeckDebuggerProps {
  graphManifest?: RouteDeckManifest | null
  snapshot?: RouteDeckRuntimeSnapshot | null
  selectedNodeId?: string | null
  onSelectedNodeChange: (nodeId: string | null) => void
  runId?: string | null
  sessionId?: string | null
  className?: string
}

type GraphTone = 'previous' | 'current' | 'next' | 'idle'
type MapMode = 'focus' | 'full'

interface GraphNode {
  node: RouteDeckManifestNode
  edge?: RouteDeckManifestEdge
  tone: GraphTone
  x: number
  y: number
  width?: number
  height?: number
}

interface GraphPosition {
  x: number
  y: number
  tone: GraphTone
  width: number
  height: number
}

const FOCUS_NODE_WIDTH = 156
const FOCUS_CURRENT_NODE_WIDTH = 176
const FOCUS_NODE_HEIGHT = 62
const FOCUS_CURRENT_NODE_HEIGHT = 72
const FULL_NODE_WIDTH = 184
const FULL_CURRENT_NODE_WIDTH = 196
const FULL_NODE_HEIGHT = 68
const FULL_CURRENT_NODE_HEIGHT = 76
const FULL_GRAPH_LEFT_PAD = 126
const FULL_GRAPH_RIGHT_PAD = 44
const FULL_GRAPH_TOP_PAD = 86
const FULL_GRAPH_LANE_GAP = 154
const FULL_GRAPH_BOTTOM_PAD = 72
const FULL_GRAPH_NODE_GAP = 44

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(' ')
}

function edgeLabel(edge: RouteDeckManifestEdge) {
  return edge.action_id || edge.condition || edge.type
}

function shortText(value?: string | null, max = 22) {
  if (!value) return ''
  return value.length > max ? `${value.slice(0, max - 1)}...` : value
}

function laneY(count: number) {
  if (count <= 1) return [170]
  if (count === 2) return [125, 215]
  if (count === 3) return [95, 170, 245]
  return [72, 137, 202, 267]
}

function spreadLaneX(count: number, canvasWidth: number) {
  const available = canvasWidth - FULL_GRAPH_LEFT_PAD - FULL_GRAPH_RIGHT_PAD
  const nodeWidth = FULL_NODE_WIDTH
  if (count <= 1) return [FULL_GRAPH_LEFT_PAD + available / 2]
  const usable = Math.max(nodeWidth, available - nodeWidth)
  return Array.from(
    { length: count },
    (_, index) => FULL_GRAPH_LEFT_PAD + nodeWidth / 2 + index * (usable / Math.max(1, count - 1)),
  )
}

function graphNodeWidth(tone: GraphTone, width?: number) {
  if (width) return width
  return tone === 'current' ? FOCUS_CURRENT_NODE_WIDTH : FOCUS_NODE_WIDTH
}

function graphNodeHeight(tone: GraphTone, height?: number) {
  if (height) return height
  return tone === 'current' ? FOCUS_CURRENT_NODE_HEIGHT : FOCUS_NODE_HEIGHT
}

function nodeHalfWidth(position: Pick<GraphPosition, 'width'>) {
  return position.width / 2
}

function nodeHalfHeight(position: Pick<GraphPosition, 'height'>) {
  return position.height / 2
}

function nodeStyle(tone: GraphTone, selected: boolean) {
  if (tone === 'current') {
    return {
      fill: selected ? '#075985' : '#0c4a6e',
      stroke: '#38bdf8',
      title: '#f0f9ff',
      sub: '#bae6fd',
      metaFill: '#082f49',
      metaText: '#e0f2fe',
    }
  }
  if (tone === 'previous') {
    return {
      fill: selected ? '#064e3b' : '#052e2b',
      stroke: '#10b981',
      title: '#ecfdf5',
      sub: '#a7f3d0',
      metaFill: '#022c22',
      metaText: '#d1fae5',
    }
  }
  if (tone === 'next') {
    return {
      fill: selected ? '#78350f' : '#422006',
      stroke: '#f59e0b',
      title: '#fffbeb',
      sub: '#fde68a',
      metaFill: '#451a03',
      metaText: '#fef3c7',
    }
  }
  return {
    fill: selected ? '#1e293b' : '#0f172a',
    stroke: '#475569',
    title: '#e2e8f0',
    sub: '#94a3b8',
    metaFill: '#020617',
    metaText: '#cbd5e1',
  }
}

function GraphNodeShape({
  item,
  selected,
  onSelect,
}: {
  item: GraphNode
  selected: boolean
  onSelect: (nodeId: string) => void
}) {
  const current = item.tone === 'current'
  const width = graphNodeWidth(item.tone, item.width)
  const height = graphNodeHeight(item.tone, item.height)
  const radius = current ? 18 : 14
  const style = nodeStyle(item.tone, selected)
  const left = item.x - width / 2
  const top = item.y - height / 2
  const badgeWidth = Math.min(66, Math.max(44, item.node.lane.length * 6 + 18))
  const titleMax = Math.max(10, Math.floor((width - badgeWidth - 34) / 7))
  const idMax = Math.max(12, Math.floor((width - 28) / 6.4))

  return (
    <g
      role="button"
      tabIndex={0}
      aria-label={item.node.label}
      onClick={() => onSelect(item.node.id)}
      onKeyDown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') onSelect(item.node.id)
      }}
      style={{ cursor: 'pointer', outline: 'none' }}
    >
      <rect
        x={left}
        y={top}
        width={width}
        height={height}
        rx={radius}
        fill={style.fill}
        stroke={selected ? '#ffffff' : style.stroke}
        strokeWidth={current ? 2.8 : 1.8}
      />
      <text x={left + 14} y={top + 24} fill={style.title} fontSize={current ? 14 : 12} fontWeight={700}>
        {shortText(item.node.label, titleMax)}
      </text>
      <text x={left + 14} y={top + 45} fill={style.sub} fontSize={10.5} fontFamily="ui-monospace, SFMono-Regular, Menlo, monospace">
        {shortText(item.node.id, idMax)}
      </text>
      <rect x={left + width - badgeWidth - 12} y={top + 12} width={badgeWidth} height={18} rx={9} fill={style.metaFill} stroke={style.stroke} strokeOpacity={0.35} />
      <text x={left + width - badgeWidth / 2 - 12} y={top + 25} fill={style.metaText} textAnchor="middle" fontSize={8.5} fontWeight={700}>
        {shortText(item.node.lane.toUpperCase(), 7)}
      </text>
    </g>
  )
}

function ActionPill({ action, valid }: { action: Pick<RouteDeckManifestAction, 'id' | 'label'>; valid: boolean }) {
  return (
    <span
      className={cx(
        'inline-flex min-w-0 max-w-full items-center gap-2 rounded-full border px-3 py-1.5',
        valid
          ? 'border-emerald-200 bg-emerald-50 text-emerald-950 dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-50'
          : 'border-slate-200 bg-slate-50 text-slate-700 dark:border-white/10 dark:bg-white/[0.04] dark:text-slate-300',
      )}
      title={action.id}
    >
      <span className={cx('h-1.5 w-1.5 shrink-0 rounded-full', valid ? 'bg-emerald-500' : 'bg-slate-400')} />
      <span className="truncate text-xs font-semibold">{action.label}</span>
      <span className="truncate font-mono text-[10px] opacity-65">{action.id}</span>
    </span>
  )
}

export function RouteDeckDebugger({
  graphManifest,
  snapshot,
  selectedNodeId,
  onSelectedNodeChange,
  runId,
  sessionId,
  className = '',
}: RouteDeckDebuggerProps) {
  const [mode, setMode] = useState<MapMode>('focus')
  const nodes = graphManifest?.nodes || []
  const edges = graphManifest?.edges || []
  const nodesById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes])
  const actionById = useMemo(() => new Map((graphManifest?.actions || []).map((action) => [action.id, action])), [graphManifest?.actions])
  const currentNodeId = snapshot?.current_node || selectedNodeId || nodes[0]?.id || null
  const selectedId = selectedNodeId || currentNodeId
  const currentNode = currentNodeId ? nodesById.get(currentNodeId) || null : null
  const selectedNode = selectedId ? nodesById.get(selectedId) || currentNode : currentNode
  const incomingEdges = edges.filter((edge) => edge.to === currentNodeId).slice(0, 4)
  const outgoingEdges = edges.filter((edge) => edge.from === currentNodeId).slice(0, 4)
  const incomingNodes = incomingEdges
    .map((edge, index) => ({ edge, node: nodesById.get(edge.from), y: laneY(incomingEdges.length)[index] }))
    .filter((item): item is { edge: RouteDeckManifestEdge; node: RouteDeckManifestNode; y: number } => Boolean(item.node))
  const outgoingNodes = outgoingEdges
    .map((edge, index) => ({ edge, node: nodesById.get(edge.to), y: laneY(outgoingEdges.length)[index] }))
    .filter((item): item is { edge: RouteDeckManifestEdge; node: RouteDeckManifestNode; y: number } => Boolean(item.node))
  const graphNodes: GraphNode[] = [
    ...incomingNodes.map((item) => ({ node: item.node, edge: item.edge, tone: 'previous' as const, x: 118, y: item.y })),
    ...(currentNode ? [{ node: currentNode, tone: 'current' as const, x: 380, y: 170 }] : []),
    ...outgoingNodes.map((item) => ({ node: item.node, edge: item.edge, tone: 'next' as const, x: 642, y: item.y })),
  ]
  const selectedActionIds = selectedNode?.allowed_actions || []
  const validActionIds = new Set((snapshot?.valid_actions || []).map((action) => action.id))
  const actions = selectedActionIds.length > 0
    ? selectedActionIds.map((actionId) => actionById.get(actionId) || { id: actionId, label: actionId }).slice(0, 10)
    : (snapshot?.valid_actions || []).slice(0, 10)
  const fullGraph = useMemo(() => {
    const laneOrder = ['system', 'auth', 'workspace', 'terminal']
    const lanes = new Map<string, RouteDeckManifestNode[]>()
    for (const node of nodes) {
      const lane = node.lane || 'workspace'
      lanes.set(lane, [...(lanes.get(lane) || []), node])
    }
    const orderedLanes = [
      ...laneOrder.filter((lane) => lanes.has(lane)),
      ...Array.from(lanes.keys()).filter((lane) => !laneOrder.includes(lane)),
    ]
    const maxLaneCount = Math.max(1, ...Array.from(lanes.values()).map((laneNodes) => laneNodes.length))
    const width = Math.max(
      860,
      FULL_GRAPH_LEFT_PAD + FULL_GRAPH_RIGHT_PAD + maxLaneCount * FULL_NODE_WIDTH + Math.max(0, maxLaneCount - 1) * FULL_GRAPH_NODE_GAP,
    )
    const height = FULL_GRAPH_TOP_PAD + Math.max(0, orderedLanes.length - 1) * FULL_GRAPH_LANE_GAP + FULL_GRAPH_BOTTOM_PAD
    const rowYs = new Map<string, number>()
    const positions = new Map<string, GraphPosition>()
    const executedNodes = new Set(snapshot?.executed_nodes || [])
    const previousNodes = new Set(edges.filter((edge) => edge.to === currentNodeId).map((edge) => edge.from))
    const nextNodes = new Set(edges.filter((edge) => edge.from === currentNodeId).map((edge) => edge.to))

    for (const [laneIndex, lane] of orderedLanes.entries()) {
      const laneNodes = lanes.get(lane) || []
      const xValues = spreadLaneX(laneNodes.length, width)
      const y = FULL_GRAPH_TOP_PAD + laneIndex * FULL_GRAPH_LANE_GAP
      rowYs.set(lane, y)
      laneNodes.forEach((node, index) => {
        const tone: GraphTone = node.id === currentNodeId
          ? 'current'
          : previousNodes.has(node.id) || executedNodes.has(node.id)
            ? 'previous'
            : nextNodes.has(node.id)
              ? 'next'
              : 'idle'
        const nodeWidth = tone === 'current' ? FULL_CURRENT_NODE_WIDTH : FULL_NODE_WIDTH
        const nodeHeight = tone === 'current' ? FULL_CURRENT_NODE_HEIGHT : FULL_NODE_HEIGHT
        positions.set(node.id, { x: xValues[index], y, tone, width: nodeWidth, height: nodeHeight })
      })
    }
    const columnXs = spreadLaneX(maxLaneCount, width)
    return { orderedLanes, positions, width, height, rowYs, columnXs }
  }, [currentNodeId, edges, nodes, snapshot?.executed_nodes])

  function exportSnapshot() {
    const payload = {
      manifest: graphManifest,
      snapshot,
      run_id: runId,
      session_id: sessionId,
      exported_at: new Date().toISOString(),
    }
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `route-deck-snapshot-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!graphManifest || !currentNode) {
    return (
      <div className={`rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs dark:border-white/10 dark:bg-white/[0.03] ${className}`}>
        <div className="font-semibold text-slate-700 dark:text-slate-200">RouteDeck map</div>
        <div className="mt-2 text-slate-500 dark:text-slate-400">No RouteDeck manifest is available for this runtime.</div>
      </div>
    )
  }

  return (
    <div className={`space-y-4 text-xs ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <div className="font-semibold text-slate-900 dark:text-white">{mode === 'focus' ? 'Route graph' : 'Full site graph'}</div>
          <div className="mt-1 text-slate-500 dark:text-slate-400">{graphManifest.version} - {nodes.length} nodes - {graphManifest.actions?.length || 0} actions</div>
        </div>
        <div className="flex items-center gap-2">
          <div className="inline-flex rounded-full border border-slate-200 bg-slate-100 p-0.5 dark:border-white/10 dark:bg-white/[0.04]">
            {(['focus', 'full'] as MapMode[]).map((item) => (
              <button
                key={item}
                type="button"
                onClick={() => setMode(item)}
                className={cx(
                  'rounded-full px-3 py-1.5 text-xs font-semibold transition',
                  mode === item
                    ? 'bg-white text-slate-950 shadow-sm dark:bg-white dark:text-slate-950'
                    : 'text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white',
                )}
              >
                {item === 'focus' ? 'Focus' : 'Full graph'}
              </button>
            ))}
          </div>
          <button
            type="button"
            onClick={exportSnapshot}
            className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition hover:bg-slate-100 dark:border-white/10 dark:bg-white/[0.05] dark:text-slate-300 dark:hover:bg-white/[0.09]"
          >
            Export JSON
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-slate-950 shadow-inner dark:border-white/10">
        {mode === 'focus' ? (
        <svg viewBox="0 0 760 340" className="block h-[24rem] w-full" role="img" aria-label="RouteDeck graph">
          <defs>
            <marker id="routeDeckArrowGreen" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L10,5 L0,10 z" fill="#10b981" />
            </marker>
            <marker id="routeDeckArrowAmber" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
              <path d="M0,0 L10,5 L0,10 z" fill="#f59e0b" />
            </marker>
            <radialGradient id="routeDeckGlow" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#0ea5e9" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#020617" stopOpacity="0" />
            </radialGradient>
          </defs>
          <rect width="760" height="340" fill="#020617" />
          <circle cx="380" cy="170" r="150" fill="url(#routeDeckGlow)" />
          <g opacity="0.18" stroke="#64748b" strokeWidth="1">
            {[80, 170, 260].map((y) => <line key={`h-${y}`} x1="32" x2="728" y1={y} y2={y} />)}
            {[118, 380, 642].map((x) => <line key={`v-${x}`} x1={x} x2={x} y1="34" y2="306" />)}
          </g>
          <text x="118" y="30" fill="#94a3b8" textAnchor="middle" fontSize="11" fontWeight="700" letterSpacing="1.5">INCOMING</text>
          <text x="380" y="30" fill="#bae6fd" textAnchor="middle" fontSize="11" fontWeight="700" letterSpacing="1.5">CURRENT</text>
          <text x="642" y="30" fill="#fcd34d" textAnchor="middle" fontSize="11" fontWeight="700" letterSpacing="1.5">OUTGOING</text>

          {incomingNodes.map(({ edge, y }) => {
            const sx = 196
            const sy = y
            const tx = 292
            const ty = 170
            const midX = (sx + tx) / 2
            const midY = (sy + ty) / 2 - 8
            return (
              <g key={`in-${edge.from}-${edge.to}-${edgeLabel(edge)}`}>
                <path d={`M${sx},${sy} C${sx + 56},${sy} ${tx - 56},${ty} ${tx},${ty}`} fill="none" stroke="#10b981" strokeWidth="2" markerEnd="url(#routeDeckArrowGreen)" />
                <rect x={midX - 46} y={midY - 10} width="92" height="20" rx="10" fill="#022c22" stroke="#10b981" strokeOpacity="0.35" />
                <text x={midX} y={midY + 4} fill="#d1fae5" textAnchor="middle" fontSize="10">{shortText(edgeLabel(edge), 15)}</text>
              </g>
            )
          })}

          {outgoingNodes.map(({ edge, y }) => {
            const sx = 468
            const sy = 170
            const tx = 562
            const ty = y
            const midX = (sx + tx) / 2
            const midY = (sy + ty) / 2 - 8
            return (
              <g key={`out-${edge.from}-${edge.to}-${edgeLabel(edge)}`}>
                <path d={`M${sx},${sy} C${sx + 56},${sy} ${tx - 56},${ty} ${tx},${ty}`} fill="none" stroke="#f59e0b" strokeWidth="2" markerEnd="url(#routeDeckArrowAmber)" />
                <rect x={midX - 46} y={midY - 10} width="92" height="20" rx="10" fill="#451a03" stroke="#f59e0b" strokeOpacity="0.35" />
                <text x={midX} y={midY + 4} fill="#fef3c7" textAnchor="middle" fontSize="10">{shortText(edgeLabel(edge), 15)}</text>
              </g>
            )
          })}

          {incomingNodes.length === 0 && <text x="118" y="174" fill="#64748b" textAnchor="middle" fontSize="12">No incoming nodes</text>}
          {outgoingNodes.length === 0 && <text x="642" y="174" fill="#64748b" textAnchor="middle" fontSize="12">No outgoing nodes</text>}

          {graphNodes.map((item) => (
            <GraphNodeShape
              key={`${item.tone}-${item.node.id}`}
              item={item}
              selected={selectedId === item.node.id}
              onSelect={onSelectedNodeChange}
            />
          ))}
        </svg>
        ) : (
          <div className="overflow-auto">
          <svg
            viewBox={`0 0 ${fullGraph.width} ${fullGraph.height}`}
            className="block max-w-none"
            style={{ width: fullGraph.width, height: fullGraph.height }}
            role="img"
            aria-label="RouteDeck full site graph"
          >
            <defs>
              <marker id="routeDeckArrowFull" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L10,5 L0,10 z" fill="#64748b" />
              </marker>
              <marker id="routeDeckArrowFullActive" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L10,5 L0,10 z" fill="#38bdf8" />
              </marker>
            </defs>
            <rect width={fullGraph.width} height={fullGraph.height} fill="#020617" />
            <g opacity="0.16" stroke="#64748b" strokeWidth="1">
              {fullGraph.orderedLanes.map((lane) => {
                const y = fullGraph.rowYs.get(lane) || 0
                return <line key={lane} x1="82" x2={fullGraph.width - 28} y1={y} y2={y} />
              })}
              {fullGraph.columnXs.map((x) => <line key={`full-v-${x}`} x1={x} x2={x} y1="48" y2={fullGraph.height - 36} />)}
            </g>
            {fullGraph.orderedLanes.map((lane) => {
              const y = fullGraph.rowYs.get(lane) || 0
              return (
                <text
                  key={`label-${lane}`}
                  data-route-lane={lane}
                  x="24"
                  y={y + 4}
                  fill="#94a3b8"
                  textAnchor="start"
                  fontSize="11"
                  fontWeight="700"
                  letterSpacing="1.5"
                >
                  {lane.toUpperCase()}
                </text>
              )
            })}
            {edges.map((edge) => {
              const source = fullGraph.positions.get(edge.from)
              const target = fullGraph.positions.get(edge.to)
              if (!source || !target) return null
              const active = edge.from === currentNodeId || edge.to === currentNodeId
              const sameLane = Math.abs(source.y - target.y) < 8
              const forward = sameLane ? source.x <= target.x : source.y <= target.y
              const sx = sameLane
                ? source.x + (forward ? nodeHalfWidth(source) : -nodeHalfWidth(source))
                : source.x
              const sy = sameLane
                ? source.y
                : source.y + (forward ? nodeHalfHeight(source) : -nodeHalfHeight(source))
              const tx = sameLane
                ? target.x + (forward ? -nodeHalfWidth(target) : nodeHalfWidth(target))
                : target.x
              const ty = sameLane
                ? target.y
                : target.y + (forward ? -nodeHalfHeight(target) : nodeHalfHeight(target))
              const bend = sameLane
                ? Math.max(42, Math.abs(tx - sx) / 2)
                : Math.max(54, Math.abs(ty - sy) / 2)
              const path = sameLane
                ? `M${sx},${sy} C${sx + (forward ? bend : -bend)},${sy} ${tx - (forward ? bend : -bend)},${ty} ${tx},${ty}`
                : `M${sx},${sy} C${sx},${sy + (forward ? bend : -bend)} ${tx},${ty - (forward ? bend : -bend)} ${tx},${ty}`
              return (
                <path
                  key={`full-edge-${edge.from}-${edge.to}-${edgeLabel(edge)}`}
                  d={path}
                  fill="none"
                  stroke={active ? '#38bdf8' : '#64748b'}
                  strokeOpacity={active ? 0.95 : 0.35}
                  strokeWidth={active ? 2.2 : 1.2}
                  markerEnd={active ? 'url(#routeDeckArrowFullActive)' : 'url(#routeDeckArrowFull)'}
                />
              )
            })}
            {nodes.map((node) => {
              const position = fullGraph.positions.get(node.id)
              if (!position) return null
              return (
                <GraphNodeShape
                  key={`full-node-${node.id}`}
                  item={{ node, tone: position.tone, x: position.x, y: position.y, width: position.width, height: position.height }}
                  selected={selectedId === node.id}
                  onSelect={onSelectedNodeChange}
                />
              )
            })}
          </svg>
          </div>
        )}
      </div>

      <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-3 dark:border-white/10 dark:bg-white/[0.04]">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <div className="font-semibold text-slate-900 dark:text-white">{selectedNode?.label || 'Selected node'}</div>
            <div className="mt-0.5 font-mono text-[11px] text-slate-500 dark:text-slate-400">{selectedNode?.id || 'none'}</div>
          </div>
          <span className="rounded-full border border-slate-200 px-2 py-1 text-[10px] uppercase text-slate-500 dark:border-white/10 dark:text-slate-300">
            {selectedNode?.lane || 'node'}
          </span>
        </div>

        <div>
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-slate-400">Allowed actions</div>
          <div className="flex flex-wrap gap-2">
            {actions.length > 0 ? actions.map((action) => (
              <ActionPill key={action.id} action={action} valid={validActionIds.has(action.id) || selectedActionIds.includes(action.id)} />
            )) : <span className="rounded-full border border-dashed border-slate-200 px-3 py-1.5 text-slate-400 dark:border-white/10">No allowed actions</span>}
          </div>
        </div>

        {(selectedNode?.expected_input || selectedNode?.recovery_prompt) && (
          <div className="grid gap-2 sm:grid-cols-2">
            {selectedNode?.expected_input && (
              <div className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-slate-600 dark:border-white/10 dark:bg-black/20 dark:text-slate-300">
                <span className="font-semibold text-slate-800 dark:text-slate-100">Input:</span> {selectedNode.expected_input}
              </div>
            )}
            {selectedNode?.recovery_prompt && (
              <div className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900 dark:border-amber-500/30 dark:bg-amber-500/10 dark:text-amber-100">
                <span className="font-semibold">Recovery:</span> {selectedNode.recovery_prompt}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
