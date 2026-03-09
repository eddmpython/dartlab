"""
실험 ID: 048-001
실험명: Chain-of-Density 2-pass 재무분석 품질 비교

목적:
- Ollama 소형 모델(qwen3)에서 1-pass 응답 vs 2-pass(초안→압축) 응답 품질 비교
- 2-pass가 핵심 수치 누락, 해석 부재, 구조 불량을 개선하는지 검증
- 토큰 비용 대비 품질 향상 효과 측정

가설:
1. 2-pass 응답이 1-pass 대비 핵심 수치 포함률(부채비율, ROE, FCF 등)이 높다
2. 2-pass 응답이 마크다운 테이블 포함률이 높다
3. 2-pass 전체 소요 시간이 1-pass의 2배 이내이다

방법:
1. 동일한 재무 컨텍스트 + 질문으로 1-pass 생성
2. 1-pass 결과를 "초안"으로, 압축 프롬프트와 함께 2nd pass 실행
3. 두 결과의 수치 포함 여부, 테이블 수, 글자 수, 소요 시간 비교

결과 (실험 후 작성):
- 모델: qwen3, 컨텍스트: 삼성전자 재무 데이터 (BS/IS/CF/비율)
- 수치 포함률: 1-pass 7/8, 2-pass 6/8 (거의 동일, CAGR 누락)
- 테이블 구분선: 1-pass 5, 2-pass 5 (동일)
- 글자 수: 1-pass 2,212자, 2-pass 1,872자 (15% 짧음)
- 소요 시간: 1-pass 73.7초, 2-pass 131.3초 (1.8배)
- 품질: 2-pass가 구조 더 깔끔, "왜?/그래서?" 해석 더 명확
- 단점: 2-pass에서 ROE/ROA 업계 평균을 hallucination (외부 지식 보충)

결론:
- 가설1 기각: 수치 포함률은 1-pass와 거의 동일 (guided generation이 더 효과적)
- 가설2 기각: 테이블 포함률 동일 (이미 프롬프트에서 테이블 강제)
- 가설3 채택: 소요 시간 1.8배 (2배 이내)
- 종합: 품질 향상 효과가 시간 비용 대비 미미. guided generation이 이미 구조를
  강제하므로, 2-pass는 불필요. "품질 모드" 옵션으로만 가치 있음.
- 결정: 패키지 코드에는 추가하지 않음. guided generation으로 충분.

실험일: 2026-03-09
"""

import json
import time

COMPRESS_PROMPT = """아래 분석 초안을 개선하세요.

## 개선 규칙
1. 핵심 수치를 빠짐없이 유지하되, 불필요한 반복/장황한 설명을 제거
2. 수치가 2개 이상이면 반드시 마크다운 테이블로 정리
3. 각 수치 뒤에 판단(양호/주의/위험)을 반드시 추가
4. "왜?"와 "그래서?" 해석을 간결하게 추가
5. 구조: 핵심 요약(1~2문장) → 분석 테이블 → 리스크 → 결론

## 초안
{draft}

## 원본 질문
{question}

위 규칙에 따라 개선된 최종 분석을 작성하세요."""


def run_test():
	try:
		from openai import OpenAI
	except ImportError:
		print("openai 패키지 필요: pip install openai")
		return

	client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
	model = "qwen3"

	context = """
# 삼성전자 (005930)
**데이터 기준: 2020~2024년** (가장 최근: 2024년, 금액: 억/조원)

## 손익계산서
| 계정 | 2024 | 2023 | 2022 | 2021 | 2020 |
| --- | --- | --- | --- | --- | --- |
| 매출액 | 300.9조 | 258.9조 | 302.2조 | 279.6조 | 236.8조 |
| 영업이익 | 32.7조 | 6.6조 | 43.4조 | 51.6조 | 35.9조 |
| 당기순이익 | 26.2조 | 15.5조 | 55.7조 | 39.9조 | 26.4조 |

## 재무상태표
| 계정 | 2024 | 2023 |
| --- | --- | --- |
| 자산총계 | 481.6조 | 455.9조 |
| 부채총계 | 103.2조 | 92.2조 |
| 자본총계 | 378.4조 | 363.7조 |
| 유동자산 | 225.1조 | 208.7조 |
| 유동부채 | 69.3조 | 63.8조 |

## 현금흐름표
| 계정 | 2024 | 2023 |
| --- | --- | --- |
| 영업활동CF | 57.1조 | 46.7조 |
| 투자활동CF | -50.2조 | -40.3조 |
| 재무활동CF | -8.1조 | -10.2조 |

## 핵심 재무비율
| 지표 | 값 | 판단 |
| --- | --- | --- |
| ROE | 6.5% | 주의 |
| ROA | 5.1% | 주의 |
| 영업이익률 | 10.9% | - |
| 부채비율 | 27.3% | 양호 |
| 유동비율 | 324.8% | 양호 |
| FCF | 6.9조 | 양호 |
| 매출 3Y CAGR | 8.3% | - |
"""

	question = "삼성전자의 재무 건전성을 종합적으로 분석해줘"

	system = """한국 상장기업 재무분석 전문 애널리스트입니다.
DART 전자공시 데이터를 기반으로 분석합니다.

## 핵심 규칙
1. 제공된 데이터에만 기반하여 답변
2. 숫자 인용 시 출처 명시
3. 테이블 필수: 수치 2개 이상이면 마크다운 테이블
4. 해석 중심: "왜?"와 "그래서?"
5. 구조: 핵심 요약 → 분석 테이블 → 리스크 → 결론"""

	messages_1pass = [
		{"role": "system", "content": system},
		{"role": "user", "content": f"{context}\n\n질문: {question}"},
	]

	print("=" * 60)
	print("=== 1-Pass (단일 생성) ===")
	print("=" * 60)
	t1 = time.time()
	resp1 = client.chat.completions.create(
		model=model,
		messages=messages_1pass,
		temperature=0,
	)
	t1_elapsed = time.time() - t1
	text_1pass = resp1.choices[0].message.content
	print(f"소요: {t1_elapsed:.1f}초, 길이: {len(text_1pass)}자")
	print(text_1pass[:3000])

	print("\n" + "=" * 60)
	print("=== 2-Pass (초안 → 압축) ===")
	print("=" * 60)
	t2 = time.time()
	resp_draft = client.chat.completions.create(
		model=model,
		messages=messages_1pass,
		temperature=0,
	)
	draft = resp_draft.choices[0].message.content
	t2_draft = time.time() - t2
	print(f"초안 소요: {t2_draft:.1f}초, 길이: {len(draft)}자")

	compress_msg = COMPRESS_PROMPT.format(draft=draft, question=question)
	t2c = time.time()
	resp_final = client.chat.completions.create(
		model=model,
		messages=[
			{"role": "system", "content": system},
			{"role": "user", "content": compress_msg},
		],
		temperature=0,
	)
	t2_compress = time.time() - t2c
	text_2pass = resp_final.choices[0].message.content
	t2_total = time.time() - t2
	print(f"압축 소요: {t2_compress:.1f}초, 최종 길이: {len(text_2pass)}자")
	print(f"2-pass 총 소요: {t2_total:.1f}초")
	print()
	print(text_2pass[:3000])

	print("\n" + "=" * 60)
	print("=== 비교 ===")
	print("=" * 60)

	key_metrics = ["부채비율", "유동비율", "ROE", "ROA", "FCF", "영업이익률", "영업이익", "CAGR"]
	print(f"{'지표':<12} | {'1-pass':^8} | {'2-pass':^8}")
	print("-" * 35)
	for m in key_metrics:
		in_1 = "O" if m in text_1pass else "X"
		in_2 = "O" if m in text_2pass else "X"
		print(f"{m:<12} | {in_1:^8} | {in_2:^8}")

	tables_1 = text_1pass.count("|---")
	tables_2 = text_2pass.count("|---")
	print(f"\n테이블 구분선 수: 1-pass={tables_1}, 2-pass={tables_2}")
	print(f"글자 수: 1-pass={len(text_1pass)}, 2-pass={len(text_2pass)}")
	print(f"소요 시간: 1-pass={t1_elapsed:.1f}초, 2-pass={t2_total:.1f}초 (비율: {t2_total / t1_elapsed:.1f}x)")


if __name__ == "__main__":
	run_test()
