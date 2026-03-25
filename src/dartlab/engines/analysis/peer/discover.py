"""TF-IDF 멀티토픽 peer 발견.

사업보고서 텍스트 유사도로 진짜 경쟁그룹을 발견한다.
Hoberg-Phillips (2010, 2016) 한국 적용.

실험 근거: 098-001~005 (ARI 0.14→멀티토픽 상관 0.27, Jaccard 0.68)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import numpy as np
import polars as pl

from dartlab.engines.analysis.peer.types import PeerMatch, PeerResult

_log = logging.getLogger(__name__)

TOPIC_CONFIG = {
    "bizOverview": {
        "titles": ["II. 사업의 내용", "1. 사업의 개요", "2. 주요 제품 및 서비스"],
        "fallback": "사업",
        "weight": 0.50,
    },
    "segments": {
        "titles": ["5. 사업부문별 정보", "4. 매출 및 수주상황"],
        "fallback": "부문|매출|수주",
        "weight": 0.25,
    },
    "contracts": {
        "titles": ["3. 원재료 및 생산설비"],
        "fallback": "원재료|생산|설비|연구개발",
        "weight": 0.15,
    },
    "risk": {
        "titles": [],
        "fallback": "위험|리스크|파생",
        "weight": 0.10,
    },
}

_EXCLUDE_INDUSTRIES = {"기타 금융업", "신탁업", "집합투자업"}
_EXCLUDE_NAME_PATTERNS = ("지주", "홀딩스", "Holdings")
_MIN_TEXT_LEN = 100

_NUM_PATTERN = re.compile(
    r"\d[\d,\.]*\s*(원|억|조|만|천|백|%|백만|십억|달러|USD|KRW|Won)"
)
_DIGITS_PATTERN = re.compile(r"\b\d[\d,\.]*\b")
_TABLE_PATTERN = re.compile(r"[│├└┌─┐┘┤┬┴┼━┃╋\(\)\[\]\{\}]+")
_SPACES_PATTERN = re.compile(r"\s+")


def _cleanText(text: str) -> str:
    """숫자/테이블 문자 제거."""
    text = re.sub(r"<[^>]+>", " ", text)
    text = _NUM_PATTERN.sub(" ", text)
    text = _DIGITS_PATTERN.sub(" ", text)
    text = _TABLE_PATTERN.sub(" ", text)
    text = _SPACES_PATTERN.sub(" ", text).strip()
    return text


def _extractTopicTexts(df: pl.DataFrame) -> dict[str, str]:
    """docs DataFrame에서 topic별 텍스트 추출."""
    bizDf = df.filter(pl.col("report_type").str.contains("사업"))
    if bizDf.height == 0:
        return {}
    latestYear = bizDf["year"].cast(str).sort(descending=True).first()
    bizDf = bizDf.filter(pl.col("year") == latestYear)

    result = {}
    for topicKey, cfg in TOPIC_CONFIG.items():
        filtered = bizDf.filter(pl.col("section_title").is_in(cfg["titles"]))
        if filtered.height == 0 and cfg["fallback"]:
            filtered = bizDf.filter(
                pl.col("section_title").str.contains(cfg["fallback"])
            )
        if filtered.height == 0:
            continue
        texts = filtered["section_content"].drop_nulls().to_list()
        combined = _cleanText("\n".join(str(t) for t in texts if t))
        if len(combined) >= _MIN_TEXT_LEN:
            result[topicKey] = combined
    return result


def _isExcluded(name: str, industry: str) -> bool:
    if industry in _EXCLUDE_INDUSTRIES:
        return True
    return any(pat in name for pat in _EXCLUDE_NAME_PATTERNS)


def discover(
    stockCode: str,
    *,
    topK: int = 5,
    minSimilarity: float = 0.01,
) -> PeerResult:
    """종목코드 → TF-IDF 멀티토픽 peer 발견.

    Company 객체를 로드하지 않고 docs parquet 직접 접근 (OOM 방지).
    """
    from scipy.sparse import hstack
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    from dartlab.core.dataLoader import loadData
    from dartlab.engines.gather.listing import getKindList

    kindDf = getKindList()
    kindMap: dict[str, tuple[str, str]] = {}
    for row in kindDf.iter_rows(named=True):
        code = row["종목코드"]
        name = row["회사명"]
        industry = row["업종"]
        if not _isExcluded(name, industry):
            kindMap[code] = (name, industry)

    if stockCode not in kindMap:
        targetName = stockCode
        kindMap[stockCode] = (stockCode, "")
    else:
        targetName = kindMap[stockCode][0]

    # 대상 종목 docs 로드
    _DOCS_COLS = ["year", "report_type", "section_title", "section_content"]
    targetDf = loadData(stockCode, category="docs", columns=_DOCS_COLS)
    if targetDf is None or targetDf.is_empty():
        return PeerResult(stockCode=stockCode, name=targetName)

    targetTexts = _extractTopicTexts(targetDf)
    if "bizOverview" not in targetTexts:
        return PeerResult(stockCode=stockCode, name=targetName)

    # 모든 종목 docs 로드 — 경량 배치
    _log.info("peer discovery: %d 종목 텍스트 수집", len(kindMap))
    allTexts: dict[str, dict[str, str]] = {stockCode: targetTexts}
    dataDir = Path(loadData.__module__).parent  # fallback

    # loadData를 사용한 배치 로드
    for code in kindMap:
        if code == stockCode:
            continue
        try:
            df = loadData(code, category="docs", columns=_DOCS_COLS)
        except (FileNotFoundError, OSError):
            continue
        if df is None or df.is_empty():
            continue
        texts = _extractTopicTexts(df)
        if "bizOverview" in texts:
            allTexts[code] = texts

    codes = sorted(allTexts.keys())
    if len(codes) < 10:
        return PeerResult(stockCode=stockCode, name=targetName)

    # topic별 TF-IDF → 가중 결합
    topicMatrices = {}
    for topicKey, cfg in TOPIC_CONFIG.items():
        textList = [allTexts[c].get(topicKey, "") for c in codes]
        vec = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            min_df=3,
            max_df=0.90,
            sublinear_tf=True,
            token_pattern=r"(?u)\b[가-힣a-zA-Z]{2,}\b",
        )
        mat = vec.fit_transform(textList)
        topicMatrices[topicKey] = mat * cfg["weight"]

    combinedMatrix = hstack(list(topicMatrices.values()))
    targetIdx = codes.index(stockCode)

    # 대상 종목과 전체의 유사도
    targetVec = combinedMatrix[targetIdx]
    similarities = cosine_similarity(targetVec, combinedMatrix).flatten()
    similarities[targetIdx] = 0  # 자기 자신 제외

    # 상위 K개
    topIndices = np.argsort(similarities)[-topK:][::-1]
    peers = []
    for idx in topIndices:
        sim = float(similarities[idx])
        if sim < minSimilarity:
            break
        peerCode = codes[idx]
        peerName = kindMap.get(peerCode, (peerCode,))[0]
        peers.append(PeerMatch(
            stockCode=peerCode,
            name=peerName,
            similarity=round(sim, 4),
        ))

    topicCoverage = {k: k in targetTexts for k in TOPIC_CONFIG}

    return PeerResult(
        stockCode=stockCode,
        name=targetName,
        peers=peers,
        topicCoverage=topicCoverage,
    )
