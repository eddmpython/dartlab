"""원본=SSOT stage(dartZip·edgarPanel) 데이터손실 가드 단위 — 네트워크 0(mock)."""

from __future__ import annotations

import tarfile

import pytest

pytestmark = pytest.mark.unit


def _makeTar(path, zipNames: list[str]) -> None:
    """zipNames 를 멤버로 갖는 회사 tar 생성(각 멤버는 유효 zip magic)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    for nm in zipNames:
        z = path.parent / nm
        z.write_bytes(b"PK\x03\x04" + b"\x00" * 50)
    with tarfile.open(path, "w") as tf:
        for nm in zipNames:
            tf.add(path.parent / nm, arcname=nm)
    for nm in zipNames:
        (path.parent / nm).unlink()


def test_dartzip_seed_safe_set_404_vs_transient(monkeypatch, tmp_path) -> None:
    """_seedChangedFromHf — 성공·*진짜 신규 404*(listing 부재) 만 safe, 일시 실패·부분추출 제외.

    404 는 listing 에 *진짜 없을 때만* 신규=safe. listing 엔 있는데 404(spurious)는 일시 실패와
    같이 제외(원본 tar truncate 데이터손실 가드 — 043260-class).
    """
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload
    from dartlab.pipeline.stages import dartZip

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "x")
    # retryHfCall 패스스루(재시도 로직 우회 — 예외 즉시 전파)
    monkeypatch.setattr("dartlab.core.hfRetry.retryHfCall", lambda fn, *a, **k: fn(*a, **k))
    # listing: AAA 존재 · BBB 부재(진짜 신규) — CCC 는 일시 실패라 listing 무관 제외.
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: {"docs/AAA.tar"})

    from huggingface_hub.utils import EntryNotFoundError

    tarDir = tmp_path / "_hf"
    _makeTar(tarDir / "AAA.tar", ["r1.zip", "r2.zip"])  # 완전 tar(2 멤버)

    def fakeDownload(*, repo_id, repo_type, filename, token):
        code = filename.split("/")[-1][:-4]
        if code == "AAA":
            return str(tarDir / "AAA.tar")
        if code == "BBB":
            raise EntryNotFoundError("404")  # 신규 종목(listing 에도 없음)
        raise RuntimeError("transient 5xx")  # 일시 실패 → 제외

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fakeDownload)

    n, safe = dartZip._seedChangedFromHf(["AAA", "BBB", "CCC"], token="x")
    assert safe == {"AAA", "BBB"}  # CCC(일시 실패) 제외 · BBB(listing 부재) 신규 safe
    assert n == 1  # AAA 만 실제 추출
    extracted = sorted(p.name for p in (tmp_path / "original" / "dart" / "docs" / "AAA").glob("*.zip"))
    assert extracted == ["r1.zip", "r2.zip"]  # 완전 추출


def test_dartzip_seed_partial_extract_excluded(monkeypatch, tmp_path) -> None:
    """부분 추출(zip < tar 멤버)은 무결성 실패 → safe 제외(잘린 panel·tar 덮어쓰기 차단)."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload
    from dartlab.pipeline.stages import dartZip

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "x")
    monkeypatch.setattr("dartlab.core.hfRetry.retryHfCall", lambda fn, *a, **k: fn(*a, **k))

    # 멤버 0 인 빈 tar → 정상(공집합). 손상 tar 는 tarfile 이 raise → 제외.
    bad = tmp_path / "_hf" / "DDD.tar"
    bad.parent.mkdir(parents=True, exist_ok=True)
    bad.write_bytes(b"not a tar at all")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", lambda **k: str(bad))
    n, safe = dartZip._seedChangedFromHf(["DDD"], token="x")
    assert safe == set() and n == 0  # 손상 tar → 제외


def test_dartzip_seed_isolates_count_from_stale_zips(monkeypatch, tmp_path) -> None:
    """무결성 카운트는 *격리 임시 dir* 기준 — dest 의 이전 run 잔재 zip 이 부분추출을 가리지 못한다.

    회귀 가드(finding #6): 옛 코드는 dest 에 바로 풀어 ``len(dest.glob)`` 로 검증해 잔재가 카운트를
    부풀렸다. 완전 tar 는 잔재 보존 + 신규 병합으로 통과하되, 카운트는 새로 푼 셋만 센다.
    """
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload
    from dartlab.pipeline.stages import dartZip

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "x")
    monkeypatch.setattr("dartlab.core.hfRetry.retryHfCall", lambda fn, *a, **k: fn(*a, **k))

    dest = tmp_path / "original" / "dart" / "docs" / "AAA"
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "stale1.zip").write_bytes(b"PK\x03\x04old1")  # 이전 run 잔재
    (dest / "stale2.zip").write_bytes(b"PK\x03\x04old2")

    tarDir = tmp_path / "_hf"
    _makeTar(tarDir / "AAA.tar", ["r1.zip", "r2.zip"])  # 완전 tar(2 멤버)
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", lambda **k: str(tarDir / "AAA.tar"))

    n, safe = dartZip._seedChangedFromHf(["AAA"], token="x")
    assert safe == {"AAA"} and n == 1
    names = sorted(p.name for p in dest.glob("*.zip"))
    assert names == ["r1.zip", "r2.zip", "stale1.zip", "stale2.zip"]  # 잔재 보존 + 신규 병합


def test_runincremental_partial_fetch_skips_build_without_raw(monkeypatch, tmp_path) -> None:
    """신규 종목 text fetch 가 부분 실패하면 build/changed 제외 + raw 미생성(다음 run 재시도)."""
    import importlib

    import dartlab.config as cfg
    from dartlab.pipeline.stages import edgarPanel
    from dartlab.pipeline.types import StageResult

    # dartlab.gather.original 은 GatherEntry 속성으로 shadow 되어 monkeypatch 의 dotted-path 해소가
    # 깨진다 → 실제 모듈 객체를 importlib 로 얻어 setattr(_runIncremental 의 from-import 가 읽는 곳).
    edgarCollect = importlib.import_module("dartlab.gather.original.edgar.collect")
    edgarBuild = importlib.import_module("dartlab.providers.edgar.panel.build")
    edgarIdentity = importlib.import_module("dartlab.gather.edgar.identity")

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(edgarPanel, "_universeTickerByCik", lambda: {"0000099999": ["NEW"]})
    monkeypatch.setattr(edgarPanel, "_seedTickerPanel", lambda ticker, *, token: False)  # 신규(404)
    monkeypatch.setattr(
        edgarCollect,
        "listRecentFilings",
        lambda dates, *, forms: [{"cik": "0000099999", "accession_no": "X-1", "txt_url": "u"}],
    )
    monkeypatch.setattr(edgarIdentity, "loadTickers", lambda refresh=False: None, raising=False)

    listed = {"n": 0}
    fetched = {"n": 0}
    built = {"n": 0}

    def fakeListAll(ticker, *, forms, sinceYear):
        listed["n"] += 1
        return [
            {"cik": "0000099999", "accession_no": "X-1", "txt_url": "u1"},
            {"cik": "0000099999", "accession_no": "X-2", "txt_url": "u2"},
        ]

    def fakeFetch(rows):
        fetched["n"] += 1
        return {"0000099999": [{"cik": "0000099999", "accession_no": "X-1", "text": "x"}]}  # 1/2 부분 실패

    def fakeBuild(ticker, filings, *, overwrite, verbose):
        built["n"] += 1
        return {"rows": 100}

    edgarSubmissions = importlib.import_module("dartlab.gather.original.edgar.submissions")
    monkeypatch.setattr(edgarSubmissions, "listAllFilings", fakeListAll)
    monkeypatch.setattr(edgarCollect, "fetchFilingTexts", fakeFetch)
    monkeypatch.setattr(edgarBuild, "buildEdgarPanel", fakeBuild)

    out = edgarPanel._runIncremental(StageResult(category="edgarPanel"), lookback=3, upload=False, token="x")

    assert listed["n"] == 1 and fetched["n"] == 1
    assert built["n"] == 0  # 부분 fetch → build 제외(부분 panel 박제 방지)
    assert out.rows == 0  # changed 0
    assert not (tmp_path / "original" / "edgar" / "docs").exists()  # raw 저장 없음


def test_seed_ticker_panel_404_vs_transient(monkeypatch, tmp_path) -> None:
    """_seedTickerPanel — panel 404=False, panel 일시실패=None."""
    import huggingface_hub

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload
    from dartlab.pipeline.stages import edgarPanel

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "x")
    monkeypatch.setattr("dartlab.core.hfRetry.retryHfCall", lambda fn, *a, **k: fn(*a, **k))

    from huggingface_hub.utils import EntryNotFoundError

    state = {"boardErr": None}

    def fake(*, repo_id, repo_type, filename, token, local_dir):
        if state["boardErr"]:
            raise state["boardErr"]
        return filename

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fake)

    # board 404 → False(신규)
    state.update(boardErr=EntryNotFoundError("404"))
    assert edgarPanel._seedTickerPanel("AAR", token="x") is False
    # board 일시실패 → None
    state.update(boardErr=RuntimeError("5xx"))
    assert edgarPanel._seedTickerPanel("AAR", token="x") is None
    # board ok → True
    state.update(boardErr=None)
    assert edgarPanel._seedTickerPanel("AAR", token="x") is True


def test_universe_ticker_by_cik_multiclass(monkeypatch) -> None:
    """_universeTickerByCik — 한 CIK 의 복수 ticker(주식클래스)를 list 로 모음."""
    import polars as pl

    from dartlab.pipeline.stages import edgarPanel

    uni = pl.DataFrame({"cik": [1652044, 1652044, 320193], "ticker": ["GOOGL", "GOOG", "AAPL"]})
    monkeypatch.setattr(
        "dartlab.core.dataLoader.loadEdgarListedUniverse", lambda *, forceUpdate=False: uni, raising=False
    )
    m = edgarPanel._universeTickerByCik()
    assert sorted(m["0001652044"]) == ["GOOG", "GOOGL"]  # 두 클래스 모두 보존
    assert m["0000320193"] == ["AAPL"]


def test_run_allfilings_callable() -> None:
    """runAllFilings forward 증분 stage callable smoke."""
    from dartlab.pipeline.stages.allFilings import runAllFilings

    assert callable(runAllFilings)


def test_run_allfilings_retries_transient_collect(monkeypatch) -> None:
    """runAllFilings — collectMetaRange transient timeout 은 bounded retry 후 계속 진행."""
    import polars as pl

    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("SYNC_LOOKBACK_DAYS", "1")
    monkeypatch.setenv("DART_ALLFILINGS_STAGE_RETRIES", "1")
    monkeypatch.setenv("DART_ALLFILINGS_RETRY_SLEEP_SECONDS", "0")

    attempts = {"collect": 0, "fill": 0, "push": 0}

    def flakyCollect(*args, **kwargs):
        attempts["collect"] += 1
        if attempts["collect"] == 1:
            raise TimeoutError("timed out")
        return 1

    def fakeFill(*args, **kwargs):
        attempts["fill"] += 1
        return pl.DataFrame({"rcept_no": ["1", "2"]})

    def fakePush(*args, **kwargs):
        attempts["push"] += 1

    monkeypatch.setattr(coll, "collectMetaRange", flakyCollect)
    monkeypatch.setattr(coll, "fillContent", fakeFill)
    monkeypatch.setattr(sync, "pushAllFilings", fakePush)

    res = allFilings.runAllFilings(upload=True)

    assert attempts == {"collect": 2, "fill": 1, "push": 1}
    assert res.rows == 2
    assert res.uploaded == 1
    assert res.report.ok == 1
    assert res.report.err == 0


def test_run_allfilings_retries_transient_fill(monkeypatch) -> None:
    """runAllFilings — fillContent transient timeout 도 날짜 단위로 retry."""
    import polars as pl

    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("SYNC_LOOKBACK_DAYS", "1")
    monkeypatch.setenv("DART_ALLFILINGS_STAGE_RETRIES", "1")
    monkeypatch.setenv("DART_ALLFILINGS_RETRY_SLEEP_SECONDS", "0")

    attempts = {"fill": 0}
    monkeypatch.setattr(coll, "collectMetaRange", lambda *args, **kwargs: 1)

    def flakyFill(*args, **kwargs):
        attempts["fill"] += 1
        if attempts["fill"] == 1:
            raise TimeoutError("timed out")
        return pl.DataFrame({"rcept_no": ["1"]})

    monkeypatch.setattr(coll, "fillContent", flakyFill)
    monkeypatch.setattr(sync, "pushAllFilings", lambda *args, **kwargs: None)

    res = allFilings.runAllFilings(upload=True)

    assert attempts["fill"] == 2
    assert res.rows == 1
    assert res.uploaded == 1
    assert res.report.ok == 1
    assert res.report.err == 0


def test_run_allfilings_progress_is_enabled_by_default(monkeypatch, capsys) -> None:
    """runAllFilings — source-owner Actions 로그를 위해 progress 를 기본 활성화."""
    from datetime import date

    import polars as pl

    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("SYNC_LOOKBACK_DAYS", "1")
    captured: list[tuple[str, bool]] = []

    def fakeCollect(*args, showProgress, **kwargs):
        captured.append(("collect", showProgress))
        return 1

    def fakeFill(period, *, showProgress, **kwargs):
        captured.append((period, showProgress))
        return pl.DataFrame({"rcept_no": ["1"]})

    monkeypatch.setattr(coll, "collectMetaRange", fakeCollect)
    monkeypatch.setattr(coll, "fillContent", fakeFill)
    monkeypatch.setattr(sync, "pushAllFilings", lambda *args, **kwargs: None)

    res = allFilings.runAllFilings(upload=True)
    out = capsys.readouterr().out

    assert res.rows == 1
    assert captured == [("collect", True), (date.today().strftime("%Y%m%d"), True)]
    assert "allFilings forward 시작" in out
    assert "allFilings fillContent 완료" in out


def test_run_allfilings_reports_after_retry_exhausted(monkeypatch) -> None:
    """runAllFilings — retry 소진 뒤에는 기존처럼 StageResult.err 로 격리."""
    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("SYNC_LOOKBACK_DAYS", "1")
    monkeypatch.setenv("DART_ALLFILINGS_STAGE_RETRIES", "1")
    monkeypatch.setenv("DART_ALLFILINGS_RETRY_SLEEP_SECONDS", "0")

    attempts = {"collect": 0}

    def failingCollect(*args, **kwargs):
        attempts["collect"] += 1
        raise TimeoutError("timed out")

    monkeypatch.setattr(coll, "collectMetaRange", failingCollect)

    res = allFilings.runAllFilings(upload=False)

    assert attempts["collect"] == 2
    assert res.report.err == 1
    assert res.report.ok == 0
    assert "TimeoutError" in res.report.failures[0]


def test_run_allfilings_reconcile_maps_summary(monkeypatch) -> None:
    """runAllFilingsReconcile — reconcile summary → StageResult(rows=pulled, uploaded=pushed, ok)."""
    from dartlab.gather.dart import allFilingsSync as collector
    from dartlab.pipeline.stages import allFilings

    captured: dict[str, bool] = {}

    def stubReconcile(*, pull, push, token=None):
        captured["pull"] = pull
        captured["push"] = push
        return {
            "localBefore": 220,
            "remoteBefore": 225,
            "pullDates": ["20260605"],
            "pushDates": ["20260606", "20260607"],
            "pulled": 1,
            "pushed": 2,
            "localAfter": 221,
            "inSync": False,
        }

    monkeypatch.setattr(collector, "reconcileAllFilings", stubReconcile)
    res = allFilings.runAllFilingsReconcile(upload=True)
    assert res.rows == 1  # pulled (HF→로컬)
    assert res.uploaded == 2  # pushed (로컬→HF)
    assert res.report.ok == 1
    assert res.report.err == 0
    assert captured == {"pull": True, "push": True}


def test_run_allfilings_reconcile_push_disabled(monkeypatch) -> None:
    """upload=False → reconcile push=False 전달 (pull-only)."""
    from dartlab.gather.dart import allFilingsSync as collector
    from dartlab.pipeline.stages import allFilings

    captured: dict[str, bool] = {}

    def stubReconcile(*, pull, push, token=None):
        captured["pull"] = pull
        captured["push"] = push
        return {
            "localBefore": 1,
            "remoteBefore": 2,
            "pullDates": [],
            "pushDates": [],
            "pulled": 0,
            "pushed": 0,
            "localAfter": 1,
            "inSync": True,
        }

    monkeypatch.setattr(collector, "reconcileAllFilings", stubReconcile)
    allFilings.runAllFilingsReconcile(upload=False)
    assert captured == {"pull": True, "push": False}


def test_run_allfilings_reconcile_isolates_failure(monkeypatch) -> None:
    """reconcile 예외는 StageResult.report.err 로 격리 — run 중단·전파 X."""
    from dartlab.gather.dart import allFilingsSync as collector
    from dartlab.pipeline.stages import allFilings

    def boom(*, pull, push, token=None):
        raise RuntimeError("HF down")

    monkeypatch.setattr(collector, "reconcileAllFilings", boom)
    res = allFilings.runAllFilingsReconcile()
    assert res.report.err == 1
    assert res.report.ok == 0
    assert any("reconcile" in f for f in res.report.failures)


def test_allfilings_reconcile_registered() -> None:
    """buildRegistry 에 allFilingsReconcile stage 등록 — run 바인딩 + uploadCategories."""
    from dartlab.pipeline.registry import buildRegistry
    from dartlab.pipeline.stages.allFilings import runAllFilingsReconcile

    reg = buildRegistry()
    assert "allFilingsReconcile" in reg
    assert reg["allFilingsReconcile"].run is runAllFilingsReconcile
    assert "allFilings" in reg["allFilingsReconcile"].uploadCategories


# ── allFilings 과거 백필 (2개월/run, floor 2015-01) ──


def test_prev_months_floor_inclusive() -> None:
    """_prevMonths — 앵커 직전부터 과거로 N개월, floor 포함·이전 차단."""
    from dartlab.pipeline.stages.allFilings import _prevMonths

    assert _prevMonths("202503", 2, "201501") == ["202502", "202501"]  # 직전 2개월
    assert _prevMonths("201502", 2, "201501") == ["201501"]  # floor inclusive (1개만)
    assert _prevMonths("201501", 2, "201501") == []  # 앵커=floor → 커버리지 달성
    assert _prevMonths("202601", 2, "201501") == ["202512", "202511"]  # 연 경계


def test_month_days() -> None:
    """_monthDays — 월 1일~말일 YYYYMMDD(2월 28·12월 31)."""
    from dartlab.pipeline.stages.allFilings import _monthDays

    assert _monthDays("202502") == [f"202502{d:02d}" for d in range(1, 29)]
    assert len(_monthDays("202412")) == 31
    assert _monthDays("202501")[0] == "20250101" and _monthDays("202501")[-1] == "20250131"


def test_run_allfilings_backfill_collects_prev_months(monkeypatch) -> None:
    """runAllFilingsBackfill — 앵커 직전 2개월 collect + 월별 push, StageResult 매핑."""
    import polars as pl

    import dartlab.core.dartClient as dc
    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("DART_ALLFILINGS_BACKFILL_MONTHS", "2")
    monkeypatch.setenv("DART_ALLFILINGS_BACKFILL_FLOOR", "201501")
    monkeypatch.setattr(dc, "DartClient", lambda *a, **k: object())  # 실 DART init 차단
    monkeypatch.setattr(coll, "collectedDates", lambda: [])  # CI = 로컬 비어있음
    monkeypatch.setattr(sync, "_remoteDates", lambda token=None: {"20250304", "20250601"})  # earliest=202503

    filled: list[str] = []

    def fakeFill(period, *, client=None, showProgress=True):
        filled.append(period)
        return pl.DataFrame({"x": [1]}) if period[-2:] in ("02", "04") else None  # 나머지=휴일(None)

    monkeypatch.setattr(coll, "fillContent", fakeFill)

    pushed: list[list[str]] = []

    def fakePush(dates, *, token=None):
        pushed.append(list(dates))
        return len(dates)

    monkeypatch.setattr(sync, "pushAllFilings", fakePush)

    res = allFilings.runAllFilingsBackfill(upload=True)

    assert {d[:6] for d in filled} == {"202502", "202501"}  # 직전 2개월만 수집 시도
    assert len(pushed) == 2  # 월별 push (timeout 내성)
    assert all(p[-2:] in ("02", "04") for batch in pushed for p in batch)  # 본문 있는 일자만 push
    assert res.report.ok == 1 and res.report.err == 0
    assert res.uploaded == sum(len(b) for b in pushed)
    assert res.rows == res.uploaded  # 본문 1행씩


def test_run_allfilings_backfill_noop_at_floor(monkeypatch) -> None:
    """앵커 월이 floor 이하면 no-op — fillContent 미호출, ok."""
    import dartlab.core.dartClient as dc
    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("DART_ALLFILINGS_BACKFILL_FLOOR", "201501")
    monkeypatch.setattr(coll, "collectedDates", lambda: [])
    monkeypatch.setattr(sync, "_remoteDates", lambda token=None: {"20150103"})  # earliest=201501=floor

    def boomFill(*a, **k):
        raise AssertionError("커버리지 달성 시 수집 금지")

    monkeypatch.setattr(coll, "fillContent", boomFill)
    monkeypatch.setattr(dc, "DartClient", lambda *a, **k: object())

    res = allFilings.runAllFilingsBackfill(upload=False)
    assert res.report.ok == 1 and res.rows == 0 and res.uploaded == 0


def test_run_allfilings_backfill_anchor_failure_is_nonblocking(monkeypatch) -> None:
    """앵커 조회 예외는 skip 으로 격리 — forward/search 자동 갱신을 막지 않는다."""
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    def boom(token=None):
        raise RuntimeError("HF down")

    monkeypatch.setattr(sync, "_remoteDates", boom)
    res = allFilings.runAllFilingsBackfill()
    assert res.report.skip == 1 and res.report.err == 0 and res.report.fail == 0
    assert any("backfill" in f for f in res.report.failures)


def test_run_allfilings_backfill_month_failure_is_nonblocking(monkeypatch) -> None:
    """월별 수집 중 transient 예외가 나도 skip 으로 격리하고 앞 일자 결과는 보존."""
    import polars as pl

    import dartlab.core.dartClient as dc
    from dartlab.gather.dart import allFilingsCollector as coll
    from dartlab.gather.dart import allFilingsSync as sync
    from dartlab.pipeline.stages import allFilings

    monkeypatch.setenv("DART_ALLFILINGS_BACKFILL_MONTHS", "1")
    monkeypatch.setattr(dc, "DartClient", lambda *a, **k: object())
    monkeypatch.setattr(coll, "collectedDates", lambda: [])
    monkeypatch.setattr(sync, "_remoteDates", lambda token=None: {"20250304"})

    calls = {"n": 0}

    def flakyFill(period, *, client=None, showProgress=True):
        calls["n"] += 1
        if calls["n"] == 1:
            return pl.DataFrame({"x": [1]})
        raise TimeoutError("timed out")

    monkeypatch.setattr(coll, "fillContent", flakyFill)

    pushed: list[list[str]] = []
    monkeypatch.setattr(sync, "pushAllFilings", lambda dates, *, token=None: pushed.append(list(dates)))

    res = allFilings.runAllFilingsBackfill(upload=True)

    assert res.report.ok == 1
    assert res.report.skip == 1
    assert res.report.err == 0 and res.report.fail == 0
    assert res.rows == 1
    assert pushed == []  # 실패한 월은 부분 push 하지 않고 다음 run 에서 재시도
    assert any("TimeoutError" in f for f in res.report.failures)


def test_allfilings_backfill_registered() -> None:
    """buildRegistry 에 allFilingsBackfill stage 등록 — run 바인딩 + uploadCategories."""
    from dartlab.pipeline.registry import buildRegistry
    from dartlab.pipeline.stages.allFilings import runAllFilingsBackfill

    reg = buildRegistry()
    assert "allFilingsBackfill" in reg
    assert reg["allFilingsBackfill"].run is runAllFilingsBackfill
    assert "allFilings" in reg["allFilingsBackfill"].uploadCategories


# ── dartZip within-company 증분 빌드 (신규 zip만 merge=True, 전이력 재파싱 OOM 제거) ──


def test_seed_panel_from_hf_404_vs_transient(monkeypatch, tmp_path) -> None:
    """_seedPanelFromHf — 성공·*진짜 신규 404*(listing 부재) 만 safe, 일시 실패·spurious 404 제외.

    404 가 listing 에 *진짜 없을 때만* 신규=safe(base 없이 merge 정당). listing 엔 있는데 404(spurious)
    면 merge base 부재로 overwrite=신규만 → 정상 HF panel 파괴(history 소실, 043260-class) → 제외.
    """
    from pathlib import Path

    import huggingface_hub
    from huggingface_hub.utils import EntryNotFoundError

    import dartlab.config as cfg
    from dartlab.pipeline import hfUpload
    from dartlab.pipeline.stages import dartZip

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "x")
    monkeypatch.setattr("dartlab.core.hfRetry.retryHfCall", lambda fn, *a, **k: fn(*a, **k))
    # listing: AAA 존재 · BBB 부재(진짜 신규) — 네트워크 0(실제 list_repo_files 대체).
    monkeypatch.setattr(dartZip, "_hfFileSet", lambda repo, *, token=None: {"dart/panel/AAA.parquet"})

    def fakeDownload(*, repo_id, repo_type, filename, local_dir, token):
        code = filename.split("/")[-1][: -len(".parquet")]
        if code == "AAA":
            p = Path(local_dir) / filename  # local_dir 하위에 merge base 배치(증분 빌드가 읽음)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"PARQUETBASE")
            return str(p)
        if code == "BBB":
            raise EntryNotFoundError("404")  # 신규 종목 — HF panel 없음 → base 없이 merge 정당
        raise RuntimeError("transient 5xx")  # 일시 실패 → 제외

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fakeDownload)

    n, safe = dartZip._seedPanelFromHf(["AAA", "BBB", "CCC"], token="x")
    assert safe == {"AAA", "BBB"}  # CCC(일시 실패) 제외
    assert n == 1  # AAA 만 실제 다운로드
    assert (tmp_path / "dart" / "panel" / "AAA.parquet").exists()  # merge base 배치


def _fakeRefAndStream(monkeypatch, tmp_path):
    """_buildPanelIncremental 의 refDf 로드(panelXbrlRef)와 buildPanelFromStream 을 mock — 호출 capture."""
    import polars as pl

    ref = tmp_path / "ref.parquet"
    pl.DataFrame({"a": [1]}).write_parquet(str(ref))
    monkeypatch.setattr("dartlab.providers.dart.panel.build.panelXbrlRefPath", lambda: ref)

    calls: list[tuple[str, list]] = []

    def fakeStream(code, docStream, *, refDf, outBaseDir, overwrite):
        calls.append((code, list(docStream)))  # 스트림 소비(= 어떤 zip 이 흘렀는지)
        return {"2025Q4": 5}

    monkeypatch.setattr("dartlab.providers.dart.panel.build.buildPanelFromStream", fakeStream)
    return calls


def test_dartzip_incremental_builds_only_new_zips(monkeypatch, tmp_path) -> None:
    """_buildPanelIncremental — 신규 zip(newZipsByCode)만 bytes 스트림으로 merge, 빌드된 코드 반환."""
    import dartlab.config as cfg
    from dartlab.pipeline.stages import dartZip
    from dartlab.pipeline.types import StageResult

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(dartZip, "_seedPanelFromHf", lambda codes, *, token: (1, {"AAA"}))
    calls = _fakeRefAndStream(monkeypatch, tmp_path)

    zdir = tmp_path / "original" / "dart" / "docs" / "AAA"
    zdir.mkdir(parents=True, exist_ok=True)
    z = zdir / "20250101000001.zip"
    z.write_bytes(b"PK\x03\x04new")
    newZipsByCode = {"AAA": [z]}

    res = StageResult(category="dartOriginal")
    built = dartZip._buildPanelIncremental(["AAA"], newZipsByCode, res, token=None)

    assert built == ["AAA"]
    assert len(calls) == 1
    code, stream = calls[0]
    assert code == "AAA"
    assert stream == [("20250101000001", b"PK\x03\x04new")]  # zp.stem=rcept, zp.read_bytes()=bytes


def test_dartzip_panel_seed_transient_excludes_build(monkeypatch, tmp_path) -> None:
    """panel seed 일시 실패 코드는 panelSafe 밖 → build·upload 제외(데이터손실 가드, return 에서 누락)."""
    import dartlab.config as cfg
    from dartlab.pipeline.stages import dartZip
    from dartlab.pipeline.types import StageResult

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    # BBB 는 일시 실패로 panelSafe 에서 빠짐(AAA 만 safe)
    monkeypatch.setattr(dartZip, "_seedPanelFromHf", lambda codes, *, token: (1, {"AAA"}))
    calls = _fakeRefAndStream(monkeypatch, tmp_path)

    base = tmp_path / "original" / "dart" / "docs"
    newZipsByCode = {}
    for code in ("AAA", "BBB"):
        d = base / code
        d.mkdir(parents=True, exist_ok=True)
        z = d / f"2025010100000{code[-1]}.zip"
        z.write_bytes(b"PK\x03\x04")
        newZipsByCode[code] = [z]

    res = StageResult(category="dartOriginal")
    built = dartZip._buildPanelIncremental(["AAA", "BBB"], newZipsByCode, res, token=None)

    assert built == ["AAA"]  # BBB 제외(merge base 부재 → 빌드 안 함)
    assert [c for c, _ in calls] == ["AAA"]


def test_dartzip_full_rebuild_flag_routes_build(monkeypatch, tmp_path) -> None:
    """DART_PANEL_FULL_REBUILD=1 → buildPanelAll(전이력), 미설정 → _buildPanelIncremental(증분) 라우팅."""
    import dartlab.config as cfg
    from dartlab.pipeline.stages import dartZip

    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))

    def fakeArchive(start, end, *, scope, corpClasses, showProgress):
        assert corpClasses == ("Y", "K", "N")
        d = tmp_path / "original" / "dart" / "docs" / "AAA"
        d.mkdir(parents=True, exist_ok=True)
        (d / "20250101000001.zip").write_bytes(b"PK\x03\x04")  # 신규 zip → newZipsByCode 차분 포착
        return {"changedCodes": ["AAA"]}

    monkeypatch.setattr("dartlab.gather.original.dart.collect.archiveDartOriginals", fakeArchive)
    monkeypatch.setattr(dartZip, "_seedChangedFromHf", lambda codes, *, token: (1, {"AAA"}))
    monkeypatch.setattr("dartlab.providers.dart.panel.build.panelXbrlRefPath", lambda: tmp_path / "ref.parquet")

    fullCalls: list = []
    incCalls: list = []
    monkeypatch.setattr("dartlab.providers.dart.panel.build.buildPanelAll", lambda **k: fullCalls.append(k))
    monkeypatch.setattr(dartZip, "_buildPanelIncremental", lambda *a, **k: incCalls.append(a) or ["AAA"])

    for flag, expectFull in (("1", True), ("0", False)):
        fullCalls.clear()
        incCalls.clear()
        monkeypatch.setenv("DART_PANEL_FULL_REBUILD", flag)
        dartZip.runDartZip(upload=False, token=None)  # upload=False → tar/panel push 스킵(라우팅만)
        if expectFull:
            assert fullCalls and not incCalls  # 전이력 재빌드
        else:
            assert incCalls and not fullCalls  # within-company 증분


# ─── dartZip 원본 tar 업로드 배치 (2026-08-19 사고 회귀 가드) ────────────────


def _fakeHfApi(calls: dict):
    class _Api:
        def __init__(self, token=None):
            self.token = token

        def create_commit(self, *, repo_id, repo_type, operations, commit_message):
            calls.setdefault("commits", []).append(len(operations))
            return object()

        def upload_file(self, **kwargs):  # pragma: no cover
            calls.setdefault("individual", []).append(kwargs.get("path_in_repo"))
            raise AssertionError("종목당 개별 upload_file 은 429 를 유발한다. 배치 커밋을 써야 한다.")

    return _Api


def _prepareDocs(tmp_path, codes: list[str], *, zipBytes: int = 64) -> None:
    for code in codes:
        d = tmp_path / "original" / "dart" / "docs" / code
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{code}_1.zip").write_bytes(b"PK\x03\x04" + b"\x00" * zipBytes)


def _patchUploadEnv(monkeypatch, tmp_path, calls: dict) -> None:
    import huggingface_hub

    import dartlab.config as cfg
    import dartlab.core.dataConfig as dataConfig
    import dartlab.pipeline.hfUpload as hfUpload

    monkeypatch.setattr(huggingface_hub, "HfApi", _fakeHfApi(calls))
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    monkeypatch.setattr(dataConfig, "repoFor", lambda key: "test/dartOriginal")
    monkeypatch.setattr(hfUpload, "_resolveHfToken", lambda token=None: "token")
    monkeypatch.setattr(hfUpload, "_BATCH_INTERVAL_SECONDS", 0)


def test_bundle_upload_batches_commits_instead_of_per_code_calls(monkeypatch, tmp_path) -> None:
    """종목당 개별 upload_file 이 아니라 커밋을 묶어 올린다.

    2026-08-19: 변경 종목이 85 에서 2448 로 늘자 종목당 1 회 upload_file 이 HF 429 를 유발했고
    60s -> 300s -> 900s 백오프 중 job timeout(150 분)에 잘렸다.
    """
    from dartlab.pipeline.stages import dartZip

    calls: dict = {}
    codes = [f"00000{i}" for i in range(5)]
    _prepareDocs(tmp_path, codes)
    _patchUploadEnv(monkeypatch, tmp_path, calls)
    monkeypatch.setattr(dartZip, "_MAX_BATCH_TARS", 2)

    uploaded = dartZip._bundleAndUpload(codes, token=None)

    assert uploaded == 5
    assert calls.get("individual") is None, "개별 upload_file 이 호출됐다"
    assert calls["commits"] == [2, 2, 1], f"배치 경계가 어긋났다: {calls['commits']}"


def test_bundle_upload_flushes_on_byte_budget(monkeypatch, tmp_path) -> None:
    """누적 바이트 상한에서도 끊는다. tar 크기 편차로 러너 디스크가 터지지 않게 한다."""
    from dartlab.pipeline.stages import dartZip

    calls: dict = {}
    codes = [f"00000{i}" for i in range(4)]
    _prepareDocs(tmp_path, codes, zipBytes=4096)
    _patchUploadEnv(monkeypatch, tmp_path, calls)
    monkeypatch.setattr(dartZip, "_MAX_BATCH_TARS", 1000)
    monkeypatch.setattr(dartZip, "_MAX_BATCH_BYTES", 1)

    uploaded = dartZip._bundleAndUpload(codes, token=None)

    assert uploaded == 4
    assert calls["commits"] == [1, 1, 1, 1], f"바이트 상한이 무시됐다: {calls['commits']}"


def test_bundle_upload_clears_stage_after_each_batch(monkeypatch, tmp_path) -> None:
    """배치를 올린 뒤 stage tar 를 지운다. 안 지우면 전 종목 tar 가 러너 디스크에 남는다."""
    from dartlab.pipeline.stages import dartZip

    calls: dict = {}
    codes = [f"00000{i}" for i in range(3)]
    _prepareDocs(tmp_path, codes)
    _patchUploadEnv(monkeypatch, tmp_path, calls)
    monkeypatch.setattr(dartZip, "_MAX_BATCH_TARS", 2)

    dartZip._bundleAndUpload(codes, token=None)

    stage = tmp_path / "original" / "_bundleStage" / "docs"
    leftover = sorted(p.name for p in stage.glob("*.tar"))
    assert leftover == [], f"stage 에 tar 가 남았다: {leftover}"


def test_bundle_upload_skips_codes_without_zips(monkeypatch, tmp_path) -> None:
    """zip 이 없는 종목은 빈 tar 를 올리지 않는다."""
    from dartlab.pipeline.stages import dartZip

    calls: dict = {}
    _prepareDocs(tmp_path, ["000001"])
    _patchUploadEnv(monkeypatch, tmp_path, calls)

    uploaded = dartZip._bundleAndUpload(["000001", "999999"], token=None)

    assert uploaded == 1
    assert calls["commits"] == [1]
