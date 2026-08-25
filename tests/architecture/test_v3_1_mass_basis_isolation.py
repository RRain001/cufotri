from __future__ import annotations

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[2]

PROTECTED_V3_BLOBS = {
    "src/cteas_ufotri/v3_pipeline/pipeline_runner.py": "6b8b4ca602b459e2bd931bc78fa5783a695b04d7",
    "src/cteas_ufotri/plant/leaf_exchange_resistance/resistance.py": "57b87cf6575c44a35505e317fb8aa4a1141d4ab1",
    "src/cteas_ufotri/plant/tfwt_v3/tfwt_solver.py": "a428db1bbfd5af6789ebd7af142eabde58b86721",
    "src/cteas_ufotri/plant/obt_v3/obt_solver.py": "11ccb776a750f0903d0640c8660acdf183ca1111",
    "src/cteas_ufotri/plant/soil_v3/soil_solver.py": "91ed6ccab4bf0169ed73944e2ad87ccb835fe5ef",
    "src/cteas_ufotri/plant/root_v3/root_solver.py": "aa69f098d20582dc2dcf80faddfae73c6b02bdc7",
    "src/cteas_ufotri/plant/food_v3/food_transfer_solver.py": "2061ed157df0b59fff194ad41034b5ae7f3ee7c7",
    "src/cteas_ufotri/plant/food_v3/harvest_state.py": "c29ad4ca1150f897b487c404cd734b02937903cb",
}


def git_blob(path: str) -> str:
    result = subprocess.run(
        ["git", "hash-object", path],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def test_v3_1_contract_does_not_modify_frozen_solver_or_pipeline_blobs() -> None:
    actual = {path: git_blob(path) for path in PROTECTED_V3_BLOBS}
    assert actual == PROTECTED_V3_BLOBS


def test_v3_1_contract_is_not_imported_by_frozen_runtime_paths() -> None:
    for path in PROTECTED_V3_BLOBS:
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "mass_basis_v3_1" not in text
