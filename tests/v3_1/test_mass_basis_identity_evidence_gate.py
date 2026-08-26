from __future__ import annotations

import pytest

from cteas_ufotri.plant.mass_basis_v3_1 import (
    AreaBasis,
    AreaBasisKind,
    BasisCompatibilityError,
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


def provenance() -> BasisProvenance:
    return BasisProvenance(
        source_id="identity-gate-test",
        source_locator="tests/v3_1/test_mass_basis_identity_evidence_gate.py",
        revision="v1",
    )


def contract(
    *,
    subject_id: str,
    mass_basis: MassBasis = MassBasis.FRESH_MASS,
    conversion_status: ConversionStatus = ConversionStatus.NOT_REQUESTED,
    conversion_evidence_id: str | None = None,
) -> MassBasisContract:
    return MassBasisContract(
        subject_id=subject_id,
        mass_basis=mass_basis,
        tissue_scope=TissueScope(TissueScopeKind.LEAF),
        area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
        provenance=provenance(),
        conversion_status=conversion_status,
        conversion_evidence_id=conversion_evidence_id,
    )


def cross_basis_evidence(evidence_id: str = "fresh-dry-001") -> BasisConversionEvidence:
    return BasisConversionEvidence(
        evidence_id=evidence_id,
        source_basis=MassBasis.FRESH_MASS,
        target_basis=MassBasis.DRY_MASS,
        tissue_scope=TissueScope(TissueScopeKind.LEAF),
        area_basis=AreaBasis(AreaBasisKind.GROUND_AREA),
        paired_measurements=(
            PairedMeasurement(
                pair_id="pair-1",
                source_measurement_id="fresh-1",
                target_measurement_id="dry-1",
            ),
        ),
        provenance=provenance(),
    )


def test_clean_same_basis_conversion_proposal_is_identity_only() -> None:
    source = contract(subject_id="source")
    target = contract(subject_id="target")

    assert validate_conversion_proposal(source, target, None) is ConversionStatus.IDENTITY_ONLY


def test_same_basis_source_evidence_declared_cannot_bypass_binding() -> None:
    source = contract(
        subject_id="source",
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )
    target = contract(subject_id="target")

    with pytest.raises(BasisCompatibilityError, match="same-basis identity proposal"):
        validate_conversion_proposal(source, target, None)


def test_same_basis_target_evidence_declared_cannot_bypass_binding() -> None:
    source = contract(subject_id="source")
    target = contract(
        subject_id="target",
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )

    with pytest.raises(BasisCompatibilityError, match="same-basis identity proposal"):
        validate_conversion_proposal(source, target, None)


def test_same_basis_proposal_rejects_supplied_cross_basis_evidence() -> None:
    source = contract(subject_id="source")
    target = contract(subject_id="target")

    with pytest.raises(BasisCompatibilityError, match="must not supply"):
        validate_conversion_proposal(source, target, cross_basis_evidence())


def test_same_basis_declared_state_with_supplied_evidence_still_fails_closed() -> None:
    source = contract(
        subject_id="source",
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )
    target = contract(subject_id="target")

    with pytest.raises(BasisCompatibilityError, match="must not supply"):
        validate_conversion_proposal(source, target, cross_basis_evidence("fresh-dry-001"))


def test_direct_same_basis_comparison_does_not_consume_conversion_evidence_state() -> None:
    source = contract(
        subject_id="source",
        conversion_status=ConversionStatus.EVIDENCE_DECLARED,
        conversion_evidence_id="fresh-dry-001",
    )
    target = contract(subject_id="target")

    # Direct identity comparison is separate from conversion-proposal governance.
    require_direct_comparison(source, target)
