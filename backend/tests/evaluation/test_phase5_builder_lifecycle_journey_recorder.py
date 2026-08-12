from pathlib import Path


SOURCE = Path("scripts/run_phase5_builder_lifecycle_journey.py").read_text(encoding="utf-8")


def test_recorder_is_retained_builder_lifecycle_only() -> None:
    assert 'BUILD_ID = "c86897ee-daf6-44a5-95cc-5310370a24b5"' in SOURCE
    assert 'AGENT_ID = "c7a10ce0-b230-43f1-87d3-c79e71a84d34"' in SOURCE
    assert 'required=["builder.run","builder.pause","builder.run","builder.stop","builder.delete","builder.delete"]' in SOURCE
    assert 'await exact_agent.wait_for(state="visible", timeout=30_000)' in SOURCE
    assert 'await card.wait_for(state="visible", timeout=30_000)' in SOURCE
    assert "Assemble accepted build" not in SOURCE
    assert "run_horizontal_product_journey" not in SOURCE


def test_recorder_proves_review_and_immutable_history() -> None:
    assert "async def _submit_sign_in" in SOURCE
    assert "await email_input.input_value() != email" in SOURCE
    assert "await password_input.input_value() != password" in SOURCE
    assert 'name="Keep build unchanged",exact=True' in SOURCE
    assert 'name="Remove draft runtime",exact=True' in SOURCE
    assert 'before["lineage"]!=after["lineage"]' in SOURCE
    assert 'before["cases"]!=after["cases"]' in SOURCE
    assert '"maximizedSurface":True' in SOURCE
    assert "asyncio.timeout(13*60)" in SOURCE
    assert 'parser.add_argument("--verify-existing", action="store_true")' in SOURCE
    assert 'get_by_text("The draft runtime was removed.",exact=False)' in SOURCE
