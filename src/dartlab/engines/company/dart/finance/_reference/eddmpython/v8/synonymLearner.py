"""자동 발전형 동의어 학습 시스템

종목 분석 → 미매칭 수집 → 후보 제안 → 학습 사이클
"""

import json
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Tuple

import polars as pl


@dataclass
class AnalysisResult:
    """종목 분석 결과"""

    stockCode: str
    corpName: str
    totalAccounts: int
    matchedStandard: int
    matchedSynonym: int
    unmatched: List[str]

    @property
    def matchRate(self) -> float:
        if self.totalAccounts == 0:
            return 0.0
        return (self.matchedStandard + self.matchedSynonym) / self.totalAccounts * 100

    @property
    def unmatchedCount(self) -> int:
        return len(self.unmatched)


@dataclass
class MappingSuggestion:
    """매핑 후보 제안"""

    stdAccountNm: str
    candidateSnakeId: str
    candidateKorName: str
    similarity: float
    frequency: int = 0  # 해당 계정의 사용 빈도


@dataclass
class LearningReport:
    """학습 리포트"""

    analyzedCompanies: int
    totalUnmatched: int
    uniqueUnmatched: int
    suggestionsGenerated: int
    synonymsLearned: int
    newMatchRate: float = 0.0


class SynonymLearner:
    """자동 발전형 동의어 학습 시스템"""

    def __init__(self, dataDir: Path = None):
        if dataDir is None:
            # v7 모듈 기준 상대 경로: finance/ 루트
            currentFile = Path(__file__).resolve()
            dataDir = currentFile.parent.parent

        self._dataDir = dataDir
        self._synonymsPath = dataDir / "learnedSynonyms.json"

        # 표준계정 로드
        self._korToSnake: Dict[str, str] = {}
        self._snakeToKor: Dict[str, str] = {}
        self._loadStandardAccounts()

        # 기존 동의어 로드
        self._synonyms: Dict[str, str] = {}
        self._loadSynonyms()

        # v6 FinanceSearch (lazy load)
        self._fs = None

    def _loadStandardAccounts(self):
        """standardAccounts.json 로드"""
        path = self._dataDir / "standardAccounts.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for acc in data.get("accounts", []):
            korName = acc.get("korName", "").replace(" ", "")
            snakeId = acc.get("snakeId", "")
            if korName and snakeId:
                if korName not in self._korToSnake:
                    self._korToSnake[korName] = snakeId
                if snakeId not in self._snakeToKor:
                    self._snakeToKor[snakeId] = korName

    def _loadSynonyms(self):
        """learnedSynonyms.json 로드"""
        if not self._synonymsPath.exists():
            return

        with open(self._synonymsPath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self._synonyms = data.get("synonyms", {})

    def _saveSynonyms(self):
        """learnedSynonyms.json 저장"""
        data = {
            "_metadata": {
                "version": "1.2",
                "description": "v6 stdAccountNm → standardAccounts snakeId 동의어 매핑",
                "totalSynonyms": len(self._synonyms),
            },
            "synonyms": self._synonyms,
        }

        with open(self._synonymsPath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _getFinanceSearch(self):
        """v6 FinanceSearch 인스턴스 (lazy load)"""
        if self._fs is None:
            from core.dart.searchDart.finance.v8.search import FinanceSearch

            self._fs = FinanceSearch()
        return self._fs

    def _isMatched(self, stdAccountNm: str) -> Tuple[bool, str]:
        """계정명이 매핑 가능한지 확인

        Returns:
            (매핑여부, 소스: 'standard'|'synonym'|'none')
        """
        normalized = stdAccountNm.replace(" ", "")

        if normalized in self._korToSnake:
            return True, "standard"
        if normalized in self._synonyms:
            return True, "synonym"
        return False, "none"

    def analyzeCompany(self, stockCode: str) -> AnalysisResult:
        """종목 매칭률 분석

        Args:
            stockCode: 종목코드 (예: '005930')

        Returns:
            AnalysisResult
        """
        fs = self._getFinanceSearch()

        # 종목 데이터 조회
        df = (
            fs.lf.filter(pl.col("stock_code") == stockCode)
            .select(["corp_name", "stdAccountNm"])
            .unique(["stdAccountNm"])
            .collect()
        )

        if df.is_empty():
            return AnalysisResult(
                stockCode=stockCode,
                corpName="",
                totalAccounts=0,
                matchedStandard=0,
                matchedSynonym=0,
                unmatched=[],
            )

        corpName = df["corp_name"][0] if df["corp_name"][0] else ""
        accounts = df["stdAccountNm"].to_list()

        matchedStd = 0
        matchedSyn = 0
        unmatched = []

        for nm in accounts:
            if nm is None:
                continue
            matched, source = self._isMatched(nm)
            if matched:
                if source == "standard":
                    matchedStd += 1
                else:
                    matchedSyn += 1
            else:
                unmatched.append(nm)

        return AnalysisResult(
            stockCode=stockCode,
            corpName=corpName,
            totalAccounts=len([a for a in accounts if a]),
            matchedStandard=matchedStd,
            matchedSynonym=matchedSyn,
            unmatched=unmatched,
        )

    def suggestMappings(
        self, unmatchedNames: List[str], similarityThreshold: float = 0.6, limit: int = 5
    ) -> List[MappingSuggestion]:
        """미매칭 계정에 대한 매핑 후보 제안

        Args:
            unmatchedNames: 미매칭 계정명 리스트
            similarityThreshold: 최소 유사도 (0.0 ~ 1.0)
            limit: 계정당 최대 후보 수

        Returns:
            MappingSuggestion 리스트
        """
        suggestions = []

        for name in unmatchedNames:
            normalized = name.replace(" ", "").lower()
            candidates = []

            # 표준계정 한글명과 유사도 계산
            for korName, snakeId in self._korToSnake.items():
                korLower = korName.lower()
                similarity = SequenceMatcher(None, normalized, korLower).ratio()

                if similarity >= similarityThreshold:
                    candidates.append((snakeId, korName, similarity))

            # 유사도 높은 순 정렬
            candidates.sort(key=lambda x: x[2], reverse=True)

            for snakeId, korName, similarity in candidates[:limit]:
                suggestions.append(
                    MappingSuggestion(
                        stdAccountNm=name,
                        candidateSnakeId=snakeId,
                        candidateKorName=korName,
                        similarity=similarity,
                    )
                )

        return suggestions

    def learnSynonym(self, stdAccountNm: str, snakeId: str) -> bool:
        """동의어 학습 (learnedSynonyms.json에 추가)

        Args:
            stdAccountNm: v6 정규화된 계정명
            snakeId: 표준계정 snakeId

        Returns:
            성공 여부
        """
        normalized = stdAccountNm.replace(" ", "")

        # 이미 표준계정에 있으면 추가 불필요
        if normalized in self._korToSnake:
            return False

        # 유효한 snakeId인지 확인
        if snakeId not in self._snakeToKor:
            return False

        self._synonyms[normalized] = snakeId
        self._saveSynonyms()
        return True

    def learnBatch(self, mappings: Dict[str, str]) -> int:
        """일괄 동의어 학습

        Args:
            mappings: {stdAccountNm: snakeId} 딕셔너리

        Returns:
            학습된 동의어 수
        """
        learned = 0
        for stdAccountNm, snakeId in mappings.items():
            if self.learnSynonym(stdAccountNm, snakeId):
                learned += 1
        return learned

    def autoLearn(
        self, stockCodes: List[str], autoApproveThreshold: float = 0.95, verbose: bool = True
    ) -> LearningReport:
        """자동 학습 (높은 유사도 매핑 자동 승인)

        Args:
            stockCodes: 분석할 종목 리스트
            autoApproveThreshold: 자동 승인 유사도 임계값
            verbose: 진행 상황 출력

        Returns:
            LearningReport
        """
        allUnmatched = []
        analyzedCount = 0

        for stockCode in stockCodes:
            result = self.analyzeCompany(stockCode)
            allUnmatched.extend(result.unmatched)
            analyzedCount += 1

            if verbose:
                print(f"[{result.corpName}] 매칭률: {result.matchRate:.1f}%")

        # 중복 제거 및 빈도 계산
        unmatchedFreq = {}
        for name in allUnmatched:
            unmatchedFreq[name] = unmatchedFreq.get(name, 0) + 1

        uniqueUnmatched = list(unmatchedFreq.keys())

        # 후보 제안
        suggestions = self.suggestMappings(uniqueUnmatched, similarityThreshold=autoApproveThreshold)

        # 자동 승인
        learned = 0
        for suggestion in suggestions:
            if suggestion.similarity >= autoApproveThreshold:
                if self.learnSynonym(suggestion.stdAccountNm, suggestion.candidateSnakeId):
                    learned += 1
                    if verbose:
                        print(
                            f"  학습: {suggestion.stdAccountNm} → {suggestion.candidateSnakeId} ({suggestion.similarity:.0%})"
                        )

        return LearningReport(
            analyzedCompanies=analyzedCount,
            totalUnmatched=len(allUnmatched),
            uniqueUnmatched=len(uniqueUnmatched),
            suggestionsGenerated=len(suggestions),
            synonymsLearned=learned,
        )

    def getUnmatchedStats(self, stockCodes: List[str] = None, limit: int = 50) -> List[Tuple[str, int]]:
        """미매칭 계정 빈도 통계

        Args:
            stockCodes: 분석할 종목 (None이면 전체)
            limit: 최대 결과 수

        Returns:
            [(계정명, 빈도)] 리스트 (빈도순 정렬)
        """
        fs = self._getFinanceSearch()

        if stockCodes:
            lf = fs.lf.filter(pl.col("stock_code").is_in(stockCodes))
        else:
            lf = fs.lf

        # 계정명별 빈도
        df = lf.group_by("stdAccountNm").agg(pl.len().alias("cnt")).sort("cnt", descending=True).collect()

        results = []
        for row in df.iter_rows(named=True):
            nm = row["stdAccountNm"]
            if nm is None:
                continue
            matched, _ = self._isMatched(nm)
            if not matched:
                results.append((nm, row["cnt"]))
                if len(results) >= limit:
                    break

        return results

    def exportUnmatched(self, outputPath: Path = None, limit: int = 200) -> Path:
        """미매칭 계정 리스트 내보내기 (수동 검토용)

        Args:
            outputPath: 출력 파일 경로
            limit: 최대 개수

        Returns:
            출력 파일 경로
        """
        if outputPath is None:
            outputPath = self._dataDir / "unmatchedAccounts.json"

        stats = self.getUnmatchedStats(limit=limit)

        # 후보 제안 포함
        data = {
            "_metadata": {
                "description": "미매칭 계정 리스트 (수동 검토용)",
                "totalUnmatched": len(stats),
            },
            "accounts": [],
        }

        for name, freq in stats:
            suggestions = self.suggestMappings([name], similarityThreshold=0.5, limit=3)
            candidates = [
                {"snakeId": s.candidateSnakeId, "korName": s.candidateKorName, "similarity": round(s.similarity, 2)}
                for s in suggestions
            ]

            data["accounts"].append(
                {
                    "stdAccountNm": name,
                    "frequency": freq,
                    "candidates": candidates,
                    "approved": None,  # 수동 검토 후 snakeId 입력
                }
            )

        with open(outputPath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return outputPath

    def importApproved(self, inputPath: Path = None) -> int:
        """수동 승인된 매핑 가져오기

        Args:
            inputPath: 입력 파일 경로 (unmatchedAccounts.json)

        Returns:
            학습된 동의어 수
        """
        if inputPath is None:
            inputPath = self._dataDir / "unmatchedAccounts.json"

        if not inputPath.exists():
            return 0

        with open(inputPath, "r", encoding="utf-8") as f:
            data = json.load(f)

        learned = 0
        for acc in data.get("accounts", []):
            approved = acc.get("approved")
            if approved:
                if self.learnSynonym(acc["stdAccountNm"], approved):
                    learned += 1

        return learned

    @property
    def synonymCount(self) -> int:
        """현재 동의어 수"""
        return len(self._synonyms)

    @property
    def standardCount(self) -> int:
        """표준계정 수"""
        return len(self._korToSnake)
