"""
YTD (Year-To-Date) 데이터 처리 유틸리티
"""

import json
from pathlib import Path
from typing import Dict, List, Set


class YTDProcessor:
    """YTD 종목 관리 및 자동 감지"""

    def __init__(self):
        self.configPath = Path(__file__).parent / "ytdTickers.json"
        self.ytdTickers: Set[str] = set()
        self.suspectedTickers: Set[str] = set()
        self._loadConfig()

    def _loadConfig(self):
        """YTD 종목 설정 로드"""
        if self.configPath.exists():
            with open(self.configPath, "r", encoding="utf-8") as f:
                config = json.load(f)
                self.ytdTickers = set(config.get("ytdOnlyTickers", []))
                self.suspectedTickers = set(config.get("suspectedYtdTickers", []))

    def isYTDTicker(self, ticker: str) -> bool:
        """YTD 종목인지 확인"""
        return ticker.upper() in self.ytdTickers

    def isSuspectedYTD(self, ticker: str) -> bool:
        """YTD 의심 종목인지 확인"""
        return ticker.upper() in self.suspectedTickers

    def addYTDTicker(self, ticker: str, note: str = ""):
        """YTD 종목 추가"""
        self.ytdTickers.add(ticker.upper())
        self._saveConfig(note)

    def _saveConfig(self, note: str = ""):
        """설정 저장"""
        if self.configPath.exists():
            with open(self.configPath, "r", encoding="utf-8") as f:
                config = json.load(f)
        else:
            config = {
                "version": "1.0",
                "lastUpdate": "",
                "description": "",
                "ytdOnlyTickers": [],
                "suspectedYtdTickers": [],
                "notes": {},
            }

        config["ytdOnlyTickers"] = sorted(list(self.ytdTickers))
        config["suspectedYtdTickers"] = sorted(list(self.suspectedTickers))

        from datetime import datetime

        config["lastUpdate"] = datetime.now().strftime("%Y-%m-%d")

        with open(self.configPath, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

    @staticmethod
    def detectYTDPattern(periods: List[str], values: List[float]) -> Dict[str, bool]:
        """
        YTD 패턴 자동 감지

        Returns:
            {'q2_is_ytd': bool, 'q3_is_ytd': bool}
        """
        result = {"q2_is_ytd": False, "q3_is_ytd": False}

        # 같은 연도 데이터만 추출
        year_data = {}
        for i, period in enumerate(periods):
            if values[i] is None:
                continue

            if "-Q" in period and not period.endswith("-Q4"):
                year = period.split("-")[0]
                quarter = period.split("-")[1]

                if year not in year_data:
                    year_data[year] = {}

                year_data[year][quarter] = values[i]

        # 각 연도별로 YTD 패턴 확인
        for year, quarters in year_data.items():
            q1 = quarters.get("Q1")
            q2 = quarters.get("Q2")
            q3 = quarters.get("Q3")

            # Q2 YTD 판정: Q2 > Q1 * 1.7 (보수적 임계값)
            if q1 and q2 and q2 > q1 * 1.7:
                result["q2_is_ytd"] = True

            # Q3 YTD 판정: Q3 > Q2 * 1.4 (이미 Q2가 개별이면)
            # 또는 Q3 > Q1 * 2.5 (Q2가 YTD이면)
            if q1 and q3:
                if q2:
                    if result["q2_is_ytd"]:
                        # Q2가 YTD이면, Q3도 YTD일 가능성
                        if q3 > q2 * 1.3:
                            result["q3_is_ytd"] = True
                    else:
                        # Q2가 개별이면, Q3 > Q2 * 1.7
                        if q3 > q2 * 1.7:
                            result["q3_is_ytd"] = True
                else:
                    # Q2가 없으면 Q1과 비교
                    if q3 > q1 * 2.5:
                        result["q3_is_ytd"] = True

        return result

    @staticmethod
    def deaccumulateYTD(
        periods: List[str], values: List[float], q2_is_ytd: bool = False, q3_is_ytd: bool = False
    ) -> List[float]:
        """
        YTD 누적 값을 개별 분기 값으로 역산

        Args:
            periods: 기간 목록 ['2023-Q1', '2023-Q2', ...]
            values: 값 목록 [100, 220, 350, ...]
            q2_is_ytd: Q2가 YTD인지
            q3_is_ytd: Q3가 YTD인지

        Returns:
            개별 분기 값 [100, 120, 130, ...]
        """
        result = [v for v in values]

        # 연도별로 처리
        year_indices = {}
        for i, period in enumerate(periods):
            if values[i] is None:
                continue

            if "-Q" in period:
                year = period.split("-")[0]
                quarter = period.split("-")[1]

                if year not in year_indices:
                    year_indices[year] = {}

                year_indices[year][quarter] = i

        # 각 연도별로 YTD 역산
        for year, quarters in year_indices.items():
            q1_idx = quarters.get("Q1")
            q2_idx = quarters.get("Q2")
            q3_idx = quarters.get("Q3")

            q1_val = values[q1_idx] if q1_idx is not None else None
            q2_val = values[q2_idx] if q2_idx is not None else None
            q3_val = values[q3_idx] if q3_idx is not None else None

            # Q2 역산
            if q2_is_ytd and q1_val and q2_val and q2_idx is not None:
                result[q2_idx] = q2_val - q1_val

            # Q3 역산
            if q3_is_ytd and q3_val and q3_idx is not None:
                if q2_is_ytd:
                    # Q2도 YTD이면: Q3(개별) = Q3(YTD) - Q2(YTD)
                    if q2_val:
                        result[q3_idx] = q3_val - q2_val
                else:
                    # Q2가 개별이면: Q3(개별) = Q3(YTD) - Q1 - Q2(개별)
                    if q1_val and q2_val:
                        result[q3_idx] = q3_val - q1_val - q2_val
                    elif q1_val:
                        result[q3_idx] = q3_val - q1_val

        return result


# 싱글톤 인스턴스
_ytd_processor = None


def getYTDProcessor() -> YTDProcessor:
    """YTDProcessor 싱글톤 인스턴스 반환"""
    global _ytd_processor
    if _ytd_processor is None:
        _ytd_processor = YTDProcessor()
    return _ytd_processor
