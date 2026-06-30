"""securitiesRegistration — IPO 증권신고서 파서 회귀 가드.

개념확립(`tests/_attempts/ipo/`, 발행사 7 곳 교차)에서 박은 판별 3 조건 + 6 카테고리 항등식.
순수 로직 (dart4.xsd string in → dict out), 데이터 로드 없음. 합성 fixture 는 항등식이 닫히는
값으로 구성(공모가 80,000 × 주식수 1,000,000 = 총액 80,000,000,000 ; ①5,000M×②20÷③1,000,000
= 평가액 100,000 ; 평가액×(1−할인율) = 밴드 80,000~90,000 ; 자산 1,000 = 부채 600 + 자본 400).
"""

from __future__ import annotations

import pytest

from dartlab.providers.dart.securitiesRegistration import classifyIpo, parseIpoProspectus

pytestmark = [pytest.mark.unit]


# ── 판별 (순수) ──


def test_classify_ipo_three_conditions():
    # 지분증권 + E + 빈 stock_code = IPO
    assert classifyIpo("증권신고서(지분증권)", "E", "", "주식회사 기도산업")["isIpo"] is True


def test_classify_fund_not_ipo():
    # 첫 괄호가 집합투자증권 — 펀드명 속 '(지분증권)' 오매칭 차단
    r = classifyIpo(
        "증권신고서(집합투자증권-회사형)(한국밸류기업가치포커스(지분증권))", "E", "", "한국투자밸류자산운용"
    )
    assert r["isIpo"] is False and r["subtype"] == "집합투자증권"


def test_classify_rights_offering_not_ipo():
    # 상장사(Y/K, stock_code 보유) 지분증권 = 유상증자
    r = classifyIpo("증권신고서(지분증권)", "Y", "000660", "SK하이닉스")
    assert r["isIpo"] is False and "유상증자" in r["verdict"]


def test_classify_spac_and_notice():
    assert classifyIpo("증권신고서(지분증권)", "E", "", "한국제16호기업인수목적")["isSpac"] is True
    assert classifyIpo("효력발생안내( 증권신고서(지분증권) )", "E", "", "레메디")["kind"] == "notice"


# ── 본문 파싱 (합성 fixture) ──

_FIXTURE = """<?xml version="1.0" encoding="utf-8"?>
<DOCUMENT>
<TITLE>1. 공모개요</TITLE>
<P>희망공모가액은 80,000원 ~ 90,000원입니다.</P>
<TABLE>
<TR><TD>증권의 종류</TD><TD>증권수량</TD><TD>모집(매출)가액</TD><TD>모집(매출)총액</TD></TR>
<TR><TD>보통주</TD><TD>1,000,000</TD><TD>80,000</TD><TD>80,000,000,000</TD></TR>
</TABLE>
<TABLE>
<TR><TD>청약기일</TD><TD>납입기일</TD></TR>
<TR><TD>2026.09.01 ~ 2026.09.02</TD><TD>2026.09.04</TD></TR>
</TABLE>
<TITLE>2. 공모방법</TITLE>
<TABLE>
<TR><TD>공모대상</TD><TD>주식수</TD><TD>배정비율</TD></TR>
<TR><TD>우리사주조합</TD><TD>200,000주</TD><TD>20%</TD></TR>
<TR><TD>일반공모</TD><TD>800,000주</TD><TD>80%</TD></TR>
</TABLE>
<TITLE>IV. 인수인의 의견(분석기관의 평가의견)</TITLE>
<TABLE>
<TR><TD>평가방법</TD><TD>상대가치법</TD></TR>
<TR><TD>평가모형</TD><TD>PER</TD></TR>
<TR><TD>적용근거</TD><TD>①</TD><TD>당기순이익</TD><TD>5,000백만원</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>②</TD><TD>유사기업 PER</TD><TD>20배</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>③</TD><TD>주식수</TD><TD>1,000,000주</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>주당 평가가액</TD><TD>주당 평가가액</TD><TD>100,000원</TD><TD>①x②÷③</TD></TR>
<TR><TD>적용근거</TD><TD>④</TD><TD>주당 평가가액에 대한 할인율</TD><TD>20% ~ 10%</TD><TD>참고</TD></TR>
<TR><TD>적용근거</TD><TD>공모가 산정 결과</TD><TD>공모가 산정 결과</TD><TD>80,000원 ~ 90,000원</TD><TD>참고</TD></TR>
</TABLE>
<TITLE>III. 재무에 관한 사항</TITLE>
<TITLE>1. 요약재무정보</TITLE>
<TABLE>
<TR><TD>구분</TD><TD>2025년</TD><TD>2024년</TD></TR>
<TR><TD>자산총계</TD><TD>1,000</TD><TD>900</TD></TR>
<TR><TD>부채총계</TD><TD>600</TD><TD>500</TD></TR>
<TR><TD>자본총계</TD><TD>400</TD><TD>400</TD></TR>
<TR><TD>매출액</TD><TD>2,000</TD><TD>1,800</TD></TR>
</TABLE>
<TITLE>1. 핵심투자위험</TITLE>
<TITLE>III. 투자위험요소</TITLE>
<TITLE>1. 사업위험</TITLE>
<TITLE>2. 회사위험</TITLE>
<TITLE>3. 기타위험</TITLE>
<TABLE>
<TR><TD>구분</TD><TD>주주명</TD><TD>회사와의관계</TD><TD>공모후</TD><TD>공모후</TD><TD>매각제한물량</TD><TD>매각제한물량</TD><TD>유통가능물량</TD><TD>유통가능물량</TD><TD>매각제한기간</TD><TD>매각제한사유</TD></TR>
<TR><TD>구분</TD><TD>주주명</TD><TD>회사와의관계</TD><TD>보유주식</TD><TD>보유주식</TD><TD>매각제한물량</TD><TD>매각제한물량</TD><TD>유통가능물량</TD><TD>유통가능물량</TD><TD>매각제한기간</TD><TD>매각제한사유</TD></TR>
<TR><TD>구분</TD><TD>주주명</TD><TD>회사와의관계</TD><TD>주식수</TD><TD>지분율</TD><TD>주식수</TD><TD>지분율</TD><TD>주식수</TD><TD>지분율</TD><TD>매각제한기간</TD><TD>매각제한사유</TD></TR>
<TR><TD>최대주주등</TD><TD>홍길동</TD><TD>본인</TD><TD>700,000</TD><TD>70.00%</TD><TD>700,000</TD><TD>70.00%</TD><TD>-</TD><TD>0.00%</TD><TD>24개월</TD><TD>주1)</TD></TR>
<TR><TD>공모주주</TD><TD>일반공모</TD><TD>일반</TD><TD>300,000</TD><TD>30.00%</TD><TD>-</TD><TD>0.00%</TD><TD>300,000</TD><TD>30.00%</TD><TD>-</TD><TD>-</TD></TR>
<TR><TD>합계</TD><TD>합계</TD><TD>합계</TD><TD>1,000,000</TD><TD>100.00%</TD><TD>700,000</TD><TD>70.00%</TD><TD>300,000</TD><TD>30.00%</TD><TD>-</TD><TD>-</TD></TR>
</TABLE>
</DOCUMENT>"""


def test_parse_offering_and_identity():
    r = parseIpoProspectus(_FIXTURE)
    off = r["offering"]
    assert off["priceBand"] == (80000.0, 90000.0)
    assert off["offerTotal"] == 80_000_000_000.0
    assert off["subscription"].startswith("2026.09.01")
    assert off["payDate"] == "2026.09.04"
    # 공모가 × 주식수 = 총액 → 복구 1,000,000
    assert r["identities"]["sharesRecovered"] == 1_000_000


def test_parse_valuation_chain_identity():
    v = parseIpoProspectus(_FIXTURE)["valuation"]
    assert v["model"] == "PER"
    assert v["netIncome"] == 5_000_000_000.0
    assert v["peerMultiple"] == 20.0
    assert v["perShareValue"] == 100_000.0
    # ① × ② ÷ ③ = 평가액 ; 평가액 × (1−할인율) = 밴드
    ids = parseIpoProspectus(_FIXTURE)["identities"]
    assert ids["valuationChain"] is True
    assert ids["valuationBand"] is True


def test_parse_financials_balance_identity():
    r = parseIpoProspectus(_FIXTURE)
    rows = r["financials"]["rows"]
    assert rows["자산총계"][0] == 1000.0
    assert r["identities"]["financialsBalance"] is True  # 1000 = 600 + 400


def test_parse_allocation_sum_identity():
    r = parseIpoProspectus(_FIXTURE)
    assert r["allocation"]["total"] == 1_000_000.0  # 200,000 + 800,000
    assert r["identities"]["allocationSum"] is True


def test_parse_float_waterfall_identity():
    r = parseIpoProspectus(_FIXTURE)
    f = r["float"]
    assert f["postOfferingShares"] == 1_000_000.0
    assert f["lockedShares"] == 700_000.0
    assert f["freeFloatShares"] == 300_000.0
    assert f["freeFloatPct"] == 30.0
    # 매각제한 + 유통가능 = 공모후 총발행
    assert r["identities"]["floatBalance"] is True
    # 주주별 보호예수(매각제한) 일정
    assert any(lu["holder"] == "홍길동" and "24개월" in lu["period"] for lu in f["lockups"])


def test_parse_six_sections_and_risk():
    r = parseIpoProspectus(_FIXTURE)
    assert {"offering", "method", "underwriterOpinion", "financials", "riskSummary", "riskDetail"} <= set(r["sections"])
    assert r["risk"]["count"] >= 3  # 핵심투자위험 + 사업/회사위험


def test_never_raise_on_garbage():
    r = parseIpoProspectus("<DOCUMENT>빈 문서</DOCUMENT>")
    assert r["sections"] == []
    assert r["offering"]["offerTotal"] is None
    assert r["valuation"] == {} and r["identities"] == {}
