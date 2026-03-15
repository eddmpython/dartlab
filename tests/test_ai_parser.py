"""aiParser 모듈 테스트 — LLM 불필요한 통계 기능만."""

import polars as pl

from dartlab.engines.ai.aiParser import (
    Anomaly,
    _statistical_prescreen,
    classify_text,
    detect_anomalies,
    interpret_accounts,
)

# ══════════════════════════════════════
# 통계 사전 스크리닝
# ══════════════════════════════════════


class TestStatisticalPrescreen:
    def test_spike_detection(self):
        """YoY 50%+ 변동 감지."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "revenue": [1000, 1100, 1200, 2500],
            }
        )
        anomalies = _statistical_prescreen(df, threshold_pct=50.0)
        spikes = [a for a in anomalies if a.anomaly_type == "spike"]
        assert len(spikes) >= 1
        assert any(a.year == "2023" and a.column == "revenue" for a in spikes)

    def test_sign_reversal(self):
        """양→음 전환 감지."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "profit": [100, 50, -30],
            }
        )
        anomalies = _statistical_prescreen(df)
        reversals = [a for a in anomalies if a.anomaly_type == "sign_reversal"]
        assert len(reversals) >= 1
        assert any(a.severity == "high" for a in reversals)

    def test_no_anomalies(self):
        """정상적 데이터는 이상치 없음."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "revenue": [100, 105, 110, 115],
            }
        )
        anomalies = _statistical_prescreen(df, threshold_pct=50.0)
        # 5% 변동이므로 50% 임계치를 넘지 않음
        spikes = [a for a in anomalies if a.anomaly_type == "spike"]
        assert len(spikes) == 0

    def test_severity_high(self):
        """|변동| > 100%면 severity=high."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021],
                "v": [100, 250],
            }
        )
        anomalies = _statistical_prescreen(df, threshold_pct=50.0)
        spikes = [a for a in anomalies if a.anomaly_type == "spike"]
        assert len(spikes) >= 1
        assert spikes[0].severity == "high"
        assert spikes[0].change_pct == 150.0

    def test_severity_medium(self):
        """50~100% 변동은 severity=medium."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021],
                "v": [100, 170],
            }
        )
        anomalies = _statistical_prescreen(df, threshold_pct=50.0)
        spikes = [a for a in anomalies if a.anomaly_type == "spike"]
        assert len(spikes) >= 1
        assert spikes[0].severity == "medium"

    def test_no_year_col(self):
        """year 컬럼 없으면 빈 리스트."""
        df = pl.DataFrame({"x": [1, 2, 3], "v": [100, 200, 300]})
        result = _statistical_prescreen(df)
        assert result == []

    def test_deduplication(self):
        """같은 (column, year, type) 중복 제거."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "v": [100, 110, 120, 500],  # 2023에서 spike
            }
        )
        anomalies = _statistical_prescreen(df, threshold_pct=50.0)
        # 같은 column+year+type 조합이 중복되지 않아야
        keys = [(a.column, a.year, a.anomaly_type) for a in anomalies]
        assert len(keys) == len(set(keys))


# ══════════════════════════════════════
# detect_anomalies (통합)
# ══════════════════════════════════════


class TestDetectAnomalies:
    def test_without_llm(self):
        """use_llm=False면 통계만으로 동작."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022, 2023],
                "assets": [1000, 1100, 1200, 2500],
            }
        )
        anomalies = detect_anomalies(df, use_llm=False, threshold_pct=50.0)
        assert len(anomalies) >= 1

    def test_anomaly_dataclass(self):
        """Anomaly 필드 검증."""
        a = Anomaly(
            column="revenue",
            year="2023",
            value=2500,
            prev_value=1200,
            change_pct=108.3,
            anomaly_type="spike",
            severity="high",
            description="급격한 매출 증가",
        )
        assert a.column == "revenue"
        assert a.anomaly_type == "spike"
        assert a.severity == "high"

    def test_severity_ordering(self):
        """결과가 severity 내림차순 정렬."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "a": [100, -50, 200],  # sign_reversal(high) + spike
            }
        )
        anomalies = detect_anomalies(df, use_llm=False, threshold_pct=50.0)
        if len(anomalies) >= 2:
            severities = [a.severity for a in anomalies]
            order = {"high": 0, "medium": 1, "low": 2}
            for i in range(len(severities) - 1):
                assert order[severities[i]] <= order[severities[i + 1]]

    def test_empty_result(self):
        """이상치 없으면 빈 리스트."""
        df = pl.DataFrame(
            {
                "year": [2020, 2021, 2022],
                "v": [100, 102, 104],
            }
        )
        result = detect_anomalies(df, use_llm=False, threshold_pct=50.0)
        assert result == []


# ══════════════════════════════════════
# interpret_accounts (LLM 없이 테스트 가능한 부분)
# ══════════════════════════════════════


class TestInterpretAccountsNoLLM:
    def test_no_account_col(self):
        """계정명 컬럼 없으면 df 그대로."""
        df = pl.DataFrame({"year": [2023], "v": [100]})
        result = interpret_accounts(df)
        assert result.columns == df.columns
        assert "설명" not in result.columns


# ══════════════════════════════════════
# classify_text (LLM 없이 테스트 가능한 부분)
# ══════════════════════════════════════


class TestClassifyTextEmpty:
    def test_empty_text(self):
        """빈 문자열은 기본값 반환."""
        result = classify_text("")
        assert result["sentiment"] == "중립"
        assert result["key_topics"] == []
        assert result["risks"] == []
        assert result["opportunities"] == []
        assert result["summary"] == ""

    def test_none_text(self):
        """None도 falsy이므로 기본값."""
        result = classify_text(None)
        assert result["sentiment"] == "중립"
