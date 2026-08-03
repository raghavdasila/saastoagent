import {
  useCallback,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { ArrowUp, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export interface ComposerProps {
  disabled: boolean;
  showCancel?: boolean;
  disabledReason?: string;
  onSend(message: string): Promise<void>;
  onCancel(): void;
  onRetry?: () => Promise<void>;
  onDiscardPending?: () => Promise<void>;
}

export function Composer({
  disabled,
  showCancel = disabled,
  disabledReason,
  onSend,
  onCancel,
  onRetry,
  onDiscardPending,
}: ComposerProps) {
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<Error | null>(null);

  const submit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (disabled || onRetry !== undefined || !draft.trim()) return;
      setError(null);
      try {
        await onSend(draft.trim());
        setDraft("");
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught
            : new Error("The chat message could not be sent."),
        );
      }
    },
    [disabled, draft, onRetry, onSend],
  );

  const retry = useCallback(async () => {
    if (onRetry === undefined) return;
    setError(null);
    try {
      await onRetry();
      setDraft("");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught
          : new Error("The chat message could not be retried."),
      );
    }
  }, [onRetry]);

  const discard = useCallback(async () => {
    if (onDiscardPending === undefined) return;
    setError(null);
    try {
      await onDiscardPending();
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught
          : new Error("The chat request could not be abandoned safely."),
      );
    }
  }, [onDiscardPending]);

  const submitOnEnter = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      if (
        event.key !== "Enter" ||
        event.shiftKey ||
        event.nativeEvent.isComposing
      ) {
        return;
      }
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    },
    [],
  );

  return (
    <form onSubmit={(event) => void submit(event)} data-agent-composer="">
      <label className="sr-only" htmlFor="routedeck-agent-message">
        Message the assistant
      </label>
      <Textarea
        id="routedeck-agent-message"
        name="message"
        value={draft}
        disabled={disabled || onRetry !== undefined}
        rows={1}
        placeholder="Message the assistant"
        aria-invalid={error !== null}
        onChange={(event) => setDraft(event.currentTarget.value)}
        onKeyDown={submitOnEnter}
      />
      <div>
        {onRetry === undefined ? (
          <Button
            type="submit"
            size="icon-lg"
            disabled={disabled || !draft.trim()}
            aria-label="Send message"
          >
            <ArrowUp data-icon="inline-start" />
          </Button>
        ) : (
          <>
            <Button type="button" disabled={disabled} onClick={() => void retry()}>
              Retry exact message
            </Button>
            <Button
              type="button"
              variant="outline"
              disabled={disabled}
              onClick={() => void discard()}
            >
              Edit as new message
            </Button>
          </>
        )}
        {showCancel ? (
          <Button type="button" variant="outline" onClick={onCancel}>
            <Square data-icon="inline-start" />
            Stop response
          </Button>
        ) : null}
      </div>
      {disabledReason === undefined ? null : <p data-composer-disabled-reason="">{disabledReason}</p>}
      {error === null ? null : (
        <p role="alert">Corpus could not complete that request. Try again.</p>
      )}
    </form>
  );
}
