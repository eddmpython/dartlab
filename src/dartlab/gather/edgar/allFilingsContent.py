"""US allFilings 본문 수집. filing_url 문서 body 를 content_raw 로 저장 (DART fillContent 대칭).

DART ``allFilingsCollector.fillContent`` 의 US 판이다. DART 는 공시 zip 안 largest 파일을 content_raw 로
담지만, SEC 는 filing 의 primary document URL 을 그대로 GET 하면 원문 body(HTML/XML)가 나온다(실측: 8-K
1건 42KB). SEC 는 DART 같은 키 한도가 없고 fair-access(~10 req/s)만 지키면 되므로, 메타(recent.parquet)의
``url`` 을 건당 GET 해 본문을 per-day content 파일(``edgar/allFilingsContent/{date}.parquet``)에 저장한다.

idempotent + diff retry (DART 동형): 기존 per-day 파일의 accessionNo, fetch_status 를 읽어 ``ok``/``no_body``
는 skip, ``error`` 만 retry, 신규만 fetch. 전 종목 2015 이후 전 공시는 4M+ 이라 한 번에 못 받는다. forward(신규
날짜) + backfill(과거 날짜)로 여러 run 에 걸쳐 점진 수집한다(DART allFilingsBackfill 동형).

content 는 메타(recent.parquet, 피드용)와 분리된 레이어다. 소비자는 공시 본문 검색/분석이다(피드는 메타만).
"""

from __future__ import annotations

import time
from collections import Counter
from pathlib import Path

import httpx
import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from dartlab.core.logger import getLogger

_log = getLogger(__name__)

# SEC fair-access: User-Agent 필수(부재 시 403), ~10 req/s 권장. 도메인은 env 미참조.
_SEC_UA = "dartlab research (contact: research@dartlab.io)"
_PACE_SECONDS = 0.12  # ~8 req/s (fair-access 10/s 안쪽 여유)
# fillContentDay 가 fetch 를 멈춘 이유. reasons Counter 에 미착수 건수로 남는다(호출측이 run 결론을 정한다).
STOP_DEADLINE = "중단:마감"
STOP_TRIP = "중단:연속오류"
_CONTENT_COLS = ("accessionNo", "stockCode", "filingDate", "content_raw", "fetch_status")
_SCHEMA = pa.schema([(name, pa.string()) for name in _CONTENT_COLS])
# 한 문서의 풀어낸 크기 상한(바이트). gzip 으로 1.3MB 인 문서가 23MB HTML 로 풀리는 날(20250513)이 있어
# 압축 크기(content-length)로는 못 가린다. 이 크기를 넘는 문서는 본문을 두지 않는다(no_body).
_MAX_BODY_BYTES = 128 * 1024 * 1024
# 본문 글자가 이만큼 쌓이거나 행이 이만큼 쌓이면 파일에 덜어 쓴다. 하루치 전체를 메모리에 두지 않으려는 값이다.
_FLUSH_CHARS = 48_000_000
_FLUSH_ROWS = 1000
# 글로 읽을 수 없는 문서 형식. PDF 등을 글로 풀면 깨진 글자만 남는다(20250513 ARS PDF 62MB).
_BINARY_TYPES = {"application/pdf", "application/zip", "application/octet-stream", "application/x-zip-compressed"}


def _contentRow(meta: dict, body: str | None, status: str) -> dict:
    """메타 한 행과 fetch 결과로 content 행을 만든다."""
    return {
        "accessionNo": str(meta["accessionNo"]),
        "stockCode": str(meta["stockCode"]),
        "filingDate": str(meta["filingDate"]),
        "content_raw": body,
        "fetch_status": status,
    }


def getFilingBody(
    url: str, *, client: httpx.Client, timeout: float = 30.0, reasons: Counter | None = None
) -> tuple[str | None, str]:
    """단일 filing primary document GET 후 (content_raw, fetch_status) 반환.

    DART ``_fetchContent`` 대칭. SEC fair-access User-Agent 로 GET. 200+비어있지않음 = ``ok``,
    200+빈 body 또는 404 = ``no_body``(final, retry 안 함), 그 외/예외 = ``error``(retry 대상).
    글이 아닌 형식(PDF·압축·그림)과 풀어낸 크기가 ``_MAX_BODY_BYTES`` 를 넘는 문서는 받지 않고 ``no_body``.

    Args:
        url: filing primary document URL (recent.parquet 의 ``url``).
        client: 재사용 ``httpx.Client`` (User-Agent 세팅된 것 권장).
        timeout: 요청 타임아웃(초).
        reasons: 주면 ``error`` 원인(HTTP 코드 또는 예외 이름)을 센다. 오류를 status 로만 남기던 탓에
            2026-10-09 run 이 85 분 동안 무엇에 막혔는지 로그로 가를 수 없었다.

    Returns:
        ``(content_raw, fetch_status)``. status 가 ``ok`` 면 content_raw 는 원문, 아니면 None.

    Raises:
        없음. HTTP/타임아웃 예외는 내부에서 ``error`` status 로 흡수.

    Example:
        >>> with httpx.Client(headers={"User-Agent": ua}) as c:
        ...     body, status = getFilingBody(url, client=c)

    Requires:
        - httpx (SEC fair-access User-Agent 필수)
    """
    if not url:
        return None, "no_body"
    try:
        with client.stream("GET", url, timeout=timeout, follow_redirects=True) as r:
            if r.status_code == 200:
                return _readBody(r)
            if r.status_code == 404:
                return None, "no_body"  # 문서 삭제/이동 (final)
            if reasons is not None:
                reasons[f"HTTP {r.status_code}"] += 1
            return None, "error"  # 403/429/5xx 등 retry 대상
    except (httpx.HTTPError, TimeoutError, ValueError) as exc:
        if reasons is not None:
            reasons[type(exc).__name__] += 1
        return None, "error"


def _readBody(r: httpx.Response) -> tuple[str | None, str]:
    """200 응답의 본문을 글로 읽는다. 글이 아닌 형식이나 상한을 넘는 문서는 받지 않고 ``no_body``."""
    mediaType = r.headers.get("content-type", "").split(";")[0].strip().lower()
    if mediaType in _BINARY_TYPES or mediaType.startswith(("image/", "audio/", "video/")):
        return None, "no_body"
    chunks: list[bytes] = []
    size = 0
    for part in r.iter_bytes():
        size += len(part)
        if size > _MAX_BODY_BYTES:
            return None, "no_body"
        chunks.append(part)
    raw = b"".join(chunks)
    del chunks
    try:
        body = raw.decode(r.encoding or "utf-8", errors="replace")
    except LookupError:
        body = raw.decode("utf-8", errors="replace")
    if body.strip():
        return body, "ok"
    return None, "no_body"


def fillContentDay(
    dayMeta: pl.DataFrame,
    outPath: Path,
    *,
    maxFetch: int | None = None,
    deadline: float | None = None,
    tripAfter: int | None = None,
    reasons: Counter | None = None,
) -> pl.DataFrame:
    """하루치 공시 메타로 본문을 fetch 해 per-day content 파일 생성 (idempotent + diff retry, atomic).

    ``dayMeta`` 는 recent.parquet 를 특정 filingDate 로 필터한 것(accessionNo·stockCode·filingDate·url).
    기존 파일의 ok/no_body 는 그대로 보존(skip), error·신규만 fetch 한다. atomic(tmp 후 rename)으로 안전.

    Args:
        dayMeta: 하루치 메타 (accessionNo·stockCode·filingDate·url 컬럼 필수).
        outPath: ``edgar/allFilingsContent/{date}.parquet``.
        maxFetch: 이번 run 에서 fetch 할 최대 건수(부분 진행). None 이면 제한 없음.
        deadline: ``time.monotonic`` 기준 마감. 지나면 남은 fetch 를 멈춘다. None 이면 마감 없음.
        tripAfter: ``error`` 가 이만큼 연달아 나면 남은 fetch 를 멈춘다(SEC 차단 추정). None 이면 끄기.
        reasons: ``getFilingBody`` 에 넘겨 ``error`` 원인을 센다. 멈췄으면 ``STOP_DEADLINE`` 또는
            ``STOP_TRIP`` 키에 미착수 건수를 더한다.

    마감이나 연속 오류로 멈추면 손대지 못한 행을 ``error``(재시도 대상)로 남긴다. 그래야 발행된 날 파일의
    ``fetch_status`` 최솟값이 ``error`` 가 되어 다음 run 의 재방문이 찾는다. 예전엔 하루치 안에 시간 제한이
    없어 2026-10-09 run 이 한 날짜에서 85 분 멈춘 채 job 상한(120 분)에 취소됐다.

    본문은 한 묶음(``_FLUSH_CHARS`` 글자 또는 ``_FLUSH_ROWS`` 행)씩 row group 으로 덜어 쓴다. 예전엔 하루치
    본문을 모두 메모리에 쌓은 뒤 DataFrame 으로 바꿔 중복 제거·정렬했다. gzip 1.3MB 가 23MB 로 풀리는 문서
    181건이 든 20250513 은 본문이 45억 글자라 이 방식이 최대 15.3GB(실측)를 써서, 16GB 러너가 5번 연속
    "The runner has received a shutdown signal" 로 끊겼다.
    행 순서는 기존 보존분 다음 신규/재시도분이며 accessionNo 로 정렬하지 않는다.

    Returns:
        pl.DataFrame. 파일에 쓴 행의 ``accessionNo``·``fetch_status`` (본문은 파일에만 있다).

    Raises:
        OSError: outPath 쓰기 실패(atomic rename 포함).

    Example:
        >>> day = recent.filter(pl.col("filingDate") == "2026-06-30")
        >>> fillContentDay(day, Path("edgar/allFilingsContent/2026-06-30.parquet"))

    SeeAlso:
        - ``.github/scripts/sync/fillEdgarAllFilingsContent.py`` (일 단위 runner)
        - ``dartlab.gather.edgar.submissions`` (메타 recent.parquet 원천)

    Requires:
        - httpx (SEC fair-access UA + pacing)
        - polars
        - pyarrow (row group 단위 쓰기)

    Capabilities:
        - DART content_raw 대칭. 공시 본문(primary doc)을 per-day parquet 로 아카이브.
        - idempotent: 기존 ok/no_body 보존, error·신규만 재시도.

    Guide:
        - "US 공시 본문 수집" 요구 시 본 함수 (runner 경유가 기본).

    When:
        - 매일 cron(edgarFilingsContentSync)에서 forward/backfill 일자별 호출.

    How:
        - 기존 파일의 상태만 읽어 ok/no_body skip, 잔여만 fetch, 묶음씩 tmp 에 쓴 뒤 rename.

    AIContext:
        internal 수집기 (runner/CI 전용). AI 직접 호출 X.
    """
    prior = _priorStatus(outPath)
    byAcc: dict[str, dict] = {}  # 같은 accessionNo 가 여럿이면 마지막 행
    for r in dayMeta.iter_rows(named=True):
        byAcc[str(r["accessionNo"])] = r
    keepAcc = {acc for acc in byAcc if prior.get(acc) in ("ok", "no_body")}  # 기존 ok/no_body 보존분
    todo = [r for acc, r in byAcc.items() if acc not in keepAcc]  # fetch 대상(신규 + error retry)
    if maxFetch is not None:
        todo = todo[:maxFetch]

    outPath.parent.mkdir(parents=True, exist_ok=True)
    tmp = outPath.with_suffix(".parquet.tmp")
    fetchedN = 0
    try:
        with pq.ParquetWriter(tmp, _SCHEMA, compression="zstd") as writer:
            sink = _RowSink(writer)
            if keepAcc:
                _copyKept(outPath, keepAcc, sink)
            stoppedAt: int | None = None
            stopReason = ""
            consecutiveErrors = 0
            if todo:
                with httpx.Client(headers={"User-Agent": _SEC_UA}) as client:
                    for i, r in enumerate(todo):
                        if deadline is not None and time.monotonic() >= deadline:
                            stoppedAt, stopReason = i, STOP_DEADLINE
                            break
                        body, status = getFilingBody(str(r.get("url") or ""), client=client, reasons=reasons)
                        sink._add(_contentRow(r, body, status))
                        fetchedN += 1
                        consecutiveErrors = consecutiveErrors + 1 if status == "error" else 0
                        if tripAfter and consecutiveErrors >= tripAfter:
                            stoppedAt, stopReason = i + 1, STOP_TRIP
                            break
                        if i + 1 < len(todo):
                            time.sleep(_PACE_SECONDS)
            if stoppedAt is not None:
                left = len(todo) - stoppedAt
                for r in todo[stoppedAt:]:
                    sink._add(_contentRow(r, None, "error"))
                fetchedN += left
                if reasons is not None:
                    reasons[stopReason] += left
                _log.warning(f"[allFilingsContent] {outPath.name}: {stopReason} {left}건 미착수(error 로 남김)")
            sink._flush(final=True)
        tmp.replace(outPath)
    except BaseException:
        tmp.unlink(missing_ok=True)
        raise
    out = pl.read_parquet(outPath, columns=["accessionNo", "fetch_status"])
    okN = out.filter(pl.col("fetch_status") == "ok").height
    _log.info(f"[allFilingsContent] {outPath.name}: {out.height}건 (ok {okN}, fetch {fetchedN})")
    return out


def _priorStatus(outPath: Path) -> dict[str, str]:
    """기존 per-day 파일의 accessionNo → fetch_status. 본문 열은 읽지 않는다. 파일이 없거나 깨졌으면 빈 dict."""
    prior: dict[str, str] = {}
    if outPath.exists():
        try:
            df = pl.read_parquet(outPath, columns=["accessionNo", "fetch_status"])
        except (OSError, pl.exceptions.PolarsError) as exc:
            _log.warning(f"[allFilingsContent] {outPath.name}: 기존 파일을 읽지 못해 처음부터 다시 받는다 ({exc})")
            return prior
        prior = {str(acc): str(status) for acc, status in df.iter_rows()}
    return prior


def _copyKept(outPath: Path, keepAcc: set[str], sink: _RowSink) -> None:
    """기존 파일에서 보존할 행(ok/no_body)만 한 묶음씩 읽어 새 파일 쓰기 대기열로 옮긴다."""
    with pq.ParquetFile(outPath) as src:
        names = [n for n in _CONTENT_COLS if n in src.schema_arrow.names]
        for batch in src.iter_batches(batch_size=100, columns=names):
            for row in batch.to_pylist():
                if str(row["accessionNo"]) in keepAcc:
                    sink._add(row)


class _RowSink:
    """행을 모았다가 글자 수나 행 수가 차면 parquet row group 으로 덜어 쓴다(하루치를 메모리에 다 두지 않는다)."""

    def __init__(self, writer: pq.ParquetWriter) -> None:
        self._writer = writer
        self._rows: list[dict] = []
        self._chars = 0
        self._groups = 0

    def _add(self, row: dict) -> None:
        """행 하나를 더하고 한도를 넘었으면 덜어 쓴다."""
        self._rows.append({name: row.get(name) for name in _CONTENT_COLS})
        self._chars += len(row.get("content_raw") or "")
        if self._chars >= _FLUSH_CHARS or len(self._rows) >= _FLUSH_ROWS:
            self._flush()

    def _flush(self, *, final: bool = False) -> None:
        """모인 행을 row group 하나로 쓴다. 마지막 호출에 행이 하나도 안 쓰였으면 빈 row group 을 쓴다."""
        if self._rows:
            self._writer.write_table(pa.Table.from_pylist(self._rows, schema=_SCHEMA))
            self._groups += 1
        elif final and self._groups == 0:
            self._writer.write_table(_SCHEMA.empty_table())
        self._rows = []
        self._chars = 0


__all__ = ["getFilingBody", "fillContentDay"]
