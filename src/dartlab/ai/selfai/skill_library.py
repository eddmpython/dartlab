"""Skill Library — 성공한 코드를 스킬로 저장하고 검색.

Voyager(Wang et al., 2023)의 스킬 라이브러리 개념을 dartlab에 적용.
audit에서 성공한 (질문, 코드, 도구) 트리플을 저장하고,
새 질문이 들어오면 유사 스킬을 검색하여 few-shot 예시로 활용.

DB 위치: ~/.dartlab/selfai/skill_library.db
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)

_DB_DIR = Path.home() / ".dartlab" / "selfai"
_DB_PATH = _DB_DIR / "skill_library.db"

# ── 카테고리 분류 규칙 ──────────────────────────────────────

_CATEGORY_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"수익성|마진|이익률|ROE|ROA|듀퐁", re.IGNORECASE), "profitability"),
    (re.compile(r"성장|매출.*증가|CAGR|성장률", re.IGNORECASE), "growth"),
    (re.compile(r"안정|부채|이자보상|ICR|레버리지", re.IGNORECASE), "stability"),
    (re.compile(r"현금|FCF|OCF|cash.*flow", re.IGNORECASE), "cashflow"),
    (re.compile(r"비용|원가|판관비|cost", re.IGNORECASE), "cost"),
    (re.compile(r"배당|자사주|환원|capital.*alloc", re.IGNORECASE), "capital"),
    (re.compile(r"신용|등급|credit|dCR", re.IGNORECASE), "credit"),
    (re.compile(r"가치|적정.*주가|DCF|DDM|valuation", re.IGNORECASE), "valuation"),
    (re.compile(r"예측|전망|forecast|방향", re.IGNORECASE), "forecast"),
    (re.compile(r"비교|vs|랑|하고", re.IGNORECASE), "comparison"),
    (re.compile(r"TOP|순위|랭킹|시장.*비교|scan", re.IGNORECASE), "scan"),
    (re.compile(r"경제|사이클|금리|매크로|macro", re.IGNORECASE), "macro"),
    (re.compile(r"주가|차트|기술적|quant", re.IGNORECASE), "quant"),
    (re.compile(r"공시|검색|유상증자|대표이사", re.IGNORECASE), "search"),
    (re.compile(r"뉴스|이슈|동향|최근", re.IGNORECASE), "news"),
]


def _classifyCategory(question: str) -> str:
    """질문에서 카테고리를 분류."""
    for pattern, category in _CATEGORY_RULES:
        if pattern.search(question):
            return category
    return "general"


def _extractTools(code: str) -> list[str]:
    """코드에서 사용된 도구 목록 추출."""
    tools = []
    if ".analysis(" in code:
        tools.append("analysis")
    if "dartlab.macro(" in code:
        tools.append("macro")
    if "dartlab.scan(" in code:
        tools.append("scan")
    if ".credit(" in code:
        tools.append("credit")
    if ".review(" in code:
        tools.append("review")
    if ".gather(" in code:
        tools.append("gather")
    if ".quant(" in code:
        tools.append("quant")
    if "dartlab.search(" in code:
        tools.append("search")
    if ".show(" in code or ".select(" in code:
        tools.append("show")
    if "newsSearch(" in code:
        tools.append("newsSearch")
    return tools


def _templatizeCode(code: str) -> str:
    """코드에서 종목코드를 변수화하여 범용 템플릿으로 변환."""
    # "005930" → "{stockCode}", "AAPL" → "{ticker}"
    result = re.sub(r'"(\d{6})"', '"{stockCode}"', code)
    result = re.sub(r"'(\d{6})'", "'{stockCode}'", result)
    return result


# ── 데이터 클래스 ───────────────────────────────────────────


@dataclass
class Skill:
    """스킬 레코드."""

    id: int
    question: str
    category: str
    tools_used: str  # JSON list
    code_template: str
    result_keys: str  # JSON list
    success_count: int
    quality_score: float


# ── DB 관리 ─────────────────────────────────────────────────

_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS skill (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT 'general',
    tools_used TEXT NOT NULL DEFAULT '[]',
    code_template TEXT NOT NULL,
    result_keys TEXT NOT NULL DEFAULT '[]',
    success_count INTEGER NOT NULL DEFAULT 1,
    quality_score REAL NOT NULL DEFAULT 0.8,
    created_at REAL NOT NULL,
    last_used REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_category ON skill(category);
"""


def _getDb() -> sqlite3.Connection:
    _DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH), timeout=5)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_CREATE_SQL)
    return conn


# ── 공개 API ────────────────────────────────────────────────


def save(
    question: str,
    code: str,
    result_keys: list[str] | None = None,
) -> int | None:
    """성공한 코드를 스킬로 저장.

    Args:
        question: 원본 질문
        code: 성공한 코드
        result_keys: 반환 구조의 주요 키 목록

    Returns:
        스킬 ID (실패 시 None)
    """
    category = _classifyCategory(question)
    tools = _extractTools(code)
    template = _templatizeCode(code)
    now = time.time()

    try:
        conn = _getDb()
        cursor = conn.execute(
            "INSERT INTO skill (question, category, tools_used, code_template, result_keys, success_count, quality_score, created_at, last_used) VALUES (?, ?, ?, ?, ?, 1, 0.8, ?, ?)",
            (
                question[:500],
                category,
                json.dumps(tools),
                template[:5000],
                json.dumps(result_keys or []),
                now,
                now,
            ),
        )
        conn.commit()
        skill_id = cursor.lastrowid
        conn.close()
        return skill_id
    except (sqlite3.OperationalError, OSError):
        log.warning("스킬 저장 실패")
        return None


def search(question: str, *, limit: int = 2) -> list[Skill]:
    """질문에 맞는 스킬을 검색.

    카테고리 매칭 + 품질 점수 순으로 반환.

    Args:
        question: 사용자 질문
        limit: 반환할 최대 스킬 수

    Returns:
        품질순 스킬 리스트
    """
    category = _classifyCategory(question)

    try:
        conn = _getDb()
    except (sqlite3.OperationalError, OSError):
        return []

    try:
        # 1차: 카테고리 매칭
        rows = conn.execute(
            "SELECT * FROM skill WHERE category = ? ORDER BY quality_score DESC, success_count DESC LIMIT ?",
            (category, limit),
        ).fetchall()

        # 2차: 카테고리 매칭 부족 시 전체에서 품질순
        if len(rows) < limit:
            existing_ids = {r[0] for r in rows}
            extra = conn.execute(
                "SELECT * FROM skill ORDER BY quality_score DESC, success_count DESC LIMIT ?",
                (limit * 3,),
            ).fetchall()
            for r in extra:
                if r[0] not in existing_ids and len(rows) < limit:
                    rows.append(r)

        return [
            Skill(
                id=r[0],
                question=r[1],
                category=r[2],
                tools_used=r[3],
                code_template=r[4],
                result_keys=r[5],
                success_count=r[6],
                quality_score=r[7],
            )
            for r in rows
        ]
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()


def recordSuccess(skill_id: int) -> None:
    """스킬 사용 성공을 기록 (success_count 증가)."""
    try:
        conn = _getDb()
        conn.execute(
            "UPDATE skill SET success_count = success_count + 1, last_used = ? WHERE id = ?",
            (time.time(), skill_id),
        )
        conn.commit()
        conn.close()
    except (sqlite3.OperationalError, OSError):
        pass


def seed_from_audit() -> int:
    """audit 테스트 케이스에서 검증된 스킬을 초기 seed로 삽입.

    Returns:
        삽입된 스킬 수
    """
    # audit 라운드 18-20에서 A/A- 등급으로 검증된 코드 패턴
    seeds = [
        {
            "question": "삼성전자 수익성 분석해줘",
            "code": """c = dartlab.Company("{stockCode}")
r = c.analysis("financial", "수익성")
flags = r.get("profitabilityFlags", {})
history = r["marginTrend"]["history"][:5]
print("| 기간 | 매출(억) | 영업이익률 | 순이익률 |")
print("| --- | --- | --- | --- |")
for h in history:
    rev = h.get("revenue", 0)
    opm = h.get("operatingMargin", 0)
    npm = h.get("netMargin", 0)
    print(f'| {h["period"]} | {rev/1e8:,.0f} | {opm:.1f}% | {npm:.1f}% |')""",
            "result_keys": ["marginTrend", "profitabilityFlags", "returnTrend"],
        },
        {
            "question": "신용등급 분석해줘",
            "code": """c = dartlab.Company("{stockCode}")
cr = c.credit(detail=True)
print(f"등급: {cr['grade']}, 건전도: {cr['healthScore']}/100")
print(f"\\n주요 지표:")
for k, v in cr.get("metrics", {}).items():
    print(f"  {k}: {v}")""",
            "result_keys": ["grade", "healthScore", "score", "metrics", "narratives"],
        },
        {
            "question": "시장에서 수익성 좋은 회사 찾아줘",
            "code": """df = dartlab.scan("profitability")
print(df.columns)
print(df.head(10))""",
            "result_keys": [],
        },
        {
            "question": "경제 사이클 분석해줘",
            "code": """r = dartlab.macro("사이클")
print(r.keys())
for k, v in r.items():
    if isinstance(v, dict):
        print(f"\\n{k}:")
        for k2, v2 in v.items():
            print(f"  {k2}: {v2}")
    else:
        print(f"{k}: {v}")""",
            "result_keys": [],
        },
        {
            "question": "최근 주가 추이 보여줘",
            "code": """c = dartlab.Company("{stockCode}")
price = c.gather("price")
if price is not None:
    print(price.tail(20))
else:
    print("주가 데이터 없음")""",
            "result_keys": [],
        },
        {
            "question": "공시 검색",
            "code": """results = dartlab.search("유상증자")
print(f"검색 결과: {len(results)}건")
print(results.head(10))""",
            "result_keys": [],
        },
        {
            "question": "종합 분석해줘",
            "code": """c = dartlab.Company("{stockCode}")
# 3축 동시 수집
prof = c.analysis("financial", "수익성")
growth = c.analysis("financial", "성장성")
stab = c.analysis("financial", "안정성")

# 수익성 요약
h = prof["marginTrend"]["history"][0]
print(f"최근 영업이익률: {h.get('operatingMargin', 0):.1f}%")

# 성장성 요약
g = growth.get("revenueGrowth", {})
print(f"매출 성장률: {g.get('yoy', 'N/A')}")

# 안정성 요약
s = stab.get("debtAnalysis", {})
print(f"부채비율: {s.get('debtRatio', 'N/A')}")""",
            "result_keys": ["marginTrend", "revenueGrowth", "debtAnalysis"],
        },
        {
            "question": "재고자산 주석 분석",
            "code": """c = dartlab.Company("{stockCode}")
inv = c.notes.inventory
if inv is not None:
    print(inv)
else:
    print("재고자산 주석 데이터 없음")""",
            "result_keys": [],
        },
    ]

    count = 0
    for s in seeds:
        result = save(
            question=s["question"],
            code=s["code"],
            result_keys=s.get("result_keys"),
        )
        if result is not None:
            count += 1

    return count
