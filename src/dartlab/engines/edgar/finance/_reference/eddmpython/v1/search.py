"""
EDGAR 재무 데이터 검색

DartSearch.finance와 동일한 인터페이스:
- getTimeseries: 시계열 재무데이터
- byAccount: 특정 계정 조회
- ranking: 계정별 랭킹
"""

from pathlib import Path

import polars as pl
from core.edgar.config import PERIOD_ORDER, getEdgarDataDir
from core.edgar.getEdgar.v1.edgarFinance import EdgarFinance
from core.edgar.searchEdgar.finance.v1.standardMapping import StandardMapper


class FinanceSearch:
    def __init__(self, dataDir: Path = None):
        if dataDir is None:
            dataDir = getEdgarDataDir()

        self.dataDir = dataDir
        self.edgarFinance = EdgarFinance(dataDir)
        self.mapper = StandardMapper()

    def _extractParentFromPre(self, pre: pl.DataFrame) -> pl.DataFrame:
        preNormalized = pre.with_columns(
            [pl.col("line").cast(pl.Int32, strict=False), pl.col("inpth").cast(pl.Int32, strict=False)]
        )

        preWithParent = []

        for (adsh, stmt), group in preNormalized.group_by(["adsh", "stmt"]):
            sortedGroup = group.sort("line")
            depthStack = {}

            rows = sortedGroup.to_dicts()
            for row in rows:
                depth = row["inpth"]
                tag = row["tag"]

                if depth is None:
                    depth = 0

                if depth == 0:
                    parentTag = None
                    parentLine = None
                else:
                    parentTag = depthStack.get(depth - 1, {}).get("tag")
                    parentLine = depthStack.get(depth - 1, {}).get("line")

                depthStack[depth] = {"tag": tag, "line": row["line"]}

                keysToRemove = [k for k in depthStack.keys() if k > depth]
                for k in keysToRemove:
                    del depthStack[k]

                row["parentTag"] = parentTag
                row["parentLine"] = parentLine
                preWithParent.append(row)

        return pl.DataFrame(preWithParent, infer_schema_length=None)

    def _mergeFactsWithMetadata(self, factsPlDf: pl.DataFrame, sub: pl.DataFrame, pre: pl.DataFrame) -> pl.DataFrame:
        periodToAdsh = sub.select(["adsh", "cik", "fy", "fp", "form", "period"]).with_columns(
            [pl.col("fy").cast(pl.Int32, strict=False), pl.col("fp").cast(pl.Utf8)]
        )

        factsWithAdsh = factsPlDf.join(periodToAdsh, on=["fy", "fp"], how="left")

        preWithParent = self._extractParentFromPre(pre)

        prePrepared = preWithParent.with_columns(
            [pl.col("line").cast(pl.Int32, strict=False), pl.col("inpth").cast(pl.Int32, strict=False)]
        ).select(["adsh", "tag", "version", "stmt", "line", "plabel", "inpth", "parentTag", "parentLine"])

        merged = factsWithAdsh.join(prePrepared, on=["adsh", "tag"], how="left")

        return merged

    def _applyStandardMapping(self, merged: pl.DataFrame) -> pl.DataFrame:
        """표준 매핑 적용 - NumPy 최적화"""
        if merged.is_empty():
            return merged

        n = len(merged)

        tags = merged["tag"].to_numpy()
        plabels = merged["plabel"].to_numpy() if "plabel" in merged.columns else [""] * n
        stmts = merged["stmt"].to_numpy() if "stmt" in merged.columns else [""] * n

        snakeIds = []
        standardCodes = []
        korNames = []
        engNames = []
        standardLevels = []
        standardLines = []
        standardParents = []
        mappingSources = []
        mappingConfidences = []

        for i in range(n):
            tag = tags[i] if tags[i] is not None else ""
            plabel = plabels[i] if plabels[i] is not None else ""
            stmt = stmts[i] if stmts[i] is not None else ""

            result = self.mapper.map(tag, plabel, stmt)

            snakeIds.append(result.snakeId)
            standardCodes.append(result.code)
            korNames.append(result.korName)
            engNames.append(result.engName)
            standardLevels.append(result.level)
            standardLines.append(result.line)
            standardParents.append(result.parent)
            mappingSources.append(result.source)
            mappingConfidences.append(result.confidence)

        return merged.with_columns(
            [
                pl.Series("snakeId", snakeIds),
                pl.Series("standardCode", standardCodes),
                pl.Series("korName", korNames),
                pl.Series("engName", engNames),
                pl.Series("standardLevel", standardLevels),
                pl.Series("standardLine", standardLines),
                pl.Series("standardParent", standardParents),
                pl.Series("mappingSource", mappingSources),
                pl.Series("mappingConfidence", mappingConfidences),
            ]
        )

    def _pivotByStmt(self, final: pl.DataFrame) -> pl.DataFrame:
        if final.is_empty():
            return pl.DataFrame(
                {
                    "report": pl.Series([], dtype=pl.Utf8),
                    "account": pl.Series([], dtype=pl.Utf8),
                    "snakeId": pl.Series([], dtype=pl.Utf8),
                    "korName": pl.Series([], dtype=pl.Utf8),
                    "line": pl.Series([], dtype=pl.Int64),
                    "level": pl.Series([], dtype=pl.Int64),
                }
            )

        final = (
            final.filter(pl.col("fp").is_in(["Q1", "Q2", "Q3", "Q4", "FY"]))
            .with_columns(
                [
                    pl.when(pl.col("form").str.contains("/A"))
                    .then(pl.concat_str([pl.col("fy").cast(pl.Utf8), pl.lit("-"), pl.col("fp"), pl.lit("A")]))
                    .otherwise(pl.concat_str([pl.col("fy").cast(pl.Utf8), pl.lit("-"), pl.col("fp")]))
                    .alias("periodCol"),
                    pl.when(pl.col("frame").is_null()).then(pl.lit(1)).otherwise(pl.lit(0)).alias("frame_priority"),
                ]
            )
            .filter(pl.col("stmt").is_not_null())
        )

        final = final.with_columns(
            [
                pl.coalesce("engName", "plabel", "tag").alias("displayAccount"),
                pl.coalesce("standardLine", "line").alias("displayLine"),
                pl.coalesce("standardLevel", "inpth", pl.lit(2)).alias("displayLevel"),
            ]
        )

        allStmtDfs = []
        periodCols = []

        for stmt in final["stmt"].unique().drop_nulls().to_list():
            stmtDf = final.filter(pl.col("stmt") == stmt)

            accountFixed = (
                stmtDf.sort("filed", descending=True)
                .unique(subset=["displayAccount"], keep="first")
                .select(["displayAccount", "displayLine", "displayLevel", "parentTag", "snakeId", "korName"])
            )

            stmtDf = stmtDf.select(["displayAccount", "val", "periodCol", "filed", "frame_priority"])

            stmtDf = (
                stmtDf.filter(pl.col("frame_priority") == 1)
                .with_columns(
                    [
                        pl.when(pl.col("periodCol").str.ends_with("-FY") | pl.col("periodCol").str.ends_with("-Q1"))
                        .then(pl.lit("max"))
                        .otherwise(pl.lit("min"))
                        .alias("agg_method")
                    ]
                )
                .group_by(["displayAccount", "periodCol"])
                .agg(
                    [
                        pl.when(pl.col("agg_method").first() == "max")
                        .then(pl.col("val").max())
                        .otherwise(pl.col("val").min())
                        .alias("val")
                    ]
                )
            )

            pivotedDf = stmtDf.pivot(values="val", index="displayAccount", on="periodCol", aggregate_function="first")

            pivotedDf = pivotedDf.join(accountFixed, on="displayAccount", how="left")
            pivotedDf = pivotedDf.sort(["displayLine", "displayLevel"])

            currentPeriodCols = [
                c
                for c in pivotedDf.columns
                if c not in ["displayAccount", "displayLine", "displayLevel", "parentTag", "snakeId", "korName"]
            ]

            def parsePeriod(col):
                parts = col.split("-")
                year = int(parts[0])
                period = parts[1]
                order = PERIOD_ORDER.get(period, 0)
                return (year, order)

            currentPeriodCols.sort(key=parsePeriod)
            periodCols = list(set(periodCols) | set(currentPeriodCols))

            pivotedDf = pivotedDf.select(
                ["displayAccount", "displayLine", "displayLevel", "parentTag", "snakeId", "korName"] + currentPeriodCols
            )
            pivotedDf = pivotedDf.with_columns(pl.lit(stmt).alias("report"))

            allStmtDfs.append(pivotedDf)

        if not allStmtDfs:
            return pl.DataFrame()

        combinedDf = pl.concat(allStmtDfs, how="diagonal")

        combinedDf = combinedDf.rename(
            {"displayAccount": "account", "displayLine": "line", "displayLevel": "level", "parentTag": "parent"}
        )

        periodCols.sort(key=lambda col: (int(col.split("-")[0]), PERIOD_ORDER.get(col.split("-")[1], 0)))

        finalCols = ["report", "account", "snakeId", "korName", "line", "level", "parent"] + periodCols
        existingCols = [c for c in finalCols if c in combinedDf.columns]
        combinedDf = combinedDf.select(existingCols)

        return combinedDf

    def getTimeseries(self, ticker: str, statements: list = None) -> pl.DataFrame:
        if statements is None:
            statements = ["BS", "IS", "CF"]

        sub = self.edgarFinance.getTickerCikSub(ticker)
        pre = self.edgarFinance.getPre(sub)
        factsDf = self.edgarFinance.getFactsBulk(ticker)
        factsPlDf = self.edgarFinance.convertBulkFactsToPolar(factsDf)

        merged = self._mergeFactsWithMetadata(factsPlDf, sub, pre)
        standardized = self._applyStandardMapping(merged)
        pivoted = self._pivotByStmt(standardized)

        if statements:
            pivoted = pivoted.filter(pl.col("report").is_in(statements))

        return pivoted

    def getFacts(self, ticker: str) -> pl.DataFrame:
        sub = self.edgarFinance.getTickerCikSub(ticker)
        pre = self.edgarFinance.getPre(sub)
        factsDf = self.edgarFinance.getFactsBulk(ticker)
        factsPlDf = self.edgarFinance.convertBulkFactsToPolar(factsDf)

        merged = self._mergeFactsWithMetadata(factsPlDf, sub, pre)
        standardized = self._applyStandardMapping(merged)

        return standardized

    def byAccount(self, snakeId: str, tickers: list = None) -> pl.DataFrame:
        if tickers is None:
            raise ValueError("tickers list is required")

        results = []
        for ticker in tickers:
            try:
                facts = self.getFacts(ticker)
                filtered = facts.filter(pl.col("snakeId") == snakeId)
                if not filtered.is_empty():
                    filtered = filtered.with_columns(pl.lit(ticker).alias("ticker"))
                    results.append(filtered)
            except Exception as e:
                print(f"Error processing {ticker}: {e}")
                continue

        if not results:
            return pl.DataFrame()

        return pl.concat(results, how="diagonal")

    def getUnmappedTimeseries(self, ticker: str) -> pl.DataFrame:
        sub = self.edgarFinance.getTickerCikSub(ticker)
        pre = self.edgarFinance.getPre(sub)
        factsDf = self.edgarFinance.getFactsBulk(ticker)
        factsPlDf = self.edgarFinance.convertBulkFactsToPolar(factsDf)

        merged = self._mergeFactsWithMetadata(factsPlDf, sub, pre)
        standardized = self._applyStandardMapping(merged)

        unmapped = standardized.filter(pl.col("snakeId").is_null())

        return self._pivotByStmt(unmapped)
