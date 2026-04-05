"""review 템플릿 -- 섹션별 블록 조합 + helper/aiGuide.

블록 메타(key, label, 순서)와 섹션 메타(title, partId)는 catalog.py가 source of truth.
이 파일은 각 섹션에서 **실제로 보여줄 블록 서브셋**과 helper/aiGuide만 관리한다.

c.review("수익구조") -> 수익구조 템플릿의 visibleKeys 블록만 조립.
c.review()           -> 전체 템플릿 순서대로 조립.
"""

from __future__ import annotations

from dartlab.review.catalog import SECTIONS, keysForSection

# ── 섹션별 설정 (helper, aiGuide, visibleKeys) ──
# visibleKeys: 이 섹션에서 실제로 보여줄 블록. None이면 섹션 전체 블록.

_SECTION_CONFIG: dict[str, dict] = {
    "수익구조": {
        "visibleKeys": None,  # 전체 표시
        "helper": (
            "① 매출 집중도(HHI)와 부문별 이익률 차이로 수익 구조 편중을 본다 (HHI 0.25 이상이면 집중, 0.01 이하면 분산)\n"
            "② 부문별 매출 추이와 YoY(전년 대비 증감률)로 성장 부문을 식별한다\n"
            "③ 매출 성장률(YoY, 3Y CAGR)로 중기 방향성을 본다 (CAGR = 3년 연평균 성장률)\n"
            "④ 성장 기여 분해로 어디에서 성장이 왔는지 본다\n"
            "⑤ 영업CF/순이익, 총이익률 추세로 매출 품질을 확인한다 (100% 미만이면 이익의 현금 뒷받침 부족)"
        ),
        "aiGuide": (
            "매출 집중도(HHI)가 높으면 단일 부문 의존 리스크를 짚어라. "
            "부문별 이익률 차이가 크면 수익 구조 편중을 언급하라. "
            "성장 부문과 정체 부문을 구분하고, 매출 YoY/3Y CAGR 방향성을 평가하라. "
            "내수/수출 비중이 한쪽으로 치우치면 지역 리스크를 언급하라. "
            "영업CF/순이익이 40% 미만이면 이익의 현금 뒷받침 부족을 경고하라. "
            "총이익률이 악화 추세면 원가 구조 변화를 짚어라."
        ),
    },
    "자금조달": {
        "visibleKeys": [
            "fundingSources",
            "capitalTimeline",
            "debtTimeline",
            "interestBurden",
            "liquidity",
            "capitalFlags",
        ],
        "helper": (
            "① 내부유보/주주자본/금융차입/영업조달 4원천 비중을 본다\n"
            "② 이익잉여금 비중이 높으면 자기 힘으로 성장\n"
            "③ 금융차입 비중이 높으면 이자보상배율과 만기를 확인한다\n"
            "④ 유동비율로 단기 지급 능력을 확인한다"
        ),
        "aiGuide": (
            "내부유보 vs 금융차입 비중으로 자금조달 성격을 먼저 판단하라. "
            "이익잉여금이 자산의 50% 이상이면 자기 힘으로 성장한 회사다. "
            "금융차입 40% 이상이면 이자보상배율과 차환 리스크를 반드시 짚어라. "
            "영업조달(매입채무·선수금)이 크면 영업력으로 자금을 조달하는 구조다. "
            "비중 추이에서 금융차입이 늘고 내부유보가 줄면 자금조달 구조 악화 신호다."
        ),
    },
    "자산구조": {
        "visibleKeys": None,  # 전체 표시
        "helper": (
            "① BS를 영업/비영업으로 재분류해 자산의 실질 성격을 본다\n"
            "② 순영업자산(NOA)이 투자 대비 수익의 분모다 (NOA = 영업자산 - 영업부채)\n"
            "③ 운전자본 순환(CCC)으로 영업 효율을 본다 (CCC = 재고일수 + 매출채권일수 - 매입채무일수. 짧을수록 현금 회수가 빠름)\n"
            "④ CAPEX/감가상각으로 성장투자인지 유지투자인지 판단한다 (1 미만이면 유지, 1.5 이상이면 공격 투자)\n"
            "⑤ 자산회전율로 같은 자산으로 매출을 더 뽑는지 본다"
        ),
        "aiGuide": (
            "영업자산 비중이 높으면 사업 집중 구조, 비영업 비중이 높으면 지주/투자 성격을 짚어라. "
            "건설중인자산이 크면 대규모 투자 진행 중이며 향후 감가상각 부담을 언급하라. "
            "CCC가 길어지면 현금 회수 느림, 마이너스면 선수금/매입채무 우위 구조다. "
            "CAPEX/감가상각이 1 미만이면 유지투자(자산 노후화), 1.5 이상이면 공격적 성장 투자다. "
            "총자산회전율이 하락하면 자산 팽창 대비 매출 성장이 부족한 신호다."
        ),
    },
    "현금흐름": {
        "visibleKeys": None,  # 전체 표시
        "helper": (
            "① 영업CF/투자CF/재무CF 부호 조합으로 CF 패턴을 본다\n"
            "② FCF(=영업CF-CAPEX)가 양수면 자유현금 창출 능력 있음\n"
            "③ 영업CF/순이익으로 이익이 현금으로 뒷받침되는지 확인한다\n"
            "④ 영업CF 마진으로 매출 대비 현금 창출력을 본다"
        ),
        "aiGuide": (
            "영업CF가 적자면 본업에서 현금이 나오지 않는 위험 신호다. "
            "FCF가 음수면 영업으로 번 것보다 투자가 크다는 뜻이므로 외부 자금 의존도를 확인하라. "
            "CF 패턴이 확장형(+/-/+)이면 성장 투자 중이므로 투자 효율을 짚어라. "
            "위기형(-/-/+)이면 영업 적자를 차입으로 메우는 구조이므로 지속 가능성을 경고하라. "
            "영업CF/순이익이 100% 미만이면 이익의 현금 전환이 부족하다. "
            "40% 미만이면 이익의 질에 심각한 의문을 제기하라."
        ),
    },
    # ── 2부: 재무비율 분석 ──
    "수익성": {
        "visibleKeys": None,
        "helper": (
            "① 매출총이익률/영업이익률/순이익률 추이로 마진 방향을 본다\n"
            "② ROE/ROA 추이로 투하자본 대비 수익력을 본다 (ROE = 자기자본이익률, ROA = 총자산이익률)\n"
            "③ 듀퐁 분해로 ROE의 원천을 파악한다 (ROE = 순이익률 x 자산회전율 x 재무레버리지)"
        ),
        "aiGuide": (
            "영업이익률이 3년 연속 하락이면 원가/경쟁 구조 변화를 짚어라. "
            "ROE > 15%이면서 레버리지(ROE/ROA)가 3배 이상이면 부채로 만든 수익성이다. "
            "듀퐁 분해에서 마진 개선 없이 레버리지로만 ROE가 올랐다면 경고하라. "
            "매출총이익률이 안정적인데 영업이익률만 하락이면 판관비 구조를 지적하라."
        ),
    },
    "성장성": {
        "visibleKeys": None,
        "helper": (
            "① 매출/영업이익/순이익 YoY로 성장 속도를 본다\n"
            "② 매출 성장 > 이익 성장이면 외형만 커진 것\n"
            "③ CAGR로 단기 변동 너머의 중기 추세를 확인한다"
        ),
        "aiGuide": (
            "매출 성장률이 영업이익 성장률보다 높으면 수익성 희석을 짚어라. "
            "3Y CAGR이 음수면 구조적 역성장이다. "
            "순이익 성장이 영업이익 성장보다 훨씬 높으면 영업외이익 의존을 경고하라. "
            "자산 성장이 매출 성장보다 빠르면 비효율적 확장이다."
        ),
    },
    "안정성": {
        "visibleKeys": None,
        "helper": (
            "① 부채비율 추이로 재무 레버리지 방향을 본다 (부채비율 = 부채/자본, 200% 이상이면 주의)\n"
            "② 이자보상배율로 이자 지급 능력을 본다 (영업이익/이자비용, 3배 미만이면 부담)\n"
            "③ Altman Z-Score로 부실 가능성을 정량 판별한다 (1.8 미만 위험, 3.0 이상 안전)\n"
            "④ 시장 리스크(베타, 변동성)로 시장 관점 안정성을 확인한다"
        ),
        "aiGuide": (
            "부채비율이 200% 이상이면 재무 위험을 짚어라. "
            "이자보상배율이 3배 미만이면 이자 지급 부담을 경고하라. "
            "Altman Z-Score가 1.8 미만이면 부실 위험 구간이다. "
            "차입금의존도가 30% 이상이면 금융차입에 과도하게 의존하는 구조다. "
            "베타가 1.5 이상이면 시장 급락 시 더 큰 손실 가능성을 경고하라. "
            "변동성(ATR%)이 5% 이상이면 일일 가격 변동이 큰 종목임을 짚어라."
        ),
    },
    "효율성": {
        "visibleKeys": None,
        "helper": (
            "① 총자산/매출채권/재고 회전율로 자산 활용도를 본다 (높을수록 자산을 잘 굴리는 것)\n"
            "② CCC로 현금이 묶이는 기간을 본다 (CCC = DSO + DIO - DPO, 짧을수록 좋음)\n"
            "③ 회전율 하락 + CCC 증가면 영업 효율 악화 신호"
        ),
        "aiGuide": (
            "총자산회전율이 하락 추세면 자산 팽창 대비 매출 부진을 짚어라. "
            "매출채권 회전율 하락은 대금 회수 지연을 의미한다. "
            "재고 회전율 하락은 재고 적체 위험이다. "
            "CCC가 마이너스면 선수금/매입채무 우위로 운전자본이 유리한 구조다."
        ),
    },
    "종합평가": {
        "visibleKeys": None,
        "helper": (
            "① 5영역(수익성/성장성/안정성/효율성/현금흐름) 등급으로 전체를 본다\n"
            "② Piotroski F-Score(0-9)로 재무 건전성을 정량 판별한다 (7점 이상 건전, 3점 이하 심각)"
        ),
        "aiGuide": (
            "스코어카드에서 F 등급이 있는 영역을 최우선으로 짚어라. "
            "Piotroski F-Score 3점 이하면 재무 상태가 심각하게 나쁘다. "
            "7점 이상이면 재무적으로 건전한 기업이다. "
            "등급 간 괴리(수익성 A인데 안정성 F)가 있으면 구조적 불균형을 경고하라."
        ),
    },
    # ── 3부: 심화 분석 ──
    "이익품질": {
        "visibleKeys": None,
        "helper": (
            "① Sloan 발생액비율로 이익 중 현금이 아닌 비중을 본다 (높으면 이익이 장부상 숫자일 뿐, 0.10 이상 주의)\n"
            "② 영업외손익 비중과 이익 변동성으로 지속성을 판단한다\n"
            "③ Beneish M-Score로 이익 조작 가능성을 정량 점검한다 (-1.78 초과 시 조작 가능성 구간)"
        ),
        "aiGuide": (
            "발생액비율이 0.10 이상이면 이익 현금화 부족을 짚어라. "
            "영업외손익 비중이 30% 이상이면 일회성 이익 의존을 경고하라. "
            "M-Score가 -1.78 초과면 이익 조작 가능성 구간이므로 반드시 언급하라. "
            "이익 변동계수(CV)가 0.5 이상이면 실적 변동성이 크다."
        ),
    },
    "비용구조": {
        "visibleKeys": None,
        "helper": (
            "① 매출원가율/판관비율 추이로 비용 구조 변화를 본다\n"
            "② DOL(영업레버리지)로 매출 변동 대비 이익 민감도를 본다 (DOL 3 이상이면 매출 감소 시 이익 급감)\n"
            "③ BEP와 안전마진으로 손익분기 여유를 확인한다 (BEP = 손익분기 매출, 안전마진 = 현재 매출이 BEP를 넘는 여유)"
        ),
        "aiGuide": (
            "매출원가율이 3년 연속 상승이면 원가 경쟁력 약화를 짚어라. "
            "판관비율 상승은 판매/관리 비효율을 의미한다. "
            "DOL이 3 이상이면 매출 감소 시 이익이 급감할 수 있다. "
            "안전마진이 10% 미만이면 손익분기점에 근접해 리스크가 크다."
        ),
    },
    "자본배분": {
        "visibleKeys": None,
        "helper": (
            "① 배당성향과 연속 배당으로 배당 정책을 판단한다\n"
            "② 총주주환원(배당+자사주)과 FCF 비교로 환원 여력을 본다\n"
            "③ CAPEX/매출과 유보율로 재투자 의지를 확인한다\n"
            "④ FCF 사용처(배당/부채상환/잔여)로 경영 우선순위를 본다"
        ),
        "aiGuide": (
            "배당성향 100% 초과면 이익 이상의 배당이므로 지속 가능성을 의심하라. "
            "총환원/FCF가 100% 초과면 외부 자금으로 환원하는 구조다. "
            "CAPEX/매출이 1% 미만이면 극소 투자로 성장 동력 부족을 짚어라. "
            "배당이 3년 연속 감소면 주주 가치 환원 약화를 경고하라. "
            "잔여(FCF-배당-상환)가 꾸준히 양수면 현금 축적 능력이 있다."
        ),
    },
    "투자효율": {
        "visibleKeys": None,
        "helper": (
            "① ROIC vs WACC Spread로 가치 창출/파괴를 판단한다 (ROIC = 투하자본수익률, WACC = 가중평균자본비용. ROIC > WACC면 가치 창출)\n"
            "② CAPEX/매출과 유무형자산 비율로 투자 강도를 본다\n"
            "③ EVA로 자본비용 차감 후 실질 가치를 확인한다 (EVA = NOPAT - 자본비용, 양수면 가치 창출)"
        ),
        "aiGuide": (
            "ROIC < WACC이 2년 연속이면 투자한 자본이 가치를 파괴하고 있다. "
            "EVA가 3년 연속 음수면 경제적 부가가치 적자 상태다. "
            "무형자산비율이 전년 대비 10%p 이상 급등하면 대규모 인수를 확인하라. "
            "WACC은 추정치이므로 절대 수치보다 추세와 방향성을 강조하라."
        ),
    },
    "재무정합성": {
        "visibleKeys": None,
        "helper": (
            "① IS-CF 괴리로 순이익 대비 현금 뒷받침을 검증한다 (IS = 손익계산서, CF = 현금흐름표. 괴리가 크면 이익의 질 의심)\n"
            "② 매출 vs 매출채권/재고 성장 괴리로 이상 징후를 포착한다 (채권/재고가 매출보다 빨리 늘면 주의)\n"
            "③ 종합 이상점수로 교차검증 결과를 한눈에 본다 (0-100, 70 이상이면 재무제표 신뢰성 주의)\n"
            "④ 유효세율과 이연법인세로 세금 리스크를 확인한다"
        ),
        "aiGuide": (
            "IS-CF 괴리가 50% 이상이면 순이익의 현금 뒷받침이 심각하게 부족하다. "
            "매출채권 성장이 매출보다 20%p 빠르면 매출 인식 방식을 의심하라. "
            "재고 성장이 매출보다 20%p 빠르면 판매 부진 또는 재고 부풀리기를 짚어라. "
            "이상점수 70 이상이면 재무제표 전체 신뢰성에 주의를 환기하라. "
            "유효세율이 10% 미만이면 세금 혜택 또는 이연의 원인을 짚어라. "
            "이연법인세자산 급증은 미래 과세소득을 낙관하고 있을 수 있다."
        ),
    },
    # ── 5부: 비재무 심화 ──
    "지배구조": {
        "visibleKeys": None,
        "helper": (
            "1 최대주주 지분율 추이로 지배구조 안정성을 본다\n"
            "2 사외이사비율로 이사회 독립성을 판단한다\n"
            "3 감사의견과 감사인 변경 이력으로 외부 감시를 확인한다"
        ),
        "aiGuide": (
            "최대주주 지분율이 50% 초과면 과반 지배 구조의 장단점을 짚어라. "
            "20% 미만이면 경영권 방어 취약 가능성을 언급하라. "
            "사외이사비율 25% 미만이면 이사회 독립성 부족을 경고하라. "
            "감사의견이 적정이 아니면 반드시 그 사유를 짚어라. "
            "감사인 잦은 변경은 감사 독립성 의심 신호다."
        ),
    },
    "공시변화": {
        "visibleKeys": None,
        "helper": (
            "1 전체 topic 변화율로 공시 성실도를 본다\n"
            "2 사업개요/리스크/회계정책 등 핵심 topic 변화를 추적한다\n"
            "3 바이트 변화량으로 실질적 변경 규모를 확인한다"
        ),
        "aiGuide": (
            "전 기간 공시 텍스트 변화가 전무하면 보일러플레이트(복붙) 가능성을 지적하라. "
            "회계정책 공시 변경이 감지되면 정책 변경 여부를 반드시 확인하라. "
            "사업개요/리스크 topic이 자주 바뀌면 사업 환경 변동이 큰 것이다. "
            "변화율 80% 이상 topic은 빈번한 변경 사유를 짚어라."
        ),
    },
    "비교분석": {
        "visibleKeys": None,
        "helper": (
            "1 핵심 비율의 시장 내 백분위로 상대적 위치를 본다\n"
            "2 ROE x 부채비율 사분면으로 수익-위험 포지션을 판단한다\n"
            "3 상위/하위 10% 지표를 통해 강점과 약점을 식별한다"
        ),
        "aiGuide": (
            "상위 10% 지표는 강점으로, 하위 10%는 개선 과제로 짚어라. "
            "고수익-저위험 사분면이면 우량 포지션으로 평가하라. "
            "저수익-고위험이면 구조적 개선 필요성을 경고하라. "
            "백분위는 전종목 기준이므로 업종 특성(금융업 등)을 감안하라."
        ),
    },
    "신용평가": {
        "visibleKeys": None,
        "helper": (
            "① 20단계 신용등급(AAA~D)으로 기업의 채무상환 능력을 종합 판정한다\n"
            "② 5축(채무상환 35%/레버리지 25%/유동성 15%/부실모델 15%/이익품질 10%)으로 점수를 산출한다\n"
            "③ 업종별 차등 기준을 적용한다 (유틸리티/금융은 높은 부채 허용)\n"
            "④ eCR(현금흐름등급)로 현금흐름창출능력을 별도 평가한다\n"
            "⑤ 등급 전망(안정적/긍정적/부정적)으로 향후 방향을 제시한다"
        ),
        "aiGuide": (
            "등급이 투자적격(BBB- 이상)인지 투기등급(BB+ 이하)인지 명확히 구분하라. "
            "ICR < 1.5이면 이자 지급 능력 부족을 최우선으로 경고하라. "
            "Debt/EBITDA > 5이면 부채 감당 능력 부족을 짚어라. "
            "eCR-4 이하이면 현금흐름 악화를 언급하라. "
            "등급 전망이 부정적이면 하방 압력 요인을 구체적으로 설명하라. "
            "5축 중 점수가 가장 높은(위험한) 축을 핵심 리스크로 짚어라. "
            "업종 특성(금융업 부채비율 400% 허용 등)을 반영하여 해석하라."
        ),
    },
    # ── 4부: 가치평가 ──
    "가치평가": {
        "visibleKeys": None,
        "helper": (
            "① DCF로 FCF 기반 내재가치를 추정한다 (DCF = 미래 현금흐름을 할인해 현재 가치로 환산)\n"
            "② DDM으로 배당 기반 가치를 본다 (DDM = 미래 배당금을 할인해 적정 주가 산출)\n"
            "③ 상대가치(PER/PBR/EV-EBITDA/PSR/PEG)로 섹터 대비 위치를 본다\n"
            "④ RIM으로 자기자본 대비 초과이익 가치를 본다 (RIM = 장부가 + 초과이익의 현재가치)\n"
            "⑤ 목표주가로 5 시나리오 확률 가중 적정가를 본다\n"
            "⑥ 민감도 그리드로 가정 변화에 따른 가치 범위를 확인한다\n"
            "⑦ 종합 판정으로 저/적정/고평가를 판단한다"
        ),
        "aiGuide": (
            "DCF와 상대가치 결과가 크게 다르면 어느 모델의 가정이 더 적합한지 설명하라. "
            "안전마진 30% 이상이면 저평가 가능성을 짚되, 가정(할인율/성장률) 민감도도 함께 언급하라. "
            "DDM 적용 불가면 무배당 기업임을 짚고 DCF/상대가치에 집중하라. "
            "PEG 1.0 미만이면 성장 대비 저평가, 2.0 이상이면 성장 대비 고평가 가능성. "
            "역내재성장률이 엔진 예측보다 낮으면 시장이 보수적, 높으면 시장이 낙관적. "
            "민감도 그리드에서 모든 시나리오가 현재가 이하면 구조적 고평가를 경고하라. "
            "종합 판정은 참고용이며 투자 권유가 아님을 명시하라."
        ),
    },
    # ── 6부: 전망분석 ──
    "매출전망": {
        "visibleKeys": None,
        "helper": (
            "-- 이 섹션의 모든 수치는 추정치이며 실제 실적과 다를 수 있습니다 --\n"
            "(1) Base/Bull/Bear 3-시나리오 매출 전망과 확률을 본다\n"
            "(2) 세그먼트별 성장률로 성장 동력을 식별한다\n"
            "(3) Pro-Forma로 매출 성장이 영업이익/FCF에 미치는 영향을 본다\n"
            "(4) 소스 가중치와 신뢰도로 예측의 근거를 확인한다"
        ),
        "aiGuide": (
            "모든 예측값은 '추정'임을 명시하라. "
            "신뢰도 'low'면 데이터 부족을 강조하라. "
            "소스에서 timeseries만 100%면 컨센서스/매크로 부재를 짚어라. "
            "시나리오 간 격차가 크면 불확실성이 높다는 의미다. "
            "Pro-Forma 비율 가정이 과거와 크게 다르면 한계를 밝혀라."
        ),
    },
    # ── 7부: 시장분석 ──
    "시장분석": {
        "visibleKeys": None,
        "helper": (
            "① 기술적 종합 판단(강세/중립/약세)으로 시장의 방향성을 본다\n"
            "② 매매 신호(골든크로스/RSI/MACD/볼린저)로 최근 전환점을 식별한다\n"
            "③ 베타로 시장 대비 변동성, CAPM으로 기대수익률을 확인한다\n"
            "④ 재무-시장 괴리 진단으로 펀더멘털과 시장 반응의 불일치를 분석한다"
        ),
        "aiGuide": (
            "기술적 판단은 참고 지표이며 투자 권유가 아님을 반드시 명시하라. "
            "재무-시장 괴리가 발생하면 양쪽의 근거를 균형있게 제시하라. "
            "재무 우량 + 기술적 약세면 '저평가 기회 또는 시장이 선행 반영한 리스크'로 양면 해석하라. "
            "재무 부진 + 기술적 강세면 '기술적 반등이지만 펀더멘털 리스크 주의'로 경고하라. "
            "베타 1.5 이상이면 시장 변동 대비 고위험 종목임을 짚어라. "
            "RSI 70 이상 + 가치평가 고평가면 과열 신호를 강화하라. "
            "RSI 30 이하 + 가치평가 저평가면 역발상 투자 기회 가능성을 언급하라."
        ),
    },
}


def _buildTemplates() -> dict[str, dict]:
    """catalog SECTIONS 순서로 TEMPLATES dict 생성."""
    templates: dict[str, dict] = {}
    for sec in SECTIONS:
        cfg = _SECTION_CONFIG.get(sec.key, {})
        visible = cfg.get("visibleKeys")
        if visible is None:
            keys = keysForSection(sec.key)
        else:
            keys = list(visible)
        templates[sec.key] = {
            "title": sec.title,
            "partId": sec.partId,
            "keys": keys,
            "helper": cfg.get("helper", ""),
            "aiGuide": cfg.get("aiGuide", ""),
        }
    return templates


TEMPLATES = _buildTemplates()
TEMPLATE_ORDER = [s.key for s in SECTIONS]


# ── 스토리 템플릿 — 기업 특성별 강조/축소 ──
# 6막 순서는 불변. emphasize된 블록에 시각적 표시 + aiGuide 조정.

STORY_TEMPLATES: dict[str, dict] = {
    "사이클": {
        "description": "업황 사이클이 전부 — 반도체/화학/조선 등",
        "emphasize": {
            "segmentComposition",
            "segmentTrend",
            "marginTrend",
            "capexPattern",
            "workingCapital",
            "roicTree",
            "technicalSignals",
            "marketBeta",
        },
        "keyQuestions": [
            "현재 사이클 어디에 있는가 (정점/저점/회복/하강)?",
            "이 사이클의 진폭은 어느 정도인가?",
            "다운턴에서 현금흐름이 버티는가?",
            "CAPEX 사이클이 업황과 얼마나 동조하는가?",
        ],
        "actFocus": {
            "1": "부문별 매출 변동 진폭 + 재고 사이클",
            "2": "마진 변동계수 + 고정비/변동비 구조 — 업황 호전기 확대 폭과 하락기 방어력",
            "3": "다운턴 시 FCF 방어력 — 감가상각이 현금 버퍼 역할을 하는가",
            "5": "CAPEX 타이밍 — 사이클 저점에서 투자하는가, 아니면 호황기에 과잉 투자하는가",
        },
        "industryContext": "반도체/화학/조선은 3-5년 사이클. 재고일수와 가동률이 선행지표.",
        "peerAxes": ["operatingMargin", "capexToRevenue", "inventoryDays"],
    },
    "프랜차이즈": {
        "description": "안정 수익 + 현금 기계 — 프랜차이즈/구독 모델",
        "emphasize": {
            "marginTrend",
            "cashQuality",
            "ocfDecomposition",
            "dividendPolicy",
            "shareholderReturn",
            "scorecard",
        },
        "keyQuestions": [
            "마진 안정성이 어느 수준인가 (변동계수)?",
            "현금 전환이 확실한가 (OCF/NI > 100%)?",
            "배당/환원 여력이 충분한가?",
            "성장 없이 가치를 유지할 수 있는 구조인가?",
        ],
        "actFocus": {
            "2": "마진 안정성 — 변동계수가 낮고 원가 전가가 가능한 구조",
            "3": "현금 기계 — OCF/NI 100% 이상, CCC 마이너스 또는 안정",
            "5": "배당 지속성 — 연속 배당, 성향, FCF 대비 환원 여력",
        },
        "industryContext": "프랜차이즈/구독 모델은 전환비용이 높아 매출 안정성이 본질적 강점.",
        "peerAxes": ["operatingMargin", "dividendYield", "cashConversionCycle"],
    },
    "턴어라운드": {
        "description": "적자→흑자 전환 — 구조조정/사업 전환",
        "emphasize": {
            "marginTrend",
            "leverageTrend",
            "coverageTrend",
            "distressScore",
            "cashFlowOverview",
            "growthTrend",
            "fundamentalDivergence",
            "technicalVerdict",
        },
        "keyQuestions": [
            "흑자 전환이 구조적인가, 일시적인가?",
            "부채를 감당할 수 있는 수준인가?",
            "영업CF가 양수로 돌아섰는가?",
            "시장은 턴어라운드를 인정하는가 (재무-시장 괴리)?",
        ],
        "actFocus": {
            "2": "마진 전환점 — 적자에서 흑자로 전환한 원인과 지속 가능성",
            "3": "현금 회복 — 영업CF 양수 전환 여부, 운전자본 정상화",
            "4": "부채 감내력 — 이자보상배율, Altman Z, 차환 리스크",
            "6": "시장 인식 — 재무 개선 vs 주가 반응 괴리",
        },
        "industryContext": "턴어라운드는 1-2년 내 재악화 위험이 높다. 구조적 원인 제거 확인이 핵심.",
        "peerAxes": ["operatingMargin", "debtRatio", "interestCoverage"],
    },
    "성장": {
        "description": "고성장 + 마진 확대 — 매출 CAGR 15% 이상",
        "emphasize": {
            "growthTrend",
            "cagrComparison",
            "roicTree",
            "segmentTrend",
            "reinvestment",
            "revenueForecast",
        },
        "keyQuestions": [
            "성장이 수익성을 동반하는가 (마진 확대)?",
            "성장의 원천은 무엇인가 (부문/지역/제품)?",
            "재투자가 가치를 창출하는가 (ROIC > WACC)?",
            "이 성장률이 지속 가능한가?",
        ],
        "actFocus": {
            "1": "성장 원천 분해 — 어느 부문/지역이 성장을 견인하는가",
            "2": "수익성 동반 성장 — 매출 성장과 마진 확대가 함께 가는가",
            "5": "재투자 효율 — CAPEX/R&D가 ROIC로 돌아오는가",
            "6": "성장 지속성 — 컨센서스, 매출 전망, PEG",
        },
        "industryContext": "고성장주는 CAGR > 15%지만, 변동성이 높으면 사이클 호황과 구분해야 한다.",
        "peerAxes": ["revenueGrowthYoY", "operatingMargin", "roic"],
    },
    "자본집약": {
        "description": "설비 의존 + 감가상각 — 항공/전력/중공업",
        "emphasize": {
            "capexPattern",
            "ocfDecomposition",
            "assetStructure",
            "turnoverTrend",
            "leverageTrend",
            "penmanDecomposition",
        },
        "keyQuestions": [
            "감가상각 대비 CAPEX 수준이 적정한가?",
            "자산회전율이 개선되고 있는가?",
            "영업CF에서 감가상각의 현금 버퍼가 충분한가?",
            "부채를 자산 가치가 뒷받침하는가?",
        ],
        "actFocus": {
            "1": "자산 규모와 구성 — 유형자산 비중, 건설중인자산, 노후도",
            "3": "감가상각 현금 효과 — OCF = NI + 감가상각, 감가상각이 현금 버퍼",
            "4": "부채 구조 — 자산 담보, 장기 차입, 이자보상",
            "5": "CAPEX 사이클 — 유지투자 vs 확장투자, CAPEX/감가상각 비율",
        },
        "industryContext": "항공/전력/중공업은 CAPEX가 수년간 회수. 자산회전율과 감가상각 커버가 핵심.",
        "peerAxes": ["capexToRevenue", "assetTurnover", "debtRatio"],
    },
    "지주": {
        "description": "자회사 포트폴리오 — 영업외손익이 핵심",
        "emphasize": {
            "nonOperatingBreakdown",
            "ownershipTrend",
            "investmentInOther",
            "dividendPolicy",
            "assetStructure",
        },
        "keyQuestions": [
            "지분법손익이 전체 이익에서 차지하는 비중은?",
            "자회사 포트폴리오가 건전한가?",
            "연결 vs 별도 재무제표 괴리가 큰가?",
            "지주 할인이 정당화되는 수준인가?",
        ],
        "actFocus": {
            "1": "사업 포트폴리오 — 자회사 구성, 지분율, 핵심 자회사 실적",
            "2": "영업외손익 분해 — 지분법/배당/처분 등 비영업 이익 원천",
            "5": "자본배분 — 자회사 배당 수취 vs 주주 환원, 자체 투자",
            "6": "지주 할인/프리미엄 — NAV 대비 시가총액, 할인율 추이",
        },
        "industryContext": "지주사는 연결 재무제표가 자회사를 합산. 별도 재무제표로 지주 본체를 분리해서 봐야 한다.",
        "peerAxes": ["nonOperatingRatio", "dividendYield", "pbr"],
    },
    "현금부자": {
        "description": "현금 축적 + 배분 이슈",
        "emphasize": {
            "fundingSources",
            "penmanDecomposition",
            "dividendPolicy",
            "shareholderReturn",
            "cashFlowOverview",
            "fcfUsage",
        },
        "keyQuestions": [
            "현금을 왜 쌓고 있는가 (전략적 vs 비효율)?",
            "주주환원 여력 대비 실제 환원 수준은?",
            "순현금 상태에서 FLEV가 마이너스인가?",
            "현금 축적이 ROE를 희석하고 있는가?",
        ],
        "actFocus": {
            "2": "Penman FLEV — 순현금이 ROE를 희석하는 구조인지 확인",
            "3": "FCF 추이 — 매년 양의 FCF가 현금을 쌓는 원천",
            "5": "배분 정책 — 배당성향, 자사주, FCF 대비 환원율, 잔여 현금 누적",
        },
        "industryContext": "순현금 기업은 안전하지만, 현금이 과도하면 ROE가 희석되고 자본 효율이 떨어진다.",
        "peerAxes": ["cashToAssets", "dividendPayout", "roe"],
    },
}


def detectTemplates(company) -> list[str]:
    """기업 재무 데이터에서 해당하는 스토리 템플릿 전부 반환.

    예: ["사이클", "자본집약"], ["지주", "현금부자"]
    우선순위 순서로 정렬 (첫 번째가 주 템플릿).
    """
    results: list[str] = []
    for name, check in _TEMPLATE_CHECKS:
        try:
            if check(company):
                results.append(name)
        except (AttributeError, ValueError, TypeError, KeyError, IndexError):
            continue
    return results


def detectTemplate(company) -> str | None:
    """기업 재무 데이터에서 스토리 템플릿 자동 판별. 첫 매칭 반환."""
    results = detectTemplates(company)
    return results[0] if results else None


# ── 복수 매칭용 독립 체크 함수 ──


def _extractCommon(company):
    """공통 데이터 추출 (체크 함수 공용)."""
    try:
        ratios = company.finance.ratios
    except (AttributeError, ValueError):
        return None

    def _g(name, default=None):
        return getattr(ratios, name, default)

    try:
        rs = company.finance.ratioSeries
        if rs:
            data, _ = rs
            opMargins = data.get("RATIO", {}).get("operatingMargin", [])
        else:
            opMargins = []
    except (AttributeError, ValueError):
        opMargins = []

    return {
        "ratios": ratios,
        "opMargin": _g("operatingMargin"),
        "netDebt": _g("netDebt"),
        "cash": _g("cash"),
        "totalAssets": _g("totalAssets"),
        "ppe": _g("ppe") or _g("tangibleAssets"),
        "opMargins": opMargins,
    }


def _cv(values: list, min_count: int = 4) -> float | None:
    """변동계수(CV) 계산. None 제거 후 min_count 미만이면 None."""
    valid = [m for m in values if m is not None]
    if len(valid) < min_count:
        return None
    avg = sum(valid) / len(valid)
    if avg == 0:
        return None
    std = (sum((m - avg) ** 2 for m in valid) / len(valid)) ** 0.5
    return std / abs(avg)


def _checkTurnaround(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    opMargins = ctx["opMargins"]
    if len(opMargins) < 3:
        return False
    recent3 = opMargins[-3:]
    hasNeg = any(m is not None and m < 0 for m in recent3[:-1])
    lastPos = recent3[-1] is not None and recent3[-1] > 0
    return hasNeg and lastPos


def _checkHolding(company) -> bool:
    from dartlab.analysis.financial.earningsQuality import calcNonOperatingBreakdown

    nob = calcNonOperatingBreakdown(company)
    if not nob:
        return False
    latest = nob["history"][0] if nob.get("history") else None
    if not latest:
        return False
    opInc = abs(latest.get("opIncome") or 1)
    assocInc = abs(latest.get("associateIncome") or 0)
    if opInc > 0 and assocInc / opInc > 0.30:
        return True
    finCost = abs(latest.get("finCost") or 0)
    finIncome = abs(latest.get("finIncome") or 0)
    nonOpTotal = abs(latest.get("nonOpTotal") or 0)
    nonOpExFinance = nonOpTotal - finCost - finIncome
    return opInc > 0 and nonOpExFinance > 0 and nonOpExFinance / opInc > 0.80


def _checkGrowth(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    from dartlab.analysis.financial.growthAnalysis import calcCagrComparison

    cc = calcCagrComparison(company)
    if not cc:
        return False
    for comp in cc.get("comparisons", []):
        if comp.get("label") == "마진 방향" and comp.get("cagr1") is not None:
            if comp["cagr1"] > 15:
                cv = _cv(ctx["opMargins"])
                if cv is not None and cv > 0.5:
                    return False
                return True
    return False


def _checkCashRich(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    nd, ta, cash = ctx["netDebt"], ctx["totalAssets"], ctx["cash"]
    return nd is not None and ta and cash and nd < 0 and cash / ta > 0.20


def _checkCyclical(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    cv = _cv(ctx["opMargins"])
    return cv is not None and cv > 0.4


def _checkCapitalIntensive(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    ppe, ta = ctx["ppe"], ctx["totalAssets"]
    return ppe is not None and ta and ppe / ta > 0.40


def _checkFranchise(company) -> bool:
    ctx = _extractCommon(company)
    if not ctx:
        return False
    opMargin = ctx["opMargin"]
    if opMargin is None or opMargin <= 10:
        return False
    cv = _cv(ctx["opMargins"])
    return cv is not None and cv < 0.15


# 우선순위 순서
_TEMPLATE_CHECKS: list[tuple[str, object]] = [
    ("턴어라운드", _checkTurnaround),
    ("지주", _checkHolding),
    ("성장", _checkGrowth),
    ("현금부자", _checkCashRich),
    ("사이클", _checkCyclical),
    ("자본집약", _checkCapitalIntensive),
    ("프랜차이즈", _checkFranchise),
]
