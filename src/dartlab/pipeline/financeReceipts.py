"""DART finance 접수 원장. 수집 run 마다 본 공시별 내용 해시를 불변 파일로 남긴다.

``data/dart/finance/{code}.parquet`` 는 제자리 덮어쓰기라 ``rcept_no`` 는 있어도 우리가 그 내용을
언제 처음 알았는지는 남지 않는다. 과거 시점 상태를 exact 로 재구성하려면 이 시각이 필요하고,
소급해서 만들 수 없으므로 지금부터 쌓는다.

한 run 의 원장은 이번에 바뀐 종목 parquet 을 읽어 (종목, 접수번호) 마다 행 수, 보고서 식별자,
고정 내용 열의 SHA-256 을 기록한 parquet 한 개다. 파일 이름은 관측 시각과 run id 로 정하고
한 번 쓰면 덮어쓰지 않는다. 한 공시의 최초 관측 시각은 원장 전체에서 같은 (종목, 접수번호,
내용 해시) 가 처음 나타난 run 의 관측 시각이며, 실제 접수보다 늦을 수는 있어도 이를 수는 없는
보수적 상한이다. 같은 접수번호의 해시가 run 사이에 달라지면 제자리 개정이다.

원장은 내용 자체를 보관하지 않는다. 현재 보존 행의 해시가 최초 관측 해시와 같으면 그 행이
최초 관측 시점에 알던 내용과 같다는 증거가 된다. 정정 공시로 옛 접수번호가 사라지면 그 내용은
원장만으로 복원할 수 없고, 그 구간은 계속 conditional 이다.

실행:
    uv run python -X utf8 -m dartlab.pipeline.financeReceipts --out-dir dist/financeReceipts
    uv run python -X utf8 -m dartlab.pipeline.financeReceipts --out-dir dist/financeReceipts --upload

``--upload`` 은 HF 데이터셋 ``dart/financeReceipts/`` 에 새 파일로만 올린다. 같은 경로가 있으면 실패한다.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import polars as pl

FINANCE_RECEIPT_SCHEMA = "dart-finance-receipt-v1"
# HF 데이터셋 안 원장 폴더. finance 본체(dart/finance) 옆에 두고 파일은 run 마다 새로 만든다.
FINANCE_RECEIPT_HF_PREFIX = "dart/financeReceipts"
# 내용 해시에 넣는 열. 회사명, 보고서명, 재무제표명 같은 파생 라벨과 수집 표식(collect_status)은
# 공시 내용이 아니라서 뺀다. 순서가 곧 규칙이다. 바꾸면 FINANCE_RECEIPT_CONTENT_RULE 도 바뀐다.
FINANCE_RECEIPT_CONTENT_COLUMNS = (
    "rcept_no",
    "reprt_code",
    "bsns_year",
    "corp_code",
    "stock_code",
    "fs_div",
    "sj_div",
    "sj_nm",
    "account_id",
    "account_nm",
    "account_detail",
    "ord",
    "currency",
    "thstrm_nm",
    "thstrm_amount",
    "thstrm_add_amount",
    "frmtrm_nm",
    "frmtrm_amount",
    "frmtrm_q_nm",
    "frmtrm_q_amount",
    "frmtrm_add_amount",
    "bfefrmtrm_nm",
    "bfefrmtrm_amount",
)
# 수집기가 접수번호 없이 남기는 상태 표식. 공시 행이 아니라서 원장에 넣지 않는다.
FINANCE_PLACEHOLDER_STATUSES = frozenset({"pending", "no_data"})
FINANCE_RECEIPT_CONTENT_RULE = hashlib.sha256(
    ("|".join((FINANCE_RECEIPT_SCHEMA, *FINANCE_RECEIPT_CONTENT_COLUMNS))).encode("utf-8")
).hexdigest()
_NULL = "\x00"
_FIELD = "\x1f"
_ROW = "\x1e"
_RECEIPT_SCHEMA = {
    "ledgerSchema": pl.Utf8,
    "contentRule": pl.Utf8,
    "runId": pl.Utf8,
    "observedAtUtc": pl.Utf8,
    "stockCode": pl.Utf8,
    "corpCode": pl.Utf8,
    "rceptNo": pl.Utf8,
    "receiptDate": pl.Utf8,
    "bsnsYears": pl.Utf8,
    "reprtCodes": pl.Utf8,
    "fsDivs": pl.Utf8,
    "rowCount": pl.Int64,
    "contentHash": pl.Utf8,
}
_ROW_COLUMNS = (
    "stockCode",
    "corpCode",
    "rceptNo",
    "receiptDate",
    "bsnsYears",
    "reprtCodes",
    "fsDivs",
    "rowCount",
    "contentHash",
)


class FinanceReceiptError(ValueError):
    """접수 원장 입력이 계약을 어기거나 불변 파일을 덮어쓰려 할 때 발생한다."""


@dataclass(frozen=True)
class FinanceReceiptLedger:
    """한 수집 run 의 접수 원장, 읽지 못한 변경 파일 목록, 제외한 수집 표식 행 수."""

    frame: pl.DataFrame
    runId: str
    observedAtUtc: str
    sourceFiles: tuple[str, ...]
    missingFiles: tuple[str, ...]
    placeholderRows: int = 0


def _observedStamp(observedAtUtc: str) -> str:
    try:
        parsed = datetime.strptime(observedAtUtc, "%Y%m%dT%H%M%SZ")
    except ValueError as error:
        raise FinanceReceiptError(f"observedAtUtc 는 YYYYMMDDTHHMMSSZ 형식이어야 합니다: {observedAtUtc}") from error
    return parsed.strftime("%Y%m%dT%H%M%SZ")


def _runIdText(runId: str) -> str:
    text = str(runId).strip()
    if not text or not all(character.isalnum() or character in "-_." for character in text):
        raise FinanceReceiptError(f"runId 는 영숫자와 - _ . 만 허용합니다: {runId!r}")
    return text


def _joinedUnique(column: str) -> pl.Expr:
    return pl.col(column).drop_nulls().unique().sort().str.join(",").alias(column)


def placeholderMask(frame: pl.DataFrame) -> pl.Series:
    """접수번호 없이 수집 상태만 적은 표식 행을 가린다.

    Args:
        frame: finance parquet 한 개의 행 전체.

    Returns:
        ``collect_status`` 가 ``pending`` 이나 ``no_data`` 이고 접수번호가 비어 있는 행이 True 인 mask.
        이런 행은 아직 오지 않았거나 없는 기간의 수집 표식이지 공시가 아니다.

    Raises:
        없음.

    Example:
        ``placeholderMask(frame).sum()`` 이 표식 행 수를 준다.
    """

    if "collect_status" not in frame.columns:
        return pl.Series("placeholder", [False] * frame.height, dtype=pl.Boolean)
    status = frame["collect_status"].cast(pl.Utf8).is_in(sorted(FINANCE_PLACEHOLDER_STATUSES)).fill_null(False)
    if "rcept_no" not in frame.columns:
        return status.alias("placeholder")
    blank = frame["rcept_no"].is_null() | (frame["rcept_no"].cast(pl.Utf8).str.strip_chars() == "")
    return (status & blank.fill_null(True)).alias("placeholder")


def financeReceiptRows(frame: pl.DataFrame, *, stockCode: str) -> pl.DataFrame:
    """한 종목 finance parquet 을 접수번호별 내용 해시 행으로 요약한다.

    Args:
        frame: ``data/dart/finance/{code}.parquet`` 한 개의 행 전체.
        stockCode: 파일 이름의 종목코드. ``stock_code`` 열이 있으면 이 값과 같아야 한다.

    Returns:
        (종목, 접수번호) 마다 한 행. corpCode, receiptDate, bsnsYears, reprtCodes, fsDivs,
        rowCount, contentHash 를 가진다. 행 순서와 무관하게 같은 내용이면 같은 해시다.
        ``placeholderMask`` 표식 행은 공시가 아니라서 빠진다.

    Raises:
        FinanceReceiptError: 표식 행이 아닌데 접수번호가 없거나 비어 있거나, 종목코드가 파일과
            다르거나, 내용 값에 구분용 제어문자가 들어 있을 때.

    Example:
        ``rows = financeReceiptRows(pl.read_parquet(path), stockCode="005930")``
    """

    placeholder = placeholderMask(frame)
    if "rcept_no" not in frame.columns:
        if placeholder.all():
            return pl.DataFrame(schema={key: _RECEIPT_SCHEMA[key] for key in _ROW_COLUMNS})
        raise FinanceReceiptError(f"{stockCode}: rcept_no 열이 없습니다")
    blank = frame["rcept_no"].is_null() | (frame["rcept_no"].cast(pl.Utf8).str.strip_chars() == "")
    if (blank & ~placeholder).any():
        raise FinanceReceiptError(f"{stockCode}: 수집 표식이 아닌데 rcept_no 가 비어 있는 행이 있습니다")
    frame = frame.filter(~blank)
    if frame.height == 0:
        return pl.DataFrame(schema={key: _RECEIPT_SCHEMA[key] for key in _ROW_COLUMNS})
    if "stock_code" in frame.columns:
        codes = set(frame["stock_code"].drop_nulls().cast(pl.Utf8).unique().to_list())
        if codes - {stockCode}:
            raise FinanceReceiptError(f"{stockCode}: 파일 안 stock_code 가 다릅니다: {sorted(codes)}")
    fields = [
        (pl.col(name).cast(pl.Utf8) if name in frame.columns else pl.lit(None, dtype=pl.Utf8)).alias(name)
        for name in FINANCE_RECEIPT_CONTENT_COLUMNS
    ]
    content = frame.select(fields)
    unsafe = content.select(
        pl.any_horizontal([pl.col(name).str.contains(r"[\x00\x1e\x1f]") for name in FINANCE_RECEIPT_CONTENT_COLUMNS])
    ).to_series()
    if unsafe.fill_null(False).any():
        raise FinanceReceiptError(f"{stockCode}: 내용 값에 구분용 제어문자가 들어 있습니다")
    rowText = pl.concat_str(
        [pl.col(name).fill_null(_NULL) for name in FINANCE_RECEIPT_CONTENT_COLUMNS], separator=_FIELD
    )
    grouped = (
        content.with_columns(rowText.alias("__row"))
        .group_by("rcept_no")
        .agg(
            pl.len().alias("rowCount"),
            pl.col("__row").sort().str.join(_ROW).alias("__content"),
            _joinedUnique("corp_code"),
            _joinedUnique("bsns_year"),
            _joinedUnique("reprt_code"),
            _joinedUnique("fs_div"),
        )
        .sort("rcept_no")
    )
    hashes = [hashlib.sha256(text.encode("utf-8")).hexdigest() for text in grouped["__content"].to_list()]
    return grouped.select(
        pl.lit(stockCode).alias("stockCode"),
        pl.col("corp_code").alias("corpCode"),
        pl.col("rcept_no").alias("rceptNo"),
        pl.when(pl.col("rcept_no").str.contains(r"^\d{8}"))
        .then(pl.col("rcept_no").str.slice(0, 8))
        .otherwise(None)
        .alias("receiptDate"),
        pl.col("bsns_year").alias("bsnsYears"),
        pl.col("reprt_code").alias("reprtCodes"),
        pl.col("fs_div").alias("fsDivs"),
        pl.col("rowCount").cast(pl.Int64),
        pl.Series("contentHash", hashes, dtype=pl.Utf8),
    )


def buildFinanceReceiptLedger(
    financeDir: str | Path,
    changedFiles: list[str] | tuple[str, ...],
    *,
    observedAtUtc: str,
    runId: str,
) -> FinanceReceiptLedger:
    """이번 run 에 바뀐 종목 parquet 들로 접수 원장 한 개를 만든다.

    Args:
        financeDir: ``data/dart/finance`` 디렉터리.
        changedFiles: 이번 run 의 변경 상대경로 목록. ``dist/changed_finance.txt`` 의 ``{code}.parquet`` 이다.
        observedAtUtc: 이 run 이 내용을 확인한 UTC 시각. ``YYYYMMDDTHHMMSSZ`` 형식이다.
        runId: 수집 run 식별자. GitHub Actions 에서는 run id 와 attempt 를 이어 쓴다.

    Returns:
        원장 frame, run id, 관측 시각, 읽은 파일, 목록에는 있으나 디스크에 없던 파일.

    Raises:
        FinanceReceiptError: 시각이나 run id 형식이 틀리거나, 파일 하나라도 계약을 어길 때.

    Example:
        ``ledger = buildFinanceReceiptLedger("data/dart/finance", ["005930.parquet"], observedAtUtc="20260929T060000Z", runId="local")``
    """

    stamp = _observedStamp(observedAtUtc)
    run = _runIdText(runId)
    root = Path(financeDir)
    frames: list[pl.DataFrame] = []
    sources: list[str] = []
    missing: list[str] = []
    placeholders = 0
    for relative in sorted({str(item).strip().replace("\\", "/") for item in changedFiles if str(item).strip()}):
        path = root / relative
        if path.suffix != ".parquet" or "/" in relative:
            raise FinanceReceiptError(f"finance 변경 목록은 종목 parquet 이름이어야 합니다: {relative}")
        if not path.exists():
            missing.append(relative)
            continue
        frame = pl.read_parquet(path)
        placeholders += int(placeholderMask(frame).sum())
        frames.append(financeReceiptRows(frame, stockCode=path.stem))
        sources.append(relative)
    rows = pl.concat(frames) if frames else pl.DataFrame(schema={key: _RECEIPT_SCHEMA[key] for key in _ROW_COLUMNS})
    ledger = rows.select(
        pl.lit(FINANCE_RECEIPT_SCHEMA).alias("ledgerSchema"),
        pl.lit(FINANCE_RECEIPT_CONTENT_RULE).alias("contentRule"),
        pl.lit(run).alias("runId"),
        pl.lit(stamp).alias("observedAtUtc"),
        *(pl.col(name) for name in _ROW_COLUMNS),
    ).sort(["stockCode", "rceptNo"])
    return FinanceReceiptLedger(ledger.cast(_RECEIPT_SCHEMA), run, stamp, tuple(sources), tuple(missing), placeholders)


def financeReceiptFileName(ledger: FinanceReceiptLedger) -> str:
    """원장 파일 이름. 관측 시각이 앞이라 이름순이 곧 시간순이다.

    Args:
        ledger: ``buildFinanceReceiptLedger`` 결과.

    Returns:
        ``{observedAtUtc}_{runId}.parquet``.

    Raises:
        없음.

    Example:
        ``financeReceiptFileName(ledger)`` 이 ``"20260929T060000Z_123-1.parquet"`` 을 준다.
    """

    return f"{ledger.observedAtUtc}_{ledger.runId}.parquet"


def writeFinanceReceiptLedger(ledger: FinanceReceiptLedger, outDir: str | Path) -> Path:
    """원장을 새 파일로 쓴다. 같은 이름이 이미 있으면 덮어쓰지 않고 실패한다.

    Args:
        ledger: ``buildFinanceReceiptLedger`` 결과.
        outDir: 원장 파일을 둘 디렉터리.

    Returns:
        쓴 파일 경로.

    Raises:
        FinanceReceiptError: 같은 이름의 원장이 이미 있을 때.

    Example:
        ``path = writeFinanceReceiptLedger(ledger, "dist/financeReceipts")``
    """

    target = Path(outDir) / financeReceiptFileName(ledger)
    target.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    ledger.frame.write_parquet(buffer, compression="zstd", statistics=True)
    try:
        with target.open("xb") as handle:
            handle.write(buffer.getvalue())
    except FileExistsError as error:
        raise FinanceReceiptError(f"원장은 덮어쓰지 않습니다: {target}") from error
    return target


def foldFinanceReceipts(ledgers: pl.DataFrame) -> pl.DataFrame:
    """여러 run 의 원장을 (종목, 접수번호, 내용 해시) 별 최초와 최근 관측으로 접는다.

    Args:
        ledgers: 원장 파일들을 이어 붙인 frame.

    Returns:
        firstSeenUtc, lastSeenUtc, observations, contentVersions, revisedInPlace 를 가진 frame.
        contentVersions 가 2 이상이면 같은 접수번호의 내용이 run 사이에 바뀐 것이다.

    Raises:
        FinanceReceiptError: 원장 schema 나 내용 규칙이 섞여 있을 때.

    Example:
        ``folded = foldFinanceReceipts(pl.concat([pl.read_parquet(p) for p in paths]))``
    """

    if ledgers.height and set(ledgers["ledgerSchema"].unique().to_list()) != {FINANCE_RECEIPT_SCHEMA}:
        raise FinanceReceiptError("원장 schema 가 섞여 있습니다")
    if ledgers.height and ledgers["contentRule"].n_unique() != 1:
        raise FinanceReceiptError("내용 해시 규칙이 다른 원장은 같은 해시로 비교하지 않습니다")
    keys = ["stockCode", "rceptNo", "contentHash"]
    folded = ledgers.group_by(keys).agg(
        pl.col("observedAtUtc").min().alias("firstSeenUtc"),
        pl.col("observedAtUtc").max().alias("lastSeenUtc"),
        pl.len().alias("observations"),
        pl.col("receiptDate").first(),
        pl.col("rowCount").first(),
    )
    return (
        folded.with_columns(
            pl.col("contentHash").n_unique().over(["stockCode", "rceptNo"]).alias("contentVersions"),
        )
        .with_columns((pl.col("contentVersions") > 1).alias("revisedInPlace"))
        .sort(["stockCode", "rceptNo", "firstSeenUtc"])
    )


def uploadFinanceReceiptLedger(path: str | Path, *, api: object | None = None, token: str | None = None) -> str:
    """원장 파일 한 개를 HF 데이터셋의 ``dart/financeReceipts/`` 에 새 파일로 올린다.

    Args:
        path: ``writeFinanceReceiptLedger`` 가 쓴 파일.
        api: ``huggingface_hub.HfApi`` 호환 객체. ``None`` 이면 새로 만든다.
        token: HF 토큰. ``None`` 이면 ``HF_TOKEN`` 환경 변수를 쓴다.

    Returns:
        데이터셋 안 경로.

    Raises:
        FinanceReceiptError: 같은 경로의 원장이 이미 데이터셋에 있을 때. 덮어쓰지 않는다.

    Example:
        ``uploadFinanceReceiptLedger("dist/financeReceipts/20260929T060000Z_123-1.parquet")``
    """

    from dartlab.core.dataConfig import repoFor
    from dartlab.core.hfRetry import retryHfCall

    if api is None:
        from huggingface_hub import HfApi

        api = HfApi(token=token)
    source = Path(path)
    repo = repoFor("finance")
    target = f"{FINANCE_RECEIPT_HF_PREFIX}/{source.name}"
    if retryHfCall(api.file_exists, repo, target, repo_type="dataset"):
        raise FinanceReceiptError(f"원장은 덮어쓰지 않습니다: {target}")
    retryHfCall(
        api.upload_file,
        path_or_fileobj=str(source),
        path_in_repo=target,
        repo_id=repo,
        repo_type="dataset",
        commit_message=f"finance receipt ledger {source.stem}",
    )
    return target


def _defaultFinanceDir() -> Path:
    from dartlab.core.dataConfig import DATA_RELEASES

    base = Path(os.environ.get("DARTLAB_DATA_DIR") or "data")
    return base / DATA_RELEASES["finance"]["dir"]


def _defaultRunId() -> str:
    runId = os.environ.get("GITHUB_RUN_ID", "").strip()
    if not runId:
        return "local"
    attempt = os.environ.get("GITHUB_RUN_ATTEMPT", "1").strip() or "1"
    return f"{runId}-{attempt}"


def main(argv: list[str] | None = None) -> int:
    """변경 매니페스트로 이번 run 의 접수 원장을 한 파일 만들고, 요청하면 HF 에 새 파일로 올린다.

    Args:
        argv: 명령행 인자. ``None`` 이면 ``sys.argv`` 를 쓴다.

    Returns:
        종료 코드. 변경이 없으면 파일을 만들지 않고 0 이다.

    Raises:
        FinanceReceiptError: 입력이 계약을 어기거나 같은 이름의 원장이 이미 있을 때.

    Example:
        ``python -m dartlab.pipeline.financeReceipts --out-dir dist/financeReceipts --upload``
    """

    from dartlab.pipeline.changed import readChanged

    parser = argparse.ArgumentParser(prog="dartlab.pipeline.financeReceipts", description=main.__doc__.split("\n")[0])
    parser.add_argument("--finance-dir", default=None, help="finance parquet 디렉터리 (기본 data/dart/finance)")
    parser.add_argument("--out-dir", default="dist/financeReceipts", help="원장 파일 디렉터리")
    parser.add_argument("--run-id", default=None, help="run 식별자 (기본 GITHUB_RUN_ID-ATTEMPT 또는 local)")
    parser.add_argument("--observed-at", default=None, help="관측 UTC 시각 YYYYMMDDTHHMMSSZ (기본 지금)")
    parser.add_argument("--upload", action="store_true", help="쓴 원장을 HF dart/financeReceipts/ 에 새 파일로 올린다")
    args = parser.parse_args(argv)
    changed = readChanged("finance")
    if not changed:
        print("[financeReceipts] 변경 없음. 원장을 만들지 않는다.", flush=True)
        return 0
    observedAt = args.observed_at or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    ledger = buildFinanceReceiptLedger(
        Path(args.finance_dir) if args.finance_dir else _defaultFinanceDir(),
        changed,
        observedAtUtc=observedAt,
        runId=args.run_id or _defaultRunId(),
    )
    path = writeFinanceReceiptLedger(ledger, args.out_dir)
    print(
        f"[financeReceipts] {path} 접수 {ledger.frame.height}건, 종목 {len(ledger.sourceFiles)}개, "
        f"디스크에 없던 변경 {len(ledger.missingFiles)}개, 제외한 수집 표식 {ledger.placeholderRows}행",
        flush=True,
    )
    if args.upload:
        print(f"[financeReceipts] HF 업로드 {uploadFinanceReceiptLedger(path)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
