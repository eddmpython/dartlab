"""frame — L1.5 raw 결합 가공 (분석 ready normalized view).

여러 raw 엔진 (gather·providers) 결과를 결합해 분석엔진 (L2) 이 보는
normalized view 제공. raw 생산 0 — 가공만. 본 단계 (P-CORE A) 에서는
디렉토리 골격만, 모듈 이동은 후속 단계 (P-CORE B) 에서 진행.

룰 (operation.architecture SSOT):
- import OK: dartlab.core, dartlab.gather, dartlab.providers
- import 금지: dartlab.{scan, synth, reference} (L1.5 4 형제 cross 금지)
- 진입 조건: ≥ 2 분석엔진이 같은 형태로 사용해야 함
- 비즈니스 로직 금지 (지표 계산·점수화·랭킹·룰 매칭은 synth/L2 영역)
"""

from dartlab.core import dataLoader as dataLoader
from dartlab.frame import inventory as inventory
from dartlab.frame import narrative as narrative

__all__ = ["dataLoader", "inventory", "narrative"]
