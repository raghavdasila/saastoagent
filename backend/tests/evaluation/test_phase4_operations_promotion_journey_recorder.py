from __future__ import annotations

from pathlib import Path


SOURCE = Path("scripts/run_phase4_operations_promotion_journey.py").read_text(
    encoding="utf-8"
)


def test_recorder_is_exact_retained_phase4_promotion_only() -> None:
    assert 'CONVERSATION_ID = "Ttzpd0t0NBNtzYcXEDSoKj3a3zl901ZA"' in SOURCE
    assert 'AGENT_ID = "1f99c29b-0097-436e-af59-0dd6d0966ebf"' in SOURCE
    assert 'BUILD_ID = "bc1bd233-c2ac-48cd-ba36-8ab23f84c496"' in SOURCE
    assert 'INTERACTION_ID = "int_78f435f2522e47c5836a0e58ce7e88ed"' in SOURCE
    assert 'PUBLIC_SESSION_ID = "ses_07af5273655c49af96c6cc2a67d120aa"' in SOURCE
    assert "run_horizontal_product_journey" not in SOURCE
    assert "Create account" not in SOURCE
    assert "process_api" not in SOURCE
    assert "deployment.deploy" not in SOURCE


def test_recorder_uses_product_reset_and_normal_ui_then_revokes_credential() -> None:
    assert "service.request_password_reset" in SOURCE
    assert "service.confirm_password_reset" in SOURCE
    assert 'get_by_role("button", name="Sign in", exact=True)' in SOURCE
    assert "_owner_reset(destroy_password)" in SOURCE
    assert '"authEvidenceClaimed": False' in SOURCE
    assert "Credential canary reached the evidence directory" in SOURCE


def test_recorder_requires_exact_lineage_reload_and_evaluation_projection() -> None:
    assert 'filter(has_text=PUBLIC_SESSION_ID)' in SOURCE
    assert 'interaction.locator("section.operations-home__outcome")' in SOURCE
    assert 'outcome.get_by_text("Apparel", exact=False)' in SOURCE
    assert '"operations.promote_evaluation_case"' in SOURCE
    assert 'name="Evaluation case created", exact=True' in SOURCE
    assert "_promotion_record()" in SOURCE
    assert 'promotion.get("source_record_id") != INTERACTION_ID' in SOURCE
    assert 'promotion.get("build_id", "").replace("-", "")' in SOURCE
    assert 'has_text="Recorded interaction"' in SOURCE
    assert '"maximizedSurface": True' in SOURCE
    assert "asyncio.timeout(13 * 60)" in SOURCE
    assert 'parser.add_argument("--verify-existing", action="store_true")' in SOURCE
    assert "if not args.verify_existing:" in SOURCE
