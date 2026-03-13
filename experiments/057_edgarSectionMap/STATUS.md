# 057 EDGAR 섹션 맵 (v2)

## 목적

EDGAR docs를 DART `056_sectionMap`과 같은 철학으로 수평 비교 가능한 topic 체계로 정리한다.

## 이전 실패 (057_edgarSectionMap_fail)

- 수집 파이프라인 4개 파편화 (002, 016, 017, 018)
- `signal.SIGALRM` Windows 미지원으로 WSL 의존
- 2,000개 목표에 31개 수집 후 중단
- output 스냅샷과 실제 데이터 불일치

## 이번 방침

1. **수집 파이프라인 1개로 통일** — subprocess ticker 격리 + timeout
2. **Windows 네이티브 호환** — signal.SIGALRM 사용 금지
3. **단계별 진행** — universe 확인 → 수집 → title 전수조사 → 매퍼 구축
4. **fetch.py 그대로 사용** — signal.SIGALRM 버그는 패키지에서 이미 수정됨

## 진행 순서

1. universe 정의 + 현재 상태 확인
2. 대형주 수집 (priority 30개)
3. 배치 수집 확대 (exchange listed → 2,000개)
4. title frequency 전수조사
5. canonical topic 설계 + sectionMappings 구축
6. sections 파이프라인 검증

## 실험 파일

- `001_universeSurvey.py` — listed universe, 로컬 커버리지 확인
