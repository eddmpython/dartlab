# finance/shareCapital 현황

## 개요
사업보고서 "주식의 총수 등" 섹션에서 발행주식/자기주식/유통주식 데이터 추출.

## 파일 구성
| 파일 | 역할 |
|------|------|
| types.py | ShareCapitalResult 데이터클래스 |
| parser.py | Ⅰ~Ⅶ 번호 체계 테이블 파서 (parseShareCapitalTable) |
| pipeline.py | shareCapital(stockCode) 파이프라인 |
| __init__.py | 공개 API export |

## 성능
- 전체 테스트: 100% (226개 성공, 실패 0)
- 섹션 없음: 3개 (데이터 수집 이슈)

## 데이터 구조
Ⅰ~Ⅶ 번호 체계, 5셀 구조 (구분, 보통주, 우선주, 합계, 비고):
- Ⅰ 발행할 주식의 총수 (authorizedShares)
- Ⅱ 현재까지 발행한 주식의 총수 (issuedShares)
- Ⅲ 현재까지 감소한 주식의 총수 (retiredShares)
- Ⅳ 발행주식의 총수 (outstandingShares)
- Ⅴ 자기주식수 (treasuryShares)
- Ⅵ 유통주식수 (floatingShares)
- Ⅶ 자기주식 보유비율 (treasuryRatio)

## 알려진 제한
- 보통주 기준 첫 번째 숫자만 추출 (우선주 별도 추출 미지원)
- 2018 주식분할 이전 데이터와 이후 데이터 단위 다름 (삼성전자)

## 실험 근거
- experiments/009_shareCapital/
