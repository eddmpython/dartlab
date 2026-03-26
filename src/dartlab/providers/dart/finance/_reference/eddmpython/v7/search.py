"""FinanceSearch v7 - 표준계정코드 매핑 통합 (독립 버전)

v6에서 완전 독립된 구현.
_dataLoader를 사용하여 데이터 로딩/캐싱/정규화 처리.

## 핵심 기능
1. v6 정규화 데이터 사용 (stdAccountNm 기반)
2. 표준계정 매핑 레이어 추가 (standardAccounts.json)
3. snakeId 기반 전 종목 비교

## 사용법
```python
fs = FinanceSearch()

# 기존 기능 (정규화된 시계열)
df = fs.timeseries("005930", sjDiv="IS")

# v7 신규: 표준 ID로 조회
df = fs.timeseriesStandard("005930", sjDiv="IS")
# 새 컬럼: standardId, standardCode

# v7 신규: 전 종목 비교 (표준 ID 기준)
df = fs.compareByStandardId("operating_profit", year="2023")
```
"""

from pathlib import Path
from typing import Any, Dict, List

import polars as pl
from core.dart.searchDart.finance._dataLoader import FinanceDataLoader

from .standardMapping import StandardMapper


class FinanceSearch:
    """FinanceSearch v7 - 표준계정코드 매핑 통합

    _dataLoader 기반 독립 구현 + 표준계정 매핑 레이어
    """

    def __init__(self, dataDir: str | Path = None):
        self._loader = FinanceDataLoader(dataDir)
        self._mapper = StandardMapper()

    @property
    def loader(self) -> FinanceDataLoader:
        """데이터 로더"""
        return self._loader

    @property
    def mapper(self) -> StandardMapper:
        """표준계정 매퍼"""
        return self._mapper

    @property
    def lf(self) -> pl.LazyFrame:
        """정규화된 LazyFrame (v6 호환)"""
        return self._loader.lf

    @property
    def rawLf(self) -> pl.LazyFrame:
        """원본 LazyFrame"""
        return self._loader.rawLf

    def timeseries(
        self, company: str | List[str], sjDiv: str = None, account: str = None, matchType: str = "contains"
    ) -> pl.DataFrame:
        """시계열 데이터 (피벗) - v6 호환"""
        return self._loader.timeseries(company, sjDiv, account, matchType)

    def _addStandardMapping(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """표준계정 매핑 컬럼 추가

        Args:
            lf: v6 정규화된 LazyFrame

        Returns:
            standardId, standardCode 컬럼이 추가된 LazyFrame
        """
        # 고유 계정명 수집
        df = lf.collect()
        uniqueNames = df["stdAccountNm"].unique().to_list()

        # 매핑
        mappings = self._mapper.mapBatch([n for n in uniqueNames if n])

        # 매핑 테이블 생성
        mappingData = []
        for name, result in mappings.items():
            mappingData.append(
                {
                    "stdAccountNm": name,
                    "standardId": result.snakeId,
                    "standardCode": result.code,
                    "mappingSource": result.source,
                    "mappingConfidence": result.confidence,
                }
            )

        if not mappingData:
            # 빈 매핑이면 null 컬럼 추가
            return df.lazy().with_columns(
                [
                    pl.lit(None).alias("standardId"),
                    pl.lit(None).alias("standardCode"),
                    pl.lit("none").alias("mappingSource"),
                    pl.lit(0.0).alias("mappingConfidence"),
                ]
            )

        mappingDf = pl.DataFrame(mappingData)

        # 조인
        resultDf = df.join(mappingDf, on="stdAccountNm", how="left")

        return resultDf.lazy()

    @property
    def lfStandard(self) -> pl.LazyFrame:
        """표준계정 매핑이 적용된 LazyFrame

        v6 정규화 + standardId, standardCode 컬럼 추가
        """
        return self._addStandardMapping(self.lf)

    def timeseriesStandard(
        self, company: str | List[str], sjDiv: str = None, account: str = None, matchType: str = "contains"
    ) -> pl.DataFrame:
        """표준계정 ID가 포함된 시계열 데이터

        Args:
            company: 종목코드 또는 종목코드 리스트
            sjDiv: 재무제표 종류 (IS, BS, CF 등)
            account: 계정명 필터
            matchType: 매칭 방식 ('contains' 또는 'exact')

        Returns:
            표준 ID가 포함된 피벗 DataFrame
        """
        if isinstance(company, str):
            companies = [company]
        else:
            companies = company

        lf = self.lfStandard.filter(pl.col("stock_code").is_in(companies))

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        if account:
            if matchType == "exact":
                lf = lf.filter(pl.col("stdAccountNm") == account)
            else:
                lf = lf.filter(pl.col("stdAccountNm").str.contains(account))

        df = lf.collect()
        return self._pivotStandard(df)

    def _pivotStandard(self, df: pl.DataFrame) -> pl.DataFrame:
        """표준 ID 포함 피벗

        기존 _pivot에 standardId, standardCode 추가
        """
        if df.is_empty():
            return pl.DataFrame()

        # 기간 정렬
        periods = df.sort(["bsns_year", "_qOrd"])["period"].unique(maintain_order=True).to_list()

        # 메타데이터 집계
        metaDf = df.group_by(["stock_code", "sj_div", "stdAccountNm"]).agg(
            [
                pl.col("ord").mode().first().alias("modeOrd"),
                pl.col("normalizedId").mode().first().alias("normalizedId"),
                pl.col("corp_name").first().alias("corp_name"),
                pl.col("standardId").first().alias("standardId"),
                pl.col("standardCode").first().alias("standardCode"),
                pl.col("mappingConfidence").first().alias("mappingConfidence"),
            ]
        )

        # 피벗
        pivotDf = df.select(
            ["stock_code", "sj_div", pl.col("stdAccountNm").alias("accountNm"), "period", "thstrm_amount"]
        )

        resultDf = pivotDf.pivot(
            on="period", index=["stock_code", "sj_div", "accountNm"], values="thstrm_amount", aggregate_function="first"
        )

        # 조인
        resultDf = resultDf.join(
            metaDf.rename({"stdAccountNm": "accountNm"}), on=["stock_code", "sj_div", "accountNm"], how="left"
        )

        # 컬럼 순서 정리
        metaCols = [
            "stock_code",
            "corp_name",
            "sj_div",
            "standardId",
            "standardCode",
            "normalizedId",
            "accountNm",
            "mappingConfidence",
            "modeOrd",
        ]
        existingPeriods = [p for p in periods if p in resultDf.columns]
        existingMeta = [c for c in metaCols if c in resultDf.columns]
        resultDf = resultDf.select(existingMeta + existingPeriods)
        resultDf = resultDf.sort(["stock_code", "sj_div", "modeOrd"], nulls_last=True)

        return resultDf

    def compareByStandardId(
        self, standardId: str, sjDiv: str = None, year: str = None, quarter: str = None, limit: int = 50
    ) -> pl.DataFrame:
        """표준 ID 기준 전 종목 비교

        Args:
            standardId: 표준계정 snakeId (예: 'operating_profit')
            sjDiv: 재무제표 종류
            year: 연도 필터
            quarter: 분기 필터 (예: '4분기')
            limit: 최대 결과 수

        Returns:
            전 종목 비교 DataFrame
        """
        lf = self.lfStandard.filter(pl.col("standardId") == standardId)

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)
        if year:
            lf = lf.filter(pl.col("bsns_year") == year)
        if quarter:
            lf = lf.filter(pl.col("reprt_nm") == quarter)

        df = lf.select(["corp_name", "stock_code", "period", "stdAccountNm", "standardId", "thstrm_amount"]).collect()

        if df.is_empty():
            return pl.DataFrame({"error": [f"'{standardId}' 데이터를 찾을 수 없습니다"]})

        # 최신 기간 기준
        latestPeriod = df.sort("period", descending=True)["period"][0]
        df = df.filter(pl.col("period") == latestPeriod)

        # 종목별 집계
        df = df.group_by(["corp_name", "stock_code"]).agg(
            [
                pl.col("thstrm_amount").first().alias("amount"),
                pl.col("stdAccountNm").first().alias("accountNm"),
                pl.col("period").first().alias("period"),
            ]
        )

        # 정렬 및 제한
        df = df.sort("amount", descending=True, nulls_last=True)
        df = df.with_columns(pl.arange(1, df.height + 1).alias("rank"))

        return df.select(["rank", "corp_name", "stock_code", "accountNm", "period", "amount"]).head(limit)

    def getMatchingStats(self, stockCode: str = None) -> Dict[str, Any]:
        """매핑 통계

        Args:
            stockCode: 특정 종목만 분석 (None이면 전체)

        Returns:
            통계 딕셔너리
        """
        if stockCode:
            lf = self.lfStandard.filter(pl.col("stock_code") == stockCode)
        else:
            lf = self.lfStandard

        df = lf.select(["stdAccountNm", "mappingSource", "mappingConfidence"]).unique().collect()

        total = len(df)
        standard = len(df.filter(pl.col("mappingSource") == "standard"))
        synonym = len(df.filter(pl.col("mappingSource") == "synonym"))
        unmatched = len(df.filter(pl.col("mappingSource") == "none"))

        return {
            "total": total,
            "matchedStandard": standard,
            "matchedSynonym": synonym,
            "unmatched": unmatched,
            "matchRate": (standard + synonym) / total * 100 if total > 0 else 0,
            "standardRate": standard / total * 100 if total > 0 else 0,
            "synonymRate": synonym / total * 100 if total > 0 else 0,
        }

    def getCoreAccountsMapping(self, stockCode: str) -> pl.DataFrame:
        """핵심 계정 매핑 상태 확인

        Args:
            stockCode: 종목코드

        Returns:
            핵심 계정 매핑 상태 DataFrame
        """
        CORE_ACCOUNTS = [
            "자산총계",
            "부채총계",
            "자본총계",
            "유동자산",
            "비유동자산",
            "유동부채",
            "비유동부채",
            "현금및현금성자산",
            "매출채권",
            "재고자산",
            "유형자산",
            "무형자산",
            "자본금",
            "이익잉여금",
            "매출액",
            "매출원가",
            "매출총이익",
            "판매비와관리비",
            "영업이익",
            "금융수익",
            "금융비용",
            "법인세비용",
            "당기순이익",
            "영업활동현금흐름",
            "투자활동현금흐름",
            "재무활동현금흐름",
        ]

        df = (
            self.lfStandard.filter(pl.col("stock_code") == stockCode)
            .select(["stdAccountNm", "standardId", "standardCode", "mappingSource"])
            .unique()
            .collect()
        )

        results = []
        for core in CORE_ACCOUNTS:
            normalized = core.replace(" ", "")
            row = df.filter(pl.col("stdAccountNm").str.replace_all(" ", "") == normalized)

            if not row.is_empty():
                results.append(
                    {
                        "coreAccount": core,
                        "stdAccountNm": row["stdAccountNm"][0],
                        "standardId": row["standardId"][0],
                        "mappingSource": row["mappingSource"][0],
                        "status": "matched" if row["standardId"][0] else "unmatched",
                    }
                )
            else:
                results.append(
                    {
                        "coreAccount": core,
                        "stdAccountNm": None,
                        "standardId": None,
                        "mappingSource": None,
                        "status": "missing",
                    }
                )

        return pl.DataFrame(results)

    # ========== v6 호환 메서드들 ==========

    def byAccount(
        self, account: str = None, normalizedId: str = None, matchType: str = "contains", sjDiv: str = None
    ) -> pl.DataFrame:
        """계정 기준 전체 종목 조회 (v6 호환)"""
        lf = self.lf

        if normalizedId:
            if matchType == "exact":
                lf = lf.filter(pl.col("normalizedId") == normalizedId)
            else:
                lf = lf.filter(pl.col("normalizedId").str.contains(normalizedId))
        elif account:
            if matchType == "exact":
                lf = lf.filter(pl.col("stdAccountNm") == account)
            else:
                lf = lf.filter(pl.col("stdAccountNm").str.contains(account))

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        df = lf.collect()
        return self._loader._pivot(df)

    def filter(
        self, company: str = None, sjDiv: str = None, account: str = None, matchType: str = "contains"
    ) -> pl.LazyFrame:
        """조건 필터링 (v6 호환)"""
        lf = self.lf

        if company:
            lf = lf.filter(pl.col("stock_code") == company)
        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        if account:
            if matchType == "exact":
                lf = lf.filter(pl.col("stdAccountNm") == account)
            else:
                lf = lf.filter(pl.col("stdAccountNm").str.contains(account))

        return lf

    def getAccountList(self, sjDiv: str = None) -> pl.DataFrame:
        """사용 가능한 계정 목록 (v6 호환)"""
        lf = self.lf.select(["sj_div", "stdAccountNm", "normalizedId"]).unique()

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        return lf.sort(["sj_div", "stdAccountNm"]).collect()

    def getCorpList(self) -> pl.DataFrame:
        """사용 가능한 기업 목록 (v6 호환)"""
        return self.lf.select(["corp_name", "stock_code"]).unique().sort("corp_name").collect()

    def rebuildCache(self):
        """캐시 강제 재생성"""
        self._loader.rebuildCache()

    def clearCache(self):
        """캐시 삭제"""
        self._loader.clearCache()
