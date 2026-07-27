"""Community Skill Market lookup.

Skill Market data is a remote, untrusted community layer.  It is intentionally
kept separate from builtin Skill OS specs so package installs do not inherit
community content as official DartLab knowledge.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_MARKET_URL = "https://eddmpython.github.io/dartlab/skills/market/marketIndex.json"
TRUST_ORDER = {
    "marketCurated": 4,
    "builtinCandidate": 3,
    "marketRunnable": 2,
    "marketDraft": 1,
    "blocked": 0,
}


@dataclass(frozen=True)
class MarketSkillMatch:
    """Community market search result."""

    item: dict[str, Any]
    score: float
    reasons: list[str] = field(default_factory=list)

    def toDict(self) -> dict[str, Any]:
        """Return a JSON-ready dict."""

        return asdict(self)


def defaultMarketUrl() -> str:
    """Return configured Skill Market index URL."""

    return os.environ.get("DARTLAB_SKILL_MARKET_URL") or DEFAULT_MARKET_URL


def emptyMarketIndex() -> dict[str, Any]:
    """Return the canonical empty market index shape."""

    return {
        "meta": {
            "schemaVersion": "1",
            "source": "dartlab-skill-market",
            "generatedAt": None,
            "skillCount": 0,
            "trustPolicy": "community market entries are untrusted until curated",
        },
        "skills": [],
    }


def loadMarketIndex(
    *,
    url: str | None = None,
    path: str | Path | None = None,
    timeout: float = 10.0,
) -> dict[str, Any]:
    """Load a Skill Market index from local path or remote URL."""

    if path is not None:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return _normalizeMarketIndex(data)

    target = url or defaultMarketUrl()
    try:
        request = urllib.request.Request(
            target,
            headers={
                "Accept": "application/json",
                "User-Agent": "dartlab-skill-market/1",
            },
        )
        # noqa 사유: target 은 운영자가 정하는 자리다. 예전 주석은 "fixed URL" 이라 적었는데
        # 사실이 아니었다. 호출자가 넘긴 주소를 그대로 열었고 그 인자가 도구 스키마에
        # 광고돼 있었다. 지금은 도구가 인자를 받지 않고 환경변수와 기본값만 쓴다.
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return emptyMarketIndex()
    try:
        return _normalizeMarketIndex(json.loads(payload))
    except json.JSONDecodeError:
        return emptyMarketIndex()


def searchMarketSkills(
    query: str,
    *,
    limit: int = 8,
    includeDraft: bool = True,
    marketData: dict[str, Any] | None = None,
) -> list[MarketSkillMatch]:
    """Search community Skill Market entries.

    Builtin Skill OS search must run first.  This function only searches the
    untrusted community layer and returns trust tier in each result payload.
    """

    data = _normalizeMarketIndex(marketData or loadMarketIndex())
    terms = _terms(query)
    matches: list[MarketSkillMatch] = []
    for item in data.get("skills", []):
        trustTier = str(item.get("trustTier") or item.get("state") or "marketDraft")
        if not includeDraft and trustTier == "marketDraft":
            continue
        score, reasons = _scoreMarketItem(item, terms, query=query)
        if score > 0 or not terms:
            matches.append(MarketSkillMatch(item=item, score=score, reasons=reasons))
    matches.sort(
        key=lambda match: (
            match.score,
            TRUST_ORDER.get(str(match.item.get("trustTier")), 0),
            str(match.item.get("updatedAt") or ""),
        ),
        reverse=True,
    )
    return matches[: max(1, int(limit or 8))]


def isRunnableMarketSkill(item: dict[str, Any]) -> bool:
    """Return whether the market item may be proposed as runnable."""

    return str(item.get("trustTier")) in {"marketRunnable", "marketCurated", "builtinCandidate"}


def _normalizeMarketIndex(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        return emptyMarketIndex()
    out = emptyMarketIndex()
    meta = data.get("meta")
    if isinstance(meta, dict):
        out["meta"].update(meta)
    rawSkills = data.get("skills")
    if isinstance(rawSkills, list):
        out["skills"] = [item for item in rawSkills if isinstance(item, dict) and item.get("id")]
    out["meta"]["skillCount"] = len(out["skills"])
    return out


def _scoreMarketItem(item: dict[str, Any], terms: list[str], *, query: str) -> tuple[float, list[str]]:
    haystacks = {
        "id": item.get("id"),
        "title": item.get("title"),
        "intent": item.get("intent"),
        "summary": item.get("summary"),
        "inputs": item.get("inputs"),
        "dataSources": item.get("dataSources"),
        "procedure": item.get("procedure"),
        "outputs": item.get("outputs"),
        "outputSchema": item.get("outputSchema"),
        "criteria": item.get("criteria"),
        "forbidden": item.get("forbidden"),
        "completionCriteria": item.get("completionCriteria"),
        "tags": item.get("tags"),
        "mappedBuiltinSkills": item.get("mappedBuiltinSkills"),
        "missingDetails": item.get("missingDetails"),
    }
    score = 0.0
    reasons: list[str] = []
    normalizedQuery = query.lower()
    for term in terms:
        for name, raw in haystacks.items():
            field = _text(raw).lower()
            if term in field:
                weight = _fieldWeight(name)
                if normalizedQuery and normalizedQuery in field:
                    weight += 2.0
                score += weight
                reasons.append(f"{name}:{term}")
    tier = str(item.get("trustTier") or "marketDraft")
    score += TRUST_ORDER.get(tier, 0) * 0.2
    return score, reasons


def _fieldWeight(name: str) -> float:
    if name == "id":
        return 4.0
    if name == "title":
        return 3.5
    if name in {"intent", "summary"}:
        return 2.75
    if name in {
        "inputs",
        "dataSources",
        "procedure",
        "outputs",
        "outputSchema",
        "criteria",
        "forbidden",
        "completionCriteria",
        "mappedBuiltinSkills",
    }:
        return 1.75
    return 1.0


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(_text(v) for v in value.values())
    if isinstance(value, list):
        return " ".join(_text(v) for v in value)
    return str(value)


def _terms(query: str) -> list[str]:
    terms: list[str] = []
    for raw in str(query or "").replace("/", " ").replace(".", " ").replace("-", " ").split():
        term = raw.lower().strip()
        if len(term) < 2:
            continue
        terms.append(term)
        if _containsHangul(term) and len(term) >= 3:
            terms.extend(term[index : index + 2] for index in range(len(term) - 1))
    return list(dict.fromkeys(terms))


def _containsHangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)
