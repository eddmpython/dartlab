"""DART OpenAPI 클라이언트.

from dartlab import Dart

d = Dart()
s = d("삼성전자")

s.finance(2020)                         # 2020~현재 Q1~Q4
s.report("배당", 2020)                  # 배당 2020~현재
s.filings("2024")                       # 공시
s.info()                                # 개황
s.shares()                              # 지분공시
s.saveFinance("재무.csv", 2020, kr=True) # 한글 컬럼 저장
"""

from dartlab.engines.dart.openapi.dart import Dart, DartCompany
from dartlab.engines.dart.openapi.saver import korColumns

__all__ = ["Dart", "DartCompany", "korColumns"]
