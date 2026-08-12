/**
 * Product-neutral public graph contract consumed by the shared ToolRouter
 * visualizer. Feature adapters may add identities and product metadata, but
 * the renderer depends only on this complete topology and recorded trace.
 */
export interface ToolRouterGraphNode {
  readonly id: string;
  readonly node_type: string;
  readonly label: string;
  readonly endpoint_id: string | null;
  readonly facets: Readonly<Record<string, string>>;
}

export interface ToolRouterGraphEdge {
  readonly id: string;
  readonly source: string;
  readonly target: string;
  readonly type: string;
  readonly status: string;
  readonly confidence: number;
}

export interface ToolRouterGraphTraceFrame {
  readonly index: number;
  readonly event_type: string;
  readonly active_endpoint_id: string | null;
  readonly added_node_ids: readonly string[];
  readonly updated_node_ids: readonly string[];
  readonly added_edge_ids: readonly string[];
  readonly cumulative_nodes: number;
  readonly cumulative_edges: number;
}

export interface ToolRouterSemanticGraph {
  readonly revision_id: string;
  readonly total_nodes: number;
  readonly total_edges: number;
  readonly nodes: readonly ToolRouterGraphNode[];
  readonly edges: readonly ToolRouterGraphEdge[];
  readonly trace: readonly ToolRouterGraphTraceFrame[];
}
