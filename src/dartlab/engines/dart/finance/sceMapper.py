"""SCE(자본변동표) 계정 정규화 매퍼.

account_nm → 변동사유(cause) snakeId
account_detail → 자본항목(component) snakeId

2-tier 매핑:
1. CAUSE_SYNONYMS dict 정확 매칭 (250+개)
2. 공백 제거 후 재매칭
3. CAUSE_FALLBACK_PATTERNS 부분 문자열 매칭 (80+개)

자본항목은 파이프(|) 구분 마지막 세그먼트에서 DETAIL_MAP → fallback 패턴.
"""

from __future__ import annotations

import re
from typing import Optional


CAUSE_SYNONYMS: dict[str, str] = {
    "기초자본": "beginning_equity",
    "기초자본 잔액": "beginning_equity",
    "수정전 기초자본": "beginning_equity",
    "수정후 기초자본": "adjusted_beginning",
    "기말자본": "ending_equity",
    "기말자본 잔액": "ending_equity",
    "자본총계": "ending_equity",
    "기말 자본": "ending_equity",
    "기말잔액": "ending_equity",

    "당기순이익": "net_income",
    "당기순이익(손실)": "net_income",
    "당기순손실": "net_income",
    "반기순이익": "net_income",
    "반기순이익(손실)": "net_income",
    "분기순이익": "net_income",
    "분기순이익(손실)": "net_income",
    "분기순손실": "net_income",

    "배당": "dividends",
    "배당금 지급": "dividends",
    "배당금지급": "dividends",
    "배당금의 지급": "dividends",
    "현금배당": "dividends",
    "연차배당": "dividends",
    "소유주에 대한 배분으로 인식된 배당금": "dividends",

    "자기주식의 취득": "treasury_acquired",
    "자기주식 취득": "treasury_acquired",
    "자기주식의취득": "treasury_acquired",
    "자기주식취득": "treasury_acquired",
    "자기주식의 소각": "treasury_retired",
    "자기주식 소각": "treasury_retired",
    "자기주식의 처분": "treasury_disposed",
    "자기주식 처분": "treasury_disposed",
    "자기주식 거래로 인한 증감": "treasury_change",

    "해외사업장환산외환차이": "fx_translation",
    "해외사업장 환산 외환차이": "fx_translation",
    "해외사업환산손익": "fx_translation",

    "기타포괄손익-공정가치금융자산평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 금융자산 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치측정 금융자산 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 금융자산평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 지분상품 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치측정 지분상품 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치측정지분상품 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치측정지분상품평가손익": "fvoci_valuation",
    "공정가치측정금융자산 평가손익": "fvoci_valuation",
    "매도가능금융자산평가": "fvoci_valuation",
    "매도가능금융자산평가손익": "fvoci_valuation",

    "현금흐름위험회피파생상품평가손익": "cashflow_hedge",
    "현금흐름위험회피 파생상품 평가손익": "cashflow_hedge",
    "파생상품평가": "cashflow_hedge",

    "순확정급여부채(자산) 재측정요소": "remeasurement_db",
    "순확정급여부채 재측정요소": "remeasurement_db",
    "순확정급여자산 재측정요소": "remeasurement_db",
    "확정급여제도의 재측정요소": "remeasurement_db",
    "확정급여제도의재측정요소": "remeasurement_db",
    "확정급여부채의 재측정요소": "remeasurement_db",
    "확정급여제도의 재측정손익(세후기타포괄손익)": "remeasurement_db",
    "확정급여제도의 재측정손익": "remeasurement_db",
    "순확정급여부채의 재측정요소": "remeasurement_db",
    "보험수리적손익": "remeasurement_db",

    "관계기업 및 공동기업의 기타포괄손익에 대한 지분": "associate_oci",
    "관계기업 및 공동기업 기타포괄손익에 대한 지분": "associate_oci",
    "지분법 기타포괄손익": "associate_oci",
    "지분법자본변동": "associate_oci",

    "연결실체내 자본거래 등": "intragroup_tx",
    "연결실체내 자본거래": "intragroup_tx",
    "지배력을 상실하지 않는 종속기업에 대한 소유지분의 변동에 따른 증가(감소)/비지배지분의 변동": "intragroup_tx",
    "연결실체의 변동": "consolidation_change",
    "연결범위의 변동": "consolidation_change",
    "연결대상범위의 변동": "consolidation_change",
    "사업결합": "consolidation_change",

    "회계정책변경누적효과": "accounting_change",
    "회계정책변경의 누적효과": "accounting_change",
    "회계정책 변경효과": "accounting_change",
    "회계정책변경에 따른 증가(감소)": "accounting_change",

    "주식기준보상": "stock_compensation",
    "주식기준보상거래": "stock_compensation",
    "주식보상비용": "stock_compensation",
    "주식기준보상거래에 따른 증가(감소), 지분": "stock_compensation",
    "주식선택권": "stock_options",
    "주식매수선택권": "stock_options",
    "주식선택권의 행사": "stock_options",
    "주식매수선택권의 행사": "stock_options",
    "주식매수선택권 행사": "stock_options",
    "주식매입선택권": "stock_options",
    "주식매입선택권의 행사": "stock_options",

    "기타": "other",
    "기타변동": "other",
    "기타거래": "other",
    "기타의 자본조정": "other",
    "기타변동의 자본조정": "other",
    "대체와 기타 변동에 따른 증가(감소), 자본": "other",
    "기타자본의 변동": "other",
    "기타자본변동": "other",
    "기타자본 증감": "other",
    "기타포괄손익": "other_oci",
    "세후기타포괄손익": "other_oci",
    "기타포괄이익": "other_oci",
    "기타포괄손실": "other_oci",
    "총포괄손익": "total_comprehensive",
    "총포괄이익": "total_comprehensive",
    "총 포괄손익": "total_comprehensive",
    "포괄이익": "total_comprehensive",
    "포괄손익": "total_comprehensive",

    "매각예정분류": "held_for_sale_reclass",
    "매각예정 분류": "held_for_sale_reclass",

    "유상증자": "capital_increase",
    "무상증자": "capital_increase",
    "지분의 발행": "capital_increase",
    "신주발행": "capital_increase",
    "주식의 발행": "capital_increase",
    "종속기업의 유상증자": "capital_increase",
    "신주인수권행사": "capital_increase",
    "신주인수권의 행사": "capital_increase",
    "무상감자": "capital_decrease",
    "유상감자": "capital_decrease",
    "감자": "capital_decrease",
    "감자차손": "capital_decrease",
    "자본감소": "capital_decrease",
    "자본 증가(감소) 합계": "equity_change_total",
    "전환사채의 전환": "convertible_bond",
    "전환사채의 발행": "convertible_bond",
    "전환사채 전환": "convertible_bond",
    "전환사채의 상환": "convertible_bond",
    "전환권 행사": "convertible_bond",
    "전환권행사": "convertible_bond",
    "전환권대가": "convertible_bond",
    "복합금융상품 전환": "convertible_bond",
    "전환권의 행사": "convertible_bond",
    "신종자본증권 발행": "hybrid_issued",
    "신종자본증권의 발행": "hybrid_issued",
    "신종자본증권 이자": "hybrid_interest",
    "영구채이자": "hybrid_interest",
    "영구채 이자": "hybrid_interest",
    "신종자본증권이자": "hybrid_interest",
    "신종자본증권 배당": "hybrid_interest",

    "기타포괄손익-공정가치 측정 금융자산 평가손익 적립금": "fvoci_valuation",
    "기타포괄손익-공정가치측정금융자산평가손익": "fvoci_valuation",
    "매도가능증권평가손익": "fvoci_valuation",
    "매도가능금융자산의 평가에 따른 증가(감소)": "fvoci_valuation",
    "매도가능금융자산 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 금융자산의 평가손익": "fvoci_valuation",
    "파생상품평가손익": "cashflow_hedge",
    "현금흐름위험회피손익": "cashflow_hedge",
    "위험회피파생상품평가손익": "cashflow_hedge",

    "배당금": "dividends",
    "주식배당": "stock_dividends",
    "중간배당": "dividends",
    "중간배당금": "dividends",

    "자기주식": "treasury_change",
    "자기주식처분": "treasury_disposed",
    "자기주식의처분": "treasury_disposed",
    "자기주식 거래에 따른 증가(감소)": "treasury_change",
    "자기주식거래": "treasury_change",

    "기초": "beginning_equity",
    "기초잔액": "beginning_equity",
    "기초 자본": "beginning_equity",
    "전기초": "beginning_equity",
    "수정 후 기초자본": "adjusted_beginning",
    "기말": "ending_equity",
    "기말 잔액": "ending_equity",

    "환율변동": "fx_translation",
    "해외사업장환산손익": "fx_translation",
    "해외사업환산외환차이": "fx_translation",
    "해외사업장 환산손익": "fx_translation",
    "해외사업장의 환산손익": "fx_translation",

    "지분법이익잉여금변동": "associate_oci",
    "지분법 자본변동": "associate_oci",
    "지분법이익잉여금 변동": "associate_oci",
    "지분법자본변동액": "associate_oci",
    "관계기업 기타포괄손익에 대한 지분": "associate_oci",
    "지분법 적용 투자지분의 변동": "associate_oci",

    "확정급여제도 재측정요소": "remeasurement_db",
    "확정급여제도의 재측정": "remeasurement_db",
    "확정급여측정": "remeasurement_db",
    "순확정급여부채(자산)의 재측정요소": "remeasurement_db",
    "퇴직급여제도의 재측정요소": "remeasurement_db",

    "재평가잉여금": "revaluation_surplus",
    "토지재평가잉여금": "revaluation_surplus",
    "유형자산재평가잉여금": "revaluation_surplus",
    "유형자산 재평가이익": "revaluation_surplus",

    "연결범위 변동": "consolidation_change",
    "연결실체의변동": "consolidation_change",
    "연결범위변동": "consolidation_change",
    "종속기업 취득": "consolidation_change",
    "종속기업 처분": "consolidation_change",
    "사업결합으로 인한 증가(감소)": "consolidation_change",

    "회계정책변경": "accounting_change",
    "회계정책 변경": "accounting_change",
    "전기오류수정": "error_correction",
    "전기오류수정손익": "error_correction",
    "오류수정": "error_correction",

    "비지배지분의 변동": "nci_change",
    "비지배지분변동": "nci_change",
    "비지배지분의 변동에 따른 증가(감소)": "nci_change",

    "연결실체내자본거래": "intragroup_tx",
    "연결실체 내 자본거래": "intragroup_tx",
    "종속기업 지분변동": "intragroup_tx",
    "지배력을 상실하지 않는 종속기업에 대한 소유지분의 변동": "intragroup_tx",

    "주식선택권 행사": "stock_options",
    "주식선택권행사": "stock_options",
    "주식선택권의 부여": "stock_compensation",
    "주식매수선택권 부여": "stock_compensation",
    "주식선택권 부여": "stock_compensation",

    "신주인수권 행사": "capital_increase",
    "신주인수권대가": "convertible_bond",
    "신주인수권 대가": "convertible_bond",

    "지분법이익잉여금": "associate_oci",

    "순확정급여부채의재측정요소": "remeasurement_db",
    "확정급여채무의 재측정요소": "remeasurement_db",
    "확정급여채무의재측정요소": "remeasurement_db",

    "총포괄손익 합계": "total_comprehensive",
    "총포괄손익 소계": "total_comprehensive",
    "총포괄이익 합계": "total_comprehensive",
    "총 포괄이익": "total_comprehensive",

    "출자전환": "debt_equity_swap",

    "기타포괄손익-공정가치측정금융자산 평가손익": "fvoci_valuation",
    "매도가능금융자산평가이익": "fvoci_valuation",
    "매도가능금융자산 평가이익": "fvoci_valuation",
    "매도가능금융자산의 평가이익": "fvoci_valuation",
    "매도가능금융자산평가이익(손실)": "fvoci_valuation",
    "매도가능금융자산의 공정가치변동": "fvoci_valuation",

    "전환사채 발행": "convertible_bond",
    "복합금융상품 발행": "convertible_bond",
    "복합금융상품발행": "convertible_bond",

    "오류수정에 따른 증가(감소)": "error_correction",
    "전기오류수정에 따른 증가(감소)": "error_correction",

    "소유주와의 거래 총액": "equity_change_total",
    "소유주와의거래총액": "equity_change_total",
    "소유주와의 거래에 의한 증가(감소)": "equity_change_total",

    "해외사업환산이익(손실)": "fx_translation",
    "해외사업환산이익": "fx_translation",
    "해외사업환산차이": "fx_translation",
    "해외사업장 환산차이": "fx_translation",

    "결손보전": "deficit_offset",
    "결손금 보전": "deficit_offset",

    "자기주식처분이익": "treasury_disposed",
    "자기주식처분손실": "treasury_disposed",
    "자기주식 처분이익": "treasury_disposed",

    "분기말자본": "ending_equity",
    "분기말 자본": "ending_equity",
    "반기말자본": "ending_equity",
    "반기말 자본": "ending_equity",

    "기타변동에 따른 증가(감소), 자본": "other",
    "기타사유에 따른 증가(감소)": "other",

    "종속기업의 취득": "consolidation_change",
    "종속기업의 처분": "consolidation_change",
    "종속기업 유상증자": "capital_increase",

    "이익잉여금 처분으로 인한 증감": "retained_earnings_appropriation",
    "이익잉여금처분": "retained_earnings_appropriation",
    "이익잉여금의 처분": "retained_earnings_appropriation",

    "재분류조정": "reclassification",
    "재분류 조정": "reclassification",

    "수정 후 재작성된 금액": "adjusted_beginning",
    "수정후 재작성 금액": "adjusted_beginning",
    "수정재작성": "adjusted_beginning",
    "수정후 금액": "adjusted_beginning",
    "수정 후 금액": "adjusted_beginning",

    "지배력을 상실하지 않는 종속기업에 대한 소유지분의 변동에 따른 증가(감소), 자본": "intragroup_tx",
    "지배력을 상실하지 않는 종속기업에 대한 소유지분의 변동에 따른 증가(감소)": "intragroup_tx",
    "비지배지분과의 거래": "intragroup_tx",
    "비지배지분과의거래": "intragroup_tx",

    "해외사업장환산차이": "fx_translation",
    "해외사업장환산외환차이(세후기타포괄손익)": "fx_translation",
    "해외사업장외화환산차이": "fx_translation",
    "해외사업장 외화환산차이": "fx_translation",
    "해외사업장환산외환차이(세후)": "fx_translation",
    "해외사업장 환산차이": "fx_translation",

    "관계기업 및 공동기업 주식 취득 및 처분": "associate_oci",
    "관계기업의 기타포괄손익에 대한 지분": "associate_oci",
    "부의지분법자본변동": "associate_oci",
    "지분법평가": "associate_oci",
    "지분법 평가": "associate_oci",

    "당기순손익": "net_income",
    "연결당기순이익": "net_income",
    "연결당기순이익(손실)": "net_income",

    "기타포괄손익-공정가치금융자산 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 금융자산 평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 지분상품 평가손익": "fvoci_valuation",
    "매도가능증권평가이익": "fvoci_valuation",
    "매도가능증권평가손실": "fvoci_valuation",
    "매도가능증권 평가이익": "fvoci_valuation",

    "현금흐름위험회피": "cashflow_hedge",
    "현금흐름 위험회피": "cashflow_hedge",

    "회계정책변경의 효과": "accounting_change",
    "회계정책의 변경효과": "accounting_change",
    "회계정책변경효과": "accounting_change",
    "회계정책의 변경": "accounting_change",

    "전환사채의 보통주 전환": "convertible_bond",
    "전환사채발행": "convertible_bond",
    "전환사채전환": "convertible_bond",
    "전환사채 전환": "convertible_bond",

    "소유주와의 거래 합계": "equity_change_total",
    "소유주와의거래합계": "equity_change_total",
    "소유주와의 거래에 따른 총 증가(감소)": "equity_change_total",

    "주식매수선택권행사": "stock_options",
    "주식기준보상거래의 인식": "stock_compensation",
    "주식선택권의 소멸": "stock_compensation",
    "주식선택권 소멸": "stock_compensation",

    "순확정급여제도의 재측정요소": "remeasurement_db",

    "소계": "equity_change_total",

    "합병으로 인한 자본변동": "merger",
    "합병으로 인한 증가": "merger",
    "합병": "merger",
    "합병차익": "merger",
    "합병차손": "merger",

    "비지배지분의 취득": "intragroup_tx",
    "비지배지분 취득": "intragroup_tx",
    "비지배지분의 변동": "nci_change",
    "종속기업지분변동": "intragroup_tx",
    "종속기업 지분의 변동": "intragroup_tx",

    "기타포괄손익-공정가치측정 금융자산평가손익": "fvoci_valuation",
    "기타포괄손익공정가치측정금융자산평가손익": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 금융자산 처분손익": "fvoci_valuation",
    "기타포괄손익-공정가치측정 금융자산 처분손익": "fvoci_valuation",

    "교환권대가": "convertible_bond",
    "교환권 대가": "convertible_bond",

    "소유주와의 거래 소계": "equity_change_total",
    "소유주와의 거래": "equity_change_total",
    "자본에 직접 반영된 소유주와의 거래 등 소계": "equity_change_total",
    "자본에 직접 반영된 소유주와의 거래": "equity_change_total",
    "자본에 직접 인식된 주주와의 거래": "equity_change_total",
    "자본에 직접 인식된 소유주와의 거래": "equity_change_total",

    "현금흐름위험회피 파생상품평가손익": "cashflow_hedge",

    "유형자산재평가이익": "revaluation_surplus",
    "유형자산 재평가이익": "revaluation_surplus",
    "재평가잉여금 변동": "revaluation_surplus",

    "전환사채 상환": "convertible_bond",
    "전환사채의 상환": "convertible_bond",
    "전환사채의전환": "convertible_bond",
    "전환사채 전환(행사)": "convertible_bond",
    "전환상환우선주의 전환": "convertible_bond",
    "전환 권 대가": "convertible_bond",
    "전환권 대가": "convertible_bond",
    "복합금융상품 상환": "convertible_bond",
    "복합금융상품의 상환": "convertible_bond",

    "연차배당금": "dividends",
    "종속기업의 배당": "dividends",
    "종속기업 배당": "dividends",

    "해외산업환산손익": "fx_translation",
    "해외사업환산손실": "fx_translation",
    "해외사업환산": "fx_translation",
    "해외사업환산이익(손실)": "fx_translation",

    "자본 총계": "ending_equity",
    "자본총계 잔액": "ending_equity",

    "주식매수선택권의 부여": "stock_compensation",
    "주식매수선택권 부여": "stock_compensation",
    "주식기준보상 인식": "stock_compensation",

    "총포괄손익합계": "total_comprehensive",

    "적립금의 적립": "retained_earnings_appropriation",
    "적립금 적립": "retained_earnings_appropriation",

    "주식발행초과금": "capital_increase",
    "주식발행": "capital_increase",

    "결손금보전": "deficit_offset",

    "관계기업 기타포괄손익에 대한 지분해당액": "associate_oci",
    "관계기업및공동기업의기타포괄손익에대한지분": "associate_oci",

    "순확정급여의 재측정요소": "remeasurement_db",
    "순확정급여채무의 재측정요소": "remeasurement_db",
    "확정급여제도의 재측정 요소": "remeasurement_db",
    "재측정요소": "remeasurement_db",

    "기타포괄손익 소계": "other_oci",
    "기타포괄손익소계": "other_oci",
    "세후기타포괄이익": "other_oci",

    "주식발행비용": "capital_increase",

    "보고금액": "adjusted_beginning",
    "보고 금액": "adjusted_beginning",

    "전환우선주의 전환": "convertible_bond",
    "전환우선주의 보통주 전환": "convertible_bond",
    "전환사채의 행사": "convertible_bond",
    "신주인수권부사채의 발행": "convertible_bond",
    "신주인수권부사채 발행": "convertible_bond",

    "매도가능금융자산평가손실": "fvoci_valuation",
    "기타포괄손익-공정가치 측정 금융자산": "fvoci_valuation",
    "기타포괄손익-공정가치측정지분증권평가손익": "fvoci_valuation",

    "기타자본조정": "other",
    "기타 자본조정": "other",

    "자본에 직접 반영된 소유주와의 거래 소계": "equity_change_total",

    "신종자본증권발행": "hybrid_issued",
    "신종자본증권 상환": "hybrid_issued",

    "기타자본잉여금": "other",

    "총포괄이익(손실)": "total_comprehensive",
    "총포괄이익 소계": "total_comprehensive",

    "신주청약": "capital_increase",
    "신주청약증거금": "capital_increase",

    "종속기업의 자기주식 취득": "treasury_acquired",
    "종속기업 자기주식 취득": "treasury_acquired",

    "사업결합으로 인한 변동": "consolidation_change",
    "합병으로 인한 변동": "merger",
    "합병으로 인한 증가(감소)": "merger",

    "지분법 이익잉여금 변동": "associate_oci",
    "지분법이익잉여금 변동": "associate_oci",
    "지분법 이익잉여금변동": "associate_oci",

    "자산재평가손익": "revaluation_surplus",
    "유형자산재평가손익": "revaluation_surplus",

    "종속기업에 대한 소유지분의 변동": "intragroup_tx",
    "종속기업에대한 소유지분의 변동": "intragroup_tx",

    "외환차이": "fx_translation",
    "외환환산차이": "fx_translation",

    "주식기준보상거래에 따른 증가(감소)": "stock_compensation",
    "주식기준보상에 따른 증가(감소)": "stock_compensation",
    "주식보상비용의 인식": "stock_compensation",
    "주식보상비용 인식": "stock_compensation",

    "순확정급여부채재측정요소": "remeasurement_db",
    "보험수리적이익(손실)": "remeasurement_db",
    "보험수리적 이익(손실)": "remeasurement_db",
    "보험수리적이익": "remeasurement_db",
    "보험수리적손실": "remeasurement_db",

    "총포괄손익 계": "total_comprehensive",
    "총기타포괄손익": "other_oci",
    "총 기타포괄손익": "other_oci",

    "분기말": "ending_equity",

    "해외사업환산손익의 변동": "fx_translation",
    "해외사업 환산손익": "fx_translation",

    "자본에 직접 반영된 소유주와의 거래 등": "equity_change_total",
    "소유주와의 거래총액": "equity_change_total",

    "주식선택권의행사": "stock_options",
    "주식매입선택권 행사": "stock_options",
    "주식매입선택권의행사": "stock_options",
    "주식매수선택권의행사": "stock_options",

    "교환사채의 발행": "convertible_bond",
    "교환사채의 교환": "convertible_bond",
    "교환사채 발행": "convertible_bond",
    "전환사채의발행": "convertible_bond",
    "전환사채": "convertible_bond",
    "전환사채의 전환권행사": "convertible_bond",

    "신종자본증권배당": "hybrid_interest",
    "신종자본증권상환": "hybrid_issued",
    "신종자본증권 상환": "hybrid_issued",

    "(부의)지분법자본변동": "associate_oci",
    "관계기업자본변동": "associate_oci",
    "관계기업 자본변동": "associate_oci",

    "종속기업유상증자": "capital_increase",

    "이익잉여금 전입": "retained_earnings_appropriation",
    "자본잉여금의 이익잉여금 전입": "retained_earnings_appropriation",

    "주식발행비": "capital_increase",

    "자기주식소각": "treasury_retired",
    "자기주식의소각": "treasury_retired",

    "수정후 재작성된 금액": "adjusted_beginning",

    "기타포괄손익-공정가치측정금융자산처분손익": "fvoci_valuation",

    "토지재평가이익": "revaluation_surplus",
    "토지재평가손익": "revaluation_surplus",
    "토지 재평가이익": "revaluation_surplus",

    "단주취득 및 처분": "treasury_change",
    "단주 취득 및 처분": "treasury_change",

    "신주인수권의행사": "capital_increase",
}


CAUSE_FALLBACK_PATTERNS: list[tuple[str, str]] = [
    ("기초자본", "beginning_equity"),
    ("기초 자본", "beginning_equity"),
    ("기초잔액", "beginning_equity"),
    ("기말자본", "ending_equity"),
    ("기말잔액", "ending_equity"),
    ("기말 자본", "ending_equity"),
    ("분기말", "ending_equity"),
    ("반기말", "ending_equity"),
    ("당기순이익", "net_income"),
    ("당기순손실", "net_income"),
    ("당기순손익", "net_income"),
    ("반기순이익", "net_income"),
    ("분기순이익", "net_income"),
    ("배당금", "dividends"),
    ("배당", "dividends"),
    ("자기주식의 취득", "treasury_acquired"),
    ("자기주식취득", "treasury_acquired"),
    ("자기주식의 처분", "treasury_disposed"),
    ("자기주식처분", "treasury_disposed"),
    ("자기주식의 소각", "treasury_retired"),
    ("자기주식소각", "treasury_retired"),
    ("자기주식", "treasury_change"),
    ("해외사업", "fx_translation"),
    ("외환차이", "fx_translation"),
    ("환산손익", "fx_translation"),
    ("환율변동", "fx_translation"),
    ("확정급여", "remeasurement_db"),
    ("보험수리", "remeasurement_db"),
    ("재측정요소", "remeasurement_db"),
    ("재측정손익", "remeasurement_db"),
    ("지분법", "associate_oci"),
    ("관계기업", "associate_oci"),
    ("공동기업", "associate_oci"),
    ("공정가치", "fvoci_valuation"),
    ("매도가능", "fvoci_valuation"),
    ("파생상품평가", "cashflow_hedge"),
    ("위험회피", "cashflow_hedge"),
    ("주식기준보상", "stock_compensation"),
    ("주식보상비용", "stock_compensation"),
    ("주식선택권", "stock_options"),
    ("주식매수선택권", "stock_options"),
    ("주식매입선택권", "stock_options"),
    ("전환사채", "convertible_bond"),
    ("전환권", "convertible_bond"),
    ("전환우선주", "convertible_bond"),
    ("교환사채", "convertible_bond"),
    ("교환권", "convertible_bond"),
    ("신주인수권", "capital_increase"),
    ("유상증자", "capital_increase"),
    ("무상증자", "capital_increase"),
    ("신종자본증권", "hybrid_issued"),
    ("영구채", "hybrid_interest"),
    ("총포괄", "total_comprehensive"),
    ("포괄손익", "total_comprehensive"),
    ("포괄이익", "total_comprehensive"),
    ("연결실체", "consolidation_change"),
    ("연결범위", "consolidation_change"),
    ("사업결합", "consolidation_change"),
    ("합병", "merger"),
    ("회계정책", "accounting_change"),
    ("오류수정", "error_correction"),
    ("소유주와의 거래", "equity_change_total"),
    ("비지배지분", "nci_change"),
    ("재평가", "revaluation_surplus"),
    ("출자전환", "debt_equity_swap"),
    ("종속기업", "intragroup_tx"),
    ("지배력을 상실", "intragroup_tx"),
    ("결손보전", "deficit_offset"),
    ("결손금보전", "deficit_offset"),
    ("결손금처리", "deficit_offset"),
    ("분기순손익", "net_income"),
    ("분기순이익", "net_income"),
    ("분기순손실", "net_income"),
    ("반기순손익", "net_income"),
    ("반기순손실", "net_income"),
    ("반기순이익", "net_income"),
    ("이익소각", "treasury_retired"),
    ("인적분할", "spinoff"),
    ("물적분할", "spinoff"),
    ("분할", "spinoff"),
    ("신주발행비", "capital_increase"),
    ("주식할인발행", "capital_increase"),
    ("주식병합", "capital_increase"),
    ("이익잉여금 전입", "retained_earnings_appropriation"),
    ("준비금의 적립", "retained_earnings_appropriation"),
    ("적립금 적립", "retained_earnings_appropriation"),
    ("기타조정", "other"),
    ("조정금액", "other"),
    ("수정후금액", "adjusted_beginning"),
    ("수정후 금액", "adjusted_beginning"),
    ("분기초", "beginning_equity"),
    ("반기초", "beginning_equity"),
    ("전환상환우선주", "convertible_bond"),
    ("전환청구권", "convertible_bond"),
    ("보험계약", "other_oci"),
    ("지분변동", "intragroup_tx"),
    ("자본에 직접 인식", "equity_change_total"),
    ("자본에 직접 반영", "equity_change_total"),
    ("소유주에 의한", "equity_change_total"),
]


_CAUSE_NOSPACE: dict[str, str] = {
    k.replace(" ", ""): v for k, v in CAUSE_SYNONYMS.items()
}


DETAIL_MAP: dict[str, str] = {
    "자본금": "share_capital",
    "주식발행초과금": "share_premium",
    "자본잉여금": "capital_surplus",
    "이익잉여금": "retained_earnings",
    "결손금": "retained_earnings",
    "기타자본구성요소": "other_equity",
    "기타자본항목": "other_equity",
    "기타자본": "other_equity",
    "기타불입자본": "other_equity",
    "자본조정": "other_equity",
    "적립금": "other_equity",
    "기타포괄손익누계액": "accumulated_oci",
    "기타포괄손익누적액": "accumulated_oci",
    "기타포괄손익누계": "accumulated_oci",
    "자기주식": "treasury_stock",
    "비지배지분": "noncontrolling_interest",
    "비지배주주지분": "noncontrolling_interest",
    "지배기업 소유주지분": "owners_equity",
    "지배기업의 소유주에게 귀속되는 지분": "owners_equity",
    "지배기업의 소유주에게 귀속되는 자본": "owners_equity",
    "지배기업소유주지분": "owners_equity",
    "지배기업의 소유주지분": "owners_equity",
    "지배기업 소유주 귀속분": "owners_equity",
    "지배기업의 소유주에게 귀속되는 지분의": "owners_equity",
    "납입자본": "capital_surplus",
    "추가납입자본": "capital_surplus",
    "추가 납입자본": "capital_surplus",
    "기타불입자본금": "capital_surplus",
    "이익준비금": "retained_earnings",
    "임의적립금": "retained_earnings",
    "미처분이익잉여금": "retained_earnings",
    "미처리결손금": "retained_earnings",
    "처분후이익잉여금": "retained_earnings",
    "이익잉여금(결손금)": "retained_earnings",
    "주식선택권": "other_equity",
    "주식매수선택권": "other_equity",
    "자본에 직접 반영된 소유주와의 거래": "other_equity",
    "기타포괄손익": "accumulated_oci",
    "기타포괄손익누계": "accumulated_oci",
    "기타포괄손익항목": "accumulated_oci",
    "기타의포괄손익누계액": "accumulated_oci",
    "지배주주지분": "owners_equity",
    "지배기업소유지분": "owners_equity",
    "지배기업 소유주 지분": "owners_equity",
    "지배기업의 소유주에게 귀속되는 자본의": "owners_equity",
    "지배기업의소유주에게귀속되는지분": "owners_equity",
    "지배기업 소유주에게 귀속되는 자본": "owners_equity",
    "지배기업소유주에게 귀속되는 지분": "owners_equity",
    "신종자본증권": "hybrid_capital",
    "영구채": "hybrid_capital",
    "매각예정분류기타자본항목": "held_for_sale",
    "매각예정으로 분류된 비유동자산 또는 처분자산집단과 관련하여 기타포괄손익으로 인식되어 자본에 누적된 금액": "held_for_sale",
    "재평가잉여금": "revaluation_surplus",
    "토지재평가잉여금": "revaluation_surplus",
    "기타의자본항목": "other_equity",
    "기타의 자본항목": "other_equity",
    "기타자본잉여금": "capital_surplus",
    "감자차익": "capital_surplus",
    "전환권대가": "other_equity",
    "신주인수권대가": "other_equity",
}


def normalizeCause(accountNm: str) -> str:
    """account_nm → 변동사유 snakeId.

    3-tier 매칭: 정확 → 공백 제거 → fallback 패턴.
    미매핑 시 'unmapped:{원본}' 반환.
    """
    nm = accountNm.strip()
    if nm in CAUSE_SYNONYMS:
        return CAUSE_SYNONYMS[nm]

    noSpace = nm.replace(" ", "")
    if noSpace in _CAUSE_NOSPACE:
        return _CAUSE_NOSPACE[noSpace]

    for pattern, snakeId in CAUSE_FALLBACK_PATTERNS:
        if pattern in nm:
            return snakeId

    return f"unmapped:{nm}"


def normalizeDetail(detail: str | None) -> str:
    """account_detail → 자본항목 snakeId.

    파이프(|) 구분 마지막 세그먼트에서 DETAIL_MAP → fallback 패턴.
    미매핑 시 'unmapped:{원본}' 반환.
    """
    if not detail:
        return "unknown"

    detail = detail.replace("\u3000", " ").strip()

    if re.search(r"연결재무제표\s*\[", detail):
        return "total"
    if re.search(r"별도재무제표\s*\[", detail):
        return "total_separate"

    cleaned = re.sub(r"\s*\[(member|구성요소|구성 요소)\]", "", detail)
    parts = [p.strip() for p in cleaned.split("|") if p.strip()]

    if not parts:
        return "unknown"

    last = parts[-1]

    for key, val in DETAIL_MAP.items():
        if key in last:
            return val

    lastNoSpace = last.replace(" ", "")
    for key, val in DETAIL_MAP.items():
        if key.replace(" ", "") in lastNoSpace:
            return val

    if "자본" in last and ("소유주" in last or "지배" in last):
        return "owners_equity"
    if "지배" in last and ("지분" in last or "귀속" in last or "소유" in last):
        return "owners_equity"
    if "지배기업" in last and len(last) < 15:
        return "owners_equity"
    if last in ("소계", "합계", "총계"):
        return "owners_equity"
    if "전환권" in last or "신주인수권" in last:
        return "other_equity"
    if "매도가능" in last and ("평가" in last or "손익" in last):
        return "accumulated_oci"
    if "해외사업" in last and "환산" in last:
        return "accumulated_oci"
    if "지분법" in last and ("자본" in last or "변동" in last):
        return "accumulated_oci"
    if "감자차" in last:
        return "capital_surplus"
    if last == "기타":
        return "other_equity"
    if "주식매입선택권" in last or "주식매수선택권" in last:
        return "other_equity"
    if "잉여금" in last:
        return "retained_earnings"
    if "합병" in last and "차" in last:
        return "capital_surplus"
    if "할인발행" in last:
        return "capital_surplus"
    if "주식발행" in last and ("초과" in last or "과" in last):
        return "share_premium"
    if "불입자본" in last or "불입 자본" in last:
        return "capital_surplus"
    if "매각예정" in last:
        return "held_for_sale"
    if "공정가치" in last and ("평가" in last or "손익" in last):
        return "accumulated_oci"
    if "파생상품" in last and "평가" in last:
        return "accumulated_oci"
    if "종속기업" in last and ("취득" in last or "추가" in last):
        return "other_equity"
    if "소유주" in last and "자본" in last:
        return "owners_equity"
    if "기타 자본" in last or "기타자본" in last:
        return "other_equity"
    if "기타지분" in last:
        return "other_equity"
    if "외부주주" in last or "소수주주" in last:
        return "noncontrolling_interest"
    if "비지배주주" in last or "비지배" in last:
        return "noncontrolling_interest"
    if last == "자본" or last == "자본 조정":
        return "other_equity"
    if "포괄손익누계" in last:
        return "accumulated_oci"
    if "연결" in last and "포괄" in last:
        return "accumulated_oci"
    if "외화환산" in last or "해외환산" in last or "환산손익" in last:
        return "accumulated_oci"
    if "불입자금" in last or "불입자본" in last:
        return "capital_surplus"
    if "재평가" in last and ("차익" in last or "이익" in last):
        return "revaluation_surplus"
    if "소유주귀속" in last or "소유주 귀속" in last:
        return "owners_equity"
    if "자본합계" in last:
        return "owners_equity"
    if "종속기업" in last and ("평가" in last or "손실" in last):
        return "other_equity"
    if "이익영여금" in last:
        return "retained_earnings"
    if "총자본" in last:
        return "owners_equity"
    if "자기조정" in last or "자본조" in last:
        return "other_equity"
    if "주식기준보상" in last or "주식결제형" in last or "종업원급여" in last:
        return "other_equity"
    if "지배주주" in last:
        return "owners_equity"
    if "비재비지분" in last or "비지배" in last:
        return "noncontrolling_interest"
    if "현금흐름위험회피" in last:
        return "accumulated_oci"
    if "연구인력" in last or "개발준비금" in last:
        return "retained_earnings"
    if "FV_OCI" in last or "FVOCI" in last:
        return "accumulated_oci"
    if "기타의자본" in last:
        return "other_equity"
    if "출자전환" in last:
        return "other_equity"
    if "기타" == last.strip():
        return "other_equity"

    return f"unmapped:{last}"
