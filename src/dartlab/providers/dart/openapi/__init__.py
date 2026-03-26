"""DART OpenAPI 클라이언트.

from dartlab import OpenDart

d = OpenDart()
s = d("삼성전자")

s.finance(2020)                         # 2020~현재 Q1~Q4
s.report("배당", 2020)                  # 배당 2020~현재
s.filings("2024")                       # 공시
s.info()                                # 개황
s.shares()                              # 지분공시
s.saveFinance("재무.csv", 2020, kr=True) # 한글 컬럼 저장
호환 alias:
    from dartlab import Dart
"""

from dartlab.providers.dart.openapi.dart import Dart, DartCompany, OpenDart, OpenDartCompany
from dartlab.providers.dart.openapi.saver import korColumns

__all__ = ["OpenDart", "OpenDartCompany", "Dart", "DartCompany", "korColumns"]
