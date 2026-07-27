import tempfile
import unittest
from pathlib import Path
import re
import subprocess

from scripts.feature_behavior_notebook import (
    FEATURES,
    parse_markdown,
    render_markdown,
    save_notes,
)


class FeatureBehaviorNotebookTests(unittest.TestCase):
    NOTEBOOK_PATH = Path(__file__).resolve().parents[1] / "docs" / "corpus-feature-behavior-notebook.html"

    def test_feature_set_matches_the_approved_basic_agent_slice(self) -> None:
        self.assertEqual(
            [feature["name"] for feature in FEATURES],
            [
                "Workspace",
                "Agents",
                "Source Hub",
                "API Source / API Collection",
                "Agent Designer",
                "Agent Builder",
                "Sandbox",
                "Evaluation",
                "Channels",
                "Deployment",
                "Operations",
            ],
        )

    def test_markdown_round_trip_preserves_multiline_notes(self) -> None:
        notes = {
            feature["id"]: f"First behavior for {feature['name']}.\n\nSecond behavior."
            for feature in FEATURES
        }

        markdown = render_markdown(notes, updated_at="2026-07-22T10:00:00+05:30")

        self.assertEqual(parse_markdown(markdown), notes)
        self.assertIn("## 4. API Source / API Collection", markdown)
        self.assertIn("Updated: 2026-07-22T10:00:00+05:30", markdown)

    def test_save_notes_atomically_writes_the_readable_markdown_file(self) -> None:
        notes = {feature["id"]: "" for feature in FEATURES}
        notes["agent-designer"] = "Generate a RouteDeck design from selected API operations."

        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "feature-behavior-notes.md"
            save_notes(
                notes,
                output_path=output_path,
                updated_at="2026-07-22T10:00:00+05:30",
            )

            saved = output_path.read_text(encoding="utf-8")
            self.assertEqual(parse_markdown(saved), notes)
            self.assertFalse(output_path.with_suffix(".md.tmp").exists())

    def test_render_rejects_missing_or_unknown_feature_keys(self) -> None:
        notes = {feature["id"]: "" for feature in FEATURES}
        notes.pop("operations")
        notes["learning"] = "Not part of this slice."

        with self.assertRaisesRegex(ValueError, "exactly the 11 approved feature keys"):
            render_markdown(notes)

    def test_structure_explorer_uses_connector_boundaries(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn('data-testid="structure-tree"', html)
        self.assertIn('data-testid="structure-inspector"', html)
        self.assertIn("Launch structure: proposal + implementation", html)
        self.assertIn("folder('connectors'", html)
        self.assertIn("folder('api'", html)
        self.assertIn("folder('web'", html)
        self.assertNotIn("folder('types'", html)
        self.assertIn('Agent Designer, Sandbox, public Web, Deployment, and Operations remain deferred', html)
        self.assertIn("status: 'planned'", html)
        self.assertIn("status: 'implemented'", html)
        self.assertIn("status: 'mixed'", html)
        self.assertIn('data-structure-legend', html)

    def test_structure_explorer_matches_the_implemented_sources_files(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        for filename in (
            "config.py",
            "contracts.py",
            "errors.py",
            "models.py",
            "repository.py",
            "service.py",
            "declarations.py",
            "feature.py",
            "bindings.py",
            "http.py",
            "base.py",
            "intake.py",
            "connector.py",
        ):
            self.assertIn(f"file('{filename}'", html)

        self.assertIn("file('handlers.py', 'Coordinates generic source", html)
        self.assertIn("file('registry.py', 'Maps a connector key", html)
        self.assertIn("file('processing.py'", html)
        self.assertIn("file('projections.py'", html)

    def test_structure_explorer_exposes_the_adapter_and_private_engine_boundary(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        for filename in (
            "settings.py",
            "contracts.py",
            "errors.py",
            "serialization.py",
            "adapter.py",
            "SOURCE.md",
            "source_manifest.json",
            "v1.json",
            "openapi_loader.py",
            "semantic_grag_router.py",
            "evalset_factory_experiment.py",
            "evalset_factory_export.py",
        ):
            self.assertIn(f"file('{filename}'", html)

        self.assertIn("private vendored engine snapshot", html)

    def test_structure_explorer_matches_the_debug_frontend_files(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("file('sourceClient.ts'", html)
        self.assertIn("file('SourceDebugSurface.tsx'", html)
        self.assertIn("file('sources.css'", html)
        self.assertIn("file('SourceList.tsx'", html)
        self.assertIn("file('ApiCollectionForm.tsx'", html)

    def test_toolrouter_evalset_generator_has_an_explicit_product_consumer(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("ToolRouterAdapter.ingest", html)
        self.assertIn("ToolRouterAdapter.generate_evalset", html)
        self.assertIn("source-grounded evalset", html)
        self.assertIn("evalset inspector", html)

    def test_structure_explorer_inline_javascript_is_valid(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")
        scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
        self.assertEqual(len(scripts), 1)

        with tempfile.TemporaryDirectory() as directory:
            script_path = Path(directory) / "notebook.js"
            script_path.write_text(scripts[0], encoding="utf-8")
            completed = subprocess.run(
                ["node", "--check", str(script_path)],
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
