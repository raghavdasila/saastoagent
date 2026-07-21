"""Validate the executable structural claims in the Corpus design notebook."""

from __future__ import annotations

import html
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = PROJECT_ROOT / "docs" / "corpus-routedeck-design-notebook.html"
EXPECTED_FEATURES = 15
EXPECTED_NODES = 53
EXPECTED_EDGES = 146

FEATURE_BLOCK = re.compile(
    r'<details\s+class="nav-feature"[^>]*>.*?'
    r'<summary>.*?<strong>(?P<feature>.*?)</strong>.*?</summary>.*?'
    r'<pre\s+class="graph-code">(?P<graph>.*?)</pre>.*?'
    r'</details>',
    re.DOTALL,
)
NODE_LINE = re.compile(r"^\[([a-z][a-z0-9_.]+)\]")
EDGE_LINE = re.compile(
    r"^([a-z][a-z0-9_.]+)\s*/\s*([a-z][a-z0-9_]*)\s*->\s*([a-z][a-z0-9_.]+)"
)
SCRIPT_BLOCK = re.compile(r"<script(?:\s[^>]*)?>(.*?)</script>", re.DOTALL | re.IGNORECASE)


@dataclass(frozen=True)
class Edge:
    source: str
    operation: str
    outcome: str
    target: str


def _plain_text(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


def parse_navgraph(document: str) -> tuple[list[str], list[str], list[Edge]]:
    features: list[str] = []
    nodes: list[str] = []
    edges: list[Edge] = []

    for block in FEATURE_BLOCK.finditer(document):
        features.append(_plain_text(block.group("feature")))
        current_node: str | None = None
        graph_text = _plain_text(block.group("graph"))
        for raw_line in graph_text.splitlines():
            line = raw_line.strip()
            node_match = NODE_LINE.match(line)
            if node_match:
                current_node = node_match.group(1)
                nodes.append(current_node)
                continue
            edge_match = EDGE_LINE.match(line)
            if edge_match:
                if current_node is None:
                    raise ValueError(f"Edge appears before a node declaration: {line}")
                edges.append(Edge(current_node, *edge_match.groups()))
    return features, nodes, edges


def validate_javascript(document: str) -> int:
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node.js is required to syntax-check the notebook's inline JavaScript.")
    scripts = [script for script in SCRIPT_BLOCK.findall(document) if script.strip()]
    if not scripts:
        raise ValueError("No inline JavaScript blocks found in the design notebook.")
    for index, script in enumerate(scripts, start=1):
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=f"-{index}.js",
            delete=False,
        ) as handle:
            handle.write(script)
            temporary_path = Path(handle.name)
        try:
            completed = subprocess.run(
                [node, "--check", str(temporary_path)],
                text=True,
                capture_output=True,
                check=False,
            )
            if completed.returncode != 0:
                detail = completed.stderr.strip() or completed.stdout.strip()
                raise ValueError(f"Inline script {index} failed Node.js syntax check:\n{detail}")
        finally:
            temporary_path.unlink(missing_ok=True)
    return len(scripts)


def validate(document: str) -> tuple[int, int, int, int]:
    features, nodes, edges = parse_navgraph(document)
    failures: list[str] = []

    if len(features) != EXPECTED_FEATURES:
        failures.append(f"feature count is {len(features)}, expected {EXPECTED_FEATURES}")
    if len(set(features)) != len(features):
        failures.append("feature names are not unique")
    if len(nodes) != EXPECTED_NODES:
        failures.append(f"node count is {len(nodes)}, expected {EXPECTED_NODES}")
    if len(set(nodes)) != len(nodes):
        failures.append("node identifiers are not unique")
    if len(edges) != EXPECTED_EDGES:
        failures.append(f"edge count is {len(edges)}, expected {EXPECTED_EDGES}")

    node_ids = set(nodes)
    missing_sources = sorted({edge.source for edge in edges if edge.source not in node_ids})
    missing_targets = sorted({edge.target for edge in edges if edge.target not in node_ids})
    if missing_sources:
        failures.append("undeclared edge sources: " + ", ".join(missing_sources))
    if missing_targets:
        failures.append("undeclared edge targets: " + ", ".join(missing_targets))

    for label, expected in (
        ("features", EXPECTED_FEATURES),
        ("nodes", EXPECTED_NODES),
        ("edges", EXPECTED_EDGES),
    ):
        if f">{expected} {label}<" not in document:
            failures.append(f"summary chip does not declare {expected} {label}")

    if failures:
        raise ValueError("Design notebook validation failed:\n- " + "\n- ".join(failures))

    script_count = validate_javascript(document)
    return len(features), len(nodes), len(edges), script_count


def main() -> int:
    document = NOTEBOOK.read_text(encoding="utf-8")
    features, nodes, edges, scripts = validate(document)
    print("Corpus design notebook validation passed")
    print(f"Notebook: {NOTEBOOK.relative_to(PROJECT_ROOT).as_posix()}")
    print(f"Features: {features}")
    print(f"Nodes: {nodes}")
    print(f"Edges: {edges}")
    print("Missing edge targets: 0")
    print(f"Inline scripts syntax-checked: {scripts}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
