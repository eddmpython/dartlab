"""extractTables 디버그 - SPAC BS 테이블 파싱 확인."""

import sys

sys.path.insert(0, "src")

from dartlab.core.tableParser import detectUnit, extractTables

# SPAC BS content (482690 대신밸런스)
content = """| 재무상태표 |
| --- |
| 제 1 기 2024.12.31 현재 |
| (단위 : 원) |
|  | 제 1 기 |
| --- | --- |
| 자산 |  |
| 유동자산 | 13,344,297,190 |
| 현금및현금성자산 | 2,299,598,441 |
| 단기금융상품 | 11,000,000,000 |
| 기타유동금융자산 | 44,468,849 |
| 당기법인세자산 | 229,900 |
| 비유동자산 | 0 |
| 자산총계 | 13,344,297,190 |
| 부채 |  |
| 유동부채 | 13,062,500 |
| 기타유동금융부채 | 13,062,500 |
| 기타 유동부채 |  |
| 비유동부채 | 1,851,873,168 |"""

tables = extractTables(content)
print(f"extractTables: {len(tables)} tables")
for i, t in enumerate(tables):
    print(f"\nTable {i}:")
    print(f"  headers ({len(t['headers'])}): {t['headers']}")
    print(f"  rows ({len(t['rows'])}): {t['rows'][:3]}")

unit = detectUnit(content)
print(f"\ndetectUnit: {unit}")
