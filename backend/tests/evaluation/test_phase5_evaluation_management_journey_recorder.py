from pathlib import Path

SOURCE=Path('scripts/run_phase5_evaluation_management_journey.py').read_text(encoding='utf-8')

def test_recorder_is_evaluation_only_and_uses_retained_failures()->None:
    assert 'from run_phase5_builder_lifecycle_journey import' in SOURCE
    assert 'FAILED_ATTEMPT_ID = "2407a0fb-3f08-4b97-ab3c-eda164e029fd"' in SOURCE
    assert 'AGENT_ID = "3898dfc7-d177-489a-9537-06f0eaccf717"' in SOURCE
    assert 'CRUD_CASE_ID = "3096a341-d746-4a48-b371-fee6035ffd07"' in SOURCE
    assert "evaluation.retry_case_run" in SOURCE
    assert "evaluation.edit_case" in SOURCE
    assert "evaluation.delete_case" in SOURCE
    assert 'run_horizontal_product_journey' not in SOURCE

def test_recorder_proves_revision_retry_and_review_lineage()->None:
    assert "retry_of_attempt_id" in SOURCE
    assert "current_revision']!=2" in SOURCE
    assert 'name=\'Keep case\'' in SOURCE
    assert 'name=\'Remove case\'' in SOURCE
    assert "asyncio.timeout(13*60)" in SOURCE
