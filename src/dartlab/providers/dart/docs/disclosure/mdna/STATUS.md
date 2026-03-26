# finance/mdna 현황

## 개요
사업보고서 "이사의 경영진단 및 분석의견" 섹션에서 MD&A 텍스트 추출.

## 파일 구성
| 파일 | 역할 |
|------|------|
| types.py | MdnaSection, MdnaResult 데이터클래스 |
| parser.py | 번호/한글 체계 섹션 분리 파서 (parseMdna, extractOverview) |
| pipeline.py | mdna(stockCode) 파이프라인 |
| __init__.py | 공개 API export |

## 성능
- 전체 테스트: 100% (206개 파싱 성공 + 61개 해당없음, 실패 0)

## 파서 구조
- 아라비아 숫자: `1. 2. 3.` (1~2자리, 연도 오탐 방지)
- 한글 번호: `가. 나. 다.` → 내부 1, 2, 3 매핑

## 섹션 분류
| 카테고리 | 키워드 |
|----------|--------|
| overview | 개요, 영업상황 |
| forecast | 예측정보 |
| financials | 재무상태, 영업실적, 경영성과 |
| liquidity | 유동성, 자금조달 |
| offBalance | 부외거래 |
| other | 그 밖에, 투자의사결정 |
| accounting | 회계정책, 회계추정 |
| regulation | 법규상, 규제 |
| derivative | 파생상품, 위험관리 |
| strategy | 추진 전략, 사업전망 |

## 알려진 제한
- 지주사(LG 등)는 자회사별 하위 섹션이 반복 → 섹션 수가 많음
- 리츠/SPAC 일부는 MD&A 미기재

## 실험 근거
- experiments/011_mdna/
