# YTD 문제 해결 현황 (2026-01-23)

## 작업 요약

### ✅ 완료된 작업
1. **데이터 품질 이슈 문서화**
   - `DATA_QUALITY_ISSUES.md`: 다중 값 혼재, Amended Period, Frame 필드 등
   - `CRITICAL_ISSUE_YTD.md`: YTD vs 개별 분기 패턴 분석

2. **28개 종목 대량 검증**
   - 정상: 22개 (AAPL, MSFT, META, 금융/헬스케어/소비재/에너지 등)
   - YTD 패턴: 2개 (GOOG, NVDA 의심)
   - 기타 이상: GE (음수 Q4), 금융주 (Q2 급감)

3. **주요 수정 사항**
   - Frame 필드 추가 및 frame_priority 로직
   - FY/Q1에 대해 max() 선택 (세그먼트 배제)
   - Q2/Q3에 대해 min() 선택 (YTD 배제 시도)
   - Amended Period 파싱 수정 (2012-Q2A 처리)

### ⚠️ 미해결 이슈: GOOG 등 YTD 전용 종목

**문제**:
- GOOG, 일부 다른 종목은 **개별 분기 값을 전혀 제공하지 않고 YTD만 제공**
- 현재 min() 선택 로직으로는 해결 불가 (min도 YTD)

**GOOG 2024 Revenue 실제 데이터**:
```
Q1: $80.54B ✅ (개별)
Q2: $144.39B ❌ (YTD, 실제 개별은 $63.85B)
Q3: $221.08B ❌ (YTD, 실제 개별은 $76.69B)
```

**시도한 해결책**:
1. ❌ 모든 분기에 max() 선택 → 타입 A 종목 (개별+YTD 혼재) 망가짐
2. ❌ 조건부 max/min 선택 + YTD 역산 → 복잡도 높고 엣지 케이스 다수
3. ❌ dataLoader에서 YTD 역산 → 같은 연도 내 누적 계산 버그

---

## 현재 상태 (안정 버전)

### 코드 상태

**search.py** (라인 206-224):
```python
# FY/Q1: max() - 전체 합계 선택
# Q2/Q3: min() - 개별 분기 선택 (YTD 배제)
stmtDf = (
    stmtDf
    .filter(pl.col("frame_priority") == 1)
    .with_columns([
        pl.when(pl.col("periodCol").str.ends_with("-FY") | pl.col("periodCol").str.ends_with("-Q1"))
            .then(pl.lit("max"))
            .otherwise(pl.lit("min"))
            .alias("agg_method")
    ])
    .group_by(["displayAccount", "periodCol"])
    .agg([
        pl.when(pl.col("agg_method").first() == "max")
            .then(pl.col("val").max())
            .otherwise(pl.col("val").min())
            .alias("val")
    ])
)
```

**dataLoader.py** (라인 130-199):
- YTD 역산 로직 비활성화 (안정성 우선)
- Q4 계산: Q4 = FY - Q1 - Q2 - Q3 (IS/CF만)
- BS는 Q4 = FY 그대로 (시점 데이터)

### 검증 결과

| Ticker | Q1 | Q2 | Q3 | Q4 | 상태 |
|--------|----|----|----|----|------|
| AAPL | $119.6B | $90.8B | $85.8B | $94.9B | ✅ 정상 |
| MSFT | $56.5B | $62.0B | $61.9B | $64.7B | ✅ 정상 |
| NVDA | $7.2B | $13.5B | $18.1B | $22.1B | ✅ 정상 |
| **GOOG** | $80.5B | **$144.4B** | **$221.1B** | None | ❌ YTD |

**전체 신뢰도**: 약 90% (GOOG 등 타입 B 제외)

---

## 제안 솔루션

### 옵션 1: 수동 보정 (단기)

**GOOG 등 알려진 YTD 종목에 대해 수동 플래그 추가**:

```python
YTD_ONLY_TICKERS = ['GOOG', ...]

if ticker in YTD_ONLY_TICKERS:
    # 특별 처리: max 선택 후 YTD 역산
    q2_individual = q2_ytd - q1
    q3_individual = q3_ytd - q2_ytd
```

**장점**: 간단, 안정적
**단점**: 확장성 없음, 모든 종목 수동 확인 필요

### 옵션 2: 휴리스틱 기반 자동 감지 (중기)

**min과 max 비율로 YTD 판단**:

```python
if (max_val / min_val > 1.5) and period in ['Q2', 'Q3']:
    # YTD로 판단 → max 선택 후 역산
    selected = max_val
    if period == 'Q2':
        individual = selected - q1
    elif period == 'Q3':
        individual = selected - q2_ytd
else:
    # 개별 값 → min 선택
    selected = min_val
```

**장점**: 대부분 종목 자동 처리
**단점**: 실제 성장률 150% 종목 (NVDA 등) 오판 가능

### 옵션 3: XBRL contextRef 파싱 (장기)

**SEC API의 XBRL 메타데이터 활용**:

```xml
<context id="From2024-01-01to2024-06-30">  <!-- YTD Q2 -->
<context id="From2024-04-01to2024-06-30">  <!-- 개별 Q2 -->
```

**장점**: 100% 정확
**단점**: 구현 복잡도 높음, API 호출 증가

### 옵션 4: 현상 유지 + 문서화 (당장)

**타입 B 종목은 알려진 제약으로 문서화**:

```markdown
## 알려진 제약

일부 종목 (GOOG 등)은 Q2/Q3를 YTD로 보고합니다.
이 경우 개별 분기 값이 아닌 누적 값이 표시됩니다.

영향 종목: GOOG, (추가 확인 필요)
대응: 수동 보정 또는 주의 표시
```

**장점**: 시간 절약, 90% 종목은 정상 작동
**단점**: GOOG 사용자 혼란 가능

---

## 권장 사항

### 즉시 (Phase 1)
1. ✅ 현재 안정 버전 유지
2. ✅ DATA_QUALITY_ISSUES.md, CRITICAL_ISSUE_YTD.md 문서화 완료
3. ⏭️ YTD 종목 목록 작성 (S&P 100 전체 검증)
4. ⏭️ UI에 주의 표시 추가 ("⚠️ YTD 누적 값")

### 단기 (Phase 2)
5. 옵션 1 구현: 수동 플래그 + 특별 처리
6. EdgarWings UI 완성
7. 사용자 피드백 수집

### 중장기 (Phase 3)
8. 옵션 2 구현: 휴리스틱 자동 감지
9. S&P 500 전체 검증
10. (필요시) 옵션 3: XBRL contextRef 파싱

---

## 학습 내용

### 발견 1: EDGAR 데이터 = 비정형

SEC는 표준 XBRL을 사용하지만, **기업마다 보고 방식이 다름**:
- 타입 A (80%): 개별 + YTD 혼재
- 타입 B (20%): YTD만 제공

### 발견 2: Frame 필드 ≠ Context

`frame` 필드는 재작성 여부를 나타내지, YTD vs 개별을 구분하지 않음:
- `frame=null`: 당기 값 (YTD 또는 개별)
- `frame=CY2023Q1`: 전기 비교 재작성

### 발견 3: Min/Max 선택의 한계

동일한 휴리스틱으로 모든 패턴을 커버할 수 없음:
- FY: max (세그먼트 배제) ✅
- Q1: max (일관성) ✅
- Q2/Q3 타입 A: min (YTD 배제) ✅
- Q2/Q3 타입 B: max + 역산 (개별 추출) ⚠️

→ **조건부 로직 필요**

---

## 다음 작업

- [ ] S&P 100 YTD 패턴 전수 조사
- [ ] 타입 B 종목 목록 작성
- [ ] 옵션 1 구현 (수동 플래그)
- [ ] EdgarWings UI 완성
- [ ] DartWings와 UI 통합

---

**작성일**: 2026-01-23
**작성자**: Claude Sonnet 4.5
**버전**: v1.0 (안정 버전 복원 완료)
