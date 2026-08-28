"""Opt-in UFOTRI Eq. (33)-(37) soil-hydrology closure.

The frozen ``soil_v4`` solver remains the authoritative inventory/conservation
core.  This module supplies only the missing manual hydrologic closure that can
be recovered without inventing constitutive parameters:

* Eq. (33): explicit total-potential decomposition helper;
* Eq. (35): Darcy water-flux relation;
* Eq. (36): matric-potential/conductivity internal inter-layer fluxes;
* Eq. (37): root sink stays an explicit external forcing owned by ``root_v4``.

The UFOTRI manual does not recover the original executable's constitutive
``K(theta)`` and ``Psi_m(theta)`` curves.  Consequently this module has no
production/default soil hydraulic parameterization.  Callers must provide a
versioned tabulated relation, interpolation is limited to the supplied domain,
and extrapolation fails closed.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from cteas_ufotri.plant.soil_v4 import ThreeLayerSoilForcing, ThreeLayerSoilState


STAGE_ID = "UFOTRI_EQ33_37_SOIL_HYDROLOGY_RECONSTRUCTION_R1"
EQ33_FORMULA_ID = "KFK4605_EQ33_TOTAL_SOIL_WATER_POTENTIAL"
EQ35_FORMULA_ID = "KFK4605_EQ35_DARCY_WATER_FLUX"
EQ36_FORMULA_ID = "KFK4605_EQ36_MATRIC_RICHARDS_FORM"
EQ37_ROLE_ID = "KFK4605_EQ37_EXTERNAL_ROOT_SINK"
INTERFACE_CONDUCTIVITY_RULE = "HARMONIC_MEAN_IMPLEMENTATION_CHOICE_NOT_MANUAL_SOURCE"
INTERPOLATION_RULE = "PIECEWISE_LINEAR_NO_EXTRAPOLATION_IMPLEMENTATION_CHOICE"


class UFOTRISoilHydrologyError(ValueError):
    """Raised when the manual-fidelity hydrology contract cannot be satisfied."""


def _finite(value: float, *, field: str) -> float:
    numeric = float(value)
    if not math.isfinite(numeric):
        raise UFOTRISoilHydrologyError(f"{field} must be finite")
    return numeric


def _nonempty(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise UFOTRISoilHydrologyError(f"{field} must be a non-empty string")
    return value


@dataclass(frozen=True)
class HydraulicRelationProvenance:
    """Identity of caller-supplied constitutive evidence.

    This is intentionally independent of production parameter activation.  It
    identifies the table used for a controlled/manual reconstruction case.
    """

    source_id: str
    source_version: str
    source_locator: str
    interpretation: str = "EXPLICIT_CALLER_SUPPLIED_NOT_UFOTRI_EXECUTABLE_RECOVERY"

    def __post_init__(self) -> None:
        _nonempty(self.source_id, field="source_id")
        _nonempty(self.source_version, field="source_version")
        _nonempty(self.source_locator, field="source_locator")
        _nonempty(self.interpretation, field="interpretation")


@dataclass(frozen=True)
class SoilPotentialComponents:
    """Manual Eq. (33) potential-head components in metres of water head."""

    matric_head_m: float
    osmotic_head_m: float = 0.0
    gravitational_head_m: float = 0.0
    pressure_or_gas_head_m: float = 0.0

    def __post_init__(self) -> None:
        for field in (
            "matric_head_m",
            "osmotic_head_m",
            "gravitational_head_m",
            "pressure_or_gas_head_m",
        ):
            _finite(getattr(self, field), field=field)

    @property
    def total_head_m(self) -> float:
        """Return Eq. (33): Psi = Psi_m + Psi_s + Psi_g + Psi_p."""

        return (
            self.matric_head_m
            + self.osmotic_head_m
            + self.gravitational_head_m
            + self.pressure_or_gas_head_m
        )


@dataclass(frozen=True)
class TabulatedSoilHydraulicRelation:
    """Explicit ``theta -> (Psi_m, K)`` constitutive relation.

    The table is an input contract rather than a built-in soil model.  Linear
    interpolation is a transparent numerical choice.  Extrapolation is
    forbidden because the available UFOTRI evidence does not authorize it.
    Matric heads are signed heads, not unsigned suction magnitudes.
    """

    theta: tuple[float, ...]
    matric_head_m: tuple[float, ...]
    hydraulic_conductivity_m_s: tuple[float, ...]
    provenance: HydraulicRelationProvenance
    interpolation_rule: str = INTERPOLATION_RULE

    def __post_init__(self) -> None:
        if self.interpolation_rule != INTERPOLATION_RULE:
            raise UFOTRISoilHydrologyError(
                f"interpolation_rule must be {INTERPOLATION_RULE!r}"
            )
        if len(self.theta) < 2:
            raise UFOTRISoilHydrologyError("at least two theta table points are required")
        if not (
            len(self.theta)
            == len(self.matric_head_m)
            == len(self.hydraulic_conductivity_m_s)
        ):
            raise UFOTRISoilHydrologyError("theta, matric_head_m and conductivity lengths must match")
        theta = tuple(_finite(value, field="theta") for value in self.theta)
        heads = tuple(_finite(value, field="matric_head_m") for value in self.matric_head_m)
        conductivities = tuple(
            _finite(value, field="hydraulic_conductivity_m_s")
            for value in self.hydraulic_conductivity_m_s
        )
        if any(value < 0.0 or value > 1.0 for value in theta):
            raise UFOTRISoilHydrologyError("theta table values must lie in [0, 1]")
        if any(right <= left for left, right in zip(theta, theta[1:])):
            raise UFOTRISoilHydrologyError("theta table values must be strictly increasing")
        if any(value < 0.0 for value in conductivities):
            raise UFOTRISoilHydrologyError("hydraulic conductivity cannot be negative")
        object.__setattr__(self, "theta", theta)
        object.__setattr__(self, "matric_head_m", heads)
        object.__setattr__(self, "hydraulic_conductivity_m_s", conductivities)

    def _interpolate(self, theta_value: float, values: tuple[float, ...], *, field: str) -> float:
        theta_value = _finite(theta_value, field="theta_value")
        if theta_value < self.theta[0] or theta_value > self.theta[-1]:
            raise UFOTRISoilHydrologyError(
                f"theta={theta_value!r} lies outside supplied constitutive domain "
                f"[{self.theta[0]!r}, {self.theta[-1]!r}]"
            )
        for index, tabulated in enumerate(self.theta):
            if theta_value == tabulated:
                return values[index]
        for index, (left, right) in enumerate(zip(self.theta, self.theta[1:])):
            if left < theta_value < right:
                weight = (theta_value - left) / (right - left)
                return values[index] + weight * (values[index + 1] - values[index])
        raise UFOTRISoilHydrologyError(f"could not interpolate {field}")

    def matric_potential_head_m(self, theta_value: float) -> float:
        return self._interpolate(theta_value, self.matric_head_m, field="matric_head_m")

    def conductivity_m_s(self, theta_value: float) -> float:
        return self._interpolate(
            theta_value,
            self.hydraulic_conductivity_m_s,
            field="hydraulic_conductivity_m_s",
        )


@dataclass(frozen=True)
class UFOTRIHydraulicProfile:
    """Per-layer constitutive relations for the canonical three-layer state."""

    layer_relations: tuple[
        TabulatedSoilHydraulicRelation,
        TabulatedSoilHydraulicRelation,
        TabulatedSoilHydraulicRelation,
    ]

    def __post_init__(self) -> None:
        if len(self.layer_relations) != 3:
            raise UFOTRISoilHydrologyError("exactly three layer relations are required")

    @classmethod
    def uniform(cls, relation: TabulatedSoilHydraulicRelation) -> "UFOTRIHydraulicProfile":
        return cls(layer_relations=(relation, relation, relation))


@dataclass(frozen=True)
class UFOTRIHydrologyFluxResult:
    """Eq. (36) internal fluxes projected to the frozen soil-core convention."""

    theta: tuple[float, float, float]
    matric_head_m: tuple[float, float, float]
    hydraulic_conductivity_m_s: tuple[float, float, float]
    layer_center_depth_m: tuple[float, float, float]
    l1_l2_water_flux_m_s: float
    l2_l3_water_flux_m_s: float
    l1_l2_hto_flux_bq_m2_s: float
    l2_l3_hto_flux_bq_m2_s: float
    interface_conductivity_rule: str = INTERFACE_CONDUCTIVITY_RULE
    root_sink_semantics: str = EQ37_ROLE_ID

    def __post_init__(self) -> None:
        if self.interface_conductivity_rule != INTERFACE_CONDUCTIVITY_RULE:
            raise UFOTRISoilHydrologyError("unexpected interface conductivity rule")
        if self.root_sink_semantics != EQ37_ROLE_ID:
            raise UFOTRISoilHydrologyError("root sink semantics must remain external Eq. (37)")


def ufotri_eq33_total_potential_head_m(
    *,
    matric_head_m: float,
    osmotic_head_m: float = 0.0,
    gravitational_head_m: float = 0.0,
    pressure_or_gas_head_m: float = 0.0,
) -> float:
    """Return the literal additive Eq. (33) potential-head identity."""

    return SoilPotentialComponents(
        matric_head_m=matric_head_m,
        osmotic_head_m=osmotic_head_m,
        gravitational_head_m=gravitational_head_m,
        pressure_or_gas_head_m=pressure_or_gas_head_m,
    ).total_head_m


def ufotri_eq35_water_flux_m_s(
    *,
    hydraulic_conductivity_m_s: float,
    potential_gradient_m_per_m: float,
    gravity_gradient_m_per_m: float = 1.0,
) -> float:
    """Evaluate manual Eq. (35), positive downward in the V4 soil convention.

    ``q = -K * (dPsi/dz - 1)`` for depth ``z`` positive downward.  Keeping the
    gravity term explicit makes the implementation auditable and yields
    ``q=+K`` for a uniform non-gravitational potential profile.
    """

    conductivity = _finite(hydraulic_conductivity_m_s, field="hydraulic_conductivity_m_s")
    gradient = _finite(potential_gradient_m_per_m, field="potential_gradient_m_per_m")
    gravity = _finite(gravity_gradient_m_per_m, field="gravity_gradient_m_per_m")
    if conductivity < 0.0:
        raise UFOTRISoilHydrologyError("hydraulic conductivity cannot be negative")
    return -conductivity * (gradient - gravity)


def _harmonic_mean(left: float, right: float) -> float:
    left = _finite(left, field="left_conductivity")
    right = _finite(right, field="right_conductivity")
    if left < 0.0 or right < 0.0:
        raise UFOTRISoilHydrologyError("conductivity cannot be negative")
    if left == 0.0 or right == 0.0:
        return 0.0
    return 2.0 * left * right / (left + right)


def _layer_theta_and_centers(
    state: ThreeLayerSoilState,
) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    theta_values: list[float] = []
    centers: list[float] = []
    for layer in state.layers:
        thickness = layer.depth_bottom_m - layer.depth_top_m
        if thickness <= 0.0:
            raise UFOTRISoilHydrologyError("layer thickness must be positive")
        theta = layer.water_inventory_m / thickness
        if not math.isfinite(theta) or theta < 0.0 or theta > 1.0:
            raise UFOTRISoilHydrologyError(
                f"derived volumetric water content for {layer.layer_id} must lie in [0, 1]"
            )
        theta_values.append(theta)
        centers.append(0.5 * (layer.depth_top_m + layer.depth_bottom_m))
    return tuple(theta_values), tuple(centers)  # type: ignore[return-value]


def _upwind_hto_flux_bq_m2_s(
    water_flux_m_s: float,
    *,
    upper_concentration_bq_m3: float,
    lower_concentration_bq_m3: float,
) -> float:
    concentration = (
        upper_concentration_bq_m3 if water_flux_m_s >= 0.0 else lower_concentration_bq_m3
    )
    concentration = _finite(concentration, field="donor_hto_concentration_bq_m3")
    if concentration < 0.0:
        raise UFOTRISoilHydrologyError("HTO donor concentration cannot be negative")
    return water_flux_m_s * concentration


def build_ufotri_eq33_37_interlayer_fluxes(
    state: ThreeLayerSoilState,
    profile: UFOTRIHydraulicProfile,
) -> UFOTRIHydrologyFluxResult:
    """Generate only the internal Eq. (36) water/HTO fluxes for ``soil_v4``.

    The reconstruction deliberately does not infer rainfall, evaporation,
    lower-boundary drainage, or Eq. (37) root uptake.  Those remain explicit
    boundary/sink inputs.  HTO is advected with the interval-start upwind donor
    concentration so signed water and HTO fluxes share the frozen soil-core
    convention.
    """

    theta, centers = _layer_theta_and_centers(state)
    heads = tuple(
        relation.matric_potential_head_m(theta_value)
        for relation, theta_value in zip(profile.layer_relations, theta)
    )
    conductivities = tuple(
        relation.conductivity_m_s(theta_value)
        for relation, theta_value in zip(profile.layer_relations, theta)
    )

    def interface_flux(upper_index: int, lower_index: int) -> float:
        distance = centers[lower_index] - centers[upper_index]
        if distance <= 0.0:
            raise UFOTRISoilHydrologyError("layer centers must increase with depth")
        gradient = (heads[lower_index] - heads[upper_index]) / distance
        interface_k = _harmonic_mean(
            conductivities[upper_index], conductivities[lower_index]
        )
        return ufotri_eq35_water_flux_m_s(
            hydraulic_conductivity_m_s=interface_k,
            potential_gradient_m_per_m=gradient,
        )

    q12 = interface_flux(0, 1)
    q23 = interface_flux(1, 2)
    concentrations = tuple(layer.hto_concentration_bq_m3_water for layer in state.layers)
    j12 = _upwind_hto_flux_bq_m2_s(
        q12,
        upper_concentration_bq_m3=concentrations[0],
        lower_concentration_bq_m3=concentrations[1],
    )
    j23 = _upwind_hto_flux_bq_m2_s(
        q23,
        upper_concentration_bq_m3=concentrations[1],
        lower_concentration_bq_m3=concentrations[2],
    )
    return UFOTRIHydrologyFluxResult(
        theta=theta,
        matric_head_m=heads,  # type: ignore[arg-type]
        hydraulic_conductivity_m_s=conductivities,  # type: ignore[arg-type]
        layer_center_depth_m=centers,
        l1_l2_water_flux_m_s=q12,
        l2_l3_water_flux_m_s=q23,
        l1_l2_hto_flux_bq_m2_s=j12,
        l2_l3_hto_flux_bq_m2_s=j23,
    )


def project_ufotri_hydrology_to_soil_forcing(
    base_forcing: ThreeLayerSoilForcing,
    fluxes: UFOTRIHydrologyFluxResult,
) -> ThreeLayerSoilForcing:
    """Inject C1 internal fluxes while preserving all RC1/replay boundaries.

    Existing non-zero internal fluxes are rejected rather than overwritten or
    added, preventing double counting between caller-supplied and UFOTRI closure
    routes.  Root extraction is copied exactly and therefore remains the Eq.
    (37) external sink.
    """

    occupied = (
        base_forcing.l1_l2_water_flux_m_s,
        base_forcing.l1_l2_hto_flux_bq_m2_s,
        base_forcing.l2_l3_water_flux_m_s,
        base_forcing.l2_l3_hto_flux_bq_m2_s,
    )
    if any(value != 0.0 for value in occupied):
        raise UFOTRISoilHydrologyError(
            "base forcing already contains interlayer transport; refusing hydrology double count"
        )
    return ThreeLayerSoilForcing(
        timestamp=base_forcing.timestamp,
        surface_water_input_m_s=base_forcing.surface_water_input_m_s,
        surface_water_loss_m_s=base_forcing.surface_water_loss_m_s,
        surface_deposition_flux_bq_m2_s=base_forcing.surface_deposition_flux_bq_m2_s,
        l1_l2_water_flux_m_s=fluxes.l1_l2_water_flux_m_s,
        l1_l2_hto_flux_bq_m2_s=fluxes.l1_l2_hto_flux_bq_m2_s,
        l2_l3_water_flux_m_s=fluxes.l2_l3_water_flux_m_s,
        l2_l3_hto_flux_bq_m2_s=fluxes.l2_l3_hto_flux_bq_m2_s,
        lower_boundary_water_loss_m_s=base_forcing.lower_boundary_water_loss_m_s,
        lower_boundary_hto_loss_bq_m2_s=base_forcing.lower_boundary_hto_loss_bq_m2_s,
        surface_reemission_hto_loss_bq_m2_s=base_forcing.surface_reemission_hto_loss_bq_m2_s,
        root_water_extraction_m_s=base_forcing.root_water_extraction_m_s,
        root_hto_extraction_bq_m2_s=base_forcing.root_hto_extraction_bq_m2_s,
        water_flux_unit=base_forcing.water_flux_unit,
        hto_flux_unit=base_forcing.hto_flux_unit,
        interval_semantics=base_forcing.interval_semantics,
    )
