"""
EDGAR 표준계정 매핑 시스템

표준계정(standardAccounts.json) + 학습된 동의어(learnedSynonyms.json)를 사용하여
XBRL 태그/라벨을 표준 snakeId로 매핑
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz


@dataclass
class MappingResult:
    snakeId: str | None
    code: str | None
    korName: str | None
    engName: str | None
    level: int
    line: int
    parent: str | None
    source: str
    confidence: float


class StandardMapper:
    def __init__(self):
        self.baseDir = Path(__file__).parent.parent
        self.standardAccounts = self._loadStandardAccounts()
        self.learnedSynonyms = self._loadLearnedSynonyms()
        self._tagIndex = self._buildTagIndex()
        self._snakeIdIndex = self._buildSnakeIdIndex()
        self._mapCache = {}

    def _loadStandardAccounts(self) -> dict:
        filePath = self.baseDir / "standardAccounts.json"
        with open(filePath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _loadLearnedSynonyms(self) -> dict:
        filePath = self.baseDir / "learnedSynonyms.json"
        with open(filePath, "r", encoding="utf-8") as f:
            return json.load(f)

    def _buildTagIndex(self) -> dict:
        index = {}
        for account in self.standardAccounts.get("accounts", []):
            for tag in account.get("commonTags", []):
                tagLower = tag.lower()
                if tagLower not in index:
                    index[tagLower] = []
                index[tagLower].append(account)
        return index

    def _buildSnakeIdIndex(self) -> dict:
        index = {}
        for account in self.standardAccounts.get("accounts", []):
            snakeId = account.get("snakeId")
            if snakeId:
                index[snakeId] = account
        return index

    def _normalizeText(self, text: str) -> str:
        if not text:
            return ""
        text = text.lower().strip()
        text = re.sub(r"[&]", " and ", text)
        text = re.sub(r"[-_]", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _splitCamelCase(self, text: str) -> str:
        if not text:
            return ""
        split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
        split = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", split)
        return split

    def _tokenize(self, text: str) -> set:
        if not text:
            return set()

        normalized = self._normalizeText(self._splitCamelCase(text))
        stopWords = {
            "a",
            "an",
            "and",
            "or",
            "of",
            "the",
            "in",
            "on",
            "at",
            "to",
            "for",
            "with",
            "by",
            "from",
            "as",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "net",
            "total",
            "other",
        }

        tokens = re.findall(r"[a-z]+", normalized)
        filtered = {tok for tok in tokens if tok not in stopWords and len(tok) > 2}
        return filtered

    def _calculateTokenScore(self, sourceTokens: set, targetTokens: set) -> float:
        if not sourceTokens or not targetTokens:
            return 0.0

        intersection = sourceTokens & targetTokens
        union = sourceTokens | targetTokens

        jaccardScore = len(intersection) / len(union) if union else 0
        overlapScore = len(intersection) / len(sourceTokens) if sourceTokens else 0

        return jaccardScore * 0.6 + overlapScore * 0.4

    def mapByTag(self, tag: str, stmt: str = None) -> MappingResult | None:
        tagLower = tag.lower()

        if tagLower in self._tagIndex:
            matches = self._tagIndex[tagLower]
            if stmt:
                stmtMatches = [m for m in matches if m.get("stmt") == stmt]
                if stmtMatches:
                    matches = stmtMatches

            if matches:
                account = matches[0]
                return MappingResult(
                    snakeId=account.get("snakeId"),
                    code=account.get("code"),
                    korName=account.get("korName"),
                    engName=account.get("engName"),
                    level=account.get("level", 2),
                    line=account.get("line", 100),
                    parent=account.get("parent"),
                    source="standard_tag",
                    confidence=1.0,
                )

        tagMappings = self.learnedSynonyms.get("tagMappings", {})
        if tagLower in tagMappings:
            snakeId = tagMappings[tagLower]
            account = self._snakeIdIndex.get(snakeId)
            if account:
                return MappingResult(
                    snakeId=snakeId,
                    code=account.get("code"),
                    korName=account.get("korName"),
                    engName=account.get("engName"),
                    level=account.get("level", 2),
                    line=account.get("line", 100),
                    parent=account.get("parent"),
                    source="learned_tag",
                    confidence=0.9,
                )

        return None

    def mapByPlabel(self, plabel: str, stmt: str = None) -> MappingResult | None:
        plabelLower = self._normalizeText(plabel)

        plabelMappings = self.learnedSynonyms.get("plabelMappings", {})
        if plabelLower in plabelMappings:
            snakeId = plabelMappings[plabelLower]
            account = self._snakeIdIndex.get(snakeId)
            if account:
                return MappingResult(
                    snakeId=snakeId,
                    code=account.get("code"),
                    korName=account.get("korName"),
                    engName=account.get("engName"),
                    level=account.get("level", 2),
                    line=account.get("line", 100),
                    parent=account.get("parent"),
                    source="learned_plabel",
                    confidence=0.85,
                )

        return None

    def mapByFuzzy(self, text: str, stmt: str = None, threshold: float = 0.7) -> MappingResult | None:
        accounts = self.standardAccounts.get("accounts", [])
        if stmt:
            accounts = [a for a in accounts if a.get("stmt") == stmt]

        if not accounts:
            return None

        textNorm = self._normalizeText(self._splitCamelCase(text))
        textTokens = self._tokenize(text)

        bestMatch = None
        bestScore = 0.0

        for account in accounts:
            engName = account.get("engName", "")
            engNorm = self._normalizeText(engName)

            fuzzyScore = fuzz.token_set_ratio(textNorm, engNorm) / 100.0

            engTokens = self._tokenize(engName)
            tokenScore = self._calculateTokenScore(textTokens, engTokens)

            combinedScore = fuzzyScore * 0.6 + tokenScore * 0.4

            if combinedScore > bestScore:
                bestScore = combinedScore
                bestMatch = account

        if bestScore >= threshold and bestMatch:
            return MappingResult(
                snakeId=bestMatch.get("snakeId"),
                code=bestMatch.get("code"),
                korName=bestMatch.get("korName"),
                engName=bestMatch.get("engName"),
                level=bestMatch.get("level", 2),
                line=bestMatch.get("line", 100),
                parent=bestMatch.get("parent"),
                source="fuzzy",
                confidence=bestScore,
            )

        return None

    def map(self, tag: str, plabel: str = None, stmt: str = None) -> MappingResult:
        cacheKey = (tag, plabel, stmt)
        if cacheKey in self._mapCache:
            return self._mapCache[cacheKey]

        result = self.mapByTag(tag, stmt)
        if result:
            self._mapCache[cacheKey] = result
            return result

        if plabel:
            result = self.mapByPlabel(plabel, stmt)
            if result:
                self._mapCache[cacheKey] = result
                return result

        combinedText = f"{self._splitCamelCase(tag)} {plabel or ''}"
        result = self.mapByFuzzy(combinedText, stmt, threshold=0.65)
        if result:
            self._mapCache[cacheKey] = result
            return result

        unmapped = MappingResult(
            snakeId=None,
            code=None,
            korName=None,
            engName=None,
            level=2,
            line=999,
            parent=None,
            source="unmapped",
            confidence=0.0,
        )
        self._mapCache[cacheKey] = unmapped
        return unmapped

    def getAccountBySnakeId(self, snakeId: str) -> dict | None:
        return self._snakeIdIndex.get(snakeId)

    def getAllAccounts(self, stmt: str = None) -> list:
        accounts = self.standardAccounts.get("accounts", [])
        if stmt:
            accounts = [a for a in accounts if a.get("stmt") == stmt]
        return accounts
