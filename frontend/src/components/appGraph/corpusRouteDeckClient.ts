import {
  createRouteDeckStore,
  routeDeckUrlString,
  type RouteDeckClientState,
  type RouteDeckDispatchResult,
  type RouteDeckLocation,
  type RouteDeckLocationCodec,
} from '@routedeck/react'

import { api } from '@/lib/api'
import type { AppGraphState } from '@/types/appGraph'
import type { CorpusActionResponse, CorpusStateResponse } from '@/types/corpus'

import { corpusNodeIds } from './corpusRouteDeckCatalog'

export const SURFACE_QUERY_KEY = 'surface_id'

export function corpusStatePath(nodeId?: string, saasAgentId?: string, surfaceId?: string | null) {
  const params = new URLSearchParams()
  const effectiveNodeId = nodeId || (saasAgentId ? corpusNodeIds.agentHome : undefined)
  if (effectiveNodeId) params.set('node_id', effectiveNodeId)
  if (saasAgentId) params.set('saas_agent_id', saasAgentId)
  if (surfaceId) params.set(SURFACE_QUERY_KEY, surfaceId)
  const query = params.toString()
  return `/corpus/state${query ? `?${query}` : ''}`
}

export function createCorpusRouteCodec(activeSaaSAgentId?: string | null): RouteDeckLocationCodec {
  return {
    encode: (location) => {
      const locationSaaSAgentId = typeof location.params?.saas_agent_id === 'string'
        ? location.params.saas_agent_id
        : activeSaaSAgentId || null
      const path = locationSaaSAgentId
        ? location.node_id === corpusNodeIds.agentHome
          ? `/app/agents/${locationSaaSAgentId}`
          : `/app/agents/${locationSaaSAgentId}/${location.node_id}`
        : location.node_id === corpusNodeIds.home
          ? '/app/home'
          : `/app/${location.node_id}`
      const params = new URLSearchParams()
      if (location.surface_id) params.set(SURFACE_QUERY_KEY, location.surface_id)
      const search = params.toString()
      return { pathname: path, search: search ? `?${search}` : '', hash: '' }
    },
    decode: (url) => {
      const params = new URLSearchParams(url.search || '')
      const agentNodeMatch = url.pathname.match(/^\/app\/agents\/([^/]+?)(?:\/([^/]+))?$/)
      if (agentNodeMatch) {
        return {
          node_id: agentNodeMatch[2] || corpusNodeIds.agentHome,
          surface_id: params.get(SURFACE_QUERY_KEY),
          params: { saas_agent_id: agentNodeMatch[1] },
        }
      }
      const nodeMatch = url.pathname.match(/^\/app\/([^/]+)$/)
      if (nodeMatch) {
        return {
          node_id: nodeMatch[1],
          surface_id: params.get(SURFACE_QUERY_KEY),
          params: {},
        }
      }
      return null
    },
  }
}

export function corpusPathFromLocation(location: RouteDeckLocation, activeSaaSAgentId?: string | null): string {
  return routeDeckUrlString(createCorpusRouteCodec(activeSaaSAgentId).encode(location))
}

export function corpusPathFromRouteDeckState(state: RouteDeckClientState): string | null {
  const location = state.projection.navigation?.current
  if (!location?.node_id) return state.location || null
  return corpusPathFromLocation(
    {
      node_id: location.node_id,
      surface_id: location.surface_id || null,
      params: {
        ...(location.params || {}),
        ...(activeSaaSAgentIdFromRouteDeckState(state) ? { saas_agent_id: activeSaaSAgentIdFromRouteDeckState(state) } : {}),
      },
    },
    activeSaaSAgentIdFromRouteDeckState(state),
  )
}

export function corpusLocationFromBrowser(pathname: string, search: string): RouteDeckLocation | null {
  return createCorpusRouteCodec().decode({ pathname, search, hash: '' })
}

export function createSaaStoAgentRouteDeckStore({
  initialState,
  statePath,
  nodeId,
  saasAgentId,
}: {
  initialState: CorpusStateResponse
  statePath: string
  nodeId?: string
  saasAgentId?: string
}) {
  return createRouteDeckStore({
    navigationMode: 'remote',
    locationCodec: createCorpusRouteCodec(saasAgentId),
    initialState: corpusStateToRouteDeckState(initialState),
    snapshot: async () => corpusStateToRouteDeckState(await api.get<CorpusStateResponse>(statePath)),
    dispatch: async (input, currentState) => {
      const graphState = graphStateFromRouteDeckState(currentState)
      if (!graphState) throw new Error('Graph state is unavailable')
      const response = await api.post<CorpusActionResponse>('/corpus/action', {
        state: graphState,
        node_id: graphState.node || nodeId,
        saas_agent_id: graphState.active_saas_agent_id || saasAgentId,
        operation_id: input.operation_id,
        args: input.args || {},
        projection_version: currentState.projection.projection_version || 1,
      })
      return corpusActionToDispatchResult(response, input.operation_id)
    },
  })
}

export function corpusStateToRouteDeckState(response: CorpusStateResponse): RouteDeckClientState {
  return {
    projection: response.projection,
    status: 'idle',
    graph_state: response.state as unknown as Record<string, unknown>,
    location: response.replace_path || null,
  }
}

export function corpusActionToDispatchResult(
  response: CorpusActionResponse,
  operationId: string,
): RouteDeckDispatchResult {
  return {
    operation_id: operationId,
    accepted: true,
    state: corpusStateToRouteDeckState({
      state: response.state,
      projection: response.projection,
      replace_path: response.replace_path,
    }),
    active_surface: response.active_surface || null,
    messages: response.messages.map((message) => ({ ...message })),
    events: [],
    metadata: {},
  }
}

export function graphStateFromRouteDeckState(state: RouteDeckClientState): AppGraphState | null {
  const graphState = state.graph_state
  if (!graphState || typeof graphState.node !== 'string') return null
  return graphState as unknown as AppGraphState
}

export function activeSaaSAgentIdFromRouteDeckState(state: RouteDeckClientState): string | null {
  return graphStateFromRouteDeckState(state)?.active_saas_agent_id || null
}
