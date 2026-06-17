import inspect

from backend.services.discovery.activation import ActivationService


def test_activation_builds_fusion_router_index_before_ready():
    source = inspect.getsource(ActivationService.activate)

    assert "build_toolrouter_index_for_agent" in source
    assert '"step": "router_index"' in source
    assert source.index("generate_tools_for_connection") < source.index("build_toolrouter_index_for_agent")
    assert source.index("build_toolrouter_index_for_agent") < source.index("ActivationOverallStatus.ready")
