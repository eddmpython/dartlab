"""terminalStmt bake — 파사드 panel → DART 동형 FINANCE_COLUMNS 변환 단위 검증.

데이터 무의존: company.panel 을 작은 wide DataFrame mock 으로 주입.
"""

import polars as pl
import pytest

pytestmark = pytest.mark.unit


class _FakeCompany:
    """panel(stmt) → 사전 정의 wide DataFrame 반환하는 mock(IS/BS/CF)."""

    def __init__(self, panels: dict[str, pl.DataFrame]):
        self._panels = panels

    def panel(self, stmt):
        df = self._panels.get(stmt)
        if df is None:
            raise KeyError(stmt)
        return df


def _is_panel() -> pl.DataFrame:
    # snakeId·항목·분기열. revenue+sales synonym 중복(같은 값) + 완전연도(2024 4분기) + 부분연도(2025 Q1~Q2).
    return pl.DataFrame(
        {
            "snakeId": ["sales", "revenue", "operating_profit", "profit_loss"],
            "항목": ["매출액", "매출액", "영업이익", "당기순이익"],
            "2025Q2": [60.0, 60.0, 12.0, 8.0],
            "2025Q1": [50.0, 50.0, 10.0, 7.0],
            "2024Q4": [40.0, 40.0, 9.0, 6.0],
            "2024Q3": [30.0, 30.0, 7.0, 5.0],
            "2024Q2": [25.0, 25.0, 6.0, 4.0],
            "2024Q1": [20.0, 20.0, 5.0, 3.0],
        }
    )


def _bs_panel() -> pl.DataFrame:
    # 유동자산 vs 비유동자산 — substring 충돌 함정. account_id 정확매칭으로 분리돼야 한다.
    return pl.DataFrame(
        {
            "snakeId": ["assets", "current_assets", "noncurrent_assets"],
            "항목": ["자산총계", "유동자산", "비유동자산"],
            "2025Q1": [210.0, 125.0, 85.0],
            "2024Q4": [200.0, 120.0, 80.0],
            "2024Q1": [180.0, 110.0, 70.0],
        }
    )


def _fake() -> _FakeCompany:
    return _FakeCompany({"IS": _is_panel(), "BS": _bs_panel(), "CF": pl.DataFrame()})


def test_schema_and_account_id_fill() -> None:
    """출력은 FINANCE_COLUMNS 스키마 + 표준항목 account_id 채움(정확매칭)."""
    from dartlab.providers.edgar.finance.terminalStmt import FINANCE_COLUMNS, bakeTerminalFinance

    df = bakeTerminalFinance("FAKE", company=_fake())
    assert df is not None
    assert list(df.columns) == list(FINANCE_COLUMNS)
    # 매출액 → ifrs-full_Revenue, 영업이익 → dart_OperatingIncomeLoss, 당기순이익 → ifrs-full_ProfitLoss
    rev = df.filter(pl.col("account_nm") == "매출액")
    assert rev.height > 0
    assert set(rev["account_id"].to_list()) == {"ifrs-full_Revenue"}


def test_current_vs_noncurrent_assets_not_confused() -> None:
    """유동자산·비유동자산이 서로 다른 account_id 로 분리 (substring 오매칭 방지)."""
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    df = bakeTerminalFinance("FAKE", company=_fake())
    ca = df.filter(pl.col("account_nm") == "유동자산")["account_id"].unique().to_list()
    nca = df.filter(pl.col("account_nm") == "비유동자산")["account_id"].unique().to_list()
    assert ca == ["ifrs-full_CurrentAssets"]
    assert "ifrs-full_CurrentAssets" not in nca  # 비유동이 유동 id 를 훔치지 않음


def test_quarterly_and_annual_rows() -> None:
    """분기 Q1~Q3(11013/11012/11014) + 연간(11011). flow 연간 = 4 분기 합(완전연도만)."""
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    df = bakeTerminalFinance("FAKE", company=_fake())
    # 2024 매출 완전연도(Q1~Q4) → 연간 = 20+25+30+40 = 115
    annual24 = df.filter(
        (pl.col("account_nm") == "매출액") & (pl.col("bsns_year") == "2024") & (pl.col("reprt_code") == "11011")
    )
    assert annual24.height == 1
    assert annual24["thstrm_amount"][0] == pytest.approx(115.0)
    # 2025 부분연도(Q1~Q2만) → flow 연간 미발행
    annual25 = df.filter(
        (pl.col("account_nm") == "매출액") & (pl.col("bsns_year") == "2025") & (pl.col("reprt_code") == "11011")
    )
    assert annual25.height == 0
    # Q4 standalone 은 미발행(DART slot 부재 → 터미널 역산)
    q4 = df.filter((pl.col("sj_div") == "IS") & ~pl.col("reprt_code").is_in(["11011", "11012", "11013", "11014"]))
    assert q4.height == 0


def test_bs_annual_is_year_end() -> None:
    """BS 연간(11011) = 회계연말(Q4) 시점잔액(합산 아님)."""
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    df = bakeTerminalFinance("FAKE", company=_fake())
    annual = df.filter(
        (pl.col("account_nm") == "자산총계") & (pl.col("bsns_year") == "2024") & (pl.col("reprt_code") == "11011")
    )
    assert annual.height == 1
    assert annual["thstrm_amount"][0] == pytest.approx(200.0)  # Q4 값, 200+180 합산 아님
    partial = df.filter(
        (pl.col("account_nm") == "자산총계") & (pl.col("bsns_year") == "2025") & (pl.col("reprt_code") == "11011")
    )
    assert partial.height == 0


def test_synonym_dedup() -> None:
    """동일 항목 synonym 중복행(매출액=sales+revenue)은 (stmt,항목,year,q)당 1행으로 dedup."""
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    df = bakeTerminalFinance("FAKE", company=_fake())
    dup = df.filter(
        (pl.col("account_nm") == "매출액") & (pl.col("bsns_year") == "2024") & (pl.col("reprt_code") == "11013")
    )
    assert dup.height == 1  # Q1 매출 1행만 (sales/revenue 중복 제거)


def test_empty_returns_none() -> None:
    """panel 전무(빈 회사) → None(터미널 정직 폴백)."""
    from dartlab.providers.edgar.finance.terminalStmt import bakeTerminalFinance

    empty = _FakeCompany({"IS": pl.DataFrame(), "BS": pl.DataFrame(), "CF": pl.DataFrame()})
    assert bakeTerminalFinance("FAKE", company=empty) is None


def test_statement_failure_aborts_bake_with_source_provenance() -> None:
    from dartlab.providers.edgar.finance.terminalStmt import TerminalFinanceBuildError, bakeTerminalFinance

    class _BrokenFinance:
        IS = _is_panel()

        def __getattr__(self, name: str):
            """BS 접근만 손상 source 로 흉내낸다.

            폐기된 BS property 정의를 대역에서도 되살리지 않는다 (stale_references
            ``bs_property_def``). 정의 없이 접근 시점에 같은 OSError 를 낸다.
            """
            if name == "BS":
                raise OSError("corrupt BS source")
            raise AttributeError(name)

    class _BrokenCompany:
        _finance = _BrokenFinance()

    with pytest.raises(TerminalFinanceBuildError, match=r"ticker=FAKE, statement=BS, error=OSError") as excInfo:
        bakeTerminalFinance("FAKE", company=_BrokenCompany())

    assert isinstance(excInfo.value.__cause__, OSError)
