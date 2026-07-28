"""frame. L1.5 raw 결합 가공 (분석 ready normalized view).

여러 raw 엔진 (gather·providers) 결과를 결합해 분석엔진 (L2) 이 보는 normalized
view 를 준다. raw 생산 0, 가공만 한다.

구성: `inventory` (사업보고서 전체 인벤토리) · `narrative` (정성 서술 추출) ·
`resolve` (자연어 종목 해소) · `select` (select 반환 래퍼) · `sector` (섹터 결합) ·
`dataProduct` (dataHub 가 읽는 metadata 선언).

룰 (operation.architecture SSOT):
- import OK: dartlab.core, dartlab.gather, dartlab.providers
- import 금지: dartlab.{scan, synth, reference} (L1.5 4 형제 cross 금지)
- 진입 조건: 2 개 이상 분석엔진이 같은 형태로 사용해야 함
- 비즈니스 로직 금지 (지표 계산·점수화·랭킹·룰 매칭은 synth/L2 영역)
- 공개 호출계약 아님. 분석엔진이 소비하는 내부 가공층이라
  `dartlab.frame(...)` 같은 호출 표면을 두지 않는다.
"""

from dartlab.core import dataLoader as dataLoader
from dartlab.frame import inventory as inventory
from dartlab.frame import narrative as narrative

__all__ = ["dataLoader", "inventory", "narrative"]
