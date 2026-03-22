"""075_viewerEnhance 흡수 테스트.

Unit: 합성 데이터로 로직 검증.
Integration: 실제 데이터로 end-to-end 검증 (데이터 없으면 skip).
"""

from __future__ import annotations

import unittest

import polars as pl
import pytest

pytestmark = pytest.mark.integration

# ──────────────────────────── diff matrix ────────────────────────────


class TestDiffMatrix(unittest.TestCase):
    """002 diff matrix — build_diff_matrix / build_heatmap_spec."""

    def _make_sections(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "topic": ["topicA", "topicA", "topicB", "topicB"],
                "chapter": ["I", "I", "II", "II"],
                "blockType": ["text", "table", "text", "text"],
                "blockOrder": [0, 1, 0, 1],
                "2024": ["hello", "t1", "world", "foo"],
                "2023": ["hello", "t1", "changed", "foo"],
                "2022": ["old", "t1", "changed", "bar"],
            }
        )

    def test_basic(self):
        from dartlab.engines.common.docs.diff import build_diff_matrix

        sections = self._make_sections()
        result = build_diff_matrix(sections)

        self.assertIn("matrix", result)
        self.assertIn("periods", result)
        self.assertGreater(result["topic_count"], 0)
        self.assertGreater(result["period_count"], 0)
        # matrix rows have topic/chapter/changeRate + period columns
        row = result["matrix"][0]
        self.assertIn("topic", row)
        self.assertIn("changeRate", row)

    def test_text_only(self):
        from dartlab.engines.common.docs.diff import build_diff_matrix

        sections = self._make_sections()
        full = build_diff_matrix(sections)
        text = build_diff_matrix(sections, textOnly=True)

        # text-only should have fewer or equal topics
        self.assertLessEqual(text["topic_count"], full["topic_count"])

    def test_heatmap_spec_shape(self):
        from dartlab.engines.common.docs.diff import build_diff_matrix, build_heatmap_spec

        sections = self._make_sections()
        matrix_data = build_diff_matrix(sections)
        spec = build_heatmap_spec(matrix_data, "테스트회사", top_n=5)

        self.assertEqual(spec["chartType"], "heatmap")
        self.assertIn("xLabels", spec)
        self.assertIn("yLabels", spec)
        self.assertIn("data", spec)
        # data rows == yLabels count
        self.assertEqual(len(spec["data"]), len(spec["yLabels"]))
        # data cols == xLabels count
        if spec["data"]:
            self.assertEqual(len(spec["data"][0]), len(spec["xLabels"]))


# ──────────────────────────── bridge ────────────────────────────


class TestBridge(unittest.TestCase):
    """003 bridge — extract_amounts / match_amounts."""

    def test_extract_amounts_patterns(self):
        from dartlab.engines.common.docs.bridge import extract_amounts_from_text

        # 조+억
        r = extract_amounts_from_text("매출액 86조 1,229억원")
        self.assertEqual(len(r), 1)
        self.assertAlmostEqual(r[0]["value_억"], 86 * 10000 + 1229, places=0)

        # 단독 억
        r = extract_amounts_from_text("영업이익 5,230억원")
        self.assertEqual(len(r), 1)
        self.assertAlmostEqual(r[0]["value_억"], 5230, places=0)

        # 백만원
        r = extract_amounts_from_text("2,587,849백만원")
        # 억 패턴도 매칭될 수 있으므로 1개 이상
        self.assertGreaterEqual(len(r), 1)
        # 백만원 단위가 포함되어야 함
        units = [a["unit"] for a in r]
        self.assertIn("백만원", units)

        # 천원
        r = extract_amounts_from_text("100,000천원")
        self.assertGreaterEqual(len(r), 1)
        units = [a["unit"] for a in r]
        self.assertIn("천원", units)

        # 빈 텍스트
        self.assertEqual(extract_amounts_from_text(""), [])
        self.assertEqual(extract_amounts_from_text(None), [])

    def test_match_amounts_tolerance(self):
        from dartlab.engines.common.docs.bridge import match_amounts

        text_amounts = [
            {"value_억": 1000, "raw": "1,000억", "unit": "억"},
            {"value_억": 500, "raw": "500억", "unit": "억"},
        ]
        finance_amounts = {
            "매출액": 1020.0,  # 2% 오차
            "영업이익": 480.0,  # 4.2% 오차
            "당기순이익": 200.0,
        }

        # 5% tolerance
        matches = match_amounts(text_amounts, finance_amounts, tolerance=0.05)
        self.assertEqual(len(matches), 2)

        # 1% tolerance — 500억 매칭 안됨
        matches_strict = match_amounts(text_amounts, finance_amounts, tolerance=0.01)
        self.assertEqual(len(matches_strict), 0)

    def test_zero_values_skipped(self):
        from dartlab.engines.common.docs.bridge import match_amounts

        text_amounts = [{"value_억": 0, "raw": "0", "unit": "억"}]
        finance_amounts = {"매출액": 1000.0}
        matches = match_amounts(text_amounts, finance_amounts)
        self.assertEqual(len(matches), 0)


# ──────────────────────────── topic graph ────────────────────────────


class TestTopicGraph(unittest.TestCase):
    """006 topic graph — mention matrix / analyze_graph."""

    def _make_sections(self) -> pl.DataFrame:
        return pl.DataFrame(
            {
                "topic": ["businessOverview", "dividend", "employee"],
                "chapter": ["I", "III", "V"],
                "blockType": ["text", "text", "text"],
                "blockOrder": [0, 0, 0],
                "2024": [
                    "사업의 개요에 따르면 매출액이 증가했다. 배당금 지급 결정. 직원 증가. 연구개발 투자 확대. 주요 사업 분야의 성장이 두드러졌다.",
                    "배당 배당금 주당배당 매출 관련 내용이 포함되어 있다. 배당수익률 및 배당성향 분석. 주주환원 정책 설명.",
                    "직원 임직원 인력 배당금 관련 보고서 내용. 종업원 현황과 평균 급여 분석. 인력 운용 관련 세부사항.",
                ],
            }
        )

    def test_mention_matrix_structure(self):
        from dartlab.engines.common.docs.topicGraph import build_mention_matrix

        sections = self._make_sections()
        result = build_mention_matrix(sections)

        self.assertIn("adjacency", result)
        self.assertIn("topics_with_text", result)
        self.assertEqual(result["period"], "2024")
        # at least some edges
        self.assertGreater(len(result["adjacency"]), 0)

    def test_analyze_graph_threshold(self):
        from dartlab.engines.common.docs.topicGraph import analyze_graph

        adjacency = {
            ("a", "b"): 5,
            ("a", "c"): 2,
            ("b", "c"): 10,
        }

        # threshold 3 — a→c 제외
        result = analyze_graph(adjacency, threshold=3)
        self.assertEqual(result["edges"], 2)
        self.assertGreater(result["avg_degree"], 0)

        # threshold 1 — 전부 포함
        result_all = analyze_graph(adjacency, threshold=1)
        self.assertEqual(result_all["edges"], 3)

    def test_empty_adjacency(self):
        from dartlab.engines.common.docs.topicGraph import analyze_graph

        result = analyze_graph({}, threshold=1)
        self.assertEqual(result["edges"], 0)
        self.assertEqual(result["nodes"], 0)


# ──────────────────────────── scan payload ────────────────────────────


class TestScanPayload(unittest.TestCase):
    """001 scan payload — converter 함수."""

    def test_governance_converter(self):
        from dartlab.engines.company.dart.scan.payload import governance_to_insight

        row = {"등급": "B", "총점": 65, "지분율": 55.0, "사외이사비율": 42.0, "pay_ratio": 3.0, "감사의견": "적정의견"}
        result = governance_to_insight(row)

        self.assertIsNotNone(result)
        self.assertEqual(result["grade"], "B")
        self.assertIn("65점", result["summary"])
        # 지분율 > 50 → risk
        self.assertTrue(any("과점" in r["text"] for r in result["risks"]))
        # 사외이사 >= 40 → opportunity
        self.assertTrue(any("사외이사" in o["text"] for o in result["opportunities"]))

    def test_governance_audit_partial_match(self):
        from dartlab.engines.company.dart.scan.payload import governance_to_insight

        # "적정" 부분 매칭 — "적정의견" 포함이면 비적정 아님
        row = {"등급": "A", "총점": 80, "감사의견": "적정의견(한정제외)"}
        result = governance_to_insight(row)
        # "적정" in "적정의견(한정제외)" → True → 비적정 risk 없음
        self.assertFalse(any("비적정" in r["text"] for r in result["risks"]))

    def test_workforce_grades(self):
        from dartlab.engines.company.dart.scan.payload import workforce_to_insight

        # A등급: rev_per >= 5
        result = workforce_to_insight({"직원수": 1000, "직원당매출_억": 6.0})
        self.assertEqual(result["grade"], "A")

        # F등급: rev_per < 0.5
        result = workforce_to_insight({"직원수": 1000, "직원당매출_억": 0.3})
        self.assertEqual(result["grade"], "F")

    def test_capital_grades(self):
        from dartlab.engines.company.dart.scan.payload import capital_to_insight

        result = capital_to_insight({"분류": "환원형", "배당여부": True, "DPS": 1000, "배당수익률": 3.5})
        self.assertEqual(result["grade"], "A")
        self.assertTrue(any("배당수익률" in o["text"] for o in result["opportunities"]))

    def test_debt_grades(self):
        from dartlab.engines.company.dart.scan.payload import debt_to_insight

        result = debt_to_insight({"위험등급": "안전", "부채비율": 50.0, "ICR": 8.0})
        self.assertEqual(result["grade"], "A")
        self.assertTrue(any("ICR 양호" in o["text"] for o in result["opportunities"]))

    def test_none_on_missing_key(self):
        from dartlab.engines.company.dart.scan.payload import (
            capital_to_insight,
            debt_to_insight,
            governance_to_insight,
            workforce_to_insight,
        )

        self.assertIsNone(governance_to_insight({}))
        self.assertIsNone(workforce_to_insight({}))
        self.assertIsNone(capital_to_insight({}))
        self.assertIsNone(debt_to_insight({}))

    def test_unified_payload_keys(self):
        """build_unified_payload가 올바른 키 구조를 반환하는지 (mock)."""
        from dartlab.engines.company.dart.scan.payload import build_scan_payload

        # Mock company
        class MockCompany:
            def governance(self):
                return pl.DataFrame([{"등급": "B", "총점": 60}])

            def workforce(self):
                return pl.DataFrame([{"직원수": 500, "직원당매출_억": 3.0}])

            def capital(self):
                return pl.DataFrame([{"분류": "중립"}])

            def debt(self):
                return pl.DataFrame([{"위험등급": "관찰", "부채비율": 100.0}])

        result = build_scan_payload(MockCompany())
        self.assertEqual(set(result.keys()), {"governance", "workforce", "capital", "debt"})
        # 모두 non-None
        for v in result.values():
            self.assertIsNotNone(v)


# ──────────────────────────── scan snapshot ────────────────────────────


class TestScanSnapshot(unittest.TestCase):
    """004 scan snapshot — percentile 조회."""

    def test_percentile_basic(self):
        from dartlab.engines.company.dart.scan.snapshot import _percentile

        arr = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        self.assertAlmostEqual(_percentile(arr, 50), 50.0, places=0)
        self.assertAlmostEqual(_percentile(arr, 100), 100.0, places=0)
        self.assertAlmostEqual(_percentile(arr, 10), 10.0, places=0)

    def test_percentile_empty(self):
        from dartlab.engines.company.dart.scan.snapshot import _percentile

        self.assertEqual(_percentile([], 50), 0.0)


# ──────────────────────────── integration (real data) ────────────────────────


def _has_data() -> bool:
    try:
        import dartlab

        dartlab.Company("005930")
        return True
    except (FileNotFoundError, ImportError, RuntimeError):
        return False


@unittest.skipUnless(_has_data(), "실제 데이터 없음")
class TestIntegrationReal(unittest.TestCase):
    """실제 데이터 기반 통합 테스트."""

    @classmethod
    def setUpClass(cls):
        import dartlab

        cls.c = dartlab.Company("005930")

    def test_diff_matrix_real(self):
        from dartlab.engines.common.docs.diff import build_diff_matrix

        sections = self.c.docs.sections.raw
        result = build_diff_matrix(sections, textOnly=True)
        self.assertGreater(result["topic_count"], 0)
        self.assertGreater(result["period_count"], 0)

    def test_bridge_real(self):
        import re

        from dartlab.engines.common.docs.bridge import (
            extract_amounts_from_text,
            get_finance_amounts,
            match_amounts,
        )

        sections = self.c.docs.sections.raw
        periods = sorted(
            [c for c in sections.columns if re.fullmatch(r"\d{4}(Q[1-4])?", c)],
            reverse=True,
        )
        if not periods:
            self.skipTest("기간 없음")

        topic_rows = sections.filter((pl.col("topic") == "businessOverview") & (pl.col("blockType") == "text"))
        if topic_rows.height == 0:
            self.skipTest("businessOverview 텍스트 없음")

        texts = topic_rows[periods[0]].drop_nulls().to_list()
        full_text = "\n".join(str(t) for t in texts if t)

        amounts = extract_amounts_from_text(full_text)
        self.assertGreater(len(amounts), 0)

        fin = get_finance_amounts(self.c, periods[0])
        matched = match_amounts(amounts, fin)
        # 삼성전자는 매칭 있어야 함
        self.assertGreater(len(matched), 0)

    def test_topic_graph_real(self):
        from dartlab.engines.common.docs.topicGraph import (
            analyze_graph,
            build_mention_matrix,
            get_related_topics,
        )

        sections = self.c.docs.sections.raw
        matrix = build_mention_matrix(sections)
        self.assertGreater(len(matrix["adjacency"]), 0)

        analysis = analyze_graph(matrix["adjacency"])
        self.assertGreater(analysis["nodes"], 0)
        self.assertGreater(analysis["avg_degree"], 2)

        related = get_related_topics(sections, "businessOverview")
        self.assertGreater(len(related), 0)

    def test_scan_payload_real(self):
        from dartlab.engines.company.dart.scan.payload import build_unified_payload

        unified = build_unified_payload(self.c)
        # 삼성전자는 최소 5개 이상 영역 유효
        valid = sum(1 for v in unified.values() if v is not None)
        self.assertGreaterEqual(valid, 5)

    def test_scan_position_real(self):
        from dartlab.engines.company.dart.scan.snapshot import getScanPosition

        pos = getScanPosition("005930")
        if pos is None:
            self.skipTest("scan 스냅샷 없음")

        # 삼성전자는 4축 모두 유효
        self.assertIsNotNone(pos["governance"])
        self.assertIsNotNone(pos["workforce"])
        self.assertIsNotNone(pos["capital"])
        self.assertIsNotNone(pos["debt"])

        # governance percentile 범위
        gov_pct = pos["governance"]["percentile"]
        self.assertGreaterEqual(gov_pct, 0)
        self.assertLessEqual(gov_pct, 100)

        # capital은 분류
        self.assertIn(pos["capital"]["class"], ("환원형", "중립", "희석형"))


if __name__ == "__main__":
    unittest.main()
