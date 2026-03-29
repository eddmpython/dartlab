"""Shared constants for CLI/TUI -- tool labels, commands, skills."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Suggestions (English defaults)
# ---------------------------------------------------------------------------

SUGGESTIONS = [
    "Analyze profitability trends and earnings quality",
    "Evaluate financial health and cash flow sustainability",
    "Assess debt structure and liquidity risks",
    "Compare dividend sustainability and shareholder returns",
    "Summarize the key investment thesis for this company",
]

# ---------------------------------------------------------------------------
# Tool labels
# ---------------------------------------------------------------------------

TOOL_LABELS = {
    "explore": "Disclosure",
    "finance": "Financial Data",
    "analysis": "Analysis Engine",
    "scan": "Market Scan",
    "gather": "Market Data",
    "review": "Review Report",
    "openapi": "OpenDART API",
    "system": "System Info",
    "chart": "Chart",
    "research": "Research",
    "macro": "Macro",
    "company": "Company",
    "ui": "UI",
    # legacy
    "analyze": "Analysis Engine",
    "market": "Market Data",
}

# ---------------------------------------------------------------------------
# Slash command registry
# ---------------------------------------------------------------------------

COMMANDS: list[tuple[str, tuple[str, ...], str]] = [
    ("/help", (), "Show available commands"),
    ("/company", ("/c",), "Switch or show current company"),
    ("/model", ("/m",), "Switch model"),
    ("/provider", ("/p",), "Switch LLM provider"),
    ("/clear", (), "Clear conversation history"),
    ("/suggest", ("/s",), "Suggested questions"),
    ("/status", (), "Session status and config"),
    ("/cost", (), "Token usage and cost"),
    ("/export", (), "Export conversation to markdown"),
    ("/history", ("/h",), "Show recent conversation turns"),
    ("/compact", (), "Compact conversation history"),
    ("/report", ("/r",), "Deep analysis (report mode)"),
    ("/quit", ("/exit", "/q"), "Exit"),
]

# ---------------------------------------------------------------------------
# Skill commands (analysis domain shortcuts)
# ---------------------------------------------------------------------------

SKILL_COMMANDS: list[tuple[str, str, str]] = [
    ("/profitability", "profitability", "Profitability analysis (DuPont, margins, earnings quality)"),
    ("/health", "health", "Financial health (leverage, liquidity, coverage)"),
    ("/valuation", "valuation", "Valuation (multiples, DCF, fair value range)"),
    ("/risk", "risk", "Risk assessment (financial, business, accounting)"),
    ("/strategy", "strategy", "Business strategy (segments, moat, growth)"),
    ("/accounting", "accounting", "Accounting quality (accruals, audit, changes)"),
    ("/dividend", "dividend", "Dividend analysis (sustainability, payout, yield)"),
    ("/comprehensive", "comprehensive", "Comprehensive investment analysis"),
]

SKILL_DEFAULT_QUESTIONS: dict[str, str] = {
    "profitability": "Analyze profitability trends: DuPont decomposition, margin structure, and earnings quality",
    "health": "Evaluate financial health: leverage structure, liquidity layers, and debt coverage",
    "valuation": "Assess valuation: key multiples vs peers, DCF fair value range, and safety margin",
    "risk": "Identify risks: financial distress signals, business risks, and accounting red flags",
    "strategy": "Analyze business strategy: segment structure, competitive moat, and growth direction",
    "accounting": "Evaluate accounting quality: accrual ratio, audit history, and policy changes",
    "dividend": "Analyze dividends: payout history, FCF sustainability, and shareholder return policy",
    "comprehensive": "Provide a comprehensive investment analysis covering financials, valuation, risks, and thesis",
}

SLASH_WORDS: list[str] = [name for name, _, _ in COMMANDS]
SLASH_WORDS.extend(skillCmd for skillCmd, _, _ in SKILL_COMMANDS)


def toolLabel(toolName: str) -> str:
    """도구 이름을 표시 레이블로 변환."""
    return TOOL_LABELS.get(toolName, toolName)


def formatToolArgs(args: dict) -> str:
    """도구 호출 인자를 축약 문자열로 변환."""
    parts = []
    for k, v in list(args.items())[:2]:
        sv = str(v)
        if len(sv) > 30:
            sv = sv[:27] + "..."
        parts.append(f"{k}={sv}")
    return ", ".join(parts)


def toolResultPreview(resultText: str) -> str:
    """도구 결과에서 한줄 미리보기를 추출."""
    if not resultText or resultText.startswith("[Error]") or resultText.startswith("["):
        return ""
    lines = resultText.strip().splitlines()
    tableRows = [ln for ln in lines if ln.startswith("|") and "---" not in ln]
    if len(tableRows) > 1:
        return f"{len(tableRows) - 1} rows"
    firstLine = lines[0].strip().lstrip("#").strip() if lines else ""
    if len(firstLine) > 60:
        firstLine = firstLine[:57] + "..."
    return firstLine
