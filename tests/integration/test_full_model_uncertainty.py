from cteas_ufotri.analysis.full_model_uncertainty import (
    run_full_model_lhs_convergence,
)
from cteas_ufotri.config import load_configuration


def test_full_model_uncertainty_is_mode_aware_and_recomputes():
    config = load_configuration(
        "configs/default_parameters.yaml",
        "configs/v2/v2_full_adult_dose.yaml",
    )
    result = run_full_model_lhs_convergence(
        config,
        config["uncertainty"]["parameters"],
        sample_sizes=(8, 16, 32),
        primary_seed=100,
        additional_seeds=(101, 102, 103),
        audit_duration_hours=2.0,
    )
    assert result["status"] == "PASS"
    assert result["model_run_count"] == 160
    assert result["parameter_write_status"] == "PASS"
    assert result["same_seed_reproducible"]
    assert "wet_scavenging_a" in result["inactive_parameters"]
    assert "leaf_stomatal_resistance_day" in result["inactive_parameters"]
    assert "pasture_max_lai" in result["active_parameters"]
    assert "feed_intake" in result["active_parameters"]
