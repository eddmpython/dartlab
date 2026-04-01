# dartlab 운영문서

프로젝트 전체의 설계 규칙, 엔진별 운영 체계, 품질 관리 절차를 한곳에 모은다.

## 진입점

| 문서 | 레이어 | 엔진 | 한 줄 요약 |
|------|--------|------|----------|
| [company.md](company.md) | L0/L1 | Company facade | sections 사상, 4 namespace, canHandle 라우팅 |
| [data.md](data.md) | L0 | core/dataConfig | HF 데이터셋, 수집 파이프라인, 카테고리 관리 |
| [scan.md](scan.md) | L1 | scan/ | 13축 시장 횡단분석 |
| [gather.md](gather.md) | L1 | gather/ | 외부 시장 데이터 (주가/수급/매크로/뉴스) |
| [quant.md](quant.md) | L1 | quant/ | 기술적 분석 (25개 지표, 9개 신호, 종합 판단) |
| [search.md](search.md) | L0 | core/search/ | 공시 시맨틱 검색 *(alpha)* |
| [analysis.md](analysis.md) | L2 | analysis/ | 14축 스토리텔링 재무분석, 6막 구조 |
| [review.md](review.md) | L2 | review/ | 블록-템플릿 보고서 렌더링, 4 출력 형식 |
| [credit.md](credit.md) | L2 | credit/ | 독립 신용평가 (dCR 20단계, 7축, 투명 공개) |
| [ai.md](ai.md) | L3 | ai/ | 적극적 분석가, 5 provider |
| [guide.md](guide.md) | 교차 | guide/ | 안내 데스크 + 교육 안내자, 4층위 |
| [experiments.md](experiments.md) | — | experiments/ | 실험 규칙, 흡수 판단 |
| [edgar.md](edgar.md) | L1 | providers/edgar/ | EDGAR 동기화 규칙, EXEMPT 관리, 데이터 소스 차이 |
| [code.md](code.md) | — | 전체 | camelCase, 독스트링 9섹션, 릴리즈, Git |
| [ui.md](ui.md) | L4 | ui/ + vscode/ | Svelte SPA + VSCode 확장, 패리티 규칙, 빌드/배포 |

## 레이어 아키텍처

```
L0 (인프라)     core/          protocols, finance, docs, registry, search
L1 (데이터)     providers/     DART, EDGAR, EDINET
                gather/        주가, 수급, 매크로, 뉴스
                scan/          시장 횡단분석 — scan("그룹", "축")
                quant/         기술적 분석
L2 (분석)       analysis/      재무+전망+가치평가 — analysis("그룹", "축")
                review/        6막 서사 보고서
L3 (AI)         ai/            적극적 분석가
L4 (표현)       ui/ + vscode/  Svelte SPA + VSCode 확장

교차 관심사     guide/         안내 데스크 (모든 레이어에서 import 가능)
```

## 엔진 호출 패턴

모든 엔진이 동일 패턴: `엔진("그룹", "축")` 또는 `엔진("축")`.

### analysis — 재무+전망+가치평가
```python
c.analysis("financial", "수익성")          # 그룹 + 하위
c.analysis("financial", "profitability")  # 영문도 동일
c.analysis("valuation")                   # 그룹 가이드
c.analysis("forecast", "revenue")         # 전망
c.analysis()                              # 전체 가이드
```

### scan — 시장 횡단분석
```python
dartlab.scan("financial", "profitability")  # 그룹 + 하위
dartlab.scan("governance")                  # 단일 축
dartlab.scan("screen", "value")             # 스크리닝 프리셋
dartlab.scan("account", "매출액")            # 계정 시계열
```

### 한글/영문 둘 다 가능
```python
c.analysis("financial", "수익성")          # 한글
c.analysis("financial", "profitability")  # 영문
dartlab.scan("financial", "수익성")        # 한글
dartlab.scan("financial", "profitability") # 영문
```

## 공통 규칙

- **코드 스타일**: camelCase (함수/변수), 이동된 snake_case는 하위호환 유지
- **진입점**: 종목코드 하나면 끝. `import dartlab` 하나로 모든 기능 접근
- **README 동기화**: 기능 변경 시 영문+한국어 동시 반영
- **노트북 감사**: 노트북 코드는 실행 확인 후에만 커밋
- **DART 먼저**: 모든 개선은 DART 우선, EDGAR는 안정화 후 따라감
- **import 방향**: L0 ← L1 ← L2 ← L3 (CI 검증)
