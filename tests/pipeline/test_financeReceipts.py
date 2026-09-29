"""DART finance 접수 원장 회귀. 내용 해시, 불변 쓰기, 최초 관측 접기를 고정한다."""

from __future__ import annotations

from pathlib import Path

import polars as pl
import pytest

from dartlab.pipeline import financeReceipts as receipts


def _financeFrame(stockCode: str = "005930", *, amount: str = "100") -> pl.DataFrame:
    """두 접수번호, 접수번호당 두 계정 행을 가진 최소 finance frame."""

    rows = []
    for rceptNo, year, reprt in (("20250515001922", "2025", "11013"), ("20250814003156", "2025", "11012")):
        for accountId, value in (("ifrs-full_Revenue", amount), ("dart_OperatingIncomeLoss", "20")):
            rows.append(
                {
                    "rcept_no": rceptNo,
                    "reprt_code": reprt,
                    "bsns_year": year,
                    "corp_code": "00126380",
                    "stock_code": stockCode,
                    "fs_div": "CFS",
                    "sj_div": "IS",
                    "account_id": accountId,
                    "thstrm_amount": value,
                    "corp_name": "삼성전자",
                    "collect_status": "collected",
                }
            )
    return pl.DataFrame(rows)


def _writeFinance(root: Path, frame: pl.DataFrame, stockCode: str = "005930") -> Path:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{stockCode}.parquet"
    frame.write_parquet(path)
    return path


def testReceiptHashIgnoresRowOrderAndLabelColumns() -> None:
    """행 순서, 회사명, 수집 표식은 공시 내용이 아니므로 해시를 바꾸지 않는다."""

    base = receipts.financeReceiptRows(_financeFrame(), stockCode="005930")
    shuffled = (
        _financeFrame()
        .reverse()
        .with_columns(
            pl.lit("삼성전자(주)").alias("corp_name"),
            pl.lit("recollected").alias("collect_status"),
        )
    )
    again = receipts.financeReceiptRows(shuffled, stockCode="005930")

    assert base["contentHash"].to_list() == again["contentHash"].to_list()
    assert base["rceptNo"].to_list() == ["20250515001922", "20250814003156"]
    assert base["receiptDate"].to_list() == ["20250515", "20250814"]
    assert base["rowCount"].to_list() == [2, 2]
    assert base["reprtCodes"].to_list() == ["11013", "11012"]


def testReceiptHashChangesOnlyForTheEditedFiling() -> None:
    """한 접수번호의 금액이 바뀌면 그 접수번호 해시만 바뀐다."""

    base = receipts.financeReceiptRows(_financeFrame(), stockCode="005930")
    edited = _financeFrame().with_columns(
        pl.when((pl.col("rcept_no") == "20250814003156") & (pl.col("account_id") == "ifrs-full_Revenue"))
        .then(pl.lit("101"))
        .otherwise(pl.col("thstrm_amount"))
        .alias("thstrm_amount")
    )
    changed = receipts.financeReceiptRows(edited, stockCode="005930")

    assert base["contentHash"][0] == changed["contentHash"][0]
    assert base["contentHash"][1] != changed["contentHash"][1]


@pytest.mark.parametrize(
    ("frame", "message"),
    (
        (_financeFrame(stockCode="000660"), "stock_code"),
        (_financeFrame().with_columns(pl.lit(None, dtype=pl.Utf8).alias("rcept_no")), "rcept_no"),
        (_financeFrame(amount="1\x1f00"), "제어문자"),
        (_financeFrame().drop("rcept_no"), "rcept_no"),
    ),
)
def testReceiptRowsFailClosedOnBrokenInput(frame: pl.DataFrame, message: str) -> None:
    """다른 종목 행, 수집 표식이 아닌 빈 접수번호, 구분 제어문자, 접수번호 열 부재는 거부한다."""

    with pytest.raises(receipts.FinanceReceiptError, match=message):
        receipts.financeReceiptRows(frame, stockCode="005930")


def _placeholderRows(count: int = 2) -> pl.DataFrame:
    """수집기가 남기는 접수번호 없는 pending, no_data 표식 행."""

    return pl.DataFrame(
        {
            "rcept_no": [None] * count,
            "bsns_year": ["2026"] * count,
            "collect_status": (["pending", "no_data"] * count)[:count],
        },
        schema={"rcept_no": pl.Utf8, "bsns_year": pl.Utf8, "collect_status": pl.Utf8},
    )


def testPlaceholderRowsAreExcludedAndCounted(tmp_path: Path) -> None:
    """pending, no_data 표식은 공시가 아니다. 원장에서 빠지고 제외 행 수로만 남는다."""

    financeDir = tmp_path / "finance"
    _writeFinance(financeDir, pl.concat([_financeFrame(), _placeholderRows()], how="diagonal"))
    _writeFinance(financeDir, _placeholderRows().drop("rcept_no"), "088980")

    ledger = receipts.buildFinanceReceiptLedger(
        financeDir,
        ["005930.parquet", "088980.parquet"],
        observedAtUtc="20260929T060000Z",
        runId="123-1",
    )
    reference = receipts.financeReceiptRows(_financeFrame(), stockCode="005930")

    assert ledger.sourceFiles == ("005930.parquet", "088980.parquet")
    assert ledger.placeholderRows == 4
    assert ledger.frame["contentHash"].to_list() == reference["contentHash"].to_list()
    mixed = pl.concat([_financeFrame(), _placeholderRows()], how="diagonal")
    assert receipts.placeholderMask(mixed).to_list() == [False] * 4 + [True, True]
    assert receipts.placeholderMask(_financeFrame().drop("collect_status")).sum() == 0


def testBlankReceiptWithCollectedStatusIsRejected() -> None:
    """collected 행의 접수번호가 비면 표식이 아니라 손상이다."""

    broken = _financeFrame().with_columns(
        pl.when(pl.col("account_id") == "ifrs-full_Revenue").then(None).otherwise(pl.col("rcept_no")).alias("rcept_no")
    )
    with pytest.raises(receipts.FinanceReceiptError, match="수집 표식이 아닌데"):
        receipts.financeReceiptRows(broken, stockCode="005930")


def testLedgerReadsChangedFilesAndReportsMissingOnes(tmp_path: Path) -> None:
    """변경 목록의 파일만 읽고, 디스크에 없는 항목은 조용히 버리지 않고 따로 남긴다."""

    financeDir = tmp_path / "finance"
    _writeFinance(financeDir, _financeFrame())
    _writeFinance(financeDir, _financeFrame("000660"), "000660")

    ledger = receipts.buildFinanceReceiptLedger(
        financeDir,
        ["005930.parquet", "999999.parquet"],
        observedAtUtc="20260929T060000Z",
        runId="123-1",
    )

    assert ledger.sourceFiles == ("005930.parquet",)
    assert ledger.missingFiles == ("999999.parquet",)
    assert ledger.frame.height == 2
    assert set(ledger.frame["stockCode"].to_list()) == {"005930"}
    assert set(ledger.frame["observedAtUtc"].to_list()) == {"20260929T060000Z"}
    assert set(ledger.frame["ledgerSchema"].to_list()) == {receipts.FINANCE_RECEIPT_SCHEMA}
    assert set(ledger.frame["contentRule"].to_list()) == {receipts.FINANCE_RECEIPT_CONTENT_RULE}


@pytest.mark.parametrize(
    ("observedAtUtc", "runId", "changed"),
    (
        ("2026-09-29", "123-1", ["005930.parquet"]),
        ("20260929T060000Z", "../escape", ["005930.parquet"]),
        ("20260929T060000Z", "123-1", ["nested/005930.parquet"]),
    ),
)
def testLedgerRejectsMalformedRunIdentity(tmp_path: Path, observedAtUtc: str, runId: str, changed: list[str]) -> None:
    """관측 시각 형식, 경로를 벗어나는 run id, 중첩 경로는 실행 전에 거부한다."""

    financeDir = tmp_path / "finance"
    _writeFinance(financeDir, _financeFrame())
    with pytest.raises(receipts.FinanceReceiptError):
        receipts.buildFinanceReceiptLedger(financeDir, changed, observedAtUtc=observedAtUtc, runId=runId)


def testLedgerFileIsNeverOverwritten(tmp_path: Path) -> None:
    """같은 관측 시각과 run id 의 원장을 다시 쓰면 실패하고 첫 파일은 그대로다."""

    financeDir = tmp_path / "finance"
    _writeFinance(financeDir, _financeFrame())
    ledger = receipts.buildFinanceReceiptLedger(
        financeDir, ["005930.parquet"], observedAtUtc="20260929T060000Z", runId="123-1"
    )
    path = receipts.writeFinanceReceiptLedger(ledger, tmp_path / "ledger")
    original = path.read_bytes()

    assert path.name == receipts.financeReceiptFileName(ledger) == "20260929T060000Z_123-1.parquet"
    with pytest.raises(receipts.FinanceReceiptError, match="덮어쓰지"):
        receipts.writeFinanceReceiptLedger(ledger, tmp_path / "ledger")
    assert path.read_bytes() == original
    assert pl.read_parquet(path).equals(ledger.frame)


def testFoldKeepsFirstSeenAndFlagsInPlaceRevision(tmp_path: Path) -> None:
    """최초 관측은 처음 본 run 시각이고, 같은 접수번호의 내용 변화는 개정으로 드러난다."""

    financeDir = tmp_path / "finance"
    runs = []
    for stamp, frame in (
        ("20260929T060000Z", _financeFrame()),
        ("20260930T060000Z", _financeFrame()),
        ("20261001T060000Z", _financeFrame(amount="105")),
    ):
        _writeFinance(financeDir, frame)
        runs.append(
            receipts.buildFinanceReceiptLedger(
                financeDir, ["005930.parquet"], observedAtUtc=stamp, runId=f"run{len(runs)}"
            ).frame
        )

    folded = receipts.foldFinanceReceipts(pl.concat(runs))
    first = folded.filter(pl.col("rceptNo") == "20250515001922")

    assert first.height == 2
    assert first["firstSeenUtc"].to_list() == ["20260929T060000Z", "20261001T060000Z"]
    assert first["lastSeenUtc"].to_list() == ["20260930T060000Z", "20261001T060000Z"]
    assert first["observations"].to_list() == [2, 1]
    assert first["contentVersions"].to_list() == [2, 2]
    assert first["revisedInPlace"].all()


def testFoldRefusesMixedContentRules() -> None:
    """내용 규칙이 다른 원장의 해시는 같은 기준으로 비교하지 않는다."""

    ledger = receipts.financeReceiptRows(_financeFrame(), stockCode="005930").with_columns(
        pl.lit(receipts.FINANCE_RECEIPT_SCHEMA).alias("ledgerSchema"),
        pl.lit("20260929T060000Z").alias("observedAtUtc"),
        pl.lit("rule-a").alias("contentRule"),
    )
    mixed = pl.concat([ledger, ledger.with_columns(pl.lit("rule-b").alias("contentRule"))])

    with pytest.raises(receipts.FinanceReceiptError, match="규칙"):
        receipts.foldFinanceReceipts(mixed)


def testMainWritesOneLedgerFromTheChangedManifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """CLI 는 dist/changed_finance.txt 를 읽어 원장 한 개를 쓰고, 변경이 없으면 아무것도 쓰지 않는다."""

    monkeypatch.chdir(tmp_path)
    financeDir = tmp_path / "data" / "dart" / "finance"
    _writeFinance(financeDir, _financeFrame())
    (tmp_path / "dist").mkdir()
    (tmp_path / "dist" / "changed_finance.txt").write_text("", encoding="utf-8")

    assert receipts.main(["--finance-dir", str(financeDir), "--out-dir", "dist/financeReceipts"]) == 0
    assert not (tmp_path / "dist" / "financeReceipts").exists()

    (tmp_path / "dist" / "changed_finance.txt").write_text("005930.parquet\n", encoding="utf-8")
    code = receipts.main(
        [
            "--finance-dir",
            str(financeDir),
            "--out-dir",
            "dist/financeReceipts",
            "--run-id",
            "777-2",
            "--observed-at",
            "20260929T060000Z",
        ]
    )

    written = sorted((tmp_path / "dist" / "financeReceipts").glob("*.parquet"))
    assert code == 0
    assert [path.name for path in written] == ["20260929T060000Z_777-2.parquet"]
    assert pl.read_parquet(written[0]).height == 2


class _FakeHfApi:
    """file_exists 와 upload_file 호출만 기록하는 HfApi 대역."""

    def __init__(self, existing: set[str] | None = None) -> None:
        self.existing = existing or set()
        self.uploads: list[dict] = []

    def file_exists(self, repoId: str, path: str, *, repo_type: str) -> bool:
        return path in self.existing

    def upload_file(self, **kwargs) -> None:
        self.uploads.append(kwargs)


def testUploadWritesANewDatasetFileAndNeverOverwrites(tmp_path: Path) -> None:
    """HF 업로드는 dart/financeReceipts/ 아래 새 경로에만 쓰고, 같은 경로가 있으면 실패한다."""

    financeDir = tmp_path / "finance"
    _writeFinance(financeDir, _financeFrame())
    ledger = receipts.buildFinanceReceiptLedger(
        financeDir, ["005930.parquet"], observedAtUtc="20260929T060000Z", runId="123-1"
    )
    path = receipts.writeFinanceReceiptLedger(ledger, tmp_path / "ledger")
    api = _FakeHfApi()

    target = receipts.uploadFinanceReceiptLedger(path, api=api)

    assert target == "dart/financeReceipts/20260929T060000Z_123-1.parquet"
    assert [item["path_in_repo"] for item in api.uploads] == [target]
    assert api.uploads[0]["repo_type"] == "dataset"
    with pytest.raises(receipts.FinanceReceiptError, match="덮어쓰지"):
        receipts.uploadFinanceReceiptLedger(path, api=_FakeHfApi({target}))


def testRealSamsungFinanceFileSummarizesEveryRow() -> None:
    """로컬 삼성전자 finance 파일이 있으면 모든 행이 접수번호 요약에 정확히 한 번 들어간다."""

    path = Path("data/dart/finance/005930.parquet")
    if not path.exists():
        pytest.skip("DART finance store is not installed")
    frame = pl.read_parquet(path)
    rows = receipts.financeReceiptRows(frame, stockCode="005930")

    assert rows.height == frame["rcept_no"].n_unique()
    assert rows["rowCount"].sum() == frame.height
    assert rows["contentHash"].n_unique() == rows.height
    assert receipts.financeReceiptRows(frame.reverse(), stockCode="005930").equals(rows)
