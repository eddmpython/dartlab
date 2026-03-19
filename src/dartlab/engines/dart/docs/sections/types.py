"""사업보고서 섹션 청킹 타입 정의."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import polars as pl

from dartlab.engines.dart.docs.sections._common import basePath
from dartlab.engines.dart.docs.sections.mapper import stripSectionPrefix


def _leafTitle(path: str) -> str:
    parts = path.split(" > ")
    leaf = parts[-1]
    return stripSectionPrefix(leaf)


@dataclass
class SectionChunk:
    """단일 텍스트 청크."""

    majorNum: int
    majorTitle: str
    subTitle: str
    path: str
    textContent: str
    tableCount: int
    tableRowCount: int
    tableSummary: str
    totalChars: int
    textChars: int
    kind: str


@dataclass
class YearSections:
    """한 기간의 청크 모음."""

    year: str
    chunks: list[SectionChunk] = field(default_factory=list)
    totalOriginalChars: int = 0
    totalTextChars: int = 0

    @property
    def savings(self) -> float:
        if self.totalOriginalChars == 0:
            return 0.0
        return 1 - (self.totalTextChars / self.totalOriginalChars)

    def byMajor(self, majorNum: int) -> list[SectionChunk]:
        return [c for c in self.chunks if c.majorNum == majorNum]

    def byKind(self, kind: str) -> list[SectionChunk]:
        return [c for c in self.chunks if c.kind == kind]

    def textChunks(self) -> list[SectionChunk]:
        return [c for c in self.chunks if c.kind not in ("skipped", "table_only")]

    def search(self, keyword: str) -> list[SectionChunk]:
        kw = keyword.lower()
        return [c for c in self.chunks if kw in c.path.lower() or kw in c.textContent.lower()]

    def toLinesDf(self) -> pl.DataFrame:
        """텍스트 청크를 줄 단위 DataFrame으로 변환."""
        rows: list[dict] = []
        for c in self.textChunks():
            bp = basePath(c.path)
            for i, line in enumerate(c.textContent.split("\n")):
                line = line.strip()
                if not line:
                    continue
                h = hashlib.md5(line.encode()).hexdigest()[:12]
                rows.append(
                    {
                        "path": bp,
                        "lineNum": i,
                        "hash": h,
                        "text": line,
                        "chars": len(line),
                    }
                )
        return pl.DataFrame(rows)

    def toLeafMap(self) -> dict[str, str]:
        """leaf title → 병합된 텍스트 dict."""
        merged: dict[str, list[str]] = {}
        for c in self.textChunks():
            bp = basePath(c.path)
            lt = _leafTitle(bp)
            if lt not in merged:
                merged[lt] = []
            merged[lt].append(c.textContent)
        return {lt: "\n".join(texts) for lt, texts in merged.items()}


@dataclass
class SectionResult:
    """전체 기간별 섹션 결과.

    finance처럼 leaf title 기준 수평 비교를 제공:
        result["영업실적"]  → {"2025": "텍스트", "2024": "텍스트", ...}
        result.topics       → 전체 leaf title 목록
        result.periods      → 전체 기간 목록
    """

    corpName: str | None
    periods: list[str]
    yearSections: dict[str, YearSections] = field(default_factory=dict)
    _topicMap: dict[str, dict[str, str]] = field(
        default_factory=dict,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not self._topicMap and self.yearSections:
            self._buildTopicMap()

    def _buildTopicMap(self) -> None:
        tm: dict[str, dict[str, str]] = {}
        for period, ys in self.yearSections.items():
            leafMap = ys.toLeafMap()
            for leaf, text in leafMap.items():
                if leaf not in tm:
                    tm[leaf] = {}
                tm[leaf][period] = text
        self._topicMap = tm

    def __getitem__(self, key: str) -> dict[str, str]:
        return self._topicMap.get(key, {})

    def __contains__(self, key: str) -> bool:
        return key in self._topicMap

    def __len__(self) -> int:
        return len(self._topicMap)

    @property
    def topics(self) -> list[str]:
        return sorted(self._topicMap.keys())

    @property
    def latest(self) -> YearSections | None:
        if not self.periods:
            return None
        return self.yearSections.get(self.periods[0])

    @property
    def years(self) -> list[str]:
        return self.periods

    def search(self, keyword: str) -> dict[str, dict[str, str]]:
        """키워드로 topic 검색."""
        kw = keyword.lower()
        return {t: series for t, series in self._topicMap.items() if kw in t.lower()}

    def overview(self) -> pl.DataFrame:
        """전체 topic × period 크기 매트릭스."""
        records: list[dict] = []
        for topic, series in self._topicMap.items():
            row: dict = {"topic": topic, "count": len(series)}
            for period in self.periods:
                row[period] = len(series[period]) if period in series else 0
            records.append(row)
        return pl.DataFrame(records).sort("count", descending=True)

    def compare(
        self,
        periodA: str,
        periodB: str,
        path: str | None = None,
    ) -> pl.DataFrame:
        """두 기간의 텍스트 변경사항을 줄 단위로 비교."""
        ysA = self.yearSections.get(periodA)
        ysB = self.yearSections.get(periodB)
        if ysA is None or ysB is None:
            return pl.DataFrame(
                schema={
                    "path": pl.Utf8,
                    "linesA": pl.UInt32,
                    "linesB": pl.UInt32,
                    "kept": pl.UInt32,
                    "added": pl.UInt32,
                    "removed": pl.UInt32,
                    "changeRate": pl.Float64,
                }
            )

        dfA = ysA.toLinesDf()
        dfB = ysB.toLinesDf()

        if path:
            kw = path.lower()
            dfA = dfA.filter(pl.col("path").str.to_lowercase().str.contains(kw, literal=True))
            dfB = dfB.filter(pl.col("path").str.to_lowercase().str.contains(kw, literal=True))

        allPaths = sorted(set(dfA["path"].to_list()) | set(dfB["path"].to_list()))

        records: list[dict] = []
        for p in allPaths:
            pA = dfA.filter(pl.col("path") == p)
            pB = dfB.filter(pl.col("path") == p)
            kept = pA.join(pB, on="hash", how="inner").height
            added = pB.join(pA, on="hash", how="anti").height
            removed = pA.join(pB, on="hash", how="anti").height
            total = pA.height + pB.height
            rate = (added + removed) / total if total > 0 else 0.0
            records.append(
                {
                    "path": p,
                    "linesA": pA.height,
                    "linesB": pB.height,
                    "kept": kept,
                    "added": added,
                    "removed": removed,
                    "changeRate": round(rate, 3),
                }
            )

        return pl.DataFrame(records).sort("changeRate", descending=True)

    def diff(
        self,
        periodA: str,
        periodB: str,
        path: str,
    ) -> pl.DataFrame:
        """특정 섹션의 줄 단위 diff 반환."""
        ysA = self.yearSections.get(periodA)
        ysB = self.yearSections.get(periodB)
        if ysA is None or ysB is None:
            return pl.DataFrame(schema={"status": pl.Utf8, "text": pl.Utf8})

        dfA = ysA.toLinesDf()
        dfB = ysB.toLinesDf()

        kw = path.lower()
        dfA = dfA.filter(pl.col("path").str.to_lowercase().str.contains(kw, literal=True))
        dfB = dfB.filter(pl.col("path").str.to_lowercase().str.contains(kw, literal=True))

        kept = dfA.join(dfB, on="hash", how="inner", suffix="_r").select(pl.lit("kept").alias("status"), pl.col("text"))
        added = dfB.join(dfA, on="hash", how="anti").select(pl.lit("added").alias("status"), pl.col("text"))
        removed = dfA.join(dfB, on="hash", how="anti").select(pl.lit("removed").alias("status"), pl.col("text"))

        return pl.concat([removed, added, kept])
