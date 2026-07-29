"""연결재무제표 우선 판정 회귀.

우선 판정이 회사별이 아니라 유니버스 전체 결정으로 구현돼 있었다. 연결 행이 하나라도
있으면 전체를 연결로 좁혔기 때문에, 별도만 제출하는 회사가 "다른 회사가 연결을 냈다" 는
이유로 전종목 표에서 통째로 사라졌다.

같은 회사를 혼자 스캔하면 남고 함께 스캔하면 없어지는, 유니버스에 의존하는 삭제였다.
사라진 회사는 표에 없으니 사용자가 빠졌다는 사실조차 볼 수 없다. 같은 블록이 아홉 모듈에
복사돼 있어 결함도 아홉 개였다.
"""

from __future__ import annotations

import polars as pl

from dartlab.scan.io.parquet import (
    _scanFinanceFromLazy,
    preferConsolidatedPerCompany,
    preferConsolidatedPerCompanyLazy,
)


def _frame() -> pl.DataFrame:
    """연결과 별도를 모두 내는 회사, 별도만 내는 회사를 섞는다."""

    return pl.DataFrame(
        {
            "stockCode": ["CONS01", "CONS01", "SOLO01", "SOLO01"],
            "fs_nm": ["연결재무제표", "재무제표", "재무제표", "재무제표"],
            "account_nm": ["매출액", "매출액", "매출액", "영업이익"],
            "thstrm_amount": ["1000", "900", "500", "50"],
        }
    )


def testStandaloneOnlyCompanySurvivesAlongsideConsolidatedFilers() -> None:
    """이 한 줄이 결함의 전부다. 별도만 내는 회사가 남아야 한다."""

    result = preferConsolidatedPerCompany(_frame())

    assert sorted(result["stockCode"].unique().to_list()) == ["CONS01", "SOLO01"]


def testConsolidatedIsPreferredWhenTheCompanyFilesBoth() -> None:
    """둘 다 내는 회사는 연결을 쓴다. 우선순위 자체는 그대로다."""

    result = preferConsolidatedPerCompany(_frame())
    consolidated = result.filter(pl.col("stockCode") == "CONS01")

    assert consolidated["fs_nm"].unique().to_list() == ["연결재무제표"]


def testStandaloneRowsAreKeptWholeForACompanyWithoutConsolidated() -> None:
    """별도만 있는 회사는 그 회사의 행이 전부 남아야 한다."""

    result = preferConsolidatedPerCompany(_frame())
    standalone = result.filter(pl.col("stockCode") == "SOLO01")

    assert standalone.height == 2


def testResultDoesNotDependOnWhoElseIsInTheUniverse() -> None:
    """혼자 스캔할 때와 함께 스캔할 때 같은 답이 나와야 한다."""

    full = preferConsolidatedPerCompany(_frame())
    alone = preferConsolidatedPerCompany(_frame().filter(pl.col("stockCode") == "SOLO01"))

    assert full.filter(pl.col("stockCode") == "SOLO01").height == alone.height


def testFrameWithoutTheJudgementColumnsIsReturnedUnchanged() -> None:
    """판정할 수 없으면 임의로 걸러내지 않는다."""

    frame = pl.DataFrame({"stockCode": ["A"], "v": [1]})

    assert preferConsolidatedPerCompany(frame).equals(frame)


def testEmptyFrameIsHandled() -> None:
    """빈 입력에서 예외가 나면 상위 스캔이 통째로 죽는다."""

    empty = pl.DataFrame({"stockCode": [], "fs_nm": []})

    assert preferConsolidatedPerCompany(empty).height == 0


def testCustomStockCodeColumnIsHonored() -> None:
    """축마다 종목코드 컬럼 이름이 다르다."""

    frame = pl.DataFrame(
        {
            "corp": ["A", "A", "B"],
            "fs_nm": ["연결재무제표", "재무제표", "재무제표"],
        }
    )

    result = preferConsolidatedPerCompany(frame, "corp")

    assert sorted(result["corp"].unique().to_list()) == ["A", "B"]
    assert result.filter(pl.col("corp") == "A")["fs_nm"].to_list() == ["연결재무제표"]


def testLazyPreferenceKeepsStandaloneOnlyCompany() -> None:
    """합본과 raw glob이 쓰는 lazy 경로에서도 회사별 판정이어야 한다."""

    result = preferConsolidatedPerCompanyLazy(_frame().lazy()).collect()

    assert sorted(result["stockCode"].unique().to_list()) == ["CONS01", "SOLO01"]


def testFinanceLazyConsumerKeepsStandaloneOnlyCompany() -> None:
    """실제 계정 스캔 소비자가 혼합 유니버스에서 별도 회사를 잃지 않는다."""

    frame = pl.DataFrame(
        {
            "stockCode": ["CONS01", "CONS01", "SOLO01"],
            "bsns_year": ["2025", "2025", "2025"],
            "fs_nm": ["연결재무제표", "재무제표", "재무제표"],
            "account_id": ["Revenue", "Revenue", "Revenue"],
            "account_nm": ["매출액", "매출액", "매출액"],
            "thstrm_amount": ["100", "90", "50"],
        }
    )

    result = _scanFinanceFromLazy(frame.lazy(), {"Revenue"}, {"매출액"}, "thstrm_amount")

    assert result == {"CONS01": 100.0, "SOLO01": 50.0}


def testDebtMergedConsumerKeepsStandaloneOnlyCompany(tmp_path) -> None:
    """부채 합본 소비자도 유니버스 전체 연결 판정을 쓰지 않는다."""
    from dartlab.scan.debt.scanner import _debtMixFromMerged

    rows = []
    for code, fs_name, liabilities, equity in [
        ("CONS01", "연결재무제표", "100", "50"),
        ("CONS01", "재무제표", "90", "45"),
        ("SOLO01", "재무제표", "40", "20"),
    ]:
        rows.extend(
            [
                {
                    "stockCode": code,
                    "bsns_year": "2025",
                    "sj_div": "BS",
                    "fs_nm": fs_name,
                    "account_id": "Liabilities",
                    "account_nm": "부채총계",
                    "thstrm_amount": liabilities,
                },
                {
                    "stockCode": code,
                    "bsns_year": "2025",
                    "sj_div": "BS",
                    "fs_nm": fs_name,
                    "account_id": "Equity",
                    "account_nm": "자본총계",
                    "thstrm_amount": equity,
                },
            ]
        )
    path = tmp_path / "finance.parquet"
    pl.DataFrame(rows).write_parquet(path)

    result = _debtMixFromMerged(path)

    assert result["CONS01"]["부채비율"] == 200.0
    assert result["SOLO01"]["부채비율"] == 200.0
