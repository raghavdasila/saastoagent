export interface EvaluationEvidence {
  status: string
  definitionSha256: string
}

export type EvaluationResultState = "loading" | "not-run" | "passed" | "failed" | "stale"

export function canonicalEvaluationJson(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value)
  if (typeof value === "string") return asciiJsonString(value)
  if (Array.isArray(value)) return `[${value.map(canonicalEvaluationJson).join(",")}]`
  if (typeof value !== "object") throw new Error("Evaluation definitions must contain JSON values only.")

  const entries = Object.entries(value as Record<string, unknown>)
    .filter(([, item]) => item !== undefined)
    .sort(([left], [right]) => left < right ? -1 : left > right ? 1 : 0)
    .map(([key, item]) => `${asciiJsonString(key)}:${canonicalEvaluationJson(item)}`)
  return `{${entries.join(",")}}`
}

export async function evaluationDefinitionSha256(definition: unknown): Promise<string> {
  const bytes = new TextEncoder().encode(canonicalEvaluationJson(definition))
  const digest = await crypto.subtle.digest("SHA-256", bytes)
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("")
}

export function resolveEvaluationResultState(
  evidence: EvaluationEvidence | undefined,
  currentDefinitionSha256: string,
): Exclude<EvaluationResultState, "loading"> {
  if (!evidence) return "not-run"
  if (evidence.definitionSha256 !== currentDefinitionSha256) return "stale"
  return evidence.status === "passed" ? "passed" : "failed"
}

function asciiJsonString(value: string): string {
  return JSON.stringify(value).replace(/[\u0080-\uffff]/g, (character) =>
    `\\u${character.charCodeAt(0).toString(16).padStart(4, "0")}`,
  )
}
