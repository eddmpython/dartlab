"""
실험 ID: 004
실험명: 전체 종목 최대주주 파서 테스트

목적:
- 보유 데이터 전체 종목에 대해 최대주주 파서 적용
- 성공/실패/데이터없음 통계 수집

가설:
1. 사업보고서 보유 종목 90% 이상 파싱 성공

방법:
1. data/docsData/ 전체 parquet 파일 순회
2. 각 종목 최신 사업보고서 주주 섹션 파싱
3. 성공/실패 분류
4. 실패 케이스 상세 기록

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


def parseAmount(text: str) -> float | None:
    if not text or text.strip() in ("", "-", "\u3000", "\u2015", "\u2013"):
        return None
    cleaned = text.strip()
    cleaned = cleaned.replace(",", "").replace(" ", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    if cleaned.count(".") > 1:
        return None
    cleaned = cleaned.strip(".")
    if not cleaned:
        return None
    return float(cleaned)


def parseMajorHolderTable(content: str) -> dict:
    lines = content.split("\n")
    result = {
        "holders": [],
        "majorHolder": None,
        "majorRatio": None,
        "totalRatio": None,
    }

    inTable = False

    for line in lines:
        s = line.strip()
        if not s.startswith("|"):
            if inTable and result["holders"]:
                break
            continue

        cells = [c.strip() for c in s.split("|")]
        if cells and cells[0] == "":
            cells = cells[1:]
        if cells and cells[-1] == "":
            cells = cells[:-1]
        if len(cells) < 3:
            continue

        txt = " ".join(cells)

        if all(c.replace("-", "") == "" for c in cells):
            continue

        if ("성 명" in txt or "성명" in txt) and ("관 계" in txt or "관계" in txt) and ("주식" in txt or "지분" in txt):
            inTable = True
            continue

        if not inTable:
            continue

        if "기 초" in txt or ("주식수" in txt and "지분율" in txt):
            continue

        if "출자자수" in txt or "명 칭" in txt or "직위" in txt or "직책" in txt:
            break

        name = cells[0]
        if name in ("합 계", "합계", "계"):
            for ci in range(len(cells) - 1, 0, -1):
                v = parseAmount(cells[ci])
                if v is not None and 0 < v < 100:
                    result["totalRatio"] = v
                    break
            break

        if len(cells) < 7:
            continue

        if not name or name in ("기 초", "기초", "주식수", "지분율"):
            continue

        relation = cells[1]
        stockType = cells[2]
        ratioEnd = parseAmount(cells[6])

        holder = {
            "name": name,
            "relation": relation,
            "stockType": stockType,
            "ratioEnd": ratioEnd,
        }
        result["holders"].append(holder)

        isMajor = "본인" in relation or ("최대주주" in relation and "특수" not in relation)
        isCommon = "보통주" in stockType or "의결권" in stockType
        if isMajor and isCommon and result["majorHolder"] is None:
            result["majorHolder"] = name
            result["majorRatio"] = ratioEnd

    if result["majorHolder"] is None and result["holders"]:
        first = result["holders"][0]
        if first["ratioEnd"] and first["ratioEnd"] > 0:
            result["majorHolder"] = first["name"]
            result["majorRatio"] = first["ratioEnd"]

    return result


def main():
    files = sorted(DATA_DIR.glob("*.parquet"))
    print(f"전체 종목: {len(files)}개")
    print("=" * 100)

    ok = []
    noSection = []
    noBiz = []
    fail = []

    for path in files:
        code = path.stem
        df = pl.read_parquet(str(path))
        corpName = (
            df["corp_name"].unique().to_list()[0] if "corp_name" in df.columns else code
        )
        years = sorted(df["year"].unique().to_list(), reverse=True)

        found = False
        for year in years[:3]:
            rows = df.filter(
                (pl.col("year") == year)
                & pl.col("section_title").str.contains("주주")
                & pl.col("report_type").str.contains("사업보고서")
                & ~pl.col("report_type").str.contains("기재정정|첨부")
            )
            if rows.height == 0:
                rows = df.filter(
                    (pl.col("year") == year)
                    & pl.col("section_title").str.contains("주주")
                    & pl.col("report_type").str.contains("사업보고서")
                )
            if rows.height == 0:
                continue

            for i in range(rows.height):
                content = rows["section_content"][i]
                if "최대주주" not in content and "주식소유" not in content:
                    continue

                parsed = parseMajorHolderTable(content)
                if parsed["majorHolder"]:
                    ok.append((code, corpName, year, parsed))
                    found = True
                    break

            if found:
                break

        if not found:
            hasBiz = (
                df.filter(pl.col("report_type").str.contains("사업보고서")).height > 0
            )
            hasHolder = df.filter(
                pl.col("section_title").str.contains("주주")
                & pl.col("report_type").str.contains("사업보고서")
            ).height > 0
            if hasHolder:
                fail.append((code, corpName, "", "주주 섹션 있으나 테이블 없음"))
            elif hasBiz:
                noSection.append((code, corpName))
            else:
                noBiz.append((code, corpName))

    print(f"\n성공: {len(ok)}개")
    print(f"주주 섹션 없음: {len(noSection)}개")
    print(f"사업보고서 없음: {len(noBiz)}개")
    print(f"실패: {len(fail)}개")

    total = len(ok) + len(fail)
    if total > 0:
        rate = len(ok) / total * 100
        print(f"\n성공률 (주주 섹션 보유 기준): {rate:.1f}%")

    if fail:
        print(f"\n{'=' * 100}")
        print("실패 목록")
        print(f"{'=' * 100}")
        for code, name, year, reason in fail:
            print(f"  [{code}] {name} ({year}): {reason}")

    print(f"\n{'=' * 100}")
    print("성공 종목 샘플 (상위 15개)")
    print(f"{'=' * 100}")
    for code, name, year, parsed in ok[:15]:
        major = parsed["majorHolder"]
        ratio = parsed["majorRatio"]
        total = parsed.get("totalRatio")
        nHolders = len(parsed["holders"])
        totalStr = f", 합계 {total}%" if total else ""
        print(
            f"  [{code}] {name} ({year}): {major} {ratio}%{totalStr} ({nHolders}명)"
        )


if __name__ == "__main__":
    main()
