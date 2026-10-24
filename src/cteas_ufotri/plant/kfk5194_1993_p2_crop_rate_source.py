"""Opt-in primary-table transfer-source mapping for KfK5194 (1993) P2 R3.

The manual's printed p.22 names the specific COMA transfer edges used to
derive each crop's mean HTO->OBT rate. Printed pp.86-89 Tables 9-12 supply
daily transfer rates. Printed pp.17,22 provide dry mass and *12 sunlit hours*
per growth day for the advanced Eq.(33) uniform biomass rate.

Research-only: COMA transfer rates are not evidence that the original hourly
solver selected the same numeric array, and Table 1 labels g, not g/m2.
Therefore this module MUST NOT inject either the mean biomass value into
an Eq.(31) ground-area photosynthesis input or any rate into a production
inventory without separate source/units acceptance.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from pathlib import Path

import yaml

from cteas_ufotri.versioned_inputs_1993 import Historical1993SourceProfile, PROFILE_ID
from .kfk5194_1993_photo_obt_rates import KFK5194CropOrgan, KFK5194PhotoOBTError

_CORPUS_HASH = "10607b7f2911bc23f9fae138dd153bf46f20baa4b7b6669bbe5f7f4c49bfc220"
_SOURCE_RELATIVE = Path("docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml")
# Table 1 dry masses themselves print g only. Table 12's symbols retain
# 'tp' spellings although p.22 calls the wheat formation term T_w5,w8.
_EDGE = {
    KFK5194CropOrgan.GRASS_WHOLE:
        (10, "t5,6", "grass HTO", "grass OBT", "grass", 170.0, 30),
    KFK5194CropOrgan.LEAFY_VEGETABLE_WHOLE:
        (9, "t14,15", "plant HTO", "plant OBT", "leafy_vegetables", 160.0, 45),
    KFK5194CropOrgan.POTATO_TUBER:
        (11, "tp5,p8", "potato hto", "tuber OBT", "potatoes", 660.0, 90),
    KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED:
        (12, "tp5,p8", "wheat HTO", "seedling OBT", "winter_wheat", 519.0, 60),
}
# Comparison-only loss network. Three of these are NOT from the edible organ
# in the crop formation edge: they refer to parent plant grass/potato/wheat OBT.
_PARENT_OBT = {
    KFK5194CropOrgan.GRASS_WHOLE: "grass OBT",
    KFK5194CropOrgan.LEAFY_VEGETABLE_WHOLE: "plant OBT",
    KFK5194CropOrgan.POTATO_TUBER: "potato OBT",
    KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED: "wheat OBT",
}


@dataclass(frozen=True, slots=True)
class KFK5194OBTOutflow:
    to_as_printed: str
    symbol_as_printed: str
    rate_d_1: float


@dataclass(frozen=True, slots=True)
class KFK5194P2CropSourceRate:
    crop_organ: KFK5194CropOrgan
    table_no: int
    printed_page: int
    formation_symbol_as_table: str
    formation_symbol_as_p22: str
    formation_from_as_printed: str
    formation_to_as_printed: str
    mean_hto_to_obt_d_1: float
    mean_hto_to_obt_h_1: float
    dry_mass_g_as_printed: float
    growth_days_as_printed: int
    active_hours_per_growth_day: int
    mean_dry_matter_g_per_source_crop_unit_sunlit_h: float
    parent_obt_compartment: str
    parent_obt_outflows: tuple[KFK5194OBTOutflow, ...]
    parent_obt_total_outflow_d_1: float
    edible_obt_loss_per_day_as_printed: float | None
    symbol_alignment: str

    @property
    def parent_obt_isolated_survival_half_time_days(self) -> float:
        if self.parent_obt_total_outflow_d_1 == 0:
            return math.inf
        return math.log(2) / self.parent_obt_total_outflow_d_1

    def isolated_parent_obt_retention_fraction(self, elapsed_days: float) -> float:
        """Pure source-only diagnostic, not complete coupled COMA simulation."""
        if type(elapsed_days) not in (int, float) or not math.isfinite(elapsed_days) or elapsed_days < 0:
            raise KFK5194PhotoOBTError("elapsed days must be nonnegative finite")
        return math.exp(-self.parent_obt_total_outflow_d_1 * elapsed_days)

    def provenance(self) -> dict[str, object]:
        return {
            "authority": "KFK5194_1993_PRINTED_P17_P22_23_P86_89",
            "source_table_sha256": _CORPUS_HASH,
            "edition": PROFILE_ID,
            "rate_context": "COMA_LONG_TERM_INGESTION_DAILY_EDGES",
            "hourly_conversion": "DAILY_RATE_DIVIDED_BY_24",
            "mean_biomass": "PRINTED_G_OVER_GROWTH_DAYS_TIMES_12_DAYLIGHT_HOURS",
            "can_feed_eq33_ground_area_pc_without_mass_normalization": False,
            "eq33_runtime_activation": False,
            "edible_obt_outflow_policy": "ZERO_LOSS_EXPLICIT_PRINTED_P23" if self.edible_obt_loss_per_day_as_printed is not None else "NOT_APPLICABLE",
            "fortran_numeric_equivalence": "NOT_ESTABLISHED",
            "independent_scientific_validation": "NOT_ESTABLISHED",
            "symbol_conflict": self.symbol_alignment,
        }


def _checked_source(profile: Historical1993SourceProfile, table_source: Path) -> dict:
    if not isinstance(profile, Historical1993SourceProfile) or profile.profile_id != PROFILE_ID:
        raise KFK5194PhotoOBTError("explicit UFOTRI 1993 profile required")
    if dict(profile.flag_defaults).get("IPHOTO") != 1:
        raise KFK5194PhotoOBTError("1993 IPHOTO=1 provenance required")
    if not isinstance(table_source, Path) or table_source.name != _SOURCE_RELATIVE.name:
        raise KFK5194PhotoOBTError("known 1993 printed table source path required")
    if not table_source.is_file():
        raise KFK5194PhotoOBTError("1993 printed table source unavailable")
    blob = table_source.read_bytes()
    if hashlib.sha256(blob).hexdigest() != _CORPUS_HASH:
        raise KFK5194PhotoOBTError("1993 printed tables differ from pinned auditable source")
    data = yaml.safe_load(blob)
    if (not isinstance(data, dict) or data.get("target_version") != "UFOTRI_4_0_1993"
            or data.get("status") != "PRINTED_TABLES_TRANSCRIBED_WITH_SOURCE_ERRATA_PENDING"
            or data.get("scope") != "LITERATURE_TABLE_TRANSCRIPTION_NOT_SOLVER_COEFFICIENTS"
            or data.get("validation") != "NOT_EQUIVALENT_TO_ORIGINAL_EXECUTABLE"
            or set(data.get("tables", {})) != {9, 10, 11, 12}):
        raise KFK5194PhotoOBTError("invalid historical table version/provenance")
    return data


def audit_kfk5194_1993_p2_crop_source_rate(
    *,
    profile: Historical1993SourceProfile,
    crop_organ: KFK5194CropOrgan,
    pinned_table_source: Path,
) -> KFK5194P2CropSourceRate:
    """Return one source-verified formation rate and *distinct* parent outflows.

    Never mistake the parent's OBT loss for edible organ loss: p.23 forbids
    OBT loss from the potato tuber and wheat seedling edible compartments.
    """
    if not isinstance(crop_organ, KFK5194CropOrgan):
        raise KFK5194PhotoOBTError("explicit supported 1993 crop enum required")
    data = _checked_source(profile, pinned_table_source)
    table_no, symbol, source, destination, mass_key, mass, days = _EDGE[crop_organ]
    table = data["tables"][table_no]
    if (table["printed_page"] != table_no + 77 or table["units"] != "d^-1"
            or "COMA long-term ingestion" not in table["context"]):
        raise KFK5194PhotoOBTError("table chronology/context not source matched")
    rows = table["rows"]
    matching = [r for r in rows
                if (r.get("source_symbol_as_printed"), r.get("from_as_printed"), r.get("to_as_printed"))
                == (symbol, source, destination)]
    if len(matching) != 1:
        raise KFK5194PhotoOBTError("missing or ambiguous printed crop formation edge")
    rate = matching[0]["rate_per_day"]
    if type(rate) not in (int, float) or not math.isfinite(rate) or rate <= 0:
        raise KFK5194PhotoOBTError("invalid source formation rate")
    t1 = data["table_1"]["values"]
    key = ("edible_dry_mass_g" if crop_organ in (
        KFK5194CropOrgan.POTATO_TUBER, KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED
    ) else "plant_dry_mass_g")
    if t1[key][mass_key] != mass:
        raise KFK5194PhotoOBTError("Table 1 dry mass drifts from p22 source contract")
    parent = _PARENT_OBT[crop_organ]
    all_parent = [r for r in rows if r.get("from_as_printed") == parent]
    if not all_parent:
        raise KFK5194PhotoOBTError("missing source outflow network for parent OBT")
    edges: list[KFK5194OBTOutflow] = []
    for row in all_parent:
        val = row["rate_per_day"]
        if type(val) not in (int, float) or not math.isfinite(val) or val <= 0:
            raise KFK5194PhotoOBTError("invalid source outflow coefficient")
        edges.append(KFK5194OBTOutflow(
            to_as_printed=row["to_as_printed"],
            symbol_as_printed=row["source_symbol_as_printed"],
            rate_d_1=float(val),
        ))
    total = math.fsum(e.rate_d_1 for e in edges)
    if not math.isfinite(total):
        raise KFK5194PhotoOBTError("nonfinite OBT outflow")
    if crop_organ is KFK5194CropOrgan.GRASS_WHOLE and len(edges) != 4:
        raise KFK5194PhotoOBTError("grass has four distinct Table 10 OBT exits")
    if crop_organ is KFK5194CropOrgan.LEAFY_VEGETABLE_WHOLE and len(edges) != 1:
        raise KFK5194PhotoOBTError("leafy vegetable Table 9 OBT outflow drift")
    if crop_organ in (KFK5194CropOrgan.POTATO_TUBER,
                      KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED) and len(edges) != 1:
        raise KFK5194PhotoOBTError("parent OBT single outflow expected; NOT edible")
    # The visual p22 source calls wheat T_w5,w8 while the Table 12
    # transcription preserves the source's conflicting tp5,p8 symbol.
    alignment = ("PRINTED_P22_T_W5_W8_VS_TABLE12_TP5_P8_SOURCE_LIMITED"
                 if crop_organ is KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED
                 else "PRINTED_P22_EDGE_AND_TABLE_MATCH")
    return KFK5194P2CropSourceRate(
        crop_organ=crop_organ,
        table_no=table_no,
        printed_page=table["printed_page"],
        formation_symbol_as_table=symbol,
        formation_symbol_as_p22=("T_w5,w8" if crop_organ is KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED else symbol),
        formation_from_as_printed=source,
        formation_to_as_printed=destination,
        mean_hto_to_obt_d_1=float(rate),
        mean_hto_to_obt_h_1=float(rate)/24.,
        dry_mass_g_as_printed=mass,
        growth_days_as_printed=days,
        active_hours_per_growth_day=12,
        mean_dry_matter_g_per_source_crop_unit_sunlit_h=mass / (days*12.),
        parent_obt_compartment=parent,
        parent_obt_outflows=tuple(edges),
        parent_obt_total_outflow_d_1=total,
        edible_obt_loss_per_day_as_printed=0.0 if crop_organ in (
            KFK5194CropOrgan.POTATO_TUBER, KFK5194CropOrgan.WHEAT_SEEDLINGS_PRINTED
        ) else None,
        symbol_alignment=alignment,
    )
