from __future__ import annotations

from pathlib import Path


APP_GRAPH_ROOT = Path(__file__).parents[1] / "services" / "app_graph"
FRONTEND_APP_GRAPH_ROOT = Path(__file__).parents[2] / "frontend" / "src" / "components" / "appGraph"


def test_corpus_surface_registry_is_thin_adapter_over_surface_catalog():
    registry_source = (APP_GRAPH_ROOT / "corpus_surfaces.py").read_text(encoding="utf-8")
    catalog_source = (APP_GRAPH_ROOT / "corpus_surface_catalog.py").read_text(encoding="utf-8")

    assert "CorpusSurfaceCatalog" in registry_source
    assert "CorpusSurfaceSpec" in catalog_source
    assert "elif state.node" not in registry_source
    assert registry_source.count("RouteDeckSurface(") <= 3


def test_surface_catalog_owns_product_surface_descriptors():
    catalog_source = (APP_GRAPH_ROOT / "corpus_surface_catalog.py").read_text(encoding="utf-8")

    for surface_id in [
        "learning.policy_gaps",
        "learning.failed_executions",
        "learning.policy_candidate.review",
        "saas_agent_select.active",
    ]:
        assert surface_id in catalog_source


def test_frontend_surface_rendering_is_split_from_shell_and_component_kit():
    shell_source = (FRONTEND_APP_GRAPH_ROOT / "AppGraphShell.tsx").read_text(encoding="utf-8")
    active_renderer_source = (FRONTEND_APP_GRAPH_ROOT / "corpusActiveSurfaces.tsx").read_text(encoding="utf-8")
    frame_source = (FRONTEND_APP_GRAPH_ROOT / "corpusFrameSurfaces.tsx").read_text(encoding="utf-8")
    component_source = (FRONTEND_APP_GRAPH_ROOT / "corpusSurfaces.tsx").read_text(encoding="utf-8")

    assert "function FrameSurfacePanel" not in shell_source
    assert "export function FrameSurfacePanel" in frame_source
    assert "const activeSurfaceRenderers" in active_renderer_source
    assert "RouteDeckSurfaceHost" in active_renderer_source
    assert "if (surface.component" not in active_renderer_source
    assert "export function AuthSurfaceCard" in component_source
    assert "export function ConnectionSetupSurface" in component_source
