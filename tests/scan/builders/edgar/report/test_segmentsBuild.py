"""segmentsBuild. DERA notes 차원 사실 → 부문 매출 선별 계약 (합성 zip, 네트워크/OOM 무관)."""

from __future__ import annotations

import zipfile

import pytest

pytestmark = pytest.mark.unit

_SUB = "adsh\tcik\tform\nA-1\t320193\t10-K\nB-1\t789019\t8-K\n"
_DIM = (
    "dimhash\tsegments\tsegt\n"
    "H1\tBusinessSegments=GreaterChinaSegment;ConsolidationItems=OperatingSegments;\t0\n"
    "H2\tProductOrService=IPhone;\t0\n"
    "H3\tBusinessSegments=AmericasSegment;ConsolidationItems=IntersegmentEliminationMember;\t0\n"
    "H4\tBusinessSegments=AmericasSegment;\t0\n"
)
_NUM_HEAD = (
    "adsh\ttag\tversion\tddate\tqtrs\tuom\tdimh\tiprx\tvalue\tfootnote\tfootlen\tdimn\tcoreg\tdurp\tdatp\tdcml\n"
)
_NUM_ROWS = (
    # 채택: 부문축+OperatingSegments (H1) 연간
    "A-1\tRevenueFromContractWithCustomerExcludingAssessedTax\tus-gaap/2025\t20250930\t4\tUSD\tH1\t0\t64400000000\t\t0\t2\t\t0\t0\t-6\n"
    # 채택: ConsolidationItems 부재 (H4) 분기
    "A-1\tRevenues\tus-gaap/2025\t20250630\t1\tUSD\tH4\t0\t1000\t\t0\t1\t\t0\t0\t0\n"
    # 배제: 제품축 (H2)
    "A-1\tRevenues\tus-gaap/2025\t20250930\t4\tUSD\tH2\t0\t9999\t\t0\t1\t\t0\t0\t0\n"
    # 배제: 내부거래 제거 (H3)
    "A-1\tRevenues\tus-gaap/2025\t20250930\t4\tUSD\tH3\t0\t8888\t\t0\t2\t\t0\t0\t0\n"
    # 배제: 10-K/10-Q 아님 (B-1 은 8-K)
    "B-1\tRevenues\tus-gaap/2025\t20250930\t4\tUSD\tH1\t0\t7777\t\t0\t2\t\t0\t0\t0\n"
    # 배제: iprx 변형 표기
    "A-1\tRevenues\tus-gaap/2025\t20250930\t4\tUSD\tH1\t1\t6666\t\t0\t2\t\t0\t0\t0\n"
)


def _writeZip(tmp_path):
    zp = tmp_path / "2025_10_notes.zip"
    with zipfile.ZipFile(zp, "w") as z:
        z.writestr("sub.tsv", _SUB)
        z.writestr("dim.tsv", _DIM)
        z.writestr("num.tsv", _NUM_HEAD + _NUM_ROWS)
    return zp


def test_segment_rows_axis_and_form_gates(tmp_path):
    """부문축만 채택: 제품축·내부거래제거·비 10-K/Q·iprx 변형 전부 배제 + 기간 라벨링."""
    from dartlab.scan.builders.edgar.report.segmentsBuild import segmentRowsFromZip

    rows = segmentRowsFromZip(_writeZip(tmp_path), {"0000320193": "AAPL"})
    assert len(rows) == 2
    annual = next(r for r in rows if r["flow"] == "Y")
    assert annual == {
        "stockCode": "AAPL",
        "period": "2025Q3",
        "year": "2025",
        "quarter": "3",
        "flow": "Y",
        "segment": "Greater China",
        "revenue": 64_400_000_000.0,
    }
    q = next(r for r in rows if r["flow"] == "Q")
    assert q["period"] == "2025Q2" and q["segment"] == "Americas"


def test_segment_name_from_member():
    """멤버명 정리: 접미 제거 + camelCase 분리."""
    from dartlab.scan.builders.edgar.report.segmentsBuild import segmentNameFromMember

    assert segmentNameFromMember("GreaterChinaSegment") == "Greater China"
    assert segmentNameFromMember("IntelligentCloudMember") == "Intelligent Cloud"
    assert segmentNameFromMember("Americas") == "Americas"
