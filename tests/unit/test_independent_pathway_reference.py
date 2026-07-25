from __future__ import annotations

import ast
import math
from pathlib import Path

from scripts.run_v2_validation_case import run_case
from validation.reference_models.independent_pathway_reference.run_reference import (
    competing_depletion,
    gaussian_ground_centerline,
    simple_dose_increment,
)


ROOT = Path(__file__).resolve().parents[2]


def test_independent_reference_has_no_formal_model_imports():
    source_path = (
        ROOT
        / "validation/reference_models/independent_pathway_reference"
        / "run_reference.py"
    )
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(name.startswith("cteas_ufotri") for name in imported)


def test_independent_gaussian_and_competing_depletion_scalars():
    remaining, dry, wet = competing_depletion(100.0, 10.0, 0.01, 0.02)
    assert math.isclose(remaining, 100.0 * math.exp(-0.3), rel_tol=1.0e-12)
    assert math.isclose(dry / wet, 0.5, rel_tol=1.0e-12)
    concentration = gaussian_ground_centerline(1.0e9, 1000.0, 3.0, 10.0, "D")
    assert concentration > 0.0


def test_independent_simple_dose_includes_nonzero_ingestion():
    result = simple_dose_increment(
        3600.0,
        100.0,
        20.0,
        1.8e-11,
        0.5,
        food_hto_bq_kg=1000.0,
        food_obt_bq_kg=500.0,
        food_intake_kg_day=0.2,
        obt_coefficient_sv_bq=4.2e-11,
    )
    assert result["ingestion_dose_sv"] > 0.0
    assert result["total_effective_dose_sv"] > result["inhalation_dose_sv"]


def test_independent_reference_case_executes(tmp_path):
    case = ROOT / "validation/cases/independent_reference_case_001.yaml"
    output = tmp_path / "reference_case"
    assert run_case(case, output) == "PASS"
