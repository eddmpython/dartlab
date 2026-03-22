# ESG — 공시 기반 ESG 분석

## 구조

```
esg/
├── extractor.py   # docs sections에서 E/S/G 3축 평가
├── taxonomy.py    # K-ESG/GRI/TCFD 표준 매핑 (36토픽)
├── timeline.py    # 연도별 ESG 추적
├── types.py       # EsgResult, EsgPillar
└── spec.py        # 메타데이터 (3 pillars, GRI indices)
```

## 핵심 설계

- **공시 기반**: 외부 ESG 등급 없이 사업보고서 sections에서 직접 추출
- **3축 평가**: Environmental / Social / Governance
- **36 토픽**: GRI/TCFD 카테고리 기반 세분류
- **연도별 추적**: 같은 토픽의 기간간 변화 감지

## 의존성

- self-contained: duck-typed Company만 사용 (특정 엔진 import 없음)

## Company 부착

- `c.esg` → EsgResult (property, lazy import)
