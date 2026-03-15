"""rich 기반 터미널 출력."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

_PR = "#ea4647"
_AC = "#fb923c"
_TX = "#f1f5f9"
_TM = "#94a3b8"
_TD = "#64748b"

_B = "#3d3558"
_BD = "#2a2040"
_E = "#0e0d1a"
_EH = "#f1f5f9"
_CH = "#ea4647"
_LN = "#ea4647"
_HD = "#fb923c"

_AVATAR_DATA = [
    [(None, "  "), (_BD, "▄▄▄▄▄▄"), (None, "      ")],
    [(_BD, "▄"), (_B, "████████"), (_BD, "▄"), (None, "   ")],
    [(_B, "██"), (_E, "██"), (_B, "████"), (_E, "██"), (_B, "██"), (None, " ")],
    [
        (_B, "██"),
        (_E, "█"),
        (_EH, "▘"),
        (_E, "█"),
        (_B, "██"),
        (_E, "█"),
        (_EH, "▘"),
        (_E, "█"),
        (_B, "█"),
        (_LN, "▄▄"),
    ],
    [(_B, "█"), (_CH, "▄"), (_B, "█▁▁██"), (_CH, "▄"), (_B, "█"), (_LN, "█"), (None, " "), (_LN, "█")],
    [(_B, "███████████"), (_LN, "▀▀"), (_HD, "▘")],
    [(None, " "), (_BD, "▀"), (_B, "████████"), (_BD, "▀"), (None, " "), (_HD, "▐")],
    [(None, "  "), (_BD, "▀▀▀▀▀▀"), (None, "   "), (_HD, "▝")],
]


def _avatar_lines():
    from rich.text import Text

    lines = []
    for row in _AVATAR_DATA:
        t = Text()
        for color, ch in row:
            t.append(ch, style=color if color else "")
        lines.append(t)
    return lines


def printRepr(corpName: str, stockCode: str, nProps: int, nNotes: int):
    from rich.console import Console
    from rich.text import Text

    console = Console()
    av = _avatar_lines()

    info = []

    t = Text()
    t.append("dartlab", style=f"bold {_PR}")
    t.append(" · ", style=_TD)
    t.append(corpName, style=f"bold {_AC}")
    t.append(f" ({stockCode})", style=_TM)
    info.append(t)

    info.append(Text("─" * 32, style=_TD))

    t = Text()
    t.append("재무제표  ", style=_TM)
    t.append("c.BS  c.IS  c.CF", style=_TX)
    info.append(t)

    t = Text()
    t.append("정기보고  ", style=_TM)
    t.append(f"{nProps} properties", style=_TX)
    info.append(t)

    t = Text()
    t.append("주석      ", style=_TM)
    t.append(f"{nNotes} notes", style=_TX)
    info.append(t)

    info.append(Text("─" * 32, style=_TD))

    t = Text()
    t.append("c.guide()", style=_PR)
    t.append(" 전체 목록", style=_TM)
    info.append(t)

    t = Text()
    t.append("c.all()", style=_PR)
    t.append("   전체 추출", style=_TM)
    info.append(t)

    maxLines = max(len(av), len(info))
    for i in range(maxLines):
        line = Text()
        if i < len(av):
            line.append_text(av[i])
        else:
            line.append(" " * 14)
        line.append("  ")
        if i < len(info):
            line.append_text(info[i])
        console.print(line)


def printGuide(corpName: str, stockCode: str, properties: list, noteKeys: list, noteKeysKr: list):
    from rich.console import Console
    from rich.text import Text

    console = Console()

    t = Text()
    t.append("\n dartlab", style=f"bold {_PR}")
    t.append(" · ", style=_TD)
    t.append(corpName, style=f"bold {_AC}")
    t.append(f" ({stockCode})", style=_TM)
    t.append(" 사용 가이드\n", style=_TM)
    console.print(t)

    console.print(Text("─" * 50, style=_TD))

    console.print(Text("\n 재무제표", style=f"bold {_TX}"))
    t = Text()
    t.append("   c.BS", style=_PR)
    t.append("  재무상태표   ", style=_TM)
    t.append("c.IS", style=_PR)
    t.append("  손익계산서   ", style=_TM)
    t.append("c.CF", style=_PR)
    t.append("  현금흐름표", style=_TM)
    console.print(t)

    console.print(Text("\n 정기보고서", style=f"bold {_TX}"))
    propLabels = {
        "dividend": "배당",
        "majorHolder": "최대주주",
        "employee": "직원",
        "subsidiary": "자회사",
        "bond": "채무증권",
        "shareCapital": "주식",
        "executive": "임원",
        "executivePay": "임원보수",
        "audit": "감사의견",
        "boardOfDirectors": "이사회",
        "capitalChange": "자본변동",
        "contingentLiability": "우발부채",
        "internalControl": "내부통제",
        "relatedPartyTx": "관계자거래",
        "rnd": "R&D",
        "sanction": "제재",
        "affiliateGroup": "계열사",
        "fundraising": "증자감자",
        "productService": "주요제품",
        "salesOrder": "매출수주",
        "riskDerivative": "위험관리",
        "articlesOfIncorporation": "정관",
        "otherFinance": "기타재무",
        "companyHistory": "연혁",
        "shareholderMeeting": "주주총회",
        "auditSystem": "감사제도",
        "investmentInOther": "타법인출자",
        "companyOverviewDetail": "회사개요",
        "holderOverview": "주주현황",
        "business": "사업내용",
        "overview": "개요",
        "mdna": "MD&A",
        "rawMaterial": "원재료",
    }
    row = Text("   ")
    count = 0
    for prop in properties:
        label = propLabels.get(prop, prop)
        row.append(f"c.{prop}", style=_PR)
        row.append(f" {label}  ", style=_TM)
        count += 1
        if count % 3 == 0:
            console.print(row)
            row = Text("   ")
    if row.plain.strip():
        console.print(row)

    console.print(Text("\n 주석 (K-IFRS)", style=f"bold {_TX}"))
    for eng, kr in zip(noteKeys, noteKeysKr):
        t = Text("   ")
        t.append(f"c.notes.{eng}", style=_PR)
        padding = " " * max(1, 24 - len(f"c.notes.{eng}"))
        t.append(padding, style="")
        t.append(kr, style=_TM)
        console.print(t)

    t = Text("   ")
    t.append('c.notes["재고자산"]', style=_PR)
    t.append("  한글 키도 가능", style=_TM)
    console.print(t)

    console.print(Text("\n 기타", style=f"bold {_TX}"))
    t = Text("   ")
    t.append("c.all()", style=_PR)
    t.append("        전체 추출 (progress bar)  ", style=_TM)
    console.print(t)
    t = Text("   ")
    t.append('c.get("audit")', style=_PR)
    t.append(" 모듈 전체 Result 객체  ", style=_TM)
    console.print(t)
    t = Text("   ")
    t.append("c.fsSummary()", style=_PR)
    t.append("  요약재무정보 + 브릿지 매칭  ", style=_TM)
    console.print(t)
    t = Text("   ")
    t.append("c.filings()", style=_PR)
    t.append("       공시 문서 목록  ", style=_TM)
    console.print(t)

    console.print(Text("\n 설정", style=f"bold {_TX}"))
    t = Text("   ")
    t.append("dartlab.verbose = False", style=_PR)
    t.append("  진행 표시 끄기", style=_TM)
    console.print(t)

    console.print()
