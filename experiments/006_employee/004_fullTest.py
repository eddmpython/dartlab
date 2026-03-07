"""
실험 ID: 004
실험명: 전체 종목 직원 현황 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 직원 현황 파서 적용
- 성공/실패/데이터없음 통계 수집

가설:
1. 사업보고서 보유 종목 90% 이상 파싱 성공

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 직원 현황 파싱
3. 성공/실패 분류
4. 실패 케이스 상세 기록

결과:

결론:

실험일: 2026-03-07
"""
import re
import sys
import io
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import polars as pl

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "docsData"


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


def _tryExtract(cells, empIdx, tenureIdx, salaryIdx, avgIdx):
    """지정 인덱스로 추출 시도. salary 없어도 emp만 있으면 성공."""
    if empIdx >= len(cells):
        return None
    emp = parseAmount(cells[empIdx])
    if emp is None or emp < 1:
        return None
    result = {"totalEmployees": emp}
    if tenureIdx < len(cells):
        tenure = parseTenure(cells[tenureIdx])
        if tenure is not None:
            result["avgTenure"] = round(tenure, 1)
    if salaryIdx < len(cells):
        salary = parseAmount(cells[salaryIdx])
        if salary is not None and salary >= emp:
            result["totalSalary"] = salary
    if avgIdx < len(cells):
        avg = parseAmount(cells[avgIdx])
        if avg is not None:
            result["avgSalary"] = avg
    return result


def parseEmployeeTable(content: str) -> dict:
    lines = content.split("\n")

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]

        isTotal = cells[0] in ("합 계", "합계")
        if not isTotal:
            continue
        if len(cells) < 4:
            continue

        # 표준 구조: cells[6]=emp, [7]=tenure, [8]=salary, [9]=avg
        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        # shifted 구조: cells[5]=emp, [6]=tenure, [7]=salary, [8]=avg
        if len(cells) >= 9:
            r = _tryExtract(cells, 5, 6, 7, 8)
            if r and r.get("totalSalary"):
                return r

        # 유비씨형: cells[2]=emp, [7]=tenure, [8]=salary, [9]=avg
        if len(cells) >= 10:
            r = _tryExtract(cells, 2, 7, 8, 9)
            if r and r.get("totalSalary"):
                return r

        # salary 없어도 emp만 추출 (한화비전, 스팩)
        if len(cells) >= 10:
            r = _tryExtract(cells, 6, 7, 8, 9)
            if r:
                return r

        # cells[2]에 emp (스팩 일부)
        if len(cells) >= 3:
            r = _tryExtract(cells, 2, 7 if len(cells) > 7 else 99, 8 if len(cells) > 8 else 99, 9 if len(cells) > 9 else 99)
            if r:
                return r

    return {}


def _hasZeroEmployeeRow(content: str) -> bool:
    """합계 행이 존재하지만 직원수가 0 또는 - 인지 확인."""
    for line in content.split("\n"):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < 4:
            continue
        if cells[0] in ("합 계", "합계"):
            return True
    return False


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))

    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
    noSection = []
    noEmployee = []
    fail = []

    for path in files:
        code = path.stem
        df = pl.read_parquet(str(path))
        corpName = df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
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
                rows = df.filter(
                    (pl.col("year") == year)
                    & (
                        pl.col("section_title").str.contains("직원")
                        | pl.col("section_title").str.contains("임원")
                    )
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                continue

            content = rows["section_content"][0]
            parsed = parseEmployeeTable(content)

            if parsed.get("totalEmployees") is not None:
                ok.append((code, corpName, year, parsed))
                found = True
                break
            else:
                hasTotal = _hasZeroEmployeeRow(content)
                if hasTotal:
                    noEmployee.append((code, corpName, year))
                else:
                    fail.append((code, corpName, year, "직원 테이블 파싱 실패"))
                found = True
                break

        if not found:
            hasBiz = df.filter(pl.col("report_type").str.contains("사업보고서")).height > 0
            if hasBiz:
                fail.append((code, corpName, "", "사업보고서 있으나 임직원 섹션 없음"))
            else:
                noSection.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"직원 0명 (리츠/스팩): {len(noEmployee)}개")
    print(f"사업보고서 없음: {len(noSection)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(fail) + len(noEmployee)
    if total > 0:
        rate = (len(ok) + len(noEmployee)) / total * 100
        print(f"\n성공률 (사업보고서 보유 종목 기준): {rate:.1f}%")

    if fail:
        print(f"\n{'=' * 100}")
        print("실패 목록")
        print(f"{'=' * 100}")
        for code, name, year, reason in fail:
            print(f"  [{code}] {name} ({year}): {reason}")

    if noEmployee:
        print(f"\n{'=' * 100}")
        print(f"직원 0명 종목 ({len(noEmployee)}개)")
        print(f"{'=' * 100}")
        for code, name, year in noEmployee[:20]:
            print(f"  [{code}] {name} ({year})")
        if len(noEmployee) > 20:
            print(f"  ... +{len(noEmployee) - 20}개")

    if noSection:
        print(f"\n{'=' * 100}")
        print(f"사업보고서 없는 종목 ({len(noSection)}개)")
        print(f"{'=' * 100}")
        for code, name in noSection[:20]:
            print(f"  [{code}] {name}")
        if len(noSection) > 20:
            print(f"  ... +{len(noSection) - 20}개")

    print(f"\n{'=' * 100}")
    print("성공 종목 샘플 (상위 10개)")
    print(f"{'=' * 100}")
    for code, name, year, parsed in ok[:10]:
        emp = parsed.get("totalEmployees", 0) or 0
        tenure = parsed.get("avgTenure", "N/A")
        avg = parsed.get("avgSalary", 0) or 0
        print(f"  [{code}] {name} ({year}): {emp:,.0f}명, {tenure}년, {avg:,.0f}백만원")


if __name__ == "__main__":
    main()
