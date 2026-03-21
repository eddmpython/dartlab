"""온톨로지 기반 계정 매퍼 - 컨텍스트 활용 매핑"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from owlready2 import *

from .ontologyBuilder import OntologyBuilder


@dataclass
class MappingResult:
    """매핑 결과"""

    snakeId: Optional[str]
    code: Optional[str]
    source: str
    confidence: float


class OntologyMapper:
    """온톨로지 기반 매퍼 (v7 StandardMapper 확장)"""

    def __init__(self, dataDir: Path = None):
        if dataDir is None:
            currentFile = Path(__file__).resolve()
            dataDir = currentFile.parent.parent

        self._dataDir = dataDir
        self._synonyms: Dict[str, str] = {}
        self._snakeToCode: Dict[str, str] = {}
        self.onto = None

        self._loadSynonyms()
        self._buildOntology()

    def _loadSynonyms(self):
        """learnedSynonyms.json 로드"""
        path = self._dataDir / "learnedSynonyms.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._synonyms = data.get("synonyms", {})

    def _buildOntology(self):
        """온톨로지 빌드"""
        builder = OntologyBuilder(self._dataDir)
        self.onto = builder.build()

        for acc in self.onto.Account.instances():
            if acc.snakeId and acc.code:
                self._snakeToCode[acc.snakeId] = acc.code

    def map(self, stdAccountNm: str) -> MappingResult:
        """기존 v7 호환 메서드 (컨텍스트 없이)"""
        return self.mapWithContext(stdAccountNm)

    def mapWithContext(
        self,
        accountName: str,
        industry: Optional[int] = None,
        statementKind: Optional[int] = None,
        allowFuzzy: bool = False,
    ) -> MappingResult:
        """컨텍스트 기반 매핑

        Args:
            accountName: 계정명
            industry: 산업코드 (0=전체, 1=제조업, 2=은행업...)
            statementKind: 재무제표종류 (1=BS, 2=IS, 4=CF, 20=공통)
            allowFuzzy: 유사 계정 검색 허용

        Returns:
            MappingResult
        """

        if not accountName:
            return MappingResult(None, None, "none", 0.0)

        normalized = accountName.replace(" ", "")

        if normalized in self._synonyms:
            snakeId = self._synonyms[normalized]

            if industry is None and statementKind is None:
                code = self._snakeToCode.get(snakeId)
                return MappingResult(snakeId, code, "synonym", 0.9)

            contextResult = self._searchWithContext(normalized, industry, statementKind, snakeId)
            if contextResult:
                return contextResult

            code = self._snakeToCode.get(snakeId)
            return MappingResult(snakeId, code, "synonym", 0.8)

        ontologyResult = self._searchOntology(normalized, industry, statementKind, allowFuzzy)
        if ontologyResult:
            return ontologyResult

        return MappingResult(None, None, "none", 0.0)

    def _searchWithContext(
        self, korName: str, industry: Optional[int], statementKind: Optional[int], expectedSnakeId: str
    ) -> Optional[MappingResult]:
        """동의어로 찾은 계정의 컨텍스트 검증"""

        candidates = []
        for acc in self.onto.Account.instances():
            if not acc.korName:
                continue

            name_match = any(korName in kn for kn in acc.korName)
            if not name_match:
                continue

            if not acc.snakeId or acc.snakeId != expectedSnakeId:
                continue

            if statementKind is not None and f"_stmt{statementKind}" not in acc.name:
                if "_stmt20" not in acc.name:
                    continue

            if industry is not None and f"_ind{industry}" not in acc.name:
                if "_ind0" not in acc.name:
                    continue

            score = 1.0

            if industry is not None:
                if f"_ind{industry}" in acc.name:
                    score += 0.2
                elif "_ind0" in acc.name:
                    score += 0.1

            if statementKind is not None:
                if f"_stmt{statementKind}" in acc.name:
                    score += 0.2
                elif "_stmt20" in acc.name:
                    score += 0.1

            candidates.append((acc, score))

        if candidates:
            candidates.sort(key=lambda x: -x[1])
            best_acc, best_score = candidates[0]
            snake_id = best_acc.snakeId
            code = best_acc.code if best_acc.code else None
            return MappingResult(snake_id, code, "synonym+context", best_score)

        return None

    def _searchOntology(
        self, korName: str, industry: Optional[int], statementKind: Optional[int], allowFuzzy: bool
    ) -> Optional[MappingResult]:
        """온톨로지 검색 (동의어 없을 때)"""

        candidates = []

        for acc in self.onto.Account.instances():
            if not acc.korName:
                continue

            exact_match = any(korName == kn for kn in acc.korName)
            fuzzy_match = allowFuzzy and any(korName in kn or kn in korName for kn in acc.korName)

            if exact_match:
                exact = True
            elif fuzzy_match:
                exact = False
            else:
                continue

            if statementKind is not None and f"_stmt{statementKind}" not in acc.name:
                if "_stmt20" not in acc.name:
                    continue

            if industry is not None and f"_ind{industry}" not in acc.name:
                if "_ind0" not in acc.name:
                    continue

            score = 1.0 if exact else 0.5

            if industry is not None:
                if f"_ind{industry}" in acc.name:
                    score += 0.2
                elif "_ind0" in acc.name:
                    score += 0.1

            if statementKind is not None:
                if f"_stmt{statementKind}" in acc.name:
                    score += 0.2
                elif "_stmt20" in acc.name:
                    score += 0.1

            candidates.append((acc, score))

        if not candidates:
            return None

        candidates.sort(key=lambda x: -x[1])
        best_acc, best_score = candidates[0]

        snake_id = best_acc.snakeId if best_acc.snakeId else None
        code = best_acc.code if best_acc.code else None
        source = "ontology" if best_score >= 1.0 else "fuzzy"

        return MappingResult(snake_id, code, source, best_score)

    def mapBatch(
        self, names: List[str], industry: Optional[int] = None, statementKind: Optional[int] = None
    ) -> Dict[str, MappingResult]:
        """일괄 매핑"""
        return {name: self.mapWithContext(name, industry, statementKind) for name in names}

    @property
    def synonymCount(self) -> int:
        """동의어 수"""
        return len(self._synonyms)

    @property
    def accountCount(self) -> int:
        """표준계정 수"""
        return len(list(self.onto.Account.instances()))
