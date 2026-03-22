"""
실험 ID: 008b
실험명: 미매핑 태그 학습 (008 Phase 4)

목적:
- Phase 3에서 스캔된 S&P 100 미매핑 태그 중 빈도 높은 것을 학습
- 기존 standardAccounts의 level=2/3 snakeId로 매핑
- 합산계정(level=1)에는 절대 매핑하지 않음 (008에서 제거한 오류 반복 방지)

결과 (2026-03-10):
- 68개 태그 추가, 1개 업데이트 (derivativeAssets: other_noncurrent_assets → derivative_assets_detail)
- 2개 블로킹 (IncomeLoss...Foreign/Domestic → income_before_tax는 level=1)
- 매핑률: 87.2% → 92.1% (+4.9%p)
- 주요 학습 항목: OCI 세부항목(40+), ROU Asset/Liability(6), CF세부(10), BS세부(12)

실험일: 2026-03-10
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_MAPPER_DATA = Path(__file__).resolve().parents[2] / "mapperData"

NEW_TAG_MAPPINGS = {
    "depreciation": "depreciation_amortization",
    "employeerelatedliabilitiescurrent": "accrued_expenses",
    "otheraccruedliabilitiescurrent": "other_current_liabilities",
    "stockholdersequityother": "accumulated_other_comprehensive_income",
    "preferredstockvalue": "common_stock",
    "derivativeliabilities": "derivative_liabilities_detail",
    "derivativeassets": "derivative_assets_detail",
    "equitysecuritieswithoutreadilydeterminablefairvalueamount": "long_term_investments",
    "contractwithcustomerliabilityrevenuerecognized": "deferred_revenue_current",
    "rightofuseassetobtainedinexchangeforoperatingleaseliability": "operating_lease_rou_asset",
    "rightofuseassetobtainedinexchangeforfinanceleaseliability": "property_plant_equipment",
    "financeleaserightofu seassetamortization": "depreciation_cf",
    "financeleaserightofuseassetamortization": "depreciation_cf",
    "proceedsfromdivestitureofbusinesses": "investment_sales",
    "proceedsfromsaleofpropertyplantandequipment": "investment_sales",
    "proceedsfromsaleandmaturityofavailableforsalesecurities": "investment_sales",
    "paymentstoacquiremarketablesecurities": "investment_purchases",
    "increasedecreaseinaccruedincometaxespayable": "working_capital_changes",
    "increasedecreaseInaccountsPayableandaccruedliabilities": "working_capital_changes",
    "increasedecreaseinaccountspayableandaccruedliabilities": "working_capital_changes",
    "capitalexpendituresincurredbutnotyetpaid": "capex",
    "interestcostscapitalized": "capex",
    "stockrepurchasedduringperiodvalue": "stock_repurchase",
    "stockrepurchasedandretiredduringperiodvalue": "stock_repurchase",
    "stockissuedduringperiodvaluenewissues": "stock_issuance",
    "stockissuedduringperiodvalueacquisitions": "stock_issuance",
    "incomelossfromcontinuingoperationsbeforeincometaxesforeign": "income_before_tax",
    "incomelossfromcontinuingoperationsbeforeincometaxesdomestic": "income_before_tax",
    "preferredstocksharesauthorized": "common_stock",
    "preferredstocksharesissued": "common_stock",
    "preferredstocksharesoutstanding": "common_stock",
    "preferredstockparorstalkedvaluepershare": "common_stock",
    "preferredstockparorstalkedvaluepershare": "common_stock",
    "adjustmentstoadditionalpaidi ncapitalsharebasedcompensationrequisiteserviceperiodrecognitionvalue": "additional_paid_in_capital",
    "adjustmentstoadditionalpaidi ncapitaltaxeffectfromsharebasedcompensation": "additional_paid_in_capital",
    "adjustmentstoadditionalpaidiNcapitalsharebasedcompensationrequisiteserviceperiodrecognitionvalue": "additional_paid_in_capital",
    "adjustmentstoadditionalpaidiNcapitaltaxeffectfromsharebasedcompensation": "additional_paid_in_capital",
    "financeleaseinterestpaymentonliability": "interest_expense",
    "othercomprehensiveincomeforeigncurrencytransactionandtranslationadjustmentnetoftaxperiodincreasedecrease": "foreign_currency_translation",
    "othercomprehensiveincomelosspensi onandotherpostretirementbenefitplansadjustmentnetoftax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeuNrealizedgainlossonderivativesarisingduringperiodnetoftax": "derivative_hedge_oci",
    "othercomprehensiveincomelosspensionandotherpostretirementbenefitplansadjustmentnetoftax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeunrealizedgainlossonderivativesarisingduringperiodnetoftax": "derivative_hedge_oci",
    "othercomprehensiveincomedefinedbenefitplansadjustmentnetoftaxperiodincreasedecrease": "other_comprehensive_income_detail",
    "othercomprehensiveincomeavailableforsalesecuritiesadjustmentnetoftaxperiodincreasedecrease": "securities_valuation_oci",
    "othercomprehensiveincomederivativesqualifyingashedgesnetoftaxperiodincreasedecrease": "derivative_hedge_oci",
    "reclassificationfromaccumulatedothercomprehensiveincomecurrentperiodnetoftax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelosstax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeunrealizedholdingGainlossonSecuritiesarisingduringperiodtax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeunrealizedholdingGainLossonsecuritiesarisingduringperiodtax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossbeforereclassificationsnetoftax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossforeigncurrencytranslationadjustmenttax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossderivativesqualifyingashedgestax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelosspensionandotherpostretirementbenefitplanstax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeforeigncurrencytransactionandtranslationgainlossarisingduringperiodnetoftax": "foreign_currency_translation",
    "othercomprehensiveincomelossreclassificationadjustmentfromaocionderivativesnetoftax": "derivative_hedge_oci",
    "othercomprehensiveincomereclassificationadjustmentonderivativesincludedinnetincomenetoftax": "derivative_hedge_oci",
    "othercomprehensiveincomelossreclassificationadjustmentfromaociforsaleofsecuritiesnetoftax": "securities_valuation_oci",
    "othercomprehensiveincomelosscashflowhedgegainlossafterreclassificationandtax": "derivative_hedge_oci",
    "othercomprehensiveincomelossreclassificationadjustmentforsaleofsecuritiesincludedinnetincomenetoftax": "securities_valuation_oci",
    "othercomprehensiveincomeunrealizedgainlossonderivativesarisingduringperiodtax": "other_comprehensive_income_detail",
    "othercomprehensiveincomeunrealizedgainlossonderivativesarisingduringperiodbeforetax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossreclassificationadjustmentfromaocionderivativestax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossavailableforsalesecuritiestax": "other_comprehensive_income_detail",
    "othercomprehensiveincomereclassificationadjustmentonderivativesincludedinnetincometax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelossreclassificationadjustmentfromaociforsaleofsecuritiestax": "other_comprehensive_income_detail",
    "othercomprehensiveincomereclassificationadjustononderivativesincludedinnetincometax": "other_comprehensive_income_detail",
    "othercomprehensiveincomedefinedbenefitplanstax": "other_comprehensive_income_detail",
    "othercomprehensiveincomelosscashflowhedgegainlossbeforereclassificationaftertax": "derivative_hedge_oci",
    "othercomprehensiveincomelosscashflowhedgegainlossreclassificationaftertax": "derivative_hedge_oci",
    "accumulatedothercomprehensiveincomelossforeigncurrencytranslationadjustmentnetoftax": "accumulated_other_comprehensive_income",
    "accumulatedothercomprehensiveincomelosscumulativechangesinnetgainlossfromcashflowhedgeseffectnetoftax": "accumulated_other_comprehensive_income",
    "accumulatedothercomprehensiveincomelossdefinedbenefitpensionandotherpostretirementplansnetoftax": "accumulated_other_comprehensive_income",
    "accumulatedothercomprehensiveincomelossavailableforsalesecuritiesadjustmentnetoftax": "accumulated_other_comprehensive_income",
    "liabilitiesofdisposalgroupincludingdiscontinuedoperationcurrent": "other_current_liabilities",
    "revenueremainingperformanceobligation": "deferred_revenue_current",
    "adjustmentsnoncashitemstoreconcilenetincomelosstocashprovidedbyusedinoperatingactivitiesother": "other_noncash_items",
    "minorityinterestdecreasefromdistributionstononcontrollinginterestholders": "dividends_paid",
    "minorityinterestdecreasefromredemptions": "stock_repurchase",
}


def cleanMappings(mappings: dict[str, str]) -> dict[str, str]:
    """키를 정규화하고 공백 오타 제거"""
    cleaned = {}
    for tag, sid in mappings.items():
        tagClean = tag.lower().replace(" ", "")
        if tagClean:
            cleaned[tagClean] = sid
    return cleaned


def loadLearnedSynonyms():
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def saveLearnedSynonyms(data):
    path = _MAPPER_DATA / "learnedSynonyms.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  saved: {path}")


def loadStandardAccountSnakeIds() -> set[str]:
    path = _MAPPER_DATA / "standardAccounts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {acct["snakeId"] for acct in data["accounts"]}


def getLevel1SnakeIds() -> set[str]:
    path = _MAPPER_DATA / "standardAccounts.json"
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return {acct["snakeId"] for acct in data["accounts"] if acct["level"] == 1}


if __name__ == "__main__":
    print("=" * 70)
    print("008b: 미매핑 태그 학습")
    print("=" * 70)

    newMappings = cleanMappings(NEW_TAG_MAPPINGS)
    validSnakeIds = loadStandardAccountSnakeIds()
    level1Ids = getLevel1SnakeIds()

    invalid = []
    blocked = []
    for tag, sid in newMappings.items():
        if sid not in validSnakeIds:
            invalid.append((tag, sid))
        if sid in level1Ids:
            blocked.append((tag, sid))

    if invalid:
        print(f"\n  WARNING: {len(invalid)}개 태그의 snakeId가 standardAccounts에 없음:")
        for tag, sid in invalid:
            print(f"    {tag} → {sid}")

    if blocked:
        print(f"\n  BLOCKED: {len(blocked)}개 태그가 level=1 합산계정으로 매핑 시도:")
        for tag, sid in blocked:
            print(f"    {tag} → {sid}")
        for tag, _ in blocked:
            del newMappings[tag]
        print(f"  → {len(blocked)}개 제거됨")

    learned = loadLearnedSynonyms()
    tagMappings = learned["tagMappings"]
    before = len(tagMappings)

    added = 0
    updated = 0
    for tag, sid in newMappings.items():
        if sid not in validSnakeIds:
            continue
        if tag not in tagMappings:
            tagMappings[tag] = sid
            added += 1
        elif tagMappings[tag] != sid:
            print(f"  update: {tag}: {tagMappings[tag]} → {sid}")
            tagMappings[tag] = sid
            updated += 1

    after = len(tagMappings)
    print(f"\n  before: {before}")
    print(f"  added: {added}")
    print(f"  updated: {updated}")
    print(f"  after: {after}")

    learned["tagMappings"] = tagMappings
    learned["_metadata"]["totalMappings"] = after
    saveLearnedSynonyms(learned)

    print("\n  완료.")
