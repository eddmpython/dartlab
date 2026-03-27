"""분석 영역별 스킬 카탈로그.

도구를 지정하지 않는다 — 분석 목표만 선언.
8대 영역이 안정화되면서 자연스럽게 효과가 향상된다.
"""

from __future__ import annotations

from dartlab.ai.skills.registry import Skill

SKILLS: tuple[Skill, ...] = (
    Skill(
        id="profitability",
        name="수익성 심층 분석",
        triggerKeywords=("수익성", "이익률", "마진", "ROE", "ROA", "영업이익률"),
        analysisGoals=(
            "ROE를 DuPont 분해하여 수익성/효율성/레버리지 동인 식별",
            "영업이익률과 원가율 추세에서 비용 구조 변화 파악",
            "영업CF/순이익 비율로 이익의 질 판단",
            "부문별 수익성 차이가 있으면 세그먼트 분해",
        ),
        synthesisGuide="DuPont 분해 → 이익의 질 → 비용 동인 → 인과 관계 서술",
        checkpoints=(
            "DuPont 3요소 분해가 있는가?",
            "CF/NI 비율을 인용했는가?",
            "비용 구조 변화의 원인을 설명했는가?",
        ),
    ),
    Skill(
        id="health",
        name="재무 건전성 분석",
        triggerKeywords=("건전성", "부채", "유동성", "안정성", "재무구조", "부채비율"),
        analysisGoals=(
            "부채비율과 유동비율 추세로 구조적 안정성 판단",
            "이자보상배율과 차입금 만기 구조 확인",
            "운전자본 사이클(매출채권+재고-매입채무) 추이 분석",
            "현금성 자산 대비 단기 의무 커버리지 확인",
        ),
        synthesisGuide="레버리지 구조 → 유동성 계층 → 부채 만기 → 종합 건전성 판단",
        checkpoints=(
            "유동비율과 부채비율 수치를 인용했는가?",
            "이자보상배율을 확인했는가?",
            "단기 유동성 위험을 평가했는가?",
        ),
    ),
    Skill(
        id="valuation",
        name="밸류에이션 분석",
        triggerKeywords=("밸류에이션", "적정가치", "목표가", "저평가", "고평가", "PER", "PBR", "DCF"),
        analysisGoals=(
            "핵심 멀티플(PER, PBR, EV/EBITDA) 산출 및 업종 비교",
            "이익 성장률과 지속가능성을 근거로 적정 멀티플 범위 추정",
            "가능하면 DCF 관점에서 내재가치 범위 제시",
            "안전마진(현재가 vs 적정가치 범위) 판단",
        ),
        synthesisGuide="멀티플 비교 → 성장률 근거 → 적정가치 범위 → 안전마진 판단",
        checkpoints=(
            "PER/PBR 수치와 업종 비교가 있는가?",
            "성장률 근거를 제시했는가?",
            "적정가치 범위를 제시했는가? (단일 목표가 아닌 범위)",
        ),
    ),
    Skill(
        id="risk",
        name="리스크 분석",
        triggerKeywords=("리스크", "위험", "위기", "불확실성", "적색신호"),
        analysisGoals=(
            "재무 리스크: 유동성, 레버리지, 이자보상 역량",
            "사업 리스크: 매출처 집중, 공급망 의존, 규제 변화",
            "회계 리스크: 감사의견 변화, 특수관계자 거래, 회계정책 변경",
            "공시에서 경영진이 직접 언급한 리스크 요인 확인",
        ),
        synthesisGuide="재무 리스크 → 사업 리스크 → 회계 리스크 → 종합 위험도 판단",
        checkpoints=(
            "적색 신호 체크리스트를 적용했는가?",
            "공시 원문에서 리스크 관련 서술을 인용했는가?",
        ),
    ),
    Skill(
        id="strategy",
        name="사업 전략 분석",
        triggerKeywords=("사업", "전략", "경쟁우위", "비즈니스모델", "사업구조", "사업개요"),
        analysisGoals=(
            "사업 구조: 부문별 매출 비중과 수익성 차이",
            "경쟁 우위: R&D 투자 강도, 마진 프리미엄, 고객 집중도",
            "성장 전략: 유기적 성장 vs 인수, CAPEX 방향",
            "공시 원문에서 경영진의 전략 서술 확인",
        ),
        synthesisGuide="사업 구조 분해 → 경쟁 우위 식별 → 성장 전략 평가 → 지속가능성 판단",
        checkpoints=(
            "부문별 매출/이익 비중을 분해했는가?",
            "R&D/CAPEX 투자 방향을 확인했는가?",
        ),
    ),
    Skill(
        id="accounting",
        name="회계 품질 분석",
        triggerKeywords=("회계", "감사", "분식", "이익의질", "발생주의", "회계정책"),
        analysisGoals=(
            "Accrual Ratio 계산: (순이익-영업CF)/평균자산 — 10% 초과 시 의심",
            "감사의견 변화와 감사인 교체 이력 확인",
            "회계정책 변경(수익인식, 자본화, 감가상각) 영향 파악",
            "매출채권/재고 증가율과 매출/원가 증가율 비교",
        ),
        synthesisGuide="Accrual Ratio → 감사 이력 → 회계정책 변경 → 이익의 질 종합",
        checkpoints=(
            "CF/NI 비율 또는 Accrual Ratio를 계산했는가?",
            "감사의견을 확인했는가?",
        ),
    ),
    Skill(
        id="dividend",
        name="배당 분석",
        triggerKeywords=("배당", "배당금", "배당률", "배당성향", "주주환원"),
        analysisGoals=(
            "배당 추이: 배당금, 배당수익률, 배당성향 3~5년 시계열",
            "배당 지속가능성: FCF 대비 배당금, 이익 안정성",
            "주주환원 정책: 자사주 매입, 소각 이력 확인",
            "동종업종 배당 수준 비교 (가능 시)",
        ),
        synthesisGuide="배당 추이 → 지속가능성(FCF) → 주주환원 정책 → 매력도 판단",
        checkpoints=(
            "배당성향과 배당수익률 수치를 인용했는가?",
            "FCF 대비 배당 커버리지를 확인했는가?",
        ),
    ),
    Skill(
        id="comprehensive",
        name="종합 분석",
        triggerKeywords=("종합", "전반", "전체", "총평", "분석해줘", "어때"),
        analysisGoals=(
            "사업 구조와 경쟁 포지셔닝 파악",
            "핵심 재무 지표(수익성, 건전성, 성장성) 3~5년 추세",
            "이익의 질과 현금흐름 프로파일",
            "적색 신호 체크 및 리스크 요인 식별",
            "강점/약점 정리와 Bull/Bear 논거",
        ),
        synthesisGuide="사업 구조 → 재무 추세 → 이익의 질 → 리스크 → 강점/약점 → 종합 판단",
        checkpoints=(
            "최소 3개 이상의 재무 비율을 인용했는가?",
            "강점과 약점을 균형 있게 제시했는가?",
            "Bull/Bear 논거를 제시했는가?",
        ),
    ),
)
