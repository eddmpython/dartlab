"""providers/edgar/bulk/loader.py mirror smoke — P6."""

import pytest

pytestmark = pytest.mark.unit


def test_imports():
    try:
        import dartlab.providers.edgar.bulk.loader  # noqa: F401
    except ImportError as e:
        pytest.skip(f"module import requires data/env: {e}")


def test_ensure_callable() -> None:
    """ensure() callable smoke."""
    from dartlab.providers.edgar.bulk.loader import EdgarBulkLoader

    assert hasattr(EdgarBulkLoader, "ensure")


def test_register_edgar_bulk_loader_callable() -> None:
    """registerEdgarBulkLoader() callable smoke."""
    from dartlab.providers.edgar.bulk.loader import registerEdgarBulkLoader

    assert callable(registerEdgarBulkLoader)


def test_localOnlyMissingCacheDoesNotCallProvider(tmp_path, monkeypatch) -> None:
    """local_only cache 부재는 SEC 호출 없이 즉시 실패한다."""
    from dartlab.providers.edgar.bulk import loader as loaderModule

    def failIfCalled(*args, **kwargs):
        raise AssertionError("local_only provider 호출 금지")

    monkeypatch.setattr(loaderModule, "ensureFinanceParquet", failIfCalled)

    with pytest.raises(FileNotFoundError, match="로컬 EDGAR finance 없음"):
        loaderModule.EdgarBulkLoader().ensure(
            "AAPL",
            tmp_path / "AAPL.parquet",
            refresh="local_only",
        )


@pytest.mark.parametrize(
    ("policy", "expected"),
    [
        ("auto", False),
        ("force_check", True),
    ],
)
def test_refreshPolicyIsForwardedWithoutAmbiguity(
    policy,
    expected,
    tmp_path,
    monkeypatch,
) -> None:
    """공개 refresh 정책을 SEC 호출자의 bool 계약으로 한 번만 변환한다."""
    from dartlab.providers.edgar.bulk import loader as loaderModule

    captured = {}

    def capture(stockCode, path, *, refresh):
        captured.update(stockCode=stockCode, path=path, refresh=refresh)

    monkeypatch.setattr(loaderModule, "ensureFinanceParquet", capture)
    target = tmp_path / "AAPL.parquet"

    loaderModule.EdgarBulkLoader().ensure("AAPL", target, refresh=policy)

    assert captured == {
        "stockCode": "AAPL",
        "path": target,
        "refresh": expected,
    }


def test_invalidRefreshFailsBeforeProviderCall(tmp_path, monkeypatch) -> None:
    """미지원 정책은 provider 경계에 도달하기 전에 거부한다."""
    from dartlab.providers.edgar.bulk import loader as loaderModule

    def failIfCalled(*args, **kwargs):
        raise AssertionError("invalid refresh provider 호출 금지")

    monkeypatch.setattr(loaderModule, "ensureFinanceParquet", failIfCalled)

    with pytest.raises(ValueError, match="지원하지 않는 refresh 정책"):
        loaderModule.EdgarBulkLoader().ensure(
            "AAPL",
            tmp_path / "AAPL.parquet",
            refresh="force_rebuild",
        )
