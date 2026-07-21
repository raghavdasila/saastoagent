from __future__ import annotations

import unittest

from scripts import validate_design_notebook


class DesignNotebookTests(unittest.TestCase):
    def test_current_navgraph_has_declared_counts_and_resolved_edges(self) -> None:
        document = validate_design_notebook.NOTEBOOK.read_text(encoding="utf-8")
        features, nodes, edges = validate_design_notebook.parse_navgraph(document)

        self.assertEqual(len(features), validate_design_notebook.EXPECTED_FEATURES)
        self.assertEqual(len(nodes), validate_design_notebook.EXPECTED_NODES)
        self.assertEqual(len(edges), validate_design_notebook.EXPECTED_EDGES)
        self.assertEqual(len(nodes), len(set(nodes)))
        self.assertFalse({edge.target for edge in edges} - set(nodes))


if __name__ == "__main__":
    unittest.main()
