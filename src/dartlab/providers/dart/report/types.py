"""OpenDART 정기보고서 API 타입 정의 및 컬럼 매핑."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import polars as pl

API_TYPES = [
    "auditContract",
    "auditOpinion",
    "capitalChange",
    "commercialPaper",
    "contingentCapital",
    "corporateBond",
    "debtSecurities",
    "dividend",
    "employee",
    "executive",
    "executivePayAllTotal",
    "executivePayByType",
    "executivePayIndividual",
    "executivePayTotal",
    "hybridSecurities",
    "investedCompany",
    "majorHolder",
    "majorHolderChange",
    "minorityHolder",
    "nonAuditContract",
    "outsideDirector",
    "privateOfferingUsage",
    "publicOfferingUsage",
    "shortTermBond",
    "stockTotal",
    "topPay",
    "treasuryStock",
    "unregisteredExecutivePay",
]

API_TYPE_LABELS: dict[str, str] = {
    "auditContract": "감사용역체결현황",
    "auditOpinion": "감사의견",
    "capitalChange": "증자감자현황",
    "commercialPaper": "기업어음증권미상환잔액",
    "contingentCapital": "조건부자본증권미상환잔액",
    "corporateBond": "회사채미상환잔액",
    "debtSecurities": "채무증권발행실적",
    "dividend": "배당",
    "employee": "직원현황",
    "executive": "임원현황",
    "executivePayAllTotal": "임원보수전체",
    "executivePayByType": "임원보수유형별",
    "executivePayIndividual": "임원보수개인별",
    "executivePayTotal": "임원보수총승인액",
    "hybridSecurities": "신종자본증권미상환잔액",
    "investedCompany": "타법인출자현황",
    "majorHolder": "최대주주현황",
    "majorHolderChange": "최대주주변동현황",
    "minorityHolder": "소액주주현황",
    "nonAuditContract": "비감사용역계약",
    "outsideDirector": "사외이사현황",
    "privateOfferingUsage": "사모자금사용내역",
    "publicOfferingUsage": "공모자금사용내역",
    "shortTermBond": "단기사채미상환잔액",
    "stockTotal": "주식총수현황",
    "topPay": "개인별보수지급(5억이상)",
    "treasuryStock": "자기주식현황",
    "unregisteredExecutivePay": "미등기임원보수",
}

STR_OVERRIDE_COLS: dict[str, set[str]] = {
    "auditContract": {"adtor", "cn"},
    "auditOpinion": {"adtor", "adt_reprt_spcmnt_matter"},
    "capitalChange": {"isu_dcrs_de", "isu_dcrs_stle", "isu_dcrs_stock_knd"},
    "nonAuditContract": {"bsns_year", "cntrct_cncls_de", "servc_cn", "servc_exc_pd"},
    "investedCompany": {"frst_acqs_de", "invstmnt_purps"},
    "majorHolderChange": {"change_on", "mxmm_shrholdr_nm", "change_cause"},
    "employee": {"rm"},
    "executivePayAllTotal": {"rm"},
    "unregisteredExecutivePay": {"rm"},
    "treasuryStock": {"stock_knd", "acqs_mth1", "acqs_mth2", "acqs_mth3", "rm"},
    "outsideDirector": {"apnt", "rlsofc", "mdstrm_resig"},
    "privateOfferingUsage": {
        "se_nm",
        "pay_de",
        "real_cptal_use_sttus",
        "real_cptal_use_dtls_cn",
        "dffrnc_occrrnc_resn",
        "cptal_use_plan",
        "mtrpt_cptal_use_plan_useprps",
    },
    "publicOfferingUsage": {
        "se_nm",
        "pay_de",
        "on_dclrt_cptal_use_plan",
        "real_cptal_use_sttus",
        "rs_cptal_use_plan_useprps",
        "real_cptal_use_dtls_cn",
        "dffrnc_occrrnc_resn",
    },
    "debtSecurities": {"se", "mtd"},
    "commercialPaper": {"mtd"},
    "hybridSecurities": {"mtd"},
    "contingentCapital": {"mtd"},
    "executivePayTotal": {"se", "rm"},
    "executivePayByType": {"se", "rm"},
    "stockTotal": {"se"},
    "minorityHolder": {"se"},
    "executive": {"mxmm_shrholdr_relate"},
    "dividend": {"se", "stock_knd"},
}


def _seriesToWide(
    years: list[int],
    metrics: list[tuple[str, list]],
) -> pl.DataFrame | None:
    """시계열 metric 리스트를 metric(행)×year(열) 와이드 DataFrame으로 변환."""
    yearCols = [str(y) for y in years]
    rows: list[dict[str, object]] = []
    for label, series in metrics:
        if not any(v is not None for v in series):
            continue
        row: dict[str, object] = {"metric": label}
        for y, v in zip(yearCols, series):
            row[y] = v
        rows.append(row)
    if not rows:
        return None
    df = pl.DataFrame(rows)
    # 최신 먼저 역순 정렬
    periodCols = [c for c in df.columns if c != "metric"]
    df = df.select(["metric"] + periodCols[::-1])
    return df


META_DROP_COLS = frozenset(
    {
        "rcept_no",
        "corp_cls",
        "corp_code",
        "corp_name",
        "corpCode",
        "fsDiv",
        "collectStatus",
        "apiName",
    }
)

KEEP_META_COLS = frozenset(
    {
        "stockCode",
        "year",
        "quarter",
        "apiType",
        "stlm_dt",
    }
)

QUARTER_MAP: dict[str, int] = {
    "1분기": 1,
    "2분기": 2,
    "3분기": 3,
    "4분기": 4,
}

PREFERRED_QUARTER: dict[str, int] = {
    "dividend": 4,
    "auditOpinion": 4,
    "auditContract": 4,
    "nonAuditContract": 4,
    "employee": 2,
    "executive": 2,
    "majorHolder": 2,
    "majorHolderChange": 2,
    "minorityHolder": 2,
    "outsideDirector": 2,
    "stockTotal": 2,
    "treasuryStock": 2,
    "investedCompany": 2,
    "corporateBond": 2,
    "shortTermBond": 2,
    "capitalChange": 2,
    "commercialPaper": 2,
    "contingentCapital": 2,
    "executivePayAllTotal": 2,
    "executivePayByType": 2,
    "executivePayIndividual": 2,
    "executivePayTotal": 2,
    "hybridSecurities": 2,
    "topPay": 2,
    "unregisteredExecutivePay": 2,
    "publicOfferingUsage": 2,
    "privateOfferingUsage": 2,
    "debtSecurities": 2,
}


@dataclass
class ReportResult:
    """apiType별 추출 결과."""

    apiType: str
    label: str
    df: pl.DataFrame
    years: list[int] = field(default_factory=list)
    nYears: int = 0

    def __repr__(self) -> str:
        return f"ReportResult(apiType={self.apiType!r}, rows={self.df.height}, nYears={self.nYears})"


@dataclass
class DividendResult:
    """배당 시계열 결과."""

    years: list[int]
    dps: list[Optional[float]]
    dividendYield: list[Optional[float]]
    stockDividend: list[Optional[float]]
    stockDividendYield: list[Optional[float]]
    df: pl.DataFrame

    @property
    def nYears(self) -> int:
        return len(self.years)

    def toWide(self) -> pl.DataFrame | None:
        return _seriesToWide(
            self.years,
            [
                ("주당현금배당금", self.dps),
                ("현금배당수익률(%)", self.dividendYield),
                ("주식배당", self.stockDividend),
                ("주식배당수익률(%)", self.stockDividendYield),
            ],
        )


@dataclass
class EmployeeResult:
    """직원 시계열 결과."""

    years: list[int]
    totalEmployee: list[Optional[float]]
    avgMonthlySalary: list[Optional[float]]
    totalAnnualSalary: list[Optional[float]]
    df: pl.DataFrame

    @property
    def nYears(self) -> int:
        return len(self.years)

    def toWide(self) -> pl.DataFrame | None:
        return _seriesToWide(
            self.years,
            [
                ("총직원수", self.totalEmployee),
                ("월평균급여(천원)", self.avgMonthlySalary),
                ("연간총급여(백만원)", self.totalAnnualSalary),
            ],
        )


@dataclass
class MajorHolderResult:
    """최대주주 시계열 결과."""

    years: list[int]
    totalShareRatio: list[Optional[float]]
    latestHolders: list[dict]
    df: pl.DataFrame

    @property
    def nYears(self) -> int:
        return len(self.years)

    def toWide(self) -> pl.DataFrame | None:
        return _seriesToWide(
            self.years,
            [
                ("최대주주총지분율(%)", self.totalShareRatio),
            ],
        )


@dataclass
class ExecutiveResult:
    """임원현황 결과."""

    df: pl.DataFrame
    totalCount: int = 0
    registeredCount: int = 0
    outsideCount: int = 0

    def toWide(self) -> pl.DataFrame | None:
        rows = [
            {"metric": "총임원수", "latest": self.totalCount},
            {"metric": "사내이사", "latest": self.registeredCount},
            {"metric": "사외이사", "latest": self.outsideCount},
        ]
        return pl.DataFrame(rows)


@dataclass
class AuditResult:
    """감사의견 시계열 결과."""

    years: list[int]
    opinions: list[Optional[str]]
    auditors: list[Optional[str]]
    df: pl.DataFrame

    @property
    def nYears(self) -> int:
        return len(self.years)

    def toWide(self) -> pl.DataFrame | None:
        return _seriesToWide(
            self.years,
            [
                ("감사의견", self.opinions),
                ("감사법인", self.auditors),
            ],
        )
