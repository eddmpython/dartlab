"""reference. L1.5 JSON 룩업 + 매핑 엔진.

정적 reference dataset (JSON) 과 그것을 읽는 매핑 엔진 (BaseMapper 계열).

구성: `data` (정적 JSON 9 종) · `mappers` (계정·섹션 매퍼) · `mapping` (매핑 적용) ·
`capability` (capability 카탈로그 룩업) · `docs` (문서 구조 룩업) · `render`
(룩업 결과 표현) · `dataProduct` (dataHub 가 읽는 metadata 선언).

룰 (operation.architecture SSOT):
- import OK: dartlab.core, dartlab.gather, dartlab.providers
- import 금지: dartlab.{scan, frame, synth} (L1.5 4 형제 cross 금지)
- 진입 조건: 2 개 이상 분석엔진이 같은 형태로 사용해야 함
- 정적 자원 (가공 아닌 룩업) 이지만 분석엔진이 직접 보는 표면이라 L1.5 에 동거
- 공개 호출계약 아님. 분석엔진이 소비하는 내부 룩업층이라 `__all__` 을 비워 두고
  `dartlab.reference(...)` 같은 호출 표면을 두지 않는다.
"""

__all__: list[str] = []
