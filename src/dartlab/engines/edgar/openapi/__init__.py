"""EDGAR OpenAPI facade.

from dartlab import OpenEdgar

e = OpenEdgar()
aapl = e("AAPL")

aapl.info()
aapl.filings(forms=["10-K", "10-Q"])
aapl.companyFactsJson()
aapl.saveDocs()
aapl.saveFinance()
"""

from dartlab.engines.edgar.openapi.edgar import OpenEdgar, OpenEdgarCompany

__all__ = ["OpenEdgar", "OpenEdgarCompany"]
