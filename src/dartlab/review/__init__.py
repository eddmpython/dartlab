"""dartlab.review — 분석 리뷰 패키지.

c.review() 하나로 분석 보고서 생성 + 렌더링.
AI reviewer는 이 위에 올라간다.

사용법::

    # 1. 블록 사전
    from dartlab.review import blocks
    b = blocks(company)
    b["매출 성장률"]                    # 한글 label로 접근
    b["growth"]                       # 영문 key로 접근
    b.growth                          # tab-complete 지원
    b                                 # 카탈로그 테이블 출력

    # 2. 자유 조립
    from dartlab.review import Review
    Review([b["부문별 매출 구성"], b["매출 성장률"]])

    # 3. 템플릿
    c.review()                        # 전체
    c.review("수익구조")               # 수익구조 템플릿
"""

from __future__ import annotations

from dataclasses import dataclass, field

from dartlab.review.blockMap import BlockMap
from dartlab.review.blocks import (
    Block,
    FlagBlock,
    HeadingBlock,
    MetricBlock,
    TableBlock,
    TextBlock,
)
from dartlab.review.catalog import (
    BlockMeta,
    SectionMeta,
    getBlockMeta,
    getSectionMeta,
    listBlocks,
    listSections,
    resolveKey,
)
from dartlab.review.layout import DEFAULT_LAYOUT, ReviewLayout
from dartlab.review.registry import buildBlocks, buildReview
from dartlab.review.renderer import renderReview
from dartlab.review.section import Section
from dartlab.review.summary import SummaryCard
from dartlab.review.utils import fmtAmt, fmtAmtScale, isTerminal, unifyTableScale


def blocks(company, *, basePeriod: str | None = None):
    """블록 사전 -- 한글 label, 영문 key, tab-complete 모두 지원.

    Capabilities:
        - 14축 분석의 모든 블록을 한 번에 생성
        - 한글 label ("매출 성장률"), 영문 key ("growth"), attribute (b.growth) 3중 접근
        - repr() 호출 시 전체 카탈로그 테이블 출력
        - 개별 블록 선택 후 Review([...])로 맞춤 보고서 조립

    Requires:
        Company 객체 (finance 데이터 자동 로드)

    AIContext:
        review 수퍼툴의 blocks action이 이 함수를 호출.
        블록 카탈로그를 AI에게 제공하여 사용자 질문에 맞는 블록 선택.

    Guide:
        - "블록 목록 보여줘" -> blocks(company) 호출 후 repr 출력
        - "매출 성장률만 보고 싶어" -> b = blocks(c); b["growth"]
        - "내가 원하는 것만 골라서 보고서" -> Review([b["growth"], b["margin"]])
        - blocks()는 전체 블록 사전, review()는 템플릿 기반 보고서.

    SeeAlso:
        - Review: 블록을 조립하여 구조화 보고서 생성
        - buildReview: 템플릿 기반 전체 리뷰 자동 생성
        - listBlocks: 블록 메타데이터 목록 (블록 생성 없이 카탈로그만)

    Args:
        company: Company 객체.

    Returns:
        BlockMap — 한글/영문/attribute 접근 가능한 블록 사전.

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
class Review:
    """분석 리뷰 — 14축 전략분석 결과를 구조화 보고서로 렌더링.

    Capabilities:
        - buildReview(company): 템플릿 기반 전체 리뷰 자동 생성 (2부 14축)
        - Review([blocks...]): 블록 자유 조립 (맞춤 보고서)
        - Review(stockCode=..., sections=[...]): 직접 구성
        - render(fmt): rich/html/markdown/json 4종 렌더링
        - toHtml(), toMarkdown(), toJson() 편의 메서드
        - Jupyter/Colab/Marimo 자동 HTML 렌더링 (_repr_html_)

    Requires:
        Company 객체 (buildReview 사용 시) 또는 Block 리스트.

    AIContext:
        review 수퍼툴이 이 클래스의 기능을 AI에게 노출.
        blocks action으로 블록 카탈로그, section으로 섹션별 리뷰.

    Guide:
        - "분석 보고서 보여줘" -> c.review() 또는 buildReview(company)
        - "수익구조만 보고 싶어" -> c.review("수익구조")
        - "HTML로 내보내기" -> review.toHtml()
        - "블록 목록 보여줘" -> blocks(company) (카탈로그 테이블)
        - "매출 성장률 블록만" -> b = blocks(c); b["growth"]

    SeeAlso:
        - analysis: 14축 전략분석 엔진 (Review의 데이터 공급원)
        - blocks: 블록 사전 (한글/영문/tab-complete)
        - Company.review: Company에서 바로 호출

    Args:
        itemsOrStockCode: Block 리스트 (자유 조립) 또는 종목코드 문자열.
        stockCode: 종목코드.
        corpName: 회사명.
        sections: Section 리스트.
        layout: ReviewLayout 설정.
        aiNote: AI 미설정 시 안내 메시지.
        circulationSummary: 재무제표 순환 서사 요약.

    Returns:
        Review 인스턴스. repr/render 호출 시 보고서 텍스트.

    Example::

        import dartlab
        c = dartlab.Company("005930")
        c.review()                        # 전체 리뷰
        c.review("수익구조")               # 수익구조 섹션만

        from dartlab.review import blocks, Review, buildReview
        b = blocks(c)
        b["growth"]                       # 매출 성장률 블록
        Review([b["growth"], b["margin"]])  # 자유 조립
    """

    stockCode: str = ""
    corpName: str = ""
    sections: list[Section] = field(default_factory=list)
    layout: ReviewLayout = field(default_factory=ReviewLayout)
    aiNote: str | None = None  # AI 미설정 시 안내 메시지
    circulationSummary: str = ""  # 재무제표 순환 서사 요약
    actTransitions: dict = field(default_factory=dict)  # 6막 전환 인과 문장
    summaryCard: SummaryCard | None = None  # 최상단 요약 카드
    template: str | None = None  # 스토리 템플릿 (사이클/성장/지주 등)

    def __init__(
        self,
        itemsOrStockCode=None,
        /,
        stockCode: str = "",
        corpName: str = "",
        sections: list[Section] | None = None,
        layout: ReviewLayout | None = None,
        aiNote: str | None = None,
        circulationSummary: str = "",
        summaryCard: SummaryCard | None = None,
    ):
        """리스트 전달 시 자유 조립, 아니면 일반 생성."""
        if isinstance(itemsOrStockCode, list):
            # 자유 조립: Review([block1, block2, ...])
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
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard
        elif isinstance(itemsOrStockCode, str):
            # Review("005930", corpName=..., ...)
            self.stockCode = itemsOrStockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard
        else:
            # Review(stockCode=..., corpName=..., ...)
            self.stockCode = stockCode
            self.corpName = corpName
            self.sections = sections or []
            self.layout = layout or ReviewLayout()
            self.aiNote = aiNote
            self.circulationSummary = circulationSummary
            self.summaryCard = summaryCard

    def render(self, fmt: str = "rich") -> str:
        """통합 렌더러 — rich/html/markdown/json 4종 출력.

        Capabilities:
            - rich: 터미널 컬러 텍스트 (기본값)
            - html: 웹 렌더링용 HTML
            - markdown: 문서/공유용 Markdown
            - json: 프로그래밍 소비용 JSON

        Requires:
            Review 인스턴스 (sections가 채워진 상태).

        AIContext:
            AI가 리뷰 결과를 텍스트로 변환할 때 render("markdown") 사용.

        Guide:
            - "보고서 텍스트로 보여줘" -> review.render() (기본 rich)
            - "HTML로 내보내기" -> review.render("html") 또는 review.toHtml()
            - "마크다운으로 저장" -> review.render("markdown")
            - "JSON으로 받고 싶어" -> review.render("json")

        SeeAlso:
            - toHtml: render("html") 편의 래퍼
            - toMarkdown: render("markdown") 편의 래퍼
            - toJson: render("json") 편의 래퍼

        Args:
            fmt: 출력 형식. "rich" | "html" | "markdown" | "json".

        Returns:
            str — 해당 형식으로 렌더링된 보고서 텍스트.

        Example::

            review = c.review()
            print(review.render())              # rich 터미널 출력
            html = review.render("html")        # HTML 문자열
            md = review.render("markdown")      # Markdown 문자열
        """
        if fmt == "rich":
            return self._renderRich()
        if fmt == "html":
            from dartlab.review.formats import renderHtml

            return renderHtml(self)
        if fmt == "markdown":
            from dartlab.review.formats import renderMarkdown

            return renderMarkdown(self)
        if fmt == "json":
            from dartlab.review.formats import renderJson

            return renderJson(self)
        raise ValueError(f"지원하지 않는 렌더링 형식: {fmt}")

    def __repr__(self) -> str:
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderReview(console, self)
        return capture.get()

    def _repr_html_(self) -> str:
        """Jupyter / Colab / Marimo HTML 렌더링."""
        from rich.console import Console

        console = Console(record=True, force_jupyter=True, width=120)
        renderReview(console, self)
        return console.export_html(inline_styles=True)

    def _renderRich(self) -> str:
        """Rich Console capture → 텍스트."""
        from rich.console import Console

        console = Console(highlight=False, force_terminal=True)
        with console.capture() as capture:
            renderReview(console, self)
        return capture.get()

    # ── 편의 메서드 ──

    def toHtml(self) -> str:
        """HTML 형식으로 렌더링한다.

        Capabilities:
            - Review를 완전한 HTML 문자열로 변환
            - 인라인 스타일 포함 — 외부 CSS 불필요
            - 웹 페이지 삽입, 이메일 첨부, 파일 저장에 적합

        Requires:
            Review 인스턴스 (sections가 채워진 상태).

        AIContext:
            웹 렌더링이 필요한 컨텍스트에서 사용. server API가 이 메서드 활용.

        Guide:
            - "HTML로 내보내기" -> review.toHtml()
            - "웹 페이지에 넣고 싶어" -> review.toHtml()로 HTML 문자열 획득

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toMarkdown: Markdown 형식 변환
            - toJson: JSON 형식 변환

        Args:
            없음.

        Returns:
            str — HTML 문자열.

        Example::

            review = c.review()
            html = review.toHtml()
            with open("report.html", "w") as f:
                f.write(html)
        """
        return self.render("html")

    def toMarkdown(self) -> str:
        """Markdown 형식으로 렌더링한다.

        Capabilities:
            - Review를 Markdown 문자열로 변환
            - GitHub/Notion/문서 시스템에 바로 붙여넣기 가능
            - 테이블, 헤딩, 플래그 등 구조 보존

        Requires:
            Review 인스턴스 (sections가 채워진 상태).

        AIContext:
            AI 응답에 보고서를 포함할 때 Markdown 형식 사용.

        Guide:
            - "마크다운으로 저장" -> review.toMarkdown()
            - "노션에 복사하고 싶어" -> review.toMarkdown()

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toHtml: HTML 형식 변환
            - toJson: JSON 형식 변환

        Args:
            없음.

        Returns:
            str — Markdown 문자열.

        Example::

            review = c.review()
            md = review.toMarkdown()
            with open("report.md", "w") as f:
                f.write(md)
        """
        return self.render("markdown")

    def toJson(self) -> str:
        """JSON 형식으로 렌더링한다.

        Capabilities:
            - Review를 JSON 문자열로 직렬화
            - 프로그래밍 소비, API 응답, 저장/전송에 적합
            - 섹션/블록 구조가 그대로 보존됨

        Requires:
            Review 인스턴스 (sections가 채워진 상태).

        AIContext:
            server API /api/review 응답 형식으로 사용. 구조화된 데이터 교환.

        Guide:
            - "JSON으로 받고 싶어" -> review.toJson()
            - "API 응답으로 쓰려면" -> review.toJson()

        SeeAlso:
            - render: 4종 형식 통합 렌더러
            - toHtml: HTML 형식 변환
            - toMarkdown: Markdown 형식 변환

        Args:
            없음.

        Returns:
            str — JSON 문자열.

        Example::

            review = c.review()
            import json
            data = json.loads(review.toJson())
        """
        return self.render("json")


__all__ = [
    "Review",
    "ReviewLayout",
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
    "buildReview",
    "renderReview",
    "fmtAmt",
    "fmtAmtScale",
    "unifyTableScale",
    "isTerminal",
    "DEFAULT_LAYOUT",
]
