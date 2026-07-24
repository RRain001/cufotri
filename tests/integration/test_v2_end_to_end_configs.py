from pathlib import Path

from cteas_ufotri.config import load_configuration


ROOT = Path(__file__).resolve().parents[2]


def test_all_v2_end_to_end_configs_inherit_frozen_stack_and_validate():
    names = {
        "v2_era5_72h_wet_deposition",
        "v2_accident_plant_obt_14d",
        "v2_crop_ingestion_season",
        "v2_pasture_milk_pathway",
        "v2_full_adult_dose",
    }
    loaded = []
    for path in sorted((ROOT / "configs/v2").glob("*.yaml")):
        config = load_configuration(
            ROOT / "configs/default_parameters.yaml", path
        )
        loaded.append(config)
        assert config["site"]["longitude_deg"] == 117.141610855
        assert config["site"]["latitude_deg"] == 31.939774444
        assert config["source"]["stack_height_m"] == 70.0
        assert config["source"]["pollutant"] == "HTO"
    assert {config["name"] for config in loaded} == names
