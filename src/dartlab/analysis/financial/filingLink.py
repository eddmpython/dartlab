"""사업보고서 글을 재무 숫자와 전년 보고서에 연결한다.

calcFilingLinks 는 문장 속 금액을 재무제표 숫자와 맞춰 회사가 밝힌 이유를 묶고,
calcNewFilingSentences 는 전년 사업보고서에 없던 문장을 고른다.
"""

from __future__ import annotations

import html
import logging
import re

from dartlab.core.memory import memoizedCalc

_log = logging.getLogger(__name__)

_STATEMENTS = ("IS", "BS", "CF")
_STATEMENT_RANK = {"IS": 0, "BS": 1, "CF": 2, "부문": 3}
_SKIP_ACCOUNTS = frozenset({"자본과부채총계", "부채와자본총계"})
_NAME_SUFFIXES = ("총계", "합계", "액")
_UNNAMED_TOLERANCE = 1e-4
_MENTION_LIMIT = 5
_REASON_LIMIT = 3
_FOLLOWING_LIMIT = 3

_AMOUNT = re.compile(
    r"(?P<jo>\d[\d,]*(?:\.\d+)?)\s*조(?:\s*(?P<joEok>\d[\d,]*)\s*억)?(?:\s*(?P<joMan>\d[\d,]*)\s*만)?"
    r"|(?P<eok>\d[\d,]*(?:\.\d+)?)\s*억(?:\s*(?P<eokMan>\d[\d,]*)\s*만)?"
    r"|(?P<mil>\d[\d,]*(?:\.\d+)?)\s*백만"
)
_WON = re.compile(r"\s*원")
_OTHER_UNIT = re.compile(r"\s*(?:달러|불|엔|위안|유로|파운드|대(?!비)|개|명|건|주|톤|장|회|배|USD|EUR|JPY|CNY|\$)")
_SENTENCE_END = re.compile(r"(?<=[다요음함됨임]\.)\s*")
_REASON = re.compile(
    r"원인|때문|따른|따라|인해|인하여|인한|영향|힘입어|기인|효과|덕분|확대로|증가로|감소로|상승으로|하락으로|둔화로|강세|약세"
)
_NAME_STRIP = re.compile(r"[\s()]")
_PARTICLES = ("은", "는", "이", "가", "의", "을", "를", "도", "에")
_YEAR_COLUMN = re.compile(r"\d{4}")
_BASE_PERIOD = re.compile(r"(\d{4})(?:Q([1-4]))?")
_NEW_CHAPTERS = ("II.", "IV.")
_NEW_MIN_LENGTH = 30
_NEW_LIMIT = 20
_COMPARE_STRIP = re.compile(r"[\d\s.,()%~\-ㆍ·'\"“”‘’\[\]]")
_OUTLOOK = re.compile(r"전망|예상|위험|불확실|우려|위축|둔화|부담|감소|하락|악화|중단|철수|소송|제재|리스크")
_CHANGE = re.compile(r"신규|새로|새롭게|인수|출시|진출|확대|축소|증가|상승|개선|계획")


def _number(text: str | None) -> float:
    """쉼표가 든 숫자 글을 실수로 읽는다. 비면 0."""
    return float(text.replace(",", "")) if text else 0.0


def _decimals(text: str | None) -> int:
    """숫자 글의 소수 자릿수."""
    return len(text.split(".")[1]) if text and "." in text else 0


def _parseAmount(match: re.Match, text: str) -> tuple[float, float] | None:
    """찾은 금액 하나를 (원 단위 값, 글이 적은 자릿수 크기) 로 읽는다. 원화가 아니면 None."""
    tail = text[match.end() :]
    won = _WON.match(tail) is not None
    if not won and _OTHER_UNIT.match(tail):
        return None
    part = match.groupdict()
    if part["jo"] is not None:
        if not won and not (part["joEok"] or part["joMan"]):
            return None
        if text[max(0, match.start() - 2) : match.start()].strip().endswith("제"):
            return None
        value = _number(part["jo"]) * 1e12 + _number(part["joEok"]) * 1e8 + _number(part["joMan"]) * 1e4
        if part["joMan"]:
            grain = 1e4
        elif part["joEok"]:
            grain = 1e8
        else:
            grain = 1e12 / 10 ** _decimals(part["jo"])
    elif part["eok"] is not None:
        value = _number(part["eok"]) * 1e8 + _number(part["eokMan"]) * 1e4
        grain = 1e4 if part["eokMan"] else 1e8 / 10 ** _decimals(part["eok"])
    else:
        if not won:
            return None
        value = _number(part["mil"]) * 1e6
        grain = 1e6 / 10 ** _decimals(part["mil"])
    return (value, grain) if value > 0 else None


def _readAmounts(sentence: str) -> list[tuple[str, float, float]]:
    """문장에 적힌 원화 금액을 (글, 값, 자릿수 크기) 로 모두 읽는다."""
    out = []
    for match in _AMOUNT.finditer(sentence):
        parsed = _parseAmount(match, sentence)
        if parsed is not None:
            won = _WON.match(sentence, match.end())
            end = won.end() if won else match.end()
            out.append((sentence[match.start() : end].strip(), parsed[0], parsed[1]))
    return out


def _splitSentences(text: str | None) -> list[str]:
    """공시 글을 '~다.' 같은 끝맺음에서 문장으로 나눈다."""
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_END.split(html.unescape(text)) if s.strip()]


def _nameKey(text: str) -> str:
    """이름 비교용 글. 공백과 괄호를 지운다."""
    return _NAME_STRIP.sub("", text)


def _accountStem(name: str) -> str:
    """계정 이름에서 끝말(총계·합계·액)을 뗀 비교용 이름."""
    key = _nameKey(name)
    for suffix in _NAME_SUFFIXES:
        if key.endswith(suffix) and len(key) > len(suffix) + 1:
            return key[: -len(suffix)]
    return key


def _isReason(sentenceKey: str, sentence: str, name: str, mentioned: bool) -> bool:
    """계정의 이유 문장인가. 이유 표시어가 있고, 금액 문장이 아니면 계정 이름 뒤에 조사가 붙어야 한다."""
    if not _REASON.search(sentence):
        return False
    stem = _accountStem(name)
    if stem not in sentenceKey:
        return False
    if mentioned:
        return True
    return any(f"{word}{p}" in sentenceKey for word in {stem, _nameKey(name)} for p in _PARTICLES)


def _chapterRank(chapter: str) -> int:
    """경영진단(IV)을 먼저, 사업의 내용(II)을 다음에 두는 차례."""
    if chapter.startswith("IV."):
        return 0
    if chapter.startswith("II."):
        return 1
    return 2


def _filingYear(company, basePeriod: str | None) -> str | None:
    """사업보고서를 읽을 연도. 기준 기간이 분기 중이면 그 전 해의 사업보고서다."""
    if basePeriod:
        match = _BASE_PERIOD.fullmatch(str(basePeriod))
        if match:
            year = int(match.group(1))
            quarter = match.group(2)
            return str(year if quarter in (None, "4") else year - 1)
    try:
        result = company.select("IS", freq="Y")
    except (AttributeError, KeyError, ValueError, TypeError) as exc:
        _log.debug("filingLink: 연간 손익계산서 연도를 읽지 못함 - %s: %s", type(exc).__name__, exc)
        return None
    df = getattr(result, "df", None)
    if df is None:
        return None
    return next((col for col in df.columns if _YEAR_COLUMN.fullmatch(col)), None)


def _textLeaves(code: str, periods: list[str]):
    """사업보고서 글 조각(text leaf)만 기간 열로 읽는다. 없으면 None."""
    import polars as pl

    from dartlab.providers.dart.panel.read import (
        PanelArtifactFetchError,
        PanelArtifactReadError,
        PanelSchemaError,
        readWide,
    )

    try:
        wide = readWide(code, tag=False, periods=periods)
    except (PanelArtifactFetchError, PanelArtifactReadError, PanelSchemaError) as exc:
        _log.debug("filingLink: %s 공시 글을 읽지 못함 - %s: %s", code, type(exc).__name__, exc)
        return None
    if wide is None or wide.is_empty() or "leafType" not in wide.columns:
        return None
    return wide.filter(pl.col("leafType") == "text")


def _stockCode(company) -> str | None:
    """DART 6자리 종목코드. 아니면 None."""
    code = getattr(company, "stockCode", None)
    return code if isinstance(code, str) and len(code) == 6 and code.isdigit() else None


def _statementAccounts(company, year: str) -> tuple[list[dict], list[tuple]]:
    """IS·BS·CF 연간 숫자에서 계정 목록과 맞출 후보 숫자를 만든다."""
    prev = str(int(year) - 1)
    accounts: list[dict] = []
    candidates: list[tuple] = []
    seen: set[tuple[str, str]] = set()
    for statement in _STATEMENTS:
        try:
            result = company.select(statement, freq="Y")
        except (AttributeError, KeyError, ValueError, TypeError) as exc:
            _log.debug("filingLink: %s 연간 숫자를 읽지 못함 - %s: %s", statement, type(exc).__name__, exc)
            continue
        df = getattr(result, "df", None)
        if df is None or year not in df.columns or "항목" not in df.columns:
            continue
        hasPrev = prev in df.columns
        for row in df.iter_rows(named=True):
            name = row.get("항목")
            if not name or _nameKey(name) in _SKIP_ACCOUNTS or (statement, name) in seen:
                continue
            seen.add((statement, name))
            current = row.get(year)
            previous = row.get(prev) if hasPrev else None
            change = current - previous if current is not None and previous is not None else None
            index = len(accounts)
            accounts.append(
                {
                    "account": name,
                    "statement": statement,
                    "current": current,
                    "previous": previous,
                    "change": change,
                    "mentions": [],
                    "reasons": [],
                }
            )
            stem = _accountStem(name)
            for kind, value in (("당기", current), ("전기", previous), ("증감", change)):
                if value:
                    candidates.append((stem, float(value), kind, "account", index, _STATEMENT_RANK[statement]))
    return accounts, candidates


def _segmentCandidates(company, year: str, basePeriod: str | None) -> list[tuple]:
    """부문 매출·영업이익을 맞출 후보 숫자로 만든다. 부문 이름은 글과 맞추지 않는다."""
    from dartlab.analysis.financial._revenueSelect import _selectDocsOpIncome, _selectDocsRevenue

    revenue = _selectDocsRevenue(company, basePeriod=basePeriod)
    if not revenue:
        return []
    segData, yCols = revenue
    opData = _selectDocsOpIncome(company, yCols) or {}
    prev = str(int(year) - 1)
    out: list[tuple] = []
    for segment, values in segData.items():
        for metric, series in (("매출", values), ("영업이익", opData.get(segment, {}))):
            current, previous = series.get(year), series.get(prev)
            change = current - previous if current is not None and previous is not None else None
            for kind, value in (("당기", current), ("전기", previous), ("증감", change)):
                if value:
                    out.append(("", float(value), kind, "segment", f"{segment} {metric}", _STATEMENT_RANK["부문"]))
    return out


def _bestCandidate(sentenceKey: str, value: float, grain: float, candidates: list[tuple]) -> tuple | None:
    """글의 금액과 맞는 후보 하나. 이름이 문장에 있는 후보, 차이가 작은 후보, 표 차례 순이다."""
    best = None
    bestKey = None
    for order, cand in enumerate(candidates):
        stem, candValue = cand[0], cand[1]
        diff = abs(abs(candValue) - value)
        if diff > grain:
            continue
        named = bool(stem) and stem in sentenceKey
        if not named and grain / value > _UNNAMED_TOLERANCE:
            continue
        key = (0 if named else 1, -len(stem) if named else 0, diff, cand[5], order)
        if bestKey is None or key < bestKey:
            best, bestKey = cand, key
    return best


@memoizedCalc
def calcFilingLinks(company, *, basePeriod: str | None = None) -> dict | None:
    """사업보고서 문장 속 금액을 재무제표 숫자와 맞춰 계정마다 회사가 밝힌 이유를 묶는다.

    Capabilities:
        사업보고서 전체 글(사업의 내용, 이사의 경영진단, 감사보고서 등)의 원화 금액을 읽어
        IS·BS·CF 연간 숫자(당기, 전기, 증감)와 부문 매출·영업이익에 맞춘다. 맞은 계정마다
        그 금액이 나온 문장과, 같은 글 조각에서 계정 이름과 이유 표시어(원인, 영향, 따른 등)가
        함께 든 문장을 모은다. 부문 금액 문장은 다음 금액 문장 전까지의 설명 문장을 붙이고,
        다른 절에 제목만 붙여 다시 실은 같은 문장은 한 번만 둔다.

    Args:
        company: DART Company 객체.
        basePeriod: 기준 기간. 분기 중이면 전년 사업보고서, None 이면 최신 연간 숫자의 해.

    Returns:
        dict | None:
            - ``year`` / ``period``: 읽은 사업보고서 연도와 기간 열 (예 "2025", "2025Q4")
            - ``sentenceCount`` / ``amountCount`` / ``matchedCount``: 읽은 문장, 원화 금액, 맞은 금액 수
            - ``accountCount``: 금액이 맞은 계정 수
            - ``accounts``: 계정마다 ``{account, statement, current, previous, change,
              mentions[{chapter, section, sentence, amount, kind}], reasons[{chapter, section, sentence}]}``
            - ``segments``: 부문 금액 문장마다 ``{chapter, section, sentence, segments, following}``
            DART 회사가 아니거나 글·숫자가 없으면 None.

    Raises:
        없음. 공시 글을 읽지 못하면 None.

    Example:
        >>> r = calcFilingLinks(Company("005930"))
        >>> r["accounts"][0]["account"], r["accounts"][0]["mentions"][0]["amount"]
        ('매출액', '333조 6,059억원')

    Guide:
        금액은 글에 적힌 자릿수(조, 억, 백만) 안에서 같으면 맞은 것으로 본다. 문장에 계정
        이름이 없으면 자릿수 크기가 값의 1만분의 1 이하일 때만 받는다(우연히 같은 값 방지).
        여러 계정의 합(예 유·무형자산 취득)은 맞지 않으면 버린다.

    When:
        스토리 '사업보고서' 섹션에서 숫자마다 회사가 밝힌 이유를 인용할 때, AI 답변에서
        숫자 변화의 회사 측 설명을 찾을 때.

    How:
        select(IS/BS/CF, freq="Y") 연간 열 → 후보 숫자. readWide(tag=False) text leaf →
        문장 분리 → 원화 금액 정규식 → 후보 맞춤 → 같은 글 조각의 이유 문장 수집.

    Requires:
        DART 사업보고서 panel 글과 연간 재무제표.

    SeeAlso:
        - ``calcNewFilingSentences``: 전년 보고서에 없던 문장
        - ``calcSegmentComposition``: 부문 구성

    AIContext:
        reasons 문장은 회사 주장이다. 인용으로 두고 해석과 섞지 않는다. 숫자 방향과 회사
        설명이 어긋나면 그 차이를 짚는다. 매수·매도 판단으로 바꾸지 않는다.
    """
    code = _stockCode(company)
    if code is None:
        return None
    year = _filingYear(company, basePeriod)
    if year is None:
        return None
    period = f"{year}Q4"
    leaves = _textLeaves(code, [period])
    if leaves is None or period not in leaves.columns:
        return None
    accounts, candidates = _statementAccounts(company, year)
    candidates.extend(_segmentCandidates(company, year, basePeriod))
    if not candidates:
        return None

    sentenceCount = amountCount = matchedCount = 0
    segments: list[dict] = []
    seenSegment: set[str] = set()
    order = 0
    for row in leaves.iter_rows(named=True):
        sentences = _splitSentences(row.get(period))
        if not sentences:
            continue
        chapter = row.get("chapter") or ""
        section = row.get("sectionLeaf") or ""
        keys = [_nameKey(s) for s in sentences]
        sentenceCount += len(sentences)
        hits: list[list[tuple[str, tuple]]] = []
        for sentence, key in zip(sentences, keys):
            found = []
            for amountText, value, grain in _readAmounts(sentence):
                amountCount += 1
                cand = _bestCandidate(key, value, grain, candidates)
                if cand is not None:
                    matchedCount += 1
                    found.append((amountText, cand))
            hits.append(found)

        touched: set[int] = set()
        for i, found in enumerate(hits):
            segNames = []
            for amountText, cand in found:
                if cand[3] == "account":
                    entry = accounts[cand[4]]
                    if all(m["sentence"] != sentences[i] for m in entry["mentions"]):
                        entry["mentions"].append(
                            {
                                "chapter": chapter,
                                "section": section,
                                "sentence": sentences[i],
                                "amount": amountText,
                                "kind": cand[2],
                                "_order": order + i,
                            }
                        )
                    touched.add(cand[4])
                elif cand[4] not in segNames:
                    segNames.append(cand[4])
            if segNames and not any(keys[i] in seen or seen in keys[i] for seen in seenSegment):
                seenSegment.add(keys[i])
                following = []
                for later, laterHits in zip(sentences[i + 1 :], hits[i + 1 :]):
                    if laterHits or len(following) >= _FOLLOWING_LIMIT:
                        break
                    following.append(later)
                segments.append(
                    {
                        "chapter": chapter,
                        "section": section,
                        "sentence": sentences[i],
                        "segments": segNames,
                        "following": following,
                        "_order": order + i,
                    }
                )

        for index in touched:
            entry = accounts[index]
            mentioned = {m["sentence"] for m in entry["mentions"]}
            for i, (sentence, key) in enumerate(zip(sentences, keys)):
                if not _isReason(key, sentence, entry["account"], sentence in mentioned):
                    continue
                if any(r["sentence"] == sentence for r in entry["reasons"]):
                    continue
                entry["reasons"].append(
                    {"chapter": chapter, "section": section, "sentence": sentence, "_order": order + i}
                )
        order += len(sentences)

    linked = []
    for entry in accounts:
        if not entry["mentions"]:
            continue
        for field, limit in (("mentions", _MENTION_LIMIT), ("reasons", _REASON_LIMIT)):
            items = sorted(entry[field], key=lambda m: (_chapterRank(m["chapter"]), m["_order"]))[:limit]
            for item in items:
                item.pop("_order", None)
            entry[field] = items
        linked.append(entry)
    segments.sort(key=lambda s: (_chapterRank(s["chapter"]), len(s["segments"]), s["_order"]))
    for item in segments:
        item.pop("_order", None)
    if not linked and not segments:
        return None
    return {
        "year": year,
        "period": period,
        "sentenceCount": sentenceCount,
        "amountCount": amountCount,
        "matchedCount": matchedCount,
        "accountCount": len(linked),
        "accounts": linked,
        "segments": segments,
    }


def _compareKey(sentence: str) -> str:
    """두 해 문장 비교용 글. 숫자·공백·구두점을 지워 숫자만 바뀐 문장은 같은 문장으로 본다."""
    return _COMPARE_STRIP.sub("", sentence)


def _newSentenceScore(sentence: str, chapter: str) -> int:
    """새 문장의 차례 점수. 전망·위험 2점, 변화 1점, 이유 1점, 경영진단(IV) 1점."""
    score = 2 if _OUTLOOK.search(sentence) else 0
    score += 1 if _CHANGE.search(sentence) else 0
    score += 1 if _REASON.search(sentence) else 0
    score += 1 if chapter.startswith("IV.") else 0
    return score


@memoizedCalc
def calcNewFilingSentences(company, *, basePeriod: str | None = None) -> dict | None:
    """올해 사업보고서의 사업의 내용·경영진단 글에서 전년 보고서에 없던 문장을 고른다.

    Capabilities:
        올해와 전년 사업보고서 글 전체를 문장으로 나눠 비교한다. 숫자만 바뀐 문장은 같은 문장으로
        보고, 사업의 내용(II)과 이사의 경영진단(IV)에서 올해 처음 나온 30자 이상 문장을 고른다.
        전망·위험, 변화, 이유를 말한 문장과 경영진단 문장을 앞에 둔다.

    Args:
        company: DART Company 객체.
        basePeriod: 기준 기간. 분기 중이면 전년 사업보고서, None 이면 최신 연간 숫자의 해.

    Returns:
        dict | None:
            - ``year`` / ``period`` / ``previousPeriod``: 읽은 해와 두 기간 열 (예 "2025", "2025Q4", "2024Q4")
            - ``newSentenceCount``: 전년에 없던 문장 수 (II·IV, 30자 이상)
            - ``sentences``: 앞 20개 ``{chapter, section, sentence}``
            DART 회사가 아니거나 두 해 글 가운데 하나가 없으면 None.

    Raises:
        없음. 공시 글을 읽지 못하면 None.

    Example:
        >>> r = calcNewFilingSentences(Company("005930"))
        >>> r["previousPeriod"], r["sentences"][0]["chapter"]
        ('2024Q4', 'IV. 이사의 경영진단 및 분석의견')

    Guide:
        문장이 새로 나왔다는 것은 회사가 올해 처음 꺼낸 말이라는 뜻이지 사실이 바뀌었다는 뜻이 아니다.
        보고서 양식이 바뀐 해에는 새 문장이 많아진다.

    When:
        스토리 '공시변화' 섹션에서 회사가 올해 새로 말한 전망·위험을 보일 때, AI 답변에서
        전년 대비 달라진 회사 설명을 찾을 때.

    How:
        readWide(tag=False) text leaf 두 해 열 → 문장 분리 → 숫자·공백·구두점을 지운 글로 전년 집합 →
        올해 II·IV 문장 가운데 집합에 없는 것 → (점수, 문서 순서) 정렬.

    Requires:
        DART 사업보고서 panel 글 두 해치.

    SeeAlso:
        - ``calcFilingLinks``: 문장 속 금액과 재무 숫자 연결
        - ``calcChangeIntensity``: topic 별 변화 크기

    AIContext:
        sentences 는 회사 주장이다. 인용으로 두고 사실 판단이나 매수·매도 판단으로 바꾸지 않는다.
    """
    code = _stockCode(company)
    if code is None:
        return None
    year = _filingYear(company, basePeriod)
    if year is None:
        return None
    period, previous = f"{year}Q4", f"{int(year) - 1}Q4"
    leaves = _textLeaves(code, [period, previous])
    if leaves is None or period not in leaves.columns or previous not in leaves.columns:
        return None
    before = {_compareKey(s) for row in leaves.iter_rows(named=True) for s in _splitSentences(row.get(previous))}
    if not before:
        return None

    found: list[tuple[int, int, dict]] = []
    seen: set[str] = set()
    order = 0
    for row in leaves.iter_rows(named=True):
        chapter = row.get("chapter") or ""
        if not chapter.startswith(_NEW_CHAPTERS):
            continue
        for sentence in _splitSentences(row.get(period)):
            order += 1
            if len(sentence) < _NEW_MIN_LENGTH:
                continue
            key = _compareKey(sentence)
            if key in before or key in seen:
                continue
            seen.add(key)
            item = {"chapter": chapter, "section": row.get("sectionLeaf") or "", "sentence": sentence}
            found.append((-_newSentenceScore(sentence, chapter), order, item))
    if not found:
        return None
    found.sort(key=lambda x: (x[0], x[1]))
    return {
        "year": year,
        "period": period,
        "previousPeriod": previous,
        "newSentenceCount": len(found),
        "sentences": [item for _, _, item in found[:_NEW_LIMIT]],
    }
