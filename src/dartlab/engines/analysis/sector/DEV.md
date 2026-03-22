# Sector — WICS 투자 섹터 분류

## 구조

```
sector/
├── classifier.py   # 3단계 하이브리드 분류기
├── params.py       # 업종별 재무 파라미터 (discountRate, β, 벤치마크)
├── types.py        # SectorClass, SectorInfo, SectorParams, IndustryGroup
└── spec.py         # 메타데이터 (11 sectors × 34 industry groups)
```

## 3단계 분류 로직

```
1️⃣ 수동 오버라이드 (~100 대형주)
  ↓ 미매칭
2️⃣ 주요제품 키워드 분석 (docs에서 추출)
  ↓ 미매칭
3️⃣ KSIC 업종명 매핑 (KIND 상장사 목록)
```

## 분류 체계

- **11 섹터**: 에너지, 소재, 산업재, 경기소비재, 필수소비재, 건강관리, 금융, IT, 통신, 유틸리티, 부동산
- **34 산업군**: 섹터 하위 세분류 (IndustryGroup enum)
- WICS (Wise Industry Classification Standard) 기반

## 의존성

- **0 외부 의존**: 다른 엔진을 import하지 않음
- **소비자**: insight, rank, watch, common.finance.{valuation, forecast, simulation}

## Company 부착

- `c.sector` → SectorInfo (섹터/산업군/분류 근거)
- `c.sectorParams` → SectorParams (discountRate, β, 벤치마크 기준값)
- 모두 lazy import
