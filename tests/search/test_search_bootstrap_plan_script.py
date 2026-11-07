"""Search bootstrap planning script tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

SCRIPT = Path(".github/scripts/search/planSearchBootstrap.py")


def test_plan_search_bootstrap_for_missing_sources(tmp_path: Path) -> None:
    evidence = tmp_path / "remote.json"
    out = tmp_path / "nested" / "plan.json"
    evidence.write_text(
        json.dumps(
            {
                "sourceCatalog": {"missingSources": ["allFilings", "dartPanel", "edgarPanel", "newsPublic"]},
                "contentIndex": {"manifests": {"full": {"exists": False}, "lite": {"exists": False}}},
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-evidence",
            str(evidence),
            "--out",
            str(out),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    plan = json.loads(out.read_text(encoding="utf-8"))
    commands = "\n".join(action["command"] for action in plan["actions"])
    assert plan["missingSources"] == ["allFilings", "dartPanel", "edgarPanel", "newsPublic"]
    assert plan["missingContentTiers"] == ["full", "lite"]
    assert "gh workflow run originalSync.yml -f jobs=allfilings" in commands
    assert "gh workflow run originalSync.yml -f jobs=dart-zip" in commands
    assert "gh workflow run originalSync.yml -f jobs=edgar" in commands
    assert "gh workflow run newsArchiveSync.yml" in commands
    assert "search_catalog_bootstrap=true" in commands
    assert "gh workflow run searchIndexBuild.yml -f build_mode=catalog" in commands
    assert "checkSearchRemoteEvidence.py" in commands
    assert "buildSearchProofBundle.py" in commands


def test_plan_search_bootstrap_skips_source_bootstrap_when_catalogs_exist(tmp_path: Path) -> None:
    evidence = tmp_path / "remote.json"
    evidence.write_text(
        json.dumps(
            {
                "sourceCatalog": {"missingSources": []},
                "contentIndex": {"manifests": {"full": {"exists": False}, "lite": {"exists": False}}},
            }
        ),
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-evidence",
            str(evidence),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    plan = json.loads(proc.stdout)
    commands = "\n".join(action["command"] for action in plan["actions"])
    assert plan["missingSources"] == []
    assert plan["missingContentTiers"] == ["full", "lite"]
    assert "search_catalog_bootstrap=true" not in commands
    assert "gh workflow run searchIndexBuild.yml -f build_mode=catalog" in commands


def test_plan_search_bootstrap_maps_status_blockers_to_actions(tmp_path: Path) -> None:
    evidence = tmp_path / "remote.json"
    status = tmp_path / "status.json"
    evidence.write_text(
        json.dumps(
            {
                "sourceCatalog": {"missingSources": []},
                "contentIndex": {"manifests": {"full": {"exists": True}, "lite": {"exists": True}}},
            }
        ),
        encoding="utf-8",
    )
    status.write_text(
        json.dumps(
            {
                "opsReady": False,
                "blockers": [
                    "sourceCatalogNotFull:dartPanel",
                    "sourceCatalogMissingProducerRun:edgarPanel",
                    "remoteContentManifestSetMissingProducerRun:full:newsPublic",
                    "remoteContentMissingFileSources:lite",
                ],
            }
        ),
        encoding="utf-8",
    )

    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "utf8",
            str(SCRIPT),
            "--remote-evidence",
            str(evidence),
            "--productization-status",
            str(status),
        ],
        cwd=Path.cwd(),
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=120,
    )

    assert proc.returncode == 0, proc.stderr
    plan = json.loads(proc.stdout)
    actionIds = [action["id"] for action in plan["actions"]]
    assert plan["missingSources"] == ["dartPanel", "edgarPanel", "newsPublic"]
    assert plan["missingContentTiers"] == ["full", "lite"]
    assert "bootstrapSource:dartPanel" in actionIds
    assert "bootstrapSource:edgarPanel" in actionIds
    assert "bootstrapSource:newsPublic" in actionIds
    assert "buildContentIndex:mainCatalog" in actionIds
