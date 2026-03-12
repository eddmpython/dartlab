# src/dartlab

## 개요
DART 공시 데이터 활용 라이브러리. 종목코드 기반 API.

## 구조
```
dartlab/
├── core/                    # 공통 기반 (데이터 로딩, 보고서 선택, 테이블 파싱, 주석 추출)
├── finance/                 # 재무 데이터 (36개 모듈)
│   ├── summary/             # 요약재무정보 시계열
│   ├── statements/          # 연결재무제표 (BS, IS, CF)
│   ├── segment/             # 부문별 보고 (주석)
│   ├── affiliate/           # 관계기업·공동기업 (주석)
│   ├── costByNature/        # 비용의 성격별 분류 (주석)
│   ├── tangibleAsset/       # 유형자산 (주석)
│   ├── notesDetail/         # 주석 상세 (23개 키워드)
│   ├── dividend/            # 배당
│   ├── majorHolder/         # 최대주주·주주현황
│   ├── shareCapital/        # 주식 현황
│   ├── employee/            # 직원 현황
│   ├── subsidiary/          # 자회사 투자
│   ├── bond/                # 채무증권
│   ├── audit/               # 감사의견·보수
│   ├── executive/           # 임원 현황
│   ├── executivePay/        # 임원 보수
│   ├── boardOfDirectors/    # 이사회
│   ├── capitalChange/       # 자본금 변동
│   ├── contingentLiability/ # 우발부채
│   ├── internalControl/     # 내부통제
│   ├── relatedPartyTx/      # 관계자 거래
│   ├── rnd/                 # R&D 비용
│   ├── sanction/            # 제재 현황
│   ├── affiliateGroup/      # 계열사 목록
│   ├── fundraising/         # 증자/감자
│   ├── productService/      # 주요 제품/서비스
│   ├── salesOrder/          # 매출/수주
│   ├── riskDerivative/      # 위험관리/파생거래
│   ├── articlesOfIncorporation/ # 정관
│   ├── otherFinance/        # 기타 재무
│   ├── companyHistory/      # 회사 연혁
│   ├── shareholderMeeting/  # 주주총회
│   ├── auditSystem/         # 감사제도
│   ├── investmentInOther/   # 타법인출자
│   └── companyOverviewDetail/ # 회사개요 상세
├── disclosure/              # 공시 서술형 (4개 모듈)
│   ├── business/            # 사업의 내용
│   ├── companyOverview/     # 회사의 개요 (정량)
│   ├── mdna/                # MD&A
│   └── rawMaterial/         # 원재료·설비
├── company.py               # 통합 접근 (property 기반, lazy + cache)
├── notes.py                 # K-IFRS 주석 통합 접근
└── config.py                # 전역 설정 (verbose)
```

## API 요약
```python
import dartlab

c = dartlab.Company("005930")
c.index                 # 회사 구조 인덱스
c.show("BS")            # topic payload
c.trace("dividend")     # source trace
c.BS                    # 재무상태표 DataFrame
c.dividend              # 배당 시계열 DataFrame

import dartlab
dartlab.verbose = False  # 진행 표시 끄기
```

## 현황
- 2026-03-06: core/ + finance/summary/ 초기 구축
- 2026-03-06: finance/statements/, segment/, affiliate/ 추가
- 2026-03-06: 전체 패키지 개선 — stockCode 시그니처, 핫라인 설계, API_SPEC.md
- 2026-03-07: finance/ 11개 모듈 추가 (dividend~bond, costByNature)
- 2026-03-07: disclosure/ 4개 모듈 추가 (business, companyOverview, mdna, rawMaterial)
- 2026-03-07: finance/ 주석 모듈 추가 (notesDetail, tangibleAsset)
- 2026-03-07: finance/ 7개 모듈 추가 (audit~internalControl, rnd, sanction)
- 2026-03-07: finance/ 7개 모듈 추가 (affiliateGroup~companyHistory, shareholderMeeting~investmentInOther, companyOverviewDetail)
- 2026-03-08: analyze → fsSummary 리네이밍, 계정명 특수문자 정리
- 2026-03-08: Company 재설계 — property 기반 접근, Notes 통합, all(), verbose 설정
