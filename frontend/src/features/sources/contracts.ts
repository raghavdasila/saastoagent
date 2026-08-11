export type SourceState = "accepted" | "queued" | "running" | "ready" | "failed";

export interface StagedApiAttachment {
  readonly attachment_id: string;
  readonly display_name: string;
  readonly filename: string;
  readonly content_sha256: string;
  readonly staged_at: string;
  readonly state: "staged" | "accepted";
  readonly source_id: string | null;
  readonly source_revision_id: string | null;
}

export interface StagedApiDescription {
  readonly attachment_id: string;
  readonly filename: string;
  readonly content_sha256: string;
  readonly staged_at: string;
  readonly state: "staged" | "saved";
  readonly source_id: string | null;
  readonly description_id: string | null;
}

export interface SourceDescriptionView {
  readonly description_id: string;
  readonly source_id: string;
  readonly filename: string;
  readonly content_sha256: string;
  readonly content: string;
  readonly created_at: string;
}

export interface SourceDependencyView {
  readonly source_id: string;
  readonly processing_state: SourceState;
  readonly attached_agent_ids: readonly string[];
  readonly build_ids: readonly string[];
  readonly design_revision_ids: readonly string[];
  readonly blocks_delete: boolean;
}

export interface SourceRevision {
  readonly revision_id: string;
  readonly source_id: string;
  readonly original_filename: string;
  readonly content_sha256: string;
  readonly description_filename: string | null;
  readonly description_sha256: string | null;
  readonly job_id: string | null;
  readonly state: SourceState;
  readonly created_at: string;
  readonly updated_at: string;
  readonly summary: Readonly<Record<string, unknown>>;
  readonly failure_code: string | null;
  readonly failure_message: string | null;
  readonly parent_revision_id: string | null;
  readonly artifact_revision_id: string | null;
}

export type ContractRevisionProposalState = "pending" | "approved";

export interface ContractPatchRecord {
  readonly patch_id: string;
  readonly kind: string;
  readonly schema_pointer: string;
  readonly field_name: string | null;
  readonly evidence_count: number;
  readonly impact_count: number;
}

export interface ContractRevisionProposal {
  readonly proposal_id: string;
  readonly source_id: string;
  readonly parent_revision_id: string;
  readonly state: ContractRevisionProposalState;
  readonly source_raw_sha256: string;
  readonly source_canonical_sha256: string;
  readonly repair_manifest_sha256: string;
  readonly repaired_parent_sha256: string;
  readonly final_canonical_sha256: string;
  readonly patches: readonly ContractPatchRecord[];
  readonly local_medusa_version: string;
  readonly local_package_json_sha256: string;
  readonly local_package_lock_sha256: string;
  readonly evidence_sha256: string;
  readonly proposed_at: string;
  readonly approved_by_owner_id: string | null;
  readonly approved_at: string | null;
  readonly approved_revision_id: string | null;
}

export interface SourceView {
  readonly source_id: string;
  readonly connector_key: string;
  readonly display_name: string;
  readonly created_at: string;
  readonly updated_at: string;
  readonly revision: SourceRevision;
}

export interface SourceInventoryClient {
  list(): Promise<readonly SourceView[]>;
}
