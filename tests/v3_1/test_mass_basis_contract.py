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
    PairedMeasurement,
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


def leaf_scope() -> TissueScope:
    return TissueScope(TissueScopeKind.LEAF)


def ground_area() -> AreaBasis:
    return AreaBasis(AreaBasisKind.GROUND_AREA)


def contract(
    mass_basis: MassBasis,
    *,
    subject_id: str = "soybean-leaf-001",
    tissue: TissueScope | None = None,
    area: AreaBasis | None = None,
    conversion_status: ConversionStatus = ConversionStatus.NOT_REQUESTED,
    conversion_evidence_id: str | None = None,
) -> MassBasisContract:
    return MassBasisContract(
        subject_id=subject_id,
        mass_basis=mass_basis,
        tissue_scope=tissue or leaf_scope(),
        area_basis=area or ground_area(),
        provenance=provenance(),
        conversion_status=conversion_status,
        conversion_evidence_id=conversion_evidence_id,
    )


def pair(
    pair_id: str = "pair-1",
    source_id: str = "pair-1-fresh",
    target_id: str = "pair-1-dry",
) -> PairedMeasurement:
    return PairedMeasurement(
        pair_id=pair_id,
        source_measurement_id=source_id,
        target_measurement_id=target_id,
    )


def evidence(
    *,
    evidence_id: str = "fresh-dry-001",
    tissue: TissueScope | None = None,
    area: AreaBasis | None = None,
    pairs: tuple[PairedMeasurement, ...] | None = None,
) -> BasisConversionEvidence:
    return BasisConversionEvidence(
        evidence_id=evidence_id,
        source_basis=MassBasis.FRESH_MASS,
        target_basis=MassBasis.DRY_MASS,
        tissue_scope=tissue or leaf_scope(),
        area_basis=area or ground_area(),
        paired_measurements=pairs or (pair(),),
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
            tissue_scope=leaf_scope(),
            area_basis=ground_area(),
            provenance=provenance(),
        )


def test_contract_version_must_match_schema() -> None:
    with pytest.raises(BasisContractError, match="version must be"):
        MassBasisContract(
            subject_id="sample",
            mass_basis=MassBasis.FRESH_MASS,
            tissue_scope=leaf_scope(),
            area_basis=ground_area(),
            provenance=provenance(),
            version="future-unreviewed-version",
        )


def test_declared_conversion_evidence_requires_explicit_evidence_id() -> None:
    with pytest.raises(BasisContractError, match="requires conversion_evidence_id"):
        contract(
            MassBasis.FRESH_MASS,
            conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        )

    declared = contract(
        MassBasis.FRESH_MASS,
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )
    assert declared.conversion_evidence_id == "fresh-dry-001"

    with pytest.raises(BasisContractError, match="only valid"):
        contract(
            MassBasis.FRESH_MASS,
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


def test_paired_measurement_is_explicit_and_cannot_self_pair() -> None:
    value = pair()
    assert value.pair_id == "pair-1"
    assert value.source_measurement_id == "pair-1-fresh"
    assert value.target_measurement_id == "pair-1-dry"

    with pytest.raises(BasisContractError, match="distinct records"):
        PairedMeasurement(
            pair_id="bad-pair",
            source_measurement_id="same-record",
            target_measurement_id="same-record",
        )


def test_cross_basis_evidence_requires_explicit_nonreused_pairs() -> None:
    with pytest.raises(BasisContractError, match="at least one explicit"):
        BasisConversionEvidence(
            evidence_id="fresh-dry-001",
            source_basis=MassBasis.FRESH_MASS,
            target_basis=MassBasis.DRY_MASS,
            tissue_scope=leaf_scope(),
            area_basis=ground_area(),
            paired_measurements=(),
            provenance=provenance(),
        )

    with pytest.raises(BasisContractError, match="pair_id values must be unique"):
        evidence(
            pairs=(
                pair("pair-1", "fresh-1", "dry-1"),
                pair("pair-1", "fresh-2", "dry-2"),
            )
        )

    with pytest.raises(BasisContractError, match="cannot be reused"):
        evidence(
            pairs=(
                pair("pair-1", "fresh-1", "dry-1"),
                pair("pair-2", "fresh-1", "dry-2"),
            )
        )

    declared = evidence()
    assert declared.paired_measurements == (pair(),)
    assert not hasattr(declared, "conversion_factor")
    assert not hasattr(declared, "multiplier")


def test_conversion_evidence_direction_and_scope_must_match_contracts() -> None:
    source = contract(MassBasis.FRESH_MASS)
    target = contract(MassBasis.DRY_MASS)

    reverse = BasisConversionEvidence(
        evidence_id="dry-fresh-001",
        source_basis=MassBasis.DRY_MASS,
        target_basis=MassBasis.FRESH_MASS,
        tissue_scope=leaf_scope(),
        area_basis=ground_area(),
        paired_measurements=(pair(),),
        provenance=provenance(),
    )
    with pytest.raises(BasisCompatibilityError, match="source basis"):
        validate_conversion_proposal(source, target, reverse)

    grain_evidence = evidence(tissue=TissueScope(TissueScopeKind.GRAIN))
    with pytest.raises(BasisCompatibilityError, match="tissue scope"):
        validate_conversion_proposal(source, target, grain_evidence)

    leaf_area_evidence = evidence(area=AreaBasis(AreaBasisKind.LEAF_AREA))
    with pytest.raises(BasisCompatibilityError, match="area basis"):
        validate_conversion_proposal(source, target, leaf_area_evidence)


def test_declared_contract_evidence_id_must_match_supplied_evidence() -> None:
    source = contract(
        MassBasis.FRESH_MASS,
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-expected",
    )
    target = contract(MassBasis.DRY_MASS)

    with pytest.raises(BasisCompatibilityError, match="conversion_evidence_id"):
        validate_conversion_proposal(
            source,
            target,
            evidence(evidence_id="fresh-dry-other"),
        )

    matching = evidence(evidence_id="fresh-dry-expected")
    assert validate_conversion_proposal(source, target, matching) is (
        ConversionStatus.EVIDENCE_DECLARED
    )


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
