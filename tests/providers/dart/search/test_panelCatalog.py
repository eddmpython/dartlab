"""providers/dart/search/panelCatalog.py mirror tests."""

from __future__ import annotations

import polars as pl

from dartlab.providers.dart.search.panelCatalog import iterPanelCatalogFrames


def _firstRow(source, path):
    frames = list(iterPanelCatalogFrames(source, [path], sourceDataAsOf="", sourceAdapterVersion="v2"))
    return pl.concat(frames).row(0, named=True)


def test_iterPanelCatalogFrames_keeps_legacy_files_without_section_path(tmp_path) -> None:
    source = tmp_path / "005930.parquet"
    pl.DataFrame({"rceptNo": ["20260330001234"], "period": ["2025Q4"], "contentRaw": ["<p>표지</p>"]}).write_parquet(
        source
    )

    row = _firstRow("dartPanel", source)

    assert row["searchText"] == "표지"
    assert row["companyName"] == "005930"
    assert row["reportName"] == ""


def _panelBlock(rceptNo, order, chapter, path, leaf, text, *, leafType="text", period="2025Q4", corp="035720"):
    return {
        "rceptNo": rceptNo,
        "corp": corp,
        "period": period,
        "chapter": chapter,
        "sectionPath": path,
        "sectionLeaf": leaf,
        "leafType": leafType,
        "blockOrder": order,
        "contentRaw": text,
    }


def test_panel_document_leads_with_company_report_business_and_notes(tmp_path) -> None:
    from dartlab.providers.dart.search.semanticConstraints import compileSemanticMapperFromRows

    sep = chr(0x241F)
    rcept = "20260318001423"
    source = tmp_path / "035720.parquet"
    cover = "사업보고서 감사보고서 연결감사보고서 6.3 6.0 6.0 (주)카카오 주식회사 카카오 C A Y 110111-1129497"
    pl.DataFrame(
        [
            _panelBlock(rcept, 0, "", "", "", f"<p>{cover}</p>"),
            _panelBlock(rcept, 1, "", "", "", "<table>사업연도 2025년 01월 01일</table>", leafType="table"),
            _panelBlock(
                rcept, 2, "I. 회사의 개요", f"I. 회사의 개요{sep}1. 회사의 개요", "1. 회사의 개요", "본점은 제주"
            ),
            _panelBlock(
                rcept,
                3,
                "II. 사업의 내용",
                f"II. 사업의 내용{sep}1. 사업의 개요",
                "1. 사업의 개요",
                "1. 사업의 개요 당사는 카카오톡 플랫폼을 운영합니다",
            ),
            _panelBlock(
                rcept,
                4,
                "III. 재무에 관한 사항",
                f"III. 재무에 관한 사항{sep}3. 연결재무제표 주석",
                "3. 연결재무제표 주석",
                "1. 일반 사항 (1) 회사 개요 2. 리스 (1) 사용권자산 3. 충당부채 (단위: 원)",
            ),
            _panelBlock(
                rcept, 5, "【 대표이사 등의 확인 】", f"【 대표이사 등의 확인 】{sep}확인", "확인", "확인서 서명"
            ),
        ]
    ).write_parquet(source)

    row = _firstRow("dartPanel", source)

    assert row["sourceRef"] == f"dart:panel:{rcept}#section=0"
    assert row["companyName"] == "카카오"
    assert row["reportName"] == "사업보고서 (2025.12)"
    assert row["title"] == "사업보고서 (2025.12)"
    assert row["searchText"].startswith("카카오 사업보고서 (2025.12) [1. 사업의 개요] 당사는 카카오톡")
    assert "주석: 일반 사항, 리스, 충당부채" in row["searchText"][:1500]
    assert row["searchText"].index("주석:") < row["searchText"].index("본점은 제주")
    assert "확인서" not in row["searchText"]
    aliases = compileSemanticMapperFromRows([row]).aliases
    assert "카카오" in aliases
    assert not {"주식회사", "주카카오", "감사보고서"} & set(aliases)


def test_panel_document_keeps_confirmation_only_filing(tmp_path) -> None:
    sep = chr(0x241F)
    source = tmp_path / "035720.parquet"
    pl.DataFrame(
        [
            _panelBlock(
                "20240621000676",
                0,
                "【 대표이사 등의 확인 】",
                f"【 대표이사 등의 확인 】{sep}확인",
                "확인",
                "대표이사 등의 확인서명",
                period="2024Q2",
            )
        ]
    ).write_parquet(source)

    row = _firstRow("dartPanel", source)

    assert row["companyName"] == "035720"
    assert row["reportName"] == "반기보고서 (2024.06)"
    assert row["searchText"] == "035720 반기보고서 (2024.06) 대표이사 등의 확인서명"


def test_edgar_panel_document_groups_items_and_reads_note_heads(tmp_path) -> None:
    sep, dash = chr(0x241F), chr(0x2014)
    rcept = "0000320193-25-000079"
    source = tmp_path / "AAPL.parquet"
    blocks = [
        ("10-K", "10-K", "UNITED STATES SECURITIES AND EXCHANGE COMMISSION FORM 10-K"),
        ("10-K", "Item 1A. Risk Factors", "ITEM 1A. RISK FACTORS Supply chain concentration in Asia"),
        ("10-K", "Item 1A. If Our Goodwill Becomes Impaired", "Item 1A If our goodwill becomes impaired"),
        ("10-K", "Item 7. Management's Discussion", "Net sales grew on iPhone demand"),
        (
            "10-K",
            "Item 8. Financial Statements",
            f"NOTE 1 {dash} ACCOUNTING POLICIES Basis of presentation. Note 2 {dash} Leases Operating leases are",
        ),
    ]
    pl.DataFrame(
        [
            _panelBlock(rcept, order, chapter, f"10-K{sep}{title}", title, text, period="2025Q4", corp="AAPL")
            for order, (chapter, title, text) in enumerate(blocks)
        ]
    ).write_parquet(source)

    row = _firstRow("edgarPanel", source)

    assert row["sourceRef"] == f"edgar:panel:{rcept}#section=0"
    assert row["companyName"] == "AAPL"
    assert row["reportName"] == "10-K (2025Q4)"
    assert row["searchText"].startswith("AAPL 10-K (2025Q4) [Item 1A. Risk Factors]")
    assert row["searchText"].count("[Item 1A") == 1
    assert "Notes: Accounting Policies, Leases" in row["searchText"]
    assert row["searchText"].index("Notes:") < row["searchText"].index("iPhone")
