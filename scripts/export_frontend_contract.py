from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BACKEND_SOURCE = REPOSITORY_ROOT / "backend" / "src"
DEFAULT_OUTPUT = (
    REPOSITORY_ROOT
    / "frontend"
    / "src"
    / "routedeck"
    / "corpus-frontend-contract.generated.json"
)
sys.path.insert(0, str(BACKEND_SOURCE))

from corpus.composition import compile_corpus_app  # noqa: E402


def _serialized_contract() -> str:
    contract = compile_corpus_app().frontend_contract.model_dump(mode="json")
    return json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export or verify Corpus's compiled RouteDeck frontend contract."
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output = args.output.resolve()
    expected = _serialized_contract()
    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != expected:
            print(
                "Corpus frontend contract is stale. Run "
                ".\\.venv\\Scripts\\python.exe scripts\\export_frontend_contract.py",
                file=sys.stderr,
            )
            return 1
        print(f"Corpus frontend contract is current: {output}")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(expected, encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
