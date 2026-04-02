---
title: Export
---

# Export

데이터를 외부 형식으로 내보내는 기능.

> **안정성: Experimental (Tier 3)** — 인터페이스가 변경될 수 있습니다.

## Excel 내보내기

```python
import dartlab

c = dartlab.Company("005930")
c.excel("삼성전자_분석.xlsx")  # 재무제표 + 분석 결과를 Excel로
```

## 지원 형식

| 형식 | 상태 | 설명 |
|------|------|------|
| Excel (.xlsx) | Experimental | openpyxl 기반 |
| CSV | 미구현 | 계획 중 |
| JSON | 미구현 | 계획 중 |

## 필요 패키지

```bash
pip install dartlab  # openpyxl이 base에 포함
```
