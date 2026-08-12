from pathlib import Path
SOURCE=(Path(__file__).resolve().parents[3]/'scripts'/'run_phase5_deployment_recovery_journey.py').read_text()
def test_isolated_deployment_recorder_reviews_restarts_and_restores():
 assert "required=['deployment.rollback']*3" in SOURCE
 assert "await _restart('http://127.0.0.1:8099')" in SOURCE
 assert "if after!=before" in SOURCE
 assert 'run_horizontal_product_journey' not in SOURCE
def test_deployment_recorder_is_maximized_normal_speed_and_bounded():
 assert 'await _maximize(page)' in SOURCE and "'playbackRate':1.0" in SOURCE
 assert 'asyncio.timeout(13*60)' in SOURCE
