"""P2 R3 KfK5194 1993 p22 formation edge and Tables 9-12 source guards."""
from dataclasses import replace
import math
from pathlib import Path

import pytest

from cteas_ufotri.versioned_inputs_1993 import (
    PROFILE_ID, load_1993_source_profile,
)
from cteas_ufotri.plant.kfk5194_1993_photo_obt_rates import (
    KFK5194CropOrgan as Crop, KFK5194PhotoOBTError,
    KFK5194OBTFormationMode as Mode, KFK5194SolarPeriod as Period,
    kfk5194_1993_obt_formation_rate,
)
from cteas_ufotri.plant.kfk5194_1993_p2_crop_rate_source import (
    audit_kfk5194_1993_p2_crop_source_rate,
)

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / "docs/v4/1993_upgrade/primary_source_transfer_tables_r3.yaml"


def _profile():
    return load_1993_source_profile(
        ROOT / "configs/ufotri_1993_manual_source_profile.yaml",
        selected_profile=PROFILE_ID,
    )


def _source(crop: Crop = Crop.GRASS_WHOLE, **kwargs):
    return audit_kfk5194_1993_p2_crop_source_rate(
        profile=_profile(), crop_organ=crop,
        pinned_table_source=CORPUS, **kwargs,
    )


@pytest.mark.parametrize("crop,table,source,destination,rate,mean_mass,days", [
    (Crop.GRASS_WHOLE, 10, "grass HTO", "grass OBT", .0081, 170., 30),
    (Crop.LEAFY_VEGETABLE_WHOLE, 9, "plant HTO", "plant OBT", .0025, 160., 45),
    (Crop.POTATO_TUBER, 11, "potato hto", "tuber OBT", .0026, 660., 90),
    (Crop.WHEAT_SEEDLINGS_PRINTED, 12, "wheat HTO", "seedling OBT", .0041, 519., 60),
])
def test_r3_p22_table_selected_formation_edge_and_12_hour_growth_oracles(
    crop, table, source, destination, rate, mean_mass, days
):
    r = _source(crop)
    assert r.table_no == table
    assert r.printed_page == table + 77
    assert r.formation_from_as_printed == source
    assert r.formation_to_as_printed == destination
    assert r.mean_hto_to_obt_d_1 == pytest.approx(rate)
    assert r.mean_hto_to_obt_h_1 == pytest.approx(rate/24.)
    assert r.dry_mass_g_as_printed == mean_mass
    assert r.growth_days_as_printed == days
    assert r.active_hours_per_growth_day == 12
    assert r.mean_dry_matter_g_per_source_crop_unit_sunlit_h == pytest.approx(
        mean_mass / (days*12)
    )
    p = r.provenance()
    assert p["eq33_runtime_activation"] is False
    assert p["can_feed_eq33_ground_area_pc_without_mass_normalization"] is False
    assert p["fortran_numeric_equivalence"] == "NOT_ESTABLISHED"
    assert p["rate_context"] == "COMA_LONG_TERM_INGESTION_DAILY_EDGES"


def test_r3_p22_four_rates_explicitly_feed_r1_simple_model_without_promotion():
    # Checks source input to an explicit opt-in test call, NOT runtime activation.
    for crop in Crop:
        src = _source(crop)
        result = kfk5194_1993_obt_formation_rate(
            profile=_profile(), crop_organ=crop,
            mode=Mode.SIMPLE_EQ32, solar_period=Period.DAY,
            mean_uniform_transfer_d_1=src.mean_hto_to_obt_d_1,
            external_fig11_phenology_factor=1.0,
        )
        assert result.actual_transfer_h_1 == pytest.approx(
            src.mean_hto_to_obt_d_1/24. * 1.75,
        )
        assert result.provenance()["production_runtime_activated"] is False
        night = kfk5194_1993_obt_formation_rate(
            profile=_profile(), crop_organ=crop,
            mode=Mode.SIMPLE_EQ32, solar_period=Period.NIGHT,
            mean_uniform_transfer_d_1=src.mean_hto_to_obt_d_1,
            external_fig11_phenology_factor=1.0,
        )
        assert night.actual_transfer_h_1 == pytest.approx(
            src.mean_hto_to_obt_d_1/24. * .25,
        )


def test_r3_grass_four_outgoing_paths_independent_budget_half_life():
    r = _source(Crop.GRASS_WHOLE)
    assert r.parent_obt_compartment == "grass OBT"
    exits = {x.to_as_printed: x.rate_d_1 for x in r.parent_obt_outflows}
    assert exits == {
        "grass HTO": .024, "cow HTO": .018,
        "cow OBT": .0029, "milk OBT": .0015,
    }
    assert r.parent_obt_total_outflow_d_1 == pytest.approx(.0464)
    assert r.parent_obt_isolated_survival_half_time_days == pytest.approx(
        math.log(2)/.0464
    )
    assert r.isolated_parent_obt_retention_fraction(0.) == 1.0
    assert r.isolated_parent_obt_retention_fraction(math.log(2)/.0464) == pytest.approx(.5)
    # Branch probabilities only for *isolated one-compartment loss*, no
    # food-chain dose or complete cow/milk solver is implied.
    assert math.fsum(x.rate_d_1/r.parent_obt_total_outflow_d_1
                     for x in r.parent_obt_outflows) == pytest.approx(1.)


@pytest.mark.parametrize("crop,loss", [
    (Crop.LEAFY_VEGETABLE_WHOLE, .032),
    (Crop.POTATO_TUBER, .069),
    (Crop.WHEAT_SEEDLINGS_PRINTED, .069),
])
def test_r3_parent_obt_loss_not_edible_obt_loss(crop, loss):
    r = _source(crop)
    assert len(r.parent_obt_outflows) == 1
    assert r.parent_obt_total_outflow_d_1 == pytest.approx(loss)
    assert r.parent_obt_isolated_survival_half_time_days == pytest.approx(
        math.log(2)/loss
    )
    if crop in (Crop.POTATO_TUBER, Crop.WHEAT_SEEDLINGS_PRINTED):
        assert r.edible_obt_loss_per_day_as_printed == 0.
        assert r.formation_to_as_printed not in (
            e.to_as_printed for e in r.parent_obt_outflows
        )
        assert r.parent_obt_compartment != r.formation_to_as_printed
        assert r.provenance()["edible_obt_outflow_policy"] == (
            "ZERO_LOSS_EXPLICIT_PRINTED_P23"
        )
    else:
        assert r.edible_obt_loss_per_day_as_printed is None


def test_r3_wheat_table12_symbol_does_not_silently_replace_printed_p22_symbol():
    r = _source(Crop.WHEAT_SEEDLINGS_PRINTED)
    assert r.formation_symbol_as_table == "tp5,p8"
    assert r.formation_symbol_as_p22 == "T_w5,w8"
    assert "SOURCE_LIMITED" in r.provenance()["symbol_conflict"]


def test_r3_wheat_and_potato_table1_dry_organ_mass_conflict_preserved():
    # Source Table 1 prints edible dry mass greater than whole-plant dry
    # mass for both plants. R3 deliberately does not "repair" this.
    import yaml
    x = yaml.safe_load(CORPUS.read_text(encoding="utf-8"))["table_1"]["values"]
    for key in ("potatoes", "winter_wheat"):
        assert x["edible_dry_mass_g"][key] > x["plant_dry_mass_g"][key]
    assert _source(Crop.POTATO_TUBER).dry_mass_g_as_printed == 660.
    assert _source(Crop.WHEAT_SEEDLINGS_PRINTED).dry_mass_g_as_printed == 519.


@pytest.mark.parametrize("crop", list(Crop))
def test_r3_nonnegative_first_order_parent_outflow_diagnostics(crop):
    r = _source(crop)
    values = [r.isolated_parent_obt_retention_fraction(t)
              for t in (0., 1., 7., 30., 365.)]
    assert all(0 <= v <= 1 for v in values)
    assert values == sorted(values, reverse=True)
    for t1, t2 in ((.2, 2.), (5., 10.)):
        assert r.isolated_parent_obt_retention_fraction(t1+t2) == pytest.approx(
            r.isolated_parent_obt_retention_fraction(t1)
            * r.isolated_parent_obt_retention_fraction(t2)
        )


@pytest.mark.parametrize("bad", [-1., float("nan"), float("inf"), True, "1"])
def test_r3_invalid_elapsed_time_is_rejected(bad):
    with pytest.raises(KFK5194PhotoOBTError):
        _source().isolated_parent_obt_retention_fraction(bad)


def test_r3_unknown_crop_and_source_profile_are_rejected():
    for bad in (None, "grass_whole", "GRASS_WHOLE", 2):
        with pytest.raises(KFK5194PhotoOBTError):
            audit_kfk5194_1993_p2_crop_source_rate(
                profile=_profile(), crop_organ=bad, pinned_table_source=CORPUS,
            )
    with pytest.raises(KFK5194PhotoOBTError):
        audit_kfk5194_1993_p2_crop_source_rate(
            profile=replace(_profile(), profile_id="KFK4605_1990"),
            crop_organ=Crop.GRASS_WHOLE, pinned_table_source=CORPUS,
        )


def test_r3_pinned_source_fails_closed_on_mutation(tmp_path):
    corpus = tmp_path / CORPUS.name
    blob = CORPUS.read_bytes()
    corpus.write_bytes(blob.replace(b"rate_per_day: 0.0081", b"rate_per_day: 0.0082"))
    with pytest.raises(KFK5194PhotoOBTError, match="pinned"):
        audit_kfk5194_1993_p2_crop_source_rate(
            profile=_profile(), crop_organ=Crop.GRASS_WHOLE,
            pinned_table_source=corpus,
        )
    with pytest.raises(KFK5194PhotoOBTError):
        audit_kfk5194_1993_p2_crop_source_rate(
            profile=_profile(), crop_organ=Crop.GRASS_WHOLE,
            pinned_table_source=tmp_path/"fake.csv",
        )


def test_r3_legacy_and_production_entrypoints_unchanged():
    for relpath in (
        "src/cteas_ufotri/config.py",
        "src/cteas_ufotri/cli.py",
        "src/cteas_ufotri/plant/obt_ufotri_v4/model.py",
        "src/cteas_ufotri/plant/obt_v3/obt_solver.py",
        "src/cteas_ufotri/v4_integration/soil_root_tfwt_obt.py",
    ):
        content = (ROOT / relpath).read_text(encoding="utf-8")
        assert "kfk5194_1993_p2_crop_rate_source" not in content
