from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from corpus.app import builder_adapters
from corpus.app.builder_adapters import _runtime_document
from corpus.features.builder.ports import BuilderUnavailable


def test_initial_valid_yaml_source_binds_the_exact_uploaded_document(tmp_path, monkeypatch):
    revision_dir = tmp_path / "r" / "revision-1"
    input_path = revision_dir / "i" / "store.yaml"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("openapi: 3.0.3\npaths: {}\n", encoding="utf-8")
    expected = {"openapi": "3.0.3", "paths": {}}
    monkeypatch.setattr(
        builder_adapters,
        "load_api_contract_documents",
        lambda _path: SimpleNamespace(
            raw_specs={"store": expected},
            repaired_specs={"store": expected},
        ),
    )

    document_path, document = _runtime_document(
        input_path=input_path,
        artifact_revision_id=None,
    )

    assert document_path == input_path
    assert document == expected


def test_repaired_yaml_source_requires_review_before_build(tmp_path, monkeypatch):
    revision_dir = tmp_path / "r" / "revision-1"
    input_path = revision_dir / "i" / "store.yaml"
    input_path.parent.mkdir(parents=True)
    input_path.write_text("openapi: 3.0.3\npaths: {}\n", encoding="utf-8")
    monkeypatch.setattr(
        builder_adapters,
        "load_api_contract_documents",
        lambda _path: SimpleNamespace(
            raw_specs={"store": {"openapi": "3.0.3", "paths": {}}},
            repaired_specs={
                "store": {
                    "openapi": "3.0.3",
                    "paths": {},
                    "x-corpus-repair": True,
                }
            },
        ),
    )

    with pytest.raises(BuilderUnavailable, match="Review the analyzed API changes"):
        _runtime_document(
            input_path=input_path,
            artifact_revision_id=None,
        )


def test_reviewed_revision_binds_its_exact_effective_json_document(tmp_path):
    revision_dir = tmp_path / "r" / "revision-2"
    input_path = revision_dir / "i" / "store.json"
    input_path.parent.mkdir(parents=True)
    expected = {"openapi": "3.0.3", "paths": {"/products": {}}}
    input_path.write_text(json.dumps(expected), encoding="utf-8")

    document_path, document = _runtime_document(
        input_path=input_path,
        artifact_revision_id="revision-1",
    )

    assert document_path == input_path
    assert document == expected
