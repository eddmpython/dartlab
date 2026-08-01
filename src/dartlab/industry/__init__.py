"""산업 매퍼엔진 — 데이터 주도 산업지도.

L2 분석 엔진. KindList(업종+제품) → docs(사업보고서) → AI+사람 검수
4단계 파이프라인으로 살아있는 산업지도를 빌드한다.

분류체계(taxonomy.json)가 데이터. 코드는 파이프라인만 고정.

사용법::

    import dartlab

    dartlab.industry()                              # 가이드 (산업 목록)
    dartlab.industry("semiconductor")               # 반도체 산업지도 DataFrame
    dartlab.industry("semiconductor", "equipment")  # 장비 공정만

    c = dartlab.Company("005930")
    c.industry()                                    # 삼성전자의 산업 내 위치
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import polars as pl

from dartlab.frame.sector import (  # noqa: F401 — public re-export
    MARKET_KR as MARKET_KR,
)
from dartlab.frame.sector import (
    MARKET_PARAMS as MARKET_PARAMS,
)
from dartlab.frame.sector import (
    MARKET_US as MARKET_US,
)
from dartlab.frame.sector import (
    IndustryGroup as IndustryGroup,
)
from dartlab.frame.sector import (
    MarketParams as MarketParams,
)
from dartlab.frame.sector import (
    Sector as Sector,
)
from dartlab.frame.sector import (
    SectorInfo as SectorInfo,
)
from dartlab.frame.sector import (
    SectorParams as SectorParams,
)
from dartlab.frame.sector import (
    classify as classify,
)
from dartlab.frame.sector import (
    getMarketParams as getMarketParams,
)
from dartlab.frame.sector import (
    getParams as getParams,
)
from dartlab.frame.sector import (
    getThresholds as getThresholds,
)

_DATA_DIR = Path(__file__).parent

# Public surface — Industry callable + addOverride. Sector/IndustryGroup 등은 core.sector
# 에서 re-export (위 import) — __all__ 자체에는 포함하지 않고 from-import 만 노출.
__all__ = ["Industry", "addOverride"]


@dataclass(frozen=True)
class IndustryAxisEntry:
    """industry 축 메타 (gather ``GatherAxisEntry`` 와 동형 — 엔진별 registry 패턴).

    ``capability/builder._injectAxisRegistriesLive`` 가 ``label``/``description`` 으로
    ``industry.{axis}`` 카탈로그 등록. ``hidden`` 은 가이드 제외.
    """

    label: str
    description: str
    targetType: str = "industryId"
    hidden: bool = False


def _resolveIndustryTarget(target: str | None) -> str | None:
    """종목코드로 온 target 을 그 회사의 산업 ID 로 바꾼다. 아니면 그대로 둔다.

    축 문서는 target 으로 industryId · themeId · stockCode 셋을 받는다고 적어 두었는데,
    정작 종목코드를 해소하는 자리가 없었다. 핸들러가 종목코드를 industryId 로 그대로 받아
    조회가 전부 빗나갔고, 예외 대신 빈 표가 나와서 어디서도 안 잡혔다. 실측으로 일곱 축
    (summary·timeline·lifecycle·concentration·dynamics·polarization·map) 이 전부 그랬다.

    노드 목록이 이미 종목코드와 산업을 함께 들고 있으므로 새 자료를 만들지 않는다.
    """
    if not target or not (len(target) == 6 and target.isdigit()):
        return target
    try:
        from dartlab.industry.build.pipeline import loadNodes

        for node in loadNodes():
            if getattr(node, "stockCode", None) == target:
                resolved = getattr(node, "industry", None)
                if resolved:
                    return resolved
    except (ImportError, OSError, RuntimeError, ValueError):
        return target
    return target


# industry 축 SSOT. gather 표준(engine(axis, target)) 의 industry 판. 옛 플래그(summary 등)·
# 메서드(edges/map/theme) 를 축으로 통일. 기본 산업지도(industryId-first)는 backward-compat 브릿지.
_AXIS_REGISTRY: dict[str, IndustryAxisEntry] = {
    "summary": IndustryAxisEntry("집계", "공정별 매출/영업이익 집계."),
    "timeline": IndustryAxisEntry("추이", "연도별 공정 매출 시계열."),
    "lifecycle": IndustryAxisEntry("수명주기", "산업 라이프사이클 phase (Vernon 3+쇠퇴)."),
    "concentration": IndustryAxisEntry("집중도", "상장사 매출 HHI/CR3 + 상위 5사 시장구조."),
    "dynamics": IndustryAxisEntry("이익풀동학", "공정별 영업이익 levels + 리더교체(집중/이동형) 판정."),
    "polarization": IndustryAxisEntry("양극화", "마진분산 vs 밸류분산 two-lens 교차검증."),
    "edges": IndustryAxisEntry("공급망", "공급-수요·계열 거래 관계 (거래액/의존도).", "industryId|stockCode"),
    "map": IndustryAxisEntry("산업정의", "산업 한글명 + 공정 단계 정의(IndustryDef)."),
    "theme": IndustryAxisEntry("테마", "횡단 투자 테마 — themeId→멤버 / stockCode→소속 테마.", "themeId|stockCode"),
}


class Industry:
    """산업 매퍼엔진 진입점.

    Guide:
        AI 역할: AI는 industry를 섹터/밸류체인 맥락 엔진으로 보고 기업 지표와 산업 driver를 분리해 연결한다.
    """

    def __call__(
        self,
        axis: str | None = None,
        target: str | None = None,
        *,
        stage: str | None = None,
        year: str | None = None,
        stockCode: str | None = None,
        grade: bool = False,
        discover: bool = False,
        industryId: str | None = None,
        summary: bool = False,
        timeline: bool = False,
        lifecycle: bool = False,
        concentration: bool = False,
        dynamics: bool = False,
        polarization: bool = False,
        **kwargs: Any,
    ) -> pl.DataFrame:
        """산업지도를 조회한다 — gather 표준 ``industry(axis, target)`` axis-dispatch.

        gather 표준 ``industry(axis, target)``: axis ∈ {summary·timeline·lifecycle·concentration·
        dynamics·polarization·edges·map·theme} (``_AXIS_REGISTRY``), target=industryId/themeId/stockCode.
        **backward-compat**: 첫 인자가 축이 아니면 옛 industryId-first 로 흡수 — ``industry("semiconductor")``·
        ``industry("semiconductor", "fab")``(stage)·``industry("semiconductor", summary=True)`` 모두 동작.

        Parameters
        ----------
        axis : str | None
            축 (summary/timeline/lifecycle/concentration/dynamics/polarization/edges/map/theme).
            None 이면 산업 목록 가이드. 축이 아닌 값이면 industryId 로 해석(옛 형식).
        target : str | None
            축 대상 — industryId(대부분) / themeId(theme) / stockCode(edges·theme). 옛 형식에선 stage.
        stage : str | None
            특정 공정만 필터 (산업지도 축).
        year : str | None
            재무 데이터 기준 연도 (summary 축). None이면 실제 관측된 최근 연간 사업연도.
        stockCode : str | None
            edges/theme 축의 종목 대상.
        grade, discover : bool
            theme 축 옵션 (멤버 매출노출% 등급 / 공급망 발견).
        summary, timeline, lifecycle, concentration, dynamics, polarization : bool
            옛 플래그 (backward-compat) — 해당 축으로 흡수. 신규는 axis 인자 권장.

        Returns
        -------
        pl.DataFrame
            industryId=None (가이드):
                산업ID : str — 산업 식별자
                산업명 : str — 한글 산업명
                공정수 : int — 해당 산업의 공정 단계 수
            industryId 지정:
                공정 : str — 공정 단계명
                종목코드 : str — 6자리 코드
                종목명 : str — 회사명
            summary=True:
                공정 : str — 공정명
                매출합계 : float — 공정별 매출 합산 (원)
                영업이익합계 : float — 공정별 영업이익 합산 (원)

        Guide
        -----
        AI 역할: AI는 industry를 섹터/밸류체인 맥락 엔진으로 보고 기업 지표와 산업 driver를 분리해 연결한다.
        When: 개별 기업 지표를 산업 공정, 밸류체인, peer 맥락으로 해석할 때.
        How: industry() 로 산업 목록 확인 → industry(industryId) 로 공정별 기업 위치 확인 → analysis/scan 근거와 연결.

        LLM Specifications:
            AntiPatterns:
                - industryId 추측 (industry() 무인자 호출 결과 가이드 확인 후)
                - stage 추측 (industryId 별로 다름 — industry(industryId) 결과의 공정 컬럼 확인)
                - summary 와 timeline 동시 (둘 중 하나만)
            OutputSchema:
                - industryId 미지정: 산업ID / 산업명 / 공정수
                - industryId 지정: 공정 / 종목코드 / 종목명
                - summary=True: 공정 / 매출합계 / 영업이익합계
                - timeline=True: 연도 / 공정별 매출 컬럼
                - concentration=True: 지표(기업수·총매출·HHI·HHI라벨·상위3비중) + 상위5사 행
                  (종목코드 / 종목명 / 공정 / 매출). 상장사 매출 기준 상대 집중도.
                - dynamics=True: 공정별 행 (공정명 / 첫해(조) / 끝해(조) / 변화(조) / 적자전환 /
                  끝해리더 / 판정[집중형|이동형] / 리더이동 / 윈도 / 생존편향주의).
                - polarization=True: 2행 two-lens (렌즈[마진/밸류] / 분산지표 / 첫해값 / 끝해값 /
                  방향레벨 / n / 음수자본제외 / 양극화판정[승자독식 심화|동질 평준화|혼재] /
                  교차검증[일치|불일치] / 윈도 / 생존편향주의). 재무·시장 두 자료원 교차검증.
            Prerequisites:
                - taxonomy + nodes.json (운영자 매핑 산출물)
                - summary=True 시 재무 데이터 (자동 다운로드)
            Freshness:
                taxonomy 정의 시점 — 운영자 수동 업데이트.
            Dataflow:
                industryId → loadNodes (nodes.json) → industry filter
                → stage filter → 공정명 룩업 (taxonomy.getIndustry) →
                DataFrame 조립. summary 모드는 buildIndustrySummary 경유.
            TargetMarkets:
                - KR
        """
        flagAxis = next(
            (
                k
                for k, v in (
                    ("summary", summary),
                    ("timeline", timeline),
                    ("lifecycle", lifecycle),
                    ("concentration", concentration),
                    ("dynamics", dynamics),
                    ("polarization", polarization),
                )
                if v
            ),
            None,
        )

        # 신형(gather 표준): industry("summary","semiconductor") / industry("theme","secondaryBattery").
        if industryId is None and axis is not None and axis in _AXIS_REGISTRY:
            return self._dispatch(
                axis, target, stage=stage, year=year, stockCode=stockCode, grade=grade, discover=discover
            )

        # backward-compat: 첫 인자 = industryId (옛 형식). keyword industryId= 우선. 2번째 positional=stage.
        idVal = industryId if industryId is not None else axis
        if idVal is None:
            return self._guide()  # industry() 또는 industry(summary=True) → 산업 목록 (불변)
        if flagAxis:
            return self._dispatch(flagAxis, idVal, year=year, stockCode=stockCode)
        return self._query(idVal, stage if stage is not None else target)

    def _dispatch(
        self,
        axis: str,
        target: str | None,
        *,
        stage: str | None = None,
        year: str | None = None,
        stockCode: str | None = None,
        grade: bool = False,
        discover: bool = False,
    ) -> Any:
        """축 → 핸들러 위임 (axis-dispatch SSOT). edges/map/theme 메서드도 본 경로로 통일."""
        target = _resolveIndustryTarget(target)
        if axis == "summary":
            return self._summary(target, year=year)
        if axis == "timeline":
            return self._timeline(target)
        if axis == "lifecycle":
            return self._lifecycle(target)
        if axis == "concentration":
            return self._concentration(target)
        if axis == "dynamics":
            return self._dynamics(target)
        if axis == "polarization":
            return self._polarization(target)
        if axis == "edges":
            return self.edges(target, stockCode)
        if axis == "map":
            return self.map(target)
        if axis == "theme":
            return self.theme(themeId=target, stockCode=stockCode, grade=grade, discover=discover)
        return self._query(target, stage)

    def _guide(self) -> pl.DataFrame:
        """등록된 산업 목록."""
        from dartlab.industry.taxonomy import listIndustries

        entries = listIndustries()
        if not entries:
            return pl.DataFrame({"산업ID": [], "산업명": [], "공정수": []})
        return pl.DataFrame(
            {
                "산업ID": [e["industryId"] for e in entries],
                "산업명": [e["name"] for e in entries],
                "공정수": [e["stages"] for e in entries],
            }
        )

    def _query(self, industryId: str, stage: str | None) -> pl.DataFrame:
        """nodes.json에서 해당 산업의 노드를 DataFrame으로 반환."""
        from dartlab.industry.build.pipeline import loadNodes
        from dartlab.industry.taxonomy import getIndustry

        nodes = loadNodes()
        filtered = [n for n in nodes if n.industry == industryId]
        if stage:
            filtered = [n for n in filtered if n.stage == stage]

        if not filtered:
            return pl.DataFrame(
                schema={
                    "종목코드": pl.Utf8,
                    "종목명": pl.Utf8,
                    "공정": pl.Utf8,
                    "공정명": pl.Utf8,
                    "역할": pl.Utf8,
                    "위치": pl.Utf8,
                    "신뢰도": pl.Float64,
                    "소스": pl.Utf8,
                }
            )

        ind = getIndustry(industryId)
        stageLabels = {s.key: s.name for s in ind.stages} if ind else {}

        df = pl.DataFrame(
            {
                "종목코드": [n.stockCode for n in filtered],
                "종목명": [n.corpName for n in filtered],
                "공정": [n.stage for n in filtered],
                "공정명": [stageLabels.get(n.stage, n.stage) for n in filtered],
                "역할": [n.role for n in filtered],
                "위치": [n.stream for n in filtered],
                "매출(억)": [round(n.revenue / 1e8, 0) if n.revenue else None for n in filtered],
                "신뢰도": [n.confidence for n in filtered],
                "소스": [n.source for n in filtered],
            }
        )
        return df.sort("매출(억)", descending=True, nulls_last=True)

    def _summary(self, industryId: str, *, year: str | None = None) -> pl.DataFrame:
        """공정별 매출/이익 집계."""
        from dartlab.industry.build.financials import buildIndustrySummary
        from dartlab.industry.build.pipeline import loadNodes

        return buildIndustrySummary(loadNodes(), industryId, year=year)

    def _timeline(self, industryId: str) -> pl.DataFrame:
        """연도별 공정 매출 추이."""
        from dartlab.industry.build.financials import buildTimelineSummary
        from dartlab.industry.build.pipeline import loadNodes

        return buildTimelineSummary(loadNodes(), industryId)

    def _lifecycle(self, industryId: str) -> pl.DataFrame:
        """산업 라이프사이클 phase 시계열 (Vernon 3-phase + 쇠퇴)."""
        from dartlab.industry.calcs.lifecycle import classifyLifecycle

        return classifyLifecycle(industryId)

    def _concentration(self, industryId: str) -> pl.DataFrame:
        """산업 매출 시장구조 집중도 (HHI/CR3 + 상위 5사).

        ``calcs.concentration.calcIndustryConcentration`` (dict) 를 표면 계약(DataFrame)으로
        감싼다. 행 = 상위 5사(매출비중% 포함), 컬럼에 산업 집계(HHI·HHI라벨·CR3·기업수·총매출)를
        반복 첨부. **동일 회계연도 상장사 매출 기준**. 비상장·해외 매출 제외라 절대 점유율이
        아닌 상대 집중도이며 상태·회계연도·커버리지를 함께 확인해야 한다.
        """
        from dartlab.industry.build.pipeline import loadNodes
        from dartlab.industry.calcs.concentration import calcIndustryConcentration

        r = calcIndustryConcentration(industryId, loadNodes())
        schema = {
            "종목코드": pl.Utf8,
            "종목명": pl.Utf8,
            "공정": pl.Utf8,
            "매출(억)": pl.Float64,
            "매출비중(%)": pl.Float64,
            "HHI": pl.Float64,
            "HHI라벨": pl.Utf8,
            "상위3비중(%)": pl.Float64,
            "기업수": pl.Int64,
            "총매출(조)": pl.Float64,
            "상태": pl.Utf8,
            "회계연도": pl.Utf8,
            "커버리지(%)": pl.Float64,
            "제한사유": pl.Utf8,
        }
        topN = r.get("topN") or []
        if not topN:
            return pl.DataFrame(
                [
                    {
                        "종목코드": None,
                        "종목명": None,
                        "공정": None,
                        "매출(억)": None,
                        "매출비중(%)": None,
                        "HHI": r.get("hhi"),
                        "HHI라벨": r.get("hhiRisk"),
                        "상위3비중(%)": r.get("top3Ratio"),
                        "기업수": r.get("companyCount"),
                        "총매출(조)": None,
                        "상태": r.get("status"),
                        "회계연도": r.get("fiscalYear"),
                        "커버리지(%)": (r.get("coverage") or {}).get("pct"),
                        "제한사유": r.get("blockedReason"),
                    }
                ],
                schema=schema,
            )

        totalRev = r.get("totalRevenue") or 0
        rows = []
        for m in topN:
            rev = m.get("revenue") or 0
            rows.append(
                {
                    "종목코드": m.get("stockCode"),
                    "종목명": m.get("corpName"),
                    "공정": m.get("stage"),
                    "매출(억)": round(rev / 1e8, 0) if rev else None,
                    "매출비중(%)": round(rev / totalRev * 100, 1) if totalRev else None,
                    "HHI": r.get("hhi"),
                    "HHI라벨": r.get("hhiRisk"),
                    "상위3비중(%)": r.get("top3Ratio"),
                    "기업수": r.get("companyCount"),
                    "총매출(조)": round(totalRev / 1e12, 2) if totalRev else None,
                    "상태": r.get("status"),
                    "회계연도": r.get("fiscalYear"),
                    "커버리지(%)": (r.get("coverage") or {}).get("pct"),
                    "제한사유": r.get("blockedReason"),
                }
            )
        return pl.DataFrame(rows, schema=schema)

    def _dynamics(self, industryId: str) -> pl.DataFrame:
        """이익 풀 동학 (집중형 vs 이동형) — 공정별 첫/끝해 영업이익 levels + argmax 리더 교체 판정.

        ``calcs.profitPoolDynamics`` (dict) 를 표면 계약(DataFrame)으로 감싼다. share 미사용·levels(조)
        만·적자전환 플래그·생존편향 고정 컬럼. 산업이 *이동형*(소재→셀)이냐 *집중형*(FAB 고착)이냐.
        """
        from dartlab.industry.calcs.profitPoolDynamics import _dynamicsDataFrame

        return _dynamicsDataFrame(industryId)

    def _polarization(self, industryId: str) -> pl.DataFrame:
        """산업 양극화 — 마진분산(재무)·밸류분산(시장) 두 렌즈 교차검증 (승자독식 vs 평준화).

        ``calcs.polarization`` (dict) 를 표면 계약(2행 two-lens DataFrame)으로 감싼다. 마진=OPM IQR
        다년 방향, 밸류=P/B p90/p10 스냅샷. 두 독립 자료원이 일치하면 강건(folk통계 방어). 음수자본
        제외수·생존편향·5점 윈도(방향신호) 정직 표기.
        """
        from dartlab.industry.calcs.polarization import _polarizationDataFrame

        return _polarizationDataFrame(industryId)

    def build(self, *, skipDocs: bool = False) -> None:
        """산업지도를 빌드한다 (4단계 파이프라인).

        Capabilities:
            KSIC → 제품 분류 → docs 보정 → review 4 단계 파이프라인을 1 회 실행. 결과는
            data/industry/{nodes,edges,deltas,hop2}.json 으로 직렬화.

        Parameters
        ----------
        skipDocs : bool
            True 면 docs 기반 제품 분류 단계 생략 (빌드 시간 단축).

        Returns
        -------
        None
            결과는 ``data/industry/nodes.json`` + ``edges.json`` 에 저장.
            조회는 ``industry(industryId)`` / ``industry.edges()``.

        Raises:
            없음 — 개별 단계 실패는 warning + skip.

        Example:
            >>> from dartlab.industry import Industry
            >>> Industry().build(skipDocs=False)

        Guide:
            전 종목 panel parquet 스캔 비용이 크다. 일반 사용자는 호출하지 말고 manifest 빌드된
            결과 (``Industry()(industryId)`` / ``edges()``) 조회만.

        When:
            산업지도 manifest 가 stale 일 때 (재무 데이터 또는 KSIC 갱신 후) 만.

        How:
            ``industry/build/pipeline.buildIndustryMap`` 위임. 내부적으로 stage1_ksic →
            stage2_product → stage3_docs → stage4_review 순.

        Requires:
            - L1 raw: DART 사업보고서·재무·KindList
            - L1.5 frame: scan/finance.parquet + panel/{code}.parquet

        See Also:
            - ``dartlab.industry.build.pipeline.buildIndustryMap`` : 본 위임 대상
            - ``dartlab.industry.Industry.__call__`` : 조회 진입점

        AIContext:
            AI 가 직접 호출하지 않는다 (배치 작업). 운영자가 manifest 갱신할 때만.
        """
        from dartlab.industry.build.pipeline import buildIndustryMap

        buildIndustryMap(skipDocs=skipDocs)

    def edges(self, industryId: str | None = None, stockCode: str | None = None) -> pl.DataFrame:
        """공급-수요·계열 관계 조회.

        Capabilities:
            ``edges.json`` 산출물을 로드해 (industryId, stockCode) 필터 후 한국어 컬럼 polars
            DataFrame 으로 반환. 단일 호출로 회사 / 산업 단위 거래 관계 검색 가능.

        Parameters
        ----------
        industryId : str | None
            산업 ID로 필터.
        stockCode : str | None
            특정 종목의 관계만.

        Returns
        -------
        pl.DataFrame
            columns: from코드, from이름, to코드, to이름, 관계, 산업, 신뢰도, 소스, 근거, 거래액, 의존도(%)

            - ``거래액``: 거래 금액(억원). 공시 「주요 매입처」 표 추출, 누락은 None(0 채움 금지).
            - ``의존도(%)``: 매입비중(공급사 매출처 의존도, type=supplier). 추출 천장 낮음 — 대부분 None.
              ★커버리지 빈곤(현 추출 amount 소수)은 화면 1급시민, "SPLC식"·"IO 승수" 과대포장 금지.

        Raises:
            없음 — manifest 없으면 빈 DataFrame.

        Example:
            >>> from dartlab.industry import Industry
            >>> Industry().edges(stockCode="005930").select(["to이름", "관계", "신뢰도"]).head(3)

        Guide:
            반환 DataFrame 의 ``소스`` 컬럼이 docs_table 이면 강한 단정, network 이면 출자 관계,
            docs 면 보고서 언급. 답변에 신뢰도/소스 단서 명시 권장.

        When:
            "이 회사 거래처", "이 산업 안 관계망" 류 답변 데이터 조회. UI 그래프 시각화 데이터.

        How:
            ``industry/build/pipeline.loadEdges`` → 산업/종목 필터 → 한국어 컬럼 DataFrame 변환.

        Requires:
            - ``data/industry/edges.json`` manifest (``build()`` 이후 산출)

        See Also:
            - ``dartlab.industry.Industry.build`` : manifest 빌드
            - ``dartlab.industry.build.pipeline.loadEdges`` : 본 위임 대상

        AIContext:
            엣지 단일 진입점. AI 답변 cite 시 ``소스`` 와 ``신뢰도`` 컬럼을 evidence 로 명시.
        """
        from dartlab.industry.build.pipeline import loadEdges

        allEdges = loadEdges()
        filtered = allEdges

        if industryId:
            filtered = [e for e in filtered if e.industry == industryId]
        if stockCode:
            filtered = [e for e in filtered if e.fromCode == stockCode or e.toCode == stockCode]

        if not filtered:
            return pl.DataFrame(
                schema={
                    "from코드": pl.Utf8,
                    "from이름": pl.Utf8,
                    "to코드": pl.Utf8,
                    "to이름": pl.Utf8,
                    "관계": pl.Utf8,
                    "산업": pl.Utf8,
                    "신뢰도": pl.Float64,
                    "소스": pl.Utf8,
                    "근거": pl.Utf8,
                    "거래액": pl.Float64,
                    "의존도(%)": pl.Float64,
                }
            )

        return pl.DataFrame(
            {
                "from코드": [e.fromCode for e in filtered],
                "from이름": [e.fromName for e in filtered],
                "to코드": [e.toCode for e in filtered],
                "to이름": [e.toName for e in filtered],
                "관계": [e.edgeType for e in filtered],
                "산업": [e.industry for e in filtered],
                "신뢰도": [e.confidence for e in filtered],
                "소스": [e.source for e in filtered],
                "근거": [e.evidence for e in filtered],
                # 거래액(억원)·의존도(%)=매입비중 — 공시인용 evidence (Killer#2). 추출 누락분은 None(0 채움 금지).
                "거래액": [e.amount for e in filtered],
                "의존도(%)": [e.ratio for e in filtered],
            }
        )

    def map(self, industryId: str) -> Any:
        """IndustryDef 객체를 반환 (taxonomy 조회).

        Capabilities:
            정적 taxonomy (``industry/taxonomy.py``) 에서 산업 정의 (한글명/공정 단계 리스트)를
            조회. 본 객체는 ``Industry()(industryId)`` 결과 카드의 헤더/공정 라벨 소스.

        Parameters
        ----------
        industryId : str
            산업 ID (예: "semiconductor").

        Returns
        -------
        IndustryDef | None
            industryId : str — 산업 식별자
            name : str — 한글 산업명
            stages : list[StageDef] — 공정 단계 정의 (key, name, role, note).
            등록되지 않은 산업이면 None.

        Raises:
            없음 — 미등록 ID 면 None.

        Example:
            >>> from dartlab.industry import Industry
            >>> Industry().map("semiconductor").name
            '반도체'

        Guide:
            결과의 ``stages`` 키 셋이 ``IndustryNode.stage`` 의 valid 값 — 매핑 검증 / 운영자
            override 작성에 참조.

        When:
            "이 산업의 공정 단계는?", "stages 키 목록 확인" 류 메타 조회.

        How:
            ``industry/taxonomy.getIndustry`` 위임 — 정적 JSON 로드 + 룩업.

        Requires:
            - reference: ``industry/taxonomy.py`` 정적 정의

        See Also:
            - ``dartlab.industry.taxonomy.getIndustry`` : 본 위임 대상
            - ``dartlab.industry.Industry.__call__`` : 회사 카드 진입점

        AIContext:
            AI 답변에서 산업 한글명과 공정 단계 키 인용에 사용. ``Industry()(code)`` 결과의
            ``stage`` 필드 매칭 표준.
        """
        from dartlab.industry.taxonomy import getIndustry

        return getIndustry(industryId)

    def theme(
        self,
        themeId: str | None = None,
        stockCode: str | None = None,
        *,
        grade: bool = False,
        discover: bool = False,
    ) -> pl.DataFrame:
        """횡단 투자 테마 — industry 엔진의 테마 능력. 테마→멤버 또는 종목→소속 테마.

        Capabilities:
            테마는 *industry 엔진의 하위 능력*(별도 엔진 아님). ``themeId`` → 그 테마 멤버 종목
            (주요제품 substring 태깅, 근거 동반). ``stockCode`` → 그 종목의 소속 테마+근거+매출
            노출%. 둘 다 없으면 테마 목록. 인포스탁 리스트와 달리 *근거 투명*. (``edges``·``map``
            과 동일 — Industry 엔진 메서드.)

        Parameters
        ----------
        themeId : str | None
            테마 ID. (themeId·stockCode 모두 None) 이면 테마 목록. stockCode 와 함께면 stockCode 우선.
        stockCode : str | None
            6자리 종목코드. 지정 시 그 종목의 소속 테마 도시에(근거+노출%).
        grade : bool
            themeId 모드 멤버별 ``노출%``·``등급근거`` 추가 (멤버별 panel 조회 — 느림).
        discover : bool
            themeId 모드 공급망 거래엣지(supplier/customer)로 비키워드 수혜주 추가(``발견``=공급망).

        Returns
        -------
        pl.DataFrame
            (인자 없음): ``themeId, name, keywords, gradeable``.
            stockCode 지정: ``themeId, 테마, 근거, 노출%, 등급근거`` (그 종목의 테마들).
            themeId 지정: ``종목코드, 회사명, 업종, 근거, 발견`` (+grade: ``노출%, 등급근거``).
            ``노출%``=None 은 미산출(추출실패/단일사업/테마 segmentKeywords 부재) — 100% 등치 금지.

        Raises:
            없음 — 미등록 테마면 빈 DataFrame.

        Example:
            >>> from dartlab.industry import Industry
            >>> Industry().theme(stockCode="051910")["노출%"][0]  # LG화학 2차전지
            48.4

        Guide:
            ``노출%``>=50 pure-play / 10~50 quasi / <10 곁다리 / None 미산출. 답변 시 ``근거``·
            ``등급근거`` 를 evidence 로 명시.

        When:
            "이 테마 종목·순도", "이 종목 무슨 테마·왜", AI 워크벤치 테마 근거 답변.

        How:
            ``industry.themes`` 백엔드(``_matchTheme`` 태깅 / ``_themeExposure`` 등급 / ``_stockThemes``
            종목 도시에) + ``build.pipeline.loadEdges`` (발견, supplyOnly).

        Requires:
            - ``industry/themes.json`` + KIND 상장목록. grade/stockCode: panel 주석 데이터.

        See Also:
            - ``dartlab.industry.Industry.edges`` : 공급망 관계 원천 (동일 industry 엔진 메서드).
            - ``dartlab.industry.Industry.map`` : 산업 정의 메타.

        AIContext:
            industry 엔진의 테마 메서드(별도 엔진 아님). 멤버십(근거)·노출%(등급근거)를 cite.
        """
        from dartlab.industry.themes import _loadThemes, _matchTheme, _stockThemes, _themeExposure

        if stockCode is not None:
            return _stockThemes(stockCode)

        themes = _loadThemes()
        if themeId is None:
            return pl.DataFrame(
                [
                    {
                        "themeId": t.themeId,
                        "name": t.name,
                        "keywords": len(t.keywords),
                        "gradeable": bool(t.segmentKeywords),
                    }
                    for t in themes.values()
                ],
                schema={"themeId": pl.Utf8, "name": pl.Utf8, "keywords": pl.Int64, "gradeable": pl.Boolean},
            )

        theme = themes.get(themeId)
        emptySchema = {
            "종목코드": pl.Utf8,
            "회사명": pl.Utf8,
            "업종": pl.Utf8,
            "근거": pl.Utf8,
            "발견": pl.Utf8,
        }
        if theme is None:
            return pl.DataFrame(schema=emptySchema)

        from dartlab.gather.krx.listing.registry import getKindList

        kind = getKindList()
        members: list[dict] = []
        memberCodes: set[str] = set()
        for r in kind.iter_rows(named=True):
            hits = _matchTheme(theme, r.get("주요제품") or "")
            if hits:
                code = r["종목코드"]
                memberCodes.add(code)
                members.append(
                    {
                        "종목코드": code,
                        "회사명": r.get("회사명"),
                        "업종": r.get("업종"),
                        "근거": ", ".join(hits),
                        "발견": "키워드",
                    }
                )

        if discover:
            members.extend(self._themeDiscover(memberCodes, members, kind))

        if grade:
            import gc

            for m in members:
                g = _themeExposure(themeId, m["종목코드"]) or {}
                m["노출%"] = g.get("exposurePct")
                m["등급근거"] = g.get("basis")
                gc.collect()

        if not members:
            return pl.DataFrame(schema=emptySchema)
        return pl.DataFrame(members)

    @staticmethod
    def _themeDiscover(memberCodes: set[str], members: list[dict], kind: pl.DataFrame) -> list[dict]:
        """공급망 거래엣지(supplier/customer)로 키워드 미언급 수혜주 발견 (덕지덕지 가드: 거래엣지만).

        고신뢰 시드(근거 키워드 2+)의 1-hop 거래 이웃 중 멤버 아닌 상장사. investor/affiliate
        엣지는 동어반복/노이즈라 제외(E6 실측: 금융 노이즈 차단). amount 는 희소(랭킹 보조).
        """
        from dartlab.industry.build.pipeline import loadEdges

        seeds = {m["종목코드"] for m in members if m.get("발견") == "키워드" and m["근거"].count(",") >= 1}
        if not seeds:
            return []
        listed = set(kind["종목코드"].to_list())
        nameMap = dict(zip(kind["종목코드"], kind["회사명"]))
        prodMap = dict(zip(kind["종목코드"], kind["업종"]))
        supplyTypes = ("supplier", "customer")
        found: dict[str, str] = {}
        for e in loadEdges():
            et = (e.edgeType or "").lower()
            if not any(t in et for t in supplyTypes):
                continue
            if e.fromCode in seeds and e.toCode and e.toCode in listed and e.toCode not in memberCodes:
                found.setdefault(e.toCode, e.fromName or "")
            if e.toCode in seeds and e.fromCode and e.fromCode in listed and e.fromCode not in memberCodes:
                found.setdefault(e.fromCode, e.toName or "")
        return [
            {
                "종목코드": code,
                "회사명": nameMap.get(code),
                "업종": prodMap.get(code),
                "근거": f"공급망 ←{via}" if via else "공급망",
                "발견": "공급망",
            }
            for code, via in found.items()
        ]


def addOverride(
    industryId: str,
    stockCode: str,
    stage: str,
    *,
    corpName: str = "",
    note: str = "",
    confidence: float = 1.0,
) -> None:
    """overrides.json에 확정 매핑을 추가/갱신한다.

    Capabilities:
        AI/운영자가 ``Industry()`` 자동 분류 오류를 발견했을 때 (industryId, stockCode, stage)
        확정 매핑을 ``overrides.json`` 에 기록. 다음 ``Industry().build()`` 호출 시 stage4_review
        에서 강제 반영.

    AI가 코드 실행 루프에서 호출하여 오분류를 보정한다.

    Parameters
    ----------
    industryId : str
        산업 ID (예: "semiconductor").
    stockCode : str
        종목코드.
    stage : str
        공정 단계 key (예: "equipment").
    corpName : str
        회사명 (선택).
    note : str
        보정 근거 (선택).
    confidence : float
        신뢰도 (기본 1.0).

    Returns
    -------
    None
        결과는 ``src/dartlab/industry/overrides.json`` 에 저장. 다음
        ``industry.build()`` 호출 시 반영된다.

    Raises:
        없음 — overrides.json 손상 시 빈 dict 로 시작 후 덮어쓰기.

    Example:
        >>> from dartlab.industry import addOverride
        >>> addOverride("semiconductor", "005930", "memory", note="DRAM 1 위")

    Guide:
        본 함수는 disk 즉시 반영이지만, 효과는 다음 ``build()`` 시점부터. taxonomy 미등록
        stage 면 stage4 가 fallback 에서 무시 — 사전에 ``Industry().map(industryId).stages`` 확인.

    When:
        AI/운영자가 자동 분류 오류를 발견한 즉시. 같은 (industryId, stockCode) 다시 호출 시
        덮어쓰기.

    How:
        ``data/industry/overrides.json`` 로드 → industryId 슬롯에 (stockCode, stage, ...) entry
        upsert → 직렬화. 다음 ``build()`` 에서 stage4_review 가 반영.

    Requires:
        - 쓰기 가능한 ``data/industry/overrides.json`` 경로

    See Also:
        - ``dartlab.industry.build.stage4_review.applyOverrides`` : 본 결과 반영
        - ``dartlab.industry.Industry.build`` : override 반영 빌드

    AIContext:
        AI 가 분석 후 "이 회사는 ○○ 단계로 분류해야" 라고 판단 시 직접 호출. ``note`` 에 근거
        문장 1 줄 (예: "DART 보고서 2024 사업보고서 사업의 내용 섹션 인용") 권장.
    """
    ovFile = _DATA_DIR / "overrides.json"
    data: dict = {}
    if ovFile.exists():
        try:
            data = json.loads(ovFile.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}

    ovList = data.setdefault(industryId, [])

    # 기존 항목 갱신 또는 추가
    for ov in ovList:
        if ov.get("stockCode") == stockCode:
            ov["stage"] = stage
            ov["confidence"] = confidence
            if corpName:
                ov["corpName"] = corpName
            if note:
                ov["note"] = note
            break
    else:
        entry: dict = {"stockCode": stockCode, "stage": stage, "confidence": confidence}
        if corpName:
            entry["corpName"] = corpName
        if note:
            entry["note"] = note
        ovList.append(entry)

    ovFile.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
