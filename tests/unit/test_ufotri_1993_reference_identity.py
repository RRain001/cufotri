"""Non-physics checks for the explicitly 1993 UFOTRI 4.0 source delta registry.

This confirms source identity and document traceability. It does NOT assert
original-executable equivalence or completion of the entire 1993 physics audit.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
UPGRADE = ROOT / "docs/v4/1993_upgrade"
TARGET = "https://publikationen.bibliothek.kit.edu/270034158/3813483"
BASELINE = "https://publikationen.bibliothek.kit.edu/270029395/3813413"


@pytest.fixture(scope="module")
def registry() -> dict:
    result = yaml.safe_load((UPGRADE / "physics_delta_matrix.yaml").read_text(encoding="utf-8"))
    assert isinstance(result, dict)
    return result


def test_1993_ufotri_four_is_authoritative_target_not_1990(registry: dict) -> None:
    assert registry["document_kind"] == "UFOTRI_1993_V4_PHYSICS_DELTA_MATRIX"
    assert registry["target_version"] == "UFOTRI_4_0_1993"
    assert registry["target_year"] == 1993
    assert registry["target_source"]["report"] == "KfK 5194"
    assert registry["target_source"]["pdf_url"] == TARGET
    assert registry["target_source"]["doi"] == "10.5445/IR/270034158"
    assert registry["baseline_version"] == "KFK4605_1990"
    assert registry["baseline_source"]["report"] == "KfK 4605"
    assert registry["baseline_source"]["pdf_url"] == BASELINE
    assert registry["audit_status"] == "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS"
    assert registry["numerical_equivalence_to_1993_executable"] == "NOT_ESTABLISHED"
    assert registry["external_empirical_validation"] == "NOT_ESTABLISHED"


def test_registry_rows_are_1993_source_anchored_and_refer_to_existing_code(registry: dict) -> None:
    rows = registry["rows"]
    assert len(rows) >= 24
    seen: set[str] = set()
    for row in rows:
        assert row["id"].startswith("UF93-")
        assert row["id"] not in seen
        seen.add(row["id"])
        assert row["reference_1993_section"]
        assert row["reference_1993_printed_pages"]
        assert row["reference_1993_pdf_page_indices"]
        assert row["kfk5194_target_fact"]
        assert row["reference_1990_section"]
        assert row["kfk4605_comparison"]
        assert row["implementation_phase"].startswith("P")
        assert row["repo_paths"]
        for path in row["repo_paths"]:
            assert (ROOT / path).exists(), (row["id"], path)
        assert "EQUIVALENCE_ESTABLISHED" not in row["repository_assessment"]


def test_human_index_and_status_distinguish_target_version_from_baseline() -> None:
    page = (UPGRADE / "PHYSICS_DELTA_MATRIX.md").read_text(encoding="utf-8")
    assert "UFOTRI **4.0（1993）**" in page
    assert "KfK 5194" in page
    assert "KfK 4605" in page
    assert TARGET in page and BASELINE in page
    assert "PARTIAL_SOURCE_ANCHORED_AUDIT_IN_PROGRESS" in page
    assert "NOT_ESTABLISHED" in page
    assert "1990 Eq.(33) 与 1993 Eq.(33) 不是同一个公式" in page
    assert "不是当前运行时已提供的选项" in page
    assert page.count("| `UF93-") == 24
