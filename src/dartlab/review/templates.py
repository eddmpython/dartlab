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
            "① 매출 집중도(HHI)와 부문별 이익률 차이로 수익 구조 편중을 본다\n"
            "② 부문별 매출 추이와 YoY로 성장 부문을 식별한다\n"
            "③ 매출 성장률(YoY, 3Y CAGR)로 중기 방향성을 본다\n"
            "④ 성장 기여 분해로 어디에서 성장이 왔는지 본다\n"
            "⑤ 영업CF/순이익, 총이익률 추세로 매출 품질을 확인한다"
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
            "② 순영업자산(NOA)이 투자 대비 수익의 분모다\n"
            "③ 운전자본 순환(CCC)으로 영업 효율을 본다\n"
            "④ CAPEX/감가상각으로 성장투자인지 유지투자인지 판단한다\n"
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
