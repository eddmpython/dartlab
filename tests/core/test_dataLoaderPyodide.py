"""pyodide 데이터 로더 순수 함수 계약.

브라우저(pyodide)에서만 도는 fetch tier 를 데스크톱에서 검증할 수 있는 부분만 고정한다.
동기 XHR 은 arraybuffer 를 못 받아 ``x-user-defined`` 텍스트로 받고 하위 8비트를 되돌린다.
그 복원이 **무손실**이어야 parquet 이 깨지지 않는다(옛 파이썬 루프 → numpy 벡터로 바꾼 뒤에도 불변).
"""

from __future__ import annotations

import random
import sys
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from dartlab.core.dataLoaderPyodide import (
    PyodideParquetError,
    _decodeUserDefined,
    _fetchBytesPyodide,
)

pytestmark = [pytest.mark.unit]


def _asUserDefinedText(raw: bytes) -> str:
    """브라우저가 ``charset=x-user-defined`` 로 넘겨주는 문자열 재현 (0x80+ 는 U+F780~U+F7FF)."""
    return "".join(chr(b) if b < 0x80 else chr(0xF700 + b) for b in raw)


def _parquetBytes(data: dict) -> bytes:
    """테스트용 parquet payload를 메모리에서 만든다."""
    sink = BytesIO()
    pq.write_table(pa.table(data), sink)
    return sink.getvalue()


def test_decodeUserDefined_roundTrip_allByteValues() -> None:
    """0~255 전 바이트가 무손실 복원된다 (경계값 0x00·0x7F·0x80·0xFF 포함)."""
    raw = bytes(range(256))
    assert _decodeUserDefined(_asUserDefinedText(raw)) == raw


def test_decodeUserDefined_roundTrip_randomPayload() -> None:
    """임의 바이너리도 그대로 복원된다 (parquet 처럼 고바이트가 섞인 payload)."""
    rng = random.Random(20260709)
    raw = bytes(rng.randrange(256) for _ in range(8192))
    assert _decodeUserDefined(_asUserDefinedText(raw)) == raw


def test_decodeUserDefined_empty() -> None:
    """빈 응답은 빈 바이트."""
    assert _decodeUserDefined("") == b""


def test_decodeUserDefined_matchesLegacyLoop() -> None:
    """numpy 벡터 경로가 옛 파이썬 루프와 byte-identical (폴백 경로와 결과 일치)."""
    rng = random.Random(7)
    raw = bytes(rng.randrange(256) for _ in range(4096))
    text = _asUserDefinedText(raw)
    legacy = bytes(ord(c) & 0xFF for c in text)
    assert _decodeUserDefined(text) == legacy


def test_decodeUserDefined_doesNotRetryAfterMemoryError(monkeypatch) -> None:
    """벡터 복원이 OOM이면 더 큰 파이썬 객체 루프로 재시도하지 않는다."""

    def outOfMemory(*_args, **_kwargs):
        raise MemoryError("heap exhausted")

    fakeNumpy = SimpleNamespace(frombuffer=outOfMemory, uint8=object())
    monkeypatch.setitem(sys.modules, "numpy", fakeNumpy)

    with pytest.raises(MemoryError, match="heap exhausted"):
        _decodeUserDefined("payload")


def test_fetchBytes_reportsEveryTierReason() -> None:
    """모든 tier 가 실패하면 tier 별 사유가 예외 메시지에 남는다.

    예전에는 tier 마다 `except Exception: pass` 로 사유를 버리고 마지막에 "fetch 실패"
    한 줄만 던졌다. 브라우저는 붙어서 디버깅하기 어려운 자리라, CORS 인지 404 인지
    JSPI 미지원인지 구분할 단서가 그 사유뿐이다.

    데스크톱에서는 pyodide·js module 이 없어 전 tier 가 ImportError 로 떨어지므로,
    사유가 실려 오는지를 여기서 그대로 검증할 수 있다.
    """
    url = "https://example.invalid/none.parquet"
    with pytest.raises(RuntimeError) as caught:
        _fetchBytesPyodide(url, allowOpenUrl=True)

    message = str(caught.value)
    assert url in message, "실패한 URL 이 메시지에 없다"
    for tier in ("pyfetch", "XHR", "open_url"):
        assert tier in message, f"tier {tier} 사유가 메시지에 없다"


def test_fetchBytes_openUrlTierIsOptional() -> None:
    """`allowOpenUrl` 이 꺼져 있으면 그 tier 를 아예 시도하지 않는다.

    `open_url` 은 HTTP status 를 안 봐서 404 본문을 성공처럼 돌려준다. parquet magic 으로
    걸러내는 호출부에서만 켜야 하고, 그렇지 않은 곳(corpList)에서는 켜지면 안 된다.
    """
    with pytest.raises(RuntimeError) as caught:
        _fetchBytesPyodide("https://example.invalid/none.parquet")

    assert "open_url" not in str(caught.value)


def test_fetchToFs_rejectsMagicOnlyTruncationWithoutReplacingCache(tmp_path: Path, monkeypatch) -> None:
    """head/tail magic만 닮은 손상 payload는 기존 정상 cache를 덮지 않는다."""
    from dartlab.core import dataLoaderPyodide

    dest = tmp_path / "sample.parquet"
    original = _parquetBytes({"year": [2024], "value": [1]})
    dest.write_bytes(original)
    truncated = b"PAR1" + b"not-a-real-parquet" + b"PAR1"
    monkeypatch.setattr(dataLoaderPyodide, "_fetchBytesPyodide", lambda *_args, **_kwargs: truncated)

    with pytest.raises(PyodideParquetError, match="다운로드 저장 검증"):
        dataLoaderPyodide.pyodideFetchToFS("sample", "panel", "dart/panel", dest)

    assert dest.read_bytes() == original
    assert not list(dest.parent.glob(f".{dest.name}.*.tmp"))


def test_fetchToFs_validatesThenAtomicallyStores(tmp_path: Path, monkeypatch) -> None:
    """정상 parquet만 최종 경로에 저장하고 임시 파일을 남기지 않는다."""
    from dartlab.core import dataLoaderPyodide

    dest = tmp_path / "sample.parquet"
    payload = _parquetBytes({"year": [2023, 2024], "value": [1, 2]})
    monkeypatch.setattr(dataLoaderPyodide, "_fetchBytesPyodide", lambda *_args, **_kwargs: payload)

    dataLoaderPyodide.pyodideFetchToFS("sample", "panel", "dart/panel", dest)

    assert pq.read_table(dest).to_pydict() == {"year": [2023, 2024], "value": [1, 2]}
    assert not list(dest.parent.glob(f".{dest.name}.*.tmp"))


def test_readParquetSafe_streamsPathAndProjectsColumns(tmp_path: Path, monkeypatch) -> None:
    """공용 Pyodide reader가 path.read_bytes 없이 요청 열만 읽는다."""
    from dartlab.core import dataLoader

    path = tmp_path / "wide.parquet"
    pl.DataFrame({"year": [2023, 2024], "wide": ["x" * 1000, "y" * 1000]}).write_parquet(path)
    monkeypatch.setattr(dataLoader, "_IS_PYODIDE", True)

    def fullReadForbidden(_self):
        raise AssertionError("path.read_bytes 전체 복사 금지")

    monkeypatch.setattr(Path, "read_bytes", fullReadForbidden)
    result = dataLoader.readParquetSafe(path, columns=["year"])

    assert result.to_dict(as_series=False) == {"year": [2023, 2024]}


def test_readParquetSafe_doesNotReclassifyArrowCapacityAsCorruption(monkeypatch) -> None:
    """비손상 Arrow 오류를 OSError 계열 손상 오류로 바꾸지 않는다."""
    from dartlab.core import dataLoader, dataLoaderPyodide

    monkeypatch.setattr(dataLoader, "_IS_PYODIDE", True)

    def capacityFailure(*_args, **_kwargs):
        raise pa.ArrowCapacityError("offset capacity exceeded")

    monkeypatch.setattr(dataLoaderPyodide, "readParquetFrame", capacityFailure)

    with pytest.raises(pa.ArrowCapacityError, match="offset capacity exceeded"):
        dataLoader.readParquetSafe("sample.parquet")


def test_loadDataPyodide_pushesProjectionAndHonorsFilters(tmp_path: Path, monkeypatch) -> None:
    """반환열과 필터 보조열만 읽고 sinceYear·predicate를 모두 적용한다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    pl.DataFrame(
        {
            "year": [2023, 2024, 2024],
            "sj_div": ["BS", "IS", "BS"],
            "wide": ["x" * 1000, "y" * 1000, "z" * 1000],
        }
    ).write_parquet(path)
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    realOpen = dataLoaderPyodide.openParquetFile
    readColumns: list[list[str] | None] = []

    @contextmanager
    def spyOpen(source):
        with realOpen(source) as parquet:

            class SpyParquet:
                schema_arrow = parquet.schema_arrow
                metadata = parquet.metadata

                @staticmethod
                def read(*, columns=None):
                    readColumns.append(columns)
                    return parquet.read(columns=columns)

            yield SpyParquet()

    monkeypatch.setattr(dataLoaderPyodide, "openParquetFile", spyOpen)
    result = dataLoaderPyodide.loadDataPyodide(
        "005930",
        "finance",
        sinceYear=2024,
        columns=["year"],
        predicate=pl.col("sj_div") == "BS",
    )

    assert readColumns == [["year", "sj_div"]]
    assert result.to_dict(as_series=False) == {"year": [2024]}


def test_loadDataPyodide_repairsCorruptCacheExactlyOnce(tmp_path: Path, monkeypatch) -> None:
    """손상된 기존 cache는 정상 payload로 한 번만 재조달한다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(b"PAR1brokenPAR1")
    payload = _parquetBytes({"year": [2024], "value": [7]})
    fetchCalls = 0

    def repair(_stockCode, _category, _dirPath, target):
        nonlocal fetchCalls
        fetchCalls += 1
        target.write_bytes(payload)

    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", repair)

    result = dataLoaderPyodide.loadDataPyodide("005930", "finance")

    assert fetchCalls == 1
    assert result.to_dict(as_series=False) == {"year": [2024], "value": [7]}


def test_loadDataPyodide_doesNotLoopAfterInvalidFreshFetch(tmp_path: Path, monkeypatch) -> None:
    """최초 다운로드가 손상이면 같은 호출 안에서 무한 재요청하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    fetchCalls = 0

    def brokenFetch(_stockCode, _category, _dirPath, target):
        nonlocal fetchCalls
        fetchCalls += 1
        target.write_bytes(b"PAR1brokenPAR1")

    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", brokenFetch)

    with pytest.raises(PyodideParquetError, match="읽기"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance")

    assert fetchCalls == 1
    assert not path.exists()


def test_loadDataPyodide_removesCorruptCacheWhenRepairFetchFails(tmp_path: Path, monkeypatch) -> None:
    """손상 cache 재조달이 실패해도 같은 손상 파일을 다음 호출에 남기지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(b"PAR1brokenPAR1")
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def failedFetch(*_args, **_kwargs):
        raise RuntimeError("network unavailable")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", failedFetch)

    with pytest.raises(PyodideParquetError, match="손상 cache 재조달"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance")

    assert not path.exists()


def test_loadDataPyodide_neverTreatsArrowOomAsCorruption(tmp_path: Path, monkeypatch) -> None:
    """Arrow OOM은 cache 삭제나 네트워크 재조달 없이 그대로 전파한다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(_parquetBytes({"year": [2024]}))
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def outOfMemory(*_args, **_kwargs):
        raise pa.ArrowMemoryError("wasm heap exhausted")

    monkeypatch.setattr(dataLoaderPyodide, "_readDataFrame", outOfMemory)

    def fetchForbidden(*_args, **_kwargs):
        raise AssertionError("OOM 뒤 fetch 금지")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetchForbidden)

    with pytest.raises(MemoryError, match="wasm heap exhausted"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance")

    assert path.exists()


def test_loadDataPyodide_doesNotRefetchOtherArrowFailures(tmp_path: Path, monkeypatch) -> None:
    """용량·미지원 같은 비손상 Arrow 오류는 cache 삭제나 재조달 대상으로 오인하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(_parquetBytes({"year": [2024]}))
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def capacityFailure(*_args, **_kwargs):
        raise pa.ArrowCapacityError("offset capacity exceeded")

    monkeypatch.setattr(dataLoaderPyodide, "_readDataFrame", capacityFailure)

    def fetchForbidden(*_args, **_kwargs):
        raise AssertionError("비손상 Arrow 오류 뒤 fetch 금지")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetchForbidden)

    with pytest.raises(PyodideParquetError, match="offset capacity exceeded"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance")

    assert path.exists()


def test_loadDataPyodide_localOnlyNeverFetchesMissingFile(tmp_path: Path, monkeypatch) -> None:
    """local_only는 cache 부재를 네트워크로 조용히 우회하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "missing.parquet"
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def fetchForbidden(*_args, **_kwargs):
        raise AssertionError("local_only fetch 금지")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetchForbidden)

    with pytest.raises(FileNotFoundError, match="로컬 parquet 없음"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance", refresh="local_only")


def test_arrowToPolarsDirectConversion() -> None:
    """공개 Arrow 변환 helper가 pyarrow table을 동일한 Polars 값으로 보존한다."""
    import pyarrow as pa

    from dartlab.core.dataLoaderPyodide import arrowToPolars

    result = arrowToPolars(pa.table({"year": [2024], "value": [7]}))

    assert result.to_dict(as_series=False) == {"year": [2024], "value": [7]}


def test_loadDataPyodide_rejectsEscapingShardBeforePath(monkeypatch) -> None:
    """Pyodide 직접 진입도 상위 경로 shard를 FS path로 해석하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    def pathForbidden(*_args, **_kwargs):
        raise AssertionError("invalid shard의 data path 생성 금지")

    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", pathForbidden)

    with pytest.raises(ValueError, match="stockCode"):
        dataLoaderPyodide.loadDataPyodide("../outside", "finance", refresh="local_only")


def test_loadDataPyodide_missingProjectionFailsExplicitly(tmp_path: Path, monkeypatch) -> None:
    """요청 열 전부 부재를 full parquet read로 조용히 강등하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(_parquetBytes({"year": [2024], "value": [1]}))
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    with pytest.raises(ValueError, match="요청 열"):
        dataLoaderPyodide.loadDataPyodide(
            "005930",
            "finance",
            refresh="local_only",
            columns=["missing"],
        )


def test_loadDataPyodide_rejectsNativeOnlyForceRebuild() -> None:
    """SEC API rebuild가 없는 Pyodide에서 force_rebuild를 auto로 강등하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    with pytest.raises(ValueError, match="refresh"):
        dataLoaderPyodide.loadDataPyodide("AAPL", "edgarDocs", refresh="force_rebuild")


def test_loadDataPyodide_localOnlyRemovesKnownCorruption(tmp_path: Path, monkeypatch) -> None:
    """local_only도 네트워크만 금지할 뿐 손상 판정 cache를 고정하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(b"PAR1brokenPAR1")
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def fetchForbidden(*_args, **_kwargs):
        raise AssertionError("local_only fetch 금지")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetchForbidden)

    with pytest.raises(PyodideParquetError, match="읽기"):
        dataLoaderPyodide.loadDataPyodide("005930", "finance", refresh="local_only")

    assert not path.exists()


def test_noRefreshStillAllowsInitialDownload(tmp_path: Path, monkeypatch) -> None:
    """DARTLAB_NO_REFRESH는 cache 갱신만 막고 최초 다운로드는 허용한다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    payload = _parquetBytes({"year": [2024], "value": [3]})
    fetchCalls = 0

    def fetch(_stockCode, _category, _dirPath, target):
        nonlocal fetchCalls
        fetchCalls += 1
        target.write_bytes(payload)

    monkeypatch.setenv("DARTLAB_NO_REFRESH", "1")
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetch)

    result = dataLoaderPyodide.loadDataPyodide("005930", "finance", refresh="force_check")

    assert fetchCalls == 1
    assert result["value"].to_list() == [3]


def test_noRefreshSkipsForceCheckForExistingCache(tmp_path: Path, monkeypatch) -> None:
    """DARTLAB_NO_REFRESH가 켜진 기존 cache는 force_check도 네트워크를 열지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "finance.parquet"
    path.write_bytes(_parquetBytes({"year": [2024], "value": [5]}))
    monkeypatch.setenv("DARTLAB_NO_REFRESH", "1")
    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)

    def fetchForbidden(*_args, **_kwargs):
        raise AssertionError("NO_REFRESH force fetch 금지")

    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", fetchForbidden)
    result = dataLoaderPyodide.loadDataPyodide("005930", "finance", refresh="force_check")

    assert result["value"].to_list() == [5]


def test_projectionFallsBackToFullReadForRootlessPredicate() -> None:
    """root 열을 확정할 수 없는 selector predicate에서는 제한 projection을 하지 않는다."""
    from dartlab.core.dataLoaderPyodide import _projectedColumns

    projected = _projectedColumns(
        ["year", "value"],
        category="finance",
        sinceYear=None,
        asOf=None,
        columns=["year"],
        predicate=pl.all().is_not_null(),
    )

    assert projected is None


def test_loadDataPyodide_asOfRefreshesStaleEdgarSnapshot(tmp_path: Path, monkeypatch) -> None:
    """EDGAR snapshot이 asOf보다 오래되면 한 번 재조달하고 신선도를 다시 확인한다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "docs.parquet"
    path.write_bytes(
        _parquetBytes(
            {
                "accession_no": ["old"],
                "filing_date": ["2023-01-01"],
            }
        )
    )
    refreshed = _parquetBytes(
        {
            "accession_no": ["new"],
            "filing_date": ["2025-01-01"],
        }
    )
    fetchCalls = 0

    def refresh(_stockCode, _category, _dirPath, target):
        nonlocal fetchCalls
        fetchCalls += 1
        target.write_bytes(refreshed)

    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", refresh)

    result = dataLoaderPyodide.loadDataPyodide(
        "AAPL",
        "edgarDocs",
        asOf="2024-01-01",
        columns=["accession_no"],
    )

    assert fetchCalls == 1
    assert result["accession_no"].to_list() == ["new"]


def test_loadDataPyodide_removesCorruptAsOfReplacement(tmp_path: Path, monkeypatch) -> None:
    """asOf 재조달 결과가 손상이면 최종 cache에 고정하지 않는다."""
    from dartlab.core import dataLoaderPyodide

    path = tmp_path / "docs.parquet"
    path.write_bytes(
        _parquetBytes(
            {
                "accession_no": ["old"],
                "filing_date": ["2023-01-01"],
            }
        )
    )

    def corruptRefresh(_stockCode, _category, _dirPath, target):
        target.write_bytes(b"PAR1brokenPAR1")

    monkeypatch.setattr(dataLoaderPyodide, "_dataPath", lambda *_args: path)
    monkeypatch.setattr(dataLoaderPyodide, "pyodideFetchToFS", corruptRefresh)

    with pytest.raises(PyodideParquetError, match="asOf 재조달 후 읽기"):
        dataLoaderPyodide.loadDataPyodide("AAPL", "edgarDocs", asOf="2024-01-01")

    assert not path.exists()


def test_loadCorpListPyodide_usesArrowReader(monkeypatch) -> None:
    """회사 목록도 비활성인 Polars WASM parquet reader 대신 공용 Arrow 경로를 쓴다."""
    from dartlab.core import dataLoaderPyodide

    payload = _parquetBytes({"회사명": ["삼성전자"], "종목코드": ["005930"]})
    monkeypatch.setattr(dataLoaderPyodide, "_fetchBytesPyodide", lambda *_args, **_kwargs: payload)

    def polarsReaderForbidden(*_args, **_kwargs):
        raise AssertionError("pl.read_parquet 사용 금지")

    monkeypatch.setattr(dataLoaderPyodide.pl, "read_parquet", polarsReaderForbidden)
    result = dataLoaderPyodide.loadCorpListPyodide()

    assert result.to_dict(as_series=False) == {"회사명": ["삼성전자"], "종목코드": ["005930"]}


def test_publicLoadData_forwardsPyodideOptionsAndEdgarDefault(monkeypatch) -> None:
    """공개 loadData가 Pyodide 분기에서 옵션을 버리지 않고 EDGAR 기본 연도를 맞춘다."""
    from dartlab.core import dataLoader

    captured = {}

    def fakeLoad(stockCode, category, **kwargs):
        captured.update(stockCode=stockCode, category=category, **kwargs)
        return pl.DataFrame({"ok": [True]})

    predicate = pl.col("form_type") == "10-K"
    monkeypatch.setattr(dataLoader, "_IS_PYODIDE", True)
    monkeypatch.setattr(dataLoader, "_loadDataPyodide", fakeLoad)

    result = dataLoader.loadData(
        "AAPL",
        "edgarDocs",
        asOf="2025-01-01",
        refresh="local_only",
        columns=["form_type"],
        predicate=predicate,
    )

    assert result["ok"].to_list() == [True]
    assert captured == {
        "stockCode": "AAPL",
        "category": "edgarDocs",
        "sinceYear": 2009,
        "asOf": "2025-01-01",
        "refresh": "local_only",
        "columns": ["form_type"],
        "predicate": predicate,
    }
