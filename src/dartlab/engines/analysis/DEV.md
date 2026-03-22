# Analysis 엔진 — L2 분석 모듈 통합

## 구조

```
analysis/
├── sector/    # WICS 투자 섹터 분류 (11섹터, 23산업군)
├── insight/   # 7영역 종합 등급 (성과/수익성/안정성/현금흐름/지배구조/리스크/기회)
├── rank/      # 시장 규모 순위 (매출/자산/성장률, ~2700종목)
├── esg/       # ESG 공시 분석 (E/S/G 3축, 36토픽)
├── supply/    # 공급망 관계 + 리스크 스코어링
├── event/     # 공시 이벤트 스터디 (CAR/BHAR, t-test)
├── watch/     # 공시 변화 감지 (중요도 스코어링)
└── analyst/   # 멀티소스 밸류에이션 합성 (DCF + consensus + peer)
```

## 의존 방향

```
sector (0 외부 의존)
  ↓ (소비: insight, rank, watch, common.finance)
insight ← common.finance, company.dart.finance
rank ← gather.listing, common.finance, sector
watch ← common.docs, sector
esg, supply, event ← self-contained (duck-typed Company)
analyst ← gather (절대 import)
```

## Company 부착

| 모듈 | Company 노출 | 타입 |
|------|-------------|------|
| sector | `c.sector`, `c.sectorParams` | property |
| insight | `c.insights` | property |
| rank | `c.rank` | property |
| esg | `c.esg` | property |
| supply | `c.supply` | property |
| event | `c.eventStudy()` | method |
| watch | `c.watch()` | method |
| analyst | 별도 `Analyst()` 클래스 | standalone |

모든 부착은 lazy import — Company 초기화 시 로드되지 않음.

## spec 체계

- 7/8 모듈에 `spec.py` 존재 (analyst 미구현)
- `engines/ai/spec.py`가 전체 수집
- `test_spec_integrity.py`로 spec-코드 일치 검증
