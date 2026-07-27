"""사용자 누적 interest profile — sessionIndex.db 의 user 발화 전체 스윕.

산출: 자주 등장하는 종목 / 한국어 키워드 / 분석 테마. 결정론적 통계 — 매 답변마다
재계산 안 하고 7 일 TTL 캐시. dialectic user model 의 *prior interest* 절반.

데이터 소스: ~/.dartlab/ai_memory/sessionIndex.db (entries 테이블, role='user').
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import time
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

from dartlab.ai.memory.sessionIndex import sessionIndexPath
from dartlab.core.market import KR_STOCK_CODE_TEXT_RE

_CACHE_DEFAULT = Path.home() / ".dartlab" / "ai_memory" / "userProfile.cache.json"
_CACHE_TTL_SECONDS = 7 * 24 * 3600

# KRX 단축코드 정본 패턴 (영숫자 코드 0008Z0 포함, 기간 "2026Q1" 오탐 배제).
_KR_STOCKCODE_RE = KR_STOCK_CODE_TEXT_RE
_US_TICKER_RE = re.compile(r"\b([A-Z]{2,5})\b")
_KO_TOKEN_RE = re.compile(r"[가-힣]{2,}")

_KO_STOPWORDS = {
    "그리고",
    "그러나",
    "하지만",
    "또한",
    "때문",
    "이거",
    "그것",
    "이것",
    "저것",
    "사용",
    "사용자",
    "지금",
    "여기",
    "이미",
    "이후",
    "이전",
    "동안",
    "위해",
    "통해",
    "대해",
    "관련",
    "있다",
    "없다",
    "있는",
    "없는",
    "같은",
    "어떤",
    "무슨",
    "어떻게",
    "왜",
    "이거",
    "저거",
    "그거",
    "이런",
    "저런",
    "그런",
    "확인",
    "진행",
    "작업",
    "내용",
    "결과",
    "방법",
    "경우",
    "상황",
}

# 분석 테마 분류 — 키워드 → 카테고리 매핑 (가벼운 휴리스틱)
_THEME_KEYWORDS = {
    "재무분석": ["매출", "영업이익", "순이익", "영업현금흐름", "자기자본", "부채비율"],
    "신용도": ["신용", "회사채", "디폴트", "credit", "신용등급", "dcr"],
    "매핑": ["매핑", "mapper", "accountmappings", "표준화"],
    "매크로": ["금리", "환율", "물가", "kospi", "fred", "macro", "ecos"],
    "산업": ["반도체", "바이오", "자동차", "배터리", "industry"],
    "회귀가드": ["회귀", "가드", "lint", "audit", "baseline"],
    "쇼츠": ["쇼츠", "shorts", "릴스", "캐러셀"],
    "스킬": ["skill", "spec", "recipe", "lifecycle"],
}

# 한국 거래소 우상 ticker (FN가이드 등 영문 약어) — US ticker regex 오탐 회피
_KR_FALSE_TICKER = {
    # 일반 영문 약어
    "KR",
    "US",
    "AI",
    "ML",
    "API",
    "CEO",
    "CFO",
    "ETF",
    "SDK",
    "IDE",
    "PER",
    "PBR",
    "ROE",
    "EPS",
    "BPS",
    "CSV",
    "PDF",
    "URL",
    "DOM",
    "OS",
    "DB",
    "TLS",
    "TCP",
    "UDP",
    "HTTP",
    "JSON",
    "YAML",
    "XML",
    "REST",
    "SOAP",
    "GRPC",
    # 영문 강조 단어
    "MSI",
    "NOT",
    "ALL",
    "ONLY",
    "MUST",
    "TODO",
    "FIX",
    "WIP",
    "WHY",
    "HOW",
    "WHAT",
    "WHEN",
    "WHERE",
    "OK",
    "NO",
    "YES",
    "BUT",
    "AND",
    "OR",
    "FOR",
    "THE",
    "TLDR",
    # 코드/로그
    "CLI",
    "GUI",
    "UI",
    "UX",
    "PR",
    "CI",
    "CD",
    "CR",
    "DR",
    "L0",
    "L1",
    "L2",
    "L3",
    "L4",
    "P0",
    "P1",
    "P2",
    "P3",
    "Q1",
    "Q2",
    "Q3",
    "Q4",
    "GET",
    "PUT",
    "POST",
    "HEAD",
    "BODY",
    "SSOT",
    "LLM",
    "TTS",
    "STT",
    "FATAL",
    "ERROR",
    "WARN",
    "INFO",
    "DEBUG",
    "TRACE",
    "ENV",
    "FLUX",
    "BOM",
    "UTF",
    "ASCII",
    "IO",
    "IPC",
    "RPC",
    "ORM",
    "MQ",
    "SLA",
    "KPI",
    "OKR",
    "OOM",
    "VPN",
    "VPS",
    "DNS",
    "IP",
    "SQL",
    "PII",
    "MD",
    "TS",
    "JS",
    "PY",
    "RS",
    "GO",
    # dartlab 특유
    "DART",
    "EDGAR",
    "KRX",
    "KOSPI",
    "KOSDAQ",
    "FRED",
    "ECOS",
    "EDINET",
}

# 영문 ticker 는 최소 출현 횟수 — 누적 turns 대비 노이즈 차단
_MIN_TICKER_COUNT = 30


@dataclass
class UserProfile:
    """사용자 누적 interest profile."""

    total_user_turns: int
    top_stock_codes: list[tuple[str, int]] = field(default_factory=list)
    top_tickers: list[tuple[str, int]] = field(default_factory=list)
    top_ko_tokens: list[tuple[str, int]] = field(default_factory=list)
    theme_breakdown: dict[str, int] = field(default_factory=dict)
    generated_at: float = 0.0


def _cachePath() -> Path:
    env = os.environ.get("DARTLAB_USER_PROFILE_CACHE_PATH")
    return Path(env) if env else _CACHE_DEFAULT


def _loadCache(path: Path) -> UserProfile | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if time.time() - float(data.get("generated_at") or 0.0) > _CACHE_TTL_SECONDS:
            return None
        return UserProfile(
            total_user_turns=int(data.get("total_user_turns") or 0),
            top_stock_codes=[tuple(x) for x in data.get("top_stock_codes") or []],
            top_tickers=[tuple(x) for x in data.get("top_tickers") or []],
            top_ko_tokens=[tuple(x) for x in data.get("top_ko_tokens") or []],
            theme_breakdown=dict(data.get("theme_breakdown") or {}),
            generated_at=float(data.get("generated_at") or 0.0),
        )
    except (OSError, json.JSONDecodeError, ValueError, TypeError):
        return None


def _saveCache(path: Path, profile: UserProfile) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(profile), ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def _streamUserTexts(dbPath: Path) -> list[str]:
    if not dbPath.exists():
        return []
    try:
        conn = sqlite3.connect(dbPath)
        rows = conn.execute("SELECT text FROM entries WHERE role = 'user' AND block_type = 'text'").fetchall()
        conn.close()
        return [str(r[0]) for r in rows if r and r[0]]
    except sqlite3.OperationalError:
        return []


def _extractSignals(texts: list[str], *, topN: int = 15) -> UserProfile:
    stock_counts: Counter[str] = Counter()
    ticker_counts: Counter[str] = Counter()
    ko_counts: Counter[str] = Counter()
    theme_counts: Counter[str] = Counter()

    for text in texts:
        for m in _KR_STOCKCODE_RE.findall(text):
            stock_counts[m] += 1
        for m in _US_TICKER_RE.findall(text):
            if m in _KR_FALSE_TICKER:
                continue
            ticker_counts[m] += 1
        for tok in _KO_TOKEN_RE.findall(text):
            if tok in _KO_STOPWORDS:
                continue
            ko_counts[tok] += 1
        lower = text.lower()
        for theme, kws in _THEME_KEYWORDS.items():
            if any(kw in lower for kw in kws):
                theme_counts[theme] += 1

    return UserProfile(
        total_user_turns=len(texts),
        top_stock_codes=stock_counts.most_common(topN),
        top_tickers=[(t, c) for t, c in ticker_counts.most_common(topN * 3) if c >= _MIN_TICKER_COUNT][:topN],
        top_ko_tokens=ko_counts.most_common(topN),
        theme_breakdown=dict(theme_counts),
        generated_at=time.time(),
    )


def userInterestProfile(*, dbPath: Path | None = None, forceRefresh: bool = False, topN: int = 15) -> UserProfile:
    """사용자 누적 interest profile 반환.

    Args:
        dbPath: sessionIndex.db 경로. None 이면 표준 위치.
        forceRefresh: True 면 캐시 무시하고 재계산.
        topN: 종목·티커·토큰 top-N.

    Returns:
        UserProfile. 데이터 없으면 total_user_turns=0 빈 객체.
    """
    cache = _cachePath()
    if not forceRefresh:
        cached = _loadCache(cache)
        if cached is not None:
            return cached

    db = dbPath or sessionIndexPath()
    texts = _streamUserTexts(db)
    profile = _extractSignals(texts, topN=topN)
    _saveCache(cache, profile)
    return profile


__all__ = ["UserProfile", "userInterestProfile"]
