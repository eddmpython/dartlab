"""
실험 ID: 003
실험명: 직원 현황 파서 개발 + 10종목 테스트

목적:
- "직원 등 현황" 테이블에서 핵심 지표 추출하는 파서 개발
- 합계 행에서 총 직원수, 평균근속, 연간급여, 1인평균급여 추출
- 성별 분리 데이터 추출

가설:
1. 10개 종목 모두 핵심 지표 추출 성공

방법:
1. "합 계" 행 찾아 셀 파싱
2. 성별합계 행 남/여 파싱
3. 평균근속연수 다양한 포맷 처리 (숫자, N년M개월)
4. 미등기임원 보수 테이블도 파싱

결과:

결론:

실험일: 2026-03-07
"""
import io
import re
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"

STOCKS = [
    "005930",
    "000660",
    "035420",
    "005380",
    "055550",
    "051910",
    "006400",
    "003550",
    "034020",
    "000270",
]


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip()
    isNegative = "\u25b3" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("\u25b3", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    val = float(cleaned)
    return -val if isNegative else val


def parseTenure(text: str) -> float | None:
    if not text or text.strip() in ("", "-"):
        return None
    s = text.strip()
    m = re.match(r"(\d+)\s*년\s*(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) + int(m.group(2)) / 12
    m = re.match(r"(\d+)\s*년", s)
    if m:
        return float(m.group(1))
    m = re.match(r"(\d+)\s*개월", s)
    if m:
        return int(m.group(1)) / 12
    val = parseAmount(s)
    if val is not None and 0 < val < 100:
        return val
    return None


def findEmployeeTableStart(content: str) -> int:
    markers = ["바. 직원", "마. 직원", "라. 직원", "다. 직원", "나. 직원"]
    for m in markers:
        idx = content.find(m)
        if idx >= 0:
            return idx

    idx = content.find("직원 등 현황")
    if idx >= 0:
        return idx

    idx = content.find("직원 등의 현황")
    if idx >= 0:
        realIdx = content.find("평균근속", idx)
        if realIdx >= 0:
            lineStart = content.rfind("\n", 0, realIdx)
            return lineStart if lineStart >= 0 else realIdx

    return -1


def parseEmployeeTable(content: str) -> dict:
    startIdx = findEmployeeTableStart(content)
    if startIdx < 0:
        return {}

    endIdx = len(content)
    for marker in ["육아지원", "미등기임원 보수", "임원의 보수", "교육훈련"]:
        eidx = content.find(marker, startIdx + 50)
        if 0 < eidx < endIdx:
            endIdx = eidx

    section = content[startIdx:endIdx]
    lines = section.split("\n")

    result = {
        "totalEmployees": None,
        "avgTenure": None,
        "totalSalary": None,
        "avgSalary": None,
        "maleEmployees": None,
        "femaleEmployees": None,
        "maleSalary": None,
        "femaleSalary": None,
        "maleAvgSalary": None,
        "femaleAvgSalary": None,
    }

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < 5:
            continue

        txt = " ".join(cells)

        if cells[0] in ("합 계", "합계") or (len(cells) > 1 and cells[1] in ("합 계", "합계")):
            if len(cells) >= 10:
                result["totalEmployees"] = parseAmount(cells[6])
                result["avgTenure"] = parseTenure(cells[7])
                if result["avgTenure"] is not None:
                    result["avgTenure"] = round(result["avgTenure"], 1)
                result["totalSalary"] = parseAmount(cells[8])
                result["avgSalary"] = parseAmount(cells[9])

        elif "성별합계" in txt or "성별 합계" in txt:
            gender = ""
            for c in cells:
                if "남" == c.strip():
                    gender = "male"
                elif "여" == c.strip():
                    gender = "female"

            if gender and len(cells) >= 10:
                employees = parseAmount(cells[6])
                salary = parseAmount(cells[8])
                avgPay = parseAmount(cells[9])
                if gender == "male":
                    result["maleEmployees"] = employees
                    result["maleSalary"] = salary
                    result["maleAvgSalary"] = avgPay
                else:
                    result["femaleEmployees"] = employees
                    result["femaleSalary"] = salary
                    result["femaleAvgSalary"] = avgPay

    execIdx = content.find("미등기임원 보수", startIdx)
    if execIdx < 0:
        execIdx = content.find("미등기임원보수", startIdx)
    if execIdx >= 0:
        execSection = content[execIdx:execIdx + 1000]
        for line in execSection.split("\n"):
            s = line.strip()
            if not s.startswith("|"):
                continue
            if "미등기임원" not in s:
                continue
            cells = [c.strip() for c in s.split("|")]
            cells = [c for c in cells if c]
            numCells = [parseAmount(c) for c in cells]
            nums = [n for n in numCells if n is not None and n > 0]
            if len(nums) >= 2:
                nums.sort(reverse=True)
                result["execTotalPay"] = nums[0]
                result["execCount"] = nums[1]
                if len(nums) >= 3 and nums[2] < 100000:
                    result["execAvgPay"] = nums[2]

    return result


def main():
    print("=" * 100)
    print("직원 현황 파서 10종목 테스트")
    print("=" * 100)

    totalTests = 0
    successTests = 0

    for code in STOCKS:
        path = DATA_DIR / f"{code}.parquet"
        if not path.exists():
            print(f"\n[{code}] 파일 없음")
            continue

        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)

        print(f"\n{'=' * 100}")
        print(f"[{code}] {corpName}")
        print(f"{'=' * 100}")

        for year in years[:3]:
            rows = df.filter(
                (pl.col("year") == year)
                & (
                    pl.col("section_title").str.contains("직원")
                    | pl.col("section_title").str.contains("임원")
                )
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                continue

            totalTests += 1
            content = rows["section_content"][0]
            parsed = parseEmployeeTable(content)

            hasEmployees = parsed.get("totalEmployees") is not None
            hasSalary = parsed.get("avgSalary") is not None
            status = "OK" if hasEmployees else "FAIL"
            if status == "OK":
                successTests += 1

            print(f"\n  {year} [{status}]")
            if parsed.get("totalEmployees"):
                print(f"    총 직원수: {parsed['totalEmployees']:,.0f}명")
            if parsed.get("avgTenure"):
                print(f"    평균근속: {parsed['avgTenure']}년")
            if parsed.get("totalSalary"):
                print(f"    연간급여총액: {parsed['totalSalary']:,.0f}백만원")
            if parsed.get("avgSalary"):
                print(f"    1인평균급여: {parsed['avgSalary']:,.0f}백만원")
            if parsed.get("maleEmployees"):
                print(f"    남: {parsed['maleEmployees']:,.0f}명, 여: {parsed.get('femaleEmployees', 0):,.0f}명")
            if parsed.get("execCount"):
                print(f"    미등기임원: {parsed['execCount']:,.0f}명, 평균: {parsed.get('execAvgPay', 0):,.0f}백만원")
            break

    print(f"\n{'=' * 100}")
    print(f"결과: {successTests}/{totalTests} 성공 ({successTests / totalTests * 100:.1f}%)")
    print(f"{'=' * 100}")


if __name__ == "__main__":
    main()
