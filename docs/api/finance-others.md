---
title: Full Module Reference
---

# Full Module Reference

The public default path for `Company` is `sections -> show -> trace`. This document provides a reference for the report/docs source namespace one level below.

> **Warning: `c.report.extract(topic)` is an internal API.** For everyday analysis, use `c.show(topic)`.
> The `c.report.extract()` calls in the examples below are deep access patterns using `c.report.extract(topic)` or `c.docs.notes`.
>
> ```python
> # Recommended path
> c.show("dividend")           # show() applies source priority
> c.show("audit")
>
> # Deep access (report namespace directly)
> c.report.extract("dividend") # report Result object
> c.docs.notes.inventory       # K-IFRS notes directly
> ```

---

## Dividends, Shareholders & Capital Structure

### c.dividend — Dividends

Dividend time series. DPS, payout ratio, dividend yield, etc.

```python
c.dividend
# year | netIncome | eps | totalDividend | payoutRatio | dividendYield | dps | dpsPreferred
```

**Result attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `corpName` | `str \| None` | Company name |
| `nYears` | `int` | Number of years |
| `timeSeries` | `pl.DataFrame \| None` | Dividend time series |

**Usage example:**

```python
# Recent dividend info
div = c.dividend
if div is not None:
    last = div.row(-1, named=True)
    print(f"DPS: {last['dps']}원, 배당수익률: {last['dividendYield']}%")
```

---

### c.majorHolder — Largest Shareholder

Time series of the largest shareholder and related parties' ownership ratios.

```python
c.majorHolder
# year | majorHolder | majorRatio | totalRatio | holderCount | ...
```

Access individual shareholder list via report namespace:

```python
result = c.report.extract("majorHolder")  # or c.show("majorHolder")
result.majorHolder   # "이재용"
result.majorRatio    # 20.76
result.totalRatio    # Total related parties ownership ratio
result.holders       # list[Holder] — Individual shareholder list
```

**Holder attributes:**

| Attribute | Type | Description |
|-----------|------|-------------|
| `name` | `str` | Shareholder name |
| `relation` | `str` | Relationship (self, relative, executive, etc.) |
| `stockType` | `str` | Stock type |
| `sharesEnd` | `float \| None` | Shares at period end |
| `ratioEnd` | `float \| None` | Ownership ratio at period end (%) |

**Usage example:**

```python
result = c.report.extract("majorHolder")
print(f"최대주주: {result.majorHolder} ({result.majorRatio}%)")
for h in result.holders:
    print(f"  {h.name} ({h.relation}): {h.ratioEnd}%")
```

---

### c.holderOverview — Shareholder Overview

Comprehensive overview of 5%+ shareholders, minority shareholders, and voting rights. Returns a Result object directly.

```python
result = c.holderOverview

result.bigHolders    # list[BigHolder] — Shareholders with 5%+ ownership
result.minority      # Minority — Minority shareholder status
result.voting        # VotingRights — Voting rights status
```

**Usage example:**

```python
result = c.holderOverview
for bh in result.bigHolders:
    print(f"{bh.name}: {bh.ratio}%")
print(f"소액주주 비율: {result.minority.ratio}%")
```

---

### c.shareCapital — Total Shares

Time series of authorized, issued, treasury, and outstanding shares.

```python
c.shareCapital
# year | authorizedShares | issuedShares | treasuryShares | outstandingShares | ...
```

Full access via report namespace:

```python
result = c.report.extract("shareCapital")
result.authorizedShares    # Total authorized shares
result.issuedShares        # Total issued shares
result.treasuryShares      # Treasury shares
result.outstandingShares   # Outstanding shares
result.treasuryRatio       # Treasury share ratio
result.timeSeries          # Time series DataFrame
```

---

### c.capitalChange — Capital Changes

Changes in paid-in capital, total shares, and treasury shares.

```python
c.capitalChange
# year | commonShares | preferredShares | commonParValue | ...
```

Additional DataFrames via report namespace:

```python
result = c.report.extract("capitalChange")
result.capitalDf     # Paid-in capital change time series
result.shareTotalDf  # Total shares time series
result.treasuryDf    # Treasury shares change time series
```

---

### c.fundraising — Capital Increases/Decreases

Capital increase (decrease) history.

```python
c.fundraising
# date | issueType | stockType | quantity | parValue | issuePrice | note
```

---

## Executives & Governance

### c.executive — Executive Status

Aggregate time series of registered executives.

```python
c.executive
# year | totalRegistered | insideDirectors | outsideDirectors | otherNonexec | maleCount | femaleCount
```

Access unregistered executive compensation via report namespace:

```python
result = c.report.extract("executive")
result.executiveDf   # Registered executive aggregate time series
result.unregPayDf    # Unregistered executive compensation time series
```

**executiveDf key columns:**

| Column | Description |
|--------|-------------|
| `totalRegistered` | Total registered executives |
| `insideDirectors` | Inside directors |
| `outsideDirectors` | Outside directors |
| `otherNonexec` | Other non-executive directors |
| `fullTimeCount` | Full-time |
| `partTimeCount` | Part-time |
| `maleCount` | Male |
| `femaleCount` | Female |

---

### c.executivePay — Executive Compensation

Compensation time series by type (registered directors / outside directors / audit committee members).

```python
c.executivePay
# year | category | headcount | totalPay | avgPay
```

Individual compensation exceeding 500 million KRW via report namespace:

```python
result = c.report.extract("executivePay")
result.payByTypeDf   # Compensation by type time series
result.topPayDf      # Individual compensation exceeding 500M KRW
```

---

### c.boardOfDirectors — Board of Directors

Board composition, meeting frequency, and attendance rate time series.

```python
c.boardOfDirectors
# year | totalDirectors | outsideDirectors | meetingCount | avgAttendanceRate
```

Committee composition via report namespace:

```python
result = c.report.extract("boardOfDirectors")
result.boardDf      # Board time series
result.committeeDf  # Committee composition (committeeName, composition, members)
```

---

### c.audit — Audit Opinion

Audit firm, audit opinion, and key audit matters time series.

```python
c.audit
# year | auditor | opinion | keyAuditMatters
```

Audit fees via report namespace:

```python
result = c.report.extract("audit")
result.opinionDf   # Audit opinion time series
result.feeDf       # Audit fee time series (auditor, contractFee, contractHours, actualFee, actualHours)
```

---

### c.auditSystem — Audit System

Audit committee composition and audit activity records.

```python
c.auditSystem
# name | role | detail
```

Audit activities via report namespace:

```python
result = c.report.extract("auditSystem")
result.committeeDf   # Audit committee composition
result.activityDf    # Audit activity records (date, agenda, result)
```

---

### c.internalControl — Internal Controls

Evaluation of internal accounting control systems.

```python
c.internalControl
# year | opinion | auditor | hasWeakness
```

---

### c.shareholderMeeting — Shareholder Meeting

Shareholder meeting agendas and resolution results.

```python
c.shareholderMeeting
# agenda | result
```

---

## Risk & Regulation

### c.contingentLiability — Contingent Liabilities

Debt guarantees and litigation status.

```python
c.contingentLiability
# year | totalGuaranteeAmount | lineCount
```

Litigation status via report namespace:

```python
result = c.report.extract("contingentLiability")
result.guaranteeDf  # Debt guarantee time series
result.lawsuitDf    # Litigation status (filingDate, parties, description, amount, status)
```

---

### c.relatedPartyTx — Related Party Transactions

Transactions with major shareholders and related parties.

```python
c.relatedPartyTx
# year | entity | sales | purchases
```

Debt guarantees and asset transactions via report namespace:

```python
result = c.report.extract("relatedPartyTx")
result.revenueTxDf   # Revenue transaction time series
result.guaranteeDf   # Debt guarantee time series
result.assetTxDf     # Asset transaction time series
```

---

### c.sanction — Sanctions

Sanctions and penalties history.

```python
c.sanction
# year | date | agency | subject | action | amount | reason
```

---

### c.riskDerivative — Risk Management

FX sensitivity and derivative contract status.

```python
c.riskDerivative
# currency | upImpact | downImpact
```

Derivatives via report namespace:

```python
result = c.report.extract("riskDerivative")
result.fxDf          # FX sensitivity
result.derivativeDf  # Derivative contracts
```

---

## Business, Products & Revenue

### c.employee — Employee Status

Time series of headcount, average salary, and tenure.

```python
c.employee
# year | totalEmployees | avgTenure | totalSalary | avgSalary
```

| Attribute | Type | Description |
|-----------|------|-------------|
| `corpName` | `str \| None` | Company name |
| `nYears` | `int` | Number of years |
| `timeSeries` | `pl.DataFrame \| None` | Employee status time series |

**Usage example:**

```python
emp = c.employee
if emp is not None:
    last = emp.row(-1, named=True)
    print(f"직원수: {last['totalEmployees']:,}명, 평균연봉: {last['avgSalary']:,.0f}백만원")
```

---

### c.productService — Key Products

Key products and services status.

```python
c.productService
# label | amount | ratio
```

---

### c.salesOrder — Sales/Orders

Sales performance (by segment/product) and order backlog.

```python
c.salesOrder
# label | v1 | v2 | v3
```

Order status via report namespace:

```python
result = c.report.extract("salesOrder")
result.salesDf   # Sales performance
result.orderDf   # Order backlog
```

---

### c.rnd — R&D

R&D expenses and ratio to revenue.

```python
c.rnd
# year | rndExpense | revenueRatio
```

---

## Finance & Assets

### c.subsidiary — Subsidiaries

Comprehensive time series of investments in other companies.

```python
c.subsidiary
# year | totalCount | listedCount | unlistedCount | totalBook
```

Individual investee companies via report namespace:

```python
result = c.report.extract("subsidiary")
for inv in result.investments[:5]:
    print(f"{inv.name}: {inv.endRatio}%, 장부가 {inv.endBook}")
```

---

### c.bond — Debt Securities

Corporate bonds, commercial paper, and other debt securities issuance records.

```python
c.bond
# year | totalIssuances | totalAmount | unredeemedCount
```

Individual issuance details via report namespace:

```python
result = c.report.extract("bond")
for b in result.issuances:
    print(f"{b.bondType} | {b.amount}백만원 | {b.interestRate} | {b.rating}")
```

---

### c.otherFinance — Other Financial Items

Allowance for doubtful accounts and inventory status.

```python
c.otherFinance
# account | period | totalDebt | provision
```

Inventory via report namespace:

```python
result = c.report.extract("otherFinance")
result.badDebtDf     # Allowance for doubtful accounts
result.inventoryDf   # Inventory status
```

---

### c.investmentInOther — Investments in Other Companies

Investment status in other companies.

```python
c.investmentInOther
# name | 상장여부 | 최초취득일자 | 출자목적 | ...
```

---

## Company Information

### c.companyOverviewDetail — Company Basic Information

Returns a `dict` (not a DataFrame).

```python
info = c.companyOverviewDetail

info["foundedDate"]    # "1969-01-13"
info["listedDate"]     # "1975-06-11"
info["ceo"]            # "한종희"
info["address"]        # Headquarters address
info["mainBusiness"]   # Main business
info["website"]        # Homepage URL
```

---

### c.affiliateGroup — Affiliates

Affiliate company status.

```python
c.affiliateGroup
# name | listed
```

Additional info via report namespace:

```python
result = c.report.extract("affiliateGroup")
result.groupName      # "삼성"
result.listedCount    # Number of listed affiliates
result.unlistedCount  # Number of unlisted affiliates
result.totalCount     # Total number of affiliates
result.affiliateDf    # Affiliates DataFrame
```

---

### c.companyHistory — Company History

Company history events.

```python
c.companyHistory
# date | event
```

---

### c.articlesOfIncorporation — Articles of Incorporation

Amendment history and business purpose status.

```python
c.articlesOfIncorporation
# date | meetingName | changes | reason
```

Business purposes via report namespace:

```python
result = c.report.extract("articlesOfIncorporation")
result.changesDf    # Amendment history
result.purposesDf   # Business purposes (purpose, active)
```

---

## Disclosure Text

> **Recommended path**: Access narrative disclosure text through sections-based show() such as `c.show("businessOverview")`, `c.show("companyOverview")`, etc.
> The `c.business` and `c.mdna` below are legacy access paths via the docs namespace.

### c.docs.business — Business Description

```python
biz = c.docs.business
for s in biz:
    print(f"[{s.key}] {s.title} ({s.chars} chars)")
    print(s.text[:200])
```

**Key section keys:**

| key | Description |
|-----|-------------|
| `overview` | Business overview |
| `products` | Key products & services |
| `materials` | Raw materials & price changes |
| `sales` | Sales & order status |
| `risk` | Risk factors |
| `rnd` | R&D status |
| `financial` | Financial matters |
| `etc` | Other reference items |

---

### c.docs.mdna — MD&A

Management's discussion and analysis.

```python
c.docs.mdna   # Business overview text
```

---

### c.docs.overview — Company Overview

Quantitative data including founding date, address, credit ratings, etc. Returns a Result object.

```python
result = c.docs.overview

result.founded          # Founding year
result.address          # Location
result.homepage         # Website
result.subsidiaryCount  # Number of subsidiaries
result.isSME            # Whether SME
result.isVenture        # Whether venture company
result.listedDate       # Listing date
```

Check credit ratings:

```python
for cr in result.creditRatings:
    print(f"{cr.agency}: {cr.grade}")
```

Check parsing status:

```python
print(f"Not in original: {result.missing}")
print(f"Parse failed: {result.failed}")
```

---

### c.docs.rawMaterial — Raw Materials/Equipment

Raw material procurement, tangible assets, and capital expenditure status. Returns a Result object.

```python
result = c.docs.rawMaterial

result.materials     # list[RawMaterial] — Raw material list
result.equipment     # Equipment — Tangible asset status
result.capexItems    # list[CapexItem] — Capital expenditure items
```

**Usage example:**

```python
result = c.rawMaterial
for m in result.materials:
    print(f"{m.item}: {m.amount}백만원 ({m.ratio}%) — {m.supplier}")

eq = result.equipment
print(f"합계: {eq.total}, CAPEX: {eq.capex}")
```

---

## K-IFRS Notes

Access via `c.notes`. See the Notes section in [API Overview](./overview) for details.

### 12 Key Items

```python
c.notes.inventory          # Inventory DataFrame
c.notes.receivables        # Trade receivables
c.notes.borrowings         # Borrowings
c.notes.tangibleAsset      # Tangible asset movement schedule
c.notes.intangibleAsset    # Intangible assets
c.notes.provisions         # Provisions
c.notes.eps                # Earnings per share
c.notes.lease              # Leases
c.notes.investmentProperty # Investment property
c.notes.affiliates         # Associates
c.notes.segments           # Segment information
c.notes.costByNature       # Expenses by nature
```

### Korean Key Access

```python
c.notes["재고자산"]         # Same as c.notes.inventory
```

### Tangible Asset Movement Schedule

```python
result = c.notes.tangibleAsset
result.reliability    # "high" or "low"
result.warnings       # Reliability warnings
result.movementDf     # Category-level opening/closing time series
```

### Segment Information

```python
result = c.notes.segments
result.revenue   # Segment revenue time series DataFrame
for year, tables in result.tables.items():
    for t in tables:
        print(f"[{year}] {t.tableType}: {t.columns}")
```

### Expenses by Nature

```python
result = c.notes.costByNature
result.timeSeries    # Expense item time series
result.ratios        # Composition ratios
result.crossCheck    # Cross-check results
```

### Direct Lookup by Unregistered Keyword

```python
c.notes.detail("법인세")       # NotesDetail result
c.notes.detail("법인세").tableDf

c.notes.detail("특수관계자")
c.notes.detail("특수관계자").tableDf
```

All 23 keywords: `재고자산`, `주당이익`, `충당부채`, `차입금`, `매출채권`, `리스`, `투자부동산`, `무형자산`, `법인세`, `특수관계자`, `약정사항`, `금융자산`, `공정가치`, `이익잉여금`, `금융부채`, `기타포괄손익`, `사채`, `종업원급여`, `퇴직급여`, `확정급여`, `재무위험`, `우발부채`, `담보`
