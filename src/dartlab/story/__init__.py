"""dartlab.story - L3 조합기 (분석엔진 X, 보고서 스토리보드).

c.story() 하나로 6 막 인과 보고서 생성 + 렌더링. 분석엔진 X - L2 5 분석엔진
(analysis · credit · macro · quant · industry) 끼리의 import 순환을 방지하기 위해
story 가 단독으로 다중 결합 책임을 짊어진다. 자체 계산 0, 모든 숫자는 하위 엔진 ref.
AI 는 이 위에 올라간다 (L4).

사용법::

    # 1. 블록 사전
    from dartlab.story import blocks
    b = blocks(company)
    b["매출 성장률"]                    # 한글 label로 접근
    b["growth"]                       # 영문 key로 접근
    b.growth                          # tab-complete 지원
    b                                 # 카탈로그 테이블 출력

    # 2. 자유 조립
    from dartlab.story import Story
    Story([b["부문별 매출 구성"], b["매출 성장률"]])

    # 3. 템플릿
    c.story()                        # 전체
    c.story("수익구조")               # 수익구조 템플릿
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.core.logger import getLogger

_log = getLogger(__name__)


from dartlab.story.blockMap import BlockMap
from dartlab.story.blocks import (
    Block,
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.story.catalog import (
    BlockMeta,
    SectionMeta,
    getBlockMeta,
    getSectionMeta,
    listBlocks,
    listSections,
    resolveKey,
)
from dartlab.story.layout import DEFAULT_LAYOUT, StoryLayout
from dartlab.story.registry import buildBlocks, buildStory
from dartlab.story.renderer import renderStory
from dartlab.story.report import buildReportModel
from dartlab.story.section import Section
from dartlab.story.summary import SummaryCard
from dartlab.story.utils import fmtAmt, fmtAmtScale, isTerminal, unifyTableScale


def blocks(company, *, basePeriod: str | None = None):
    """블록 사전 -- 한글 label, 영문 key, tab-complete 모두 지원.

    Capabilities:
        - 14축 분석의 모든 블록을 한 번에 생성
        - 한글 label ("매출 성장률"), 영문 key ("growth"), attribute (b.growth) 3중 접근
        - repr() 호출 시 전체 카탈로그 테이블 출력
        - 개별 블록 선택 후 Story([...])로 맞춤 보고서 조립

    Requires:
        Company 객체 (finance 데이터 자동 로드)

    AIContext:
        story 수퍼툴의 blocks action이 이 함수를 호출.
        블록 카탈로그를 AI에게 제공하여 사용자 질문에 맞는 블록 선택.

    Guide:
        - "블록 목록 보여줘" -> blocks(company) 호출 후 repr 출력
        - "매출 성장률만 보고 싶어" -> b = blocks(c); b["growth"]
        - "내가 원하는 것만 골라서 보고서" -> Story([b["growth"], b["marginTrend"]])
        - blocks()는 전체 블록 사전, story()는 템플릿 기반 보고서.

    SeeAlso:
        - Story: 블록을 조립하여 구조화 보고서 생성
        - buildStory: 템플릿 기반 전체 리뷰 자동 생성
        - listBlocks: 블록 메타데이터 목록 (블록 생성 없이 카탈로그만)

    Args:
        company: Company 객체.

    Returns:
        BlockMap - 한글/영문/attribute 접근 가능한 블록 사전.

    Example::

        import dartlab
        c = dartlab.Company("005930")
        b = blocks(c)
        b["매출 성장률"]          # 한글 label
        b["growth"]              # 영문 key
        b.growth                 # attribute (tab-complete)
        b                        # 카탈로그 테이블

    사용법::

        b = blocks(c)
        b["매출 성장률"]          # 한글 label
        b["growth"]              # 영문 key
        b.growth                 # attribute (tab-complete)
        b                        # 카탈로그 테이블
    """
    return buildBlocks(company, basePeriod=basePeriod)


def _flattenItems(items) -> list:
    """리스트/SelectResult 혼합을 flat하게 펼친다."""
    flat = []
    for item in items:
        if isinstance(item, list):
            flat.extend(item)
        elif item is not None:
            flat.append(item)
    return flat


@dataclass
class Story:
    """보고서 조합기 - 6 엔진 블록을 조합하여 6막 구조화 보고서 생성.

    analysis/credit/scan/quant/macro/industry 엔진의 결과를 블록 단위로 조합.
    11 보고서 타입 × 7 기업유형 템플릿. 해석하지 않고 다양한 관점의 근거를 배치.
    buildStory(company) 로 자동 생성, Story([blocks]) 로 자유 조립.

    Parameters
    ----------
    itemsOrStockCode : list | str, optional
        Block 리스트 (자유 조립) 또는 종목코드 문자열.
    stockCode : str
        종목코드.
    corpName : str
        회사명.
    sections : list[Section], optional
        Section 리스트 (직접 구성).
    layout : StoryLayout, optional
        렌더링 레이아웃 설정.

    Returns
    -------
    Story
        보고서 인스턴스. 주요 속성/메서드:
            sections : list[Section] - 6막별 섹션 목록
            render(fmt) : str - 렌더링 ("rich"/"html"/"markdown"/"json")
            toHtml() : str - HTML 출력
            toMarkdown() : str - Markdown 출력
            summaryCard : SummaryCard - 최상단 요약 카드

    Raises
    ------
    ValueError
        보고서 타입이 등록되지 않은 경우.
    RuntimeError
        Company 데이터 로드 실패 시.

    Examples
    --------
    >>> c.story()                              # 전체 보고서
    >>> c.story("수익구조")                     # 수익구조 섹션만
    >>> c.story(reportType="credit")           # 신용분석 보고서
    >>> from dartlab.story import blocks, Story
    >>> b = blocks(c)
    >>> Story([b["growth"], b["marginTrend"]])  # 자유 조립

    Notes
    -----
    사람의 진입점은 c.story() (Company 메서드). AI 는 dartlab.ask() 경유.
    4 출력 형식: rich(터미널), html, markdown, json.
    Jupyter/Colab/Marimo 에서 _repr_html_ 자동 렌더링.

    Guide
    -----
    AI 역할: AI는 story를 검증된 engine output을 보고서 섹션으로 조립하는 엔진으로 보고 원자료 없이 새 claim을 만들지 않는다.
    When: 종목의 종합 분석 보고서가 필요할 때.
    How: 11 타입 중 선택 - full(전체), executive(경영진 요약), credit(신용),
        valuation(가치평가), growth(성장), crisis(위기), audit(감사),
        dividend(배당), governance(지배구조), macro(매크로), thesis(투자논제).
    Verified:
        - credit 타입 → credit + analysis(안정성,현금흐름,자금조달) 조합 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - audit 타입 → analysis(이익품질,재무정합성) + 감사의견 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - governance 타입 → analysis(지배구조,공시변화) (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - dividend 타입 → analysis(수익구조,현금흐름,자본배분) (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - valuation 타입 → analysis(가치평가) + quant (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)
        - thesis 타입 → macro + analysis 복합 근거 수집 (observed via ai-ask, 2026-04-25 - 정식 Phase P 판정 아님)

    See Also
    --------
    analysis : 재무 심층 분석 - story 의 주요 데이터 공급원.
    credit : 신용 분석 - story credit 타입의 핵심 엔진.
    scan : 전종목 비교 - 동종업계 비교 블록 제공.
    quant : 기술적 분석 - 가격 기반 신호 블록 제공.
    macro : 거시 분석 - 매크로 환경 블록 제공.
    """

    stockCode: str = ""
    corpName: str = ""
    sections: list[Section] = field(default_factory=list)
    layout: StoryLayout = field(default_factory=StoryLayout)
    aiNote: str | None = None  # AI 미설정 시 안내 메시지
    circulationSummary: str = ""  # 재무제표 순환 서사 요약
    actTransitions: dict = field(default_factory=dict)  # 6막 전환 인과 문장
    summaryCard: SummaryCard | None = None  # 최상단 요약 카드
    template: str | None = None  # 스토리 템플릿 (사이클/성장/지주 등)
    templates: list[str] = field(default_factory=list)  # 복수 자동 감지 템플릿
    reportType: str | None = None  # 보고서 관점
    lensProducts: dict = field(default_factory=dict)  # 엔진별 Lens Product 원문
    lensGaps: list[dict] = field(default_factory=list)  # 대표 축 호출 또는 계약 결손
    _lensBundle: dict = field(default_factory=dict, repr=False)  # 같은 세션 최소 결과 재사용

    def __init__(
        self,
        itemsOrStockCode=None,
        /,
        stockCode: str = "",
        corpName: str = "",
        sections: list[Section] | None = None,
        layout: StoryLayout | None = None,
        aiNote: str | None = None,
        circulationSummary: str = "",
        summaryCard: SummaryCard | None = None,
        reportType: str | None = None,
        lensProducts: dict | None = None,
        lensGaps: list[dict] | None = None,
        template: str | None = None,
        templates: list[str] | None = None,
    ):
        """리스트 전달 시 자유 조립, 아니면 일반 생성."""
        if isinstance(itemsOrStockCode, list):
            # 자유 조립: Story([block1, block2, ...])
            self.stockCode = stockCode
            self.corpName = corpName
            flat = _flattenItems(itemsOrStockCode)
            self.sections = (
                [
                    Section(
                        key="custom",
                        partId="",
                        title="",
                        blocks=flat,
                    )
                ]
                if flat
                else []
            )
            self.layout = layout or StoryLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard
            self.reportType = reportType
            self.lensProducts = lensProducts or {}
            self.lensGaps = lensGaps or []
            self._lensBundle = {}
        elif isinstance(itemsOrStockCode, str):
            # Story("005930", corpName=..., ...)
            self.stockCode = itemsOrStockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or StoryLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard
            self.reportType = reportType
            self.lensProducts = lensProducts or {}
            self.lensGaps = lensGaps or []
            self._lensBundle = {}
        else:
            # Story(stockCode=..., corpName=..., ...)
            self.stockCode = stockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or StoryLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard
            self.reportType = reportType
            self.lensProducts = lensProducts or {}
            self.lensGaps = lensGaps or []
            self._lensBundle = {}

        self.actTransitions = {}
        self.template = template
        self.templates = list(templates or [])

    def render(self, fmt: str = "rich") -> str:
        """통합 렌더러 - rich/html/markdown/json 4종 출력.

        Capabilities:
            - rich: 터미널 컬러 텍스트 (기본값)
            - html: 웹 렌더링용 HTML
            - markdown: 문서/공유용 Markdown
            - json: 프로그래밍 소비용 JSON

        Requires:
            Story 인스턴스 (sections가 채워진 상태).

        AIContext:
            AI가 리뷰 결과를 텍스트로 변환할 때 render("markdown") 사용.

        Guide:
            - "보고서 텍스트로 보여줘" -> story.render() (기본 rich)
            - "HTML로 내보내기" -> story.render("html") 또는 story.toHtml()
            - "마크다운으로 저장" -> story.render("markdown")
            - "JSON으로 받고 싶어" -> story.render("json")

        SeeAlso:
            - toHtml: render("html") 편의 래퍼
            - toMarkdown: render("markdown") 편의 래퍼
            - toJson: render("json") 편의 래퍼

        Args:
            fmt: 출력 형식. "rich" | "html" | "markdown" | "json".

        Returns:
            str - 해당 형식으로 렌더링된 보고서 텍스트.

        Example::

            story = c.story()
            _log.info(story.render())              # rich 터미널 출력
            html = story.render("html")        # HTML 문자열
            md = story.render("markdown")      # Markdown 문자열
        """
        if fmt == "rich":
            return self._renderRich()
        if fmt == "html":
            from dartlab.story.formats import renderHtml

            return renderHtml(self, chartDir=getattr(self, "chartDir", None))
        if fmt == "markdown":
            from dartlab.story.formats import renderMarkdown

            return renderMarkdown(self, chartDir=getattr(self, "chartDir", None))
        if fmt == "json":
            from dartlab.story.formats import renderJson

            return renderJson(self)
        raise ValueError(f"지원하지 않는 렌더링 형식: {fmt}")

    def __repr__(self) -> str:
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderStory(console, self)
        return capture.get()

    def _repr_html_(self) -> str:
        """Jupyter / Colab / Marimo HTML 렌더링."""
        return self.toHtml()

    def _renderRich(self) -> str:
        """Rich Console capture → 텍스트."""
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderStory(console, self)
        return capture.get()

    # ── 편의 메서드 ──

    def toHtml(self) -> str:
        """HTML 형식으로 렌더링한다.

        Capabilities:
            - Story를 완전한 HTML 문자열로 변환
            - 인라인 스타일 포함 - 외부 CSS 불필요
            - 웹 페이지 삽입, 이메일 첨부, 파일 저장에 적합

        Requires:
            Story 인스턴스 (sections가 채워진 상태).

        AIContext:
            웹 렌더링이 필요한 컨텍스트에서 사용. server API가 이 메서드 활용.

        Guide:
            - "HTML로 내보내기" -> story.toHtml()
            - "웹 페이지에 넣고 싶어" -> story.toHtml()로 HTML 문자열 획득

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toMarkdown: Markdown 형식 변환
            - toJson: JSON 형식 변환

        Args:
            없음.

        Returns:
            str - HTML 문자열.

        Example::

            story = c.story()
            html = story.toHtml()
            with open("report.html", "w") as f:
                f.write(html)
        """
        return self.render("html")

    def toMarkdown(self) -> str:
        """Markdown 형식으로 렌더링한다.

        Capabilities:
            - Story를 Markdown 문자열로 변환
            - GitHub/Notion/문서 시스템에 바로 붙여넣기 가능
            - 테이블, 헤딩, 플래그 등 구조 보존

        Requires:
            Story 인스턴스 (sections가 채워진 상태).

        AIContext:
            AI 응답에 보고서를 포함할 때 Markdown 형식 사용.

        Guide:
            - "마크다운으로 저장" -> story.toMarkdown()
            - "노션에 복사하고 싶어" -> story.toMarkdown()

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toHtml: HTML 형식 변환
            - toJson: JSON 형식 변환

        Args:
            없음.

        Returns:
            str - Markdown 문자열.

        Example::

            story = c.story()
            md = story.toMarkdown()
            with open("report.md", "w") as f:
                f.write(md)
        """
        return self.render("markdown")

    def toJson(self) -> str:
        """JSON 형식으로 렌더링한다.

        Capabilities:
            - Story를 JSON 문자열로 직렬화
            - 프로그래밍 소비, API 응답, 저장/전송에 적합
            - 섹션/블록 구조가 그대로 보존됨

        Requires:
            Story 인스턴스 (sections가 채워진 상태).

        AIContext:
            server API /api/story 응답 형식으로 사용. 구조화된 데이터 교환.

        Guide:
            - "JSON으로 받고 싶어" -> story.toJson()
            - "API 응답으로 쓰려면" -> story.toJson()

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toHtml: HTML 형식 변환
            - toMarkdown: Markdown 형식 변환

        Args:
            없음.

        Returns:
            str - JSON 문자열.

        Example::

            story = c.story()
            import json
            data = json.loads(story.toJson())
        """
        return self.render("json")


__all__ = [
    "Story",
    "StoryLayout",
    "Section",
    "SummaryCard",
    "Block",
    "TextBlock",
    "HeadingBlock",
    "TableBlock",
    "FlagBlock",
    "MetricBlock",
    "BlockMap",
    "blocks",
    "listBlocks",
    "getBlockMeta",
    "resolveKey",
    "BlockMeta",
    "SectionMeta",
    "listSections",
    "getSectionMeta",
    "buildBlocks",
    "buildStory",
    "buildReportModel",
    "renderStory",
    "fmtAmt",
    "fmtAmtScale",
    "unifyTableScale",
    "isTerminal",
    "DEFAULT_LAYOUT",
]
