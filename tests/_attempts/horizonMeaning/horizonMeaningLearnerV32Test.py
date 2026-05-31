"""Horizon Meaning Learner V32 - coordinate experience line.

V32 실제 기록
--------------
아이디어:
    stem 을 0~1 수평선 위 문자 좌표로 놓고, 의미는 stem 자체가 아니라 문서 안에서 그 stem 이 경험한
    앞/뒤/거리/순서/이웃 stem 의 경험 sketch 로 본다. `사과는` 은 marker 를 떼면 stem `사과` 이고,
    raw 표면 좌표는 Unicode code point 고정 폭 나열로 `0.493244428445716...` 처럼 표현된다.

    V32 는 이 아이디어를 단일 파일에서 직접 검증한다. dense vector, embedding, GPU, LLM 호출 없이
    code point 좌표 atom, horizon 경험 atom, 이웃 sketch 를 다시 순서대로 나열한 experience-line atom 만
    만든 뒤 역인덱스식 posting 으로 surface route 와 문서 검색을 수행한다.

시도 방법:
    1. `data/dart/allFilings`, `data/dart/docs` parquet 에서 focus term 주변 meaning window 를 균형 수집한다.
    2. `stemCoordinateAtoms()` 는 code point prefix/suffix/char-ngram atom 을 만든다. `손실충당금` 과
       `대손충당금` 은 suffix `충당금` 뿐 아니라 char `손` 도 공유하고, `복구충당금` 은 suffix 만 공유한다.
    3. 1차 pass 는 stem occurrence 주변의 좌/우 거리, marker, 이웃 coordinate cell 을 `hx:*` 로 누적한다.
    4. stem 별 `hx:*` 를 IDF top-k sketch 로 압축한다.
    5. 2차 pass 는 이웃 stem 의 sketch hash 를 좌/우 순서대로 `xp:*`, `el:*` 로 다시 나열한다.
    6. coordinate overlap 이 있는 surface 끼리는 `xp/el` 을 아주 약하게 relay 한다. 이는 수동 family lock 이
       아니라 "수평선상 가까운 stem 의 경험 공유" 가 가능한지 보는 일반 메커니즘이다.
    7. 검색은 query surface 를 target surface 로 route 한 뒤, route signature atom posting 으로 unit 을 찾는다.

실행:
    uv run python -X utf8 -m py_compile tests/_attempts/horizonMeaning/horizonMeaningLearnerV32Test.py

    $env:DARTLAB_HORIZON_V32_MAX_FILES_PER_SOURCE='8'
    $env:DARTLAB_HORIZON_V32_MAX_RECORDS_PER_SOURCE='180'
    $env:DARTLAB_HORIZON_V32_MAX_UNITS='1200'
    $env:DARTLAB_HORIZON_V32_MAX_WINDOWS_PER_RECORD='2'
    uv run python -X utf8 tests/_attempts/horizonMeaning/horizonMeaningLearnerV32Test.py

판정 기준:
    수동 family lock, `충당/충당금` 전용 rescue atom, target 별 예외처리 없이
    positive route 4/4, bad accepted 0/7 을 목표로 한다. 특히 `손실충당금 -> 대손충당금` 은
    accepted 여야 하고, `복구충당금 -> 대손충당금`, `대출채권 -> 매출채권` 은 accepted 되면 안 된다.

결과:
    py_compile 통과.

    smoke(1,200 units, allFilings 600 + docs 600):
        model seconds=57.1, surfaces=7,063, coordKeys=55,727.
        `손실충당금 -> 대손충당금` 은 top1 이 대손충당금이었지만
        score=0.159/xp0.006/el0.004/cx0.435 로 accepted=False 였다.
        `복구충당금 -> 대손충당금` 은 score=2.189/xp0.666/el0.400/cx0.391 로 bad accepted=True.
        `대출채권 -> 매출채권`, `당기순이익 -> 영업이익` 도 bad accepted=True.
        positiveHits=2/4, badAccepted=3/7, searchTop1=4/5, totalSeconds=57.2.

    larger smoke(4,000 units, allFilings 2,000 + docs 2,000):
        model seconds=135.1, surfaces=11,316, coordKeys=84,909.
        `손실충당금 -> 대손충당금` 은 top1 이 대손충당금이었지만
        score=0.153/xp0.004/el0.003/cx0.435 로 accepted=False 였다.
        `복구충당금 -> 대손충당금` 은 score=2.124/xp0.660/el0.365/cx0.391 로 bad accepted=True.
        `대출채권 -> 매출채권`, `당기순이익 -> 영업이익` 도 bad accepted=True.
        positiveHits=1/4, badAccepted=3/7, searchTop1=4/5, totalSeconds=135.3.

판정:
    실패/진단 성공. Unicode 좌표 수평선과 ordered experience-line 은 `영업손익 -> 영업이익` 같은 일부
    alias 와 검색 후보 생성에는 작동했지만, 목표였던 loss-allowance 의미는 아직 경험으로 학습되지 않았다.
    `손실충당금` 은 대손충당금으로 top1 route 되지만 경험 overlap 이 거의 없어 accepted 가 아니며, 반대로
    `복구충당금` 은 넓은 충당금/대손충당금 표 경험을 공유해 강하게 오염된다. 다음 실험은 단순 experience
    공유가 아니라 same-suffix surface 들을 서로 contrast 해 "공유 경험" 과 "역할을 가르는 경험" 을 분리해야 한다.
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

MAX_FILES_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V32_MAX_FILES_PER_SOURCE", "30"))
MAX_RECORDS_PER_SOURCE = int(os.environ.get("DARTLAB_HORIZON_V32_MAX_RECORDS_PER_SOURCE", "700"))
MAX_UNITS = int(os.environ.get("DARTLAB_HORIZON_V32_MAX_UNITS", "8000"))
MAX_WINDOWS_PER_RECORD = int(os.environ.get("DARTLAB_HORIZON_V32_MAX_WINDOWS_PER_RECORD", "3"))
WINDOW_CHARS = int(os.environ.get("DARTLAB_HORIZON_V32_WINDOW_CHARS", "720"))
RADIUS = int(os.environ.get("DARTLAB_HORIZON_V32_RADIUS", "6"))
SKETCH_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V32_SKETCH_LIMIT", "32"))
SIGNATURE_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V32_SIGNATURE_LIMIT", "96"))
POSTING_LIMIT = int(os.environ.get("DARTLAB_HORIZON_V32_POSTING_LIMIT", "1200"))
ROUTE_MIN_SCORE = float(os.environ.get("DARTLAB_HORIZON_V32_ROUTE_MIN_SCORE", "0.075"))
ROUTE_MIN_EXPERIENCE = float(os.environ.get("DARTLAB_HORIZON_V32_ROUTE_MIN_EXPERIENCE", "0.018"))

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
FOCUS_TERMS = tuple(
    sorted(
        set(TARGETS)
        | {surface for surface, _ in POSITIVE_PROBES}
        | {surface for surface, _ in NEGATIVE_PROBES}
        | {term for _, terms in RELATIONS for term in terms}
        | {"기대신용손실", "손상", "채권", "손실", "대손"},
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


def relKeys(text: str) -> set[str]:
    return {f"rel:{name}" for name, terms in RELATIONS if any(term in text for term in terms)}


def tokenize(unit: Unit) -> Cache:
    stems: list[str] = []
    markers: list[str] = []
    occs: list[Occ] = []
    for pos, match in enumerate(TOKEN_RE.finditer(unit.text)):
        raw = match.group(0)
        stem, marker = splitStemMarker(raw)
        stem = normStem(stem)
        stems.append(stem)
        markers.append(marker)
        if isContentStem(stem):
            occs.append(Occ(stem, marker, pos))
    terms = set(TOKEN_RE.findall(unit.text)) | relKeys(unit.text)
    return Cache(unit, stems, markers, occs, terms)


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
            pref(query, ("xp:", "hx:", "relay:xp", "relay:hx")), pref(targetSig, ("xp:", "hx:", "relay:xp", "relay:hx"))
        )
        el = cosine(pref(query, ("el:", "relay:el")), pref(targetSig, ("el:", "relay:el")))
        cx = cosine(pref(query, ("cx:",)), pref(targetSig, ("cx:",)))
        score = xp * 2.2 + el * 1.5 + cx * 0.32
        accepted = score >= ROUTE_MIN_SCORE and (xp + el) >= ROUTE_MIN_EXPERIENCE
        rows.append((score, target, xp, el, cx, accepted))
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
    sketches = buildSketches(caches)
    signatures = buildSignatures(caches, sketches)
    model = Model(units, caches, sketches, signatures, coordPostings(signatures), {}, {})
    buildUnitIndex(model)
    print(f"[model] seconds={time.perf_counter() - started:.1f}")
    return model


def preview(rows, limit: int = 3) -> str:
    return " | ".join(
        f"{target}:{score:.3f}/xp{xp:.3f}/el{el:.3f}/cx{cx:.3f}/{'Y' if ok else 'N'}"
        for score, target, xp, el, cx, ok in rows[:limit]
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
        ok = rows[0][1] == expected and rows[0][5]
        pos += int(ok)
        print(f"  {surface}->{expected} ok={ok} {preview(rows)}")
    print("[routes:negative]")
    for surface, forbidden in NEGATIVE_PROBES:
        rows = route(surface, model)
        targetRow = next(row for row in rows if row[1] == forbidden)
        isBad = rows[0][1] == forbidden and targetRow[5]
        bad += int(isBad)
        print(
            f"  {surface}-/->{forbidden} bad={isBad} forbidden={targetRow[0]:.3f}/xp{targetRow[2]:.3f}/el{targetRow[3]:.3f} top={preview(rows, 2)}"
        )
    searchOk = 0
    print("[search]")
    for query, expected, polarity in SEARCH_PROBES:
        rows = route(querySurface(query), model)
        hits = search(query, polarity, model)
        ok = rows[0][1] == expected
        searchOk += int(ok)
        print(
            f"  {query} route={rows[0][1]} expected={expected} ok={ok} accepted={rows[0][5]} hit={(hits[0][0] if hits else 0):.2f} text={(hits[0][3] if hits else '')}"
        )
    print(
        f"[summary] positiveHits={pos}/{len(POSITIVE_PROBES)} badAccepted={bad}/{len(NEGATIVE_PROBES)} searchTop1={searchOk}/{len(SEARCH_PROBES)} totalSeconds={time.perf_counter() - started:.1f}"
    )


if __name__ == "__main__":
    main()
