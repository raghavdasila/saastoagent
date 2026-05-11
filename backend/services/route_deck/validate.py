from __future__ import annotations

import json

from .catalog import build_route_deck_manifest, validate_route_deck_manifest


def main() -> None:
    errors = validate_route_deck_manifest()
    if errors:
        print("RouteDeck manifest validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    manifest = build_route_deck_manifest()
    print(
        json.dumps(
            {
                "status": "ok",
                "version": manifest.version,
                "nodes": len(manifest.nodes),
                "edges": len(manifest.edges),
                "actions": len(manifest.actions),
                "test_paths": len(manifest.test_paths),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
