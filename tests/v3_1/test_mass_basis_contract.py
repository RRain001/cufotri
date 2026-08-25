from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import jsonschema
import pytest

from cteas_ufotri.plant.mass_basis_v3_1 import (
    AreaBasis,
    AreaBasisKind,
    BasisCompatibilityError,
    BasisContractError,
    BasisConversionEvidence,
    BasisProvenance,
    ConversionStatus,
    MassBasis,
    MassBasisContract,
    TissueScope,
    TissueScopeKind,
    require_direct_comparison,
    validate_conversion_proposal,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/v3_1/mass_basis_contract.schema.json"


def provenance() -> BasisProvenance:
    return BasisProvenance(
        source_id="measurement-set-001",
        source_locator="lab/notebook/001",
        revision="rev-a",
        note="declared measurement basis",
    )


def contract(
    mass_basis: MassBasis,
    *,
    subject_id: str = "soybean-leaf-001",
    tissue: TissueScope | None = None,
    area: AreaBasis | None = None,
) -> MassBasisContract:
    return MassBasisContract(
        subject_id=subject_id,
        mass_basis=mass_basis,
        tissue_scope=tissue or TissueScope(TissueScopeKind.LEAF),
        area_basis=area or AreaBasis(AreaBasisKind.GROUND_AREA),
        provenance=provenance(),
    )


def test_contract_is_typed_immutable_and_value_free() -> None:
    value = contract(MassBasis.FRESH_MASS)
    assert value.mass_basis is MassBasis.FRESH_MASS
    assert value.conversion_status is ConversionStatus.NOT_REQUESTED
    assert value.conversion_evidence_id is None
    assert value.version == "v3.1-mass-basis-v1"
    with pytest.raises(FrozenInstanceError):
        value.subject_id = "changed"  # type: ignore[misc]


def test_contract_rejects_untyped_mass_basis() -> None:
    with pytest.raises(BasisContractError, match="MassBasis"):
        MassBasisContract(
            subject_id="sample",
            mass_basis="fresh_mass",  # type: ignore[arg-type]
            tissue_scope=TissueScope(TissueScopeKind.LEAF),
            area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
            provenance=provenance(),
        )


def test_declared_conversion_evidence_requires_explicit_evidence_id() -> None:
    with pytest.raises(BasisContractError, match="requires conversion_evidence_id"):
        MassBasisContract(
            subject_id="sample",
            mass_basis=MassBasis.FRESH_MASS,
            tissue_scope=TissueScope(TissueScopeKind.LEAF),
            area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
            provenance=provenance(),
            conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        )

    declared = MassBasisContract(
        subject_id="sample",
        mass_basis=MassBasis.FRESH_MASS,
        tissue_scope=TissueScope(TissueScopeKind.LEAF),
        area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
        provenance=provenance(),
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )
    assert declared.conversion_evidence_id == "fresh-dry-001"

    with pytest.raises(BasisContractError, match="only valid"):
        MassBasisContract(
            subject_id="sample",
            mass_basis=MassBasis.FRESH_MASS,
            tissue_scope=TissueScope(TissueScopeKind.LEAF),
            area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
            provenance=provenance(),
            conversion_evidence_id="orphan-evidence",
        )


def test_custom_scope_and_area_require_identifiers() -> None:
    with pytest.raises(BasisContractError, match="custom tissue"):
        TissueScope(TissueScopeKind.CUSTOM)
    with pytest.raises(BasisContractError, match="custom area"):
        AreaBasis(AreaBasisKind.CUSTOM)


def test_direct_comparison_requires_identical_mass_tissue_and_area_basis() -> None:
    left = contract(MassBasis.DRY_MASS, subject_id="sample-a")
    right = contract(MassBasis.DRY_MASS, subject_id="sample-b")
    require_direct_comparison(left, right)

    with pytest.raises(BasisCompatibilityError, match="mass basis mismatch"):
        require_direct_comparison(left, contract(MassBasis.FRESH_MASS))

    with pytest.raises(BasisCompatibilityError, match="tissue scope mismatch"):
        require_direct_comparison(
            left,
            contract(
                MassBasis.DRY_MASS,
                tissue=TissueScope(TissueScopeKind.GRAIN),
            ),
        )

    with pytest.raises(BasisCompatibilityError, match="area basis mismatch"):
        require_direct_comparison(
            left,
            contract(
                MassBasis.DRY_MASS,
                area=AreaBasis(AreaBasisKind.LEAF_AREA),
            ),
        )


def test_cross_basis_conversion_fails_closed_without_evidence() -> None:
    source = contract(MassBasis.FRESH_MASS)
    target = contract(MassBasis.DRY_MASS)
    with pytest.raises(BasisCompatibilityError, match="paired evidence"):
        validate_conversion_proposal(source, target, None)


def test_cross_basis_evidence_is_metadata_only_and_requires_paired_measurements() -> None:
    source = contract(MassBasis.FRESH_MASS)
    target = contract(MassBasis.DRY_MASS)

    with pytest.raises(BasisContractError, match="at least two"):
        BasisConversionEvidence(
            evidence_id="fresh-dry-001",
            source_basis=MassBasis.FRESH_MASS,
            target_basis=MassBasis.DRY_MASS,
            paired_measurement_ids=("pair-1",),
            provenance=provenance(),
        )

    evidence = BasisConversionEvidence(
        evidence_id="fresh-dry-001",
        source_basis=MassBasis.FRESH_MASS,
        target_basis=MassBasis.DRY_MASS,
        paired_measurement_ids=("pair-1-fresh", "pair-1-dry"),
        provenance=provenance(),
    )
    assert validate_conversion_proposal(source, target, evidence) is (
        ConversionStatus.EVIDENCE_DECLARED
    )
    assert not hasattr(evidence, "conversion_factor")
    assert not hasattr(evidence, "multiplier")


def test_conversion_evidence_direction_must_match_contracts() -> None:
    source = contract(MassBasis.FRESH_MASS)
    target = contract(MassBasis.DRY_MASS)
    reverse = BasisConversionEvidence(
        evidence_id="dry-fresh-001",
        source_basis=MassBasis.DRY_MASS,
        target_basis=MassBasis.FRESH_MASS,
        paired_measurement_ids=("pair-a", "pair-b"),
        provenance=provenance(),
    )
    with pytest.raises(BasisCompatibilityError, match="source basis"):
        validate_conversion_proposal(source, target, reverse)


def test_identity_proposal_needs_no_conversion_evidence() -> None:
    left = contract(MassBasis.WATER_MASS, subject_id="a")
    right = contract(MassBasis.WATER_MASS, subject_id="b")
    assert validate_conversion_proposal(left, right, None) is ConversionStatus.IDENTITY_ONLY


def test_json_schema_accepts_complete_contract_and_rejects_invalid_evidence_binding() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    payload = {
        "subject_id": "soybean-leaf-001",
        "mass_basis": "fresh_mass",
        "tissue_scope": {"kind": "leaf", "identifier": None},
        "area_basis": {"kind": "ground_area", "identifier": None},
        "provenance": {
            "source_id": "measurement-set-001",
            "source_locator": "lab/notebook/001",
            "revision": "rev-a",
            "note": None,
        },
        "conversion_status": "not_requested",
        "conversion_evidence_id": None,
        "version": "v3.1-mass-basis-v1",
    }
    jsonschema.validate(payload, schema)

    payload["tissue_scope"] = {"kind": "custom", "identifier": None}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)

    payload["tissue_scope"] = {"kind": "leaf", "identifier": None}
    payload["conversion_status"] = "evidence_declared"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)

    payload["conversion_evidence_id"] = "fresh-dry-001"
    jsonschema.validate(payload, schema)

    payload["conversion_status"] = "not_requested"
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(payload, schema)
