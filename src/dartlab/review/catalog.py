"""review 블록 카탈로그 -- 순서 + 메타데이터 단일 진실의 원천.

블록과 섹션의 정의, 순서, 라벨을 이 파일 하나에서 관리한다.
순서 변경은 _BLOCKS / SECTIONS 리스트에서만 한다.

규칙:
  - key는 불변 -- 한번 등록된 key는 변경/재사용 금지
  - label은 자유 -- 사용자 표시명은 언제든 변경 가능
  - 리스트 정의 순서 = 렌더링 순서
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BlockMeta:
    """블록 메타 정보."""

    key: str
    label: str
    section: str
    description: str


@dataclass
class SectionMeta:
    """섹션 메타 정보."""

    key: str
    partId: str
    title: str


# ── 섹션 정의 (리스트 순서 = 렌더링 순서) ──

SECTIONS: list[SectionMeta] = [
    # ── 1부: 사업구조 분석 ──
    SectionMeta("수익구조", "1-1", "수익 구조 -- 이 회사는 무엇으로 돈을 버는가"),
    SectionMeta("자금조달", "1-2", "자금 조달 -- 돈을 어디서 조달하는가"),
    SectionMeta("자산구조", "1-3", "자산 구조 -- 조달한 돈으로 뭘 준비했는가"),
    SectionMeta("현금흐름", "1-4", "현금흐름 -- 실제로 현금은 어떻게 흘렀는가"),
    # ── 2부: 재무비율 분석 ──
    SectionMeta("수익성", "2-1", "수익성 -- 이 회사는 얼마나 잘 벌고 있는가"),
    SectionMeta("성장성", "2-2", "성장성 -- 이 회사는 얼마나 빨리 성장하는가"),
    SectionMeta("안정성", "2-3", "안정성 -- 이 회사는 망하지 않는가"),
    SectionMeta("효율성", "2-4", "효율성 -- 이 회사는 자산을 잘 굴리는가"),
    SectionMeta("종합평가", "2-5", "종합 평가 -- 재무 상태를 한마디로"),
]

# ── 블록 정의 (리스트 순서 = 렌더링 순서. 순서 변경은 여기서만.) ──

_BLOCKS: list[BlockMeta] = [
    # ── 수익구조 ──
    BlockMeta("profile", "기업 개요", "수익구조", "기업명, 업종, 결산월 등 기본 정보"),
    BlockMeta("segmentComposition", "부문별 매출 구성", "수익구조", "주요 사업부문별 매출액과 영업이익 비중"),
    BlockMeta("segmentTrend", "부문별 매출 추이", "수익구조", "사업부문별 매출 시계열 변화"),
    BlockMeta("region", "지역별 매출", "수익구조", "내수/수출 또는 지역별 매출 비중"),
    BlockMeta("product", "제품별 매출", "수익구조", "제품/서비스별 매출 비중"),
    BlockMeta("growth", "매출 성장률", "수익구조", "YoY 성장률과 3개년 CAGR"),
    BlockMeta("growthContribution", "성장 기여 분해", "수익구조", "부문별 매출 성장 기여도"),
    BlockMeta("concentration", "매출 집중도", "수익구조", "HHI 기반 매출 편중도"),
    BlockMeta("revenueQuality", "매출 품질", "수익구조", "영업CF/순이익, 총이익률 추세"),
    BlockMeta("revenueFlags", "수익구조 플래그", "수익구조", "수익 관련 경고/기회 신호"),
    # ── 자금조달 ──
    BlockMeta("fundingSources", "자금 원천 구성", "자금조달", "내부유보/주주자본/금융차입/영업조달 비중"),
    BlockMeta("capitalOverview", "자본 구조 개요", "자금조달", "자기자본/부채 비율과 구성"),
    BlockMeta("capitalTimeline", "자본 구조 추이", "자금조달", "자본 구성 시계열 변화"),
    BlockMeta("debtTimeline", "부채 추이", "자금조달", "차입금/사채 시계열 변화"),
    BlockMeta("interestBurden", "이자 부담", "자금조달", "이자보상배율과 금융비용 추이"),
    BlockMeta("liquidity", "유동성", "자금조달", "유동비율, 당좌비율, 단기 지급 능력"),
    BlockMeta("cashFlowStructure", "자금흐름 구조", "자금조달", "영업/투자/재무CF 요약"),
    BlockMeta("distressIndicators", "재무 위험 지표", "자금조달", "Altman Z, 이자보상, 부채비율 종합"),
    BlockMeta("capitalFlags", "자금조달 플래그", "자금조달", "자금 관련 경고/기회 신호"),
    # ── 자산구조 ──
    BlockMeta("assetStructure", "자산 재분류", "자산구조", "영업/비영업 자산 재분류와 NOA"),
    BlockMeta("workingCapital", "운전자본 순환", "자산구조", "CCC, 매출채권/재고/매입채무 회전"),
    BlockMeta("capexPattern", "CAPEX 패턴", "자산구조", "설비투자 규모와 감가상각 대비"),
    BlockMeta("assetEfficiency", "자산 효율성", "자산구조", "총자산/고정자산 회전율"),
    BlockMeta("assetFlags", "자산구조 플래그", "자산구조", "자산 관련 경고/기회 신호"),
    # ── 현금흐름 ──
    BlockMeta("cashFlowOverview", "현금흐름 종합", "현금흐름", "영업/투자/재무CF 패턴과 FCF"),
    BlockMeta("cashQuality", "이익의 현금 전환", "현금흐름", "영업CF/순이익, 영업CF 마진"),
    BlockMeta("cashFlowFlags", "현금흐름 플래그", "현금흐름", "현금 관련 경고/기회 신호"),
    # ── 수익성 ──
    BlockMeta("marginTrend", "마진 추이", "수익성", "매출총이익률, 영업이익률, 순이익률 시계열"),
    BlockMeta("returnTrend", "수익률 추이", "수익성", "ROE, ROA 시계열과 레버리지 분해"),
    BlockMeta("dupont", "듀퐁 분해", "수익성", "순이익률 x 자산회전율 x 재무레버리지"),
    BlockMeta("profitabilityFlags", "수익성 플래그", "수익성", "수익성 관련 경고/기회 신호"),
    # ── 성장성 ──
    BlockMeta("growthTrend", "성장률 추이", "성장성", "매출/영업이익/순이익 YoY 시계열"),
    BlockMeta("growthQuality", "성장 품질", "성장성", "외형 성장 vs 내실 성장 괴리, CAGR"),
    BlockMeta("growthFlags", "성장성 플래그", "성장성", "성장성 관련 경고/기회 신호"),
    # ── 안정성 ──
    BlockMeta("leverageTrend", "레버리지 추이", "안정성", "부채비율, 차입금의존도 시계열"),
    BlockMeta("coverageTrend", "이자보상 추이", "안정성", "이자보상배율 시계열"),
    BlockMeta("distressScore", "부실 판별", "안정성", "Altman Z-Score 시계열과 종합 등급"),
    BlockMeta("stabilityFlags", "안정성 플래그", "안정성", "안정성 관련 경고/기회 신호"),
    # ── 효율성 ──
    BlockMeta("turnoverTrend", "회전율 추이", "효율성", "총자산/매출채권/재고 회전율 시계열"),
    BlockMeta("cccTrend", "CCC 추이", "효율성", "현금전환주기 구성요소 시계열"),
    BlockMeta("efficiencyFlags", "효율성 플래그", "효율성", "효율성 관련 경고/기회 신호"),
    # ── 종합평가 ──
    BlockMeta("scorecard", "재무 스코어카드", "종합평가", "5영역 등급(A-F) 요약"),
    BlockMeta("piotroski", "Piotroski F-Score", "종합평가", "9점 만점 재무 건전성 상세"),
    BlockMeta("summaryFlags", "종합 플래그", "종합평가", "전체 경고/기회 요약"),
]

# ── 파생 인덱스 (자동 생성, 직접 수정 금지) ──

_INDEX: dict[str, BlockMeta] = {b.key: b for b in _BLOCKS}

_BY_SECTION: dict[str, list[BlockMeta]] = {}
for _b in _BLOCKS:
    _BY_SECTION.setdefault(_b.section, []).append(_b)

_SECTION_INDEX: dict[str, SectionMeta] = {s.key: s for s in SECTIONS}

# ── 한글 label → key 역인덱스 ──

_LABEL_TO_KEY: dict[str, str] = {b.label: b.key for b in _BLOCKS}


def _suggest(query: str) -> str:
    """오타 시 유사 key/label 제안 메시지."""
    from difflib import get_close_matches

    candidates = list(_INDEX.keys()) + list(_LABEL_TO_KEY.keys())
    matches = get_close_matches(query, candidates, n=3, cutoff=0.4)
    if matches:
        return f" -- 혹시: {', '.join(matches)}?"
    return ""


def resolveKey(keyOrLabel: str) -> str | None:
    """영문 key 또는 한글 label → key 반환. 못 찾으면 None."""
    if keyOrLabel in _INDEX:
        return keyOrLabel
    mapped = _LABEL_TO_KEY.get(keyOrLabel)
    if mapped:
        return mapped
    return None


# ── 공개 API ──


def listBlocks(section: str | None = None) -> list[BlockMeta]:
    """블록 카탈로그 조회 (순서 보장).

    section이 None이면 전체, "수익구조" 등 지정하면 해당 섹션만.
    """
    if section is None:
        return list(_BLOCKS)
    return list(_BY_SECTION.get(section, []))


def getBlockMeta(key: str) -> BlockMeta | None:
    """블록 키로 메타 조회."""
    return _INDEX.get(key)


def listSections() -> list[SectionMeta]:
    """섹션 목록 (순서 보장)."""
    return list(SECTIONS)


def keysForSection(section: str) -> list[str]:
    """섹션에 속한 블록 key 리스트 (순서 보장)."""
    return [b.key for b in _BY_SECTION.get(section, [])]


def getSectionMeta(key: str) -> SectionMeta | None:
    """섹션 키로 메타 조회."""
    return _SECTION_INDEX.get(key)
