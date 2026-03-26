"""표준계정코드 매핑 모듈

standardAccounts.json과 learnedSynonyms.json을 사용하여
v6 정규화된 계정명(stdAccountNm)을 표준계정 ID(snakeId)로 매핑
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class StandardAccount:
    """표준계정 정보"""

    code: str
    korName: str
    engName: str
    snakeId: str
    industry: int = 0
    codeType: str = "M"
    statementKind: int = 0


@dataclass
class MappingResult:
    """매핑 결과"""

    snakeId: Optional[str]
    code: Optional[str]
    source: str  # 'standard', 'synonym', 'none'
    confidence: float  # 0.0 ~ 1.0


class StandardMapper:
    """표준계정코드 매핑 클래스"""

    def __init__(self, dataDir: Path = None):
        if dataDir is None:
            # v7 모듈 기준 상대 경로: finance/ 루트
            currentFile = Path(__file__).resolve()
            dataDir = currentFile.parent.parent

        self._dataDir = dataDir
        self._korToStandard: Dict[str, StandardAccount] = {}
        self._synonyms: Dict[str, str] = {}
        self._snakeToStandard: Dict[str, StandardAccount] = {}

        self._loadStandardAccounts()
        self._loadLearnedSynonyms()

    def _loadStandardAccounts(self):
        """standardAccounts.json 로드"""
        path = self._dataDir / "standardAccounts.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for acc in data.get("accounts", []):
            stdAcc = StandardAccount(
                code=acc.get("code", ""),
                korName=acc.get("korName", ""),
                engName=acc.get("engName", ""),
                snakeId=acc.get("snakeId", ""),
                industry=acc.get("industry", 0),
                codeType=acc.get("codeType", "M"),
                statementKind=acc.get("statementKind", 0),
            )

            # korName 정규화 (공백 제거)
            korNormalized = stdAcc.korName.replace(" ", "")
            if korNormalized and korNormalized not in self._korToStandard:
                self._korToStandard[korNormalized] = stdAcc

            # snakeId 역매핑
            if stdAcc.snakeId and stdAcc.snakeId not in self._snakeToStandard:
                self._snakeToStandard[stdAcc.snakeId] = stdAcc

    def _loadLearnedSynonyms(self):
        """learnedSynonyms.json 로드"""
        path = self._dataDir / "learnedSynonyms.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._synonyms = data.get("synonyms", {})

    def reload(self):
        """매핑 데이터 리로드"""
        self._korToStandard.clear()
        self._synonyms.clear()
        self._snakeToStandard.clear()
        self._loadStandardAccounts()
        self._loadLearnedSynonyms()

    def map(self, stdAccountNm: str) -> MappingResult:
        """v6 정규화된 계정명 → 표준계정 매핑

        Args:
            stdAccountNm: v6 정규화된 계정명

        Returns:
            MappingResult (snakeId, code, source, confidence)
        """
        if not stdAccountNm:
            return MappingResult(None, None, "none", 0.0)

        # 정규화 (공백 제거)
        normalized = stdAccountNm.replace(" ", "")

        # 1. standardAccounts 직접 매칭
        if normalized in self._korToStandard:
            acc = self._korToStandard[normalized]
            return MappingResult(acc.snakeId, acc.code, "standard", 1.0)

        # 2. learnedSynonyms 매칭
        if normalized in self._synonyms:
            snakeId = self._synonyms[normalized]
            acc = self._snakeToStandard.get(snakeId)
            code = acc.code if acc else None
            return MappingResult(snakeId, code, "synonym", 0.9)

        # 3. 매칭 실패
        return MappingResult(None, None, "none", 0.0)

    def mapBatch(self, names: List[str]) -> Dict[str, MappingResult]:
        """일괄 매핑

        Args:
            names: 계정명 리스트

        Returns:
            {계정명: MappingResult} 딕셔너리
        """
        return {name: self.map(name) for name in names}

    def getStandardBySnakeId(self, snakeId: str) -> Optional[StandardAccount]:
        """snakeId로 표준계정 조회"""
        return self._snakeToStandard.get(snakeId)

    def getStandardByKorName(self, korName: str) -> Optional[StandardAccount]:
        """한글명으로 표준계정 조회"""
        normalized = korName.replace(" ", "")
        return self._korToStandard.get(normalized)

    def searchStandard(self, query: str, limit: int = 10) -> List[StandardAccount]:
        """표준계정 검색 (부분 매칭)

        Args:
            query: 검색어
            limit: 최대 결과 수

        Returns:
            매칭된 StandardAccount 리스트
        """
        results = []
        queryLower = query.lower()

        for korName, acc in self._korToStandard.items():
            if query in korName or queryLower in acc.snakeId.lower():
                results.append(acc)
                if len(results) >= limit:
                    break

        return results

    @property
    def standardCount(self) -> int:
        """표준계정 수"""
        return len(self._korToStandard)

    @property
    def synonymCount(self) -> int:
        """동의어 수"""
        return len(self._synonyms)

    def getStats(self) -> Dict:
        """통계 정보"""
        return {
            "standardAccounts": self.standardCount,
            "learnedSynonyms": self.synonymCount,
            "totalMappable": self.standardCount + self.synonymCount,
        }
