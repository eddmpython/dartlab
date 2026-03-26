# Watch — 공시 변화 감지

## 구조

```
watch/
├── scanner.py   # scan_company() / scan_market()
├── scorer.py    # 중요도 스코어링 (4요소 가중합)
├── digest.py    # 시장 다이제스트 (전체 종목 변화 요약)
└── spec.py      # 메타데이터 (가중치 설정)
```

## 중요도 스코어링 (4요소)

| 요소 | 배점 | 설명 |
|------|------|------|
| 변화율 | 50점 | 기간간 텍스트 해시 변화 비율 |
| 토픽 가중치 | ×1.5 | 특정 토픽(리스크, 감사 등) 가중 |
| 텍스트 크기 | 30점 | 변화된 텍스트 분량 |
| 키워드 | 20점 | 핵심 키워드 출현 빈도 |

## 핵심 동작

- `scan_company(c)`: 단일 기업 — 기간간 변화 토픽 + 중요도 순위
- `scan_market(companies)`: 시장 전체 — 변화 감지 다이제스트
- `common/docs/diff.py` 결과를 입력으로 사용

## 의존성

- `common.docs` — diff 엔진
- `sector` — 섹터별 토픽 가중치 조정

## Company 부착

- `c.watch()` → WatchResult (method, lazy import)
