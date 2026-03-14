# 060 Lazy Profile 실험

## 요약

DART Company의 `_buildProfile`이 86개 topic을 eager `show()` → 30초.
lazy index로 전환하면 sections 메타데이터만으로 1.1초. **27배 빠름.**

## 실험 결과

### 001: 병목 정밀 측정

삼성전자(005930) 기준 86개 topic show() 개별 측정:

| 구간 | 개수 | 합계 | 비율 |
|------|------|------|------|
| > 1초 (느림) | 5개 | 16.6s | 75% |
| 0.01~1초 (보통) | 31개 | 5.5s | 25% |
| < 0.01초 (빠름) | 50개 | 0.06s | 0% |

느린 5개: fsSummary(6.4s), businessOverview(4.3s), consolidatedNotes(2.3s), affiliateGroup(1.9s), financialNotes(1.7s)

### 002: lazy vs eager 속도 비교

| 방식 | 시간 | 행 수 |
|------|------|-------|
| lazy (sections 메타 + finance + report 존재확인) | 1.18초 | 99행 |
| eager (_buildProfile → show() 전부) | 30.15초 | 86행 |
| **배율** | **25.5x** | |

### 003: sections diff 가능성

sections DataFrame만으로 기간간 텍스트 변화 감지:

- sections 로드: 0.674s
- diff 연산: 0.419s
- **총: 1.093s** (eager 30초 vs lazy+diff 1초)
- 71개 topic, 2,945개 변화 지점 감지
- hash 기반 비교 → 공백 차이도 잡힘

## 결론

- **lazy 전환 채택**: _buildProfile eager → lazy
- sections 수평화 spine은 동일 유지
- diff는 sections DataFrame 위에서 추가 연산 (0.4초)
- 개별 파서는 show(topic) 시에만 on-demand 실행
- Phase 3(매퍼 학습), Phase 4(diff + viewer) 모두 lazy 위에서 동작 가능
