"""EDGAR 태그 → DART canonical snakeId 매핑.

매핑 파이프라인:
1. STMT_OVERRIDES (stmt 기반 충돌 해결, 예: NetIncomeLoss → IS/CF 분리)
2. commonTags (standardAccounts.json, 344개 태그 → 179개 snakeId)
3. learnedSynonyms (tagMappings, 11,375개 태그)
4. EDGAR→DART alias 변환 (L0 SNAKEID_ALIASES 참조)

commonTags는 learnedSynonyms보다 우선한다.
"""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Optional

from dartlab.core.finance.labels import SNAKEID_ALIASES

_DATA_DIR = Path(__file__).parent / "mapperData"

# L0 통합 dict를 그대로 사용 — 하위 호환
EDGAR_TO_DART_ALIASES = SNAKEID_ALIASES

STMT_OVERRIDES: dict[tuple[str, str], str] = {
    ("NetIncomeLoss", "IS"): "net_profit",
    ("NetIncomeLoss", "CF"): "net_income_cf",
}


class EdgarMapper:
    """EDGAR XBRL 태그를 DART canonical snakeId로 변환하는 매퍼."""

    _tagMap: Optional[dict[str, str]] = None
    _stmtTagMap: Optional[dict[str, dict[str, str]]] = None
    _commonTags: Optional[set[str]] = None
    _accounts: Optional[list[dict]] = None
    _lock = threading.Lock()

    @classmethod
    def _ensureLoaded(cls):
        if cls._tagMap is not None:
            return
        with cls._lock:
            if cls._tagMap is not None:
                return
            cls._loadData()

    @classmethod
    def _loadData(cls):
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
        """태그가 standardAccounts의 commonTags에 포함되는지 확인."""
        cls._ensureLoaded()
        return tag.lower() in cls._commonTags

    @classmethod
    def map(cls, tag: str, stmtType: str = "") -> Optional[str]:
        """EDGAR 태그를 snakeId로 매핑하고, stmt 충돌 시 오버라이드 적용."""
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
        """EDGAR 태그를 DART 호환 snakeId로 변환 (alias 적용 포함)."""
        sid = cls.map(tag, stmtType)
        if sid is None:
            return None
        return EDGAR_TO_DART_ALIASES.get(sid, sid)

    @classmethod
    def classifyTagsByStmt(cls) -> dict[str, set[str]]:
        """재무제표 유형(IS/BS/CF/CI)별로 commonTags를 분류하여 반환."""
        cls._ensureLoaded()
        stmtTags: dict[str, set[str]] = {"IS": set(), "BS": set(), "CF": set(), "CI": set()}
        for acct in cls._accounts:
            stmt = acct["stmt"]
            if stmt in stmtTags:
                for tag in acct.get("commonTags", []):
                    stmtTags[stmt].add(tag)
        return stmtTags

    @classmethod
    def getTagsForSnakeIds(cls, snakeIds: list[str]) -> set[str]:
        """지정한 snakeId에 매핑된 모든 원본 태그를 반환."""
        cls._ensureLoaded()
        sidSet = set(snakeIds)
        # EDGAR_TO_DART_ALIASES 역방향 포함
        for edgarSid, dartSid in EDGAR_TO_DART_ALIASES.items():
            if dartSid in sidSet:
                sidSet.add(edgarSid)
        tags: set[str] = set()
        for acct in cls._accounts:
            if acct["snakeId"] in sidSet:
                for tag in acct.get("commonTags", []):
                    tags.add(tag)
        return tags
