import { Field, FieldDescription, FieldLabel } from "@/components/ui/field"
import { Textarea } from "@/components/ui/textarea"
import type { FeaturePolicyDesign } from "@/workbench/types"

export function PolicyScopeEditor({ policies, onChange }: { policies: FeaturePolicyDesign; onChange: (policies: FeaturePolicyDesign) => void }) {
  return (
    <section aria-labelledby="agent-policy-heading" className="flex flex-col gap-4 border-t border-border pt-4">
      <div>
        <h2 id="agent-policy-heading" className="text-sm font-semibold">AgentPolicy</h2>
        <p className="text-xs text-muted-foreground">Write trusted agent guidance directly where it applies. Use one policy per line.</p>
      </div>

      <PolicyText id="feature-policy" label="Feature policy" policies={policies.policies} onChange={(next) => onChange({ ...policies, policies: next })} />

      {policies.nodes.map((node, nodeIndex) => (
        <div key={node.id} className="flex flex-col gap-3 border border-border p-3">
          <div><p className="text-xs font-semibold text-primary">Node</p><h3 className="text-sm font-semibold">{node.title} · {node.id}</h3></div>
          <PolicyText id={`node-${nodeIndex}-policy`} label="Node policy" policies={node.policies} onChange={(next) => updateNode(nodeIndex, { policies: next })} />

          {node.capabilities.map((capability, capabilityIndex) => (
            <PolicyText key={capability.id} id={`node-${nodeIndex}-capability-${capabilityIndex}-policy`} label={`Capability policy · ${capability.title}`} policies={capability.policies} onChange={(next) => updateNode(nodeIndex, { capabilities: node.capabilities.map((item, index) => index === capabilityIndex ? { ...item, policies: next } : item) })} />
          ))}

          {node.activeSurface && <PolicyText id={`node-${nodeIndex}-surface-policy`} label={`Surface policy · ${node.activeSurface.id}`} policies={node.activeSurface.policies} onChange={(next) => updateNode(nodeIndex, { activeSurface: { ...node.activeSurface!, policies: next } })} />}

          {node.operations.map((operation, operationIndex) => (
            <PolicyText key={operation.id} id={`node-${nodeIndex}-operation-${operationIndex}-policy`} label={`Operation policy · ${operation.id}`} policies={operation.policies} onChange={(next) => updateNode(nodeIndex, { operations: node.operations.map((item, index) => index === operationIndex ? { ...item, policies: next } : item) })} />
          ))}
        </div>
      ))}
    </section>
  )

  function updateNode(index: number, patch: Partial<FeaturePolicyDesign["nodes"][number]>) {
    onChange({ ...policies, nodes: policies.nodes.map((node, nodeIndex) => nodeIndex === index ? { ...node, ...patch } : node) })
  }
}

function PolicyText({ id, label, policies, onChange }: { id: string; label: string; policies: string[]; onChange: (policies: string[]) => void }) {
  return (
    <Field>
      <FieldLabel htmlFor={id}>{label}</FieldLabel>
      <Textarea id={id} className="min-h-16" value={policies.join("\n")} placeholder="Write policy guidance in plain language..." onChange={(event) => onChange(event.target.value.split("\n"))} />
      <FieldDescription className="text-xs">Plain-language design guidance. RouteDeck IDs and references are extracted later.</FieldDescription>
    </Field>
  )
}
