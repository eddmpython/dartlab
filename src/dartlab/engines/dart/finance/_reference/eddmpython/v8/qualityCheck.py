"""매핑 품질 점검 및 데이터 표준화 검증

실제 DART 데이터로:
1. 매핑률 분석
2. Confidence 분포
3. 미매핑 계정 리스트
4. 표준화 품질 점검
"""

import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from collections import Counter, defaultdict
from typing import Dict, List, Tuple

import polars as pl
from core.dart.searchDart.finance.v8 import ParquetMapper
from core.paths import DART_DATA_DIR


class MappingQualityChecker:
    """매핑 품질 점검기"""

    def __init__(self):
        self.mapper = ParquetMapper()
        self.financeDir = DART_DATA_DIR / "finance"

    def run(self, maxCompanies: int = 10):
        """품질 점검 실행"""

        print("=" * 90)
        print("매핑 품질 점검 및 데이터 표준화 검증")
        print("=" * 90)
        print()

        print("ParquetMapper 초기화 완료")
        print(f"  - 동의어: {self.mapper.synonymCount:,}개")
        print(f"  - 표준계정: {self.mapper.accountCount:,}개")
        print()

        allAccounts = self._loadAccounts(maxCompanies)
        if not allAccounts:
            print("❌ DART 데이터가 없습니다.")
            return

        print("=" * 90)
        print("1. 매핑률 분석")
        print("=" * 90)
        print()

        self._analyzeMappingRate(allAccounts)

        print()
        print("=" * 90)
        print("2. Confidence 분포")
        print("=" * 90)
        print()

        self._analyzeConfidence(allAccounts)

        print()
        print("=" * 90)
        print("3. 미매핑 계정 상위 20개")
        print("=" * 90)
        print()

        self._analyzeUnmapped(allAccounts)

        print()
        print("=" * 90)
        print("4. 표준화 품질 점검 (재무제표별)")
        print("=" * 90)
        print()

        self._analyzeStandardization(allAccounts)

        print()
        print("=" * 90)
        print("5. 재무제표별 매핑률")
        print("=" * 90)
        print()

        self._analyzeByStatement(allAccounts)

        print()
        print("=" * 90)
        print("6. 종합 평가")
        print("=" * 90)
        print()

        self._summarize(allAccounts)

    def _loadAccounts(self, maxCompanies: int) -> Dict[str, List[Tuple[str, str]]]:
        """DART 데이터에서 계정명 로드

        Returns:
            {재무제표종류: [(계정명, 빈도), ...]}
        """

        if not self.financeDir.exists():
            return {}

        parquetFiles = list(self.financeDir.glob("*.parquet"))[:maxCompanies]
        print(f"데이터 로딩 중... ({len(parquetFiles)}개 회사)")

        accountsByStatement = defaultdict(lambda: defaultdict(int))

        for filepath in parquetFiles:
            try:
                df = pl.read_parquet(filepath)
                if "account_nm" not in df.columns or "sj_div" not in df.columns:
                    continue

                for row in df.select(["sj_div", "account_nm"]).unique().iter_rows(named=True):
                    sjDiv = row.get("sj_div", "")
                    accountNm = row.get("account_nm", "")
                    if sjDiv and accountNm:
                        accountsByStatement[sjDiv][accountNm] += 1

            except Exception as e:
                continue

        result = {}
        for sjDiv, accounts in accountsByStatement.items():
            sorted_accounts = sorted(accounts.items(), key=lambda x: -x[1])
            result[sjDiv] = sorted_accounts

        totalUnique = sum(len(accounts) for accounts in accountsByStatement.values())
        print(f"✅ 로딩 완료: 총 {totalUnique:,}개 고유 계정")
        print()

        return result

    def _analyzeMappingRate(self, allAccounts: Dict):
        """매핑률 분석"""

        totalAccounts = 0
        mappedAccounts = 0
        highConfidence = 0
        mediumConfidence = 0
        lowConfidence = 0

        for sjDiv, accounts in allAccounts.items():
            for accountNm, freq in accounts:
                totalAccounts += 1

                statementKind = {"BS": 1, "IS": 2, "CIS": 2, "CF": 4, "SCE": 8}.get(sjDiv)
                result = self.mapper.mapWithContext(accountNm, statementKind=statementKind, allowFuzzy=True)

                if result.snakeId:
                    mappedAccounts += 1

                    if result.confidence >= 1.0:
                        highConfidence += 1
                    elif result.confidence >= 0.7:
                        mediumConfidence += 1
                    else:
                        lowConfidence += 1

        mappingRate = (mappedAccounts / totalAccounts * 100) if totalAccounts > 0 else 0

        print(f"총 고유 계정: {totalAccounts:,}개")
        print(f"매핑 성공: {mappedAccounts:,}개 ({mappingRate:.1f}%)")
        print(f"미매핑: {totalAccounts - mappedAccounts:,}개 ({100 - mappingRate:.1f}%)")
        print()

        print("신뢰도 분포:")
        print(f"  높음 (≥1.0): {highConfidence:,}개 ({highConfidence / totalAccounts * 100:.1f}%)")
        print(f"  중간 (≥0.7): {mediumConfidence:,}개 ({mediumConfidence / totalAccounts * 100:.1f}%)")
        print(f"  낮음 (<0.7): {lowConfidence:,}개 ({lowConfidence / totalAccounts * 100:.1f}%)")

    def _analyzeConfidence(self, allAccounts: Dict):
        """Confidence 분포 분석"""

        confidenceDistribution = Counter()

        for sjDiv, accounts in allAccounts.items():
            statementKind = {"BS": 1, "IS": 2, "CIS": 2, "CF": 4, "SCE": 8}.get(sjDiv)

            for accountNm, freq in accounts[:100]:
                result = self.mapper.mapWithContext(accountNm, statementKind=statementKind, allowFuzzy=True)

                if result.snakeId:
                    confBucket = int(result.confidence * 10) / 10
                    confidenceDistribution[confBucket] += 1

        print("Confidence 분포 (상위 100개 계정):")
        for conf in sorted(confidenceDistribution.keys(), reverse=True):
            count = confidenceDistribution[conf]
            bar = "█" * int(count / 2)
            print(f"  {conf:.1f}: {bar} {count}개")

    def _analyzeUnmapped(self, allAccounts: Dict):
        """미매핑 계정 분석"""

        unmappedAccounts = []

        for sjDiv, accounts in allAccounts.items():
            statementKind = {"BS": 1, "IS": 2, "CIS": 2, "CF": 4, "SCE": 8}.get(sjDiv)

            for accountNm, freq in accounts:
                result = self.mapper.mapWithContext(accountNm, statementKind=statementKind, allowFuzzy=True)

                if not result.snakeId:
                    unmappedAccounts.append((accountNm, freq, sjDiv))

        unmappedAccounts.sort(key=lambda x: -x[1])

        if not unmappedAccounts:
            print("✅ 모든 계정 매핑 성공!")
            return

        print(f"총 {len(unmappedAccounts):,}개 미매핑 계정\n")
        print(f"{'순위':<5} {'빈도':<6} {'재무제표':<10} {'계정명'}")
        print("-" * 90)

        for i, (accountNm, freq, sjDiv) in enumerate(unmappedAccounts[:20], 1):
            print(f"{i:<5} {freq:<6} {sjDiv:<10} {accountNm}")

    def _analyzeStandardization(self, allAccounts: Dict):
        """표준화 품질 점검 - 같은 개념이 다른 이름으로 표현되는지"""

        print("대표 계정의 변형 검사:\n")

        testGroups = [
            ("매출액", ["매출", "수익(매출액)", "영업수익", "매출액(수익)"]),
            ("당기순이익", ["순이익", "당기순이익(손실)", "당기순손실"]),
            ("영업이익", ["영업이익(손실)", "영업손익", "영업손실"]),
            ("자산총계", ["총자산", "자산합계"]),
        ]

        for baseAccount, variants in testGroups:
            print(f"[{baseAccount}]")

            results = {}
            for account in [baseAccount] + variants:
                result = self.mapper.mapWithContext(account, allowFuzzy=True)
                results[account] = result.snakeId or "NONE"

            baseSnakeId = results[baseAccount]

            unified = 0
            for variant in variants:
                if results[variant] == baseSnakeId:
                    print(f"  ✅ '{variant}' → {results[variant]}")
                    unified += 1
                else:
                    print(f"  ❌ '{variant}' → {results[variant]} (불일치)")

            unificationRate = (unified / len(variants) * 100) if variants else 0
            print(f"  통일률: {unified}/{len(variants)} ({unificationRate:.0f}%)")
            print()

    def _analyzeByStatement(self, allAccounts: Dict):
        """재무제표별 매핑률"""

        statementNames = {
            "BS": "재무상태표",
            "IS": "손익계산서",
            "CIS": "포괄손익계산서",
            "CF": "현금흐름표",
            "SCE": "자본변동표",
        }

        print(f"{'재무제표':<15} {'총 계정':<10} {'매핑':<10} {'매핑률'}")
        print("-" * 60)

        for sjDiv in ["BS", "IS", "CIS", "CF", "SCE"]:
            if sjDiv not in allAccounts:
                continue

            accounts = allAccounts[sjDiv]
            total = len(accounts)
            mapped = 0

            statementKind = {"BS": 1, "IS": 2, "CIS": 2, "CF": 4, "SCE": 8}.get(sjDiv)

            for accountNm, freq in accounts:
                result = self.mapper.mapWithContext(accountNm, statementKind=statementKind, allowFuzzy=True)
                if result.snakeId:
                    mapped += 1

            mappingRate = (mapped / total * 100) if total > 0 else 0
            stmtName = statementNames.get(sjDiv, sjDiv)

            print(f"{stmtName:<15} {total:<10} {mapped:<10} {mappingRate:.1f}%")

    def _summarize(self, allAccounts: Dict):
        """종합 평가"""

        totalUnique = sum(len(accounts) for accounts in allAccounts.values())
        totalMapped = 0
        highConf = 0

        for sjDiv, accounts in allAccounts.items():
            statementKind = {"BS": 1, "IS": 2, "CIS": 2, "CF": 4, "SCE": 8}.get(sjDiv)

            for accountNm, freq in accounts:
                result = self.mapper.mapWithContext(accountNm, statementKind=statementKind, allowFuzzy=True)

                if result.snakeId:
                    totalMapped += 1
                    if result.confidence >= 1.0:
                        highConf += 1

        mappingRate = (totalMapped / totalUnique * 100) if totalUnique > 0 else 0
        highConfRate = (highConf / totalUnique * 100) if totalUnique > 0 else 0

        print("📊 종합 점수")
        print()
        print(f"매핑률: {mappingRate:.1f}%")
        if mappingRate >= 95:
            print("  ✅ 우수 (≥95%)")
        elif mappingRate >= 90:
            print("  ✅ 양호 (≥90%)")
        elif mappingRate >= 80:
            print("  ⚠️  보통 (≥80%)")
        else:
            print("  ❌ 개선 필요 (<80%)")

        print()
        print(f"고신뢰도 매핑률: {highConfRate:.1f}%")
        if highConfRate >= 80:
            print("  ✅ 우수 (≥80%)")
        elif highConfRate >= 70:
            print("  ✅ 양호 (≥70%)")
        else:
            print("  ⚠️  개선 여지 있음")

        print()
        print("💡 권장사항:")
        if mappingRate < 95:
            print("  - 미매핑 계정을 learnedSynonyms.json에 추가 고려")
        if highConfRate < 80:
            print("  - 낮은 신뢰도 계정 검토 필요")

        print()
        print("✅ ParquetMapper 품질 검증 완료!")


def main():
    checker = MappingQualityChecker()
    checker.run(maxCompanies=10)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ 에러 발생: {e}")
        import traceback

        traceback.print_exc()
