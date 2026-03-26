"""벤치마크 데이터 구조 + 렌더링 + 커버리지 테스트."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


def test_all_benchmarks_have_meta():
    """모든 벤치마크에 _meta (updated, source) 존재 확인."""
    from dartlab.ai.conversation.templates.benchmarkData import BENCHMARK_DATA

    for key, data in BENCHMARK_DATA.items():
        meta = data.get("_meta")
        assert meta is not None, f"'{key}' 벤치마크에 _meta 없음"
        assert "updated" in meta, f"'{key}' 벤치마크에 _meta.updated 없음"
        assert "source" in meta, f"'{key}' 벤치마크에 _meta.source 없음"


def test_all_benchmarks_have_metrics():
    """모든 벤치마크에 지표가 1개 이상 존재 확인."""
    from dartlab.ai.conversation.templates.benchmarkData import BENCHMARK_DATA

    for key, data in BENCHMARK_DATA.items():
        metrics = data.get("지표", {})
        assert len(metrics) >= 1, f"'{key}' 벤치마크에 지표 없음"
        for name, spec in metrics.items():
            assert "good" in spec, f"'{key}'.{name}에 good 없음"
            assert "normal_low" in spec, f"'{key}'.{name}에 normal_low 없음"
            assert "normal_high" in spec, f"'{key}'.{name}에 normal_high 없음"
            assert "unit" in spec, f"'{key}'.{name}에 unit 없음"


def test_benchmark_render_all():
    """모든 벤치마크가 렌더링 가능 확인."""
    from dartlab.ai.conversation.templates.benchmarkData import BENCHMARK_DATA
    from dartlab.ai.conversation.templates.benchmarks import render_benchmark

    for key in BENCHMARK_DATA:
        result = render_benchmark(key)
        assert isinstance(result, str), f"'{key}' 렌더링 실패"
        assert len(result) > 50, f"'{key}' 렌더링 결과 너무 짧음: {len(result)}"
        assert "벤치마크" in result, f"'{key}' 렌더링에 '벤치마크' 미포함"


def test_render_nonexistent_returns_empty():
    """존재하지 않는 키는 빈 문자열 반환."""
    from dartlab.ai.conversation.templates.benchmarks import render_benchmark

    assert render_benchmark("존재하지않는업종") == ""


def test_sector_map_covers_all_benchmarks():
    """SECTOR_MAP의 모든 값이 BENCHMARK_DATA에 존재."""
    from dartlab.ai.conversation.templates.benchmarkData import BENCHMARK_DATA
    from dartlab.ai.conversation.templates.benchmarks import _SECTOR_MAP

    benchmark_keys = set(BENCHMARK_DATA.keys())
    for sector, mapped_key in _SECTOR_MAP.items():
        assert mapped_key in benchmark_keys, f"_SECTOR_MAP['{sector}'] = '{mapped_key}'가 BENCHMARK_DATA에 없음"


def test_industry_benchmarks_cache_matches_render():
    """_INDUSTRY_BENCHMARKS 캐시가 render_benchmark와 동일한 결과."""
    from dartlab.ai.conversation.templates.benchmarks import (
        _INDUSTRY_BENCHMARKS,
        render_benchmark,
    )

    for key, cached in _INDUSTRY_BENCHMARKS.items():
        rendered = render_benchmark(key)
        assert cached == rendered, f"'{key}' 캐시와 렌더링 불일치"


def test_benchmark_data_count():
    """벤치마크 데이터 16개 (15 업종 + 일반) 확인."""
    from dartlab.ai.conversation.templates.benchmarkData import BENCHMARK_DATA

    assert len(BENCHMARK_DATA) == 16, f"벤치마크 {len(BENCHMARK_DATA)}개 (기대: 16)"
