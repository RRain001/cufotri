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
