"""credit engine 설정 상수 SSOT — 모든 매직 넘버 한 곳.

credit/engine.py 가 1319 줄 god module 이라 config 분리.
identity 보존을 위해 engine.py 가 본 모듈에서 re-export 한다.

_CONFIG 그룹:
- Notch Adjustment (gate · cap · 매출/시총 임계)
- 공기업/지주 키워드
- CHS 안정/부실 임계
- 시계열 안정화 가중치
- 축1 압축 · OFS 블렌딩

_WEIGHTS — 기업 유형별 7축 가중치 (default/captive/holding)
_CHS_PD_BRACKETS — CHS PD → 점수 매핑 테이블
"""

from __future__ import annotations

_CONFIG = {
    # Notch Adjustment
    "notch_gate_score": 10,
    "notch_a_range_score": 19,
    "notch_a_range_cap": 4,
    "notch_cap_large": 7,
    "notch_cap_medium": 4,
    "notch_cap_small": 2,
    "revenue_large": 10e12,
    "revenue_mega": 50e12,
    "mktcap_top30": 30e12,
    "mktcap_top100": 10e12,
    "public_corps": {"한국전력", "한국가스공사", "한국수력원자력", "한국도로공사", "한국토지주택공사"},
    "holding_keywords": ("지주", "홀딩스", "Holdings"),
    "holding_investment_ratio": 0.5,
    # CHS
    "chs_safe_max_down": 1.0,
    "chs_weak_max_up": -3.0,
    # 시계열 안정화
    "ts_weights": (0.60, 0.25, 0.15),
    # 축1 압축
    "axis1_compress_threshold": 20,
    "axis1_compress_ratio": 0.6,
    # OFS 블렌딩
    "ofs_advantage_threshold": 10,
    "ofs_strong_weight": 0.65,
    "ofs_default_weight": 0.50,
}

_WEIGHTS = {
    "default": [0.25, 0.20, 0.15, 0.15, 0.10, 0.10, 0.05],
    "captive": [0.30, 0.15, 0.15, 0.15, 0.10, 0.10, 0.05],
    "holding": [0.15, 0.25, 0.15, 0.15, 0.15, 0.10, 0.05],
}

_CHS_PD_BRACKETS = [
    (0.001, 3),  # AAA 급
    (0.01, 10),  # AA 급
    (0.05, 25),  # A 급
    (0.1, 40),  # BBB 급
    (0.3, 60),  # BB 급
    (1.0, 80),  # B 이하
]
