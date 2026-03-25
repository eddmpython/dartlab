"""OpenDART 공통 상수 — 분기 코드, 카테고리 매핑."""

# 분기 → DART API 보고서 코드
QUARTER_TO_CODE: dict[str, str] = {
    "Q1": "11013",
    "Q2": "11012",
    "Q3": "11014",
    "Q4": "11011",
    "annual": "11011",
}

# DART API 코드 → 분기 라벨
CODE_TO_LABEL: dict[str, str] = {
    "11013": "Q1",
    "11012": "Q2",
    "11014": "Q3",
    "11011": "annual",
}

# DART API 코드 → 분기 (Q1-Q4)
CODE_TO_QUARTER: dict[str, str] = {
    "11013": "Q1",
    "11012": "Q2",
    "11014": "Q3",
    "11011": "Q4",
}

# DART API 코드 → 한글 분기명 (parquet 저장용)
CODE_TO_QUARTER_KR: dict[str, str] = {
    "11013": "1분기",
    "11012": "2분기",
    "11014": "3분기",
    "11011": "4분기",
}

# 한글 카테고리 → 영문 apiType
KR_TO_API_TYPE: dict[str, str] = {
    "증자감자": "capitalChange",
    "배당": "dividend",
    "자기주식": "treasuryStock",
    "최대주주": "majorHolder",
    "최대주주변동": "majorHolderChange",
    "소액주주": "minorityHolder",
    "임원": "executive",
    "직원": "employee",
    "이사회임원개인보수": "executivePayIndividual",
    "이사회임원전체보수": "executivePayAllTotal",
    "개인별보수": "topPay",
    "타법인출자": "investedCompany",
    "미등기임원보수": "unregisteredExecutivePay",
    "주식총수": "stockTotal",
    "회계감사인": "auditOpinion",
    "감사용역체결": "auditContract",
    "감사비감사계약": "nonAuditContract",
    "사외이사변동": "outsideDirector",
    "회사채미상환": "corporateBond",
    "단기사채미상환": "shortTermBond",
    "공모자금용도": "publicOfferingUsage",
    "공모자금사용": "privateOfferingUsage",
    "대주주지분변동": "majorShareholderChange",
    "기업어음미상환": "commercialPaper",
    "채무증권발행실적": "debtSecurities",
    "조건부자본증권미상환": "contingentCapital",
    "신종자본증권미상환": "hybridCapital",
    "이사감사보수총회인정": "executivePayApproval",
    "이사감사보수지급형태": "executivePayType",
}
