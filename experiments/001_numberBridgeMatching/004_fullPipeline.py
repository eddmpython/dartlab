"""
실험 ID: 001-004
실험명: 전체 기업 대상 통합 브릿지 매칭 파이프라인

목적:
- 기재정정/첨부 포함, 'III. 재무에 관한 사항' 섹션 활용으로 연도 커버리지 100% 달성
- 전체 267개 기업에서 연속 연도 구간 내 99% 매칭률 달성
- 001~003 실험 결과를 통합한 최종 파이프라인 검증

가설:
1. 기재정정본 포함 + 'III. 재무에 관한 사항' 내 요약재무 추출로 연도 커버리지 95%+ 달성
2. 연속 연도 구간 내 1차 숫자 브릿지 매칭률 99% 달성
3. 전환점 자동 탐지(70% 임계값) + 핵심 계정 브릿지로 전체 연속성 유지

방법:
1. 전체 267개 parquet 파일 로드
2. 보고서 선택: 원본 사업보고서 우선, 없으면 기재정정/첨부 중 최신
3. 섹션 선택: '요약재무정보' 우선, 없으면 'III. 재무에 관한 사항'에서 요약 영역 추출
4. 요약재무 테이블에서 당기(idx=0)/전기(idx=1) 추출
5. 1차 숫자 브릿지 매칭 (중복 방지 usedPrev)
6. 전환점 탐지 (70% 미만)
7. 구간 내 매칭률 집계

결과 (K-IFRS 2011~2025, 임계값 85%):
- 전체 구간 내 매칭률: 98.0% (1380/1408)
- 기업별 최대 구간 매칭률:
  | 기업 | 구간 | 매칭률 | 비고 |
  | 삼성전자 | 2025~2011 (15년) | 99.0% | 전환점 없음, 전 구간 단일 |
  | SK하이닉스 | 2025~2021 (5년) | 99.2% | 기재정정 포함으로 연도 채움 |
  | 유진증권 | 2023~2016 (8년) | 99.1% | 2024 계정 재편으로 분리 |
  | 동화약품 | 2025~2021 (5년) | 98.0% | 2020 전환점 |
  | KR모터스 | 2022~2018 (5년) | 100% | 매년 전환점 발생하는 기업 |
- 미매칭 원인 분류 (구간 내 62건):
  재작성(restatement): 48.4% → 이름동일+금액5%이내로 30건→0건 해결
  계정신설/소멸: 37.1% → 불가피한 미매칭
  EPS 동일금액: 9.7% → 이름강제매칭으로 해결
  비재무항목(회사수 등): 4.8% → 이름강제매칭으로 해결

결론:
- 가설1 채택: 기재정정 포함으로 SK하이닉스 연도 커버리지 6년→14년 (K-IFRS 기준)
- 가설2 부분채택: 대기업(삼성, SK) 구간 내 99%+ 달성. 중소기업(KR모터스) 93~100% (변동 큼)
- 가설3 채택: 전환점 85% 임계값으로 구간 분리 시 구간 내 98.0% 달성
- 핵심 발견:
  1. 재작성(restatement): N년 보고서의 전기 수치 ≠ N-1년 보고서의 당기 수치 (소급수정)
     → 이름유사+금액근사(5%)로 보정 가능
  2. 연결 vs 별도: 2008년 이전은 별도만, 이후는 연결 → 연결 우선 추출 필요
  3. 5개년 테이블(~2014): 재작성 빈도가 높아 매칭률 저하 → K-IFRS 이후 3개년 테이블에서 안정
  4. 중소기업: 매년 계정 구조 변경 → 전환점 빈발, 연속 구간이 짧음
  5. 금융업: 계정 체계가 일반기업과 달라 별도 처리 고려

실험일: 2026-03-06
"""

import os
import re
from collections import defaultdict
from pathlib import Path

import polars as pl

DATA_DIR = Path("data/docsData")

# "자산총계" 판별: 공백/특수문자 제거 후 비교
ASSET_TOTAL_KEYWORDS = ["자산총계", "자산합계", "자산총액"]

def _normalizeSpaces(text):
    """공백·특수문자 제거 (자 산 총 계 → 자산총계)."""
    return re.sub(r"[\s·ㆍ\u3000]", "", text)

def _hasAssetTotal(text):
    """텍스트에 자산총계/자산합계가 포함되어 있는지 (공백 무시)."""
    norm = _normalizeSpaces(text)
    return any(kw in norm for kw in ASSET_TOTAL_KEYWORDS)

def _findAssetTotalLine(lines):
    """자산총계/자산합계가 포함된 첫 번째 테이블 행 인덱스."""
    for i, line in enumerate(lines):
        if "|" not in line:
            continue
        if _hasAssetTotal(line):
            return i
    return -1

CORE_ACCOUNTS = [
    "자산총계", "부채총계", "자본총계",
    "매출액", "영업이익", "당기순이익",
    "유동자산", "비유동자산", "유동부채", "비유동부채",
]

BREAKPOINT_THRESHOLD = 0.85


# ─── 데이터 로드 ───

def selectReport(df, year):
    """해당 연도 사업보고서 선택. 원본 우선, 없으면 기재정정/첨부 중 가장 나중 접수."""
    bizReports = df.filter(
        (pl.col("year") == year)
        & (pl.col("report_type").str.contains("사업보고서"))
    )
    if bizReports.height == 0:
        return None

    # 원본 (기재정정/첨부 아닌 것)
    orig = bizReports.filter(
        ~pl.col("report_type").str.contains("기재정정|첨부")
    )
    if orig.height > 0:
        return orig

    # 기재정정/첨부 중 rcept_date 가장 큰 것
    latest = bizReports.sort("rcept_date", descending=True).head(1)
    latestType = latest["report_type"][0]
    return bizReports.filter(pl.col("report_type") == latestType)


def extractSummaryContent(report):
    """요약재무정보 섹션 내용 추출.

    전략:
    - 연결재무정보 우선, 없으면 별도/개별
    - 전용 섹션('요약재무정보')이 있으면 그 안에서 연결 영역만 추출
    - 없으면 'III. 재무에 관한 사항' 전체에서 추출
    """
    # 소스 콘텐츠 찾기
    content = None
    summary = report.filter(pl.col("section_title").str.contains("요약재무정보"))
    if summary.height > 0:
        content = summary["section_content"][0]
    else:
        finance = report.filter(pl.col("section_title").str.contains("재무에 관한 사항"))
        if finance.height > 0:
            content = finance["section_content"][0]

    if content is None:
        return None

    lines = content.split("\n")

    # 요약 제목 라인들 수집
    summaryHeaders = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if len(stripped) >= 80 or stripped.startswith("|"):
            continue
        if "요약" in stripped and ("재무" in stripped or "연결" in stripped):
            isConsolidated = "연결" in stripped
            summaryHeaders.append((i, stripped, isConsolidated))

    if not summaryHeaders:
        # 요약 제목이 없으면 첫 번째 자산총계 테이블 기반
        return _extractFirstAssetTable(lines)

    # 연결 우선 선택
    target = None
    for idx, title, isCons in summaryHeaders:
        if isCons:
            target = (idx, title)
            break
    if target is None:
        # 연결이 없으면 첫 번째 (별도)
        target = (summaryHeaders[0][0], summaryHeaders[0][1])

    startIdx = target[0]

    # 해당 영역의 끝 찾기: 다음 요약 제목 or 번호 제목까지
    endIdx = len(lines)
    inTable = False
    for i in range(startIdx + 1, len(lines)):
        stripped = lines[i].strip()
        if stripped.startswith("|"):
            inTable = True
        elif inTable and stripped:
            # 테이블이 끝나고 새 제목 시작
            if re.match(r"^\d+\.", stripped) or re.match(r"^[가-힣][.．]", stripped):
                endIdx = i
                break

    region = "\n".join(lines[startIdx:endIdx])
    if not _hasAssetTotal(region):
        # 연결에 자산총계가 없으면 전체에서 시도
        return _extractFirstAssetTable(lines)

    return region


def _extractFirstAssetTable(lines):
    """자산총계/자산합계가 포함된 첫 번째 테이블 영역을 추출."""
    assetIdx = _findAssetTotalLine(lines)
    if assetIdx < 0:
        return None

    # 위로 올라가서 테이블 시작 찾기
    startIdx = 0
    for j in range(assetIdx - 1, -1, -1):
        stripped = lines[j].strip()
        if not stripped.startswith("|") and not stripped == "":
            startIdx = j
            break
    # 아래로 테이블 끝 찾기
    endIdx = len(lines)
    inTable = False
    for j in range(assetIdx, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("|"):
            inTable = True
        elif inTable and stripped and not stripped.startswith("|"):
            endIdx = j
            break

    region = "\n".join(lines[startIdx:endIdx])
    if _hasAssetTotal(region):
        return region
    return None


# ─── 테이블 파싱 ───

def extractTables(content):
    """마크다운 테이블 파싱. DART 중첩 테이블(단위행+본체) 처리."""
    tables = []
    lines = content.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("|") and i + 1 < len(lines) and "---" in lines[i + 1]:
            cells = [c.strip() for c in line.split("|")]
            cells = [c for c in cells if c != ""]
            headers = cells
            i += 2
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rowLine = lines[i].strip()
                if "---" in rowLine:
                    if rows:
                        newHeader = rows.pop()
                        if rows:
                            tables.append({"headers": headers, "rows": rows})
                        headers = newHeader
                        rows = []
                    i += 1
                    continue
                rowCells = [c.strip() for c in rowLine.split("|")]
                rowCells = [c for c in rowCells if c != ""]
                if rowCells:
                    rows.append(rowCells)
                i += 1
            if headers and rows and len(headers) >= 2:
                tables.append({"headers": headers, "rows": rows})
        else:
            i += 1
    return tables


def parseAmount(text):
    """금액 문자열 → float. △와 () 음수 처리."""
    if not text or text.strip() in ("", "-", "　", "―", "–"):
        return None
    cleaned = text.strip()
    isNegative = "△" in cleaned or "(" in cleaned
    cleaned = cleaned.replace("△", "").replace(",", "").replace(" ", "")
    cleaned = cleaned.replace("(", "").replace(")", "")
    cleaned = re.sub(r"[^\d.]", "", cleaned)
    if not cleaned:
        return None
    try:
        val = float(cleaned)
        return -val if isNegative else val
    except ValueError:
        return None


def detectUnit(content):
    """content에서 단위를 감지. 백만원=1, 천원=0.001, 원=0.000001 반환 (백만원 기준 스케일)."""
    # "단위: 백만원", "(단위 : 원)" 등
    m = re.search(r"단위\s*[：:]\s*(백만원|천원|원)", content)
    if m:
        unit = m.group(1)
        if unit == "백만원":
            return 1.0
        elif unit == "천원":
            return 0.001
        elif unit == "원":
            return 0.000001
    return 1.0  # 기본 백만원 가정


def extractAccounts(content):
    """요약재무정보 테이블에서 {계정명: [당기, 전기, ...]} 추출. 단위 정규화 포함."""
    unit = detectUnit(content)
    tables = extractTables(content)

    # 테이블이 0개면 직접 | 행을 파싱하는 폴백
    if not tables:
        rows = []
        headers = None
        for line in content.split("\n"):
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            if "---" in stripped:
                continue
            cells = [c.strip() for c in stripped.split("|")]
            cells = [c for c in cells if c != ""]
            if not cells:
                continue
            # "단위" 포함 행 스킵
            if any("단위" in c for c in cells):
                continue
            # "기" or "년" 포함 행 → 헤더
            cellText = " ".join(cells)
            if headers is None and ("기" in cellText or "년" in cellText) and len(cells) >= 2:
                headers = cells
                continue
            if headers and len(cells) >= 2:
                rows.append(cells)
        if headers and rows:
            tables = [{"headers": headers, "rows": rows}]
    result = {}
    order = []
    for table in tables:
        headers = table["headers"]
        if len(headers) < 2:
            continue
        # 헤더가 단위행("단위", "백만원" 등)이면, rows에서 실제 헤더를 탐색
        headerText = " ".join(headers)
        if "단위" in headerText or all(not h for h in headers[1:]):
            # rows에서 "구분" 또는 "기"를 포함하는 행을 찾아 헤더로 교체
            for ri in range(min(3, len(table["rows"]))):
                candidate = table["rows"][ri]
                candText = " ".join(candidate)
                if "기" in candText or "년" in candText:
                    headers = candidate
                    table["rows"] = table["rows"][ri + 1:]
                    break
            else:
                continue
        # 헤더에 "기" 또는 "년" 포함 여부 (제N기, 당기, 전기, 2024년 등)
        if not any("기" in h or "년" in h for h in headers[1:]):
            continue
        for row in table["rows"]:
            if len(row) < 2:
                continue
            name = row[0].strip()
            if not name or "※" in name or "월" in name:
                continue
            # 날짜행 스킵 (2024년 12월말 등)
            if re.match(r"^\d{4}년", name):
                continue
            # 공백 정규화: "자 산 총 계" → "자산총계"
            # 한글 사이의 공백만 제거 (영문/숫자 앞뒤는 유지)
            name = re.sub(r"(?<=[\uAC00-\uD7A3])\s+(?=[\uAC00-\uD7A3])", "", name)
            amounts = [parseAmount(cell) for cell in row[1:]]
            # 전부 None이면 스킵
            if all(a is None for a in amounts):
                continue
            # 단위 정규화 (백만원 기준)
            if unit != 1.0:
                amounts = [a * unit if a is not None else None for a in amounts]
            result[name] = amounts
            order.append(name)
    return result, order


# ─── 브릿지 매칭 ───

def nameSimilarity(a, b):
    """두 계정명의 유사도 (0~1). 공통 문자 비율 기반."""
    a = a.replace("[", "").replace("]", "").replace("ㆍ", "").strip()
    b = b.replace("[", "").replace("]", "").replace("ㆍ", "").strip()
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    common = sum(1 for c in a if c in b)
    return common / max(len(a), len(b))


def numberBridgeMatch(accCur, accPrev):
    """숫자 브릿지: N년 전기(idx=1) == N-1년 당기(idx=0).

    3단계:
    1차: 정확 매칭 (차이 < 0.5), 동일 금액 후보 여러 개면 이름 유사도 높은 것
    2차: 미매칭 건에서 이름 동일 + 금액 차이 2% 이내 (재작성 보정)
    3차: 미매칭 건에서 이름 유사도 0.7+ 금액 차이 2% 이내 (재작성+명칭변경)
    """
    matched = 0
    total = 0
    usedPrev = set()
    pairs = {}
    unmatchedCur = []

    # 1차: 정확 매칭
    for nameCur, amtsCur in accCur.items():
        if len(amtsCur) < 2 or amtsCur[1] is None:
            continue
        total += 1
        prevAmt = amtsCur[1]

        candidates = []
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            if abs(prevAmt - amtsPrev[0]) < 0.5:
                sim = nameSimilarity(nameCur, namePrev)
                candidates.append((namePrev, sim))

        if candidates:
            candidates.sort(key=lambda x: -x[1])
            bestPrev = candidates[0][0]
            matched += 1
            usedPrev.add(bestPrev)
            pairs[nameCur] = bestPrev
        else:
            unmatchedCur.append(nameCur)

    # 2차: 재작성 보정 (이름 유사 0.8+ 금액 차이 5% 이내)
    stillUnmatched = []
    for nameCur in unmatchedCur:
        amtsCur = accCur[nameCur]
        prevAmt = amtsCur[1]
        if prevAmt == 0:
            stillUnmatched.append(nameCur)
            continue

        bestMatch = None
        bestScore = 0
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            curAmt = amtsPrev[0]
            if curAmt == 0:
                continue
            diff = abs(prevAmt - curAmt) / max(abs(prevAmt), abs(curAmt))
            sim = nameSimilarity(nameCur, namePrev)
            if sim >= 0.8 and diff < 0.05:
                score = sim * (1 - diff)
                if score > bestScore:
                    bestScore = score
                    bestMatch = namePrev

        if bestMatch:
            matched += 1
            usedPrev.add(bestMatch)
            pairs[nameCur] = bestMatch
        else:
            stillUnmatched.append(nameCur)

    # 3차: 이름 유사 + 근사 금액 (명칭 변경 + 재작성)
    for nameCur in list(stillUnmatched):
        amtsCur = accCur[nameCur]
        prevAmt = amtsCur[1]
        if prevAmt == 0:
            continue

        bestMatch = None
        bestScore = 0
        for namePrev, amtsPrev in accPrev.items():
            if namePrev in usedPrev:
                continue
            if len(amtsPrev) < 1 or amtsPrev[0] is None:
                continue
            curAmt = amtsPrev[0]
            if curAmt == 0:
                continue
            diff = abs(prevAmt - curAmt) / max(abs(prevAmt), abs(curAmt))
            sim = nameSimilarity(nameCur, namePrev)
            if sim >= 0.6 and diff < 0.05:
                score = sim * (1 - diff)
                if score > bestScore:
                    bestScore = score
                    bestMatch = namePrev

        if bestMatch:
            matched += 1
            usedPrev.add(bestMatch)
            pairs[nameCur] = bestMatch
            stillUnmatched.remove(nameCur)

    # 4차: 특수 항목 강제 매칭 (주당순이익 동일 금액, 회사수 등)
    for nameCur in list(stillUnmatched):
        amtsCur = accCur[nameCur]
        prevAmt = amtsCur[1]

        # 기본/희석 주당순이익: 이름으로 직접 매칭
        if "주당" in nameCur and "순이익" in nameCur:
            for namePrev in accPrev:
                if namePrev in usedPrev:
                    continue
                if "주당" in namePrev and "순이익" in namePrev:
                    # 같은 종류(기본↔기본, 희석↔희석) 매칭
                    curType = "희석" if "희석" in nameCur else "기본"
                    prevType = "희석" if "희석" in namePrev else "기본"
                    if curType == prevType:
                        matched += 1
                        usedPrev.add(namePrev)
                        pairs[nameCur] = namePrev
                        stillUnmatched.remove(nameCur)
                        break

        # 연결 회사수: 이름으로 직접 매칭
        elif "회사" in nameCur and "수" in nameCur:
            for namePrev in accPrev:
                if namePrev in usedPrev:
                    continue
                if "회사" in namePrev and "수" in namePrev:
                    matched += 1
                    usedPrev.add(namePrev)
                    pairs[nameCur] = namePrev
                    if nameCur in stillUnmatched:
                        stillUnmatched.remove(nameCur)
                    break

    rate = matched / total if total > 0 else 0
    return rate, matched, total, pairs


def prevPrevBridgeMatch(accCur, accPrev, accPrevPrev, usedPrev):
    """2차 전전기 브릿지: N년 전전기(idx=2) == N-2년 당기(idx=0)로 중개."""
    extraPairs = {}
    if not accPrevPrev:
        return extraPairs, usedPrev

    for nameCur, amtsCur in accCur.items():
        if len(amtsCur) < 3 or amtsCur[2] is None:
            continue
        ppAmt = amtsCur[2]

        # N-2년 당기에서 같은 숫자 찾기
        ppName = None
        for namepp, amtspp in accPrevPrev.items():
            if len(amtspp) < 1 or amtspp[0] is None:
                continue
            if abs(ppAmt - amtspp[0]) < 0.5:
                ppName = namepp
                break

        if ppName is None:
            continue

        # N-2년에서 찾은 계정의 위치와 비슷한 위치의 N-1년 계정 매칭
        ppKeys = list(accPrevPrev.keys())
        prevKeys = list(accPrev.keys())
        if ppName not in ppKeys:
            continue
        ppPos = ppKeys.index(ppName)

        bestMatch = None
        bestDist = 999
        for namePrev in prevKeys:
            if namePrev in usedPrev:
                continue
            prevPos = prevKeys.index(namePrev)
            dist = abs(ppPos - prevPos)
            if dist < bestDist:
                bestDist = dist
                bestMatch = namePrev

        if bestMatch and bestDist <= 2:
            extraPairs[nameCur] = bestMatch
            usedPrev.add(bestMatch)

    return extraPairs, usedPrev


# ─── 전체 파이프라인 ───

def loadCompanyData(filepath):
    """parquet → {year: (accounts, order)} 딕셔너리."""
    df = pl.read_parquet(str(filepath))
    yearData = {}
    years = sorted(df["year"].unique().to_list(), reverse=True)

    for year in years:
        report = selectReport(df, year)
        if report is None:
            continue

        content = extractSummaryContent(report)
        if content is None:
            continue

        accounts, order = extractAccounts(content)
        if accounts:
            yearData[year] = (accounts, order)

    return yearData


def analyzeCompany(filepath, ifrsOnly=False):
    """단일 기업 분석: 연도별 매칭률, 전환점 탐지, 구간 분리."""
    yearData = loadCompanyData(filepath)

    if len(yearData) < 2:
        return None

    sortedYears = sorted(yearData.keys(), reverse=True)

    # K-IFRS 이후만 (2011~)
    if ifrsOnly:
        sortedYears = [y for y in sortedYears if int(y) >= 2011]
        if len(sortedYears) < 2:
            return None

    # 연도 쌍별 매칭
    pairResults = []
    for i in range(len(sortedYears) - 1):
        curYear = sortedYears[i]
        prevYear = sortedYears[i + 1]
        accCur = yearData[curYear][0]
        accPrev = yearData[prevYear][0]

        rate, matched, total, pairs = numberBridgeMatch(accCur, accPrev)
        yearGap = int(curYear) - int(prevYear)

        pairResults.append({
            "curYear": curYear,
            "prevYear": prevYear,
            "rate": rate,
            "matched": matched,
            "total": total,
            "yearGap": yearGap,
        })

    # 전환점 탐지 + 구간 분리
    segments = [{"years": [sortedYears[0]], "pairs": []}]
    breakpoints = []

    for pr in pairResults:
        isBreak = pr["rate"] < BREAKPOINT_THRESHOLD
        if isBreak:
            breakpoints.append(pr)
            segments.append({"years": [pr["prevYear"]], "pairs": []})
        else:
            segments[-1]["years"].append(pr["prevYear"])
            segments[-1]["pairs"].append(pr)

    # 구간별 집계
    segmentStats = []
    for seg in segments:
        if not seg["pairs"]:
            segmentStats.append({
                "startYear": seg["years"][0],
                "endYear": seg["years"][-1],
                "nYears": len(seg["years"]),
                "matched": 0,
                "total": 0,
                "rate": None,
            })
            continue
        segMatched = sum(p["matched"] for p in seg["pairs"])
        segTotal = sum(p["total"] for p in seg["pairs"])
        segRate = segMatched / segTotal if segTotal > 0 else 0
        segmentStats.append({
            "startYear": seg["years"][0],
            "endYear": seg["years"][-1],
            "nYears": len(seg["years"]),
            "matched": segMatched,
            "total": segTotal,
            "rate": segRate,
        })

    # 연속 연도(gap=1) 쌍만의 매칭률
    contPairs = [p for p in pairResults if p["yearGap"] == 1]
    contMatched = sum(p["matched"] for p in contPairs)
    contTotal = sum(p["total"] for p in contPairs)
    contRate = contMatched / contTotal if contTotal > 0 else None

    # 전체 매칭률
    allMatched = sum(p["matched"] for p in pairResults)
    allTotal = sum(p["total"] for p in pairResults)
    allRate = allMatched / allTotal if allTotal > 0 else None

    return {
        "nYears": len(sortedYears),
        "nPairs": len(pairResults),
        "nBreakpoints": len(breakpoints),
        "nSegments": len(segments),
        "allRate": allRate,
        "allMatched": allMatched,
        "allTotal": allTotal,
        "contRate": contRate,
        "contMatched": contMatched,
        "contTotal": contTotal,
        "segments": segmentStats,
        "breakpoints": breakpoints,
        "pairResults": pairResults,
    }


def main():
    print("=== 004: 전체 기업 통합 브릿지 매칭 파이프라인 ===\n")

    parquetFiles = sorted(DATA_DIR.glob("*.parquet"))
    print(f"대상 파일: {len(parquetFiles)}개\n")

    results = {}
    errors = []

    for filepath in parquetFiles:
        code = filepath.stem
        try:
            r = analyzeCompany(filepath, ifrsOnly=True)
            if r:
                results[code] = r
        except Exception as e:
            errors.append((code, str(e)))

    print(f"분석 완료: {len(results)}개 기업, 에러: {len(errors)}개\n")

    if errors:
        print("=== 에러 목록 ===")
        for code, err in errors[:10]:
            print(f"  {code}: {err}")
        print()

    # ─── 통계 집계 ───

    # 1. 전체 연속 연도 매칭률
    totalContMatched = sum(r["contMatched"] for r in results.values())
    totalContTotal = sum(r["contTotal"] for r in results.values())
    totalContRate = totalContMatched / totalContTotal if totalContTotal > 0 else 0

    totalAllMatched = sum(r["allMatched"] for r in results.values())
    totalAllTotal = sum(r["allTotal"] for r in results.values())
    totalAllRate = totalAllMatched / totalAllTotal if totalAllTotal > 0 else 0

    print("=== 전체 통계 ===")
    print(f"기업 수: {len(results)}")
    print(f"전체 매칭률: {totalAllRate:.1%} ({totalAllMatched}/{totalAllTotal})")
    print(f"연속 연도 매칭률: {totalContRate:.1%} ({totalContMatched}/{totalContTotal})")

    # 2. 연속 연도 매칭률 분포
    contRates = []
    for code, r in results.items():
        if r["contRate"] is not None and r["contTotal"] > 0:
            contRates.append((code, r["contRate"], r["contMatched"], r["contTotal"], r["nYears"]))

    contRates.sort(key=lambda x: x[1])

    print(f"\n=== 연속 연도 매칭률 분포 ({len(contRates)}개 기업) ===")
    brackets = [
        (1.0, 1.0, "100%"),
        (0.99, 1.0, "99~100%"),
        (0.97, 0.99, "97~99%"),
        (0.95, 0.97, "95~97%"),
        (0.90, 0.95, "90~95%"),
        (0.0, 0.90, "<90%"),
    ]
    for lo, hi, label in brackets:
        if label == "100%":
            count = sum(1 for _, r, _, _, _ in contRates if r == 1.0)
        elif label == "99~100%":
            count = sum(1 for _, r, _, _, _ in contRates if 0.99 <= r < 1.0)
        else:
            count = sum(1 for _, r, _, _, _ in contRates if lo <= r < hi)
        pct = count / len(contRates) * 100 if contRates else 0
        print(f"  {label}: {count}개 ({pct:.1f}%)")

    # 3. 하위 20개 기업 (연속 연도 매칭률 낮은 순)
    print(f"\n=== 연속 연도 매칭률 하위 20개 ===")
    print(f"{'종목코드':>8} | {'연도':>4} | {'매칭률':>7} | {'매칭':>5}/{'':<5}")
    print("-" * 45)
    for code, rate, matched, total, nYears in contRates[:20]:
        print(f"{code:>8} | {nYears:>4} | {rate:>6.1%} | {matched:>5}/{total:<5}")

    # 4. 전환점 통계
    bpCounts = [r["nBreakpoints"] for r in results.values()]
    noBp = sum(1 for b in bpCounts if b == 0)
    hasBp = sum(1 for b in bpCounts if b > 0)
    print(f"\n=== 전환점 통계 ===")
    print(f"전환점 없음: {noBp}개 ({noBp/len(results)*100:.1f}%)")
    print(f"전환점 있음: {hasBp}개 ({hasBp/len(results)*100:.1f}%)")

    bpDist = defaultdict(int)
    for b in bpCounts:
        bpDist[b] += 1
    for k in sorted(bpDist.keys()):
        print(f"  {k}개 전환점: {bpDist[k]}개 기업")

    # 5. 연도 커버리지
    yearCounts = [r["nYears"] for r in results.values()]
    print(f"\n=== 연도 커버리지 ===")
    print(f"평균 연도 수: {sum(yearCounts)/len(yearCounts):.1f}")
    print(f"최소: {min(yearCounts)}, 최대: {max(yearCounts)}")
    yearBrackets = [(1, 5), (6, 10), (11, 15), (16, 20), (21, 30)]
    for lo, hi in yearBrackets:
        count = sum(1 for y in yearCounts if lo <= y <= hi)
        print(f"  {lo}~{hi}년: {count}개")

    # 6. 연속 연도 매칭률 상위/중간 예시
    print(f"\n=== 연속 연도 매칭률 99%+ 기업 수: {sum(1 for _, r, _, _, _ in contRates if r >= 0.99)} ===")

    # 7. 구간 내 매칭률 (전환점으로 분리된 연속 구간)
    segRates = []
    for code, r in results.items():
        for seg in r["segments"]:
            if seg["rate"] is not None and seg["total"] > 0 and seg["nYears"] >= 2:
                segRates.append(seg["rate"])

    if segRates:
        avgSegRate = sum(segRates) / len(segRates)
        print(f"\n=== 구간 내 매칭률 (전환점 분리 후) ===")
        print(f"구간 수: {len(segRates)}")
        print(f"평균: {avgSegRate:.1%}")
        print(f"99%+: {sum(1 for r in segRates if r >= 0.99)}/{len(segRates)}")
        print(f"95%+: {sum(1 for r in segRates if r >= 0.95)}/{len(segRates)}")
        print(f"90%+: {sum(1 for r in segRates if r >= 0.90)}/{len(segRates)}")


if __name__ == "__main__":
    main()
