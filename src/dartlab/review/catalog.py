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
    SectionMeta("수익구조", "1-1", "수익 구조 -- 이 회사는 무엇으로 돈을 버는가"),
    SectionMeta("자금조달", "1-2", "자금 조달 -- 돈을 어디서 조달하는가"),
    SectionMeta("자산구조", "1-3", "자산 구조 -- 조달한 돈으로 뭘 준비했는가"),
    SectionMeta("현금흐름", "1-4", "현금흐름 -- 실제로 현금은 어떻게 흘렀는가"),
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
]

# ── 파생 인덱스 (자동 생성, 직접 수정 금지) ──

_INDEX: dict[str, BlockMeta] = {b.key: b for b in _BLOCKS}

_BY_SECTION: dict[str, list[BlockMeta]] = {}
for _b in _BLOCKS:
    _BY_SECTION.setdefault(_b.section, []).append(_b)

_SECTION_INDEX: dict[str, SectionMeta] = {s.key: s for s in SECTIONS}


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
