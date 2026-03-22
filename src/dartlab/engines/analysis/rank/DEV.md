# Rank — 시장 규모 순위

## 구조

```
rank/
├── rank.py    # 시장 전체/섹터 순위 스냅샷 빌드 + 조회
├── screen.py  # 필터링 (sizeClass, 성장률, 수익성 등)
└── spec.py    # 메타데이터
```

## 핵심 동작

- **빌드**: ~2700 종목의 매출/자산/3년 성장률 스냅샷 (약 2분)
- **조회**: 빌드 후 즉시 순위 조회 (O(1))
- **sizeClass**: Large (상위 100) / Mid (100~500) / Small (나머지)

## RankInfo

| 필드 | 설명 |
|------|------|
| revenueRank | 매출 순위 |
| assetRank | 자산 순위 |
| growthRank | 3년 매출 성장률 순위 |
| sizeClass | Large / Mid / Small |

## 의존성

- `gather.listing` — KRX 상장사 목록
- `common.finance` — 재무비율 계산
- `sector` — 섹터별 순위 필터

## Company 부착

- `c.rank` → RankInfo (property, lazy import)
