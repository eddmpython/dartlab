"""story 블록 카탈로그 -- 순서 + 메타데이터 단일 진실의 원천.

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
    """섹션 메타 정보.

    act : 6막 중 어느 막에 속하는가 (1~6). 0 = 메타 (IP/SV/T).
    partId : 세부 번호 ("1", "1-2", "5-3" 등 — act-index).
    """

    key: str
    partId: str
    title: str
    act: int = 0  # F1 Phase 10: 6막 매핑 명시 필드


# ── 섹션 정의 (리스트 순서 = 렌더링 순서) ──

SECTIONS: list[SectionMeta] = [
    # ── 제1막: 이 회사는 뭘 하는가 (사업 이해) ──
    SectionMeta("수익구조", "1", "수익 구조 -- 이 회사는 무엇으로 돈을 버는가", act=1),
    SectionMeta("성장성", "1-2", "성장성 -- 얼마나 빨리 성장하는가", act=1),
    # ── 제2막: 얼마나 잘 하는가 (수익성 + 원천) ──
    SectionMeta("수익성", "2", "수익성 -- 번 돈이 얼마나 남는가", act=2),
    SectionMeta("비용구조", "2-2", "비용 구조 -- 왜 이만큼 남는가", act=2),
    # ── 제3막: 현금이 실제로 도는가 (현금 전환) ──
    SectionMeta("현금흐름", "3", "현금흐름 -- 이익이 현금으로 전환되는가", act=3),
    SectionMeta("이익품질", "3-2", "이익의 질 -- 이익이 진짜인가", act=3),
    # ── 제4막: 자본 구조는 안전한가 (안정성) ──
    SectionMeta("자금조달", "4", "자본/부채 -- 돈의 출처와 구조는 건전한가", act=4),
    SectionMeta("안정성", "4-2", "안정성 -- 이 현금흐름으로 부채를 감당하는가", act=4),
    # ── 제5막: 번 돈을 어떻게 쓰는가 (자본배분) ──
    SectionMeta("자산구조", "5", "자산 구조 -- 자산을 어떻게 배치했는가", act=5),
    SectionMeta("효율성", "5-2", "효율성 -- 자산을 잘 굴리는가", act=5),
    SectionMeta("투자효율", "5-3", "투자 효율 -- 투자가 가치를 만드는가", act=5),
    SectionMeta("자본배분", "5-4", "자본 배분 -- 번 돈을 어디에 쓰는가", act=5),
    SectionMeta("재무정합성", "5-5", "재무 정합성 -- 재무제표가 서로 맞는가", act=5),
    SectionMeta("종합평가", "5-6", "종합 평가 -- 재무 상태를 한마디로", act=5),
    SectionMeta("신용평가", "5-7", "신용평가 -- 이 회사의 신용등급은 어디인가", act=5),
    # ── 제6막: 앞으로 어떻게 될 것인가 (전망 + 가치) ──
    SectionMeta("가치평가", "6", "가치평가 -- 이 회사의 적정 가치는 얼마인가", act=6),
    SectionMeta("지배구조", "6-2", "지배구조 -- 이 회사의 주인은 누구이며 감시는 작동하는가", act=6),
    SectionMeta("공시변화", "6-3", "공시변화 -- 이 회사의 공시가 뭐가 달라졌는가", act=6),
    SectionMeta("비교분석", "6-4", "비교분석 -- 이 회사는 시장에서 어디에 서 있는가", act=6),
    SectionMeta("매출전망", "6-5", "매출 전망 -- 이 회사의 매출은 어디로 가는가", act=6),
    SectionMeta("시장분석", "6-6", "시장 분석 -- 시장은 이 회사를 어떻게 보는가", act=6),
    SectionMeta("매크로", "6-7", "매크로 환경 -- 경제 사이클이 이 회사에 어떤 의미인가", act=6),
    # ── 개선 시나리오 (How축 — 진단 → 처방) ──
    SectionMeta("improvementPlan", "IP", "개선 시나리오 -- 이 회사가 더 좋아지려면 무엇을 해야 하는가", act=0),
    # ── 스토리 검증 (Damodaran 3-test) ──
    SectionMeta("storyValidation", "SV", "스토리 검증 -- 이 서사는 신뢰할 수 있는가", act=0),
    # ── AI 주도 서사 보고서 (thesis) ──
    SectionMeta("thesisReport", "T", "논제 검증 -- 가설을 증거로 검증한다", act=0),
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
    BlockMeta(
        "storyPrecedents", "유사 경로 선례", "수익구조", "Damodaran Possible Test — 같은 phase 기업 + 블로그 경험"
    ),
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
    BlockMeta("ocfDecomposition", "영업CF 분해", "현금흐름", "OCF = NI + 감가상각 + 운전자본 변동"),
    BlockMeta("cashFlowFlags", "현금흐름 플래그", "현금흐름", "현금 관련 경고/기회 신호"),
    # ── 수익성 ──
    BlockMeta("marginTrend", "마진 추이", "수익성", "매출총이익률, 영업이익률, 순이익률 시계열"),
    BlockMeta("returnTrend", "수익률 추이", "수익성", "ROE, ROA 시계열과 레버리지 분해"),
    BlockMeta("dupont", "듀퐁 분해", "수익성", "순이익률 x 자산회전율 x 재무레버리지"),
    BlockMeta("penmanDecomposition", "Penman 분해", "수익성", "ROCE = RNOA + FLEV×SPREAD (영업력 vs 레버리지)"),
    BlockMeta("roicTree", "ROIC Tree", "수익성", "ROIC = 마진×회전 분해 + 원인 추적"),
    BlockMeta("profitabilityFlags", "수익성 플래그", "수익성", "수익성 관련 경고/기회 신호"),
    # ── 성장성 ──
    BlockMeta("growthTrend", "성장률 추이", "성장성", "매출/영업이익/순이익 YoY 시계열"),
    BlockMeta("growthQuality", "성장 품질", "성장성", "외형 성장 vs 내실 성장 괴리, CAGR"),
    BlockMeta("cagrComparison", "CAGR 비교", "성장성", "계정별 CAGR 교차비교 — 구조적 변화 감지"),
    BlockMeta("growthFlags", "성장성 플래그", "성장성", "성장성 관련 경고/기회 신호"),
    # ── 안정성 ──
    BlockMeta("leverageTrend", "레버리지 추이", "안정성", "부채비율, 차입금의존도 시계열"),
    BlockMeta("coverageTrend", "이자보상 추이", "안정성", "이자보상배율 시계열"),
    BlockMeta("distressScore", "부실 판별", "안정성", "비금융 Altman Z'' 시계열과 구간 판정"),
    BlockMeta("marketRisk", "시장 리스크", "안정성", "베타, 변동성(ATR), 상대강도 — 시장 관점 리스크"),
    BlockMeta("scenarioSensitivity", "시나리오 민감도", "안정성", "OPM/매출/금리 shock별 핵심 지표 변화"),
    BlockMeta("criticalAssumptions", "핵심 가정", "안정성", "현 판단을 지탱하는 핵심 가정 + 위반 시 영향"),
    BlockMeta("stabilityFlags", "안정성 플래그", "안정성", "안정성 관련 경고/기회 신호"),
    # ── 효율성 ──
    BlockMeta("turnoverTrend", "회전율 추이", "효율성", "총자산/매출채권/재고 회전율 시계열"),
    BlockMeta("cccTrend", "CCC 추이", "효율성", "현금전환주기 구성요소 시계열"),
    BlockMeta("efficiencyFlags", "효율성 플래그", "효율성", "효율성 관련 경고/기회 신호"),
    # ── 종합평가 ──
    BlockMeta("scorecard", "재무 스코어카드", "종합평가", "5영역 등급(A-F) 요약"),
    BlockMeta("piotroski", "Piotroski F-Score", "종합평가", "9점 만점 재무 건전성 상세"),
    BlockMeta("summaryFlags", "종합 플래그", "종합평가", "전체 경고/기회 요약"),
    # ── 3-1 이익품질 ──
    BlockMeta("accrualAnalysis", "발생액 분석", "이익품질", "Sloan 발생액비율, 영업CF/순이익 시계열"),
    BlockMeta("earningsPersistence", "이익 지속성", "이익품질", "영업외손익 비중, 이익 변동성"),
    BlockMeta("beneishMScore", "Beneish M-Score (비발행)", "이익품질", "canonical 입력 계약 대기"),
    BlockMeta("richardsonAccrual", "Richardson 3계층 발생액", "이익품질", "WCACC/LTOACC/FINACC 분해 + 신뢰도"),
    BlockMeta("nonOperatingBreakdown", "영업외손익 분해", "이익품질", "금융/지분법/기타 항목별 영업외 추적"),
    BlockMeta("earningsQualityFlags", "이익품질 플래그", "이익품질", "이익 품질 경고 신호"),
    # ── 3-2 비용구조 ──
    BlockMeta("costBreakdown", "비용 비중 분해", "비용구조", "매출원가율, 판관비율 시계열"),
    BlockMeta("operatingLeverage", "영업레버리지", "비용구조", "DOL — 매출 변동 대비 이익 민감도"),
    BlockMeta("breakevenEstimate", "손익분기점", "비용구조", "BEP 매출, 안전마진 시계열"),
    BlockMeta("costStructureFlags", "비용구조 플래그", "비용구조", "비용 구조 경고 신호"),
    # ── 3-3 자본배분 ──
    BlockMeta("dividendPolicy", "배당 정책", "자본배분", "배당성향, 연속배당, 배당성장 시계열"),
    BlockMeta("shareholderReturn", "주주환원", "자본배분", "배당+자사주 vs FCF"),
    BlockMeta("reinvestment", "재투자", "자본배분", "CAPEX/매출, 유보율 시계열"),
    BlockMeta("fcfUsage", "FCF 사용처", "자본배분", "배당/부채상환/잔여 분해"),
    BlockMeta("dividendSustainability", "배당 지속성", "자본배분", "배당성향 5Y + FCF 커버리지 + 순이익 변동성"),
    BlockMeta("totalShareholderReturn", "총 주주환원율", "자본배분", "배당+자사주+감자 합산 5Y 총환원율"),
    BlockMeta("treasuryStockStatus", "자사주 현황", "자본배분", "자사주 취득/처분/소각 현황 (EDGAR: XBRL fallback)"),
    BlockMeta("capitalAllocationFlags", "자본배분 플래그", "자본배분", "자본배분 경고 신호"),
    # ── 3-4 투자효율 ──
    BlockMeta("roicTimeline", "ROIC 시계열", "투자효율", "ROIC, WACC 추정, Spread"),
    BlockMeta("investmentIntensity", "투자 강도", "투자효율", "CAPEX/매출, 유무형자산 비율"),
    BlockMeta("evaTimeline", "EVA 시계열", "투자효율", "경제적 부가가치 — NOPAT vs 자본비용"),
    BlockMeta("investmentFlags", "투자효율 플래그", "투자효율", "투자 분석 경고 신호"),
    # ── 3-5 재무정합성 ──
    BlockMeta("isCfDivergence", "IS-CF 괴리", "재무정합성", "순이익 vs 영업CF 괴리 시계열"),
    BlockMeta("isBsDivergence", "IS-BS 괴리", "재무정합성", "매출 vs 매출채권/재고 성장 괴리"),
    BlockMeta("anomalyScore", "이상 점수", "재무정합성", "교차검증 종합 이상 점수 0-100"),
    BlockMeta("effectiveTaxRate", "유효세율", "재무정합성", "유효세율, 법정세율 대비 갭"),
    BlockMeta("deferredTax", "이연법인세", "재무정합성", "이연법인세 자산/부채 추세"),
    BlockMeta("articulationCheck", "BS-CF 정합성", "재무정합성", "PPE/현금/자본 3표 연결 검증"),
    BlockMeta("crossStatementFlags", "재무정합성 플래그", "재무정합성", "교차검증+세금 경고 신호"),
    # ── 3-6 신용평가 ──
    BlockMeta(
        "creditMetrics", "신용평가 지표", "신용평가", "16개 핵심 지표 시계열 (채무상환/레버리지/유동성/현금흐름)"
    ),
    BlockMeta("creditScore", "신용등급 종합", "신용평가", "20단계 등급(AAA~D) + 5축 가중평균 + 업종 조정"),
    BlockMeta("creditHistory", "신용등급 시계열", "신용평가", "5개년 등급 변화 궤적"),
    BlockMeta("cashFlowGrade", "현금흐름등급", "신용평가", "eCR-1~6 현금흐름창출능력 별도 평가"),
    BlockMeta("creditScenario", "신용등급 시나리오", "신용평가", "부채비율/ICR 가정 변경 시 등급 변화"),
    BlockMeta("creditPeerPosition", "업종 내 신용 순위", "신용평가", "동종업계 대비 핵심 지표 위치"),
    BlockMeta("creditFlags", "신용 플래그", "신용평가", "신용 등급 하방/상방 신호"),
    BlockMeta("creditNarrative", "신용 서사", "신용평가", "7축 서사 — 왜 이 등급인가 (인과 체인)"),
    BlockMeta(
        "creditAudit", "신평사 대조", "신용평가", "외부 신평사(KIS/KR/NICE) 등급과 notch 차이 + 동의/비동의 근거"
    ),
    # ── 4-1 가치평가 ──
    BlockMeta("dcfValuation", "DCF 밸류에이션", "가치평가", "현금흐름 할인 모델 적정가치"),
    BlockMeta("ddmValuation", "DDM 밸류에이션", "가치평가", "배당 할인 모델 적정가치"),
    BlockMeta("relativeValuation", "상대가치", "가치평가", "PER/PBR/EV-EBITDA/PSR/PEG 배수 비교"),
    BlockMeta("residualIncome", "RIM 밸류에이션", "가치평가", "잔여이익모델 기반 적정가치"),
    BlockMeta("priceTarget", "확률 가중 목표주가", "가치평가", "5 시나리오 + Monte Carlo 목표가"),
    BlockMeta("reverseImplied", "역내재성장률", "가치평가", "시장이 내재하는 매출 성장률 역산"),
    BlockMeta("sensitivity", "민감도 분석", "가치평가", "WACC x 성장률 그리드"),
    BlockMeta("valuationSynthesis", "종합 적정가치", "가치평가", "DCF+DDM+상대가치 통합 판정"),
    BlockMeta("dFV", "dartlab 적정주가", "가치평가", "dFV — 적합도 가중 + 질적 조정 종합 적정가"),
    BlockMeta("methodFitness", "방법론 적합도", "가치평가", "DCF/RIM/DDM/상대가치 적합도 비교"),
    BlockMeta("qualityFactors", "질적 조정 요인", "가치평가", "신용/이익품질/거버넌스/사이클 할인·프리미엄"),
    BlockMeta("lifeCycleStage", "생애주기 단계", "가치평가", "Damodaran Corporate Life Cycle 단계 + 모델 힌트"),
    BlockMeta("valuationSins", "밸류에이션 정합성", "가치평가", "Damodaran 7 Sins + CF Consistency 검증"),
    BlockMeta("valuationFlags", "가치평가 플래그", "가치평가", "가치평가 관련 경고/기회 신호"),
    # ── 5-1 지배구조 ──
    BlockMeta("ownershipTrend", "최대주주 지분 추이", "지배구조", "최대주주 지분율 시계열과 주주 구성"),
    BlockMeta("boardComposition", "이사회 구성", "지배구조", "사외이사비율, 전체 임원 수"),
    BlockMeta("auditOpinionTrend", "감사의견 시계열", "지배구조", "감사의견과 감사인 변경 이력"),
    BlockMeta("executivePayDivergence", "임원보수 괴리", "지배구조", "임원보수 5Y 증가율 vs 매출/순이익 증가율"),
    BlockMeta("independentDirectorQuality", "외부이사 독립성", "지배구조", "외부이사 재임기간/비율 + 독립성 플래그"),
    BlockMeta("governanceFlags", "지배구조 플래그", "지배구조", "지배구조 관련 경고/기회 신호"),
    # ── 5-2 공시변화 ──
    BlockMeta("disclosureChangeSummary", "공시변화 종합", "공시변화", "전체 topic 변화 요약과 상위 변화"),
    BlockMeta("keyTopicChanges", "핵심 공시 변화", "공시변화", "사업개요/리스크/회계정책 등 핵심 topic 변화"),
    BlockMeta("changeIntensity", "변화 크기 분석", "공시변화", "바이트 기준 변화량 상위 topic"),
    BlockMeta("disclosureDeltaFlags", "공시변화 플래그", "공시변화", "공시변화 관련 경고/기회 신호"),
    # ── 5-3 비교분석 ──
    BlockMeta("peerRanking", "시장 내 백분위 순위", "비교분석", "핵심 재무비율 시장 내 백분위"),
    BlockMeta("riskReturnPosition", "수익-위험 포지션", "비교분석", "ROE x 부채비율 사분면 위치"),
    BlockMeta("peerBenchmarkFlags", "비교분석 플래그", "비교분석", "비교분석 관련 경고/기회 신호"),
    # ── 6-1 매출전망 ──
    BlockMeta("revenueForecast", "[추정] 매출 예측", "매출전망", "7-소스 앙상블 3-시나리오 매출 전망"),
    BlockMeta("segmentForecast", "[추정] 세그먼트별 전망", "매출전망", "부문별 개별 매출 성장 전망"),
    BlockMeta("proFormaHighlights", "[추정] Pro-Forma 전망", "매출전망", "매출->영업이익->순이익->FCF 전망"),
    BlockMeta("scenarioImpact", "[추정] 시나리오 영향", "매출전망", "매크로 시나리오별 매출/마진 영향"),
    BlockMeta("forecastMethodology", "예측 방법론", "매출전망", "소스 가중치, 가정, 데이터 품질"),
    BlockMeta("historicalRatios", "과거 구조 비율", "매출전망", "Pro-Forma 기반 과거 재무 비율"),
    BlockMeta("forecastFlags", "매출전망 플래그", "매출전망", "예측 관련 경고/제한 사항"),
    BlockMeta("calibrationReport", "예측 정확도 검증", "매출전망", "과거 예측의 확률 캘리브레이션 (Brier Score)"),
    BlockMeta(
        "plausibilityBand",
        "가정 타당성 대역",
        "매출전망",
        "섹터 피어 분포 대비 현재 forecast percentile (Plausible Test)",
    ),
    # ── 시장분석 ──
    BlockMeta("technicalVerdict", "기술적 종합 판단", "시장분석", "강세/중립/약세 판정, RSI, ADX, SMA/BB 위치"),
    BlockMeta("technicalSignals", "매매 신호", "시장분석", "골든크로스/RSI/MACD/볼린저 신호 최근 20일"),
    BlockMeta(
        "strategySnapshot",
        "전략별 진입 진단",
        "시장분석",
        "8 검증 스타일 백테스트 + 오늘 진입/청산 진단 (Sharpe/MDD/DSR)",
    ),
    BlockMeta("marketBeta", "시장 베타", "시장분석", "실측 베타, 알파, CAPM 기대수익률"),
    BlockMeta("fundamentalDivergence", "재무-시장 괴리", "시장분석", "재무 스코어 vs 기술적 판단 교차검증"),
    # ── 비교분석 (scan 교차 조합 관점) ──
    BlockMeta("peerPosition", "시장 내 위치", "비교분석", "전종목 수익성/성장/부채 백분위 + 교차 관점"),
    BlockMeta("governanceSummary", "지배구조 요약", "비교분석", "5축 점수/등급"),
    # ── 시장분석 (quant 서사) ──
    BlockMeta("trendNarrative", "추세 서사", "시장분석", "MA 정배열 + ADX + 12년 audit 근거"),
    BlockMeta("riskNarrative", "리스크 서사", "시장분석", "ATR 변동성 + 베타 + RSI"),
    BlockMeta("signalNarrative", "수급 신호 서사", "시장분석", "최근 20일 매수/매도 신호 집계"),
    BlockMeta("strategyNarrative", "전략 검증 서사", "시장분석", "8 스타일 Sharpe + 오늘 진입 신호"),
    BlockMeta("crosscheckNarrative", "재무-시장 교차 서사", "시장분석", "재무 등급 vs 기술적 판단"),
    BlockMeta("quantConclusion", "시장 결론", "시장분석", "5 서사 방향 카운트 → 매수/매도/혼조"),
    BlockMeta("marketAnalysisFlags", "시장분석 플래그", "시장분석", "기술적 신호 경고/기회"),
    BlockMeta(
        "factorTearSheet",
        "팩터 분해 (Fama-French)",
        "시장분석",
        "SMB/HML/RMW/CMA 4 팩터 long-short Sharpe + 한국 시장 alpha 원천 정량화 (Alphalens 표준)",
    ),
    BlockMeta(
        "riskDecomposition",
        "리스크 분해 (Multi-Factor)",
        "시장분석",
        "Barra-style B Σ_f Bᵀ + D — systematic vs idiosyncratic + 팩터별 리스크 기여도",
    ),
    BlockMeta(
        "factorIC",
        "팩터 예측력 (Cross-Sectional IC)",
        "시장분석",
        "Grinold & Kahn Ch.5 — 일별 Spearman IC × √252 = ICIR + hit rate (Alphalens 표준)",
    ),
    # 6막 분산 — 부실(자금조달) / 이익품질(이익품질) / 종합 (종합평가) / 가격기반 (시장분석)
    BlockMeta(
        "altmanFactor",
        "Altman Z/Z'' 적용성 분포",
        "자금조달",
        "비금융 적격 universe의 단일 모형 판별 점수 + 제외 사유와 방법론 원장",
    ),
    BlockMeta(
        "beneishFactor",
        "Beneish M-Score 비발행 계약",
        "이익품질",
        "원식 계정 의미와 공시 as-of가 보장될 때까지 structured unavailable",
    ),
    BlockMeta(
        "accrualsFactor",
        "Sloan Accrual Quality 분포",
        "이익품질",
        "Sloan 1996 — (NI-CFO)/TA, high/low 3 그룹, low accrual = long-short premium 후보",
    ),
    BlockMeta(
        "piotroskiFactor",
        "Piotroski F-Score 분포",
        "종합평가",
        "Piotroski 2000 — 9 재무 신호 합 (0~9점), strong/moderate/weak 분포 + 9 신호 시장 통과율",
    ),
    BlockMeta(
        "qFactor",
        "q-factor (Hou-Xue-Zhang)",
        "종합평가",
        "Hou-Xue-Zhang 2015 — ROE + (−assetGrowth) composite, 수익성×보수투자 복합 랭킹",
    ),
    BlockMeta(
        "qmj",
        "QMJ (Quality minus Junk)",
        "종합평가",
        "Asness-Frazzini-Pedersen 2019 — Profitability (ROE/ROA/CFOA) + Safety 합성 품질 랭킹",
    ),
    BlockMeta(
        "bab",
        "BAB (저변동성 프리미엄)",
        "시장분석",
        "Frazzini-Pedersen 2014 — 252일 beta 저베타 랭킹 + 60일 realized vol 보조",
    ),
    BlockMeta(
        "earningsSurprise",
        "Earnings Surprise (PEAD)",
        "시장분석",
        "Bernard-Thomas 1989 — YoY NI growth 횡단면 z-score, positive SUE drift 후보",
    ),
    BlockMeta(
        "fundMomentum",
        "펀더멘털 × 가격 모멘텀",
        "시장분석",
        "Chordia-Shivakumar 2006 — earnings growth + 12-1 price momentum 합성 랭킹",
    ),
    # ── 매크로 (시장 환경 + 기업-매크로 연결) ──
    BlockMeta("macroEnvironment", "경제 환경 종합", "매크로", "매크로 종합 판정 + 축별 기여도 + 자산배분 시사점"),
    BlockMeta("macroCycle", "경기 사이클", "매크로", "회복/확장/둔화/침체 4국면 + 전환 시퀀스 + 섹터 전략"),
    BlockMeta("macroRates", "금리 환경", "매크로", "금리 방향 + 수익률곡선 + 실질금리 국면"),
    BlockMeta("macroLiquidity", "유동성 환경", "매크로", "유동성 regime + FCI + 신용스프레드"),
    BlockMeta("macroSentiment", "시장 심리", "매크로", "공포탐욕 지수 + VIX 구간 + 분할매수 신호"),
    BlockMeta("macroForecast", "경기 전망", "매크로", "침체확률 + LEI 신호 + 성장 모멘텀"),
    BlockMeta("macroCorporate", "기업집계", "매크로", "전종목 이익사이클 + Ponzi비율 + 레버리지 추세"),
    BlockMeta("macroTrade", "교역조건", "매크로", "교역조건 방향 + 수출이익 함의 (KR)"),
    BlockMeta("macroFlags", "매크로 플래그", "매크로", "매크로 경고/기회 신호 집계"),
    BlockMeta("macroSensitivity", "매크로 민감도", "매크로", "금리/환율/유가 등 거시 지표가 이 회사에 미치는 영향"),
    BlockMeta("valuationBand", "밸류에이션 밴드", "매크로", "PER/PBR 과거 정규분포 대비 현재 위치"),
    BlockMeta(
        "companyCyclePosition",
        "사이클 위치 + 역사적 유사",
        "매크로",
        "현재 매크로 환경과 유사했던 과거 에포크 + 그 시점의 귀결",
    ),
    # ── 업종별 KPI (조건부 inject) ──
    BlockMeta("sectorKpi", "업종 특수 KPI", "종합평가", "업종별 핵심 지표 — 건설/반도체/게임/제약 자동 감지"),
    # ── 산업 밸류체인 (L2 industry 엔진) ──
    BlockMeta(
        "chainPosition",
        "산업 밸류체인 내 위치",
        "비교분석",
        "전 상장사 2,665사 중 이 회사가 속한 산업·공정·역할·스트림 + 같은 공정 피어",
    ),
    BlockMeta("sectorMetrics", "업종 실적 분포", "비교분석", "이 회사 업종의 OPM/CAGR/ROE 분포 + 업종 내 백분위"),
    BlockMeta("sectorOutlook", "섹터 전망", "비교분석", "업종 사이클 판정(확장/수축/안정) + 매크로 순풍/역풍"),
    # ── 개선 시나리오 (How축) ──
    BlockMeta("improvementLevers", "개선 레버 순위", "improvementPlan", "영향도 × 난이도별 개선 경로"),
    BlockMeta("gradeUpgradePath", "신용등급 상향 경로", "improvementPlan", "dCR 한 노치 상향에 필요한 것"),
    BlockMeta("technicalActionTargets", "기술적 행동 목표", "improvementPlan", "지지/저항 + 진입 트리거"),
    BlockMeta("cyclicalActionPlan", "사이클 대응", "improvementPlan", "사이클 위치 기반 행동 제안"),
    # ── storyValidation (Damodaran 3-test) ──
    BlockMeta("damodaran3test", "스토리 3-test", "storyValidation", "History/Experience/CommonSense 3단 검증 결과"),
    # ── thesisReport (AI 서사) ──
    BlockMeta("thesisStatement", "가설 선언", "thesisReport", "사용자 가설 + 측정 가능 명제 분해"),
    BlockMeta("evidenceFor", "지지 증거", "thesisReport", "가설을 뒷받침하는 수치/팩트"),
    BlockMeta("evidenceAgainst", "반박 증거", "thesisReport", "가설을 반박하는 수치/팩트"),
    BlockMeta("verdict", "판정", "thesisReport", "지지/반박/미결 + 신뢰도"),
]

# ── 파생 인덱스 (자동 생성, 직접 수정 금지) ──

_INDEX: dict[str, BlockMeta] = {b.key: b for b in _BLOCKS}

_BY_SECTION: dict[str, list[BlockMeta]] = {}
for _b in _BLOCKS:
    _BY_SECTION.setdefault(_b.section, []).append(_b)

_SECTION_INDEX: dict[str, SectionMeta] = {s.key: s for s in SECTIONS}

# ── 한글 label → key 역인덱스 ──

_LABEL_TO_KEY: dict[str, str] = {b.label: b.key for b in _BLOCKS}


def _suggest(query) -> str:
    """오타 시 유사 key/label 제안 메시지. int/float/list 입력도 방어."""
    from difflib import get_close_matches

    # Phase 4 G14b: int/float 등 비-str 방어 ('int' object is not iterable 버그)
    query = str(query) if not isinstance(query, str) else query

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


# ── 6막 헤더 (단일 진실의 원천) ──

ACT_HEADERS: dict[str, tuple[str, str]] = {
    "1": ("제1막: 이 회사는 뭘 하는가", "매출의 원천은 무엇이고 얼마나 빨리 성장하는가?"),
    "2": ("제2막: 얼마나 잘 하는가", "번 돈이 얼마나 남고, 왜 그만큼 남는가?"),
    "3": ("제3막: 현금이 실제로 도는가", "이익이 현금으로 전환되는가? 이익이 진짜인가?"),
    "4": ("제4막: 자본 구조는 안전한가", "부채를 감당할 수 있는가?"),
    "5": ("제5막: 번 돈을 어떻게 쓰는가", "자산, 배당, 재투자 — 가치를 만드는 배분인가?"),
    "6": ("제6막: 앞으로 어떻게 될 것인가", "적정 가치는 얼마이고, 어떤 리스크가 있는가?"),
}
