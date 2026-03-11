"""tools.text 모듈 테스트 — 데이터 의존 없음."""

from dartlab.tools.text import (
	extract_keywords,
	extract_numbers,
	section_diff,
	sentiment_indicators,
)

# ══════════════════════════════════════
# 키워드 추출
# ══════════════════════════════════════

class TestExtractKeywords:
	def test_basic(self):
		text = "매출이 증가했고 매출 성장이 지속되었다. 영업이익도 증가했다."
		result = extract_keywords(text)
		assert len(result) > 0
		keywords = [kw for kw, _ in result]
		assert "증가" in keywords or "매출" in keywords

	def test_empty_text(self):
		assert extract_keywords("") == []

	def test_stopwords(self):
		text = "당사는 사업을 합니다"
		result = extract_keywords(text)
		keywords = [kw for kw, _ in result]
		assert "당사" not in keywords
		assert "합니다" not in keywords

	def test_min_length(self):
		text = "큰 매출 증가 a big growth"
		result = extract_keywords(text, min_length=3)
		keywords = [kw for kw, _ in result]
		# 1~2글자 단어는 제외
		for kw in keywords:
			assert len(kw) >= 3

	def test_top_n(self):
		text = "매출 증가 영업이익 성장 자본 확대 투자 확대 사업 확장"
		result = extract_keywords(text, top_n=3)
		assert len(result) <= 3


# ══════════════════════════════════════
# 감성 분석
# ══════════════════════════════════════

class TestSentimentIndicators:
	def test_positive(self):
		text = "매출이 증가하고 성장이 지속되며 실적이 개선되었다."
		result = sentiment_indicators(text)
		assert result["positive_count"] > 0
		assert result["score"] > 0

	def test_negative(self):
		text = "매출이 감소하고 실적이 하락하며 적자가 지속되었다."
		result = sentiment_indicators(text)
		assert result["negative_count"] > 0
		assert result["score"] < 0

	def test_mixed(self):
		text = "매출은 증가했으나 영업이익은 감소했다."
		result = sentiment_indicators(text)
		assert result["positive_count"] > 0
		assert result["negative_count"] > 0
		assert -1.0 <= result["score"] <= 1.0

	def test_empty(self):
		result = sentiment_indicators("")
		assert result["positive_count"] == 0
		assert result["negative_count"] == 0
		assert result["risk_count"] == 0
		assert result["score"] == 0.0

	def test_risk_keywords(self):
		text = "소송이 제기되었으며 우발부채가 존재한다. 제재 가능성이 있다."
		result = sentiment_indicators(text)
		assert result["risk_count"] > 0
		risk_kw = result["risk_keywords"]
		assert len(risk_kw) > 0


# ══════════════════════════════════════
# 숫자 추출
# ══════════════════════════════════════

class TestExtractNumbers:
	def test_basic(self):
		text = "매출 1,234억원을 달성했다."
		result = extract_numbers(text)
		assert len(result) > 0
		found = [r for r in result if r["value"] == 1234]
		assert len(found) > 0
		assert found[0]["unit"] == "억원"

	def test_percentage(self):
		text = "영업이익률 12.3%를 기록했다."
		result = extract_numbers(text)
		found = [r for r in result if r["value"] == 12.3]
		assert len(found) > 0
		assert found[0]["unit"] == "%"

	def test_no_unit(self):
		text = "직원 수는 1234 명이다."
		result = extract_numbers(text)
		assert len(result) > 0

	def test_empty(self):
		assert extract_numbers("") == []

	def test_context(self):
		text = "전년 대비 매출이 1,500억원으로 증가했다."
		result = extract_numbers(text)
		assert len(result) > 0
		assert "context" in result[0]
		assert len(result[0]["context"]) > 0


# ══════════════════════════════════════
# 섹션 비교
# ══════════════════════════════════════

class _FakeSection:
	def __init__(self, key, text):
		self.key = key
		self.text = text


class TestSectionDiff:
	def test_added_removed(self):
		a = [_FakeSection("sec1", "내용1")]
		b = [_FakeSection("sec2", "내용2")]
		result = section_diff(a, b)
		assert "sec1" in result["removed"]
		assert "sec2" in result["added"]

	def test_changed(self):
		a = [_FakeSection("sec1", "원래 내용입니다.")]
		b = [_FakeSection("sec1", "완전히 다른 새로운 내용입니다.")]
		result = section_diff(a, b)
		assert len(result["changed"]) == 1
		assert result["changed"][0]["key"] == "sec1"

	def test_unchanged(self):
		a = [_FakeSection("sec1", "동일한 내용")]
		b = [_FakeSection("sec1", "동일한 내용")]
		result = section_diff(a, b)
		assert "sec1" in result["unchanged"]
