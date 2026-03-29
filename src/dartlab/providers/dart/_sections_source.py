"""sections source-of-truth accessor.

company.py에서 분리된 accessor 클래스.
raw DataFrame를 감싸되, 같은 경로에서 freq/semantic 파생표를 바로 꺼낼 수 있게 한다.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

import polars as pl

if TYPE_CHECKING:
    from dartlab.providers.dart.company import Company

_PERIOD_RE = re.compile(r"^\d{4}$")
_NUM_PATTERN = r"[\d,.]+"


class _SectionsSource:
    """sections source-of-truth accessor.

    raw DataFrame를 감싸되, 같은 경로에서 freq/semantic 파생표를 바로 꺼낼 수 있게 한다.
    일반 DataFrame 연산은 내부 raw DataFrame으로 위임한다.
    """

    def __init__(self, company: "Company"):
        self._company = company

    @property
    def raw(self) -> pl.DataFrame | None:
        return self._company._get_primary("sections")

    @property
    def frame(self) -> pl.DataFrame | None:
        return self.raw

    def forTopics(self, topics: set[str]) -> pl.DataFrame | None:
        """특정 topic만 포함하는 부분 sections."""
        return self._company._get_primary("sections", topics=frozenset(topics))

    def topics(self) -> list[str]:
        return self._company._docsSectionTopics()

    def outline(self, topic: str | None = None) -> pl.DataFrame | None:
        return self._company._docsTopicOutline(topic=topic)

    def periods(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> list[str]:
        frame = self.raw
        if frame is None:
            return []
        from dartlab.providers.dart.docs.sections import periodColumns

        return periodColumns(frame.columns, descending=recentFirst, annualAsQ4=annualAsQ4)

    def ordered(self, *, recentFirst: bool = True, annualAsQ4: bool = True) -> pl.DataFrame | None:
        return self._company._docsSectionsOrdered(recentFirst=recentFirst, annualAsQ4=annualAsQ4)

    def coverage(
        self,
        *,
        topic: str | None = None,
        recentFirst: bool = True,
        annualAsQ4: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsCoverage(
            topic=topic,
            recentFirst=recentFirst,
            annualAsQ4=annualAsQ4,
        )

    def freq(self, freqScope: str, *, includeMixed: bool = True) -> pl.DataFrame | None:
        return self._company._docsSectionsFreq(freqScope, includeMixed=includeMixed)

    def semanticRegistry(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsSemanticRegistry(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            collisionsOnly=False,
        )

    def semanticCollisions(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsSemanticRegistry(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            collisionsOnly=True,
        )

    def structureRegistry(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureRegistry(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            collisionsOnly=False,
            nodeType=nodeType,
        )

    def structureCollisions(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureRegistry(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            collisionsOnly=True,
            nodeType=nodeType,
        )

    def structureEvents(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        changedOnly: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureEvents(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            changedOnly=changedOnly,
            nodeType=nodeType,
        )

    def structureSummary(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureSummary(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
        )

    def structureChanges(
        self,
        *,
        topic: str | None = None,
        freqScope: str = "all",
        includeMixed: bool = True,
        nodeType: str | None = None,
        latestOnly: bool = True,
        changedOnly: bool = True,
    ) -> pl.DataFrame | None:
        return self._company._docsSectionsStructureChanges(
            topic=topic,
            freqScope=freqScope,
            includeMixed=includeMixed,
            nodeType=nodeType,
            latestOnly=latestOnly,
            changedOnly=changedOnly,
        )

    def changes(
        self,
        *,
        topic: str | None = None,
        fromPeriod: str | None = None,
        toPeriod: str | None = None,
    ) -> pl.DataFrame | None:
        """기간 간 변화 블록 추출 (벡터화).

        sections wide DataFrame에서 인접 기간 비교로 변화만 추출.
        5종 유형: appeared, disappeared, numeric, structural, wording.
        """
        frame = self.raw
        if frame is None:
            return None
        return _buildChanges(frame, topic=topic, fromPeriod=fromPeriod, toPeriod=toPeriod)

    def changeSummary(self, *, topN: int = 10) -> pl.DataFrame | None:
        """topic별 변화 요약 — AI 컨텍스트용."""
        ch = self.changes()
        if ch is None or ch.is_empty():
            return None
        return (
            ch.group_by(["topic", "changeType"])
            .agg(
                pl.len().alias("count"),
                pl.col("sizeDelta").mean().round(0).cast(pl.Int64).alias("avgDelta"),
            )
            .sort(["topic", "count"], descending=[False, True])
            .head(topN * 5)
        )

    def __getattr__(self, name: str) -> Any:
        frame = self.raw
        if frame is None:
            raise AttributeError(name)
        return getattr(frame, name)

    def __getitem__(self, key: Any) -> Any:
        frame = self.raw
        if frame is None:
            raise KeyError(key)
        return frame[key]

    def __len__(self) -> int:
        frame = self.raw
        return 0 if frame is None else len(frame)

    def __repr__(self) -> str:
        frame = self.raw
        if frame is None:
            return "SectionsSource(missing)"
        return (
            "SectionsSource("
            "shape="
            f"{frame.shape}, methods=[raw, topics(), outline(), periods(), ordered(), coverage(), freq(), changes(), changeSummary(), semanticRegistry(), semanticCollisions(), structureRegistry(), structureCollisions(), structureEvents(), structureSummary(), structureChanges()]"
            ")"
        )


def _buildChanges(
    sections: pl.DataFrame,
    *,
    topic: str | None = None,
    fromPeriod: str | None = None,
    toPeriod: str | None = None,
) -> pl.DataFrame:
    """sections wide DataFrame → 변화 블록 DataFrame (벡터화).

    실험 101-010에서 검증된 Polars 벡터화 패턴.
    0.15초에 22,060행 생성 (Python 루프 대비 12x).
    """
    annualCols = sorted(c for c in sections.columns if _PERIOD_RE.match(c))
    if len(annualCols) < 2:
        return pl.DataFrame()

    metaCols = ["topic"]
    for col in ("textPathKey", "blockType", "blockOrder"):
        if col in sections.columns:
            metaCols.append(col)

    if topic is not None:
        sections = sections.filter(pl.col("topic") == topic)
        if sections.is_empty():
            return pl.DataFrame()

    work = sections.with_row_index("_row")

    # wide → long
    long = work.select(["_row"] + metaCols + annualCols).unpivot(
        index=["_row"] + metaCols,
        on=annualCols,
        variable_name="period",
        value_name="text",
    )
    long = long.with_columns(pl.col("text").cast(pl.Utf8))

    # hash + len (null 보존)
    long = long.with_columns(
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").hash())
        .otherwise(pl.lit(None, dtype=pl.UInt64))
        .alias("_hash"),
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").str.len_chars())
        .otherwise(pl.lit(None, dtype=pl.UInt32))
        .alias("_len"),
        pl.when(pl.col("text").is_not_null())
        .then(pl.col("text").str.slice(0, 200))
        .otherwise(pl.lit(None, dtype=pl.Utf8))
        .alias("preview"),
    )

    # 인접 기간 비교
    long = long.sort(["_row", "period"])
    long = long.with_columns(
        pl.col("period").shift(1).over("_row").alias("_prevPeriod"),
        pl.col("_hash").shift(1).over("_row").alias("_prevHash"),
        pl.col("_len").shift(1).over("_row").alias("_prevLen"),
        pl.col("text").shift(1).over("_row").alias("_prevText"),
    )

    # 변화 필터
    changes = long.filter(
        pl.col("_prevPeriod").is_not_null()
        & ~(pl.col("text").is_null() & pl.col("_prevText").is_null())
        & ((pl.col("_hash") != pl.col("_prevHash")) | pl.col("text").is_null() | pl.col("_prevText").is_null())
    )

    if changes.is_empty():
        return pl.DataFrame()

    # 기간 필터
    if fromPeriod is not None:
        changes = changes.filter(pl.col("_prevPeriod") >= fromPeriod)
    if toPeriod is not None:
        changes = changes.filter(pl.col("period") <= toPeriod)

    # 변화 유형 분류
    changes = changes.with_columns(
        pl.col("text").str.replace_all(_NUM_PATTERN, "N").alias("_stripped"),
        pl.col("_prevText").str.replace_all(_NUM_PATTERN, "N").alias("_prevStripped"),
    )

    changes = changes.with_columns(
        pl.when(pl.col("_prevText").is_null())
        .then(pl.lit("appeared"))
        .when(pl.col("text").is_null())
        .then(pl.lit("disappeared"))
        .when(pl.col("_stripped") == pl.col("_prevStripped"))
        .then(pl.lit("numeric"))
        .when(
            (pl.col("_prevLen") > 0)
            & (
                (pl.col("_len").cast(pl.Int64) - pl.col("_prevLen").cast(pl.Int64)).abs().cast(pl.Float64)
                / pl.col("_prevLen").cast(pl.Float64)
                > 0.5
            )
        )
        .then(pl.lit("structural"))
        .otherwise(pl.lit("wording"))
        .alias("changeType")
    )

    # 결과 정리
    resultCols = ["_prevPeriod", "period", "changeType", "_prevLen", "_len", "preview"] + metaCols
    renameMap = {"_prevPeriod": "fromPeriod", "period": "toPeriod", "_prevLen": "sizeA", "_len": "sizeB"}

    result = changes.select(resultCols).rename(renameMap)
    result = result.with_columns((pl.col("sizeB").cast(pl.Int64) - pl.col("sizeA").cast(pl.Int64)).alias("sizeDelta"))

    return result
