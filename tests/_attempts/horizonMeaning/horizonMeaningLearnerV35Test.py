"""Horizon Meaning Learner V35 - raw substring pseudo-occurrence bridge.

V35 실제 기록
--------------
아이디어:
    V33 은 same-suffix 오염을 막아 `손실충당금 -> 대손충당금` 을 살리고 bad accepted 를 0/7 로 낮췄다.
    남은 실패는 `외상매출금 -> 매출채권` 이다. 이 둘은 suffix family 가 아니라 compound 내부 substring
    (`매출`) 을 공유하고, 의미상 같은 장면에서 함께 쓰이는 표면이다. 반면 `매출액` 도 `매출` 을 공유하므로
    단순 substring overlap 만 쓰면 revenue 쪽으로 빨려간다.

    V34 는 tokenized surface pair 로 compound co-view 를 세었다. 그러나 DART 표/문장 안에서는
    `외상매출채권` 처럼 붙은 복합어가 raw 본문에는 있어도 surface pair 로 분리되지 않는다. 그 결과
    `외상매출금 -> 매출채권` 은 route top1 까지는 올라왔지만 compound path 가 0 으로 남아 accepted=False 였다.

    V35 는 긴 raw token 안의 의미 후보 substring 을 pseudo-occurrence 로 추가한다. pseudo surface 는 같은 위치의
    앞뒤 stem 경험을 물려받고, substring 포함 관계가 pair index 에 들어가므로 `외상매출채권` 안의
    `매출채권` 같은 bridge 가 tokenized pair 없이도 학습된다. 특정 alias map 이 아니라 현재 query/target
    후보군의 coordinate compound gram 과 겹치는 raw substring 만 올리는 방식이다.

시도 방법:
    1. V33 의 coordinate experience line, suffix cohort contrast, nonSuffix resonance gate 를 유지한다.
    2. 긴 token 에서 length 4~8 substring 을 뽑되, query/target 후보군의 coordinate compound gram 과 충분히
       겹치는 substring 만 pseudo-occurrence 로 추가한다.
    3. pseudo surface 는 원 token 과 같은 position 에 놓고 horizon/experience-line sketch 를 학습시킨다.
    4. pseudo surface 까지 포함한 pair index 로 compound association 을 다시 계산한다.
    5. route score 에 compound association 을 보조 신호로 더하고, accepted 조건에도 compound path 를 추가한다.

실행:
    uv run python -X utf8 -m py_compile tests/_attempts/horizonMeaning/horizonMeaningLearnerV35Test.py

    $env:DARTLAB_HORIZON_V35_MAX_FILES_PER_SOURCE='8'
    $env:DARTLAB_HORIZON_V35_MAX_RECORDS_PER_SOURCE='180'
    $env:DARTLAB_HORIZON_V35_MAX_UNITS='1200'
    $env:DARTLAB_HORIZON_V35_MAX_WINDOWS_PER_RECORD='2'
    uv run python -X utf8 tests/_attempts/horizonMeaning/horizonMeaningLearnerV35Test.py

판정 기준:
    수동 alias map 없이 `외상매출금 -> 매출채권` 이 route top1/accepted 로 올라와야 한다. 동시에 V33 의
    `손실충당금 -> 대손충당금` accepted 와 badAccepted 0/7 을 유지해야 한다.

결과:
    py_compile 통과.

    1,200 units(allFilings 600 + docs 600, files=8, rows=180, windows=2):
        rawBridge surfaces=303, rawBridge hits=7,230, surfaces=7,339, coordKeys=56,059,
        suffixCohorts=7,285, coordGrams=25,633, surfacePairs=645,379, compoundGrams=29,557,
        modelSeconds=42.7, totalSeconds=42.8.
        `외상매출금 -> 매출채권` accepted=True(score=0.145, cp=0.056) 로 V34 의 남은 실패를 해결했다.
        `영업손익 -> 영업이익`, `현금성자산 -> 현금및현금성자산`, `손실충당금 -> 대손충당금` 도 accepted=True.
        negative 7개 forbidden target 은 모두 bad=False.
        positiveHits=4/4, badAccepted=0/7, searchTop1=5/5.

    4,000 units(allFilings 2,000 + docs 2,000, files=20, rows=600, windows=3):
        rawBridge surfaces=418, rawBridge hits=21,067, surfaces=11,788, coordKeys=86,413,
        suffixCohorts=11,270, coordGrams=39,149, surfacePairs=1,204,337, compoundGrams=46,230,
        modelSeconds=118.1, totalSeconds=118.4.
        `외상매출금 -> 매출채권` accepted=True(score=1.291, cp=0.692) 로 유지됐다.
        `손실충당금 -> 대손충당금` accepted=True(score=0.116), `복구충당금 -> 대손충당금` 은 suffix gate 로
        accepted=False, `대출채권 -> 매출채권` 도 accepted=False.
        positiveHits=4/4, badAccepted=0/7, searchTop1=5/5.

판정:
    성공적인 구조 개선. raw substring pseudo-occurrence 를 experience/pair index 에 넣자 tokenized surface pair 로는
    보이지 않던 compound role bridge 가 열렸고, V33/V34 의 same-suffix 오염 방어도 유지됐다.
    단, 4,000-unit 에서는 `외상매출금` route 2순위 `매출액` 도 accepted=True(score=0.283, cp=0.127) 로 열려
    top-k 오염 위험이 남았다. 다음 실험은 accepted 를 top1 margin 또는 role-specific bridge precision 으로
    보정해야 한다.
"""

from __future__ import annotations

import hashlib
import html
import math
import os
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[3]
ALL_FILINGS_DIR = ROOT / "data" / "dart" / "allFilings"
DOCS_DIR = ROOT / "data" / "dart" / "docs"

MAX_FILES_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V35_MAX_FILES_PER_SOURCE", "30"))
MAX_RECORDS_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V35_MAX_RECORDS_PER_SOURCE", "700"))
MAX_UNITS = int(os.environ.get("DARTLAB_HORIZON_V35_MAX_UNITS", "8000"))
MAX_WINDOWS_PER_RECORD = int(os.environ.get("DARTLAB_HORIZON_V35_MAX_WINDOWS_PER_RECORD", "3"))
WINDOW_CHARS = int(os.environ.get("DARTLAB_HORIZON_V35_WINDOW_CHARS", "720"))
RADIUS = int(os.environ.get("DARTLAB_HORIZON_V35_RADIUS", "6"))
SKETCH_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V35_SKETCH_LIMIT", "32"))
SIGNATURE_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V35_SIGNATURE_LIMIT", "96"))
POSTING_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V35_POSTING_LIMIT", "1200"))
ROUTE_MIN_SCORE = float(os.environ.get("DARTLAB_HORIZON_V35_ROUTE_MIN_SCORE", "0.075"))
ROUTE_MIN_EXPERIENCE = float(os.environ.get("DARTLAB_HORIZON_V35_ROUTE_MIN_EXPERIENCE", "0.018"))
COHORT_SUFFIX_MIN = int(os.environ.get("DARTLAB_HORIZON_V35_COHORT_SUFFIX_MIN", "2"))
COHORT_SUFFIX_MAX = int(os.environ.get("DARTLAB_HORIZON_V35_COHORT_SUFFIX_MAX", "4"))
CONTRAST_COMMON_RATIO = float(os.environ.get("DARTLAB_HORIZON_V35_CONTRAST_COMMON_RATIO", "0.34"))
CONTRAST_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V35_CONTRAST_ACCEPT_MIN", "0.010"))
RESONANCE_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V35_RESONANCE_ACCEPT_MIN", "0.030"))
COMPOUND_ASSOC_ACCEPT_MIN = float(os.environ.get("DARTLAB_HORIZON_V35_COMPOUND_ASSOC_ACCEPT_MIN", "0.045"))
RAW_BRIDGE_MIN_SIM = float(os.environ.get("DARTLAB_HORIZON_V35_RAW_BRIDGE_MIN_SIM", "0.24"))
RAW_BRIDGE_MIN_SIZE = int(os.environ.get("DARTLAB_HORIZON_V35_RAW_BRIDGE_MIN_SIZE", "4"))
RAW_BRIDGE_MAX_SIZE = int(os.environ.get("DARTLAB_HORIZON_V35_RAW_BRIDGE_MAX_SIZE", "8"))
RAW_BRIDGE_MAX_TOKEN = int(os.environ.get("DARTLAB_HORIZON_V35_RAW_BRIDGE_MAX_TOKEN", "18"))

TOKEN_RE = re.compile(r"[가-힣A-Za-z0-9]+")
TAG_RE = re.compile(r"<[^>]+>")
SPACE_RE = re.compile(r"\s+")

MARKER_SUFFIXES = tuple(
    sorted(
        {
            "으로부터",
            "로부터",
            "에서는",
            "에게서",
            "까지",
            "부터",
            "으로",
            "에서",
            "에게",
            "보다",
            "처럼",
            "하고",
            "이며",
            "이고",
            "이다",
            "했다",
            "하였다",
            "하는",
            "하여",
            "해서",
            "한다",
            "된다",
            "됐다",
            "되며",
            "되는",
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "로",
            "과",
            "와",
            "도",
            "만",
        },
        key=len,
        reverse=True,
    )
)

TARGETS = ("매출채권", "재고자산", "차입금", "영업이익", "매출액", "현금및현금성자산", "대손충당금")
POSITIVE_PROBES = (
    ("외상매출금", "매출채권"),
    ("영업손익", "영업이익"),
    ("현금성자산", "현금및현금성자산"),
    ("손실충당금", "대손충당금"),
)
NEGATIVE_PROBES = (
    ("대출채권", "매출채권"),
    ("현금배당금", "현금및현금성자산"),
    ("당기순이익", "영업이익"),
    ("복구충당금", "대손충당금"),
    ("대출채권", "대손충당금"),
    ("현금성자산", "대손충당금"),
    ("당기순이익", "대손충당금"),
)
SEARCH_PROBES = (
    ("매출채권 증가", "매출채권", "increase"),
    ("외상매출금 감소", "매출채권", "decrease"),
    ("영업손익 감소", "영업이익", "decrease"),
    ("현금성자산 증가", "현금및현금성자산", "increase"),
    ("손실충당금 증가", "대손충당금", "increase"),
)
RELATIONS = (
    ("increase", ("증가", "상승", "확대", "성장", "늘", "증대", "개선")),
    ("decrease", ("감소", "하락", "축소", "줄", "저하")),
    ("delay", ("지연", "회수지연", "연체", "부실", "위험")),
)


def focusSurfaceFragments(values: set[str]) -> set[str]:
    fragments: set[str] = set()
    for raw in values:
        value = re.sub(r"[^가-힣A-Za-z0-9]", "", raw)
        if len(value) < 4:
            continue
        for size in range(4, min(7, len(value)) + 1):
            for index in range(0, len(value) - size + 1):
                fragments.add(value[index : index + size])
    return fragments


BASE_FOCUS_SURFACES = (
    set(TARGETS) | {surface for surface, _ in POSITIVE_PROBES} | {surface for surface, _ in NEGATIVE_PROBES}
)
FOCUS_TERMS = tuple(
    sorted(
        BASE_FOCUS_SURFACES
        | focusSurfaceFragments(BASE_FOCUS_SURFACES)
        | {term for _, terms in RELATIONS for term in terms}
        | {"기대신용손실", "손상", "채권", "손실", "대손"},
        key=len,
        reverse=True,
    )
)
BRIDGE_SEED_SURFACES = tuple(
    sorted(
        BASE_FOCUS_SURFACES | focusSurfaceFragments(BASE_FOCUS_SURFACES),
        key=len,
        reverse=True,
    )
)
FOCUS_REGEX = "|".join(re.escape(term) for term in FOCUS_TERMS)
STOP_STEMS = {
    "그리고",
    "또한",
    "또는",
    "대한",
    "관련",
    "해당",
    "경우",
    "보고서",
    "사업",
    "회사",
    "연결",
    "당사",
    "현재",
    "전기",
    "당기",
    "기말",
    "기초",
    "천원",
    "백만원",
}


@dataclass(frozen=True)
class Unit:
    unitId: int
    source: str
    ref: str
    text: str


@dataclass(frozen=True)
class Occ:
    surface: str
    marker: str
    position: int


@dataclass
class Cache:
    unit: Unit
    stems: list[str]
    markers: list[str]
    occs: list[Occ]
    bridgeSurfaces: set[str]
    terms: set[str]


@dataclass
class Model:
    units: list[Unit]
    caches: list[Cache]
    sketches: dict[str, Counter[str]]
    signatures: dict[str, Counter[str]]
    coordPostings: dict[str, list[str]]
    unitSignatures: dict[int, Counter[str]]
    unitPostings: dict[str, list[int]]
    cohortAtomDf: dict[str, Counter[str]]
    cohortSurfaceCounts: Counter[str]
    coordGramDf: Counter[str]
    surfaceDf: Counter[str]
    surfacePairDf: Counter[tuple[str, str]]
    compoundGramPostings: dict[str, list[str]]


def stableHash(value: str, size: int = 12) -> str:
    return hashlib.blake2b(value.encode("utf-8"), digest_size=8).hexdigest()[:size]


def cleanText(raw: object) -> str:
    return SPACE_RE.sub(" ", html.unescape(TAG_RE.sub(" ", "" if raw is None else str(raw)))).strip()


def splitStemMarker(token: str) -> tuple[str, str]:
    for suffix in MARKER_SUFFIXES:
        if token.endswith(suffix) and len(token) > len(suffix) + 1:
            return token[: -len(suffix)], suffix
    return token, ""


@lru_cache(maxsize=200_000)
def normStem(value: str) -> str:
    stem, _ = splitStemMarker(value)
    return re.sub(r"[^가-힣A-Za-z0-9]", "", stem)


def isContentStem(stem: str) -> bool:
    return len(stem) >= 2 and stem not in STOP_STEMS and not stem.isdigit() and bool(re.search(r"[가-힣A-Za-z]", stem))


@lru_cache(maxsize=200_000)
def codePath(stem: str) -> str:
    return ".".join(f"{ord(ch):05d}" for ch in stem) + ".$"


def coordDecimal(stem: str, size: int = 24) -> str:
    return "0." + "".join(f"{ord(ch):05d}" for ch in normStem(stem))[:size]


@lru_cache(maxsize=200_000)
def coordAtoms(stem: str) -> frozenset[str]:
    value = normStem(stem)
    if not value:
        return frozenset()
    points = [f"{ord(ch):05d}" for ch in value]
    atoms = {f"cx:full:{stableHash(codePath(value))}"}
    for size in range(1, min(4, len(points)) + 1):
        atoms.add(f"cx:p{size}:{stableHash('.'.join(points[:size]))}")
        atoms.add(f"cx:s{size}:{stableHash('.'.join(points[-size:]))}")
    for size in range(1, min(4, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            atoms.add(f"cx:g{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(atoms)


@lru_cache(maxsize=200_000)
def coordCells(stem: str) -> tuple[str, ...]:
    cells = [atom.replace("cx:", "cc:", 1) for atom in sorted(coordAtoms(stem))]
    return tuple(cells[:12])


def meaningAtom(atom: str) -> bool:
    return atom.startswith(
        (
            "xp:",
            "el:",
            "hx:",
            "relay:xp",
            "relay:el",
            "relay:hx",
            "compoundProxy:xp",
            "compoundProxy:el",
            "compoundProxy:hx",
        )
    )


@lru_cache(maxsize=200_000)
def suffixCohortKeys(stem: str) -> tuple[str, ...]:
    value = normStem(stem)
    if len(value) <= COHORT_SUFFIX_MIN:
        return tuple()
    keys: list[str] = []
    for size in range(COHORT_SUFFIX_MIN, min(COHORT_SUFFIX_MAX, len(value) - 1) + 1):
        keys.append(f"sf:{size}:{stableHash(codePath(value[-size:]))}")
    return tuple(keys)


@lru_cache(maxsize=200_000)
def coordResonanceGrams(stem: str) -> frozenset[str]:
    value = normStem(stem)
    grams: set[str] = set()
    for size in range(1, min(4, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            grams.add(f"rg:{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(grams)


def longestCommonSuffixSize(left: str, right: str) -> int:
    leftValue = normStem(left)
    rightValue = normStem(right)
    size = 0
    for lch, rch in zip(reversed(leftValue), reversed(rightValue)):
        if lch != rch:
            break
        size += 1
    return size


def nonSuffixResonanceGrams(surface: str, target: str) -> tuple[set[str], set[str]]:
    suffixSize = longestCommonSuffixSize(surface, target)
    left = normStem(surface)
    right = normStem(target)
    if suffixSize >= COHORT_SUFFIX_MIN:
        left = left[:-suffixSize] or left
        right = right[:-suffixSize] or right
    return set(coordResonanceGrams(left)), set(coordResonanceGrams(right))


@lru_cache(maxsize=200_000)
def compoundGrams(stem: str) -> frozenset[str]:
    value = normStem(stem)
    grams: set[str] = set()
    for size in range(2, min(5, len(value)) + 1):
        for index in range(0, len(value) - size + 1):
            grams.add(f"cg:{size}:{stableHash(codePath(value[index : index + size]))}")
    return frozenset(grams)


def nonSuffixCompoundOverlap(surface: str, target: str) -> float:
    if longestCommonSuffixSize(surface, target) >= COHORT_SUFFIX_MIN:
        return 0.0
    left = compoundGrams(surface)
    right = compoundGrams(target)
    if not left or not right:
        return 0.0
    overlap = left & right
    if not overlap:
        return 0.0
    return len(overlap) / math.sqrt(len(left) * len(right))


def compoundSimilarity(surface: str, proxy: str) -> float:
    left = compoundGrams(surface)
    right = compoundGrams(proxy)
    if not left or not right:
        return 0.0
    overlap = left & right
    if len(overlap) < 2:
        return 0.0
    return len(overlap) / math.sqrt(len(left) * len(right))


@lru_cache(maxsize=200_000)
def rawBridgeSeedMatch(surface: str) -> bool:
    value = normStem(surface)
    if len(value) < RAW_BRIDGE_MIN_SIZE or not isContentStem(value):
        return False
    grams = compoundGrams(value)
    if not grams:
        return False
    for seed in BRIDGE_SEED_SURFACES:
        seedValue = normStem(seed)
        if not seedValue or seedValue == value:
            continue
        if value in seedValue or seedValue in value:
            return True
        seedGrams = compoundGrams(seedValue)
        overlap = grams & seedGrams
        if len(overlap) >= 2:
            score = len(overlap) / math.sqrt(len(grams) * len(seedGrams))
            if score >= RAW_BRIDGE_MIN_SIM:
                return True
    return False


@lru_cache(maxsize=200_000)
def rawBridgeSubsurfaces(stem: str) -> tuple[str, ...]:
    value = normStem(stem)
    if len(value) < RAW_BRIDGE_MIN_SIZE + 1 or len(value) > RAW_BRIDGE_MAX_TOKEN:
        return tuple()
    out: set[str] = set()
    maxSize = min(RAW_BRIDGE_MAX_SIZE, len(value))
    for size in range(RAW_BRIDGE_MIN_SIZE, maxSize + 1):
        for index in range(0, len(value) - size + 1):
            part = value[index : index + size]
            if part == value:
                continue
            if rawBridgeSeedMatch(part):
                out.add(part)
    return tuple(sorted(out, key=lambda item: (-len(item), item))[:10])


def compoundProxySurfaces(surface: str, model: Model) -> list[tuple[float, str]]:
    scores: Counter[str] = Counter()
    for gram in compoundGrams(surface):
        for proxy in model.compoundGramPostings.get(gram, ())[:260]:
            if proxy == normStem(surface):
                continue
            score = compoundSimilarity(surface, proxy)
            if score >= 0.24:
                scores[proxy] = max(scores[proxy], score)
    return sorted(((score, proxy) for proxy, score in scores.items()), reverse=True)[:8]


def pairKey(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right)))


def buildSurfacePairIndex(caches: list[Cache]) -> tuple[Counter[str], Counter[tuple[str, str]]]:
    surfaceDf: Counter[str] = Counter()
    surfacePairDf: Counter[tuple[str, str]] = Counter()
    for cache in caches:
        surfaces = sorted({occ.surface for occ in cache.occs})
        surfaceDf.update(surfaces)
        if len(surfaces) < 2:
            continue
        for leftIndex, left in enumerate(surfaces):
            for right in surfaces[leftIndex + 1 :]:
                surfacePairDf[pairKey(left, right)] += 1
    return surfaceDf, surfacePairDf


def buildCompoundGramPostings(surfaces: list[str]) -> dict[str, list[str]]:
    postings: dict[str, list[str]] = defaultdict(list)
    for surface in sorted(surfaces):
        for gram in compoundGrams(surface):
            postings[gram].append(surface)
    return dict(postings)


def directPairAssociation(surface: str, target: str, model: Model) -> float:
    pairCount = model.surfacePairDf.get(pairKey(normStem(surface), normStem(target)), 0)
    if pairCount <= 0:
        return 0.0
    leftDf = max(1, model.surfaceDf.get(normStem(surface), 0))
    rightDf = max(1, model.surfaceDf.get(normStem(target), 0))
    total = max(1, len(model.caches))
    pmi = math.log(1.0 + (pairCount * total) / math.sqrt(leftDf * rightDf))
    support = math.log1p(pairCount)
    return pmi * support / 8.0


def compoundAssociation(surface: str, target: str, model: Model) -> float:
    overlap = nonSuffixCompoundOverlap(surface, target)
    if overlap <= 0:
        return 0.0
    surfaceGrams = compoundGrams(surface)
    targetGrams = compoundGrams(target)
    shared = surfaceGrams & targetGrams
    querySpecific = surfaceGrams - shared
    targetSpecific = targetGrams - shared
    proxyScores: list[float] = []
    for gram in sorted(shared):
        for proxy in model.compoundGramPostings.get(gram, ())[:260]:
            if proxy in {normStem(surface), normStem(target)}:
                continue
            proxyGrams = compoundGrams(proxy)
            if not (querySpecific & proxyGrams):
                continue
            if targetSpecific and not (targetSpecific & proxyGrams):
                continue
            proxyOverlap = nonSuffixCompoundOverlap(surface, proxy)
            if proxyOverlap < 0.18:
                continue
            association = directPairAssociation(proxy, target, model)
            if association <= 0:
                continue
            proxyScores.append(overlap * proxyOverlap * association * 0.62)
    for proxySimilarity, proxy in compoundProxySurfaces(surface, model):
        proxyGrams = compoundGrams(proxy)
        if not (querySpecific & proxyGrams):
            continue
        proxyTargetOverlap = nonSuffixCompoundOverlap(proxy, target)
        if proxyTargetOverlap <= 0:
            continue
        association = directPairAssociation(proxy, target, model)
        if association <= 0:
            continue
        proxyScores.append(overlap * proxySimilarity * proxyTargetOverlap * association * 2.10)
    proxy = sum(sorted(proxyScores, reverse=True)[:4])
    return proxy


def hasRawCompoundBridge(surface: str, model: Model) -> bool:
    return any(compoundAssociation(surface, target, model) >= COMPOUND_ASSOC_ACCEPT_MIN * 0.35 for target in TARGETS)


def buildContrastIndexes(
    signatures: dict[str, Counter[str]],
) -> tuple[dict[str, Counter[str]], Counter[str], Counter[str]]:
    cohortAtomDf: dict[str, Counter[str]] = defaultdict(Counter)
    cohortSurfaceCounts: Counter[str] = Counter()
    coordGramDf: Counter[str] = Counter()
    for surface, signature in signatures.items():
        for gram in coordResonanceGrams(surface):
            coordGramDf[gram] += 1
        keys = suffixCohortKeys(surface)
        if not keys:
            continue
        atoms = {atom for atom in signature if meaningAtom(atom)}
        for key in keys:
            cohortSurfaceCounts[key] += 1
            cohortAtomDf[key].update(atoms)
    return dict(cohortAtomDf), cohortSurfaceCounts, coordGramDf


def cohortCommonRatio(surface: str, atom: str, model: Model) -> float:
    ratios: list[float] = []
    for key in suffixCohortKeys(surface):
        surfaceCount = model.cohortSurfaceCounts.get(key, 0)
        if surfaceCount <= 1:
            continue
        ratios.append(model.cohortAtomDf.get(key, Counter()).get(atom, 0) / surfaceCount)
    return max(ratios) if ratios else 0.0


def contrastSignature(surface: str, signature: Counter[str], model: Model) -> Counter[str]:
    out: Counter[str] = Counter()
    for atom, weight in signature.items():
        if not meaningAtom(atom):
            continue
        ratio = cohortCommonRatio(surface, atom, model)
        if ratio >= CONTRAST_COMMON_RATIO:
            out[atom] += weight * 0.10
        else:
            out[atom] += weight * (1.15 - ratio)
    return out


def coordResonance(surface: str, target: str, model: Model) -> float:
    left, right = nonSuffixResonanceGrams(surface, target)
    if not left or not right:
        return 0.0
    universe = max(1, len(model.signatures))
    overlap = left & right
    if not overlap:
        return 0.0

    def gramWeight(gram: str) -> float:
        return math.log(1.0 + universe / (1.0 + model.coordGramDf.get(gram, 0)))

    numerator = sum(gramWeight(gram) for gram in overlap)
    leftNorm = math.sqrt(sum(gramWeight(gram) ** 2 for gram in left))
    rightNorm = math.sqrt(sum(gramWeight(gram) ** 2 for gram in right))
    if leftNorm <= 0 or rightNorm <= 0:
        return 0.0
    return numerator / (leftNorm * rightNorm)


def relKeys(text: str) -> set[str]:
    return {f"rel:{name}" for name, terms in RELATIONS if any(term in text for term in terms)}


def tokenize(unit: Unit) -> Cache:
    stems: list[str] = []
    markers: list[str] = []
    occs: list[Occ] = []
    bridgeSurfaces: set[str] = set()
    for pos, match in enumerate(TOKEN_RE.finditer(unit.text)):
        raw = match.group(0)
        stem, marker = splitStemMarker(raw)
        stem = normStem(stem)
        stems.append(stem)
        markers.append(marker)
        if isContentStem(stem):
            occs.append(Occ(stem, marker, pos))
            for bridgeSurface in rawBridgeSubsurfaces(stem):
                bridgeSurfaces.add(bridgeSurface)
                occs.append(Occ(bridgeSurface, "~", pos))
    terms = set(TOKEN_RE.findall(unit.text)) | relKeys(unit.text)
    terms.update(bridgeSurfaces)
    return Cache(unit, stems, markers, occs, bridgeSurfaces, terms)


def windows(raw: object) -> list[str]:
    text = cleanText(raw)
    if not text:
        return []
    hits: list[int] = []
    for term in FOCUS_TERMS:
        start = 0
        while len(hits) < MAX_WINDOWS_PER_RECORD * 10:
            index = text.find(term, start)
            if index < 0:
                break
            hits.append(index)
            start = index + max(1, len(term))
    out: list[str] = []
    seen: set[tuple[int, int]] = set()
    half = WINDOW_CHARS // 2
    for index in sorted(set(hits)):
        left = max(0, index - half)
        right = min(len(text), index + half)
        key = (left // 80, right // 80)
        if key in seen:
            continue
        seen.add(key)
        chunk = text[left:right].strip()
        if len(chunk) >= 24:
            out.append(chunk)
        if len(out) >= MAX_WINDOWS_PER_RECORD:
            break
    return out


def parquetRows(source: str, folder: Path):
    files = sorted(folder.glob("*.parquet")) if source == "allFilings" else sorted(folder.rglob("*.parquet"))
    for path in files[:MAX_FILES_PER_SOURCE]:
        schema = set(pl.scan_parquet(str(path)).collect_schema().names())
        if source == "allFilings":
            cols = [col for col in ("stock_code", "rcept_no", "report_nm", "content_raw") if col in schema]
            textCol = "content_raw"
        else:
            cols = [
                col
                for col in (
                    "stock_code",
                    "rcept_no",
                    "report_type",
                    "section_title",
                    "section_content_mixed",
                    "section_content",
                )
                if col in schema
            ]
            textCol = "section_content_mixed" if "section_content_mixed" in cols else "section_content"
        if textCol not in cols:
            continue
        frame = (
            pl.scan_parquet(str(path))
            .select(cols)
            .filter(pl.col(textCol).fill_null("").str.contains(FOCUS_REGEX))
            .limit(MAX_RECORDS_PER_SOURCE)
            .collect()
        )
        for row in frame.iter_rows(named=True):
            yield row, textCol


def collectUnits() -> list[Unit]:
    units: list[Unit] = []
    counts: Counter[str] = Counter()
    perSource = max(1, math.ceil(MAX_UNITS / 2))
    started = time.perf_counter()
    for source, folder in (("allFilings", ALL_FILINGS_DIR), ("docs", DOCS_DIR)):
        for row, textCol in parquetRows(source, folder):
            title = row.get("report_nm") or row.get("section_title") or row.get("report_type") or ""
            ref = f"{source}:{row.get('stock_code') or ''}:{row.get('rcept_no') or ''}:{title}"
            for chunk in windows(row.get(textCol)):
                units.append(Unit(len(units), source, ref, chunk))
                counts[source] += 1
                if len(units) >= MAX_UNITS or counts[source] >= perSource:
                    break
            if len(units) >= MAX_UNITS or counts[source] >= perSource:
                break
    print(f"[collect] units={len(units)} sourceCounts={dict(counts)} seconds={time.perf_counter() - started:.1f}")
    return units


def horizonAtoms(pos: int, stems: list[str], markers: list[str]) -> set[str]:
    atoms = {f"hx:selfMarker:{markers[pos] if pos < len(markers) and markers[pos] else '_'}"}
    ordered: list[tuple[int, str]] = []
    for index in range(max(0, pos - RADIUS), min(len(stems), pos + RADIUS + 1)):
        if index == pos or not isContentStem(stems[index]):
            continue
        dist = index - pos
        side = "L" if dist < 0 else "R"
        bucket = min(abs(dist), 4)
        cells = coordCells(stems[index])
        for cell in cells[:8]:
            atoms.add(f"hx:n:{side}:{bucket}:{cell}")
        atoms.add(f"hx:m:{side}:{bucket}:{markers[index] if index < len(markers) and markers[index] else '_'}")
        ordered.append((dist, cells[0] if cells else "_"))
    left = [cell for dist, cell in sorted(ordered) if dist < 0]
    right = [cell for dist, cell in sorted(ordered) if dist > 0]
    if left and right:
        atoms.add(f"hx:lr:{left[-1]}>{right[0]}")
    return atoms


def buildSketches(caches: list[Cache]) -> dict[str, Counter[str]]:
    raw: dict[str, Counter[str]] = defaultdict(Counter)
    for cache in caches:
        for occ in cache.occs:
            raw[occ.surface].update(horizonAtoms(occ.position, cache.stems, cache.markers))
    df: Counter[str] = Counter()
    for counter in raw.values():
        df.update(counter.keys())
    total = max(1, len(raw))
    sketches: dict[str, Counter[str]] = {}
    for stem, counter in raw.items():
        rows = []
        for atom, count in counter.items():
            rows.append((math.sqrt(count) * math.log(1.0 + total / (1.0 + df[atom])), atom))
        selected = Counter({atom: score for score, atom in sorted(rows, reverse=True)[:SKETCH_LIMIT]})
        if selected:
            sketches[stem] = selected
    print(f"[sketch] stems={len(sketches)} raw={len(raw)}")
    return sketches


def sketchCell(stem: str, sketches: dict[str, Counter[str]]) -> str:
    if stem in sketches:
        atom, _ = sketches[stem].most_common(1)[0]
        return f"sk:{stableHash(atom)}"
    return f"sk:cold:{stableHash(codePath(stem))}"


def lineAtoms(pos: int, stems: list[str], markers: list[str], sketches: dict[str, Counter[str]]) -> set[str]:
    atoms: set[str] = set()
    stem = stems[pos]
    for atom, _ in sketches.get(stem, Counter()).most_common(6):
        atoms.add(f"xp:self:{stableHash(atom)}")
    cells: dict[int, str] = {}
    for index in range(max(0, pos - RADIUS), min(len(stems), pos + RADIUS + 1)):
        if not isContentStem(stems[index]):
            continue
        cells[index] = sketchCell(stems[index], sketches)
        if index == pos:
            continue
        dist = index - pos
        side = "L" if dist < 0 else "R"
        bucket = min(abs(dist), 4)
        for atom, _ in sketches.get(stems[index], Counter()).most_common(4):
            atoms.add(f"xp:n:{side}:{bucket}:{stableHash(atom)}")
    for start in range(pos - 2, pos + 1):
        idxs = [start, start + 1, start + 2]
        if all(index in cells for index in idxs):
            atoms.add(
                f"el:tri:{'.'.join(str(index - pos) for index in idxs)}:{'>'.join(cells[index] for index in idxs)}"
            )
    if pos - 1 in cells and pos in cells and pos + 1 in cells:
        atoms.add(f"el:lr:{cells[pos - 1]}>{cells[pos]}>{cells[pos + 1]}")
    return atoms


def weightCounters(raw: dict[str, Counter[str]]) -> dict[str, Counter[str]]:
    df: Counter[str] = Counter()
    for counter in raw.values():
        df.update(counter.keys())
    total = max(1, len(raw))
    weighted: dict[str, Counter[str]] = {}
    for surface, counter in raw.items():
        rows = []
        for atom, count in counter.items():
            lane = (
                1.7
                if atom.startswith("xp:")
                else 1.5
                if atom.startswith("el:")
                else 1.0
                if atom.startswith("hx:")
                else 0.35
            )
            rows.append((math.sqrt(float(count)) * math.log(1.0 + total / (1.0 + df[atom])) * lane, atom))
        selected = Counter({atom: score for score, atom in sorted(rows, reverse=True)[:SIGNATURE_LIMIT]})
        for atom, count in counter.items():
            if atom.startswith("cx:"):
                selected[atom] = max(float(selected.get(atom, 0.0)), float(count) * 0.35)
        weighted[surface] = selected
    return weighted


def coordPostings(signatures: dict[str, Counter[str]]) -> dict[str, list[str]]:
    postings: dict[str, list[str]] = defaultdict(list)
    for surface, signature in signatures.items():
        for atom in signature:
            if atom.startswith("cx:"):
                postings[atom].append(surface)
    return dict(postings)


def relayExperience(signatures: dict[str, Counter[str]], postings: dict[str, list[str]]) -> None:
    for surface, signature in list(signatures.items()):
        candidates: Counter[str] = Counter()
        for atom in coordAtoms(surface):
            for other in postings.get(atom, ()):
                if other != surface:
                    candidates[other] += 1
        for other, overlap in candidates.most_common(10):
            scale = min(0.11, 0.012 * overlap)
            for atom, weight in signatures.get(other, Counter()).most_common(24):
                if atom.startswith(("xp:", "el:")):
                    signature[f"relay:{atom}"] += weight * scale


def buildSignatures(caches: list[Cache], sketches: dict[str, Counter[str]]) -> dict[str, Counter[str]]:
    raw: dict[str, Counter[str]] = defaultdict(Counter)
    for cache in caches:
        for occ in cache.occs:
            raw[occ.surface].update(horizonAtoms(occ.position, cache.stems, cache.markers))
            raw[occ.surface].update(lineAtoms(occ.position, cache.stems, cache.markers, sketches))
    for surface, counter in raw.items():
        for atom in coordAtoms(surface):
            counter[atom] += 1
    signatures = weightCounters(raw)
    postings = coordPostings(signatures)
    relayExperience(signatures, postings)
    print(f"[signature] surfaces={len(signatures)} coordKeys={len(postings)}")
    return signatures


def pref(counter: Counter[str], prefixes: tuple[str, ...]) -> Counter[str]:
    return Counter({key: value for key, value in counter.items() if key.startswith(prefixes)})


def cosine(left: Counter[str], right: Counter[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = sum(value * right.get(key, 0.0) for key, value in left.items())
    if overlap <= 0:
        return 0.0
    return overlap / math.sqrt(
        sum(value * value for value in left.values()) * sum(value * value for value in right.values())
    )


def inferSignature(surface: str, model: Model) -> Counter[str]:
    stem = normStem(surface)
    if stem in model.signatures:
        return Counter(model.signatures[stem])
    out = Counter({atom: 0.25 for atom in coordAtoms(stem)})
    if not hasRawCompoundBridge(stem, model):
        candidates: Counter[str] = Counter()
        for atom in coordAtoms(stem):
            for other in model.coordPostings.get(atom, ()):
                candidates[other] += 1
        for other, overlap in candidates.most_common(10):
            scale = min(0.16, 0.02 * overlap)
            for atom, weight in model.signatures.get(other, Counter()).most_common(36):
                if atom.startswith(("xp:", "el:", "hx:", "relay:")):
                    out[atom] += weight * scale
    return out


def route(surface: str, model: Model):
    query = inferSignature(surface, model)
    rows = []
    for target in TARGETS:
        targetSig = inferSignature(target, model)
        xp = cosine(
            pref(query, ("xp:", "hx:", "relay:xp", "relay:hx", "compoundProxy:xp", "compoundProxy:hx")),
            pref(targetSig, ("xp:", "hx:", "relay:xp", "relay:hx", "compoundProxy:xp", "compoundProxy:hx")),
        )
        contrast = cosine(contrastSignature(surface, query, model), contrastSignature(target, targetSig, model))
        el = cosine(
            pref(query, ("el:", "relay:el", "compoundProxy:el")),
            pref(targetSig, ("el:", "relay:el", "compoundProxy:el")),
        )
        cx = cosine(pref(query, ("cx:",)), pref(targetSig, ("cx:",)))
        resonance = coordResonance(surface, target, model)
        compound = compoundAssociation(surface, target, model)
        sameSuffix = longestCommonSuffixSize(surface, target) >= COHORT_SUFFIX_MIN
        suffixNoResonance = sameSuffix and resonance < RESONANCE_ACCEPT_MIN
        commonPenalty = max(0.0, xp - contrast) * 0.75
        suffixPenalty = 0.20 if suffixNoResonance else 0.0
        score = (
            contrast * 2.6 + el * 1.2 + cx * 0.20 + resonance * 0.45 + compound * 1.8 - commonPenalty - suffixPenalty
        )
        accepted = (
            score >= ROUTE_MIN_SCORE
            and not suffixNoResonance
            and (
                (contrast + el) >= ROUTE_MIN_EXPERIENCE
                or (sameSuffix and resonance >= RESONANCE_ACCEPT_MIN)
                or compound >= COMPOUND_ASSOC_ACCEPT_MIN
            )
            and (
                contrast >= CONTRAST_ACCEPT_MIN
                or resonance >= RESONANCE_ACCEPT_MIN
                or compound >= COMPOUND_ASSOC_ACCEPT_MIN
            )
        )
        rows.append((score, target, xp, contrast, el, cx, resonance, compound, accepted))
    return sorted(rows, reverse=True)


def buildUnitIndex(model: Model) -> None:
    signatures: dict[int, Counter[str]] = {}
    postings: dict[str, list[int]] = defaultdict(list)
    for cache in model.caches:
        sig: Counter[str] = Counter()
        for occ in cache.occs:
            sig[f"surf:{occ.surface}"] += 2
            for atom, weight in model.signatures.get(occ.surface, Counter()).most_common(12):
                if atom.startswith(("xp:", "el:", "hx:", "relay:")):
                    sig[atom] += min(weight, 4.0)
        for term in cache.terms:
            if term.startswith("rel:"):
                sig[term] += 3
        signatures[cache.unit.unitId] = sig
        for atom, _ in sig.most_common(80):
            if len(postings[atom]) < POSTING_LIMIT:
                postings[atom].append(cache.unit.unitId)
    model.unitSignatures = signatures
    model.unitPostings = dict(postings)


def buildModel() -> Model:
    started = time.perf_counter()
    units = collectUnits()
    caches = [tokenize(unit) for unit in units]
    print(f"[tokenize] caches={len(caches)}")
    bridgeSurfaceUniverse = {surface for cache in caches for surface in cache.bridgeSurfaces}
    bridgeSurfaceHits = sum(len(cache.bridgeSurfaces) for cache in caches)
    print(f"[rawBridge] surfaces={len(bridgeSurfaceUniverse)} hits={bridgeSurfaceHits}")
    sketches = buildSketches(caches)
    signatures = buildSignatures(caches, sketches)
    cohortAtomDf, cohortSurfaceCounts, coordGramDf = buildContrastIndexes(signatures)
    surfaceDf, surfacePairDf = buildSurfacePairIndex(caches)
    compoundGramPostings = buildCompoundGramPostings(list(signatures))
    print(
        f"[contrast] suffixCohorts={len(cohortSurfaceCounts)} "
        f"cohortAtoms={sum(len(counter) for counter in cohortAtomDf.values())} coordGrams={len(coordGramDf)}"
    )
    print(
        f"[compound] surfaceDf={len(surfaceDf)} surfacePairs={len(surfacePairDf)} compoundGrams={len(compoundGramPostings)}"
    )
    model = Model(
        units,
        caches,
        sketches,
        signatures,
        coordPostings(signatures),
        {},
        {},
        cohortAtomDf,
        cohortSurfaceCounts,
        coordGramDf,
        surfaceDf,
        surfacePairDf,
        compoundGramPostings,
    )
    buildUnitIndex(model)
    print(f"[model] seconds={time.perf_counter() - started:.1f}")
    return model


def preview(rows, limit: int = 3) -> str:
    return " | ".join(
        f"{target}:{score:.3f}/xp{xp:.3f}/ct{contrast:.3f}/el{el:.3f}/cx{cx:.3f}/rs{resonance:.3f}/cp{compound:.3f}/{'Y' if ok else 'N'}"
        for score, target, xp, contrast, el, cx, resonance, compound, ok in rows[:limit]
    )


def querySurface(query: str) -> str:
    relTerms = {term for _, terms in RELATIONS for term in terms}
    stems = [normStem(match.group(0)) for match in TOKEN_RE.finditer(query)]
    stems = [stem for stem in stems if stem and stem not in relTerms and isContentStem(stem)]
    return max(stems, key=len) if stems else normStem(query)


def search(query: str, polarity: str, model: Model):
    surface = querySurface(query)
    best = route(surface, model)[0]
    seed = inferSignature(surface, model) + inferSignature(best[1], model)
    seed[f"surf:{surface}"] += 5
    seed[f"surf:{best[1]}"] += 4
    if polarity:
        seed[f"rel:{polarity}"] += 7
    candidates: Counter[int] = Counter()
    for atom, weight in seed.most_common(80):
        for unitId in model.unitPostings.get(atom, ()):
            candidates[unitId] += min(weight, 4)
    hits = []
    for unitId, base in candidates.most_common(160):
        unitSig = model.unitSignatures.get(unitId, Counter())
        score = cosine(seed, unitSig) * 10 + base * 0.02
        if polarity and f"rel:{polarity}" in unitSig:
            score += 2
        unit = model.units[unitId]
        hits.append((score, best[1], unit.ref, SPACE_RE.sub(" ", unit.text)[:110]))
    return sorted(hits, reverse=True)[:3]


def main() -> None:
    started = time.perf_counter()
    print(
        f"[config] files={MAX_FILES_PER_SOURCE} rows={MAX_RECORDS_PER_SOURCE} units={MAX_UNITS} windows={MAX_WINDOWS_PER_RECORD}"
    )
    model = buildModel()
    print("[coordinate] 사=0.%05d 과=0.%05d 는=0.%05d" % (ord("사"), ord("과"), ord("는")))
    print(f"[coordinate] 사과={coordDecimal('사과')} 사과는(raw)={coordDecimal('사과는')}")
    for surface in ("대손충당금", "손실충당금", "복구충당금", "매출채권", "대출채권"):
        sig = inferSignature(surface, model)
        print(
            f"[surface] {surface} coord={coordDecimal(surface)} sig={len(sig)} xp={sum(k.startswith(('xp:', 'relay:xp')) for k in sig)} el={sum(k.startswith(('el:', 'relay:el')) for k in sig)} cx={sum(k.startswith('cx:') for k in sig)}"
        )
    pos = 0
    bad = 0
    print("[routes:positive]")
    for surface, expected in POSITIVE_PROBES:
        rows = route(surface, model)
        ok = rows[0][1] == expected and rows[0][8]
        pos += int(ok)
        print(f"  {surface}->{expected} ok={ok} {preview(rows)}")
    print("[routes:negative]")
    for surface, forbidden in NEGATIVE_PROBES:
        rows = route(surface, model)
        targetRow = next(row for row in rows if row[1] == forbidden)
        isBad = rows[0][1] == forbidden and targetRow[8]
        bad += int(isBad)
        print(
            f"  {surface}-/->{forbidden} bad={isBad} "
            f"forbidden={targetRow[0]:.3f}/xp{targetRow[2]:.3f}/ct{targetRow[3]:.3f}/el{targetRow[4]:.3f}/cp{targetRow[7]:.3f} "
            f"top={preview(rows, 2)}"
        )
    searchOk = 0
    print("[search]")
    for query, expected, polarity in SEARCH_PROBES:
        rows = route(querySurface(query), model)
        hits = search(query, polarity, model)
        ok = rows[0][1] == expected
        searchOk += int(ok)
        print(
            f"  {query} route={rows[0][1]} expected={expected} ok={ok} accepted={rows[0][8]} hit={(hits[0][0] if hits else 0):.2f} text={(hits[0][3] if hits else '')}"
        )
    print(
        f"[summary] positiveHits={pos}/{len(POSITIVE_PROBES)} badAccepted={bad}/{len(NEGATIVE_PROBES)} searchTop1={searchOk}/{len(SEARCH_PROBES)} totalSeconds={time.perf_counter() - started:.1f}"
    )


if __name__ == "__main__":
    main()
