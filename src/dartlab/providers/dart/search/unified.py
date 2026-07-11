"""통합 검색 R* — plain BM25 ⊕ (큐레이션 동의어 + 결정론 라우팅 canon) 확장 BM25 RRF.

``scope="auto"`` 의 랭킹 코어. unifiedSearchRecipe honest-gold 실측으로 확정한 레시피의
본진 이식 — hard(자유구어·paraphrase) nDCG@10 0.237(word·무확장) → 0.502, 정식어 0.618 → 0.943
(tests/_attempts/unifiedSearchRecipe/ARCHITECTURE.md). 임베딩·GPU·학습 0.

융합은 always-safe: 확장이 발화하지 않거나 라우팅이 틀려도 plain BM25 lane 이 RRF 로 보존돼
최악이 plain 과 동급이다. 같은 실험의 기각 카탈로그 — meaning graph(+0.010, 동어반복 인공물)·
fasttext(dominated)·DuckDB FTS(한국어 이점 0) — 는 본진에 들이지 않는다.

artifact: ``router.json`` (인덱스와 동거 배포, 부재 시 라우팅 lane 생략). 큐레이션 동의어는
코드 내장(curatedSyn). title-ngram lane ⊕ content RRF 통합은 후속(type-name 질의 극대화,
ARCHITECTURE §7.5) — 본 모듈은 실측 완료된 content lane 만 담는다.
"""

from __future__ import annotations

import re

import numpy as np
import polars as pl

from dartlab.core.logger import getLogger
from dartlab.providers.dart.search.curatedSyn import expandQuery
from dartlab.providers.dart.search.fieldIndex import (
    _activeIndexDir,
    _getSegments,
    _resolveResultUrl,
    _scopeMask,
    _scoreBM25,
    tokenizeContent,
)
from dartlab.providers.dart.search.router import loadRouterModel, routeCanon
from dartlab.providers.dart.search.semanticConstraints import (
    SemanticConstraintPlan,
    compileSemanticMapper,
    planSemanticConstraints,
    rankBySemanticConstraints,
    scoreSemanticConstraintEvidence,
    semanticScopeMask,
)

_log = getLogger(__name__)

RRF_K = 60  # reciprocal-rank 융합 상수 (landing·recipe parity)
EXPAND_BOOST = 0.5  # 확장토큰 가중 (질의 원토큰 1.0 대비)
EVENT_TITLE_CANDIDATE_FLOOR = 5000
EVENT_TITLE_CANDIDATE_MULTIPLIER = 500
EVENT_TITLE_CANDIDATE_CAP = 5000
BODY_SEMANTIC_CANDIDATE_FLOOR = 800
BODY_SEMANTIC_CANDIDATE_MULTIPLIER = 100
BODY_SEMANTIC_CANDIDATE_CAP = 2000
_REPORT_SURFACE_CACHE: dict[int, tuple[pl.DataFrame, pl.DataFrame]] = {}
_EVENT_TITLE_TERMS: tuple[str, ...] = (
    "공시",
    "원문",
    "결정",
    "변경",
    "제출",
    "체결",
    "발행",
    "취득",
    "처분",
    "소집",
    "결과",
    "합병",
    "분할",
    "양수",
    "양도",
    "소송",
    "횡령",
    "배임",
    "영업정지",
    "배당",
)
_EVENT_TITLE_STRONG_TERMS: tuple[str, ...] = (
    "결정",
    "변경",
    "제출",
    "체결",
    "발행",
    "취득",
    "처분",
    "소집",
    "결과",
    "합병",
    "분할",
    "양수",
    "양도",
    "소송",
    "횡령",
    "배임",
    "영업정지",
    "배당",
)
_BODY_SEMANTIC_TERMS: tuple[str, ...] = (
    "본문",
    "주석",
    "사업의 내용",
    "위험",
    "위험요인",
    "리스크",
    "risk",
    "md&a",
    "유동성",
    "손상",
    "정책",
    "비중",
    "만기",
)
_BODY_SEMANTIC_CUES: tuple[str, ...] = (
    "언급",
    "다룬",
    "관련",
    "수혜",
    "부담",
    "수요",
    "증설",
    "설비투자",
    "전력",
    "인프라",
)
_BODY_GENERIC_WEIGHT_TERMS: tuple[str, ...] = ("공시", "원문", "투자", "기업", "회사", "관련", "언급", "내용", "수혜")
_NEWS_INTENT_TERMS: tuple[str, ...] = ("뉴스", "기사")
_BODY_HANGUL_RE = re.compile(r"[가-힣]+")
_BODY_ASCII_RE = re.compile(r"[A-Za-z]{2,20}")
_REPORT_TERMS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("사업보고서", ("사업보고서", "annual report", "10-k", "10k")),
    ("반기보고서", ("반기보고서", "semiannual report")),
    ("분기보고서", ("분기보고서", "quarterly report", "10-q", "10q")),
    ("감사보고서", ("감사보고서", "audit report")),
    ("투자설명서", ("투자설명서", "prospectus", "investment prospectus")),
    ("증권신고서", ("증권신고서", "registration statement", "securities registration statement")),
    ("일괄신고서", ("일괄신고서", "shelf registration")),
)
_NON_BODY_REPORT_TITLES: tuple[str, ...] = (
    "일괄신고서",
    "투자설명서",
    "증권신고서",
    "감사보고서제출",
)
_NON_DECISION_TERMS: tuple[str, ...] = ("결과", "제출", "보고서", "기사", "뉴스")
_DECISION_RESULT_TERMS: tuple[str, ...] = ("발행결과", "청약결과", "증권발행실적")


def _expansionWeights(query: str, routerModel: dict | None) -> dict[str, float]:
    """질의 → bigram 가중치 dict. 원토큰 1.0 + 큐레이션·라우팅 canon 확장 0.5(max 병합)."""
    weights: dict[str, float] = {t: 1.0 for t in tokenizeContent(query)}

    def boost(term: str) -> None:
        """확장 용어의 bigram 들을 EXPAND_BOOST 가중으로 병합 (기존 가중과 max — 원토큰 1.0 보존).

        Args:
            term: 확장 용어 (동의어 또는 라우팅 canon 본문어).

        Raises:
            없음.

        Example:
            >>> boost("자기주식")  # doctest: +SKIP

        Returns:
            None — 클로저의 weights dict 를 제자리 갱신.
        """
        for t in tokenizeContent(term):
            weights[t] = max(weights.get(t, 0.0), EXPAND_BOOST)

    for term in expandQuery(query):
        boost(term)
    for term in routeCanon(routerModel, query):
        boost(term)
    return weights


def _rrfFuse(plain: np.ndarray, boosted: np.ndarray, *, k: int = RRF_K) -> np.ndarray:
    """두 점수 배열을 reciprocal-rank 로 등가 융합 — 순위 기반이라 lane 간 스케일 무관."""
    fused = np.zeros(len(plain), dtype=np.float32)
    for arr in (plain, boosted):
        nz = np.nonzero(arr)[0]
        for r, d in enumerate(nz[np.argsort(-arr[nz])], start=1):
            fused[int(d)] += np.float32(1.0 / (k + r))
    return fused


def searchUnified(
    query: str,
    *,
    corpCode: str | None = None,
    stockCode: str | None = None,
    sourceKind: str | None = None,
    constraintPlan: SemanticConstraintPlan | None = None,
    limit: int = 10,
) -> pl.DataFrame:
    """통합 검색 — plain BM25 ⊕ 확장 BM25 RRF. main+delta 병합 (delta 우선).

    확장(동의어·canon)이 발화하지 않으면 plain BM25 단독 — searchContent 와 동일 동작으로
    graceful degrade. router.json 부재 시 라우팅 lane 만 생략(큐레이션은 코드 내장이라 동작).

    Args:
        query: 검색어 (자연어 — 구어·약어 허용).
        corpCode: 회사 식별자 corp_code. None 이면 전체.
        stockCode: 종목코드 (6 자리). None 이면 전체.
        limit: 최대 결과 행 수.

    Raises:
        없음.

    Example:
        >>> searchUnified("자사주 샀어?", limit=5)  # doctest: +SKIP

    Returns:
        pl.DataFrame — searchContent 와 동일 스키마 + score/segment/dartUrl. 인덱스 부재 시 info 컬럼.
    """
    tokens = tokenizeContent(query)
    if not tokens:
        return pl.DataFrame()

    segments = _getSegments()
    if not segments:
        return pl.DataFrame(
            {"info": ["content 인덱스가 없습니다. dartlab.providers.dart.search.rebuildContent() 실행 필요."]}
        )
    if constraintPlan is None:
        mapper = compileSemanticMapper(segments)
        constraintPlan = planSemanticConstraints(query, corpCode=corpCode, stockCode=stockCode, mapper=mapper)
    corpCode = corpCode or constraintPlan.facets.corpCode
    stockCode = stockCode or constraintPlan.facets.stockCode

    routerModel = loadRouterModel(_activeIndexDir())  # 세그먼트와 동거 — 부재 시 None
    weights = _expansionWeights(query, routerModel)
    hasExpansion = len(weights) > len(set(tokens))
    bodySemanticRerank = sourceKind != "news" and _prefersBodySemanticRerank(query)
    eventTitleRerank = not bodySemanticRerank and _prefersEventTitleRerank(query)
    reportLabels = _reportLabels(query) if eventTitleRerank else ()
    if eventTitleRerank:
        candidateLimit = _candidateLimit(query, limit)
    elif bodySemanticRerank:
        candidateLimit = _bodyCandidateLimit(query, limit)
    else:
        candidateLimit = limit * 3

    allHits: list[dict] = []
    deltaKeys: set[tuple] = set()
    for name in ("delta", "main"):
        if name not in segments:
            continue
        idx, meta = segments[name]
        # corp/stock 스코프는 RRF *전* lane 점수에 적용 — "회사 안에서 검색" 의미론.
        # 사후 필터는 전역 top-N 에 못 들면 0건이 되는 결함 (흔한 질의 + 회사 지정).
        mask = _scopeMask(meta, corpCode, stockCode, sourceKind)
        constraintMask = semanticScopeMask(meta, constraintPlan)
        if constraintMask is not None:
            mask = constraintMask if mask is None else (mask & constraintMask)
        plain = _scoreBM25(idx, tokens)
        if mask is not None:
            plain = np.where(mask, plain, 0.0)
        if hasExpansion:
            boosted = _scoreBM25(idx, list(weights), weights=weights)
            if mask is not None:
                boosted = np.where(mask, boosted, 0.0)
            fused = _rrfFuse(plain, boosted)
        else:
            fused = plain
        candidateScores: dict[int, float] = {
            int(i): float(fused[i]) for i in np.argsort(-fused)[:candidateLimit] if fused[i] > 0
        }
        if reportLabels:
            reportScores = _scoreReportLabelEvidence(meta, reportLabels, query)
            if mask is not None:
                reportScores = np.where(mask, reportScores, 0.0)
            for i in np.argsort(-reportScores)[:candidateLimit]:
                score = float(reportScores[i])
                if score <= 0:
                    continue
                index = int(i)
                candidateScores[index] = max(candidateScores.get(index, 0.0), score)
        constraintScores = scoreSemanticConstraintEvidence(meta, constraintPlan, mask=mask)
        for i in np.argsort(-constraintScores)[:candidateLimit]:
            score = float(constraintScores[i])
            if score <= 0:
                continue
            index = int(i)
            candidateScores[index] = max(candidateScores.get(index, 0.0), score)
        seenSegmentKeys: set[tuple[str, str, str]] = set()
        for i, score in sorted(candidateScores.items(), key=lambda item: item[1], reverse=True):
            row = meta.row(int(i), named=True)
            rowKey = _rowKey(row)
            if rowKey in seenSegmentKeys:
                continue
            seenSegmentKeys.add(rowKey)
            key = (row["rcept_no"], row["section_order"])
            if name == "main" and key in deltaKeys:
                continue
            if name == "delta":
                deltaKeys.add(key)
            allHits.append({**row, "score": score, "segment": name})

    if not allHits:
        return pl.DataFrame()

    if eventTitleRerank:
        allHits = _rerankEventTitleHits(query, allHits, routerModel)
    elif bodySemanticRerank:
        allHits = _rerankBodySemanticHits(query, allHits, routerModel)
    allHits = rankBySemanticConstraints(allHits, constraintPlan)

    # corp/stock 스코프는 _scopeMask 로 랭킹 전 적용 완료 — 사후 필터 불필요.
    df = pl.DataFrame(allHits).sort("score", descending=True)
    return _resolveResultUrl(df).head(limit)


def _candidateLimit(query: str, limit: int) -> int:
    """Return a wider candidate pool for generic event-title filing queries."""
    del query
    return min(EVENT_TITLE_CANDIDATE_CAP, max(limit * EVENT_TITLE_CANDIDATE_MULTIPLIER, EVENT_TITLE_CANDIDATE_FLOOR))


def _bodyCandidateLimit(query: str, limit: int) -> int:
    """Return a wider candidate pool for body/footnote semantic queries."""
    del query
    return min(
        BODY_SEMANTIC_CANDIDATE_CAP,
        max(limit * BODY_SEMANTIC_CANDIDATE_MULTIPLIER, BODY_SEMANTIC_CANDIDATE_FLOOR),
    )


def _prefersEventTitleRerank(query: str) -> bool:
    """Whether the query asks for a disclosure event/title rather than body evidence."""
    text = " ".join(str(query or "").strip().lower().split())
    if not text:
        return False
    if any(term in text for term in _BODY_SEMANTIC_TERMS) and "제출" not in text:
        return False
    return any(term in text for term in _EVENT_TITLE_TERMS)


def _prefersBodySemanticRerank(query: str) -> bool:
    """Whether the query needs topic-focused body reranking.

    Formal body/footnote queries already stay on the content lane through the
    API router. Do not rerank them here; the stronger reranker is for natural
    topic questions that ask whether a body text mentions or discusses a theme.
    """
    text = " ".join(str(query or "").strip().lower().split())
    if not text or any(term in text for term in _NEWS_INTENT_TERMS):
        return False
    if any(term in text for term in _EVENT_TITLE_STRONG_TERMS):
        return False
    return any(term in text for term in _BODY_SEMANTIC_CUES)


def _rerankEventTitleHits(query: str, hits: list[dict], routerModel: dict | None) -> list[dict]:
    """Rerank broad BM25 candidates with report title, event canon, and freshness signals."""
    if not hits:
        return hits
    weights = _eventTitleWeights(query, routerModel)
    reportLabels = _reportLabels(query)
    dates = [_dateOrdinal(row.get("rcept_dt")) for row in hits]
    maxDate = max(dates or [0])
    minDate = min([value for value in dates if value] or [maxDate])
    dateSpan = max(1, maxDate - minDate)
    genericDecision = _genericDecisionQuery(query)
    ranked: list[dict] = []
    total = max(1, len(hits))
    for index, row in enumerate(hits):
        title = _titleText(row)
        evidence = _bodyEvidenceText(row)
        titleScore = _weightedTokenOverlap(title, weights)
        reportScore = _reportMatchScore(title, evidence, reportLabels)
        decisionScore = _decisionTitleScore(title, genericDecision=genericDecision, query=query)
        sourceScore = 1.0 if str(row.get("source") or "") == "allFilings" else 0.0
        dateValue = _dateOrdinal(row.get("rcept_dt"))
        freshness = (dateValue - minDate) / dateSpan if dateValue else 0.0
        originalRank = 1.0 - (index / total)
        finalScore = (
            float(row.get("score") or 0.0)
            + 8.0 * titleScore
            + 60.0 * reportScore
            + 7.0 * decisionScore
            + 1.5 * sourceScore
            + 1.5 * freshness
            + 2.0 * originalRank
        )
        ranked.append({**row, "score": finalScore})
    return sorted(ranked, key=lambda row: float(row.get("score") or 0.0), reverse=True)


def _rerankBodySemanticHits(query: str, hits: list[dict], routerModel: dict | None) -> list[dict]:
    """Rerank body queries toward actual filing body/panel evidence, not news or boilerplate titles."""
    if not hits:
        return hits
    weights = _bodySemanticWeights(query, routerModel)
    reportLabels = _reportLabels(query)
    ranked: list[dict] = []
    total = max(1, len(hits))
    for index, row in enumerate(hits):
        source = str(row.get("source") or "")
        title = _titleText(row)
        evidence = _bodyEvidenceText(row)
        sourceScore = _bodySourceScore(source)
        reportScore = _reportMatchScore(title, evidence, reportLabels)
        surface = " ".join((title, evidence))
        overlap = _weightedTokenOverlap(surface, weights)
        exactTopicScore = _bodyExactTopicScore(query, surface)
        bodyMarker = 1.0 if any(term in evidence or term in title for term in _BODY_SEMANTIC_TERMS) else 0.0
        boilerplatePenalty = _bodyBoilerplatePenalty(query, title)
        originalRank = 1.0 - (index / total)
        finalScore = (
            3.0 * sourceScore
            + 6.0 * reportScore
            + 5.0 * overlap
            + 6.0 * exactTopicScore
            + 1.5 * bodyMarker
            + 1.0 * originalRank
            - boilerplatePenalty
            + 0.01 * float(row.get("score") or 0.0)
        )
        ranked.append({**row, "score": finalScore})
    return sorted(ranked, key=lambda row: float(row.get("score") or 0.0), reverse=True)


def _eventTitleWeights(query: str, routerModel: dict | None) -> dict[str, float]:
    weights = _expansionWeights(query, routerModel)
    if _genericDecisionQuery(query):
        for token in tokenizeContent("결정 주요사항보고서"):
            weights[token] = max(weights.get(token, 0.0), 0.7)
    if "수주" in query or "납품" in query:
        for token in tokenizeContent("단일판매 공급계약 공급계약체결 단일판매공급계약체결"):
            weights[token] = max(weights.get(token, 0.0), 3.0)
    return weights


def _bodySemanticWeights(query: str, routerModel: dict | None) -> dict[str, float]:
    """Return query weights for body evidence, downweighting broad UI/request words."""
    weights = _expansionWeights(query, routerModel)
    for token in tokenizeContent(" ".join(_BODY_GENERIC_WEIGHT_TERMS)):
        if token in weights:
            weights[token] = min(weights[token], 0.15)
    return weights


def _genericDecisionQuery(query: str) -> bool:
    text = str(query or "")
    return ("공시" in text or "원문" in text) and not any(term in text for term in _NON_DECISION_TERMS)


def _weightedTokenOverlap(text: str, weights: dict[str, float]) -> float:
    tokens = set(tokenizeContent(text))
    if not tokens:
        return 0.0
    return sum(float(weight) for token, weight in weights.items() if token in tokens)


def _bodyExactTopicScore(query: str, text: str) -> float:
    """Score exact topical surfaces for body semantic queries."""
    q = str(query or "")
    t = str(text or "").lower()
    if not q or not t:
        return 0.0
    score = 0.0
    for token in _BODY_ASCII_RE.findall(q):
        term = token.lower()
        if len(term) >= 2 and term in t:
            score += 1.5 if len(term) <= 2 else 2.0
    for run in _BODY_HANGUL_RE.findall(q):
        if len(run) >= 4 and run in text:
            score += 2.0
        elif len(run) >= 3 and run in text:
            score += 1.0
    return score


def _reportLabels(query: str) -> tuple[str, ...]:
    text = str(query or "").lower()
    return tuple(label for label, aliases in _REPORT_TERMS if any(alias in text for alias in aliases))


def _reportTitleScore(title: str, reportLabels: tuple[str, ...]) -> float:
    if not reportLabels:
        return 0.0
    text = str(title or "").lower()
    return 1.0 if any(_reportLabelMatches(text, label) for label in reportLabels) else -1.0


def _reportMatchScore(title: str, evidence: str, reportLabels: tuple[str, ...]) -> float:
    """Score requested report labels, falling back to body text when title metadata is absent."""
    if not reportLabels:
        return 0.0
    if _hasUsableReportSurface(title):
        return _reportTitleScore(title, reportLabels)
    text = _evidenceReportHeader(evidence)
    return 1.0 if any(_reportLabelMatches(text, label) for label in reportLabels) else -1.0


def _scoreReportLabelEvidence(meta: pl.DataFrame, reportLabels: tuple[str, ...], query: str) -> np.ndarray:
    """Build a small candidate lane for report-label queries with missing title metadata."""
    scores = np.zeros(meta.height, dtype=np.float32)
    if not reportLabels or meta.height == 0:
        return scores
    columns = set(meta.columns)
    titleCols = [col for col in ("report_nm", "section_title", "title") if col in columns]
    evidenceCols = [col for col in ("evidenceText", "text", "snippet") if col in columns]
    if not titleCols and not evidenceCols:
        return scores
    frame = _reportSurfaceFrame(meta, titleCols=titleCols, evidenceCols=evidenceCols)
    aliases = _reportAliases(reportLabels)
    titleMatches = _containsAnyExpr("_title", aliases)
    evidenceMatches = _containsAnyExpr("_evidenceReportHead", aliases)
    usableTitle = (pl.col("_titleNorm") != "") & ~pl.col("_titleNorm").is_in(["0", "none", "nan", "null"])
    eligibleExpr = (usableTitle & titleMatches) | (~usableTitle & evidenceMatches)
    if "제출" in str(query or ""):
        eligibleExpr = eligibleExpr & (
            pl.col("_title").str.contains("제출", literal=True).fill_null(False)
            | pl.col("_evidenceSubmitHead").str.contains("제출", literal=True).fill_null(False)
        )
    eligible = frame.filter(eligibleExpr)
    if eligible.height == 0:
        return scores
    dateValues = [_dateOrdinal(value) for value in frame["_date"].to_list()]
    maxDate = max(dateValues or [0])
    minDate = min([value for value in dateValues if value] or [maxDate])
    dateSpan = max(1, maxDate - minDate)
    for row in eligible.select("_i", "_source", "_date", "_title", "_evidence").iter_rows(named=True):
        index = int(row["_i"])
        source = str(row.get("_source") or "")
        sourceScore = 1.0 if source in {"panel", "edgar-panel", "edgarPanel"} else 0.5
        dateValue = _dateOrdinal(row.get("_date"))
        freshness = (dateValue - minDate) / dateSpan if dateValue else 0.0
        surface = f"{row.get('_title') or ''} {row.get('_evidence') or ''}"[:1200]
        literalScore = _bodyExactTopicScore(query, surface)
        scores[index] = np.float32(80.0 + 3.0 * sourceScore + 2.0 * freshness + 8.0 * literalScore)
    return scores


def _reportLabelMatches(text: str, label: str) -> bool:
    aliases = next((aliases for candidate, aliases in _REPORT_TERMS if candidate == label), ())
    return label.lower() in text or any(alias in text for alias in aliases)


def _hasUsableReportSurface(title: str) -> bool:
    text = " ".join(str(title or "").strip().lower().split())
    return bool(text) and text not in {"0", "none", "nan", "null"}


def _evidenceReportHeader(evidence: str) -> str:
    return str(evidence or "").lower()[:140]


def _reportAliases(reportLabels: tuple[str, ...]) -> tuple[str, ...]:
    aliases: list[str] = []
    for label in reportLabels:
        for alias in (label, *next((items for candidate, items in _REPORT_TERMS if candidate == label), ())):
            text = str(alias or "").lower()
            if text and text not in aliases:
                aliases.append(text)
    return tuple(aliases)


def _concatTextExpr(columns: list[str]) -> pl.Expr:
    if not columns:
        return pl.lit("")
    return pl.concat_str([pl.col(col).cast(pl.Utf8).fill_null("") for col in columns], separator=" ").str.to_lowercase()


def _reportSurfaceFrame(meta: pl.DataFrame, *, titleCols: list[str], evidenceCols: list[str]) -> pl.DataFrame:
    cacheKey = id(meta)
    cached = _REPORT_SURFACE_CACHE.get(cacheKey)
    # id(meta) 는 GC 후 재사용된다. height 만 확인하면, 우연히 크기가 같은 다른 프레임의
    # stale 결과를 돌려줘 엉뚱한 랭킹이 나온다(로컬 단독은 캐시가 비어 안 터지고 CI xdist 에서만
    # 교차오염으로 점수가 0 이 되던 버그). meta 참조를 함께 들고 identity 로 검증한다.
    # 캐시가 참조를 쥐고 있는 동안 그 id 는 재사용되지 않으므로 충돌 자체가 원천 차단된다.
    if cached is not None and cached[0] is meta:
        return cached[1]
    columns = set(meta.columns)
    frame = meta.select(
        [
            _concatTextExpr(titleCols).alias("_title"),
            _concatTextExpr(evidenceCols).alias("_evidence"),
            pl.col("source").cast(pl.Utf8).fill_null("").alias("_source")
            if "source" in columns
            else pl.lit("").alias("_source"),
            pl.col("rcept_dt").cast(pl.Utf8).fill_null("").alias("_date")
            if "rcept_dt" in columns
            else pl.lit("").alias("_date"),
        ]
    ).with_row_index("_i")
    frame = frame.with_columns(
        pl.col("_title").str.strip_chars().alias("_titleNorm"),
        pl.col("_evidence").str.slice(0, 140).alias("_evidenceReportHead"),
        pl.col("_evidence").str.slice(0, 400).alias("_evidenceSubmitHead"),
    )
    if len(_REPORT_SURFACE_CACHE) > 8:
        _REPORT_SURFACE_CACHE.clear()
    _REPORT_SURFACE_CACHE[cacheKey] = (meta, frame)
    return frame


def _containsAnyExpr(column: str, needles: tuple[str, ...]) -> pl.Expr:
    expr = pl.lit(False)
    for needle in needles:
        expr = expr | pl.col(column).str.contains(needle, literal=True).fill_null(False)
    return expr


def _rowKey(row: dict) -> tuple[str, str, str]:
    return (
        str(row.get("sourceRef") or row.get("source") or ""),
        str(row.get("rcept_no") or ""),
        str(row.get("section_order") or ""),
    )


def _bodySourceScore(source: str) -> float:
    if source in {"panel", "edgar-panel", "edgarPanel"}:
        return 1.2
    if source == "allFilings":
        return 0.5
    if source == "news" or source.lower().startswith("news"):
        return -2.0
    return 0.0


def _titleText(row: dict) -> str:
    return " ".join(str(row.get(key) or "") for key in ("report_nm", "section_title", "title"))


def _bodyEvidenceText(row: dict) -> str:
    return " ".join(str(row.get(key) or "") for key in ("evidenceText", "text", "snippet"))


def _bodyBoilerplatePenalty(query: str, title: str) -> float:
    titleText = str(title or "")
    if not any(term in titleText for term in _NON_BODY_REPORT_TITLES):
        return 0.0
    text = str(query or "")
    if any(term in text for term in _NON_BODY_REPORT_TITLES):
        return 0.0
    return 20.0


def _decisionTitleScore(title: str, *, genericDecision: bool, query: str) -> float:
    if "결정" not in query and not genericDecision:
        return 0.0
    score = 1.0 if "결정" in title else 0.0
    if genericDecision and any(term in title for term in _DECISION_RESULT_TERMS):
        score -= 1.0
    return score


def _dateOrdinal(value: object) -> int:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())[:8]
    if len(digits) != 8:
        return 0
    try:
        year = int(digits[:4])
        month = int(digits[4:6])
        day = int(digits[6:8])
    except ValueError:
        return 0
    return year * 372 + month * 31 + day
