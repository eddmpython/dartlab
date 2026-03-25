"""실험 ID: 097-003
실험명: sections topic별 페르소나 질문 실제 검증

목적:
- sections 68개 topic을 기반으로 회계사/감사/투자자/애널리스트가 할 수 있는 질문을 설계
- 실제 ollama에 질문→답변을 받고, AI가 dartlab 데이터를 제대로 쓰는지 직접 판단
- 자동 채점이 아닌 답변 내용 자체를 보고 개선사항/장기 추가기능을 도출

가설:
1. sections 기반 질문은 docs source 데이터를 직접 활용해야 함
2. AI가 sections 원문을 인용하면서 답변할 수 있어야 함
3. finance source topic은 정확한 수치를 제시해야 함

방법:
1. 주요 chapter별 대표 topic 선정 (10~15개)
2. 각 topic에 대해 페르소나별 1개 질문 (회계사/투자자/애널리스트)
3. 질문→답변→판단을 기록

결과:
- 15개 sections topic 기반 질문 실행 완료
- 답변 정상: 8건 (53%), 수치 의심: 4건 (27%), 심각한 문제: 3건 (20%)
- 심각한 문제 3건:
  1. fsSummary → "재무데이터 없음" (finance 있는데 context 미주입)
  2. mdnaOverview → 빈 답변 (sections 데이터 있는데 전달 실패)
  3. executivePay → "데이터 미포함" (report API 있는데 context 미포함)
- hallucination 의심: rawMaterial(국내35%/해외65% 출처불명), productService(TV 308.6조)
- 수치 불일치: liquidityAndCapitalResources(부채비율 45.2% vs 65.3% 같은 질문에 다른 수치)

결론:
1. AI가 dartlab을 "제대로" 쓰지 못하는 핵심 원인 3가지 확인:
   - finance_context.py의 route→module 매핑이 불완전 (fsSummary route=finance인데 context 누락)
   - sections 데이터 중 일부 topic이 context builder에서 빠짐 (mdnaOverview)
   - report API 데이터가 context에 포함되는 조건이 너무 좁음 (executivePay)
2. hallucination 방지: context에 정확한 테이블이 없으면 LLM이 수치를 만들어냄
3. 장기 추가기능:
   - 답변 내 수치 vs 실제 데이터 교차검증 post-check
   - sections topic별 context 주입 커버리지 맵 자동 생성
   - "근거 인용" 강화 (어떤 section에서 왔는지 출처 명시)

실험일: 2026-03-25
"""

from __future__ import annotations

import gc
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "src"))

# sections topic 기반 페르소나별 예상 질문
# chapter → topic → 페르소나별 질문
SECTION_QUESTIONS = [
    # I. 회사의 개요
    {
        "topic": "companyOverview",
        "chapter": "I",
        "persona": "investor",
        "question": "삼성전자 회사 개요에서 최근 변동 사항이 있나",
        "checkPoints": ["설립일/상장일", "주요 사업 영역", "종업원 수"],
    },
    {
        "topic": "dividend",
        "chapter": "I",
        "persona": "investor",
        "question": "삼성전자 배당 현황과 최근 3년 변화 알려줘",
        "checkPoints": ["DPS 금액", "배당수익률", "배당성향"],
    },
    # II. 사업의 내용
    {
        "topic": "businessOverview",
        "chapter": "II",
        "persona": "analyst",
        "question": "삼성전자 사업보고서 기준 사업 구조와 매출 구성 설명해줘",
        "checkPoints": ["DX/DS/SDC/Harman 부문", "부문별 매출 비중", "주요 제품"],
    },
    {
        "topic": "productService",
        "chapter": "II",
        "persona": "analyst",
        "question": "삼성전자 주요 제품별 매출 추이와 시장 점유율 알려줘",
        "checkPoints": ["DRAM/NAND/스마트폰/TV", "매출 금액", "시장 점유율 수치"],
    },
    {
        "topic": "riskDerivative",
        "chapter": "II",
        "persona": "accountant",
        "question": "삼성전자 파생상품 및 리스크 관리 현황 분석해줘",
        "checkPoints": ["환율 리스크", "파생상품 평가손익", "헷지 정책"],
    },
    {
        "topic": "rawMaterial",
        "chapter": "II",
        "persona": "analyst",
        "question": "삼성전자 원재료 조달 구조와 가격 변동 영향 분석해줘",
        "checkPoints": ["주요 원재료", "조달 방식", "가격 변동"],
    },
    # III. 재무에 관한 사항
    {
        "topic": "fsSummary",
        "chapter": "III",
        "persona": "accountant",
        "question": "삼성전자 재무제표 요약 기준 최근 3년 주요 지표 변화 알려줘",
        "checkPoints": ["매출/영업이익/당기순이익", "총자산/총부채", "연도별 비교"],
    },
    {
        "topic": "consolidatedNotes",
        "chapter": "III",
        "persona": "accountant",
        "question": "삼성전자 연결재무제표 주석에서 중요 회계 정책 변경 사항 있나",
        "checkPoints": ["회계 정책 변경", "IFRS 적용", "추정의 불확실성"],
    },
    # IV. 이사의 경영진단 및 분석의견
    {
        "topic": "mdnaOverview",
        "chapter": "IV",
        "persona": "analyst",
        "question": "삼성전자 경영진 분석 의견에서 올해 핵심 이슈가 뭔지 정리해줘",
        "checkPoints": ["경영진 시각", "사업 전망", "핵심 리스크"],
    },
    {
        "topic": "liquidityAndCapitalResources",
        "chapter": "IV",
        "persona": "accountant",
        "question": "삼성전자 유동성과 자본 조달 상황 분석해줘",
        "checkPoints": ["유동비율", "차입금 현황", "자금 조달 계획"],
    },
    # V. 감사인의 감사의견등
    {
        "topic": "internalControl",
        "chapter": "V",
        "persona": "accountant",
        "question": "삼성전자 내부통제 시스템 현황과 감사 의견 알려줘",
        "checkPoints": ["내부통제 의견", "감사위원회", "주요 지적사항"],
    },
    # VII. 주주에 관한 사항
    {
        "topic": "majorHolder",
        "chapter": "VII",
        "persona": "investor",
        "question": "삼성전자 최대주주 및 특수관계인 지분 변동 현황 알려줘",
        "checkPoints": ["최대주주 이름/지분율", "특수관계인 합산", "지분 변동"],
    },
    # VIII. 임원 및 직원 등에 관한 사항
    {
        "topic": "employee",
        "chapter": "VIII",
        "persona": "analyst",
        "question": "삼성전자 직원 수 변화와 평균 근속연수 추이 알려줘",
        "checkPoints": ["총 직원 수", "남녀 비율", "평균 근속연수", "평균 급여"],
    },
    {
        "topic": "executivePay",
        "chapter": "VIII",
        "persona": "investor",
        "question": "삼성전자 등기임원 보수 총액과 개인별 보수 현황 알려줘",
        "checkPoints": ["보수 총액", "개인별 상위 보수", "성과급 비중"],
    },
    # XI. 재무제표등
    {
        "topic": "contingentLiability",
        "chapter": "XI",
        "persona": "accountant",
        "question": "삼성전자 우발채무 및 약정사항 현황 분석해줘",
        "checkPoints": ["소송 현황", "보증/약정 금액", "리스크 수준"],
    },
]


def runQuestion(question: str, stockCode: str = "005930") -> str:
    """질문 실행 → 답변 반환."""
    import dartlab
    dartlab.llm.configure(provider="ollama", model="qwen3:latest")
    return dartlab.ask(stockCode, question, stream=False)


def main():
    results = []
    for i, q in enumerate(SECTION_QUESTIONS):
        print(f"\n{'=' * 70}")
        print(f"[{i + 1}/{len(SECTION_QUESTIONS)}] {q['topic']} ({q['persona']})")
        print(f"질문: {q['question']}")
        print(f"체크포인트: {q['checkPoints']}")
        print(f"{'=' * 70}")

        try:
            answer = runQuestion(q["question"])
            print(f"\n--- 답변 ---")
            print(answer[:500] if answer else "(빈 답변)")
            if answer and len(answer) > 500:
                print(f"... (총 {len(answer)}자)")

            results.append({
                "topic": q["topic"],
                "chapter": q["chapter"],
                "persona": q["persona"],
                "question": q["question"],
                "checkPoints": q["checkPoints"],
                "answerLength": len(answer) if answer else 0,
                "answerPreview": (answer[:300] if answer else ""),
                "hasAnswer": bool(answer and len(answer) > 50),
            })
        except Exception as e:
            print(f"\n[ERROR] {e}")
            results.append({
                "topic": q["topic"],
                "chapter": q["chapter"],
                "persona": q["persona"],
                "question": q["question"],
                "error": str(e),
                "hasAnswer": False,
            })
        gc.collect()

    # 저장
    outDir = Path(__file__).parent
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    outPath = outDir / f"sections_verify_{ts}.jsonl"
    with open(outPath, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n저장: {outPath}")

    # 요약
    total = len(results)
    answered = sum(1 for r in results if r.get("hasAnswer"))
    errors = sum(1 for r in results if "error" in r)
    print(f"\n총 {total}건: 답변 {answered}건, ERROR {errors}건")


if __name__ == "__main__":
    main()
