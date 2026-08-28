#!/usr/bin/env python3
"""Machine-visible C2 qualification for UFOTRI coupled water/HTO hydrology.

C2 is qualification-only.  At every interval the C1 Eq. (33)-(37) closure is
recomputed from the current three-layer soil state, projected into the frozen
``ThreeLayerSoilForcing`` contract, and then advanced through the existing
soil->root->TFWT->OBT integrator.  No second soil or hydrology solver is created.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import math
from typing import Any

from cteas_ufotri.plant.leaf_exchange_resistance import ForcingProvenance
from cteas_ufotri.plant.obt_v3 import OBTState, OBTSolver, PlantBiologicalForcing
from cteas_ufotri.plant.root_v4 import (
    RootWaterFluxProvenanceV4,
    ThreeLayerRootWaterFluxForcingV4,
)
from cteas_ufotri.plant.soil_ufotri_v4 import (
    HydraulicRelationProvenance,
    TabulatedSoilHydraulicRelation,
    UFOTRIHydraulicProfile,
    build_ufotri_eq33_37_interlayer_fluxes,
    project_ufotri_hydrology_to_soil_forcing,
)
from cteas_ufotri.plant.soil_v4 import (
    SoilV4Provenance,
    ThreeLayerSoilForcing,
    ThreeLayerSoilState,
    ThreeLayerSoilStorageSolver,
)
from cteas_ufotri.plant.tfwt_v3 import TFWTState
from cteas_ufotri.v4_integration import (
    SELECTED_OPERATOR_SPLIT,
    V4SoilRootTFWTOBTIntegrator,
    V4SoilRootTFWTOBTState,
)


UTC = timezone.utc
STAGE = "UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION_R1"
HALF_LIFE_S = 388_789_632.0
TEST_KF_S = 2.0e-5
TEST_KR_S = 5.0e-6
LAYER_THICKNESSES_M = (0.05, 0.10, 0.15)
ROOT_Q_M_S = (1.0e-10, 2.0e-10, 1.0e-10)
WATER_TOL_M = 1.0e-12
HTO_TOL_BQ_M2 = 1.0e-9


def plant_provenance(resolution_s: float) -> ForcingProvenance:
    return ForcingProvenance(
        source_id="SYNTHETIC_C2_PLANT",
        source_version="r1",
        artifact_sha256="a" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=resolution_s,
    )


def soil_provenance(resolution_s: float) -> SoilV4Provenance:
    return SoilV4Provenance(
        source_id="SYNTHETIC_C2_SOIL",
        source_version="r1",
        artifact_sha256="b" * 64,
        spatial_reference="synthetic-common-soil-surface-area",
        temporal_resolution_s=resolution_s,
    )


def root_provenance() -> RootWaterFluxProvenanceV4:
    return RootWaterFluxProvenanceV4(
        source_id="SYNTHETIC_C2_ROOT_QW",
        source_locator="scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py",
        revision="r1",
        artifact_sha256="c" * 64,
        profile_context="SYNTHETIC_C2_EXPLICIT_ROOT_WATER_FLUX",
    )


def hydraulic_provenance(name: str) -> HydraulicRelationProvenance:
    return HydraulicRelationProvenance(
        source_id=f"SYNTHETIC_C2_{name}",
        source_version="r1",
        source_locator="scripts/v4/run_ufotri_coupled_water_hto_hydrology_verification_r1.py",
    )


def relation(
    *,
    name: str,
    theta: tuple[float, ...],
    head_m: tuple[float, ...],
    conductivity_m_s: tuple[float, ...],
) -> TabulatedSoilHydraulicRelation:
    return TabulatedSoilHydraulicRelation(
        theta=theta,
        matric_head_m=head_m,
        hydraulic_conductivity_m_s=conductivity_m_s,
        provenance=hydraulic_provenance(name),
    )


def gravity_profile() -> UFOTRIHydraulicProfile:
    # Equal matric head at every theta isolates gravity direction, while the
    # theta-dependent K makes dynamic recomputation observable across steps.
    return UFOTRIHydraulicProfile.uniform(
        relation(
            name="GRAVITY_PROFILE",
            theta=(0.05, 0.40),
            head_m=(-0.40, -0.40),
            conductivity_m_s=(1.0e-9, 8.0e-9),
        )
    )


def capillary_profile() -> UFOTRIHydraulicProfile:
    # Signed matric head rises with theta.  With wetter lower layers the
    # recovered Eq. (35) gradient is > 1 and therefore q is negative/upward.
    return UFOTRIHydraulicProfile.uniform(
        relation(
            name="CAPILLARY_PROFILE",
            theta=(0.05, 0.40),
            head_m=(-1.00, 0.00),
            conductivity_m_s=(5.0e-10, 5.0e-10),
        )
    )


def limiting_profile() -> UFOTRIHydraulicProfile:
    return UFOTRIHydraulicProfile.uniform(
        relation(
            name="DRY_WET_LIMIT_PROFILE",
            theta=(0.05, 0.30),
            head_m=(-0.50, -0.50),
            conductivity_m_s=(0.0, 2.0e-9),
        )
    )


def initial_state(
    *,
    dt_s: float,
    theta: tuple[float, float, float] = (0.18, 0.22, 0.26),
    concentrations_bq_m3: tuple[float, float, float] = (100.0, 200.0, 300.0),
    tfwt_inventory_bq_m2: float = 2.0,
    obt_inventory_bq_m2: float = 1.0,
) -> V4SoilRootTFWTOBTState:
    timestamp = datetime(2026, 1, 1, tzinfo=UTC)
    water = tuple(
        value * thickness for value, thickness in zip(theta, LAYER_THICKNESSES_M, strict=True)
    )
    hto = tuple(
        concentration * inventory
        for concentration, inventory in zip(concentrations_bq_m3, water, strict=True)
    )
    soil = ThreeLayerSoilState.from_inventories(
        soil_identifier="synthetic-c2-soil",
        water_inventories_m=water,
        hto_inventories_bq_m2=hto,
        timestamp=timestamp,
        provenance=soil_provenance(dt_s),
    )
    tfwt = TFWTState.from_inventory(
        plant_identifier="synthetic-c2-plant",
        crop="synthetic_crop",
        growth_stage="synthetic_stage",
        tfwt_inventory_bq_m2=tfwt_inventory_bq_m2,
        water_content_kg_m2=5.0,
        time=timestamp,
        provenance=plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    obt = OBTState.from_inventory(
        plant_identifier="synthetic-c2-plant",
        crop="synthetic_crop",
        growth_stage="synthetic_stage",
        obt_inventory_bq_m2=obt_inventory_bq_m2,
        plant_mass_kg_m2=2.0,
        timestamp=timestamp,
        provenance=plant_provenance(dt_s),
        area_basis="soil_surface_area",
    )
    return V4SoilRootTFWTOBTState(soil_state=soil, tfwt_state=tfwt, obt_state=obt)


def integrator() -> V4SoilRootTFWTOBTIntegrator:
    return V4SoilRootTFWTOBTIntegrator(
        soil_solver=ThreeLayerSoilStorageSolver(tritium_half_life_s=HALF_LIFE_S),
        obt_solver=OBTSolver(kf_s=TEST_KF_S, kr_s=TEST_KR_S),
    )


def root_forcing(
    state: V4SoilRootTFWTOBTState,
    *,
    water_uptake_fluxes_m_s: tuple[float, float, float] = ROOT_Q_M_S,
) -> ThreeLayerRootWaterFluxForcingV4:
    return ThreeLayerRootWaterFluxForcingV4(
        plant_identifier=state.plant_identifier,
        timestamp=state.timestamp,
        water_uptake_fluxes_m_s=water_uptake_fluxes_m_s,
        provenance=root_provenance(),
    )


def base_boundary_forcing(
    state: V4SoilRootTFWTOBTState,
    *,
    with_boundaries: bool,
) -> ThreeLayerSoilForcing:
    if not with_boundaries:
        return ThreeLayerSoilForcing(timestamp=state.timestamp)
    lower_water = 1.0e-10
    lower_concentration = state.soil_state.layers[2].hto_concentration_bq_m3_water
    return ThreeLayerSoilForcing(
        timestamp=state.timestamp,
        surface_water_input_m_s=2.0e-10,
        surface_water_loss_m_s=1.0e-10,
        surface_deposition_flux_bq_m2_s=1.0e-7,
        lower_boundary_water_loss_m_s=lower_water,
        lower_boundary_hto_loss_bq_m2_s=lower_water * lower_concentration,
        surface_reemission_hto_loss_bq_m2_s=2.0e-8,
    )


def state_vector(state: V4SoilRootTFWTOBTState) -> tuple[float, ...]:
    return (
        *(layer.water_inventory_m for layer in state.soil_state.layers),
        *(layer.hto_inventory_bq_m2 for layer in state.soil_state.layers),
        state.tfwt_state.inventory(),
        state.obt_state.inventory(),
    )


def max_abs_difference(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    return max(abs(a - b) for a, b in zip(left, right, strict=True))


def run_coupled_sequence(
    *,
    dt_s: float,
    duration_s: float,
    profile: UFOTRIHydraulicProfile,
    theta: tuple[float, float, float] = (0.18, 0.22, 0.26),
    root_q_m_s: tuple[float, float, float] = ROOT_Q_M_S,
    with_boundaries: bool = True,
    restart_at_s: float | None = None,
) -> dict[str, Any]:
    steps = int(round(duration_s / dt_s))
    if steps <= 0 or not math.isclose(steps * dt_s, duration_s, rel_tol=0.0, abs_tol=1.0e-9):
        raise ValueError("duration_s must be an exact positive multiple of dt_s")
    if restart_at_s is not None and not math.isclose(
        restart_at_s / dt_s,
        round(restart_at_s / dt_s),
        rel_tol=0.0,
        abs_tol=1.0e-12,
    ):
        raise ValueError("restart_at_s must align with dt_s")

    state = initial_state(dt_s=dt_s, theta=theta)
    model = integrator()
    initial_soil_water = state.soil_state.total_water_inventory_m
    initial_coupled_hto = (
        state.soil_state.total_hto_inventory_bq_m2
        + state.tfwt_state.inventory()
        + state.obt_state.inventory()
    )
    q_history: list[tuple[float, float]] = []
    max_water_residual = 0.0
    max_soil_hto_residual = 0.0
    max_coupled_hto_residual = 0.0
    max_root_water_identity = 0.0
    max_root_hto_identity = 0.0
    cumulative_external_water_input = 0.0
    cumulative_external_water_loss = 0.0
    cumulative_coupled_hto_input = 0.0
    cumulative_nonroot_hto_loss = 0.0
    cumulative_decay_loss = 0.0
    cumulative_obt_external_loss = 0.0
    total_root_transfer = 0.0
    total_lower_water_loss = 0.0
    total_lower_hto_loss = 0.0

    for index in range(steps):
        elapsed = index * dt_s
        if restart_at_s is not None and math.isclose(
            elapsed, restart_at_s, rel_tol=0.0, abs_tol=1.0e-9
        ):
            state = V4SoilRootTFWTOBTState.from_json(state.to_json())

        fluxes = build_ufotri_eq33_37_interlayer_fluxes(state.soil_state, profile)
        q_history.append((fluxes.l1_l2_water_flux_m_s, fluxes.l2_l3_water_flux_m_s))
        base = base_boundary_forcing(state, with_boundaries=with_boundaries)
        projected = project_ufotri_hydrology_to_soil_forcing(base, fluxes)
        result = model.advance(
            state,
            soil_forcing=projected,
            root_forcing=root_forcing(state, water_uptake_fluxes_m_s=root_q_m_s),
            biological_forcing=PlantBiologicalForcing(is_daylight=True),
            interval_seconds=dt_s,
        )

        soil_balance = result.soil_result.global_balance
        max_water_residual = max(max_water_residual, abs(soil_balance.water_residual_m))
        max_soil_hto_residual = max(max_soil_hto_residual, abs(soil_balance.hto_residual_bq_m2))
        max_coupled_hto_residual = max(
            max_coupled_hto_residual, abs(result.balance.coupled_residual_bq_m2)
        )
        max_root_water_identity = max(
            max_root_water_identity, abs(result.balance.soil_root_water_identity_residual_m)
        )
        max_root_hto_identity = max(
            max_root_hto_identity, abs(result.balance.soil_root_hto_identity_residual_bq_m2)
        )
        cumulative_external_water_input += soil_balance.external_water_input_m
        cumulative_external_water_loss += soil_balance.external_water_loss_m
        cumulative_coupled_hto_input += soil_balance.external_hto_input_bq_m2
        cumulative_nonroot_hto_loss += result.balance.soil_nonroot_external_hto_loss_bq_m2
        cumulative_decay_loss += result.balance.soil_decay_loss_bq_m2
        cumulative_obt_external_loss += result.balance.obt_external_loss_bq_m2
        total_root_transfer += result.root_plan.total_hto_transfer_bq_m2
        total_lower_water_loss += result.applied_soil_forcing.lower_boundary_water_loss_m_s * dt_s
        total_lower_hto_loss += result.applied_soil_forcing.lower_boundary_hto_loss_bq_m2_s * dt_s
        state = result.state

    final_soil_water = state.soil_state.total_water_inventory_m
    final_coupled_hto = (
        state.soil_state.total_hto_inventory_bq_m2
        + state.tfwt_state.inventory()
        + state.obt_state.inventory()
    )
    cumulative_water_residual = (
        cumulative_external_water_input
        - cumulative_external_water_loss
        - (final_soil_water - initial_soil_water)
    )
    cumulative_coupled_hto_residual = (
        cumulative_coupled_hto_input
        - cumulative_nonroot_hto_loss
        - cumulative_decay_loss
        - cumulative_obt_external_loss
        - (final_coupled_hto - initial_coupled_hto)
    )

    return {
        "final_state": state.to_mapping(),
        "final_vector": state_vector(state),
        "q_history": q_history,
        "max_abs_water_residual_m": max_water_residual,
        "max_abs_soil_hto_residual_bq_m2": max_soil_hto_residual,
        "max_abs_coupled_hto_residual_bq_m2": max_coupled_hto_residual,
        "max_abs_root_water_identity_residual_m": max_root_water_identity,
        "max_abs_root_hto_identity_residual_bq_m2": max_root_hto_identity,
        "cumulative_water_residual_m": cumulative_water_residual,
        "cumulative_coupled_hto_residual_bq_m2": cumulative_coupled_hto_residual,
        "total_root_hto_transfer_bq_m2": total_root_transfer,
        "total_lower_water_loss_m": total_lower_water_loss,
        "total_lower_hto_loss_bq_m2": total_lower_hto_loss,
    }


def signed_direction_probes() -> dict[str, Any]:
    down_state = initial_state(dt_s=900.0, theta=(0.20, 0.20, 0.20))
    down = build_ufotri_eq33_37_interlayer_fluxes(down_state.soil_state, gravity_profile())
    up_state = initial_state(dt_s=900.0, theta=(0.12, 0.20, 0.28))
    up = build_ufotri_eq33_37_interlayer_fluxes(up_state.soil_state, capillary_profile())
    return {
        "down_q_m_s": (down.l1_l2_water_flux_m_s, down.l2_l3_water_flux_m_s),
        "down_hto_bq_m2_s": (down.l1_l2_hto_flux_bq_m2_s, down.l2_l3_hto_flux_bq_m2_s),
        "up_q_m_s": (up.l1_l2_water_flux_m_s, up.l2_l3_water_flux_m_s),
        "up_hto_bq_m2_s": (up.l1_l2_hto_flux_bq_m2_s, up.l2_l3_hto_flux_bq_m2_s),
    }


def wet_dry_probe() -> dict[str, Any]:
    profile = limiting_profile()
    dry = build_ufotri_eq33_37_interlayer_fluxes(
        initial_state(dt_s=900.0, theta=(0.05, 0.05, 0.05)).soil_state,
        profile,
    )
    wet = build_ufotri_eq33_37_interlayer_fluxes(
        initial_state(dt_s=900.0, theta=(0.30, 0.30, 0.30)).soil_state,
        profile,
    )
    return {
        "dry_q_m_s": (dry.l1_l2_water_flux_m_s, dry.l2_l3_water_flux_m_s),
        "wet_q_m_s": (wet.l1_l2_water_flux_m_s, wet.l2_l3_water_flux_m_s),
    }


def boundary_and_root_probe() -> dict[str, Any]:
    dt_s = 900.0
    state = initial_state(dt_s=dt_s, theta=(0.20, 0.20, 0.20))
    fluxes = build_ufotri_eq33_37_interlayer_fluxes(state.soil_state, gravity_profile())
    projected = project_ufotri_hydrology_to_soil_forcing(
        base_boundary_forcing(state, with_boundaries=True),
        fluxes,
    )
    result = integrator().advance(
        state,
        soil_forcing=projected,
        root_forcing=root_forcing(state),
        biological_forcing=PlantBiologicalForcing(is_daylight=True),
        interval_seconds=dt_s,
    )
    expected_lower_water = projected.lower_boundary_water_loss_m_s * dt_s
    expected_lower_hto = projected.lower_boundary_hto_loss_bq_m2_s * dt_s
    return {
        "root_water_transfer_m": result.root_plan.total_water_transfer_m,
        "root_hto_transfer_bq_m2": result.root_plan.total_hto_transfer_bq_m2,
        "root_water_identity_residual_m": result.balance.soil_root_water_identity_residual_m,
        "root_hto_identity_residual_bq_m2": result.balance.soil_root_hto_identity_residual_bq_m2,
        "lower_water_loss_m": expected_lower_water,
        "lower_hto_loss_bq_m2": expected_lower_hto,
        "soil_external_water_loss_m": result.soil_result.global_balance.external_water_loss_m,
        "soil_nonroot_hto_loss_bq_m2": result.balance.soil_nonroot_external_hto_loss_bq_m2,
        "coupled_residual_bq_m2": result.balance.coupled_residual_bq_m2,
        "selected_operator_split": result.selected_operator_split,
    }


def refinement_probe() -> dict[str, Any]:
    duration_s = 14_400.0
    dts = (3600.0, 1800.0, 900.0, 450.0, 225.0)
    runs = {
        dt: run_coupled_sequence(
            dt_s=dt,
            duration_s=duration_s,
            profile=gravity_profile(),
            with_boundaries=True,
        )
        for dt in dts
    }
    reference = tuple(float(value) for value in runs[225.0]["final_vector"])
    errors = {
        str(int(dt)): max_abs_difference(
            tuple(float(value) for value in runs[dt]["final_vector"]), reference
        )
        for dt in dts[:-1]
    }
    return {
        "reference_dt_s": 225.0,
        "errors_to_reference": errors,
        "coarse_to_fine_order_s": (3600, 1800, 900, 450),
    }


def build_result() -> dict[str, Any]:
    direct = run_coupled_sequence(
        dt_s=900.0,
        duration_s=7200.0,
        profile=gravity_profile(),
        with_boundaries=True,
    )
    repeat = run_coupled_sequence(
        dt_s=900.0,
        duration_s=7200.0,
        profile=gravity_profile(),
        with_boundaries=True,
    )
    restarted = run_coupled_sequence(
        dt_s=900.0,
        duration_s=7200.0,
        profile=gravity_profile(),
        with_boundaries=True,
        restart_at_s=3600.0,
    )
    upward_dynamic = run_coupled_sequence(
        dt_s=900.0,
        duration_s=3600.0,
        profile=capillary_profile(),
        theta=(0.12, 0.20, 0.28),
        root_q_m_s=(0.0, 0.0, 0.0),
        with_boundaries=False,
    )
    directions = signed_direction_probes()
    limits = wet_dry_probe()
    boundary_root = boundary_and_root_probe()
    refinement = refinement_probe()
    refinement_errors = refinement["errors_to_reference"]
    ordered_errors = [float(refinement_errors[str(dt)]) for dt in (3600, 1800, 900, 450)]

    gates = {
        "water_balance_each_step": direct["max_abs_water_residual_m"] <= WATER_TOL_M,
        "soil_hto_balance_each_step": direct["max_abs_soil_hto_residual_bq_m2"] <= HTO_TOL_BQ_M2,
        "coupled_hto_balance_each_step": direct["max_abs_coupled_hto_residual_bq_m2"] <= HTO_TOL_BQ_M2,
        "cumulative_water_balance": abs(direct["cumulative_water_residual_m"]) <= WATER_TOL_M,
        "cumulative_coupled_hto_balance": abs(direct["cumulative_coupled_hto_residual_bq_m2"]) <= HTO_TOL_BQ_M2,
        "signed_downward_transport": all(value > 0.0 for value in directions["down_q_m_s"])
        and all(value > 0.0 for value in directions["down_hto_bq_m2_s"]),
        "signed_upward_transport": all(value < 0.0 for value in directions["up_q_m_s"])
        and all(value < 0.0 for value in directions["up_hto_bq_m2_s"]),
        "upward_dynamic_sequence": all(
            q12 < 0.0 and q23 < 0.0 for q12, q23 in upward_dynamic["q_history"]
        ),
        "dry_limit_zero_internal_flow": all(abs(value) <= 1.0e-30 for value in limits["dry_q_m_s"]),
        "wet_limit_positive_gravity_flow": all(value > 0.0 for value in limits["wet_q_m_s"]),
        "lower_boundary_exercised": boundary_root["lower_water_loss_m"] > 0.0
        and boundary_root["lower_hto_loss_bq_m2"] > 0.0,
        "root_sink_coupled_once": boundary_root["root_water_transfer_m"] > 0.0
        and boundary_root["root_hto_transfer_bq_m2"] > 0.0
        and abs(boundary_root["root_water_identity_residual_m"]) <= WATER_TOL_M
        and abs(boundary_root["root_hto_identity_residual_bq_m2"]) <= HTO_TOL_BQ_M2,
        "selected_operator_split_preserved": boundary_root["selected_operator_split"] == SELECTED_OPERATOR_SPLIT,
        "hydrology_recomputed_from_current_state": len(set(direct["q_history"])) > 1,
        "deterministic_repeat": repeat == direct,
        "restart_equivalence": restarted == direct,
        "timestep_refinement": ordered_errors[-1] < ordered_errors[0]
        and all(
            finer <= coarser * 1.05
            for coarser, finer in zip(ordered_errors, ordered_errors[1:], strict=True)
        ),
    }
    status = "PASS_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION" if all(gates.values()) else "HOLD_C2_GATE_FAILED"
    result: dict[str, Any] = {
        "schema_version": "v1",
        "stage": STAGE,
        "status": status,
        "source_kind": "SYNTHETIC_PROVENANCED_QUALIFICATION_ONLY",
        "gates": gates,
        "diagnostics": {
            "directions": directions,
            "wet_dry": limits,
            "boundary_root": boundary_root,
            "refinement": refinement,
            "direct_max_abs_water_residual_m": direct["max_abs_water_residual_m"],
            "direct_max_abs_soil_hto_residual_bq_m2": direct["max_abs_soil_hto_residual_bq_m2"],
            "direct_max_abs_coupled_hto_residual_bq_m2": direct["max_abs_coupled_hto_residual_bq_m2"],
            "direct_cumulative_water_residual_m": direct["cumulative_water_residual_m"],
            "direct_cumulative_coupled_hto_residual_bq_m2": direct["cumulative_coupled_hto_residual_bq_m2"],
            "direct_total_root_hto_transfer_bq_m2": direct["total_root_hto_transfer_bq_m2"],
            "direct_total_lower_water_loss_m": direct["total_lower_water_loss_m"],
            "direct_total_lower_hto_loss_bq_m2": direct["total_lower_hto_loss_bq_m2"],
            "dynamic_q_first_m_s": direct["q_history"][0],
            "dynamic_q_last_m_s": direct["q_history"][-1],
        },
        "hard_boundaries": {
            "existing_source_modified": False,
            "second_soil_solver_added": False,
            "second_hydrology_solver_added": False,
            "production_hydraulic_parameters": False,
            "calibration": False,
            "empirical_validation": False,
            "physical_accuracy_claim": False,
            "original_constitutive_curves_recovered": False,
            "original_numerical_discretization_recovered": False,
            "real_cteas_atmos_binding": False,
            "original_executable_equivalence": False,
        },
    }
    if status != "PASS_COUPLED_WATER_HTO_HYDROLOGY_VERIFICATION":
        failed = [name for name, passed in gates.items() if not passed]
        raise RuntimeError(f"C2 qualification gates failed: {failed}; diagnostics={json.dumps(result['diagnostics'], sort_keys=True)}")
    return result


def main() -> int:
    result = build_result()
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    print(f"UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_STATUS={result['status']}")
    print(f"UFOTRI_COUPLED_WATER_HTO_HYDROLOGY_RESULT_JSON={encoded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
