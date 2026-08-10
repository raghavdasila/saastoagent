import type { ContractRevisionProposal } from "./contracts";
import type { SourceClient } from "./sourceClient";

interface ContractRevisionSnapshot {
  readonly proposal: ContractRevisionProposal | null;
  readonly loading: boolean;
  readonly error: string | null;
  readonly approvalSequence: number;
}

export class ContractRevisionStore {
  private value: ContractRevisionSnapshot = {
    proposal: null,
    loading: false,
    error: null,
    approvalSequence: 0,
  };
  private readonly listeners = new Set<() => void>();

  constructor(private readonly client: SourceClient) {}

  readonly snapshot = (): ContractRevisionSnapshot => this.value;
  readonly subscribe = (listener: () => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  async load(sourceId: string, proposalRef: string): Promise<void> {
    this.update({ ...this.value, loading: true, error: null });
    try {
      const proposals = await this.client.listContractRevisions(sourceId);
      const proposal = proposals.find(
        (item) => `contract-proposal-${item.proposal_id}` === proposalRef,
      );
      if (proposal === undefined) {
        throw new Error("The exact reviewed contract proposal is unavailable.");
      }
      this.update({ ...this.value, proposal, loading: false, error: null });
    } catch (error) {
      this.update({
        ...this.value,
        proposal: null,
        loading: false,
        error: error instanceof Error ? error.message : "The contract proposal is unavailable.",
      });
    }
  }

  reportError(message: string): void {
    this.update({ ...this.value, error: message, loading: false });
  }

  clearError(): void {
    this.update({ ...this.value, error: null });
  }

  markApproved(): void {
    this.update({
      ...this.value,
      proposal: this.value.proposal === null
        ? null
        : { ...this.value.proposal, state: "approved" },
      error: null,
      approvalSequence: this.value.approvalSequence + 1,
    });
  }

  private update(value: ContractRevisionSnapshot): void {
    this.value = value;
    this.listeners.forEach((listener) => listener());
  }
}
