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
        self.assertIn("folder('connectors'", html)
        self.assertIn("folder('api'", html)
        self.assertIn("folder('web'", html)
        self.assertNotIn("folder('types'", html)
        self.assertIn('Agent Designer internals remain deliberately deferred', html)

    def test_toolrouter_evalset_generator_has_an_explicit_product_consumer(self) -> None:
        html = self.NOTEBOOK_PATH.read_text(encoding="utf-8")

        self.assertIn("file('processing.py'", html)
        self.assertIn('construct the graph/index, generate the evalset', html)
        self.assertIn("file('evalsets.py'", html)
        self.assertIn("file('eval_runner.py'", html)
        self.assertIn("file('EvalsetRunPanel.tsx'", html)
        self.assertIn('different source revisions', html)

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
