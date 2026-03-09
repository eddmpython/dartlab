"""
실험 ID: 012
실험명: 종합 요약 텍스트 자동 생성

목적:
- 7개 인사이트 등급 + 이상치를 종합한 1~3문장 요약 자동 생성
- LLM 없이 룰 기반으로 자연스러운 한국어 요약문 구성
- 패키지 흡수 시 summary 필드로 활용

가설:
1. 등급 조합 패턴으로 5가지 이상의 기업 프로필 분류가 가능하다
2. 이상치 플래그를 포함하면 요약의 정보 밀도가 향상된다
3. 20종목 요약이 각각 차별화된 내용을 담는다 (동일 요약 0건)

방법:
1. 기업 프로필 분류 (우량/성장/안정/주의/위험)
2. 각 프로필에 맞는 요약 템플릿 + 핵심 수치 삽입
3. 이상치가 있으면 부가 문장 추가
4. 20종목 일괄 생성 + 수동 품질 검토

결과 (실험 후 작성):
- 20/20 고유 요약 생성 (중복 0건)
- 프로필 분류: premium 5, stable 1, mixed 6, caution 8, growth 0, distress 0
- premium: 삼성전자, SK하이닉스, NAVER, 미래에셋증권, 삼성생명
- stable: 삼성물산
- mixed: 카카오, KB금융, 신한지주, LG전자, 기아, 셀트리온
- caution: 현대차, POSCO홀딩스, LG화학, LG에너지, LG, SK이노, SK, 한전
- 한국어 조사 처리: 받침 판단 josa 함수 적용 (한글 정상, 영문은 한계)
- 이상치 포함 요약: danger 이상치 있으면 "다만~유의" 문장, 3건 이상이면 "모니터링 필요"
- keyMetric으로 핵심 수치 1개 추출 삽입 (매출 성장률, 영업이익률, ROE 등)

결론:
- 가설 1 채택: 5개 프로필(premium/stable/mixed/caution/distress) + growth 총 6개 설계, 4개 실제 분포
- 가설 2 채택: 이상치 포함 요약이 더 구체적 (현대차 CF 이슈, LG화학 이익품질 등)
- 가설 3 채택: 20종목 전부 고유 요약 (중복 0건)
- growth 미분류: 현재 20종목 중 perf+profit+opp 모두 A/B인 종목이 없음
- distress 미분류: 평균 1.5 미만 + risk F 조건이 엄격 (SK이노 1.3이나 risk=D)
- POSCO 홀딩스의 caution 분류가 약간 과도할 수 있음 (risk F 때문이나 실제는 중간 수준)

실험일: 2026-03-09
"""

import sys
sys.path.insert(0, "src")

import importlib.util
from pathlib import Path
from typing import Optional

import dartlab
dartlab.verbose = False

protoPath = Path(__file__).parent / "010_gradingCalibration.py"
spec = importlib.util.spec_from_file_location("proto010", protoPath)
proto = importlib.util.module_from_spec(spec)
spec.loader.exec_module(proto)

anomalyPath = Path(__file__).parent / "011_anomalyDetection.py"
specA = importlib.util.spec_from_file_location("proto011", anomalyPath)
protoA = importlib.util.module_from_spec(specA)
specA.loader.exec_module(protoA)


GRADE_SCORE = {"A": 4, "B": 3, "C": 2, "D": 1, "F": 0, "N": None}


def _josa(word: str, josaWithBatchim: str, josaWithout: str) -> str:
    if not word:
        return word + josaWithBatchim
    lastChar = ord(word[-1])
    if 0xAC00 <= lastChar <= 0xD7A3:
        hasBatchim = (lastChar - 0xAC00) % 28 != 0
        return word + (josaWithBatchim if hasBatchim else josaWithout)
    return word + josaWithBatchim


def _eun_neun(word: str) -> str:
    return _josa(word, "은", "는")


def _i_ga(word: str) -> str:
    return _josa(word, "이", "가")

STOCKS = {
    "005930": "삼성전자",
    "000660": "SK하이닉스",
    "005380": "현대자동차",
    "005490": "POSCO홀딩스",
    "035420": "NAVER",
    "035720": "카카오",
    "105560": "KB금융",
    "055550": "신한지주",
    "006800": "미래에셋증권",
    "032830": "삼성생명",
    "051910": "LG화학",
    "373220": "LG에너지솔루션",
    "066570": "LG전자",
    "003550": "LG",
    "000270": "기아",
    "068270": "셀트리온",
    "028260": "삼성물산",
    "096770": "SK이노베이션",
    "034730": "SK",
    "015760": "한국전력",
}

FINANCIAL_STOCKS = {"105560", "055550", "006800", "032830"}


def _avgGrade(grades: dict[str, str]) -> float:
    scores = [GRADE_SCORE[g] for g in grades.values() if GRADE_SCORE.get(g) is not None]
    if not scores:
        return 0
    return sum(scores) / len(scores)


def _classifyProfile(grades: dict[str, str], avgScore: float) -> str:
    perf = grades.get("performance", "C")
    profit = grades.get("profitability", "C")
    health = grades.get("health", "C")
    risk = grades.get("risk", "C")
    opp = grades.get("opportunity", "C")

    if avgScore >= 3.0 and risk in ["A", "B"]:
        return "premium"
    if perf in ["A", "B"] and profit in ["A", "B"] and opp in ["A", "B"]:
        return "growth"
    if health in ["A", "B"] and risk in ["A", "B"] and profit in ["A", "B"]:
        return "stable"
    if risk in ["D", "F"] or health in ["F"]:
        return "caution"
    if avgScore < 1.5:
        return "distress"
    return "mixed"


def _getStrengths(insights: dict) -> list[str]:
    strengths = []
    mapping = {
        "performance": "실적",
        "profitability": "수익성",
        "health": "재무건전성",
        "cashflow": "현금흐름",
        "governance": "지배구조",
    }
    for key, label in mapping.items():
        if key in insights and insights[key].grade in ["A"]:
            strengths.append(label)
    return strengths


def _getWeaknesses(insights: dict) -> list[str]:
    weaknesses = []
    mapping = {
        "performance": "실적",
        "profitability": "수익성",
        "health": "재무건전성",
        "cashflow": "현금흐름",
        "governance": "지배구조",
    }
    for key, label in mapping.items():
        if key in insights and insights[key].grade in ["F"]:
            weaknesses.append(label)
    return weaknesses


def _getKeyMetric(insights: dict) -> Optional[str]:
    for key in ["performance", "profitability"]:
        if key in insights:
            for detail in insights[key].details:
                for keyword in ["성장", "이익률", "ROE"]:
                    if keyword in detail:
                        return detail
    return None


def generateSummary(
    corpName: str,
    insights: dict,
    anomalies: list,
) -> str:
    grades = {}
    for cat in ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]:
        if cat in insights:
            grades[cat] = insights[cat].grade

    avgScore = _avgGrade(grades)
    profile = _classifyProfile(grades, avgScore)
    strengths = _getStrengths(insights)
    weaknesses = _getWeaknesses(insights)
    keyMetric = _getKeyMetric(insights)

    parts = []

    nameEunNeun = _eun_neun(corpName)

    if profile == "premium":
        if strengths:
            parts.append(f"{nameEunNeun} {', '.join(strengths)} 등 전반적으로 우수한 재무 상태를 보이는 우량 기업입니다.")
        else:
            parts.append(f"{nameEunNeun} 전반적으로 우수한 재무 상태를 보이는 우량 기업입니다.")

    elif profile == "growth":
        parts.append(f"{nameEunNeun} 성장성과 수익성이 돋보이는 기업입니다.")

    elif profile == "stable":
        parts.append(f"{nameEunNeun} 안정적인 재무구조를 갖춘 기업입니다.")

    elif profile == "caution":
        if weaknesses:
            parts.append(f"{nameEunNeun} {', '.join(weaknesses)} 측면에서 주의가 필요합니다.")
        else:
            riskGrade = grades.get("risk", "C")
            if riskGrade in ["D", "F"]:
                parts.append(f"{nameEunNeun} 재무 리스크 요인이 존재하여 주의가 필요합니다.")
            else:
                parts.append(f"{nameEunNeun} 일부 재무 지표에서 주의가 필요합니다.")

    elif profile == "distress":
        parts.append(f"{nameEunNeun} 여러 재무 지표에서 개선이 시급한 상황입니다.")

    else:
        if strengths and weaknesses:
            strengthsStr = ", ".join(strengths)
            weaknessesStr = ", ".join(weaknesses)
            parts.append(f"{nameEunNeun} {strengthsStr} 양호하나 {weaknessesStr}에서 약점을 보입니다.")
        elif strengths:
            if len(strengths) == 1:
                parts.append(f"{nameEunNeun} {_i_ga(strengths[0])} 양호한 기업입니다.")
            else:
                front = ", ".join(strengths[:-1])
                parts.append(f"{nameEunNeun} {front}, {_i_ga(strengths[-1])} 양호한 기업입니다.")
        else:
            parts.append(f"{nameEunNeun} 전반적으로 보통 수준의 재무 상태를 보입니다.")

    if keyMetric:
        parts.append(keyMetric + ".")

    dangerAnomalies = [a for a in anomalies if a.severity == "danger"]
    if dangerAnomalies:
        topAnomaly = dangerAnomalies[0].text.split("—")[0].strip()
        parts.append(f"다만 {topAnomaly} 점에 유의해야 합니다.")
    elif len(anomalies) >= 3:
        parts.append(f"이상 신호 {len(anomalies)}건이 감지되어 모니터링이 필요합니다.")

    return " ".join(parts)


if __name__ == "__main__":
    print(f"{'=' * 80}")
    print("  종합 요약 텍스트 생성 (20종목)")
    print(f"{'=' * 80}")

    summaries = {}
    profiles = {}

    for code, name in STOCKS.items():
        insights = proto.runFullAnalysis(code)
        if insights is None:
            continue

        isFinancial = code in FINANCIAL_STOCKS
        anomalies = protoA.runAnomalyDetection(code, isFinancial)

        grades = {}
        for cat in ["performance", "profitability", "health", "cashflow", "governance", "risk", "opportunity"]:
            if cat in insights:
                grades[cat] = insights[cat].grade

        avgScore = _avgGrade(grades)
        profile = _classifyProfile(grades, avgScore)
        summary = generateSummary(name, insights, anomalies)

        summaries[code] = summary
        profiles[code] = profile

        gradeStr = " ".join(f"{g}" for g in grades.values())
        print(f"\n  {name} ({code})")
        print(f"    등급: {gradeStr}")
        print(f"    프로필: {profile} (평균 {avgScore:.1f})")
        print(f"    이상치: {len(anomalies)}건")
        print(f"    요약: {summary}")

    print(f"\n\n{'=' * 80}")
    print("  프로필별 분포")
    print(f"{'=' * 80}")

    from collections import Counter
    profileCounts = Counter(profiles.values())
    for p in ["premium", "growth", "stable", "mixed", "caution", "distress"]:
        c = profileCounts.get(p, 0)
        stocks = [STOCKS[k] for k, v in profiles.items() if v == p]
        stockStr = ", ".join(stocks) if stocks else ""
        print(f"  {p:10s}: {c}종목  {stockStr}")

    print(f"\n\n{'=' * 80}")
    print("  요약 중복 체크")
    print(f"{'=' * 80}")
    uniqueSummaries = set(summaries.values())
    print(f"  고유 요약: {len(uniqueSummaries)} / {len(summaries)}종목")
    if len(uniqueSummaries) < len(summaries):
        for s in uniqueSummaries:
            dupes = [STOCKS[k] for k, v in summaries.items() if v == s]
            if len(dupes) > 1:
                print(f"  중복: {', '.join(dupes)}")
                print(f"    \"{s}\"")
