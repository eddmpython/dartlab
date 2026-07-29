"""allFilingsSync (HF push/pull/reconcile) 단위 — 네트워크 0(stub)."""

import pytest

pytestmark = pytest.mark.unit


def test_imports() -> None:
    try:
        import dartlab.gather.dart.allFilingsSync  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_push_all_filings_callable() -> None:
    """pushAllFilings() callable smoke."""
    from dartlab.gather.dart.allFilingsSync import pushAllFilings

    assert callable(pushAllFilings)


def test_reconcile_callable() -> None:
    """reconcileAllFilings() / _remoteDates() / _pullDates() callable smoke."""
    from dartlab.gather.dart.allFilingsSync import _pullDates, _remoteDates, reconcileAllFilings

    assert callable(reconcileAllFilings)
    assert callable(_remoteDates)
    assert callable(_pullDates)


def test_remote_dates_parses_and_excludes_meta(monkeypatch) -> None:
    """_remoteDates 가 본문 {YYYYMMDD}.parquet 만 추출 — _meta·비parquet 제외, 외부 호출 stub."""
    from dartlab.gather.dart import allFilingsSync as mod

    class _Item:
        def __init__(self, path):
            self.path = path

    class _StubApi:
        def __init__(self, *a, **k):
            pass

        def list_repo_tree(self, *a, **k):
            return [
                _Item("dart/allFilings/20260601.parquet"),
                _Item("dart/allFilings/20260602.parquet"),
                _Item("dart/allFilings/20260603_meta.parquet"),  # 목록만 — 제외
                _Item("dart/allFilings/README.md"),  # 비parquet — 제외
            ]

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _StubApi)
    monkeypatch.delenv("HF_TOKEN", raising=False)
    assert mod._remoteDates() == {"20260601", "20260602"}


def test_remote_dates_failure_is_typed_and_preserves_cause(monkeypatch) -> None:
    """HF 목록 실패를 원격 정상 0건으로 위장하지 않는다."""
    from dartlab.gather.dart import allFilingsSync as mod
    from dartlab.gather.dart.allFilingsCollector import AllFilingsHfListingError

    class _BoomApi:
        def __init__(self, *a, **k):
            pass

        def list_repo_tree(self, *a, **k):
            raise RuntimeError("network down")

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _BoomApi)
    monkeypatch.delenv("HF_TOKEN", raising=False)

    with pytest.raises(AllFilingsHfListingError, match="목록 조회") as excInfo:
        mod._remoteDates()

    assert isinstance(excInfo.value.__cause__, RuntimeError)


def test_remote_dates_normal_empty_repository_returns_empty_set(monkeypatch) -> None:
    """정상적으로 비어 있는 원격 경로만 빈 set을 반환한다."""
    from dartlab.gather.dart import allFilingsSync as mod

    class _EmptyApi:
        def __init__(self, *a, **k):
            pass

        def list_repo_tree(self, *a, **k):
            return []

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _EmptyApi)

    assert mod._remoteDates() == set()


def test_remote_dates_missing_remote_path_returns_empty_set(monkeypatch) -> None:
    """dataset은 있으나 allFilings 경로가 아직 없는 404는 정상 0건이다."""
    from dartlab.gather.dart import allFilingsSync as mod

    class _MissingPathApi:
        def __init__(self, *a, **k):
            pass

        def list_repo_tree(self, *a, **k):
            from huggingface_hub.errors import EntryNotFoundError

            raise EntryNotFoundError("path missing")

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _MissingPathApi)

    assert mod._remoteDates() == set()


def test_reconcile_set_difference(monkeypatch) -> None:
    """양방향 reconcile — HF가 앞선 일자 pull, 로컬이 앞선 일자 push (집합 차분)."""
    from dartlab.gather.dart import allFilingsSync as mod

    monkeypatch.setattr(mod, "collectedDates", lambda: ["20260601", "20260602"])
    monkeypatch.setattr(mod, "_remoteDates", lambda **kw: {"20260602", "20260603"})

    calls: dict[str, list | None] = {"pull": None, "push": None}

    def stubPull(dates, **kw):
        calls["pull"] = list(dates)
        return len(dates)

    def stubPush(periods=None, **kw):
        calls["push"] = list(periods)
        return len(periods)

    monkeypatch.setattr(mod, "_pullDates", stubPull)
    monkeypatch.setattr(mod, "pushAllFilings", stubPush)

    out = mod.reconcileAllFilings()
    assert out["pullDates"] == ["20260603"]  # HF 가 앞섬 → 로컬로
    assert out["pushDates"] == ["20260601"]  # 로컬이 앞섬 → HF 로
    assert out["pulled"] == 1
    assert out["pushed"] == 1
    assert out["inSync"] is False
    assert calls["pull"] == ["20260603"]
    assert calls["push"] == ["20260601"]


def test_reconcile_push_disabled(monkeypatch) -> None:
    """upload=False 미러: push 끄면 pushDates 비고 pushAllFilings 미호출 — pull 만."""
    from dartlab.gather.dart import allFilingsSync as mod

    monkeypatch.setattr(mod, "collectedDates", lambda: ["20260601", "20260602"])
    monkeypatch.setattr(mod, "_remoteDates", lambda **kw: {"20260603"})

    pushed = {"called": False}

    def stubPush(periods=None, **kw):
        pushed["called"] = True
        return len(periods)

    monkeypatch.setattr(mod, "_pullDates", lambda dates, **kw: len(dates))
    monkeypatch.setattr(mod, "pushAllFilings", stubPush)

    out = mod.reconcileAllFilings(push=False)
    assert out["pushDates"] == []
    assert out["pushed"] == 0
    assert pushed["called"] is False
    assert out["pullDates"] == ["20260603"]


def test_reconcile_in_sync(monkeypatch) -> None:
    """로컬·HF 동일하면 처리 0 + inSync=True — 부작용 없음(idempotent)."""
    from dartlab.gather.dart import allFilingsSync as mod

    monkeypatch.setattr(mod, "collectedDates", lambda: ["20260601", "20260602"])
    monkeypatch.setattr(mod, "_remoteDates", lambda **kw: {"20260601", "20260602"})

    def stubPush(periods=None, **kw):
        raise AssertionError("pushAllFilings 호출됨 — in-sync 인데 push 시도")

    monkeypatch.setattr(mod, "_pullDates", lambda dates, **kw: len(dates))
    monkeypatch.setattr(mod, "pushAllFilings", stubPush)

    out = mod.reconcileAllFilings()
    assert out["pullDates"] == []
    assert out["pushDates"] == []
    assert out["inSync"] is True


def test_push_all_filings_no_token(monkeypatch, tmp_path) -> None:
    """업로드 대상 자체가 없으면 token 없이도 정상 0건이다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsSync as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    n = mod.pushAllFilings()
    assert n == 0


def test_push_all_filings_target_without_token_is_explicit_unavailable(monkeypatch, tmp_path) -> None:
    """업로드 대상이 있는데 token이 없으면 정상 0건으로 위장하지 않는다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsSync as mod
    from dartlab.gather.dart.allFilingsCollector import AllFilingsHfUnavailableError

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    monkeypatch.delenv("HF_TOKEN", raising=False)
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"PK")

    with pytest.raises(AllFilingsHfUnavailableError, match="HF_TOKEN"):
        mod.pushAllFilings()


def test_push_all_filings_failure_reports_partial_progress(monkeypatch, tmp_path) -> None:
    """commit 실패가 성공 파일 수 반환으로 삼켜지지 않는다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsSync as mod
    from dartlab.gather.dart.allFilingsCollector import AllFilingsHfUploadError

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"PK")

    class _FailingApi:
        def __init__(self, *a, **k):
            pass

        def create_commit(self, **_kwargs):
            raise OSError("upload disconnected")

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _FailingApi)

    with pytest.raises(AllFilingsHfUploadError, match="배치") as excInfo:
        mod.pushAllFilings(token="x")

    assert excInfo.value.uploadedFiles == 0
    assert excInfo.value.totalFiles == 1
    assert isinstance(excInfo.value.__cause__, OSError)


def test_pull_dates_missing_artifact_is_download_error(monkeypatch, tmp_path) -> None:
    """snapshot 성공 반환 후 요청 파일이 없으면 성공 0건이 아니다."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsSync as mod
    from dartlab.gather.dart.allFilingsCollector import AllFilingsHfDownloadError

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "snapshot_download", lambda **_kwargs: str(tmp_path))

    with pytest.raises(AllFilingsHfDownloadError, match="누락"):
        mod._pullDates(["20260527"])


def test_push_all_filings_single_commit_batch(monkeypatch, tmp_path) -> None:
    """pushAllFilings 는 파일당 commit 아닌 create_commit 단일 배치 — 128 commit/hr 한도 회피."""
    import dartlab.config as _cfg
    from dartlab.gather.dart import allFilingsSync as mod

    monkeypatch.setattr(_cfg, "dataDir", str(tmp_path))
    outDir = mod._allFilingsDir()
    (outDir / "20260527.parquet").write_bytes(b"PK")
    (outDir / "20260528.parquet").write_bytes(b"PK")

    commits: list[dict] = []

    class _FakeApi:
        def __init__(self, *a, **k):
            pass

        def create_commit(self, *, repo_id, repo_type, operations, commit_message):  # noqa: N802
            commits.append({"ops": list(operations), "msg": commit_message})

    import huggingface_hub

    monkeypatch.setattr(huggingface_hub, "HfApi", _FakeApi)

    n = mod.pushAllFilings(["20260527", "20260528"], token="x")
    assert n == 2
    assert len(commits) == 1  # 2 파일 → 단일 commit (파일당 아님)
    ops = commits[0]["ops"]
    assert sorted(op.path_in_repo for op in ops) == [
        "dart/allFilings/20260527.parquet",
        "dart/allFilings/20260528.parquet",
    ]
