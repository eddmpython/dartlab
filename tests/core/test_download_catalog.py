"""다운로드 센터 노출 카탈로그 drift·보안 가드 (mainPlan/data-download-center Phase 0).

Python `downloadCatalog()`(SSOT) 와 TS 미러(`downloadCatalog.ts`)의 dir↔shardKind 동기화 +
보안(public:False 부재)을 강제한다. 새 public 카테고리 추가 시 TS 미러 누락이면 fail,
private dir 이 노출되면 fail.
"""

from __future__ import annotations

import re
from pathlib import Path

from dartlab.core.dataConfig import DATA_RELEASES, downloadCatalog

_REPO_ROOT = Path(__file__).resolve().parents[2]
_TS_MIRROR = _REPO_ROOT / "ui" / "packages" / "runtime" / "src" / "data" / "catalog" / "downloadCatalog.ts"
_WORKER_MIRROR = _REPO_ROOT / "infra" / "workers" / "dataCsv" / "allowlist.js"

# 코드 게이트가 막아야 하는 private dir (공개 repo 와 same-repo 라 토큰 차단 안 먹음 — 03-tier2-live-worker).
_MUST_BLOCK = {
    "dart/allFilings",
    "edgar/scan",
    "dart/stemIndex",
    "edinet/finance",
    "edinet/docs",
    "ai/knowledge",
    "original/dart/docs",
    "news/private/naver",
    "news/private/naver_enriched",
}


def _tsMirrorEntries() -> dict[str, str]:
    """TS 미러 파일에서 {dir: shardKind} 추출."""
    text = _TS_MIRROR.read_text(encoding="utf-8")
    pairs = re.findall(r"\{\s*dir:\s*'([^']+)',[^}]*shardKind:\s*'([^']+)'", text)
    return {d: kind for d, kind in pairs}


def _workerMirrorEntries() -> dict[str, str]:
    """라이브 API 워커 allowlist.js 에서 {dir: shardKind} 추출 (TS 미러와 동일 리터럴 형태)."""
    text = _WORKER_MIRROR.read_text(encoding="utf-8")
    pairs = re.findall(r"\{\s*dir:\s*'([^']+)',[^}]*shardKind:\s*'([^']+)'", text)
    return {d: kind for d, kind in pairs}


def test_no_private_dir_exposed() -> None:
    """노출 카탈로그에 public:False dir 이 절대 없다 (보안 SSOT)."""
    exposed = {entry["dir"] for entry in downloadCatalog()}
    leaked = exposed & _MUST_BLOCK
    assert not leaked, f"private dir 노출됨: {sorted(leaked)}"
    for entry in downloadCatalog():
        specs = [spec for spec in DATA_RELEASES.values() if spec["dir"] == entry["dir"]]
        assert specs and specs[0].get("public") is True, f"비공개/미등록 dir 노출: {entry['dir']}"
        assert not specs[0].get("nested"), f"nested dir 노출: {entry['dir']}"


def test_public_flat_tabular_auto_exposed() -> None:
    """public·flat·표형 dir 은 자동 노출된다 (새 카테고리 자동 확장 — 비표형 명시 제외만 빠짐)."""
    from dartlab.core.dataConfig import _DOWNLOAD_EXCLUDE_DIRS

    exposed = {entry["dir"] for entry in downloadCatalog()}
    for spec in DATA_RELEASES.values():
        if spec.get("public") and not spec.get("nested") and spec["dir"] not in _DOWNLOAD_EXCLUDE_DIRS:
            assert spec["dir"] in exposed, f"public flat 표형 dir 누락: {spec['dir']}"


def test_ts_mirror_in_sync() -> None:
    """TS 미러의 dir↔shardKind 가 Python SSOT 와 정확히 일치한다 (drift 0)."""
    pyCatalog = {entry["dir"]: entry["shardKind"] for entry in downloadCatalog()}
    tsCatalog = _tsMirrorEntries()
    assert tsCatalog, f"TS 미러 파싱 실패: {_TS_MIRROR}"
    missingInTs = set(pyCatalog) - set(tsCatalog)
    extraInTs = set(tsCatalog) - set(pyCatalog)
    assert not missingInTs, f"TS 미러 누락(Python 에만 있음): {sorted(missingInTs)}"
    assert not extraInTs, f"TS 미러 잉여(Python 에 없음): {sorted(extraInTs)}"
    for d, kind in pyCatalog.items():
        assert tsCatalog[d] == kind, f"shardKind drift {d}: py={kind} ts={tsCatalog[d]}"


def test_worker_allowlist_in_sync() -> None:
    """라이브 API 워커(infra/workers/dataCsv/allowlist.js)의 dir↔shardKind 가 Python SSOT 와 정확히
    일치한다 (drift 0). 워커 allowlist 는 same-repo private 6종 차단의 유일 방어라 SSOT 동기화가 보안 게이트."""
    pyCatalog = {entry["dir"]: entry["shardKind"] for entry in downloadCatalog()}
    workerCatalog = _workerMirrorEntries()
    assert workerCatalog, f"워커 allowlist 파싱 실패: {_WORKER_MIRROR}"
    missing = set(pyCatalog) - set(workerCatalog)
    extra = set(workerCatalog) - set(pyCatalog)
    assert not missing, f"워커 allowlist 누락(Python 에만 있음): {sorted(missing)}"
    assert not extra, f"워커 allowlist 잉여(Python 에 없음 — 보안 누설 위험): {sorted(extra)}"
    leaked = set(workerCatalog) & _MUST_BLOCK
    assert not leaked, f"워커 allowlist 에 private dir 노출됨: {sorted(leaked)}"
    for d, kind in pyCatalog.items():
        assert workerCatalog[d] == kind, f"워커 shardKind drift {d}: py={kind} worker={workerCatalog[d]}"
