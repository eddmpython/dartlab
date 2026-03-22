# Company 엔진 — L1 데이터 소스 통합

## 구조

```
company/
├── dart/      # 한국 DART 전자공시
│   ├── company.py     # DART Company 본체
│   ├── docs/          # 공시 문서 파싱 (sections 수평화)
│   ├── finance/       # XBRL 재무 정규화
│   ├── report/        # 정기보고서 API (28개 apiType)
│   ├── openapi/       # OpenDART API 클라이언트 + 수집기
│   └── scan/          # 시장 스캔 (network, signal)
├── edgar/     # 미국 SEC EDGAR
│   ├── company.py     # EDGAR Company 본체
│   ├── docs/          # 10-K/10-Q sections 수평화
│   ├── finance/       # SEC XBRL 재무 정규화
│   └── openapi/       # SEC API 클라이언트
└── edinet/    # 일본 EDINET
    ├── company.py     # EDINET Company 본체
    ├── docs/          # 유가증권보고서 수평화
    ├── finance/       # EDINET XBRL 정규화
    └── openapi/       # EDINET API 클라이언트
```

## 원칙

- 각 엔진은 `CompanyProtocol`을 구현 (common/protocols.py)
- 공통 인터페이스: `show()`, `trace()`, `diff()`, `filings()`, `ask()`, `chat()`
- 3-namespace: `docs` (서술형), `finance` (정량), `report` (정형, DART만)
- 하위 엔진은 루트 facade (`dartlab.company`)를 import하지 않는다
- L2 분석 엔진(analysis/)은 lazy import로만 부착

## 상세

- dart: `company/dart/DEV.md`
- edgar: `company/edgar/DEV.md`
