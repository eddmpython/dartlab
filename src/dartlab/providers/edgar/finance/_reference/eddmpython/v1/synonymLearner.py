"""
EDGAR 동의어 학습 시스템

미매핑된 XBRL 태그/라벨을 분석하고 표준계정으로의 매핑을 학습
DART의 synonymLearner와 동일한 패턴
"""

import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from core.edgar.searchEdgar.finance.v1.standardMapping import StandardMapper
from rapidfuzz import fuzz


class SynonymLearner:
    def __init__(self):
        self.baseDir = Path(__file__).parent.parent
        self.synonymsFile = self.baseDir / "learnedSynonyms.json"
        self.mapper = StandardMapper()
        self._synonyms = self._loadSynonyms()

    def _loadSynonyms(self) -> dict:
        if self.synonymsFile.exists():
            with open(self.synonymsFile, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "_metadata": {
                "version": "1.0.0",
                "description": "학습된 XBRL 태그/라벨 → 표준계정 매핑",
                "lastUpdated": None,
                "totalMappings": 0,
            },
            "tagMappings": {},
            "plabelMappings": {},
        }

    def saveSynonyms(self):
        self._synonyms["_metadata"]["lastUpdated"] = datetime.now().isoformat()
        tagCount = len(self._synonyms.get("tagMappings", {}))
        plabelCount = len(self._synonyms.get("plabelMappings", {}))
        self._synonyms["_metadata"]["totalMappings"] = tagCount + plabelCount

        with open(self.synonymsFile, "w", encoding="utf-8") as f:
            json.dump(self._synonyms, f, ensure_ascii=False, indent=2)

        print(f"Saved {tagCount} tag mappings and {plabelCount} plabel mappings")

    def addTagMapping(self, tag: str, snakeId: str) -> bool:
        account = self.mapper.getAccountBySnakeId(snakeId)
        if not account:
            print(f"Invalid snakeId: {snakeId}")
            return False

        tagLower = tag.lower()
        self._synonyms["tagMappings"][tagLower] = snakeId
        return True

    def addPlabelMapping(self, plabel: str, snakeId: str) -> bool:
        account = self.mapper.getAccountBySnakeId(snakeId)
        if not account:
            print(f"Invalid snakeId: {snakeId}")
            return False

        plabelLower = self.mapper._normalizeText(plabel)
        self._synonyms["plabelMappings"][plabelLower] = snakeId
        return True

    def removeTagMapping(self, tag: str) -> bool:
        tagLower = tag.lower()
        if tagLower in self._synonyms["tagMappings"]:
            del self._synonyms["tagMappings"][tagLower]
            return True
        return False

    def removePlabelMapping(self, plabel: str) -> bool:
        plabelLower = self.mapper._normalizeText(plabel)
        if plabelLower in self._synonyms["plabelMappings"]:
            del self._synonyms["plabelMappings"][plabelLower]
            return True
        return False

    def suggestMapping(self, text: str, stmt: str = None, topN: int = 5) -> list:
        accounts = self.mapper.getAllAccounts(stmt)

        textNorm = self.mapper._normalizeText(self.mapper._splitCamelCase(text))

        candidates = []
        for account in accounts:
            engName = account.get("engName", "")
            engNorm = self.mapper._normalizeText(engName)

            score = fuzz.token_set_ratio(textNorm, engNorm)

            candidates.append(
                {
                    "snakeId": account.get("snakeId"),
                    "engName": engName,
                    "korName": account.get("korName"),
                    "score": score,
                }
            )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:topN]

    def analyzeUnmapped(self, factsData: list) -> dict:
        unmapped = []
        mapped = []

        for fact in factsData:
            tag = fact.get("tag", "")
            plabel = fact.get("plabel", "")
            stmt = fact.get("stmt", "")

            result = self.mapper.map(tag, plabel, stmt)

            if result.source == "unmapped":
                unmapped.append(
                    {
                        "tag": tag,
                        "plabel": plabel,
                        "stmt": stmt,
                        "suggestions": self.suggestMapping(f"{tag} {plabel}", stmt, topN=3),
                    }
                )
            else:
                mapped.append(
                    {
                        "tag": tag,
                        "plabel": plabel,
                        "snakeId": result.snakeId,
                        "source": result.source,
                        "confidence": result.confidence,
                    }
                )

        tagCounts = Counter(item["tag"] for item in unmapped)
        topUnmappedTags = tagCounts.most_common(20)

        return {
            "totalFacts": len(factsData),
            "mappedCount": len(mapped),
            "unmappedCount": len(unmapped),
            "coverageRate": len(mapped) / len(factsData) * 100 if factsData else 0,
            "topUnmappedTags": topUnmappedTags,
            "unmappedSamples": unmapped[:50],
            "mappedSamples": mapped[:20],
        }

    def learnFromAnalysis(self, analysis: dict, minConfidence: float = 0.7) -> int:
        learned = 0

        for item in analysis.get("unmappedSamples", []):
            tag = item.get("tag", "")
            suggestions = item.get("suggestions", [])

            if suggestions and suggestions[0]["score"] >= minConfidence * 100:
                bestMatch = suggestions[0]
                if self.addTagMapping(tag, bestMatch["snakeId"]):
                    learned += 1
                    print(f"Learned: {tag} → {bestMatch['snakeId']} (score: {bestMatch['score']})")

        if learned > 0:
            self.saveSynonyms()

        return learned

    def getCoverage(self) -> dict:
        tagCount = len(self._synonyms.get("tagMappings", {}))
        plabelCount = len(self._synonyms.get("plabelMappings", {}))
        standardCount = len(self.mapper.getAllAccounts())

        return {
            "standardAccounts": standardCount,
            "learnedTagMappings": tagCount,
            "learnedPlabelMappings": plabelCount,
            "totalMappings": tagCount + plabelCount,
            "lastUpdated": self._synonyms.get("_metadata", {}).get("lastUpdated"),
        }

    def exportMappings(self) -> dict:
        return {
            "tagMappings": self._synonyms.get("tagMappings", {}),
            "plabelMappings": self._synonyms.get("plabelMappings", {}),
        }

    def importMappings(self, mappings: dict, merge: bool = True):
        if merge:
            self._synonyms["tagMappings"].update(mappings.get("tagMappings", {}))
            self._synonyms["plabelMappings"].update(mappings.get("plabelMappings", {}))
        else:
            self._synonyms["tagMappings"] = mappings.get("tagMappings", {})
            self._synonyms["plabelMappings"] = mappings.get("plabelMappings", {})

        self.saveSynonyms()
