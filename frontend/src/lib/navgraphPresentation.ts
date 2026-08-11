import type { FrontendContract } from "@routedeck/core";


export function presentNavGraphContract(contract: FrontendContract): FrontendContract {
  return {
    ...contract,
    nodes: Object.fromEntries(Object.entries(contract.nodes).map(([id, node]) => [id, {
      ...node,
      title: presentNavGraphNodeTitle(id, node.title, contract.entry_node_id),
    }])),
  };
}

export function presentNavGraphNodeTitle(nodeId: string, title: string, entryNodeId: string): string {
  return nodeId === entryNodeId ? "Agent home" : presentSemanticLabel(title);
}

export function presentSemanticLabel(value: string): string {
  const label = value.replace(/[_-]+/g, " ").replace(/\s+/g, " ").trim();
  return label.length === 0 ? "Runtime area" : label[0]!.toUpperCase() + label.slice(1);
}
