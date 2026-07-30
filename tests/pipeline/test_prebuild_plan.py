"""Data prebuild planning contracts."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def _loadScript(rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


def test_prebuild_base_seed_plan_is_cache_first():
    """Cached heavy categories must not reopen HF tree listing."""
    mod = _loadScript(".github/scripts/prebuild/planning/prebuildPlan.py")

    plan = mod.planBaseSeed({"finance": 2, "report": 0})

    assert plan.cachedCategories == ("finance",)
    assert plan.missingCategories == ("report",)


def test_prebuild_panel_bootstrap_records_remote_without_download():
    """First incremental run must not download every panel file."""
    mod = _loadScript(".github/scripts/prebuild/planning/prebuildPlan.py")

    plan = mod.planPanelDelta({}, {"dart/panel/005930.parquet": 11, "dart/panel/000660.parquet": 22})

    assert plan.bootstrap is True
    assert plan.processRel == ()
    assert plan.changedCodes == ()
    assert plan.newState == {"dart/panel/005930.parquet": 11, "dart/panel/000660.parquet": 22}


def test_prebuild_panel_delta_caps_without_marking_deferred_complete():
    """Capped changed files must stay in the old ledger state for next-cycle drain."""
    mod = _loadScript(".github/scripts/prebuild/planning/prebuildPlan.py")

    prior = {
        "dart/panel/000660.parquet": 1,
        "dart/panel/005930.parquet": 1,
        "dart/panel/035420.parquet": 1,
        "dart/panel/OLD.parquet": 1,
    }
    remote = {
        "dart/panel/000660.parquet": 2,
        "dart/panel/005930.parquet": 2,
        "dart/panel/035420.parquet": 2,
    }

    plan = mod.planPanelDelta(prior, remote, cap=2)

    assert plan.capped is True
    assert plan.processRel == ("dart/panel/000660.parquet", "dart/panel/005930.parquet")
    assert plan.deferredRel == ("dart/panel/035420.parquet",)
    assert plan.changedCodes == ("000660", "005930")
    assert plan.removedCodes == ("OLD",)
    assert plan.newState["dart/panel/000660.parquet"] == 2
    assert plan.newState["dart/panel/005930.parquet"] == 2
    assert plan.newState["dart/panel/035420.parquet"] == 1
    assert "dart/panel/OLD.parquet" not in plan.newState


def test_prebuild_scan_manifest_uses_fixed_artifacts():
    """Scan seeding should resolve known files directly instead of listing the tree."""
    mod = _loadScript(".github/scripts/prebuild/planning/prebuildManifest.py")

    rels = mod.scanArtifactRelPaths("dart/scan", ["dividend", "employee"])

    assert "dart/scan/finance.parquet" in rels
    assert "dart/scan/_scanBuildState.json" in rels
    assert "dart/scan/network/affiliateDocs.parquet" in rels
    assert "dart/scan/report/dividend.parquet" in rels
    assert "dart/scan/report/employee.parquet" in rels


def test_prebuild_missing_network_baseline_promotes_incremental_to_full(tmp_path: Path):
    """The first rollout must not enter incremental mode without a complete baseline."""
    import polars as pl

    from dartlab.scan.network.affiliates import (
        AFFILIATE_DOCS_SCHEMA,
        AFFILIATE_DOCS_SCHEMA_VERSION,
    )

    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")

    assert mod._requiresAffiliateDocsBootstrap(str(tmp_path), "dart/scan", incremental=True)

    artifact = tmp_path / "dart" / "scan" / mod.AFFILIATE_DOCS_RELATIVE_PATH
    artifact.parent.mkdir(parents=True)
    pl.DataFrame(
        {
            "sourceStockCode": ["000001"],
            "affiliateStockCode": ["000001"],
            "sourcePeriod": ["2024Q4"],
            "sourceRceptNo": ["20250319000001"],
            "groupName": [None],
            "datasetAsOf": ["20250319"],
            "schemaVersion": [AFFILIATE_DOCS_SCHEMA_VERSION],
        },
        schema=AFFILIATE_DOCS_SCHEMA,
    ).write_parquet(artifact)

    assert not mod._requiresAffiliateDocsBootstrap(str(tmp_path), "dart/scan", incremental=True)
    assert not mod._requiresAffiliateDocsBootstrap(str(tmp_path), "dart/scan", incremental=False)

    pl.DataFrame(
        {
            "sourceStockCode": ["000001"],
            "affiliateStockCode": ["000001"],
            "sourcePeriod": ["2024Q4"],
            "sourceRceptNo": ["20250319000001"],
            "groupName": [None],
            "datasetAsOf": ["20250319"],
            "schemaVersion": [1],
        },
        schema=AFFILIATE_DOCS_SCHEMA,
    ).write_parquet(artifact)
    assert mod._requiresAffiliateDocsBootstrap(str(tmp_path), "dart/scan", incremental=True)


def test_prebuild_validates_profile_identity_before_panel_seed(tmp_path: Path):
    """scan prebuild는 legacy profile로 full panel seed를 시작하지 않는다."""
    import polars as pl

    from dartlab.scan.builders.kr.corpProfile import (
        CORP_PROFILE_SCHEMA,
        CORP_PROFILE_SCHEMA_VERSION,
        CorpProfileIdentityError,
    )

    mod = _loadScript(".github/scripts/prebuild/prebuildData.py")
    profile = tmp_path / "dart" / "scan" / "corpProfile.parquet"
    profile.parent.mkdir(parents=True)
    row = {
        "corp_code": ["A"],
        "stockCode": ["100001"],
        "corp_name": ["알파"],
        "jurir_no": ["1234561234567"],
        "bizr_no": [""],
        "acc_mt": ["12"],
        "induty_code": [""],
        "est_dt": [""],
        "corp_cls": ["K"],
        "profileSchemaVersion": [CORP_PROFILE_SCHEMA_VERSION],
    }
    pl.DataFrame(row, schema=CORP_PROFILE_SCHEMA).write_parquet(profile)

    assert mod._validateCorpProfileIdentity(str(tmp_path)) == 1

    row["profileSchemaVersion"] = [1]
    pl.DataFrame(row, schema=CORP_PROFILE_SCHEMA).write_parquet(profile)
    with pytest.raises(CorpProfileIdentityError, match="backfill 미완료"):
        mod._validateCorpProfileIdentity(str(tmp_path))
