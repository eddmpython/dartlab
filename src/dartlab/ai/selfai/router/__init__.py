"""도구 라우터 — 질문을 분석하여 최적의 dartlab 도구와 코드를 선택.

2단계 아키텍처의 Stage 1.
로컬 소형 모델(Qwen3 1.7B)로 초고속 도구 선택 → Stage 2(해석기)의 부담을 줄인다.

3가지 모드:
1. rule: 규칙 기반 (모델 불필요, Phase 1-2 즉시 사용)
2. local: ExLlamaV2 로컬 모델 (Phase 3)
3. hybrid: rule 우선 → 불확실하면 local fallback
"""

from dartlab.ai.selfai.router.engine import route

__all__ = ["route"]
