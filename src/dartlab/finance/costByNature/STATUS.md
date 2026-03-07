# finance/costByNature 현황

## 개요
연결재무제표 주석에서 "비용의 성격별 분류" 테이블 추출, 계정명 정규화, 시계열 구성.

## 파일 구성
| 파일 | 역할 |
|------|------|
| types.py | CostByNatureResult 데이터클래스 |
| parser.py | 비용의 성격별 분류 파서 (inline/split/multiCol 3방식) |
| pipeline.py | costByNature(stockCode, period) 파이프라인 |
| __init__.py | 공개 API export |

## 성능
- 전체 테스트: 100% (171/171 파싱 성공)
- 시계열 구성: 173개 종목
- 교차검증 일치율: 87.8%
- null 비율: 17.5%

## 파서 구조
- 3가지 테이블 유형 자동 감지: inline (당기/전기 병렬), split (기간별 별도 블록), multiCol
- 30개 정규화 매핑: 487개 원본 계정명 → 표준 계정명
- 22가지 합계행 패턴 자동 제거

## period 파라미터
- "y": 사업보고서 (연간)
- "q": Q1/반기/Q3/사업보고서 (분기)
- "h": 반기/사업보고서 (반기)
- 분기/반기 보고서에 비용의 성격이 없는 기업 다수 (연간만 공시)

## 비용 구성비
- ratios: 각 비용 항목의 양수 합계 대비 비율(%) DataFrame
- year, account, amount, ratio 컬럼

## 알려진 제한
- 금융업/리츠/지주회사는 비용의 성격 미공시 (58개/267개)
- 교차검증 불일치 12.2%는 기업의 소급 재작성 (파서 오류 아님)

## 실험 근거
- experiments/004_costByNature/
