from pathlib import Path

SOURCE=(Path(__file__).resolve().parents[3]/'scripts'/'run_phase5_channel_availability_journey.py').read_text(encoding='utf-8')

def test_channel_recorder_is_isolated_reviewed_and_restores_state():
    assert "required=['channels.set_enabled']*3" in SOURCE
    assert "public_status!={'before':200,'paused':503,'after':200}" in SOURCE
    assert "page.request.post(args.url+f'/api/public/agents/{SLUG}/sessions',data={})" in SOURCE
    assert "if after!=before" in SOURCE
    assert "Review pause" in SOURCE and "Review resume" in SOURCE
    assert 'run_horizontal_product_journey' not in SOURCE

def test_channel_recorder_is_maximized_normal_speed_and_bounded():
    assert 'await _maximize(page)' in SOURCE
    assert "'playbackRate':1.0" in SOURCE
    assert 'asyncio.timeout(13*60)' in SOURCE
    assert 'Credential canary reached Channel evidence' in SOURCE
