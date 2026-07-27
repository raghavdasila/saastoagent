from __future__ import annotations

import json
from pathlib import Path

import numpy as np


class KeywordEmbeddingProvider:
    """Deterministic test-only provider; product construction uses MiniLM."""

    vocabulary = ("create", "list", "delete", "widget", "name", "identifier")

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        rows = []
        for text in texts:
            normalized = text.casefold()
            rows.append(
                [float(normalized.count(term)) for term in self.vocabulary]
            )
        return np.asarray(rows, dtype=np.float32)


def write_openapi_fixture(path: Path) -> Path:
    path.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "Widget API", "version": "1.0.0"},
                "paths": {
                    "/widgets": {
                        "get": {
                            "operationId": "listWidgets",
                            "summary": "List widgets",
                            "tags": ["widgets"],
                            "responses": {"200": {"description": "Widget list"}},
                        },
                        "post": {
                            "operationId": "createWidget",
                            "summary": "Create a widget",
                            "tags": ["widgets"],
                            "requestBody": {
                                "required": True,
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/CreateWidget"
                                        }
                                    }
                                },
                            },
                            "responses": {"201": {"description": "Widget created"}},
                        },
                    },
                    "/widgets/{widget_id}": {
                        "delete": {
                            "operationId": "deleteWidget",
                            "summary": "Delete a widget",
                            "tags": ["widgets"],
                            "parameters": [
                                {
                                    "name": "widget_id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "string"},
                                }
                            ],
                            "responses": {"204": {"description": "Widget deleted"}},
                        }
                    },
                },
                "components": {
                    "schemas": {
                        "CreateWidget": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {"name": {"type": "string"}},
                        }
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return path

