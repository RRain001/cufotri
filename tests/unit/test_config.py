import pytest
import yaml

from cteas_ufotri.config import load_configuration, load_yaml


def test_non_hto_source_is_rejected(tmp_path):
    case = load_yaml("configs/test_case.yaml")
    case["source"]["pollutant"] = "HT"
    path = tmp_path / "ht_case.yaml"
    path.write_text(yaml.safe_dump(case), encoding="utf-8")
    with pytest.raises(ValueError, match="HTO only"):
        load_configuration(
            "configs/default_parameters.yaml",
            path,
        )


def test_feedback_area_mismatch_is_rejected(tmp_path):
    case = load_yaml("configs/test_case.yaml")
    case["coupling"] = {"feedback_area_m2": 2.0}
    path = tmp_path / "bad_area.yaml"
    path.write_text(yaml.safe_dump(case), encoding="utf-8")
    with pytest.raises(ValueError, match="Feedback area"):
        load_configuration("configs/default_parameters.yaml", path)


@pytest.mark.parametrize("pathway", ("dry", "wet"))
def test_deposition_footprint_area_must_be_explicit_and_positive(
    tmp_path,
    pathway,
):
    parameters = load_yaml("configs/default_parameters.yaml")
    parameters["deposition"][f"{pathway}_footprint"]["area_m2"] = 0.0
    parameters_path = tmp_path / "parameters.yaml"
    parameters_path.write_text(yaml.safe_dump(parameters), encoding="utf-8")
    with pytest.raises(ValueError, match="footprint area"):
        load_configuration(parameters_path, "configs/test_case.yaml")


def test_invalid_beef_production_mode_is_rejected(tmp_path):
    parameters = load_yaml("configs/default_parameters.yaml")
    parameters["foodchain"]["animal_products"]["beef"]["mode"] = "body_surrogate"
    parameters_path = tmp_path / "parameters.yaml"
    parameters_path.write_text(yaml.safe_dump(parameters), encoding="utf-8")
    with pytest.raises(ValueError, match="beef-production mode"):
        load_configuration(parameters_path, "configs/test_case.yaml")


def test_named_wet_parameter_set_is_materialized():
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/test_case.yaml",
    )
    depletion = config["atmosphere"]["depletion"]
    assert (
        depletion["wet_scavenging_parameter_set"]
        == "iaea_emras_japanet_comparison"
    )
    assert depletion["power_law_a_s"] == 5.0e-5
    assert depletion["power_law_b"] == 0.8
    assert (
        depletion["wet_scavenging_parameter_status"]
        == "LITERATURE_COMPARISON_NOT_UFOTRI"
    )
