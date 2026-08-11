"""artifactSync — 비파괴 Skill OS 산출물 동기화 가드.

핵심 계약:
- 기본 check 는 쓰지 않고 드리프트만 보고 (exit≠0).
- ``--write`` 후 재 check 는 드리프트 0 (멱등·결정적 파생).
- 어떤 자동 도구도 artifactSync 를 호출하지 않는다 (자동 sync 금지, 수동 --write 만).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from dartlab.skills import artifactSync

pytestmark = pytest.mark.unit

_ARTIFACT_NAMES = ("catalog.json", "agent.json", "mcp.json", "web.json", "pyodide.json", "graph.json")


def test_derive_produces_six_artifacts() -> None:
    """deriveArtifacts 는 6 종 payload 를 결정적으로 만든다 (전부 .md 파생)."""
    art = artifactSync.deriveArtifacts()
    assert set(art) == set(_ARTIFACT_NAMES)
    assert art["catalog.json"]["skills"], "catalog 가 비어있음"
    # catalog 와 agent 는 동일 직렬화 (소비자만 다름).
    assert art["catalog.json"]["skills"] == art["agent.json"]["skills"]


def test_write_then_check_is_clean(tmp_path: Path) -> None:
    """--write 후 같은 디렉터리의 기본 check 는 드리프트 0 (멱등)."""
    assert artifactSync.syncArtifacts(write=True, webDir=tmp_path) == 0
    for name in _ARTIFACT_NAMES:
        assert (tmp_path / name).exists(), f"{name} 미생성"
    assert artifactSync.syncArtifacts(write=False, webDir=tmp_path) == 0


def test_check_detects_drift(tmp_path: Path) -> None:
    """기본 check 는 .md 와 어긋난 on-disk json 을 드리프트로 잡는다 (exit 1)."""
    artifactSync.syncArtifacts(write=True, webDir=tmp_path)
    catalog = tmp_path / "catalog.json"
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    payload["skills"] = payload["skills"][:-1]  # 1 개 스킬 의도적 제거 → 드리프트 유발
    catalog.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert artifactSync.syncArtifacts(write=False, webDir=tmp_path) == 1


def test_check_reports_missing_file(tmp_path: Path) -> None:
    """산출물 파일 자체가 없으면 드리프트 (생성 필요)."""
    assert artifactSync.syncArtifacts(write=False, webDir=tmp_path) == 1


def test_no_auto_callers() -> None:
    """addEngine·addAxis·addRecipe·recipePromote·run.py 가 artifactSync 를 자동 호출하지 않는다.

    회귀 가드 — 옛 generateSkills 가 이들에서 자동 실행돼 운영자 수기작업을 덮어쓴 사고
    (b6090528b 폐기). artifactSync 는 운영자 수동 전용이어야 한다.
    """
    root = Path(__file__).resolve().parents[2]
    suspects = [
        root / "src" / "dartlab" / "skills" / "addEngine.py",
        root / "src" / "dartlab" / "skills" / "addAxis.py",
        root / "src" / "dartlab" / "skills" / "recipePromote.py",
        root / "tests" / "run.py",
    ]
    optional = [root / "src" / "dartlab" / "skills" / "addRecipe.py"]
    for path in suspects:
        text = path.read_text(encoding="utf-8")
        assert "artifactSync" not in text, f"{path.name} 가 artifactSync 를 참조 — 자동 호출 금지 위반"
    for path in optional:
        if path.exists():
            assert "artifactSync" not in path.read_text(encoding="utf-8"), f"{path.name} artifactSync 참조 금지"
