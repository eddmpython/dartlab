"""Core 함수 벤치마크 — pytest-benchmark 기반.

CI에서 자동 추적되며, 30% 이상 성능 저하 시 PR에 경고.
데이터 없이 실행 가능한 순수 계산 벤치마크만 포함.
"""

import pytest

from dartlab.core.finance.extract import getLatest, getTTM, getRevenueGrowth3Y
from dartlab.core.finance.ratios import _safeDiv, _safePct


# ── 테스트 데이터 ──

_SERIES_20Q = {
    "IS": {
        "sales": [float(i * 1_000_000) for i in range(1, 21)],
        "operatingIncome": [float(i * 100_000) for i in range(1, 21)],
        "netIncome": [float(i * 80_000) for i in range(1, 21)],
    },
    "BS": {
        "totalAssets": [float(i * 10_000_000) for i in range(1, 21)],
        "totalEquity": [float(i * 5_000_000) for i in range(1, 21)],
    },
    "CF": {
        "operatingCashflow": [float(i * 90_000) for i in range(1, 21)],
    },
}

_SERIES_SPARSE = {
    "IS": {
        "sales": [
            None,
            1e9,
            None,
            2e9,
            None,
            3e9,
            None,
            4e9,
            None,
            5e9,
            None,
            6e9,
            None,
            7e9,
            None,
            8e9,
            None,
            9e9,
            None,
            10e9,
        ],
    },
    "BS": {
        "totalAssets": [None] * 10 + [float(i * 1e9) for i in range(1, 11)],
    },
}


# ── getTTM 벤치마크 ──


def test_getTTM_20q(benchmark):
    """getTTM: 20분기 연속 데이터."""
    benchmark(getTTM, _SERIES_20Q, "IS", "sales")


def test_getTTM_sparse(benchmark):
    """getTTM: sparse 데이터 (50% None)."""
    benchmark(getTTM, _SERIES_SPARSE, "IS", "sales")


def test_getTTM_annualize(benchmark):
    """getTTM: annualize 모드."""
    benchmark(getTTM, _SERIES_SPARSE, "IS", "sales", annualize=True)


# ── getLatest 벤치마크 ──


def test_getLatest_20q(benchmark):
    """getLatest: 20분기 연속 데이터."""
    benchmark(getLatest, _SERIES_20Q, "BS", "totalAssets")


def test_getLatest_sparse(benchmark):
    """getLatest: sparse 데이터."""
    benchmark(getLatest, _SERIES_SPARSE, "BS", "totalAssets")


# ── getRevenueGrowth3Y 벤치마크 ──


def test_revenueGrowth3Y(benchmark):
    """getRevenueGrowth3Y: 20분기 데이터."""
    benchmark(getRevenueGrowth3Y, _SERIES_20Q)


# ── safeDiv 벤치마크 ──


def test_safeDiv_normal(benchmark):
    """_safeDiv: 정상 입력."""
    benchmark(_safeDiv, 1_000_000.0, 500_000.0)


def test_safeDiv_zeroDenom(benchmark):
    """_safeDiv: 0 분모."""
    benchmark(_safeDiv, 1_000_000.0, 0.0)


def test_safePct_normal(benchmark):
    """_safePct: 정상 입력."""
    benchmark(_safePct, 300_000.0, 1_000_000.0)
