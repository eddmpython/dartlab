"""증권사 리서치 메타 로컬 parquet I/O. pub_date 월별 파티션과 report_id dedup.

수집 메타를 ``data/research/brokerage/{YYYYMM}.parquet`` 로 병합 기록(report_id 중복 제거)하고,
변경된 월 파일의 상대경로를 돌려준다. sync 가 그걸 changed manifest 로 써서 증분 HF 업로드한다.
별도빌드 금지: 파티션/병합 로직은 본 source 가 소유(sync 는 호출만).

수집은 게시판 첫 페이지뿐이라 한 run 이 그 달의 일부만 본다. CI 러너에는 월 파일이 없으므로 병합 전에
HF 의 같은 달 파일을 받아 둬야 한다(``seedMonthsFromHf``). 예전엔 받지 않아 매 run 이 그 달 파일을 첫
페이지 행만으로 덮어써, 2026-10-12 HF 에 8 월 7 행, 9 월 17 행만 남아 있었다.
"""

from __future__ import annotations

import os
from pathlib import Path

import polars as pl

from dartlab.core.dataConfig import DATA_RELEASES
from dartlab.core.logger import getLogger

from .schema import _COLUMNS

_CATEGORY = "brokerageReports"
_log = getLogger(__name__)


def _dataRoot() -> Path:
    """``{DARTLAB_DATA_DIR|data}``. hfUpload 와 동일 base."""
    return Path(os.environ.get("DARTLAB_DATA_DIR") or "data")


def _dataDir() -> Path:
    """``{DARTLAB_DATA_DIR|data}/research/brokerage`` 디렉터리(없으면 생성)."""
    d = _dataRoot() / DATA_RELEASES[_CATEGORY]["dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _months(df: pl.DataFrame) -> list[str]:
    """pub_date(YYYY-MM-DD) 가 있는 행의 YYYYMM 목록(정렬, 중복 없음)."""
    if df.is_empty() or "pub_date" not in df.columns:
        return []
    values = df.filter(pl.col("pub_date").str.len_chars() >= 7)["pub_date"].to_list()
    return sorted({str(value).replace("-", "")[:6] for value in values} - {""})


def seedMonthsFromHf(df: pl.DataFrame, *, token: str | None = None) -> list[str]:
    """수집 행이 걸친 달의 월 parquet 이 로컬에 없으면 HF 에서 받아 둔다(병합 base).

    Capabilities:
        - 수집 df 의 pub_date 월마다 ``{relDir}/{YYYYMM}.parquet`` 을 HF 에서 받아 로컬 경로에 둔다.
        - 로컬에 이미 있으면 건드리지 않는다(로컬 누적 이력 보존).
        - HF 에 없는 달(새 달, 404)은 건너뛴다. 그 밖의 실패는 그대로 올려, 병합 base 없이 HF 파일을
          덮어쓰는 일을 막는다.

    AIContext:
        - CI 러너는 빈 디스크라 seed 없이 ``writeMonthly`` 를 부르면 그 달 HF 파일을 이번 수집분으로 덮어쓴다.

    Guide:
        sync 가 ``writeMonthly`` 직전에 호출한다.

    When:
        매 sync run, 병합 기록 전.

    How:
        ``_months(df)`` → 로컬 부재 달만 ``retryHfCall(hf_hub_download, local_dir=data root)``.

    Args:
        df: 이번 run 의 수집 메타 DataFrame.
        token: HF 토큰. None 이면 huggingface_hub 기본 해석(env).

    Returns:
        list[str]: HF 에서 받아 둔 월 파일 이름(예: ``["202610.parquet"]``).

    Requires:
        huggingface_hub + 네트워크.

    Raises:
        HfHubHTTPError 등: 404 가 아닌 HF 실패(재시도 소진 포함). 호출측이 run 을 실패시켜 덮어쓰기를 막는다.

    Example::

        from dartlab.gather.sources.brokerage.io import seedMonthsFromHf, writeMonthly
        seedMonthsFromHf(df)
        changed = writeMonthly(df)

    See Also:
        writeMonthly : 받아 둔 월 파일에 이번 수집분을 병합한다.
    """
    from huggingface_hub import hf_hub_download
    from huggingface_hub.utils import EntryNotFoundError

    from dartlab.core.dataConfig import repoFor
    from dartlab.core.hfRetry import retryHfCall

    base = _dataDir()
    relDir = DATA_RELEASES[_CATEGORY]["dir"]
    seeded: list[str] = []
    for ym in _months(df):
        if (base / f"{ym}.parquet").exists():
            continue
        try:
            retryHfCall(
                hf_hub_download,
                repo_id=repoFor(_CATEGORY),
                repo_type="dataset",
                filename=f"{relDir}/{ym}.parquet",
                local_dir=str(_dataRoot()),
                token=token,
            )
        except EntryNotFoundError:
            # HF 에 아직 없는 새 달(404)이라 병합 base 가 없다. 이번 수집분으로 새로 쓰는 것이 맞다.
            _log.info("HF 에 %s 월 파일 없음(새 달): 병합 base 없이 기록", ym)
            continue
        seeded.append(f"{ym}.parquet")
    return seeded


def writeMonthly(df: pl.DataFrame) -> list[str]:
    """리포트 메타 DataFrame 을 pub_date 월별 parquet 로 병합 기록하고 변경 상대경로 반환.

    Capabilities:
        - pub_date(YYYY-MM-DD) → YYYYMM 버킷별로 분할.
        - 기존 월 파일이 있으면 concat 후 report_id 기준으로 합친다(재수집 idempotent). 같은 report_id 는
          열마다 마지막 non-null 값을 쓴다. corpCode 조회가 실패한 run 의 빈 ticker 가 앞서 해소된 ticker 를
          지우지 않게 하기 위해서다.
        - 발간일 내림차순 정렬 후 ``{YYYYMM}.parquet`` 기록.

    AIContext:
        - 본문 0 — 메타만 적재(제목·URL·날짜·구분·종목). 링크아웃 대상.
        - 반환 상대경로는 changed manifest 입력(증분 HF 업로드 SSOT).

    Guide:
        sync 스크립트가 gather 수집 결과(g.brokerageReports())를 그대로 넘겨 호출.

    When:
        일별/증분 sync 시 또는 과거 백필 시.

    How:
        pub_date≥7자만 채택 → ``group_by(YYYYMM)`` → 월 파일 merge(report_id 별 열마다 마지막 non-null) → write.

    Args:
        df: report_id·broker·title·pub_date 등 PRD 스키마 DataFrame.

    Returns:
        list[str] — 변경된 월 파일 상대경로(예: ``["202606.parquet"]``). 빈 입력은 ``[]``.

    Requires:
        polars + 쓰기 가능한 ``data/research/brokerage`` 경로.

    Raises:
        없음 — 빈/이상 날짜 행은 skip.

    Example::

        from dartlab.gather.sources.brokerage.io import writeMonthly
        changed = writeMonthly(df)   # ["202606.parquet"]

    See Also:
        loadLocal : 기록된 월 parquet 을 다시 읽는다.
        dartlab.pipeline.changed.writeChanged : 반환값을 manifest 로 기록.
    """
    if df.is_empty():
        return []
    base = _dataDir()
    work = df.filter(pl.col("pub_date").str.len_chars() >= 7).with_columns(
        pl.col("pub_date").str.replace_all("-", "").str.slice(0, 6).alias("_ym")
    )
    changed: list[str] = []
    for (ym,), grp in work.group_by("_ym", maintain_order=True):
        if not ym or len(str(ym)) < 6:
            continue
        part = grp.drop("_ym").select(_COLUMNS)
        fp = base / f"{ym}.parquet"
        if fp.exists():
            merged = (
                pl.concat([pl.read_parquet(fp).select(_COLUMNS), part])
                .group_by("report_id", maintain_order=True)
                .agg(pl.all().drop_nulls().last())
                .select(_COLUMNS)
            )
        else:
            merged = part
        merged.sort("pub_date", descending=True).write_parquet(fp)
        changed.append(f"{ym}.parquet")
    return changed


def loadLocal() -> pl.DataFrame:
    """로컬에 기록된 모든 월 parquet 을 합쳐 반환(발간일 내림차순). 없으면 빈 DataFrame.

    Capabilities:
        - ``data/research/brokerage/*.parquet`` 전부 read + concat + 발간일 정렬.

    AIContext:
        - 오프라인/로컬 검증용 read 경로. 공개 HF 직독은 bulkData 경유(별도).

    Guide:
        sync 직후 적재 결과 확인, 테스트 검증에 사용.

    When:
        로컬 빌드 검증 / 디버깅 시.

    How:
        glob ``*.parquet`` → ``pl.read_parquet`` 각각 → concat → sort.

    Args:
        없음.

    Returns:
        pl.DataFrame — 전 월 합본(발간일 내림차순). 파일 없으면 빈 DataFrame(스키마 0열).

    Requires:
        polars + ``data/research/brokerage`` (없으면 빈 결과).

    Raises:
        없음.

    Example::

        from dartlab.gather.sources.brokerage.io import loadLocal
        df = loadLocal()

    See Also:
        writeMonthly : 본 함수가 읽는 월 parquet 생산자.
    """
    base = _dataDir()
    files = sorted(base.glob("*.parquet"))
    if not files:
        return pl.DataFrame()
    frames = [pl.read_parquet(f) for f in files]
    return pl.concat(frames).sort("pub_date", descending=True)
