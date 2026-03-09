"""
실험 ID: 047-001
실험명: Ollama JSON Schema Guided Generation 테스트

목적:
- Ollama의 OpenAI 호환 엔드포인트에서 response_format JSON schema 지원 여부 확인
- 재무분석 응답을 구조화된 JSON으로 강제할 수 있는지 검증
- 소형 모델(llama3.1:8b)에서 JSON 구조 준수율 측정

가설:
1. response_format으로 JSON schema를 전달하면 모델이 구조를 준수한다
2. 자유 텍스트 대비 핵심 정보 누락이 줄어든다
3. 후처리로 마크다운 변환이 가능하다

방법:
1. Ollama OpenAI 호환 API로 JSON mode 호출
2. 재무분석용 Pydantic 스키마 정의
3. 동일 프롬프트로 자유 텍스트 vs JSON 출력 비교

결과 (실험 후 작성):

결론:

실험일: 2026-03-09
"""

from pydantic import BaseModel, Field


class MetricItem(BaseModel):
	name: str = Field(description="지표명 (예: 부채비율, ROE)")
	value: str = Field(description="값 (예: 45.2%)")
	year: str = Field(description="연도 (예: 2024)")
	trend: str = Field(description="추세 (개선/악화/유지)")
	assessment: str = Field(description="판단 (양호/주의/위험)")


class RiskItem(BaseModel):
	description: str = Field(description="리스크 설명")
	severity: str = Field(description="심각도 (낮음/보통/높음)")


class AnalysisResponse(BaseModel):
	summary: str = Field(description="핵심 요약 1~2문장")
	metrics: list[MetricItem] = Field(description="분석 지표 리스트 (3~8개)")
	positives: list[str] = Field(description="긍정 신호 (1~3개)")
	risks: list[RiskItem] = Field(description="리스크/주의점 (0~3개)")
	grade: str = Field(description="종합 등급 (A/B/C/D/F 또는 양호/보통/주의/위험)")
	conclusion: str = Field(description="결론 (2~3문장, 근거 요약 포함)")


def test_json_schema():
	"""JSON schema를 Ollama에 전달하여 구조화 출력 테스트."""
	try:
		from openai import OpenAI
	except ImportError:
		print("openai 패키지 필요: pip install openai")
		return

	client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

	schema = AnalysisResponse.model_json_schema()
	print("=== 스키마 ===")
	import json
	print(json.dumps(schema, indent=2, ensure_ascii=False))

	test_context = """
# 삼성전자 (005930)
**데이터 기준: 2020~2024년** (가장 최근: 2024년)

## 손익계산서
| 계정 | 2024 | 2023 | 2022 | 2021 |
| --- | --- | --- | --- | --- |
| 매출액 | 300.9조 | 258.9조 | 302.2조 | 279.6조 |
| 영업이익 | 32.7조 | 6.6조 | 43.4조 | 51.6조 |
| 당기순이익 | 26.2조 | 15.5조 | 55.7조 | 39.9조 |

## 재무상태표
| 계정 | 2024 | 2023 |
| --- | --- | --- |
| 자산총계 | 481.6조 | 455.9조 |
| 부채총계 | 103.2조 | 92.2조 |
| 자본총계 | 378.4조 | 363.7조 |
| 유동자산 | 225.1조 | 208.7조 |
| 유동부채 | 69.3조 | 63.8조 |

## 핵심 재무비율
| 지표 | 값 | 판단 |
| --- | --- | --- |
| ROE | 6.5% | 주의 |
| 영업이익률 | 10.9% | - |
| 부채비율 | 27.3% | 양호 |
| 유동비율 | 324.8% | 양호 |
"""

	test_question = "삼성전자의 재무 건전성을 분석해줘"

	system_prompt = (
		"한국 상장기업 재무분석 전문 애널리스트입니다. "
		"DART 전자공시 데이터를 기반으로 분석합니다. "
		"반드시 지정된 JSON 스키마에 맞춰 응답하세요."
	)

	messages = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": f"{test_context}\n\n질문: {test_question}"},
	]

	print("\n=== 테스트 1: JSON Schema 모드 ===")
	try:
		response = client.chat.completions.create(
			model="qwen3",
			messages=messages,
			temperature=0,
			response_format={
				"type": "json_schema",
				"json_schema": {
					"name": "analysis_response",
					"schema": schema,
				}
			},
		)
		raw = response.choices[0].message.content
		print(f"원본 길이: {len(raw)} chars")
		print(raw[:2000])

		parsed = AnalysisResponse.model_validate_json(raw)
		print(f"\n=== 파싱 성공 ===")
		print(f"요약: {parsed.summary}")
		print(f"지표 수: {len(parsed.metrics)}")
		for m in parsed.metrics:
			print(f"  - {m.name}: {m.value} ({m.year}) [{m.assessment}] {m.trend}")
		print(f"긍정: {parsed.positives}")
		print(f"리스크: {len(parsed.risks)}개")
		print(f"등급: {parsed.grade}")
		print(f"결론: {parsed.conclusion}")

	except Exception as e:
		print(f"에러: {e}")
		import traceback
		traceback.print_exc()

	print("\n=== 테스트 2: 자유 텍스트 모드 (비교용) ===")
	try:
		response2 = client.chat.completions.create(
			model="qwen3",
			messages=messages,
			temperature=0,
		)
		text = response2.choices[0].message.content
		print(f"원본 길이: {len(text)} chars")
		print(text[:2000])
	except Exception as e:
		print(f"에러: {e}")


def test_simple_json_mode():
	"""단순 JSON 모드 (스키마 없이) 테스트."""
	try:
		from openai import OpenAI
	except ImportError:
		print("openai 패키지 필요: pip install openai")
		return

	client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

	messages = [
		{"role": "system", "content": "재무분석가입니다. JSON으로 답하세요."},
		{"role": "user", "content": "삼성전자의 부채비율이 27.3%입니다. 이게 양호한지 JSON으로 판단해주세요. 필드: assessment, reason, grade"},
	]

	print("=== 단순 JSON 모드 ===")
	try:
		response = client.chat.completions.create(
			model="qwen3",
			messages=messages,
			temperature=0,
			response_format={"type": "json_object"},
		)
		print(response.choices[0].message.content)
	except Exception as e:
		print(f"에러: {e}")


if __name__ == "__main__":
	test_simple_json_mode()
	print("\n" + "=" * 60 + "\n")
	test_json_schema()
