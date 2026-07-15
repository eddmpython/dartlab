# Visual attempts

> 상태: 계획 확정, 미실행
> 책임: semantic LOD, 상태 문법, layout 결정론, renderer 성능, 접근성, 3D uplift를 반증한다.

## 가설

의미 좌표와 representation 교체형 zoom을 쓰면 force graph보다 상태, 시간, 근거, 결손을 빠르고 정확하게 읽을 수 있다.

## 실행 순서

1. U0-V01: fact, candidate, derived, disputed, scenario, unknown 문법 판독
2. U0-V02: 고정 anchor와 deterministic layout
3. U0-V03: 250, 500, 1,000 node density와 omitted receipt
4. U0-V04: validAt와 knownAt 이중 시간 comprehension
5. U0-V05: keyboard, screen reader, mobile low GPU
6. U0-V06: SVG, current Cosmos, DOM, 후보 renderer bakeoff
7. U5-X01: 2D 대비 2.5D 또는 3D uplift

## 합격

- 상태 판독 90% 이상
- label collision 2% 이하
- logical coordinate hash 일치, 같은 viewport와 DPR에서 고정 anchor 재실행 오차 1px 이하
- desktop 45fps, mobile 30fps 목표 또는 명시적 lower LOD
- table에서 핵심 task 100% 완료

## 기각

- unknown을 낮은 점수 색으로 표현
- opacity 하나로 confidence와 status를 표현
- 3D에서만 가능한 핵심 기능
- decorative starfield 또는 particle가 정보 수율을 낮춤
- 새 dependency가 task, frame, heap, bundle을 개선하지 못함

## 산출물 예정

- renderer별 동일 scene fixture
- comprehension task와 score sheet
- frame, heap, hit-test, context-loss 측정
- keyboard와 screen reader task receipt

production dependency는 U0-V06 결론 전에 추가하지 않는다.
