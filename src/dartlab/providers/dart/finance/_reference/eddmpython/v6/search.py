"""DART 재무 데이터 통합 검색 클래스 v6

## v6 신규 기능 (v5 대비)
1. 계정 계층구조 추가 (account_level, parent_account, formula)
2. 신뢰도 메트릭 (id_confidence, name_confidence, confidence_score)
3. 데이터 검증 레이어 (품질 점수, 공식 검증)
4. 확장된 동의어 테이블 (806개 다중 ID 문제 개선)

## v5 특징 (유지)
- v4 FinanceData 기반 (캐시, 정규화)
- 3가지 데이터 접근 방식 통합:
  1. rawLf: 원본 데이터 조회
  2. lf: 정규화된 LazyFrame (계층/신뢰도 정보 포함)
  3. timeseries(): 피벗된 시계열
- LLM 검색 기능 (안전한 함수 호출 방식):
  - search(): 계정/기업/기간 조건 검색
  - ask(): 자연어 질의 → 함수 호출 → 결과 해석

## 사용법
```python
fs = FinanceSearch()

# 정규화 데이터 (계층 정보 포함)
df = fs.lf.filter(pl.col("stock_code") == "005930").collect()
# 새 컬럼: account_level, parent_account, formula, confidence_score

# 데이터 검증
from .validator import FinanceValidator
validator = FinanceValidator()
quality = validator.calculate_quality_score(fs.lf, "005930")

# 동의어 분석
from .synonyms import SynonymDetector
detector = SynonymDetector(fs.lf)
coverage = detector.analyze_coverage()
```
"""

import json
import re
from pathlib import Path

import polars as pl
from core.paths import DATA_DIR

# v6: 확장된 config 사용
from .config import ACCOUNT_NAME_SYNONYMS, COLUMN_MAPPING, COLUMN_ORDER, HIDDEN_COLUMNS, ID_SYNONYMS, NUMERIC_COLS
from .hierarchy import enrich_with_hierarchy

FUNCTION_SCHEMAS = {
    "getCompanyTimeseries": {
        "description": "특정 종목의 재무제표 시계열 데이터 조회 (분기별 피벗)",
        "parameters": {
            "company": {"type": "string", "description": "종목코드 또는 회사명", "required": True},
            "sjDiv": {
                "type": "string",
                "description": "재무제표 종류: IS(손익계산서), BS(재무상태표), CIS(포괄손익계산서), CF(현금흐름표)",
                "enum": ["IS", "BS", "CIS", "CF", "SCE"],
            },
            "account": {"type": "string", "description": "계정명 필터 (예: 매출액, 영업이익)"},
        },
    },
    "compareByAccount": {
        "description": "특정 계정을 기준으로 여러 종목 비교",
        "parameters": {
            "account": {"type": "string", "description": "계정명 (예: 매출액, 영업이익)", "required": True},
            "sjDiv": {"type": "string", "description": "재무제표 종류", "enum": ["IS", "BS", "CIS", "CF", "SCE"]},
            "limit": {"type": "integer", "description": "결과 수 제한", "default": 20},
        },
    },
    "searchAccounts": {
        "description": "계정명 검색",
        "parameters": {
            "query": {"type": "string", "description": "검색어 (예: 매출, 이익, 자산)", "required": True},
            "corpName": {"type": "string", "description": "회사명 필터"},
            "year": {"type": "string", "description": "연도 필터 (예: 2023)"},
            "sjDiv": {"type": "string", "description": "재무제표 종류", "enum": ["IS", "BS", "CIS", "CF", "SCE"]},
            "limit": {"type": "integer", "description": "결과 수 제한", "default": 50},
        },
    },
    "getAccountList": {
        "description": "사용 가능한 계정 목록 조회",
        "parameters": {
            "sjDiv": {"type": "string", "description": "재무제표 종류 필터", "enum": ["IS", "BS", "CIS", "CF", "SCE"]}
        },
    },
    "getCorpList": {"description": "사용 가능한 기업 목록 조회", "parameters": {}},
    "getYoYGrowth": {
        "description": "전년동기대비 성장률 계산",
        "parameters": {
            "company": {"type": "string", "description": "종목코드 또는 회사명", "required": True},
            "account": {"type": "string", "description": "계정명 (예: 매출액)", "required": True},
            "sjDiv": {"type": "string", "description": "재무제표 종류", "enum": ["IS", "BS", "CIS", "CF", "SCE"]},
        },
    },
    "getRanking": {
        "description": "특정 계정 기준 기업 순위",
        "parameters": {
            "account": {"type": "string", "description": "계정명 (예: 매출액)", "required": True},
            "year": {"type": "string", "description": "연도 (예: 2023)"},
            "quarter": {"type": "string", "description": "분기 (예: 1분기, 4분기)"},
            "sjDiv": {"type": "string", "description": "재무제표 종류", "enum": ["IS", "BS", "CIS", "CF", "SCE"]},
            "limit": {"type": "integer", "description": "상위 N개", "default": 10},
            "ascending": {"type": "boolean", "description": "오름차순 정렬", "default": False},
        },
    },
}


class FinanceSearch:
    """DART 재무 데이터 통합 검색 클래스 v5"""

    QUARTER_ORDER = {"1분기": 1, "2분기": 2, "3분기": 3, "4분기": 4}
    PREPARED_FILENAME = "prepared.parquet"

    def __init__(self, dataDir: str | Path = None):
        if dataDir:
            self._financeDir = Path(dataDir)
        else:
            currentFile = Path(__file__).resolve()
            projectRoot = self._findProjectRoot(currentFile)
            baseDir = DATA_DIR / "dartData"
            self._financeDir = baseDir / "finance"

        self._cacheDir = self._financeDir / "_cache"
        self._rawLf = None
        self._preparedLf = None

    def _findProjectRoot(self, currentFile: Path) -> Path:
        for parent in currentFile.parents:
            if parent.name == "eddmpython" or (parent / "pyproject.toml").exists():
                return parent
        return currentFile.parents[-1]

    def _ensureCacheDir(self):
        self._cacheDir.mkdir(parents=True, exist_ok=True)

    def _getOriginalMaxMtime(self) -> float:
        files = list(self._financeDir.glob("*.parquet"))
        if not files:
            return 0.0
        return max(f.stat().st_mtime for f in files)

    def _needsRebuild(self) -> bool:
        preparedPath = self._cacheDir / self.PREPARED_FILENAME
        if not preparedPath.exists():
            return True
        originalMaxMtime = self._getOriginalMaxMtime()
        preparedMtime = preparedPath.stat().st_mtime
        return originalMaxMtime > preparedMtime

    @property
    def rawLf(self) -> pl.LazyFrame:
        """원본 LazyFrame (숫자캐스팅 + 공백제거만)"""
        if self._rawLf is None:
            self._rawLf = self._buildRawLf()
        return self._rawLf

    def getRawLf(self, koreanCols: bool = False, hideColumns: bool = False, orderColumns: bool = True) -> pl.LazyFrame:
        """원본 LazyFrame (옵션 적용)"""
        lf = self.rawLf
        schema = lf.collect_schema()
        currentCols = list(schema.keys())

        if hideColumns:
            currentCols = [c for c in currentCols if c not in HIDDEN_COLUMNS]

        if orderColumns:
            ordered = [c for c in COLUMN_ORDER if c in currentCols]
            remaining = [c for c in currentCols if c not in COLUMN_ORDER]
            currentCols = ordered + remaining

        lf = lf.select(currentCols)

        if koreanCols:
            renameMap = {col: COLUMN_MAPPING.get(col, col) for col in currentCols}
            lf = lf.rename(renameMap)

        return lf

    def _buildRawLf(self) -> pl.LazyFrame:
        files = list(self._financeDir.glob("*.parquet"))
        if not files:
            schema = {col: pl.Utf8 for col in COLUMN_MAPPING.keys()}
            for col in NUMERIC_COLS:
                schema[col] = pl.Float64
            return pl.DataFrame(schema=schema).lazy()

        pattern = str(self._financeDir / "*.parquet")
        lf = pl.scan_parquet(pattern, missing_columns="insert", extra_columns="ignore")

        castExprs = [pl.col(col).replace("", None).cast(pl.Float64, strict=False).alias(col) for col in NUMERIC_COLS]
        lf = lf.with_columns(castExprs)

        lf = lf.with_columns(pl.col("account_nm").str.replace_all(r"\s+", "").alias("account_nm"))

        return lf

    def _buildMappingTables(self, lf: pl.LazyFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
        mappingLf = lf.select(["sj_div", "account_id", "account_nm"])

        mappingLf = mappingLf.with_columns(
            pl.col("account_id")
            .str.replace("^ifrs-full_", "")
            .str.replace("^ifrs_", "")
            .str.replace("^dart_", "")
            .alias("normalizedId")
        )

        mappingLf = mappingLf.filter(
            pl.col("normalizedId").is_not_null()
            & pl.col("normalizedId").ne("")
            & pl.col("normalizedId").ne("-표준계정코드 미사용-")
        )

        mappingDf = mappingLf.collect()

        nameToIdDf = mappingDf.group_by(["sj_div", "account_nm"]).agg(
            [
                pl.col("normalizedId").mode().first().alias("inferredId"),
            ]
        )

        idToNameDf = mappingDf.group_by(["sj_div", "normalizedId"]).agg(
            [
                pl.col("account_nm").mode().first().alias("stdAccountNm"),
            ]
        )

        return nameToIdDf, idToNameDf

    def _applyNormalization(self, lf: pl.LazyFrame, nameToIdDf: pl.DataFrame, idToNameDf: pl.DataFrame) -> pl.LazyFrame:
        lf = lf.with_columns(
            pl.col("account_id")
            .str.replace("^ifrs-full_", "")
            .str.replace("^ifrs_", "")
            .str.replace("^dart_", "")
            .alias("normalizedIdRaw")
        )

        lf = lf.join(
            nameToIdDf.lazy().select(["sj_div", "account_nm", "inferredId"]), on=["sj_div", "account_nm"], how="left"
        )

        lf = lf.with_columns(
            pl.when(
                pl.col("normalizedIdRaw").is_null()
                | (pl.col("normalizedIdRaw") == "")
                | (pl.col("normalizedIdRaw") == "-표준계정코드 미사용-")
            )
            .then(pl.coalesce(pl.col("inferredId"), pl.col("account_nm")))
            .otherwise(pl.col("normalizedIdRaw"))
            .alias("normalizedId")
        )

        lf = lf.with_columns(pl.col("normalizedId").replace(ID_SYNONYMS).alias("normalizedId"))

        lf = lf.join(
            idToNameDf.lazy().select(["sj_div", "normalizedId", "stdAccountNm"]),
            on=["sj_div", "normalizedId"],
            how="left",
        )

        lf = lf.with_columns(pl.coalesce(pl.col("stdAccountNm"), pl.col("account_nm")).alias("stdAccountNm"))

        lf = lf.with_columns(pl.col("stdAccountNm").replace(ACCOUNT_NAME_SYNONYMS).alias("stdAccountNm"))

        lf = lf.drop(["normalizedIdRaw", "inferredId"])

        return lf

    def _applyCfsPriority(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        lf = lf.with_columns(pl.when(pl.col("fs_div") == "CFS").then(1).otherwise(2).alias("_fsPriority"))

        lf = lf.sort(["stock_code", "bsns_year", "reprt_nm", "sj_div", "normalizedId", "_fsPriority"])
        lf = lf.unique(["stock_code", "bsns_year", "reprt_nm", "sj_div", "normalizedId"], keep="first")
        lf = lf.drop("_fsPriority")

        return lf

    def _normalizeQ4(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        lf = lf.with_columns(pl.col("reprt_nm").replace(self.QUARTER_ORDER).alias("_qOrd"))

        groupKey = ["stock_code", "bsns_year", "sj_div", "normalizedId"]
        lf = lf.sort(groupKey + ["_qOrd"])

        lf = lf.with_columns(pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd"))

        lf = lf.with_columns(
            [
                pl.when(
                    pl.col("sj_div").is_in(["IS", "CIS"])
                    & (pl.col("reprt_nm") == "4분기")
                    & pl.col("thstrm_add_amount").is_null()
                )
                .then(pl.col("thstrm_amount"))
                .otherwise(pl.col("thstrm_add_amount"))
                .alias("thstrm_add_amount"),
            ]
        )

        lf = lf.with_columns(pl.col("thstrm_add_amount").shift(1).over(groupKey).alias("_prevAdd"))

        lf = lf.with_columns(
            [
                pl.when(~pl.col("sj_div").is_in(["IS", "CIS"]))
                .then(pl.col("thstrm_amount"))
                .when((pl.col("reprt_nm") == "1분기") & pl.col("thstrm_amount").is_null())
                .then(pl.col("thstrm_add_amount"))
                .when(
                    (pl.col("reprt_nm") != "1분기")
                    & (pl.col("thstrm_amount").is_null() | (pl.col("thstrm_amount") == pl.col("thstrm_add_amount")))
                )
                .then(pl.col("thstrm_add_amount") - pl.col("_prevAdd").fill_null(0))
                .when((pl.col("reprt_nm") == "4분기") & pl.col("thstrm_add_amount").is_null())
                .then(pl.col("thstrm_amount") - pl.col("_prevAdd").fill_null(0))
                .otherwise(pl.col("thstrm_amount"))
                .alias("thstrm_amount"),
            ]
        )

        lf = lf.drop("_prevAdd")

        return lf

    def _addPeriodColumn(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        lf = lf.with_columns(
            [
                (pl.col("bsns_year") + "_" + pl.col("reprt_nm").str.replace("분기", "Q")).alias("period"),
            ]
        )
        return lf

    def _addHierarchyInfo(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """v6: 계층 정보 추가

        Returns:
            계층 정보가 추가된 LazyFrame (account_level, parent_account, formula 컬럼)
        """
        return enrich_with_hierarchy(lf)

    def _addConfidenceMetrics(self, lf: pl.LazyFrame) -> pl.LazyFrame:
        """v6: 신뢰도 메트릭 추가

        Returns:
            신뢰도 메트릭이 추가된 LazyFrame (id_confidence, name_confidence, confidence_score)
        """
        # ID 추론 신뢰도 계산을 위한 통계 수집
        lf = lf.with_columns(
            [
                # ID가 원본에 있었는지 (normalizedIdRaw가 있었는지는 이미 처리됨)
                # account_id가 null이거나 비어있거나 "-표준계정코드 미사용-"인 경우 추론됨
                pl.when(
                    pl.col("account_id").is_null()
                    | (pl.col("account_id") == "")
                    | (pl.col("account_id") == "-표준계정코드 미사용-")
                )
                .then(0.7)  # 추론된 경우 70% 신뢰도
                .otherwise(1.0)  # 원본 ID 사용 시 100%
                .alias("id_confidence"),
                # 계정명 표준화 신뢰도
                pl.when(pl.col("account_nm") != pl.col("stdAccountNm"))
                .then(0.85)  # 동의어 매핑된 경우 85%
                .otherwise(1.0)  # 원본 그대로 100%
                .alias("name_confidence"),
            ]
        )

        # 종합 신뢰도 = ID 신뢰도 × 계정명 신뢰도
        lf = lf.with_columns([(pl.col("id_confidence") * pl.col("name_confidence")).alias("confidence_score")])

        return lf

    def _buildPrepared(self) -> pl.LazyFrame:
        self._ensureCacheDir()
        preparedPath = self._cacheDir / self.PREPARED_FILENAME

        rawLf = self._buildRawLf()

        rawLf = rawLf.filter(pl.col("bsns_year") != "2015")

        nameToIdDf, idToNameDf = self._buildMappingTables(rawLf)

        lf = self._applyNormalization(rawLf, nameToIdDf, idToNameDf)

        lf = self._applyCfsPriority(lf)

        lf = self._normalizeQ4(lf)

        lf = self._addPeriodColumn(lf)

        # v6: 계층 정보 추가
        lf = self._addHierarchyInfo(lf)

        # v6: 신뢰도 메트릭 추가
        lf = self._addConfidenceMetrics(lf)

        df = lf.collect()
        df.write_parquet(preparedPath)

        return pl.scan_parquet(preparedPath)

    @property
    def lf(self) -> pl.LazyFrame:
        """정규화된 LazyFrame (자동 캐시)"""
        if self._preparedLf is None or self._needsRebuild():
            preparedPath = self._cacheDir / self.PREPARED_FILENAME
            if self._needsRebuild():
                self._preparedLf = self._buildPrepared()
            else:
                self._preparedLf = pl.scan_parquet(preparedPath)
        return self._preparedLf

    def _pivot(self, df: pl.DataFrame) -> pl.DataFrame:
        if df.is_empty():
            return pl.DataFrame()

        periods = df.sort(["bsns_year", "_qOrd"])["period"].unique(maintain_order=True).to_list()

        metaDf = df.group_by(["stock_code", "sj_div", "stdAccountNm"]).agg(
            [
                pl.col("ord").mode().first().alias("modeOrd"),
                pl.col("normalizedId").mode().first().alias("normalizedId"),
                pl.col("corp_name").first().alias("corp_name"),
            ]
        )

        pivotDf = df.select(
            ["stock_code", "sj_div", pl.col("stdAccountNm").alias("accountNm"), "period", "thstrm_amount"]
        )

        resultDf = pivotDf.pivot(
            on="period", index=["stock_code", "sj_div", "accountNm"], values="thstrm_amount", aggregate_function="first"
        )

        resultDf = resultDf.join(
            metaDf.rename({"stdAccountNm": "accountNm"}), on=["stock_code", "sj_div", "accountNm"], how="left"
        )

        metaCols = ["stock_code", "corp_name", "sj_div", "normalizedId", "accountNm", "modeOrd"]
        existingPeriods = [p for p in periods if p in resultDf.columns]
        resultDf = resultDf.select(metaCols + existingPeriods)
        resultDf = resultDf.sort(["stock_code", "sj_div", "modeOrd"], nulls_last=True)

        return resultDf

    def timeseries(
        self, company: str | list[str], sjDiv: str = None, account: str = None, matchType: str = "contains"
    ) -> pl.DataFrame:
        """시계열 데이터 (피벗)"""
        if isinstance(company, str):
            companies = [company]
        else:
            companies = company

        lf = self.lf.filter(pl.col("stock_code").is_in(companies))

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        if account:
            if matchType == "exact":
                lf = lf.filter(pl.col("stdAccountNm") == account)
            else:
                lf = lf.filter(pl.col("stdAccountNm").str.contains(account))

        df = lf.collect()
        return self._pivot(df)

    def byAccount(
        self, account: str = None, normalizedId: str = None, matchType: str = "contains", sjDiv: str = None
    ) -> pl.DataFrame:
        """계정 기준 전체 종목 조회 (계정명 또는 normalizedId)"""
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
        return self._pivot(df)

    def filter(
        self,
        company: str = None,
        sjDiv: str = None,
        account: str = None,
        matchType: str = "contains",
        koreanCols: bool = False,
        hideColumns: bool = False,
    ) -> pl.LazyFrame:
        """조건 필터링 (LazyFrame)"""
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

        if hideColumns:
            cols = [c for c in lf.collect_schema().keys() if c not in HIDDEN_COLUMNS]
            lf = lf.select(cols)

        if koreanCols:
            renameMap = {col: COLUMN_MAPPING.get(col, col) for col in lf.collect_schema().keys()}
            lf = lf.rename(renameMap)

        return lf

    def search(
        self,
        query: str = None,
        corpName: str = None,
        stockCode: str = None,
        year: str = None,
        quarter: str = None,
        sjDiv: str = None,
        limit: int = 100,
    ) -> pl.DataFrame:
        """계정 검색 (LLM용)"""
        lf = self.lf

        if stockCode:
            lf = lf.filter(pl.col("stock_code") == stockCode)
        elif corpName:
            lf = lf.filter(pl.col("corp_name").str.contains(corpName))

        if year:
            lf = lf.filter(pl.col("bsns_year") == year)

        if quarter:
            lf = lf.filter(pl.col("reprt_nm") == quarter)

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        if query:
            lf = lf.filter(pl.col("stdAccountNm").str.contains(query))

        selectCols = [
            "corp_name",
            "stock_code",
            "bsns_year",
            "reprt_nm",
            "period",
            "sj_div",
            "stdAccountNm",
            "thstrm_amount",
        ]

        return lf.select(selectCols).limit(limit).collect()

    def _buildContext(self, df: pl.DataFrame, maxChars: int = 6000) -> str:
        """검색 결과를 LLM 컨텍스트로 변환"""
        if df.is_empty():
            return "관련 데이터를 찾을 수 없습니다."

        contexts = []
        totalChars = 0

        grouped = df.group_by(["corp_name", "stock_code", "sj_div"]).agg(
            [
                pl.col("stdAccountNm").alias("accounts"),
                pl.col("period").alias("periods"),
                pl.col("thstrm_amount").alias("amounts"),
            ]
        )

        for row in grouped.iter_rows(named=True):
            corpName = row["corp_name"]
            sjDiv = row["sj_div"]
            accounts = row["accounts"]
            periods = row["periods"]
            amounts = row["amounts"]

            header = f"[{corpName} / {sjDiv}]"
            lines = [header]

            for acc, period, amt in zip(accounts, periods, amounts):
                amtStr = f"{amt:,.0f}" if amt else "-"
                lines.append(f"  {acc} ({period}): {amtStr}원")

            docText = "\n".join(lines)

            if totalChars + len(docText) > maxChars:
                break

            contexts.append(docText)
            totalChars += len(docText)

        return "\n\n".join(contexts)

    def ask(self, question: str, corpName: str = None, stockCode: str = None, maxIterations: int = 3) -> str:
        """자연어 질의 → 함수 호출 → 결과 해석"""
        try:
            from agents.codeAgent import getLlmResponse as llmChat

            def llmManager_chat(prompt, temperature):
                return llmChat(prompt)

            llmManager = type("obj", (object,), {"chat": llmManager_chat})()
        except ImportError:
            return "LLM 기능을 사용하려면 agents.codeAgent를 설정하세요."

        functionSchemas = self._getFunctionSchemas()

        planPrompt = f"""당신은 DART 재무제표 분석 전문가입니다.
사용자의 질문을 분석하여 적절한 함수를 호출하세요.

{functionSchemas}

## 질문
{question}

## 힌트
{"- 회사: " + (corpName or stockCode) if corpName or stockCode else ""}

## 응답 형식 (JSON만 출력)
{{
    "function": "함수명",
    "params": {{"파라미터명": "값", ...}},
    "reason": "이 함수를 선택한 이유"
}}

JSON만 출력하세요. 다른 텍스트는 출력하지 마세요."""

        try:
            planResponse = llmManager.chat(planPrompt, temperature=0)
            jsonMatch = re.search(r"\{[\s\S]*\}", planResponse)
            if not jsonMatch:
                return f"함수 선택 실패: {planResponse}"

            plan = json.loads(jsonMatch.group())
            funcName = plan.get("function")
            params = plan.get("params", {})

            if corpName and "corpName" in FUNCTION_SCHEMAS.get(funcName, {}).get("parameters", {}):
                params.setdefault("corpName", corpName)
            if corpName and "company" in FUNCTION_SCHEMAS.get(funcName, {}).get("parameters", {}):
                params.setdefault("company", corpName)
            if stockCode and "stockCode" in FUNCTION_SCHEMAS.get(funcName, {}).get("parameters", {}):
                params.setdefault("stockCode", stockCode)
            if stockCode and "company" in FUNCTION_SCHEMAS.get(funcName, {}).get("parameters", {}):
                params.setdefault("company", stockCode)

            resultDf = self._callFunction(funcName, params)
            resultStr = self._formatResultForLLM(resultDf)

            answerPrompt = f"""당신은 DART 재무제표 분석 전문가입니다.
사용자의 질문에 대해 아래 데이터를 바탕으로 답변하세요.

## 질문
{question}

## 호출한 함수
{funcName}({params})

## 결과 데이터
{resultStr}

## 답변 규칙
- 데이터에 있는 정보만 사용하세요
- 출처(기업명, 기간)를 명시하세요
- 시계열 데이터는 마크다운 테이블로 정리하세요
- 금액은 단위(원)를 명시하세요
- 간결하고 정확하게 답변하세요

## 답변"""

            answer = llmManager.chat(answerPrompt, temperature=0)
            return answer

        except json.JSONDecodeError as e:
            return f"JSON 파싱 오류: {e}\n응답: {planResponse}"
        except Exception as e:
            return f"오류 발생: {str(e)}"

    def getAccountList(self, sjDiv: str = None) -> pl.DataFrame:
        """사용 가능한 계정 목록"""
        lf = self.lf.select(["sj_div", "stdAccountNm", "normalizedId"]).unique()

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)

        return lf.sort(["sj_div", "stdAccountNm"]).collect()

    def getCorpList(self) -> pl.DataFrame:
        """사용 가능한 기업 목록"""
        return self.lf.select(["corp_name", "stock_code"]).unique().sort("corp_name").collect()

    def _resolveCompany(self, company: str) -> str | None:
        """회사명 → 종목코드 변환 (이미 종목코드면 그대로 반환)"""
        if company.isdigit() and len(company) == 6:
            return company
        corpDf = self.getCorpList().filter(pl.col("corp_name").str.contains(company))
        if corpDf.is_empty():
            return None
        return corpDf["stock_code"][0]

    def getCompanyTimeseries(self, company: str, sjDiv: str = None, account: str = None) -> pl.DataFrame:
        """LLM용: 종목 시계열 조회 (회사명/종목코드 모두 지원)"""
        stockCode = self._resolveCompany(company)
        if stockCode is None:
            return pl.DataFrame({"error": [f"'{company}' 종목을 찾을 수 없습니다"]})
        return self.timeseries(stockCode, sjDiv=sjDiv, account=account)

    def compareByAccount(self, account: str, sjDiv: str = None, limit: int = 20) -> pl.DataFrame:
        """LLM용: 계정 기준 전종목 비교"""
        df = self.byAccount(account=account, sjDiv=sjDiv)
        if df.is_empty():
            return pl.DataFrame({"error": [f"'{account}' 계정을 찾을 수 없습니다"]})
        return df.head(limit)

    def searchAccounts(
        self, query: str, corpName: str = None, year: str = None, sjDiv: str = None, limit: int = 50
    ) -> pl.DataFrame:
        """LLM용: 계정 검색"""
        return self.search(query=query, corpName=corpName, year=year, sjDiv=sjDiv, limit=limit)

    def getYoYGrowth(self, company: str, account: str, sjDiv: str = None) -> pl.DataFrame:
        """LLM용: 전년동기대비 성장률 계산"""
        stockCode = self._resolveCompany(company)
        if stockCode is None:
            return pl.DataFrame({"error": [f"'{company}' 종목을 찾을 수 없습니다"]})

        df = self.timeseries(stockCode, sjDiv=sjDiv, account=account)
        if df.is_empty():
            return pl.DataFrame({"error": [f"'{account}' 계정을 찾을 수 없습니다"]})

        periodCols = [c for c in df.columns if "_" in c and c[0].isdigit()]
        if len(periodCols) < 2:
            return pl.DataFrame({"error": ["성장률 계산에 필요한 데이터가 부족합니다"]})

        growthData = []
        for row in df.iter_rows(named=True):
            accountNm = row.get("accountNm", "")
            for i, period in enumerate(periodCols[1:], 1):
                prevPeriod = periodCols[i - 1]
                currVal = row.get(period)
                prevVal = row.get(prevPeriod)

                if currVal is not None and prevVal is not None and prevVal != 0:
                    growth = ((currVal - prevVal) / abs(prevVal)) * 100
                    growthData.append(
                        {
                            "accountNm": accountNm,
                            "period": period,
                            "prevPeriod": prevPeriod,
                            "currValue": currVal,
                            "prevValue": prevVal,
                            "growthRate": round(growth, 2),
                        }
                    )

        if not growthData:
            return pl.DataFrame({"error": ["성장률 계산 가능한 데이터가 없습니다"]})

        return pl.DataFrame(growthData)

    def getRanking(
        self,
        account: str,
        year: str = None,
        quarter: str = None,
        sjDiv: str = None,
        limit: int = 10,
        ascending: bool = False,
    ) -> pl.DataFrame:
        """LLM용: 계정 기준 기업 순위"""
        lf = self.lf.filter(pl.col("stdAccountNm").str.contains(account))

        if sjDiv:
            lf = lf.filter(pl.col("sj_div") == sjDiv)
        if year:
            lf = lf.filter(pl.col("bsns_year") == year)
        if quarter:
            lf = lf.filter(pl.col("reprt_nm") == quarter)

        df = lf.select(["corp_name", "stock_code", "period", "stdAccountNm", "thstrm_amount"]).collect()

        if df.is_empty():
            return pl.DataFrame({"error": [f"'{account}' 데이터를 찾을 수 없습니다"]})

        latestPeriod = df.sort("period", descending=True)["period"][0]
        df = df.filter(pl.col("period") == latestPeriod)

        df = df.group_by(["corp_name", "stock_code"]).agg(
            [
                pl.col("thstrm_amount").first().alias("amount"),
                pl.col("stdAccountNm").first().alias("accountNm"),
                pl.col("period").first().alias("period"),
            ]
        )

        df = df.sort("amount", descending=not ascending, nulls_last=True)
        df = df.with_columns(pl.arange(1, df.height + 1).alias("rank"))

        return df.select(["rank", "corp_name", "stock_code", "accountNm", "period", "amount"]).head(limit)

    def _callFunction(self, funcName: str, params: dict) -> pl.DataFrame:
        """화이트리스트 함수 실행"""
        allowedFunctions = {
            "getCompanyTimeseries": self.getCompanyTimeseries,
            "compareByAccount": self.compareByAccount,
            "searchAccounts": self.searchAccounts,
            "getAccountList": self.getAccountList,
            "getCorpList": self.getCorpList,
            "getYoYGrowth": self.getYoYGrowth,
            "getRanking": self.getRanking,
        }

        if funcName not in allowedFunctions:
            return pl.DataFrame({"error": [f"'{funcName}'은 허용되지 않는 함수입니다"]})

        try:
            return allowedFunctions[funcName](**params)
        except Exception as e:
            return pl.DataFrame({"error": [f"함수 실행 오류: {str(e)}"]})

    def _formatResultForLLM(self, df: pl.DataFrame, maxRows: int = 30) -> str:
        """DataFrame을 LLM 컨텍스트용 문자열로 변환"""
        if df.is_empty():
            return "데이터가 없습니다."

        if "error" in df.columns:
            return df["error"][0]

        df = df.head(maxRows)
        return df.write_csv()

    def _getFunctionSchemas(self) -> str:
        """LLM에게 제공할 함수 스키마 설명"""
        lines = ["사용 가능한 함수:"]
        for name, schema in FUNCTION_SCHEMAS.items():
            params = []
            for pName, pInfo in schema["parameters"].items():
                required = pInfo.get("required", False)
                pType = pInfo["type"]
                desc = pInfo["description"]
                if "enum" in pInfo:
                    pType = f"enum[{', '.join(pInfo['enum'])}]"
                marker = "*" if required else ""
                params.append(f"    - {pName}{marker}: {pType} - {desc}")

            lines.append(f"\n## {name}")
            lines.append(f"설명: {schema['description']}")
            if params:
                lines.append("파라미터:")
                lines.extend(params)

        return "\n".join(lines)

    def rebuildCache(self):
        """캐시 강제 재생성"""
        self._preparedLf = None
        preparedPath = self._cacheDir / self.PREPARED_FILENAME
        if preparedPath.exists():
            preparedPath.unlink()
        self._buildPrepared()

    def clearCache(self):
        """캐시 삭제"""
        self._preparedLf = None
        if self._cacheDir.exists():
            for f in self._cacheDir.glob("*.parquet"):
                f.unlink()
