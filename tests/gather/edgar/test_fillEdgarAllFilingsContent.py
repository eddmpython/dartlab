"""fillEdgarAllFilingsContent.selectDays 계약. forward(최신) + backfill(과거) 미충전일 선정. 순수 함수.

스크립트라 importlib 경유. 네트워크/HF 무관.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_SCRIPT = Path(__file__).resolve().parents[3] / ".github" / "scripts" / "sync" / "fillEdgarAllFilingsContent.py"


def _module():
    spec = importlib.util.spec_from_file_location("fillEdgarAllFilingsContentForTest", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _selectDays():
    return _module().selectDays


def test_forward_newest_plus_backfill_oldest():
    """최신 forwardDays(피드 신선도) + 오래된 미충전(backfill), 합 maxDays."""
    selectDays = _selectDays()
    allDays = [f"2026010{i}" for i in range(1, 10)]  # 20260101..20260109
    done = {"20260105"}  # 하나만 충전됨
    got = selectDays(allDays, done, maxDays=4, forwardDays=2)
    # forward = 최신 미충전 2일(20260108,20260109), backfill = 오래된 미충전(20260101,20260102)
    assert got == ["20260108", "20260109", "20260101", "20260102"]


def test_empty_when_all_done():
    """전 일자 충전 완료면 빈 리스트."""
    selectDays = _selectDays()
    allDays = ["20260101", "20260102"]
    assert selectDays(allDays, {"20260101", "20260102"}, maxDays=10, forwardDays=3) == []


def test_backfill_only_when_forward_zero():
    """forwardDays=0 이면 오래된 것부터(순수 backfill)."""
    selectDays = _selectDays()
    allDays = ["20260101", "20260102", "20260103"]
    assert selectDays(allDays, set(), maxDays=2, forwardDays=0) == ["20260101", "20260102"]


# ─── 시간 예산 (2026-09-01: 매 run 이 timeout cancelled 로 끝나 감시에 실패로 보이던 것) ───


def test_fill_days_stops_starting_new_days_after_budget():
    """예산이 지나면 새 날짜를 시작하지 않는다. 시작한 날짜는 끝까지 간다."""
    fillDays = _module().fillDays
    now = [0.0]
    filled: list[str] = []

    def fillDay(day: str) -> None:
        filled.append(day)
        now[0] += 30.0  # 하루치 30 초

    done = fillDays(["d1", "d2", "d3", "d4"], fillDay, budgetSeconds=50.0, clock=lambda: now[0])
    # 0s: d1 시작(예산 안) -> 30s: d2 시작(예산 안) -> 60s: 예산 초과, d3 미착수
    assert done == ["d1", "d2"]
    assert filled == ["d1", "d2"]


def test_fill_days_finishes_all_when_budget_remains():
    """예산이 남으면 todo 를 전부 처리한다."""
    fillDays = _module().fillDays
    assert fillDays(["a", "b"], lambda day: None, budgetSeconds=60.0) == ["a", "b"]


def test_workflow_passes_budget_below_job_timeout():
    """workflow 의 예산(분) + 실측 최장 하루치가 job timeout 안에 들어야 timeout cancelled 가 사라진다."""
    import re

    workflow = (_SCRIPT.parents[2] / "workflows" / "edgarFilingsContentSync.yml").read_text(encoding="utf-8")
    timeout = int(re.search(r"timeout-minutes:\s*(\d+)", workflow).group(1))
    budget = float(re.search(r"--budget-minutes\s+(\d+)", workflow).group(1))
    longestDayMinutes = 55  # 2026-08-31 run 실측 최장 53.5 분(20251202) + 여유
    assert budget + longestDayMinutes < timeout, f"예산 {budget} + 하루치 {longestDayMinutes} >= timeout {timeout}"


# ─── HF 429 내성 (2026-09-22: resolver 한도 429 한 번에 run 이 죽고 모니터 재실행도 같은 창에서 실패) ───


class _FakeResponse:
    """HfHubHTTPError 가 요구하는 최소 응답. huggingface_hub 0.x(requests)·1.x(httpx) 양쪽에서 생성된다."""

    headers: dict[str, str] = {}
    request = None
    text = ""
    url = "https://huggingface.co/x"

    def __init__(self, status: int) -> None:
        self.status_code = status


def _hfError(status: int):
    from huggingface_hub.errors import HfHubHTTPError

    return HfHubHTTPError(f"{status} Client Error", response=_FakeResponse(status))


class _Entry:
    def __init__(self, path: str) -> None:
        self.path = path


class _FakeApi:
    """list_repo_tree 결과를 차례로 돌려준다. 값이 예외면 던진다."""

    def __init__(self, *results) -> None:
        self._results = list(results)
        self.calls = 0

    def list_repo_tree(self, *_args, **_kwargs):
        self.calls += 1
        result = self._results.pop(0)
        if isinstance(result, BaseException):
            raise result
        return iter(result)


def test_done_days_is_empty_only_when_directory_is_missing(monkeypatch):
    """404(최초 실행)만 빈 집합. 429 가 끝내 풀리지 않으면 빈 집합으로 속이지 않고 실패한다."""
    mod = _module()
    monkeypatch.setattr("dartlab.core.hfRetry.time.sleep", lambda _s: None)
    monkeypatch.setenv("DARTLAB_HF_RETRY_ATTEMPTS", "2")

    assert mod._doneDays(_FakeApi(_hfError(404))) == set()

    with pytest.raises(Exception) as caught:
        mod._doneDays(_FakeApi(_hfError(429), _hfError(429)))
    assert getattr(caught.value.response, "status_code", None) == 429

    recovered = _FakeApi(_hfError(429), [_Entry("edgar/allFilingsContent/20260101.parquet"), _Entry("x/readme.md")])
    assert mod._doneDays(recovered) == {"20260101"}
    assert recovered.calls == 2


def test_main_survives_one_429_on_metadata_download(monkeypatch, tmp_path):
    """메타 다운로드가 429 를 한 번 받아도 재시도로 넘어간다(이슈 #156 의 실패 지점)."""
    import huggingface_hub
    import polars as pl

    mod = _module()
    monkeypatch.setattr("dartlab.core.hfRetry.time.sleep", lambda _s: None)
    monkeypatch.setenv("DARTLAB_HF_RETRY_ATTEMPTS", "3")
    monkeypatch.setenv("HF_TOKEN", "test-token")
    metaPath = tmp_path / "recent.parquet"
    pl.DataFrame(
        {"accessionNo": ["a1"], "stockCode": ["AAPL"], "filingDate": ["20260101"], "url": ["https://sec.gov/x"]}
    ).write_parquet(metaPath)
    downloads: list[str] = []

    def fakeDownload(*_args, **_kwargs):
        downloads.append("call")
        if len(downloads) == 1:
            raise _hfError(429)
        return str(metaPath)

    api = _FakeApi([_Entry("edgar/allFilingsContent/20260101.parquet")])
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fakeDownload)
    monkeypatch.setattr(huggingface_hub, "HfApi", lambda token=None: api)

    assert mod.main(["--revisit-days", "0"]) == 0
    assert len(downloads) == 2


# ─── 재방문과 하루치 마감 (2026-10-09 85 분 정지 · 2026-10-12 표본 11% error 행) ───


def test_scan_slice_rotates_through_published_days():
    """날마다 다음 구간을 보고, 한 바퀴를 돌면 처음으로 돌아온다."""
    scanSlice = _module().scanSlice
    done = [f"d{i}" for i in range(5)]
    assert scanSlice(done, 2, ordinal=0) == ["d0", "d1"]
    assert scanSlice(done, 2, ordinal=1) == ["d2", "d3"]
    assert scanSlice(done, 2, ordinal=2) == ["d4", "d0"]
    assert scanSlice(done, 9, ordinal=3) == done
    assert scanSlice([], 2, ordinal=1) == []


def test_plan_work_puts_revisit_after_forward():
    """최신 미충전(피드 신선도) 다음에 재방문, 그다음 과거 backfill."""
    planWork = _module().planWork
    assert planWork(["f1", "f2", "b1"], ["r1", "f2"], forwardDays=2) == ["f1", "f2", "r1", "b1"]
    assert planWork([], ["r1"], forwardDays=3) == ["r1"]


def test_has_error_rows_reads_only_footer_minimum(tmp_path):
    """상태값은 error < no_body < ok 라 footer 최솟값만 보면 error 행이 남은 날을 가른다."""
    import polars as pl
    import pyarrow.parquet as pq

    hasErrorRows = _module().hasErrorRows
    clean = tmp_path / "clean.parquet"
    pl.DataFrame({"accessionNo": ["a", "b"], "fetch_status": ["ok", "no_body"]}).write_parquet(clean)
    dirty = tmp_path / "dirty.parquet"
    pl.DataFrame({"accessionNo": ["a", "b"], "fetch_status": ["ok", "error"]}).write_parquet(dirty)
    assert hasErrorRows(pq.ParquetFile(clean).metadata) is False
    assert hasErrorRows(pq.ParquetFile(dirty).metadata) is True


def _metaFile(tmp_path, days: list[str]):
    import polars as pl

    path = tmp_path / "recent.parquet"
    pl.DataFrame(
        {
            "accessionNo": [f"a{i}" for i in range(len(days))],
            "stockCode": ["AAPL"] * len(days),
            "filingDate": days,
            "url": [f"https://sec.gov/{i}" for i in range(len(days))],
        }
    ).write_parquet(path)
    return path


def test_main_revisits_published_day_with_error_rows(monkeypatch, tmp_path):
    """footer 에 error 가 남은 발행일은 HF 발행본을 받아 병합 base 로 두고 다시 채워 올린다."""
    import huggingface_hub
    import polars as pl

    import dartlab.config as cfg

    mod = _module()
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    metaPath = _metaFile(tmp_path, ["20260101"])
    published = tmp_path / "published.parquet"
    pl.DataFrame({"accessionNo": ["a0"], "fetch_status": ["error"]}).write_parquet(published)
    downloads: list[str] = []

    def fakeDownload(repo, filename, **kwargs):
        downloads.append(filename)
        return str(metaPath)

    class _Fs:
        def __init__(self, token=None):
            pass

        def open(self, path, mode):
            return open(published, mode)

    uploads: list[str] = []

    class _Api(_FakeApi):
        def upload_file(self, **kwargs):
            uploads.append(kwargs["path_in_repo"])

    filled: list[str] = []

    def fakeFill(dayMeta, outPath, **kwargs):
        filled.append(outPath.name)
        return pl.DataFrame({"accessionNo": ["a0"], "fetch_status": ["ok"]})

    api = _Api([_Entry("edgar/allFilingsContent/20260101.parquet")])
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", fakeDownload)
    monkeypatch.setattr(huggingface_hub, "HfFileSystem", _Fs)
    monkeypatch.setattr(huggingface_hub, "HfApi", lambda token=None: api)
    monkeypatch.setattr(mod, "fillContentDay", fakeFill)

    assert mod.main([]) == 0
    assert "edgar/allFilingsContent/20260101.parquet" in downloads
    assert filled == ["20260101.parquet"]
    assert uploads == ["edgar/allFilingsContent/20260101.parquet"]


def test_main_exits_nonzero_after_consecutive_error_trip(monkeypatch, tmp_path):
    """연속 오류로 멈춘 run 은 exit 1 로 끝나 감시가 새 러너로 재실행한다. 남은 날은 시작하지 않는다."""
    import huggingface_hub
    import polars as pl

    import dartlab.config as cfg
    from dartlab.gather.edgar.allFilingsContent import STOP_TRIP

    mod = _module()
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setattr(cfg, "dataDir", str(tmp_path))
    metaPath = _metaFile(tmp_path, ["20260101", "20260102"])

    class _Api(_FakeApi):
        def upload_file(self, **kwargs):
            pass

    filled: list[str] = []

    def fakeFill(dayMeta, outPath, *, reasons, **kwargs):
        filled.append(outPath.name)
        reasons[STOP_TRIP] += 1
        return pl.DataFrame({"accessionNo": ["a"], "fetch_status": ["error"]})

    api = _Api(_hfError(404))
    monkeypatch.setattr(huggingface_hub, "hf_hub_download", lambda *a, **k: str(metaPath))
    monkeypatch.setattr(huggingface_hub, "HfApi", lambda token=None: api)
    monkeypatch.setattr(mod, "fillContentDay", fakeFill)

    assert mod.main(["--forward-days", "2"]) == 1
    assert len(filled) == 1


def test_hard_deadline_default_leaves_upload_margin_under_job_timeout():
    """하루치 마감(기본 105 분) 뒤 마지막 업로드까지 job 상한(120 분) 안에 들어가야 취소가 없다."""
    import re

    workflow = (_SCRIPT.parents[2] / "workflows" / "edgarFilingsContentSync.yml").read_text(encoding="utf-8")
    timeout = int(re.search(r"timeout-minutes:\s*(\d+)", workflow).group(1))
    script = _SCRIPT.read_text(encoding="utf-8")
    hard = float(re.search(r'"--hard-minutes",\s*type=float,\s*default=([\d.]+)', script).group(1))
    assert hard + 10 <= timeout
