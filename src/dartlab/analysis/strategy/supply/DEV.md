# Supply — 공급망 분석

## 구조

```
supply/
├── extractor.py   # segments/rawMaterial/relatedParty에서 공급망 추출
├── mapper.py      # 고객/공급사 식별 + 관계 매핑
├── risk.py        # HHI 집중도, 투명도 리스크 스코어링
├── types.py       # SupplyChainResult, SupplyLink
└── spec.py        # 메타데이터 (4 risk factors)
```

## 핵심 설계

- **docs sections 기반**: segments, rawMaterial, relatedPartyTx 토픽에서 추출
- **HHI 집중도**: 매출/매입 집중도 (Herfindahl-Hirschman Index)
- **4가지 리스크**: 고객 집중, 공급사 집중, 원재료 의존, 관계사 거래 비중

## 의존성

- self-contained: duck-typed Company만 사용

## Company 부착

- `c.supply` → SupplyChainResult (property, lazy import)
