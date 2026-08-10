import Graph from "graphology";
import { connectedComponents } from "graphology-components";
import forceAtlas2 from "graphology-layout-forceatlas2";

interface LayoutNode {
  readonly id: string;
  readonly node_type: string;
  readonly facets?: Readonly<Record<string, string>>;
}

interface LayoutEdge {
  readonly id: string;
  readonly source: string;
  readonly target: string;
}

interface Position { readonly id: string; readonly x: number; readonly y: number }

const TYPE_ANCHORS: Readonly<Record<string, readonly [number, number]>> = Object.freeze({
  api_operation: [0, 0],
  action: [3, 0],
  resource: [0, 3],
  api_shape: [-3, 0],
  api_schema: [-3, 2],
  api_inline_shape: [-4, 1],
  api_field: [-3, 3],
  permission: [0, -3],
  side_effect: [3, 3],
  doc_chunk: [3, -3],
  example_query: [-3, -3],
});

function hash32(value: string): number {
  let hash = 0x811c9dc5;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return hash >>> 0;
}

function initialPosition(node: LayoutNode) {
  const anchor = TYPE_ANCHORS[node.node_type] ?? [0, 0];
  const angle = (hash32(node.id) / 0xffffffff) * Math.PI * 2;
  const radius = 0.6 + (hash32(`${node.id}|semantic-layout`) / 0xffffffff) * 2.4;
  return { x: anchor[0] + Math.cos(angle) * radius, y: anchor[1] + Math.sin(angle) * radius };
}

function boundsFor(entries: readonly Position[]) {
  if (entries.length === 0) return { minX: 0, minY: 0, maxX: 0, maxY: 0, width: 1, height: 1 };
  const xs = entries.map(({ x }) => x);
  const ys = entries.map(({ y }) => y);
  const minX = Math.min(...xs); const maxX = Math.max(...xs);
  const minY = Math.min(...ys); const maxY = Math.max(...ys);
  return { minX, minY, maxX, maxY, width: Math.max(1, maxX - minX), height: Math.max(1, maxY - minY) };
}

function spread(entries: readonly Position[]): Position[] {
  const bounds = boundsFor(entries);
  const aspect = bounds.width / bounds.height;
  const scaleX = aspect < 1.35 ? 1.35 / aspect : 1;
  const scaleY = aspect > 2 ? aspect / 2 : 1;
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  return entries.map((entry) => ({
    ...entry,
    x: centerX + (entry.x - centerX) * scaleX,
    y: centerY + (entry.y - centerY) * scaleY,
  }));
}

function gridEntries(ids: readonly string[], spacing = 2.2): Position[] {
  const sorted = [...ids].sort();
  const columns = Math.max(1, Math.ceil(Math.sqrt(sorted.length)));
  return sorted.map((id, index) => ({ id, x: (index % columns) * spacing, y: Math.floor(index / columns) * spacing }));
}

function makeGroup(key: string, entries: readonly Position[], padding = 6) {
  const bounds = boundsFor(entries);
  return { key, entries, count: entries.length, bounds, width: bounds.width + padding * 2, height: bounds.height + padding * 2, padding };
}

function packGroups(groups: ReturnType<typeof makeGroup>[]) {
  const sorted = [...groups].sort((left, right) => right.count - left.count || right.width * right.height - left.width * left.height || left.key.localeCompare(right.key));
  const positions: Record<string, { x: number; y: number }> = {};
  if (sorted.length === 0) return positions;
  const place = (group: ReturnType<typeof makeGroup>, x: number, y: number) => {
    const offsetX = x + group.padding - group.bounds.minX;
    const offsetY = y + group.padding - group.bounds.minY;
    for (const entry of group.entries) positions[entry.id] = { x: entry.x + offsetX, y: entry.y + offsetY };
  };
  const dominant = sorted[0];
  place(dominant, 0, 0);
  const gap = 8;
  let cursorX = dominant.width + gap; let cursorY = 0; let columnWidth = 0;
  for (const group of sorted.slice(1)) {
    if (cursorY > 0 && cursorY + group.height > dominant.height) {
      cursorX += columnWidth + gap; cursorY = 0; columnWidth = 0;
    }
    place(group, cursorX, cursorY);
    cursorY += group.height + gap;
    columnWidth = Math.max(columnWidth, group.width);
  }
  const entries = Object.entries(positions).map(([id, point]) => ({ id, ...point }));
  const bounds = boundsFor(entries);
  const scale = 100 / Math.max(bounds.width, bounds.height, 1);
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  return Object.fromEntries(entries.map(({ id, x, y }) => [id, { x: (x - centerX) * scale, y: (y - centerY) * scale }]));
}

function computeLayout(nodes: readonly LayoutNode[], edges: readonly LayoutEdge[]) {
  const graph = new Graph({ type: "directed", multi: false, allowSelfLoops: true });
  for (const node of nodes) {
    if (!node.id) throw new Error("Every semantic graph node requires an ID.");
    if (graph.hasNode(node.id)) throw new Error(`Duplicate semantic graph node ${node.id}.`);
    graph.addNode(node.id, { ...initialPosition(node), nodeType: node.node_type });
  }
  for (const edge of edges) {
    if (!edge.id || !graph.hasNode(edge.source) || !graph.hasNode(edge.target)) throw new Error(`Semantic graph edge ${edge.id || "without ID"} is invalid.`);
    graph.addDirectedEdgeWithKey(edge.id, edge.source, edge.target, { weight: 1 });
  }

  const isolatedFields = new Map<string, string[]>();
  const excluded = new Set<string>();
  for (const node of nodes) {
    if (node.node_type !== "api_field" || graph.degree(node.id) !== 0) continue;
    const schema = node.facets?.schema ?? "unscoped";
    isolatedFields.set(schema, [...(isolatedFields.get(schema) ?? []), node.id]);
    excluded.add(node.id);
  }

  const groups: ReturnType<typeof makeGroup>[] = [];
  for (const component of connectedComponents(graph)) {
    const ids = component.filter((id) => !excluded.has(id)).sort();
    if (ids.length === 0) continue;
    const keep = new Set(ids);
    const local = new Graph({ type: "directed", multi: false, allowSelfLoops: true });
    for (const id of ids) local.addNode(id, graph.getNodeAttributes(id));
    graph.forEachEdge((key, attributes, source, target) => {
      if (keep.has(source) && keep.has(target)) local.addDirectedEdgeWithKey(key, source, target, attributes);
    });
    if (local.order <= 3) {
      ids.forEach((id, index) => local.mergeNodeAttributes(id, {
        x: Math.cos((index / Math.max(ids.length, 1)) * Math.PI * 2) * 2,
        y: Math.sin((index / Math.max(ids.length, 1)) * Math.PI * 2) * 2,
      }));
    } else {
      const inferred = forceAtlas2.inferSettings(local);
      forceAtlas2.assign(local, {
        iterations: local.order < 80 ? 120 : local.order < 800 ? 180 : 240,
        settings: {
          ...inferred,
          adjustSizes: true,
          barnesHutOptimize: local.order >= 100,
          edgeWeightInfluence: 0,
          gravity: 1,
          scalingRatio: Math.max(2, Math.sqrt(local.order) / 2),
          slowDown: 1,
          strongGravityMode: false,
        },
      });
    }
    groups.push(makeGroup(`component:${ids[0]}`, spread(ids.map((id) => ({ id, ...local.getNodeAttributes(id) } as Position)))));
  }
  for (const [schema, ids] of [...isolatedFields.entries()].sort(([left], [right]) => left.localeCompare(right))) {
    groups.push(makeGroup(`schema:${schema}`, gridEntries(ids), 4));
  }
  const positions = packGroups(groups);
  for (const node of nodes) if (positions[node.id] === undefined) positions[node.id] = initialPosition(node);
  return positions;
}

self.onmessage = (event: MessageEvent<{ type: string; requestId: string; nodes: readonly LayoutNode[]; edges: readonly LayoutEdge[] }>) => {
  if (event.data.type !== "layout") return;
  try {
    self.postMessage({ type: "layout-complete", requestId: event.data.requestId, positions: computeLayout(event.data.nodes, event.data.edges) });
  } catch (error) {
    self.postMessage({ type: "layout-error", requestId: event.data.requestId, error: error instanceof Error ? `${error.name}: ${error.message}` : String(error) });
  }
};
