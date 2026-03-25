# Analysis 엔진 — L2 분석 모듈 통합

## 구조

```
analysis/
├── sector/    # WICS 투자 섹터 분류 (11섹터, 23산업군)
├── insight/   # 10영역 종합 등급 (성과/수익성/안정성/현금흐름/지배구조/리스크/기회/예측성/불확실성/핵심이익)
├── rank/      # 시장 규모 순위 (매출/자산/성장률, ~2700종목)
├── esg/       # ESG 공시 분석 (E/S/G 3축, 36토픽)
├── supply/    # 공급망 관계 + 리스크 스코어링
├── event/     # 공시 이벤트 스터디 (CAR/BHAR, t-test)
├── watch/     # 공시 변화 감지 (중요도 스코어링)
├── analyst/   # 멀티소스 밸류에이션 합성 (DCF + consensus + peer)
├── peer/      # 글로벌 피어 매핑 (WICS→GICS) + 멀티소스 컨센서스
└── research/  # 교차분석 서술 엔진 (narrative + thesis + sectorKpi)
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
peer ← gather.consensus, gather.listing, sector
research ← insight, peer, company (오케스트레이션)
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
| peer | `c.peers`, `c.peerConsensus` | property |
| research | 별도 `research()` 함수 | standalone |

모든 부착은 lazy import — Company 초기화 시 로드되지 않음.

## spec 체계

- 9/10 모듈에 `spec.py` 존재 (analyst 미구현)
- `engines/ai/spec.py`가 전체 수집
- `test_spec_integrity.py`로 spec-코드 일치 검증

## 공통 패턴

모든 모듈은 다음 구조를 따른다:

```
analysis/{module}/
├── __init__.py      # public API export
├── spec.py          # 메타데이터 (buildSpec())
├── types.py         # 타입 정의
└── [로직 파일들]
```

새 모듈 추가 시:
1. `analysis/` 아래 디렉토리 생성
2. `spec.py` 작성 (buildSpec() → dict 반환)
3. `ai/spec.py`의 `_ENGINE_SPECS`에 경로 등록
4. Company 부착이 필요하면 `company.py`에 lazy import 추가

## 모듈별 상세

- `sector/DEV.md` — WICS 3단계 분류
- `insight/DEV.md` — 10영역 등급 + 부실 모델
- `rank/DEV.md` — 시장 규모 순위
- `esg/DEV.md` — ESG 3축 분석
- `supply/DEV.md` — 공급망 리스크
- `event/DEV.md` — 이벤트 스터디
- `watch/DEV.md` — 공시 변화 감지
- `analyst/DEV.md` — 밸류에이션 합성
- `peer/` — 글로벌 피어 매핑 + 컨센서스
- `research/` — 교차분석 서술 엔진 (experimental)
