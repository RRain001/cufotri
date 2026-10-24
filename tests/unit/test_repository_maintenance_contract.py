"""Guard scientific navigation links and non-sensitive GitHub Docker caching."""
from pathlib import Path
import re
import tomllib

ROOT = Path(__file__).resolve().parents[2]

def test_documentation_index_local_links_resolve() -> None:
    index = ROOT / "docs/INDEX.md"
    text = index.read_text(encoding="utf-8")
    links = re.findall(r"\[[^\]]+\]\(([^)]+)\)", text)
    assert len(links) >= 20
    for link in links:
        if link.startswith(("https:", "http:", "#")):
            continue
        target = link.split("#", 1)[0]
        path = (index.parent / target).resolve()
        assert path.is_relative_to(ROOT), f"index link escapes repository: {link}"
        assert path.exists(), f"broken science index link: {link}"

def test_project_description_matches_reconstruction_claim() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    description = project["project"]["description"]
    assert "UFOTRI" in description
    assert "tritium" in description
    assert "Minimal coupled HTO" not in description

def test_base_image_digest_and_safe_cache_stage_contract() -> None:
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert re.search(r"ARG PYTHON_BASE=python:3\.11-slim-bookworm@sha256:[0-9a-f]{64}", dockerfile)
    assert dockerfile.index("AS verification-deps") < dockerfile.index("FROM verification-deps AS verification")
    assert dockerfile.index("RUN uv sync --locked --extra test") < dockerfile.index("COPY . .")
    workflows = ROOT / ".github/workflows"
    owner = (workflows / "docker-portable.yml").read_text(encoding="utf-8")
    assert "target: verification-deps" in owner
    assert "cache-to: type=gha,scope=cufotri-py311-deps-v1,mode=max" in owner
    assert "runtime-packages.txt" in owner
    for name in ("v3-integration-gate.yml", "python-compatibility.yml",
                 "external-evidence.yml"):
        source = (workflows / name).read_text(encoding="utf-8")
        assert "cache-from: type=gha,scope=cufotri-py311-deps-v1" in source
        assert "cache-to: type=gha" not in source
