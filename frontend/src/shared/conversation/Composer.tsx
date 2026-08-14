import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";
import { ArrowUp, Paperclip, Square } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

export interface ComposerProps {
  disabled: boolean;
  showCancel?: boolean;
  disabledReason?: string;
  onSend(message: string): Promise<void>;
  onUploadApiSource?: (file: File) => Promise<ChatSourceUpload>;
  onCancel(): void;
  onRetry?: () => Promise<void>;
  onDiscardPending?: () => Promise<void>;
  onKeyboardSend?: () => void;
}

export interface ChatSourceUpload {
  readonly attachmentId: string;
  readonly displayName: string;
  readonly kind: "api_definition" | "api_description";
}

export function Composer({
  disabled,
  showCancel = disabled,
  disabledReason,
  onSend,
  onUploadApiSource,
  onCancel,
  onRetry,
  onDiscardPending,
  onKeyboardSend,
}: ComposerProps) {
  const [draft, setDraft] = useState("");
  const [definition, setDefinition] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const restoreKeyboardFocusRef = useRef(false);

  useEffect(() => {
    if (
      restoreKeyboardFocusRef.current &&
      !disabled &&
      !uploading &&
      onRetry === undefined
    ) {
      textareaRef.current?.focus();
      restoreKeyboardFocusRef.current = false;
    }
  }, [disabled, draft, onRetry, uploading]);

  const submit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (disabled || onRetry !== undefined || !draft.trim()) return;
      setError(null);
      try {
        setUploading(definition !== null);
        const uploaded = definition === null || onUploadApiSource === undefined
          ? null
          : await onUploadApiSource(definition);
        const message = uploaded === null
          ? draft.trim()
          : uploaded.kind === "api_description"
            ? `${draft.trim()}\n\nI attached the Markdown API description "${uploaded.displayName}" to this conversation.`
            : `${draft.trim()}\n\nI attached the API definition "${uploaded.displayName}" to this conversation.`;
        await onSend(message);
        setDraft("");
        setDefinition(null);
        if (fileRef.current !== null) fileRef.current.value = "";
      } catch (caught) {
        setError(
          caught instanceof Error
            ? caught
            : new Error("The chat message could not be sent."),
        );
      } finally { setUploading(false); }
    },
    [definition, disabled, draft, onRetry, onSend, onUploadApiSource],
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
      restoreKeyboardFocusRef.current = true;
      onKeyboardSend?.();
      event.currentTarget.form?.requestSubmit();
    },
    [onKeyboardSend],
  );

  return (
    <form onSubmit={(event) => void submit(event)} data-agent-composer="">
      <label className="sr-only" htmlFor="routedeck-agent-message">
        Message the assistant
      </label>
      <Textarea
        ref={textareaRef}
        id="routedeck-agent-message"
        name="message"
        value={draft}
        disabled={disabled || uploading || onRetry !== undefined}
        rows={1}
        placeholder="Message the assistant"
        aria-invalid={error !== null}
        onChange={(event) => setDraft(event.currentTarget.value)}
        onKeyDown={submitOnEnter}
      />
      {onUploadApiSource === undefined ? null : (
        <label data-chat-source-upload="">
          <Paperclip aria-hidden="true" />
          <strong>Attach API definition</strong>
          <input
            ref={fileRef}
            type="file"
            aria-label="Attach API definition"
            accept=".json,.yaml,.yml,.md,.markdown,application/json,application/yaml,text/yaml,text/markdown"
            disabled={disabled || uploading || onRetry !== undefined}
            onChange={(event) => setDefinition(event.currentTarget.files?.[0] ?? null)}
          />
          <span>{definition?.name ?? "No API definition attached"}</span>
        </label>
      )}
      <div>
        {onRetry === undefined ? (
          <Button
            type="submit"
            size="icon-lg"
            disabled={disabled || uploading || !draft.trim()}
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
      {uploading ? <p role="status">Adding the Source file to this conversation…</p> : null}
      {error === null ? null : (
        <p role="alert">Corpus could not complete that request. Try again.</p>
      )}
    </form>
  );
}
