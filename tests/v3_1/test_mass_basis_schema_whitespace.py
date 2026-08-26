from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import jsonschema
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/v3_1/mass_basis_contract.schema.json"


def valid_payload() -> dict[str, object]:
    return {
        "subject_id": "soybean-leaf-001",
        "mass_basis": "fresh_mass",
        "tissue_scope": {"kind": "leaf", "identifier": None},
        "area_basis": {"kind": "ground_area", "identifier": None},
        "provenance": {
            "source_id": "measurement-set-001",
            "source_locator": "lab/notebook/001",
            "revision": "rev-a",
            "note": "declared measurement basis",
        },
        "conversion_status": "not_requested",
        "conversion_evidence_id": None,
        "version": "v3.1-mass-basis-v1",
    }


def schema() -> dict[str, object]:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def assert_schema_rejects(payload: dict[str, object]) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema())


def test_schema_rejects_whitespace_only_subject_and_provenance_text() -> None:
    for field in ("subject_id",):
        payload = valid_payload()
        payload[field] = "   \t"
        assert_schema_rejects(payload)

    for field in ("source_id", "source_locator", "revision", "note"):
        payload = valid_payload()
        provenance = deepcopy(payload["provenance"])
        assert isinstance(provenance, dict)
        provenance[field] = "  \n  "
        payload["provenance"] = provenance
        assert_schema_rejects(payload)


def test_schema_rejects_whitespace_only_tissue_identifiers() -> None:
    payload = valid_payload()
    payload["tissue_scope"] = {"kind": "leaf", "identifier": "   "}
    assert_schema_rejects(payload)

    payload = valid_payload()
    payload["tissue_scope"] = {"kind": "custom", "identifier": "\t"}
    assert_schema_rejects(payload)


def test_schema_rejects_whitespace_only_area_identifiers() -> None:
    payload = valid_payload()
    payload["area_basis"] = {"kind": "ground_area", "identifier": "   "}
    assert_schema_rejects(payload)

    payload = valid_payload()
    payload["area_basis"] = {"kind": "custom", "identifier": "\n"}
    assert_schema_rejects(payload)


def test_schema_rejects_whitespace_only_declared_evidence_id() -> None:
    payload = valid_payload()
    payload["conversion_status"] = "evidence_declared"
    payload["conversion_evidence_id"] = "   "
    assert_schema_rejects(payload)


def test_schema_still_accepts_nonempty_text_and_null_optional_fields() -> None:
    payload = valid_payload()
    jsonschema.validate(payload, schema())

    payload["provenance"] = {
        "source_id": "measurement-set-001",
        "source_locator": "lab/notebook/001",
        "revision": "rev-a",
        "note": None,
    }
    payload["tissue_scope"] = {"kind": "leaf", "identifier": None}
    payload["area_basis"] = {"kind": "ground_area", "identifier": None}
    jsonschema.validate(payload, schema())
