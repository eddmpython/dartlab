"""pipeline reconcile (reconcileCategory + panel/edgarPanel stages) 단위 — 네트워크 0(stub)."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.unit


def test_reconcile_category_set_difference(monkeypatch, tmp_path) -> None:
    """파일집합 차분 — HF에만 있으면 pull, 로컬에만 있으면 push (panel)."""
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline import reconcile
    from dartlab.pipeline import seed as seedmod

    # 로컬 dart/panel/{A,B}.parquet
    pdir = tmp_path / "dart" / "panel"
    pdir.mkdir(parents=True)
    (pdir / "A.parquet").write_bytes(b"x")
    (pdir / "B.parquet").write_bytes(b"x")

    # HF 에는 {B,C}
    monkeypatch.setattr(
        seedmod, "listRemoteFiles", lambda category, token=None: {"dart/panel/B.parquet": 1, "dart/panel/C.parquet": 1}
    )

    pulled_arg = {}
    pushed_arg = {}

    def stubDownload(category, relPaths, *, dataDir=None, token=None):
        pulled_arg["rels"] = list(relPaths)
        return len(relPaths), 0

    def stubUpload(category, *, changedFiles=None, dataDir=None, token=None):
        pushed_arg["names"] = list(changedFiles or [])
        return len(changedFiles or [])

    monkeypatch.setattr(seedmod, "downloadCategoryFiles", stubDownload)
    monkeypatch.setattr(upmod, "uploadCategoryToHf", stubUpload)

    out = reconcile.reconcileCategory("panel", dataDir=str(tmp_path))
    assert out["pull"] == 1 and out["pulled"] == 1
    assert out["push"] == 1 and out["pushed"] == 1
    assert out["inSync"] is False
    assert pulled_arg["rels"] == ["dart/panel/C.parquet"]  # HF에만 → 로컬로
    assert pushed_arg["names"] == ["A.parquet"]  # 로컬에만 → HF로 (category dir 기준 파일명)


def test_reconcile_category_in_sync(monkeypatch, tmp_path) -> None:
    """로컬·HF 동일하면 처리 0 + inSync — 외부 호출 없음."""
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline import reconcile
    from dartlab.pipeline import seed as seedmod

    pdir = tmp_path / "dart" / "panel"
    pdir.mkdir(parents=True)
    (pdir / "A.parquet").write_bytes(b"x")

    monkeypatch.setattr(seedmod, "listRemoteFiles", lambda category, token=None: {"dart/panel/A.parquet": 1})

    def boomDl(*a, **k):
        raise AssertionError("download 호출됨 — in-sync인데 pull")

    def boomUp(*a, **k):
        raise AssertionError("upload 호출됨 — in-sync인데 push")

    monkeypatch.setattr(seedmod, "downloadCategoryFiles", boomDl)
    monkeypatch.setattr(upmod, "uploadCategoryToHf", boomUp)

    out = reconcile.reconcileCategory("panel", dataDir=str(tmp_path))
    assert out["pull"] == 0 and out["push"] == 0 and out["inSync"] is True


def test_reconcile_category_push_disabled(monkeypatch, tmp_path) -> None:
    """push=False → 로컬전용 파일 push 안 함(pull만)."""
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline import reconcile
    from dartlab.pipeline import seed as seedmod

    pdir = tmp_path / "dart" / "panel"
    pdir.mkdir(parents=True)
    (pdir / "A.parquet").write_bytes(b"x")  # 로컬에만

    monkeypatch.setattr(seedmod, "listRemoteFiles", lambda category, token=None: {"dart/panel/C.parquet": 1})
    monkeypatch.setattr(seedmod, "downloadCategoryFiles", lambda *a, **k: (1, 0))

    called = {"up": False}

    def stubUp(*a, **k):
        called["up"] = True
        return 0

    monkeypatch.setattr(upmod, "uploadCategoryToHf", stubUp)

    out = reconcile.reconcileCategory("panel", push=False, dataDir=str(tmp_path))
    assert out["push"] == 0
    assert called["up"] is False
    assert out["pull"] == 1


def test_reconcile_category_unknown_rejected() -> None:
    """미등록 category → ValueError."""
    from dartlab.pipeline import reconcile

    with pytest.raises(ValueError, match="unknown category"):
        reconcile.reconcileCategory("__nope__")


def test_reconcile_category_nested_rejected(monkeypatch) -> None:
    """nested 카테고리 → ValueError (flat 전용 가드)."""
    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.pipeline import reconcile

    monkeypatch.setitem(DATA_RELEASES["panel"], "nested", True)
    with pytest.raises(ValueError, match="nested"):
        reconcile.reconcileCategory("panel")


def test_run_panel_reconcile_maps_summary(monkeypatch) -> None:
    """runPanelReconcile — reconcileCategory summary → StageResult(rows=pulled, uploaded=pushed)."""
    from dartlab.pipeline import reconcile as recmod
    from dartlab.pipeline.stages import reconcile as stage

    captured = {}

    def stub(dataCat, *, pull, push, token=None):
        captured["cat"] = dataCat
        captured["push"] = push
        return {"localBefore": 100, "remoteBefore": 90, "pull": 5, "push": 3, "pulled": 5, "pushed": 3, "inSync": False}

    monkeypatch.setattr(recmod, "reconcileCategory", stub)
    res = stage.runPanelReconcile(upload=True)
    assert res.rows == 5 and res.uploaded == 3 and res.report.ok == 1
    assert captured == {"cat": "panel", "push": True}


def test_run_edgar_panel_reconcile_maps_summary(monkeypatch) -> None:
    """runEdgarPanelReconcile — category=edgarPanel, upload=False→push=False."""
    from dartlab.pipeline import reconcile as recmod
    from dartlab.pipeline.stages import reconcile as stage

    captured = {}

    def stub(dataCat, *, pull, push, token=None):
        captured["cat"] = dataCat
        captured["push"] = push
        return {"localBefore": 1, "remoteBefore": 1, "pull": 0, "push": 0, "pulled": 0, "pushed": 0, "inSync": True}

    monkeypatch.setattr(recmod, "reconcileCategory", stub)
    stage.runEdgarPanelReconcile(upload=False)
    assert captured == {"cat": "edgarPanel", "push": False}


def test_run_reconcile_isolates_failure(monkeypatch) -> None:
    """reconcile 예외는 StageResult.report.err 로 격리."""
    from dartlab.pipeline import reconcile as recmod
    from dartlab.pipeline.stages import reconcile as stage

    def boom(*a, **k):
        raise RuntimeError("HF down")

    monkeypatch.setattr(recmod, "reconcileCategory", boom)
    res = stage.runPanelReconcile()
    assert res.report.err == 1 and res.report.ok == 0
    assert any("panelReconcile" in f for f in res.report.failures)


def test_reconcile_stages_registered() -> None:
    """buildRegistry 에 panelReconcile·edgarPanelReconcile 등록 + run 바인딩."""
    from dartlab.pipeline.registry import buildRegistry
    from dartlab.pipeline.stages.reconcile import runEdgarPanelReconcile, runPanelReconcile

    reg = buildRegistry()
    assert reg["panelReconcile"].run is runPanelReconcile
    assert reg["edgarPanelReconcile"].run is runEdgarPanelReconcile
    assert "panel" in reg["panelReconcile"].uploadCategories
    assert "edgarPanel" in reg["edgarPanelReconcile"].uploadCategories


# ── rcept 단위(파일내) panel reconcile (panelRceptReconcile.runPanelRceptReconcile) ──────────


def _stubFilings(rows: list[tuple[str, str, str]]):
    """(stock_code, rcept_no, report_nm) → listFilings 대체 polars df 반환 stub."""
    import polars as pl

    def _fn(client, corp=None, start=None, end=None, **kw):
        return pl.DataFrame(
            {"stock_code": [r[0] for r in rows], "rcept_no": [r[1] for r in rows], "report_nm": [r[2] for r in rows]}
        )

    return _fn


def _wireReconcile(
    monkeypatch,
    *,
    panelHave: dict[str, set[str] | None],
    built: list[str],
    fullHist: dict[str, set[str]] | None = None,
):
    """panelRceptReconcile 의 외부 의존(네트워크/HF/빌드/업로드)을 전부 stub 으로 차단.

    fullHist: 종목별 전이력 정기 rcept (truncation 회복 테스트용). 미지정 시 _fullPeriodicRcepts
    는 panel 보유분과 동일 반환(=truncation 없음).
    """
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    calls: dict = {"build": None, "fetch": [], "fetchCalls": [], "panelUpload": None, "bundle": None, "seq": []}

    monkeypatch.setattr("dartlab.gather.dart.client.DartClient", lambda *a, **k: object())
    monkeypatch.setattr(
        panelRceptReconcile, "_panelRceptsFromHf", lambda repo, relDir, code, *, token=None: panelHave.get(code)
    )
    fh = fullHist or {}
    monkeypatch.setattr(
        panelRceptReconcile, "_fullPeriodicRcepts", lambda client, code: fh.get(code, panelHave.get(code) or set())
    )
    monkeypatch.setattr(upmod, "_resolveHfToken", lambda token=None: None)

    def _iter(client, targets, *, outDir, workers=4):
        calls["fetch"].extend(list(targets))  # chunk 마다 호출되므로 누적
        calls["fetchCalls"].append(list(targets))
        calls["seq"].append(("fetch", sorted({sc for sc, _rc in targets})))
        for sc, rc in targets:
            yield sc, rc, True, 1000

    monkeypatch.setattr("dartlab.gather.dart.document.iterZipsParallel", _iter)

    def _build(changed, newZipsByCode, res, *, token=None, uploadEvery=None):
        # panel 업로드는 이제 빌드 안에서 checkpoint 로 일어난다(uploadEvery). 호출 인자로만 관찰.
        calls["build"] = {"changed": sorted(changed), "newZips": sorted(newZipsByCode), "uploadEvery": uploadEvery}
        calls["seq"].append(("build", sorted(changed)))
        return [c for c in built if c in set(changed)]

    monkeypatch.setattr(dartZip, "_buildPanelIncremental", _build)
    monkeypatch.setattr(dartZip, "_seedChangedFromHf", lambda codes, *, token=None: (len(codes), set(codes)))
    monkeypatch.setattr(panelRceptReconcile, "_pruneHistoryZips", lambda docsBase, codes, *, keep: 0)

    def _bundle(codes, *, token=None):
        calls["bundle"] = sorted(codes)
        calls["seq"].append(("bundle", sorted(codes)))
        return len(codes)

    monkeypatch.setattr(dartZip, "_bundleAndUpload", _bundle)

    def _panelUp(category, *, changedFiles=None, dataDir=None, token=None):
        calls["panelUpload"] = (category, sorted(changedFiles or []))

    monkeypatch.setattr(upmod, "uploadCategoryToHf", _panelUp)
    return calls


def test_panel_rcept_reconcile_registered() -> None:
    """buildRegistry 에 panelRceptReconcile 등록 + dartZip.runPanelRceptReconcile 바인딩."""
    from dartlab.pipeline.registry import buildRegistry
    from dartlab.pipeline.stages.panelRceptReconcile import runPanelRceptReconcile

    reg = buildRegistry()
    assert reg["panelRceptReconcile"].run is runPanelRceptReconcile
    assert "panel" in reg["panelRceptReconcile"].uploadCategories
    assert "dartOriginal" in reg["panelRceptReconcile"].uploadCategories


def test_panel_rcept_reconcile_detects_and_heals(monkeypatch) -> None:
    """DART 에 있는 정기 rcept 가 panel 에 빠지면 그 rcept 만 fetch→merge→push."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    # A: panel 이 분기보고서 rcept 누락 / B: 이미 보유 / C: 비정기(필터 제외)
    monkeypatch.setattr(
        disclosure,
        "listFilings",
        _stubFilings(
            [
                ("000A", "20260513000001", "분기보고서 (2026.03)"),
                ("000B", "20260512000002", "분기보고서 (2026.03)"),
                ("000C", "20260511000003", "주요사항보고서"),
            ]
        ),
    )
    calls = _wireReconcile(
        monkeypatch,
        panelHave={"000A": {"20250514000099"}, "000B": {"20260512000002"}},  # A 누락, B 보유
        built=["000A"],
    )

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert res.changedFiles == ["000A"]
    assert calls["fetch"] == [("000A", "20260513000001")]  # 누락 rcept 만 fetch (B·C 제외)
    assert calls["build"]["changed"] == ["000A"]
    assert calls["build"]["uploadEvery"] == dartZip._PANEL_UPLOAD_EVERY  # panel 업로드는 빌드 안 checkpoint
    assert calls["bundle"] == ["000A"]  # 원본 tar superset 재번들
    assert res.report.ok == 1


def test_panel_rcept_reconcile_no_missing_skips_heal(monkeypatch) -> None:
    """모든 정기 rcept 가 panel 에 있으면 fetch/build/upload 0 (탐지만)."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(disclosure, "listFilings", _stubFilings([("000A", "20260513000001", "분기보고서 (2026.03)")]))
    calls = _wireReconcile(monkeypatch, panelHave={"000A": {"20260513000001"}}, built=[])

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert res.changedFiles == []
    assert calls["fetch"] == [] and calls["build"] is None and calls["panelUpload"] is None
    assert res.report.ok == 1


def test_panel_rcept_reconcile_skips_lookup_failure(monkeypatch) -> None:
    """panel rcept 조회 *일시 실패*(None)는 skip. 다음 run 재시도(성급한 재빌드 차단)."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(disclosure, "listFilings", _stubFilings([("000Z", "20260513000001", "분기보고서 (2026.03)")]))
    calls = _wireReconcile(monkeypatch, panelHave={"000Z": None}, built=[])  # 조회 실패

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert res.changedFiles == [] and calls["fetch"] == [] and calls["build"] is None
    assert res.report.ok == 1


def test_panel_rcept_reconcile_heals_panel_absent(monkeypatch) -> None:
    """panel 미존재(404 는 빈 set)는 heal 대상. 윈도 rcept 전부 fetch + 빌드.

    회귀 가드: 옛 구현은 미존재를 None(skip)으로 두어 "panel 이 한 번도 없던 종목" 이
    영구히 복구되지 않았다 (실측 178600 대동고려삼, 185190 수프로. 코넥스 신규 정기보고서).
    """
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(disclosure, "listFilings", _stubFilings([("000Z", "20260513000001", "분기보고서 (2026.03)")]))
    calls = _wireReconcile(monkeypatch, panelHave={"000Z": set()}, built=["000Z"])  # panel 미존재

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert calls["fetch"] == [("000Z", "20260513000001")]
    assert calls["build"] == {"changed": ["000Z"], "newZips": ["000Z"], "uploadEvery": dartZip._PANEL_UPLOAD_EVERY}
    assert res.changedFiles == ["000Z"]
    assert calls["build"]["uploadEvery"] == dartZip._PANEL_UPLOAD_EVERY  # panel 업로드는 빌드 안 checkpoint
    assert res.report.ok == 1


def test_panel_rcept_reconcile_isolates_listfilings_failure(monkeypatch) -> None:
    """listFilings 실패는 StageResult.report.err 로 격리."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr("dartlab.gather.dart.client.DartClient", lambda *a, **k: object())

    def _boom(*a, **k):
        raise RuntimeError("DART down")

    monkeypatch.setattr(disclosure, "listFilings", _boom)

    res = panelRceptReconcile.runPanelRceptReconcile(upload=False)
    assert res.report.err == 1 and res.report.ok == 0
    assert any("panelRceptReconcile" in f for f in res.report.failures)


def test_panel_rcept_reconcile_recovers_truncation(monkeypatch) -> None:
    """HF panel history 가 파괴(소수 period)된 종목은 전이력 대조로 옛 분기까지 회복(043260-class)."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(disclosure, "listFilings", _stubFilings([("000T", "20260515000010", "분기보고서 (2026.03)")]))
    # panel 엔 최신 1개만(truncated) · 전이력엔 3개 → 옛 2개가 회복 대상.
    calls = _wireReconcile(
        monkeypatch,
        panelHave={"000T": {"20260515000010"}},
        built=["000T"],
        fullHist={"000T": {"20260515000010", "20200515000001", "20210517000002"}},
    )

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert res.changedFiles == ["000T"]
    assert sorted(calls["fetch"]) == [("000T", "20200515000001"), ("000T", "20210517000002")]
    assert calls["build"]["uploadEvery"] == dartZip._PANEL_UPLOAD_EVERY  # panel 업로드는 빌드 안 checkpoint


def test_panel_rcept_reconcile_heals_in_chunks_tar_before_panel(monkeypatch) -> None:
    """heal 은 _HEAL_CHUNK 종목씩 "원본 tar 번들, 그다음 panel 빌드" 순으로 닫힌다.

    분기 마감 뒤 수천 종목 backlog 가 job timeout 에 통째로 증발하지 않게 chunk 마다 진전을 남기고,
    원본 SSOT(tar) 가 panel 보다 뒤지지 않게 한다.
    """
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(
        disclosure,
        "listFilings",
        _stubFilings(
            [
                ("000A", "20260814000001", "반기보고서 (2026.06)"),
                ("000B", "20260814000002", "반기보고서 (2026.06)"),
            ]
        ),
    )
    calls = _wireReconcile(monkeypatch, panelHave={"000A": set(), "000B": set()}, built=["000A", "000B"])
    monkeypatch.setattr(panelRceptReconcile, "_HEAL_CHUNK", 1)

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    # zip fetch 도 chunk 안에서 일어난다. 첫 체크포인트가 전체 fetch 뒤로 밀리지 않는다(2026-08-22 실측 가드).
    assert calls["seq"] == [
        ("fetch", ["000A"]),
        ("bundle", ["000A"]),
        ("build", ["000A"]),
        ("fetch", ["000B"]),
        ("bundle", ["000B"]),
        ("build", ["000B"]),
    ]
    assert calls["fetchCalls"] == [[("000A", "20260814000001")], [("000B", "20260814000002")]]
    assert res.changedFiles == ["000A", "000B"]
    assert res.uploaded == 2  # chunk 별 tar 업로드 수 누적
    assert res.report.ok == 1


def test_panel_rcept_reconcile_reports_total_fetch_failure(monkeypatch) -> None:
    """모든 chunk 에서 zip fetch 가 0 이면 fail 로 보고하고 빌드는 호출되지 않는다(다음 run 재시도)."""
    from dartlab.gather.dart import disclosure
    from dartlab.pipeline.stages import panelRceptReconcile

    monkeypatch.setattr(disclosure, "listFilings", _stubFilings([("000A", "20260814000001", "반기보고서 (2026.06)")]))
    calls = _wireReconcile(monkeypatch, panelHave={"000A": set()}, built=["000A"])

    def _iterFail(client, targets, *, outDir, workers=4):
        for sc, rc in targets:
            yield sc, rc, False, 0

    monkeypatch.setattr("dartlab.gather.dart.document.iterZipsParallel", _iterFail)

    res = panelRceptReconcile.runPanelRceptReconcile(upload=True)

    assert res.report.fail == 1 and any("zip fetch 0/1" in f for f in res.report.failures)
    assert calls["build"] is None and calls["bundle"] is None
    assert res.changedFiles == []


# ── seed spurious-404 데이터손실 가드 (_seedPanelFromHf / _seedChangedFromHf) ──────


def test_seed_panel_spurious_404_excluded(monkeypatch) -> None:
    """listing 엔 있는데 download 404(spurious) → unsafe(제외) — 파괴적 덮어쓰기 가드."""
    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    from dartlab.core.dataConfig import DATA_RELEASES
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    relDir = DATA_RELEASES["panel"]["dir"]
    monkeypatch.setattr(upmod, "_resolveHfToken", lambda token=None: None)
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: {f"{relDir}/000A.parquet"})

    def _dl(*a, **k):
        raise EntryNotFoundError("spurious 404")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _dl)
    _n, safe = dartZip._seedPanelFromHf(["000A"], token=None)
    assert safe == set()  # listing 에 존재 → spurious → NOT safe → overwrite 안 함


def test_seed_panel_genuine_new_safe(monkeypatch) -> None:
    """listing 에도 없음(진짜 신규) → safe — base 없이 신규 write 정당."""
    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(upmod, "_resolveHfToken", lambda token=None: None)
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: set())  # repo 에 없음

    def _dl(*a, **k):
        raise EntryNotFoundError("not found")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _dl)
    _n, safe = dartZip._seedPanelFromHf(["000NEW"], token=None)
    assert safe == {"000NEW"}


def test_seed_panel_listing_unavailable_conservative(monkeypatch) -> None:
    """listing 실패(None) → 모든 404 transient 취급(보수적) → safe 0, 데이터손실 0."""
    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(upmod, "_resolveHfToken", lambda token=None: None)
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: None)  # listing 실패

    def _dl(*a, **k):
        raise EntryNotFoundError("404")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _dl)
    _n, safe = dartZip._seedPanelFromHf(["000A"], token=None)
    assert safe == set()  # 구분 불가 → 보수적 제외(다음 run 회복)


def test_seed_changed_spurious_404_excluded(monkeypatch, tmp_path) -> None:
    """원본 tar seed 도 동일 가드 — listing 에 있으면 spurious 404 는 unsafe(tar truncate 방지)."""
    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload as upmod
    from dartlab.pipeline.stages import dartZip, panelRceptReconcile

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))  # tar stage 디렉터리가 실제 data/ 에 생기지 않게
    monkeypatch.setattr(upmod, "_resolveHfToken", lambda token=None: None)
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: {"docs/000A.tar"})

    def _dl(*a, **k):
        raise EntryNotFoundError("spurious 404")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", _dl)
    _n, safe = dartZip._seedChangedFromHf(["000A"], token=None)
    assert safe == set()
