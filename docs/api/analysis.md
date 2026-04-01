---
title: Analysis (재무분석)
---

# Analysis — 14축 재무분석

단일 종목 심층 분석. 숫자 나열이 아니라 6막 인과 구조의 스토리텔링.

## 사용법

```python
c = dartlab.Company("005930")

c.analysis()                            # 전체 가이드
c.analysis("financial", "수익성")         # 수익성 분석
c.analysis("financial", "profitability") # 영문도 동일
c.analysis("valuation", "가치평가")      # 가치평가
c.analysis("forecast", "매출전망")       # 매출 전망
```

반환값은 dict. 각 축별 calc 함수의 결과가 키로 들어있다.

## 14축 체계

### 1부: 기초 분석

| 축 | 호출 | 핵심 질문 |
|------|------|---------|
| 수익구조 | `"financial", "수익구조"` | 무엇으로 돈을 버는가 |
| 자금조달 | `"financial", "자금조달"` | 돈을 어디서 조달하는가 |
| 자산구조 | `"financial", "자산구조"` | 자산을 어떻게 배치했는가 |
| 현금흐름 | `"financial", "현금흐름"` | 현금이 실제로 도는가 |

### 2부: 성과 분석

| 축 | 호출 | 핵심 질문 |
|------|------|---------|
| 수익성 | `"financial", "수익성"` | 얼마나 잘 버는가 |
| 성장성 | `"financial", "성장성"` | 얼마나 빨리 성장하는가 |
| 안정성 | `"financial", "안정성"` | 망하지 않는가 |
| 효율성 | `"financial", "효율성"` | 자산을 잘 굴리는가 |
| 종합평가 | `"financial", "종합평가"` | 재무 상태를 한마디로 |

### 3부: 심화 분석

| 축 | 호출 | 핵심 질문 |
|------|------|---------|
| 이익품질 | `"financial", "이익품질"` | 이익이 진짜인가 |
| 비용구조 | `"financial", "비용구조"` | 비용이 어떻게 움직이는가 |
| 자본배분 | `"financial", "자본배분"` | 번 돈을 어디에 쓰는가 |
| 투자효율 | `"financial", "투자효율"` | 투자가 가치를 만드는가 |
| 재무정합성 | `"financial", "재무정합성"` | 재무제표가 서로 맞는가 |

### 가치평가 + 전망

```python
c.analysis("valuation", "가치평가")    # DCF, DDM, 상대가치, RIM
c.analysis("forecast", "매출전망")     # 매출 방향 예측 (72-78% 정확도)
```

## 6막 서사 구조

analysis의 14축은 6막 인과 구조로 연결된다. **앞 막이 뒷 막의 원인.**

```
1막 사업이해 → 2막 수익성 → 3막 현금전환 → 4막 안정성 → 5막 자본배분 → 6막 전망
```

예: "DX 사업부 비중 확대(1막) → 마진 21% 회복(2막) → FCF 15조(3막) → 순현금(4막) → 배당 확대(5막)"

## 결과 사용 예시

```python
r = c.analysis("financial", "수익성")

# 마진 추이
for h in r["marginTrend"]["history"][:5]:
    print(f'{h["period"]}: 매출 {h["revenue"]/1e8:,.0f}억 | '
          f'영업이익률 {h["operatingMargin"]:.1f}%')

# 듀퐁 분해
dupont = r["returnTrend"]["history"][0]
print(f'ROE = 마진 {dupont["dupontMargin"]:.1f}% × '
      f'회전 {dupont["dupontTurnover"]:.2f} × '
      f'레버리지 {dupont["dupontLeverage"]:.2f}')
```
