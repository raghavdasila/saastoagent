from __future__ import annotations

from typing import Any

from backend.core.models import EntryStage
from backend.core.schemas import EntryGraphMessage

from .graph_runtime import EntryTurnRuntime
from .graph_spec import EntryNodeSpec


def stream_chunks(content: str) -> list[str]:
    return [content] if content else []


async def emit_stage_started(runtime: EntryTurnRuntime, stage_record: EntryStage) -> None:
    await runtime.emit(
        "stage_started",
        {
            "type": "stage_started",
            "turn_id": str(runtime.run_record.id),
            "run_id": str(runtime.run_record.id),
            "session_id": str(runtime.session_record.id),
            "stage_id": stage_record.stage_id,
            "parent_stage_id": stage_record.parent_stage_id,
            "depends_on": stage_record.depends_on or [],
            "sequence": stage_record.sequence,
            "lane": stage_record.lane,
            "status": stage_record.status,
            "started_at": stage_record.started_at.isoformat() if stage_record.started_at else None,
            "input": stage_record.input_payload,
        },
    )


async def emit_stage_completed(
    runtime: EntryTurnRuntime,
    stage_record: EntryStage,
    *,
    output_payload: dict[str, Any] | None = None,
) -> None:
    await runtime.emit(
        "stage_completed",
        {
            "type": "stage_completed",
            "turn_id": str(runtime.run_record.id),
            "run_id": str(runtime.run_record.id),
            "session_id": str(runtime.session_record.id),
            "stage_id": stage_record.stage_id,
            "parent_stage_id": stage_record.parent_stage_id,
            "sequence": stage_record.sequence,
            "lane": stage_record.lane,
            "status": stage_record.status,
            "started_at": stage_record.started_at.isoformat() if stage_record.started_at else None,
            "completed_at": stage_record.completed_at.isoformat() if stage_record.completed_at else None,
            "duration_ms": stage_record.duration_ms,
            "output": output_payload if output_payload is not None else stage_record.output_payload,
            "error": stage_record.error,
        },
    )


async def record_and_stream_messages(
    *,
    runtime: EntryTurnRuntime,
    node_spec: EntryNodeSpec,
    stage_id: str,
    messages: list[Any],
    emit_deltas: bool = True,
) -> None:
    for message in messages:
        if not isinstance(message, EntryGraphMessage):
            continue
        output_sequence = runtime.next_output_sequence()
        await runtime.store.record_output(
            run_record=runtime.run_record,
            session_record=runtime.session_record,
            stage_id=stage_id,
            sequence=output_sequence,
            lane=node_spec.lane.value,
            content=message.content,
        )
        if emit_deltas:
            chunks = stream_chunks(message.content)
            for index, chunk in enumerate(chunks):
                await runtime.emit(
                    "message_delta",
                    {
                        "content": chunk,
                        "stage_id": stage_id,
                        "lane": node_spec.lane.value,
                        "sequence": output_sequence,
                        "chunk_index": index,
                        "is_final": index == len(chunks) - 1,
                        "source": "stage_output",
                    },
                )
