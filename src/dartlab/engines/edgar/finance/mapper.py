"""EDGAR 태그 → DART canonical snakeId 매핑.

매핑 파이프라인:
1. STMT_OVERRIDES (stmt 기반 충돌 해결, 예: NetIncomeLoss → IS/CF 분리)
2. commonTags (standardAccounts.json, 344개 태그 → 179개 snakeId)
3. learnedSynonyms (tagMappings, 11,375개 태그)
4. EDGAR→DART alias 변환 (13개)

commonTags는 learnedSynonyms보다 우선한다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).parent / "mapperData"

EDGAR_TO_DART_ALIASES: dict[str, str] = {
    "operating_cash_flow": "operating_cashflow",
    "investing_cash_flow": "investing_cashflow",
    "financing_cash_flow": "cash_flows_from_financing_activities",
    "noncurrent_assets": "noncurrent_assets",
    "noncurrent_liabilities": "noncurrent_liabilities",
    "cost_of_revenue": "cost_of_sales",
    "inventory": "inventories",
    "property_plant_equipment": "tangible_assets",
    "income_before_tax": "profit_before_tax",
    "short_term_debt": "shortterm_borrowings",
    "long_term_debt": "longterm_borrowings",
    "accounts_receivable": "trade_and_other_receivables",
    "noncontrolling_interest": "noncontrolling_interests_equity",
    "cash_and_equivalents": "cash_and_cash_equivalents",
    "total_equity": "owners_of_parent_equity",
    "equity_including_nci": "total_stockholders_equity",
    "equity_nci": "noncontrolling_interests_equity",
    "revenue": "sales",
    "operating_income": "operating_profit",
    "net_income": "net_profit",
    "income_tax_expense": "income_taxes",
    "basic_eps": "basic_earnings_per_share",
    "diluted_eps": "diluted_earnings_per_share",
    "ppe": "tangible_assets",
    "trade_receivables": "trade_and_other_receivables",
    "short_term_borrowings": "shortterm_borrowings",
    "long_term_borrowings": "longterm_borrowings",
    "bonds": "debentures",
    "non_current_assets": "noncurrent_assets",
    "non_current_liabilities": "noncurrent_liabilities",
    "finance_cost": "finance_costs",
    "interest_expense": "finance_costs",
    "interest_income": "finance_income",
    "financing_cashflow": "cash_flows_from_financing_activities",
    "other_equity_components": "other_equity",
    "issued_capital": "paidin_capital",
    "selling_general_admin": "selling_and_administrative_expenses",
    "capex": "purchase_of_property_plant_and_equipment",
    "accounts_payable": "trade_and_other_payables",
}

STMT_OVERRIDES: dict[tuple[str, str], str] = {
    ("NetIncomeLoss", "IS"): "net_profit",
    ("NetIncomeLoss", "CF"): "net_income_cf",
}


class EdgarMapper:
    _tagMap: Optional[dict[str, str]] = None
    _stmtTagMap: Optional[dict[str, dict[str, str]]] = None
    _commonTags: Optional[set[str]] = None
    _accounts: Optional[list[dict]] = None

    @classmethod
    def _ensureLoaded(cls):
        if cls._tagMap is not None:
            return

        stdPath = _DATA_DIR / "standardAccounts.json"
        with open(stdPath, encoding="utf-8") as f:
            stdData = json.load(f)

        cls._accounts = stdData["accounts"]

        cls._stmtTagMap = {}
        cls._commonTags = set()
        commonTagMap: dict[str, str] = {}
        for acct in cls._accounts:
            sid = acct["snakeId"]
            stmt = acct["stmt"]
            for tag in acct.get("commonTags", []):
                tagLower = tag.lower()
                commonTagMap[tagLower] = sid
                cls._commonTags.add(tagLower)
                cls._stmtTagMap.setdefault(tagLower, {})[stmt] = sid

        learnedPath = _DATA_DIR / "learnedSynonyms.json"
        with open(learnedPath, encoding="utf-8") as f:
            learnedData = json.load(f)

        cls._tagMap = {}
        for tag, sid in learnedData.get("tagMappings", {}).items():
            cls._tagMap[tag.lower()] = sid

        for tag, sid in commonTagMap.items():
            cls._tagMap[tag] = sid

    @classmethod
    def isCommonTag(cls, tag: str) -> bool:
        cls._ensureLoaded()
        return tag.lower() in cls._commonTags

    @classmethod
    def map(cls, tag: str, stmtType: str = "") -> Optional[str]:
        cls._ensureLoaded()

        overrideKey = (tag, stmtType)
        if overrideKey in STMT_OVERRIDES:
            return STMT_OVERRIDES[overrideKey]

        tagLower = tag.lower()

        if stmtType and tagLower in cls._stmtTagMap:
            stmtMap = cls._stmtTagMap[tagLower]
            if stmtType in stmtMap:
                return stmtMap[stmtType]

        return cls._tagMap.get(tagLower)

    @classmethod
    def mapToDart(cls, tag: str, stmtType: str = "") -> Optional[str]:
        sid = cls.map(tag, stmtType)
        if sid is None:
            return None
        return EDGAR_TO_DART_ALIASES.get(sid, sid)

    @classmethod
    def classifyTagsByStmt(cls) -> dict[str, set[str]]:
        cls._ensureLoaded()
        stmtTags: dict[str, set[str]] = {"IS": set(), "BS": set(), "CF": set(), "CI": set()}
        for acct in cls._accounts:
            stmt = acct["stmt"]
            if stmt in stmtTags:
                for tag in acct.get("commonTags", []):
                    stmtTags[stmt].add(tag)
        return stmtTags
