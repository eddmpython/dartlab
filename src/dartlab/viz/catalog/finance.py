"""재무제표 dashboard 카드 카탈로그 — SSOT.

각 entry 는 모양 (kind/seriesPlan/options) + 기본 색상 + 데이터 정의까지
한 곳에 박는다. builder 는 norm DataFrame 만 받아 catalog 의 SeriesPlan 보고
자동으로 추출/합성/비율/YoY 계산. statements 함수 신설 0.

SeriesPlan 데이터 정의 우선순위 (한 series 마다 하나):
  - ratio   : {num: {accountKey: sign}, den: {accountKey: sign}, scale?: int}
  - yoy     : "accountKey"
  - compose : {accountKey: sign}
  - account : "accountKey"

accountKey 는 `accounts.STANDARD` 28 항목 중 하나:
  revenue, costOfSales, grossProfit, operatingIncome, netIncome,
  sga, rnd, financeIncome, financeCosts, incomeTax,
  assets, currentAssets, nonCurrentAssets, cash, inventories, receivables,
  liabilities, currentLiabilities, nonCurrentLiabilities, payables,
  shortDebt, longDebt, equity, retainedEarnings,
  cfOperating, cfInvesting, cfFinancing, capex, dividendsPaid.
"""

from __future__ import annotations

from dartlab.viz.palette import COLORS
from dartlab.viz.schema import CatalogEntry

FINANCE_CARDS: dict[str, CatalogEntry] = {
    # ─────────────────────────────────────────────────────────────
    # 단순 KPI tile 8 카드 (kpiRevenue/OpIncome/Roe/DebtRatio + kpiGrowth* + kpiCash*)
    # 폐기 — 운영자 명시 2026-05-18 ("자산구조 → 부채상세 → 자본상세 → 손익구조"
    # narrative 와 단절된 단순 숫자 노출은 어이없음). 같은 정보가 trend 카드
    # (incomeBreakdown · marginTrend · returnTrend · stabilityRatio · cashflowSigned)
    # 안에 시계열 + 변화율로 자연스레 들어가 있다.
    # ─────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    # 1-A. 자산구조 — dual-stack (자산 막대 ‖ 부채+자본 막대).
    #      회계 등식 자산 = 부채 + 자본 → 두 막대 동일 높이로 시각 확인.
    #      매출채권·재고도 영업자산 분류에 속하므로 stack 안에서 별도 색.
    #      "기타 영업자산" = assets − cash − receivables − inventories
    #      (= 비유동 영업자산: PPE · 무형 · 관계사 등).
    # ─────────────────────────────────────────────────────────────
    "assetComposition": {
        "kind": "trend",
        "title": "자산구조",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            # 회계 의미 묶음 색상 SSOT — 9 hue chaos 폐기. 자산 = sky monochrome
            # (cool, 4 shade 유동→비유동), 부채 = amber monochrome (warm, 2 shade
            # 영업→금융), 자본 = emerald monochrome (cool, 3 shade 자본금→잉여→기타).
            # Tailwind shade ramp — dense stack 인접 색 명확 구분 + 영역별 의미 통일.
            # ── 자산 stack (sky monochrome) ────────────────────
            {
                "key": "cash",
                "label": "현금성자산",
                "color": "#bae6fd",  # sky-200
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "asset",
                "account": "cash",
            },
            {
                "key": "receivables",
                "label": "매출채권",
                "color": "#38bdf8",  # sky-400
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "asset",
                "account": "receivables",
            },
            {
                "key": "inventories",
                "label": "재고자산",
                "color": "#0284c7",  # sky-600
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "asset",
                "account": "inventories",
            },
            {
                "key": "opAssetCore",
                "label": "기타 영업자산",
                "color": "#075985",  # sky-800
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "asset",
                "compose": {"assets": 1, "cash": -1, "receivables": -1, "inventories": -1},
            },
            # ── 부채+자본 stack (amber 2 + emerald 3) ─────────
            {
                "key": "opLiab",
                "label": "영업부채",
                "color": "#fcd34d",  # amber-300
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "liabEq",
                "compose": {"liabilities": 1, "shortDebt": -1, "longDebt": -1},
            },
            {
                "key": "finDebt",
                "label": "금융부채",
                "color": "#d97706",  # amber-600
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "liabEq",
                "compose": {"shortDebt": 1, "longDebt": 1},
            },
            {
                "key": "capitalStock",
                "label": "자본금",
                "color": "#6ee7b7",  # emerald-300
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "liabEq",
                "account": "capitalStock",
            },
            {
                "key": "retainedEarnings",
                "label": "이익잉여금",
                "color": "#10b981",  # emerald-500
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "liabEq",
                "account": "retainedEarnings",
            },
            {
                "key": "otherEquity",
                "label": "기타자본",
                "color": "#047857",  # emerald-700
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "liabEq",
                "compose": {"equity": 1, "capitalStock": -1, "retainedEarnings": -1},
            },
        ],
        "options": {"stacked": True, "unit": "원", "dualStack": True},
        # 자산구조 hero — 한 행 full width (12-col) + 높이 3.
        "layout": {"colSpan": 12, "rowSpan": 3},
        "help": "자산(왼쪽) = 부채+자본(오른쪽). 두 막대 높이는 항상 같다 (회계 등식). 매출채권·재고도 영업자산이지만 운전자본 회수기간 신호로 따로 분리. 기타 영업자산은 PPE·무형·관계사 등 비유동 본업 자본. 금융부채 ↑ 이자 부담, 이익잉여금 ↑ 내부유보 건전.",
    },
    # ─────────────────────────────────────────────────────────────
    # 1-A2. 회계 등식 시각 검증 (diverging stacked bar) — 자산구조 보조
    # ─────────────────────────────────────────────────────────────
    "bsMirror": {
        "kind": "trend",
        "title": "회계 등식 시각 (자산 ↔ 부채+자본)",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            # assetComposition 과 동일 색상 SSOT — 회계 의미 묶음 (자산 sky / 부채
            # amber / 자본 emerald) monochrome shade. 두 카드 한 행 같은 색상 체계
            # 라 사용자 시각 일관성.
            # 좌측 (음수, 0 line 아래로 stack) — 자산 측 4 항목 (sky)
            {
                "key": "cashNeg",
                "label": "현금성자산",
                "color": "#bae6fd",  # sky-200
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"cash": -1},
            },
            {
                "key": "receivablesNeg",
                "label": "매출채권",
                "color": "#38bdf8",  # sky-400
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"receivables": -1},
            },
            {
                "key": "inventoriesNeg",
                "label": "재고자산",
                "color": "#0284c7",  # sky-600
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"inventories": -1},
            },
            {
                "key": "opAssetNeg",
                "label": "기타 영업자산",
                "color": "#075985",  # sky-800
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"assets": -1, "cash": 1, "receivables": 1, "inventories": 1},
            },
            # 우측 (양수, 0 line 위로 stack) — 부채 2 (amber) + 자본 3 (emerald)
            {
                "key": "opLiab2",
                "label": "영업부채",
                "color": "#fcd34d",  # amber-300
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"liabilities": 1, "shortDebt": -1, "longDebt": -1},
            },
            {
                "key": "finDebt2",
                "label": "금융부채",
                "color": "#d97706",  # amber-600
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"shortDebt": 1, "longDebt": 1},
            },
            {
                "key": "capitalStock2",
                "label": "자본금",
                "color": "#6ee7b7",  # emerald-300
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "account": "capitalStock",
            },
            {
                "key": "retainedEarnings2",
                "label": "이익잉여금",
                "color": "#10b981",  # emerald-500
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "account": "retainedEarnings",
            },
            {
                "key": "otherEquity2",
                "label": "기타자본",
                "color": "#047857",  # emerald-700
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "balance",
                "compose": {"equity": 1, "capitalStock": -1, "retainedEarnings": -1},
            },
        ],
        "options": {"stacked": True, "unit": "원", "diverging": True},
        # 자산구조 바로 아래 한 행 — colSpan=12 + rowSpan=3 (양변 대칭 가독).
        # 회귀 가드: 12x2 는 trend variance 미허용 → resolveLayout ValueError →
        # packSkyline 가 queue pop 안 한 채 skip → 무한 loop → backend hang.
        "layout": {"colSpan": 12, "rowSpan": 3},
        "help": "회계 등식 자산 = 부채 + 자본 의 시각 검증. 0 line 기준 아래 막대 (자산 측 4 항목 = 현금/매출채권/재고/기타영업자산) 와 위 막대 (부채+자본 측 5 항목 = 영업부채/금융부채/자본금/이익잉여금/기타자본) 의 절대값이 항상 같음 = 등식 성립. 기존 자산구조 카드의 분해 표시를 양변 명시 시각으로 보강.",
    },
    # ─────────────────────────────────────────────────────────────
    # 1-B. 부채 상세 (매입채무 → 기타 영업부채 → 단기차입금 → 장기차입금·사채)
    # ─────────────────────────────────────────────────────────────
    "liabilityDetail": {
        "kind": "trend",
        "title": "부채 상세",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "payables",
                "label": "매입채무",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "liab",
                "account": "payables",
            },
            {
                "key": "otherOpLiab",
                "label": "기타 영업부채",
                "color": COLORS[6],
                "intent": "neutral",
                "unit": "원",
                "type": "bar",
                "stack": "liab",
                "compose": {"liabilities": 1, "payables": -1, "shortDebt": -1, "longDebt": -1},
            },
            {
                "key": "shortDebt",
                "label": "단기차입금",
                "color": COLORS[7],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "liab",
                "account": "shortDebt",
            },
            {
                "key": "longDebt",
                "label": "장기차입금·사채",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "liab",
                "account": "longDebt",
            },
        ],
        "options": {"stacked": True, "unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "매입채무는 무이자 영업부채 (좋은 부채). 단기차입금 ↑ 은 자금 압박 신호. 장기차입금·사채는 만기 분산되지만 이자 비용 부담. 영업부채 비중이 크면 운전자본으로 자금 조달 — 건전.",
    },
    # ─────────────────────────────────────────────────────────────
    # 1-C. 자본 상세 (자본금 → 자본잉여금 → 이익잉여금 → 기타자본)
    # ─────────────────────────────────────────────────────────────
    "equityDetail": {
        "kind": "trend",
        "title": "자본 상세",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "capitalStock",
                "label": "자본금",
                "color": COLORS[5],
                "intent": "neutral",
                "unit": "원",
                "type": "bar",
                "stack": "eq",
                "account": "capitalStock",
            },
            {
                "key": "capitalSurplus",
                "label": "자본잉여금",
                "color": COLORS[4],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "eq",
                "account": "capitalSurplus",
            },
            {
                "key": "retainedEarnings",
                "label": "이익잉여금",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "eq",
                "account": "retainedEarnings",
            },
            {
                "key": "otherEquity",
                "label": "기타자본",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "stack": "eq",
                "compose": {"equity": 1, "capitalStock": -1, "capitalSurplus": -1, "retainedEarnings": -1},
            },
        ],
        "options": {"stacked": True, "unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "이익잉여금이 매년 누적 증가하면 건전한 내부유보. 자본금 변동 없이 잉여금만 증가하면 이상적. 기타자본 음수는 자기주식 매입 (주주환원). 자본잉여금은 주식발행초과금.",
    },
    # ─────────────────────────────────────────────────────────────
    # 3. 손익구조 (매출 bar + 영업이익·당기순이익 area)
    # ─────────────────────────────────────────────────────────────
    "incomeBreakdown": {
        "kind": "trend",
        "title": "손익구조",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "revenue",
                "label": "매출액",
                "color": COLORS[2],
                "intent": "neutral",
                "unit": "원",
                "type": "bar",
                "account": "revenue",
            },
            {
                "key": "operatingIncome",
                "label": "영업이익",
                "color": COLORS[3],
                "intent": "accent",
                "unit": "원",
                "type": "line",
                "axis": "right",
                "account": "operatingIncome",
            },
            {
                "key": "netIncome",
                "label": "당기순이익",
                "color": COLORS[1],
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "axis": "right",
                "account": "netIncome",
            },
        ],
        "options": {"unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "매출(막대·좌축) 과 영업이익·당기순이익(영역·우축) 별도 축. 우축이 좌축의 ~10% 스케일이라 이익 변동이 잘 보임. 매출 안정인데 이익 변동 크면 운영 레버리지 높음.",
    },
    # ─────────────────────────────────────────────────────────────
    # 4. 현금흐름 signed (영업+/투자-/재무- + 순현금증감 line)
    # ─────────────────────────────────────────────────────────────
    "cashflowSigned": {
        "kind": "trend",
        "title": "현금흐름",
        "topic": "CF",
        "tab": "financial",
        "subCategory": "cashflow",
        "seriesPlan": [
            {
                "key": "cfOperating",
                "label": "영업활동",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "account": "cfOperating",
            },
            {
                "key": "cfInvesting",
                "label": "투자활동",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "account": "cfInvesting",
            },
            {
                "key": "cfFinancing",
                "label": "재무활동",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "account": "cfFinancing",
            },
            {
                "key": "netChange",
                "label": "순현금증감",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "axis": "right",
                "compose": {"cfOperating": 1, "cfInvesting": 1, "cfFinancing": 1},
            },
        ],
        "options": {"unit": "원", "signed": True},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "정상 패턴: 영업+ / 투자- / 재무- (성숙기 기업). 영업CF 가 음수면 사업 자체로 현금 못 만드는 위험 신호. 투자+ 는 자산 매각, 재무+ 는 차입 증가 (성장기 또는 자금 부족).",
    },
    # ─────────────────────────────────────────────────────────────
    # 5. 이익률 (매출총이익률 / 영업이익률 / 순이익률)
    # ─────────────────────────────────────────────────────────────
    "marginTrend": {
        "kind": "trend",
        "title": "이익률 추세",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "gpm",
                "label": "매출총이익률",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"grossProfit": 1}, "den": {"revenue": 1}, "scale": 100},
            },
            {
                "key": "opm",
                "label": "영업이익률",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"operatingIncome": 1}, "den": {"revenue": 1}, "scale": 100},
            },
            {
                "key": "npm",
                "label": "순이익률",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "매출총이익률 = 원가 대비 가격결정력 (산업/제품 경쟁력). 영업이익률 = 비용 통제 능력. 순이익률 = 금융비용·세금 차감 후 최종. 추세 하락은 경쟁 심화 또는 비용 증가.",
    },
    # ─────────────────────────────────────────────────────────────
    # 6. 수익성 (ROE / ROA)
    # ─────────────────────────────────────────────────────────────
    "returnTrend": {
        "kind": "trend",
        "title": "수익성",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "roe",
                "label": "자기자본이익률",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"equity": 1}, "scale": 100},
            },
            {
                "key": "roa",
                "label": "총자산이익률",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"assets": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "자기자본이익률 15%↑ 우수. 총자산이익률 과의 갭이 크면 부채 레버리지 효과 — 부채로 끌어올린 ROE 인지 확인 필요. ROE 가 ROA 와 가깝게 움직이면 무차입에 가까운 건전 수익성.",
    },
    # ─────────────────────────────────────────────────────────────
    # 7. 성장성 (매출/영업/순이익 YoY)
    # ─────────────────────────────────────────────────────────────
    "growthYoy": {
        "kind": "trend",
        "title": "성장성",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "growth",
        "seriesPlan": [
            {
                "key": "revenueYoy",
                "label": "매출 증가율",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "bar",
                "yoy": "revenue",
            },
            {
                "key": "operatingYoy",
                "label": "영업이익 증가율",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "bar",
                "yoy": "operatingIncome",
            },
            {
                "key": "netIncomeYoy",
                "label": "순이익 증가율",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "bar",
                "yoy": "netIncome",
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "영업이익 증가율이 매출 증가율을 넘으면 마진 동반 성장 (질 좋은 성장). 매출만 늘고 이익 정체는 가격 인하 또는 비용 증가 신호. 음수 = 역성장.",
    },
    # ─────────────────────────────────────────────────────────────
    # 8. 비용 구조 stacked (매출원가/판관비/R&D/금융비용)
    # ─────────────────────────────────────────────────────────────
    "costStructureTrend": {
        "kind": "trend",
        "title": "비용 구조",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "costOfSales",
                "label": "매출원가",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "cost",
                "account": "costOfSales",
            },
            {
                "key": "sga",
                "label": "판매관리비",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "cost",
                "account": "sga",
            },
            {
                "key": "rnd",
                "label": "연구개발비",
                "color": COLORS[4],
                "intent": "neutral",
                "unit": "원",
                "type": "bar",
                "stack": "cost",
                "account": "rnd",
            },
            {
                "key": "financeCosts",
                "label": "금융비용",
                "color": COLORS[7],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "stack": "cost",
                "account": "financeCosts",
            },
        ],
        "options": {"stacked": True, "unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "매출원가 비중이 안정적인가가 핵심. 판관비 ↑↑ 는 영업 효율 악화 신호. R&D 비중 ↑ 는 미래 투자 의지. 금융비용 ↑ 는 차입 증가의 결과.",
    },
    # ─────────────────────────────────────────────────────────────
    # 9. 잉여현금흐름 (영업CF / CapEx / FCF + 영업CF/매출)
    # ─────────────────────────────────────────────────────────────
    "fcfTrend": {
        "kind": "trend",
        "title": "잉여현금흐름",
        "topic": "CF",
        "tab": "financial",
        "subCategory": "cashflow",
        "seriesPlan": [
            {
                "key": "operating",
                "label": "영업현금흐름",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "account": "cfOperating",
            },
            {
                "key": "capex",
                "label": "자본적지출",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "account": "capex",
            },
            {
                "key": "fcf",
                "label": "잉여현금흐름",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "원",
                "type": "line",
                "compose": {"cfOperating": 1, "capex": -1},
            },
            {
                "key": "cfToRevenue",
                "label": "영업현금흐름/매출",
                "color": COLORS[6],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "axis": "right",
                "ratio": {"num": {"cfOperating": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "잉여현금흐름 = 영업현금흐름 - 자본적지출. 지속 양수면 배당·자사주 여력. 영업현금흐름/매출 비율은 이익 품질 지표 — 회계 이익이 진짜 현금으로 들어오는지.",
    },
    # ─────────────────────────────────────────────────────────────
    # 10. 레버리지 (D/E + D/A + 유동비율)
    # ─────────────────────────────────────────────────────────────
    "leverageTrend": {
        "kind": "trend",
        "title": "레버리지 (부채자본·부채자산·유동)",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "debtToEquity",
                "label": "부채자본비율",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"liabilities": 1}, "den": {"equity": 1}, "scale": 100},
            },
            {
                "key": "debtToAssets",
                "label": "부채자산비율",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"liabilities": 1}, "den": {"assets": 1}, "scale": 100},
            },
            {
                "key": "currentRatio",
                "label": "유동비율",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"currentAssets": 1}, "den": {"currentLiabilities": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "부채자본비율 100% 미만 안정, 200% 이상 부담. 부채자산비율은 전체 자산 중 부채 비중. 유동비율은 단기 지급능력 (1 년 내 갚을 부채 대비 1 년 내 현금화 자산).",
    },
    # ─────────────────────────────────────────────────────────────
    # 11. 안정성 (부채비율 + 자기자본비율)
    # ─────────────────────────────────────────────────────────────
    "stabilityRatio": {
        "kind": "trend",
        "title": "안정성",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "debtRatio",
                "label": "부채비율",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"liabilities": 1}, "den": {"equity": 1}, "scale": 100},
            },
            {
                "key": "equityRatio",
                "label": "자기자본비율",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"equity": 1}, "den": {"assets": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "부채비율 100% 미만 = 자본이 부채보다 큼 (보수적 재무구조). 자기자본비율 50% 이상 = 자기자본 의존도 높음 (안정성). 두 지표는 같은 정보를 다른 각도로.",
    },
    # ─────────────────────────────────────────────────────────────
    # 12. 유동성 (유동/당좌/현금 비율 + 1.0/1.5 reference)
    # ─────────────────────────────────────────────────────────────
    "liquidityTrend": {
        "kind": "trend",
        "title": "유동성",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "currentRatio",
                "label": "유동비율",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"currentAssets": 1}, "den": {"currentLiabilities": 1}, "scale": 100},
            },
            {
                "key": "quickRatio",
                "label": "당좌비율",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"cash": 1, "receivables": 1}, "den": {"currentLiabilities": 1}, "scale": 100},
            },
            {
                "key": "cashRatio",
                "label": "현금비율",
                "color": COLORS[5],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"cash": 1}, "den": {"currentLiabilities": 1}, "scale": 100},
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [
                {"value": 100, "label": "1.0", "intent": "neutral"},
                {"value": 150, "label": "1.5", "intent": "positive"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "유동비율 150% 이상이 안전선 (참조선). 당좌비율은 재고 제외한 보수적 지표 — 재고 안 팔려도 갚을 수 있는가. 현금비율은 가장 보수적 — 현금만으로 갚을 수 있는가.",
    },
    # ─────────────────────────────────────────────────────────────
    # 13. 활동성 (자산/재고/매출채권 회전율 — 회)
    # ─────────────────────────────────────────────────────────────
    "turnoverTrend": {
        "kind": "trend",
        "title": "활동성",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "assetTurnover",
                "label": "자산회전율",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "회",
                "type": "line",
                "ratio": {"num": {"revenue": 1}, "den": {"assets": 1}, "scale": 1},
            },
            {
                "key": "inventoryTurnover",
                "label": "재고회전율",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "회",
                "type": "line",
                "ratio": {"num": {"costOfSales": 1}, "den": {"inventories": 1}, "scale": 1},
            },
            {
                "key": "receivableTurnover",
                "label": "매출채권회전율",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "회",
                "type": "line",
                "ratio": {"num": {"revenue": 1}, "den": {"receivables": 1}, "scale": 1},
            },
        ],
        "options": {"unit": "회"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "자산회전율 = 매출 / 자산. 1 회면 자산 만큼 매출. 재고회전율 ↑ = 빠른 판매. 매출채권회전율 ↑ = 빠른 회수. 회전율 하락은 자산 효율 악화.",
    },
    # ─────────────────────────────────────────────────────────────
    # 14. 운전자본 (DSO / DIO — 일)
    #     DSO = (매출채권 / 매출) × 365, DIO = (재고 / 매출원가) × 365
    # ─────────────────────────────────────────────────────────────
    # ─────────────────────────────────────────────────────────────
    # 15. 이익 품질 — 영업CF / 순이익 (현금 vs 회계 ratio).
    #     1.0 미만 = 회계이익이 현금으로 안 들어옴 (불량). 1.0 이상 = 건전.
    # ─────────────────────────────────────────────────────────────
    "earningsQuality": {
        "kind": "trend",
        "title": "이익 품질 (현금주의 vs 발생주의)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "quality",
        "seriesPlan": [
            {
                "key": "cfNiRatio",
                "label": "영업CF/순이익 (배)",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "배",
                "type": "line",
                "ratio": {"num": {"cfOperating": 1}, "den": {"netIncome": 1}, "scale": 1},
            },
            {
                "key": "cfRevenueRatio",
                "label": "영업CF/매출 (%)",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "axis": "right",
                "ratio": {"num": {"cfOperating": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {
            "unit": "배",
            "refLines": [{"value": 1.0, "label": "1.0×", "intent": "neutral"}],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "좌축 영업CF/순이익 — 1.0배 이상 = 회계이익이 현금 동반 (건전). 우축 영업CF/매출 — 매출 1원당 현금 회수율, 산업 평균과 비교. 두 축이 같이 떨어지면 매출 인식 — 현금 회수 갭 확대 (위험).",
    },
    # ─────────────────────────────────────────────────────────────
    # 16. 이자보상배율 — 영업이익 / 금융비용. 부채 안전판.
    # ─────────────────────────────────────────────────────────────
    "interestCoverage": {
        "kind": "trend",
        "title": "이자보상 (영업이익 · 영업CF)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "icr",
                "label": "영업이익/이자",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "배",
                "type": "line",
                "ratio": {"num": {"operatingIncome": 1}, "den": {"financeCosts": 1}, "scale": 1},
            },
            {
                "key": "icrCfo",
                "label": "영업CF/이자",
                "color": COLORS[4],
                "intent": "positive",
                "unit": "배",
                "type": "line",
                "ratio": {"num": {"cfOperating": 1}, "den": {"financeCosts": 1}, "scale": 1},
            },
        ],
        "options": {
            "unit": "배",
            "refLines": [
                {"value": 1.0, "label": "1.0 (위험)", "intent": "negative"},
                {"value": 3.0, "label": "3.0 (안전)", "intent": "positive"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "영업이익 / 금융비용. 1.0 미만이면 본업이 이자도 못 갚는 위험. 3.0 이상이 안전선. 추세 하락은 부채 증가 또는 본업 악화 — 신용 등급 강등 직전 신호.",
    },
    # kpiCashFcf / kpiCashFcfMargin / kpiCashCapex 폐기 — 운영자 명시 2026-05-18
    # ("자산구조 → 부채 → 자본 → 손익" narrative 와 단절된 단순 숫자). FCF 시계열은
    # fcfTrend 카드 (영업CF·CapEx·FCF·CFO/매출) 안에 4 series 로 통합.
    # cashflowAllocation (자본배분 흐름 sankey) 폐기 — 운영자 명시 2026-05-18.
    # riskDistress (부실 위험 Altman Z') 폐기 — 운영자 명시 2026-05-18.
    # ─────────────────────────────────────────────────────────────
    # 19. 리스크·신호 — 이상신호 top 6
    # ─────────────────────────────────────────────────────────────
    # 변동 큰 지표 — colSpan=1 rowSpan=2 (6 item 짧은 list, 여백 0). 운영자 명시 2026-05-18.
    "riskAnomaly": {
        "kind": "topList",
        "title": "변동 큰 지표",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "risk",
        "seriesPlan": [],
        "dataSpec": {
            "adapter": "flagsTopList",
            "module": "dartlab.analysis.financial.earningsQuality",
            "fn": "calcEarningsQualityFlags",
        },
        "options": {},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "전년 대비 변동 큰 지표 top 6 (절대 변동값 기준). DSO/DIO/마진/레버리지 동향.",
    },
    # riskLifeCycle (생애주기 단계) 폐기 — 운영자 명시 2026-05-18.
    # ─────────────────────────────────────────────────────────────
    # 14. 현금전환주기 (CCC) — DSO + DIO − DPO. 진정한 운전자본 묶이는 기간.
    #     DSO 매출채권회수 / DIO 재고회수 / DPO 매입채무지급 (마이너스 = 현금 보유 길어짐).
    # ─────────────────────────────────────────────────────────────
    "workingCapitalDays": {
        "kind": "trend",
        "title": "현금전환주기 (CCC)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "dso",
                "label": "매출채권 (DSO)",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "일",
                "type": "line",
                "ratio": {"num": {"receivables": 365}, "den": {"revenue": 1}, "scale": 1},
            },
            {
                "key": "dio",
                "label": "재고자산 (DIO)",
                "color": COLORS[6],
                "intent": "neutral",
                "unit": "일",
                "type": "line",
                "ratio": {"num": {"inventories": 365}, "den": {"costOfSales": 1}, "scale": 1},
            },
            {
                "key": "dpo",
                "label": "매입채무 (DPO)",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "일",
                "type": "line",
                "ratio": {"num": {"payables": 365}, "den": {"costOfSales": 1}, "scale": 1},
            },
        ],
        "options": {"unit": "일"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "CCC = DSO + DIO − DPO. 짧을수록 현금이 빨리 회수. DPO ↑ = 매입채무 길게 끌어 현금 보유 (좋다). 매출 성장에도 CCC ↑ 면 운전자본 부담 — 진정한 성장 의심.",
    },
    # ─────────────────────────────────────────────────────────────
    # 17. DuPont 5-step 분해 — ROE = Tax × IntBurden × OpMargin × AsTurn × EqMult.
    #     Damodaran 정통 (CFA Level 1). 3-step (NPM × Turn × Lev) 의 NPM 을
    #     Tax × IntBurden × OpMargin 으로 더 쪼개 본업 vs 세금·이자 동력 분리.
    # ─────────────────────────────────────────────────────────────
    "dupont5Step": {
        "kind": "trend",
        "title": "DuPont 5단 분해",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "taxBurden",
                "label": "세금부담 (NI/PreTax)",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"netIncome": 1},
                    "den": {"operatingIncome": 1, "financeIncome": 1, "financeCosts": -1},
                    "scale": 100,
                },
            },
            {
                "key": "intBurden",
                "label": "이자부담 (PreTax/EBIT)",
                "color": COLORS[6],
                "intent": "neutral",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"operatingIncome": 1, "financeIncome": 1, "financeCosts": -1},
                    "den": {"operatingIncome": 1},
                    "scale": 100,
                },
            },
            {
                "key": "opMargin",
                "label": "영업이익률",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"operatingIncome": 1}, "den": {"revenue": 1}, "scale": 100},
            },
            {
                "key": "asTurn",
                "label": "자산회전율 (×100)",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"revenue": 1}, "den": {"assets": 1}, "scale": 100},
            },
            {
                "key": "eqMult",
                "label": "자본승수 (×100)",
                "color": COLORS[7],
                "intent": "neutral",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"assets": 1}, "den": {"equity": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "ROE = 세금부담 × 이자부담 × 영업이익률 × 자산회전 × 자본승수. 세금↓ 또는 이자↓ 가 부채로 ROE 끌어올리는 신호. 영업이익률↑ 만 본업 동력. Damodaran 5단 정통 (CFA Level 1).",
    },
    # ─────────────────────────────────────────────────────────────
    # 18. ROIC — 투하자본수익률. NOPAT / (자본 + 차입금). WACC 8% 참조선.
    #     세효과 단순화: NOPAT ≈ 영업이익 × 0.78 (법인세율 22% 가정).
    # ─────────────────────────────────────────────────────────────
    "roic": {
        "kind": "trend",
        "title": "수익성 3종 (ROE · ROA · ROIC)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "roe",
                "label": "ROE (자기자본)",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"equity": 1}, "scale": 100},
            },
            {
                "key": "roa",
                "label": "ROA (총자산)",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"assets": 1}, "scale": 100},
            },
            {
                "key": "roic",
                "label": "ROIC (투하자본)",
                "color": COLORS[4],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"operatingIncome": 78},
                    "den": {"equity": 1, "shortDebt": 1, "longDebt": 1},
                    "scale": 1,
                },
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [{"value": 8, "label": "WACC ≈ 8%", "intent": "neutral"}],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "ROE 주주 수익률 (부채 효과 포함) · ROA 총자산 효율 · ROIC 투하자본 수익 (부채 효과 제거, WACC ≈8% 초과 시 가치창출). ROE 와 ROIC 갭이 크면 부채 레버리지 의존.",
    },
    # ─────────────────────────────────────────────────────────────
    # 19. 순차입금 — 차입금 − 현금. 음수 = net cash (재무 여유).
    # ─────────────────────────────────────────────────────────────
    "netDebt": {
        "kind": "trend",
        "title": "순차입금 · 차입금 부담",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "netDebt",
                "label": "순차입금 (원)",
                "color": COLORS[2],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "compose": {"shortDebt": 1, "longDebt": 1, "cash": -1},
            },
            {
                "key": "debtToEquity",
                "label": "차입금/자기자본 (%)",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "axis": "right",
                "ratio": {
                    "num": {"shortDebt": 1, "longDebt": 1},
                    "den": {"equity": 1},
                    "scale": 100,
                },
            },
        ],
        "options": {"unit": "원", "signed": True},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "좌축 순차입금 = (단기+장기차입금)−현금. 음수 = net cash 여유. 우축 차입금/자기자본 — 자본 대비 차입 의존도. 둘 다 ↓ = deleveraging.",
    },
    # ─────────────────────────────────────────────────────────────
    # 20. Sloan accruals — (순이익 − 영업CF) / 평균자산. 분식 의심 정량.
    # ─────────────────────────────────────────────────────────────
    "sloanAccruals": {
        "kind": "trend",
        "title": "발생액 품질 (Sloan + WC ratios)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "quality",
        "seriesPlan": [
            {
                "key": "accruals",
                "label": "Sloan 발생액/자산",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"netIncome": 1, "cfOperating": -1},
                    "den": {"assets": 1},
                    "scale": 100,
                },
            },
            {
                "key": "arRatio",
                "label": "매출채권/매출",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"receivables": 1}, "den": {"revenue": 1}, "scale": 100},
            },
            {
                "key": "invRatio",
                "label": "재고/매출",
                "color": COLORS[2],
                "intent": "negative",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"inventories": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [
                {"value": 0, "label": "0", "intent": "neutral"},
                {"value": 10, "label": "+10%", "intent": "negative"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "(순이익 − 영업CF) / 자산. 양수 ↑ 는 회계이익이 현금 동반 안 됨 — 매출채권·재고 누적으로 이익 과대 의심 (Sloan 1996). +10% 이상 위험.",
    },
    # ─────────────────────────────────────────────────────────────
    # 21. Altman Z'' — analysis 단일 원장의 비금융사 부실 위험 4요소.
    # ─────────────────────────────────────────────────────────────
    "altmanZ": {
        "kind": "trend",
        "title": "Altman Z'' (부실 위험)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "credit",
        "seriesPlan": [
            {
                "key": "z",
                "label": "Z''",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "배",
                "type": "line",
                "analysisCall": {
                    "module": "financial._stabilityDistress",
                    "fn": "calcDistressScore",
                    "outputKey": "history.zScore",
                    "outputType": "timeseries",
                },
            },
        ],
        "options": {
            "unit": "배",
            "refLines": [
                {"value": 1.1, "label": "1.1 위험 경계", "intent": "negative"},
                {"value": 2.6, "label": "2.6 안전 경계", "intent": "positive"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "비금융사 Z'' < 1.1 = 부실 위험, > 2.6 = 안전, 사이는 회색. 필수 계정이 없으면 점수를 발행하지 않으며 EBIT은 영업이익 proxy다.",
    },
    # ─────────────────────────────────────────────────────────────
    # 22. 자본배분 — CapEx + 배당 + R&D stacked bar.
    #     번 돈을 어디 쓰는가 (재투자 / 주주환원 / 미래).
    # ─────────────────────────────────────────────────────────────
    "capitalAllocation": {
        "kind": "trend",
        "title": "자본배분",
        "topic": "CF",
        "tab": "financial",
        "subCategory": "cashflow",
        "seriesPlan": [
            {
                "key": "capex",
                "label": "CapEx (재투자)",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "compose": {"capex": -1},
            },
            {
                "key": "dividend",
                "label": "배당 (주주환원)",
                "color": COLORS[4],
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "stack": "alloc",
                "compose": {"dividendsPaid": -1},
            },
        ],
        "options": {"stacked": True, "unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "CapEx (재투자) + 배당 (주주환원) 의 상대 비중으로 경영진 자본배분 의도 파악. CapEx ↑ = 성장기, 배당 ↑ = 성숙기. R&D·자사주매입은 회사별 보고 양식 달라 별도 카드로 분리 (표준 28 계정 한정).",
    },
    # ─────────────────────────────────────────────────────────────
    # 23. R&D 강도 — R&D / 매출. 기술기업·제약은 5%+, 일반제조 1~3%.
    # ─────────────────────────────────────────────────────────────
    "rndIntensity": {
        "kind": "trend",
        "title": "R&D 강도",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "growth",
        "seriesPlan": [
            {
                "key": "rndRatio",
                "label": "R&D/매출",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"rnd": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [
                {"value": 5, "label": "5% (기술기업)", "intent": "positive"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "R&D / 매출. 5% 이상 = 기술 집약 (반도체·제약·SW), 1~3% = 일반 제조, 1% 미만 = 기술 의존도 낮음. 추세 ↑ = 미래 베팅 확대.",
    },
    # ─────────────────────────────────────────────────────────────
    # 25. 배당성향 — 배당 / 순이익. 주주환원 비중. 30~50% 안정.
    # ─────────────────────────────────────────────────────────────
    "payoutRatio": {
        "kind": "trend",
        "title": "환원율 (순이익 · 영업CF 기준)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "cashflow",
        "seriesPlan": [
            {
                "key": "payout",
                "label": "배당/순이익",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"dividendsPaid": -100},
                    "den": {"netIncome": 1},
                    "scale": 1,
                },
            },
            {
                "key": "payoutCfo",
                "label": "배당/영업CF",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"dividendsPaid": -100},
                    "den": {"cfOperating": 1},
                    "scale": 1,
                },
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [
                {"value": 30, "label": "30%", "intent": "neutral"},
                {"value": 50, "label": "50%", "intent": "positive"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "배당 / 순이익. 30~50% = 성숙 안정 기업 정통. 100% 초과 = 이익 초과 배당 (지속 불가). 0% = 성장 재투자 우선 또는 적자. dividendsPaid 부호 음수라 ×−1 보정.",
    },
    # ─────────────────────────────────────────────────────────────
    # 26. 현금 보유 비중 — 현금 / 자산. 보수적 경영 신호 + M&A 여력.
    # ─────────────────────────────────────────────────────────────
    "cashAssetsRatio": {
        "kind": "trend",
        "title": "현금 보유 비중",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "capitalStructure",
        "seriesPlan": [
            {
                "key": "cashRatio",
                "label": "현금 / 자산",
                "color": COLORS[5],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"cash": 1}, "den": {"assets": 1}, "scale": 100},
            },
        ],
        "options": {
            "unit": "%",
            "refLines": [
                {"value": 10, "label": "10%", "intent": "neutral"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "현금성자산 / 총자산. 10% 이상 = 보수적 경영 + M&A·배당·자사주 여력. 5% 미만 = 단기 유동성 부담 가능. 사업 모델별 정상 범위 다름 (현금 집약 IT 는 높고 제조는 낮음).",
    },
    # ─────────────────────────────────────────────────────────────
    # 27. 자본 성장 — 자기자본 YoY. 내부 유보 누적 추세.
    # ─────────────────────────────────────────────────────────────
    "equityGrowth": {
        "kind": "trend",
        "title": "자본 vs 매출 vs 순이익 (성장 비교)",
        "topic": "BS",
        "tab": "financial",
        "subCategory": "growth",
        "seriesPlan": [
            {
                "key": "equityYoy",
                "label": "자기자본 YoY",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "yoy": "equity",
            },
            {
                "key": "revenueYoy",
                "label": "매출 YoY",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "yoy": "revenue",
            },
            {
                "key": "netIncomeYoy",
                "label": "순이익 YoY",
                "color": COLORS[4],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "yoy": "netIncome",
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "자기자본 YoY = 내부유보 + 유상증자. 자기자본 < 순이익 YoY 면 배당·자사주 환원 활발. 자기자본 > 매출 YoY 지속 = 자본 누적 (자본 효율 ↓ 우려).",
    },
    # ─────────────────────────────────────────────────────────────
    # 28. 실효세율 — 법인세 / 세전이익. 24% 표준 + 안정성.
    # ─────────────────────────────────────────────────────────────
    "effectiveTaxRate": {
        "kind": "trend",
        "title": "마진 layering (영업 → 세전 → 순)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "quality",
        "seriesPlan": [
            {
                "key": "opm",
                "label": "영업이익률",
                "color": COLORS[0],
                "intent": "primary",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"operatingIncome": 1}, "den": {"revenue": 1}, "scale": 100},
            },
            {
                "key": "ptm",
                "label": "세전이익률",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "%",
                "type": "line",
                "ratio": {
                    "num": {"operatingIncome": 1, "financeIncome": 1, "financeCosts": -1},
                    "den": {"revenue": 1},
                    "scale": 100,
                },
            },
            {
                "key": "npm",
                "label": "순이익률",
                "color": COLORS[4],
                "intent": "positive",
                "unit": "%",
                "type": "line",
                "ratio": {"num": {"netIncome": 1}, "den": {"revenue": 1}, "scale": 100},
            },
        ],
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "영업 → 세전 → 순 마진 layering. 영업이익률 = 본업 수익. 세전 = 영업 + 영업외(이자/환). 순 = 세전 − 법인세. 세 라인 갭이 작으면 영업외+세금 부담 작음. 영업이익 ≈ 순이익 이면 영업외(+) 와 법인세(−) 가 cancel out.",
    },
    # ─────────────────────────────────────────────────────────────
    # 24. 영업이익 → 순이익 walk — 4 단 막대. 본업과 비본업/세금 분리.
    # ─────────────────────────────────────────────────────────────
    "taxWalk": {
        "kind": "trend",
        "title": "영업이익 → 순이익",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [
            {
                "key": "operating",
                "label": "영업이익",
                "color": COLORS[3],
                "intent": "positive",
                "unit": "원",
                "type": "bar",
                "account": "operatingIncome",
            },
            {
                "key": "nonOperating",
                "label": "영업외손익",
                "color": COLORS[1],
                "intent": "accent",
                "unit": "원",
                "type": "bar",
                "compose": {"financeIncome": 1, "financeCosts": -1},
            },
            {
                "key": "tax",
                "label": "법인세",
                "color": COLORS[0],
                "intent": "negative",
                "unit": "원",
                "type": "bar",
                "compose": {"incomeTax": -1},
            },
            {
                "key": "netIncome",
                "label": "순이익",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "원",
                "type": "bar",
                "account": "netIncome",
            },
        ],
        "options": {"unit": "원", "signed": True},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "영업이익 + 영업외손익 − 법인세 = 순이익. 영업외 (금융수익 − 금융비용) 가 큰 비중이면 본업 외 변동성. 법인세율 (= 법인세/세전이익) 안정성도 확인.",
    },
    # ─────────────────────────────────────────────────────────────
    # 29. Beneish 호환 카드. canonical 공급자 입력 계약 전까지 history가 비어 있다.
    # ─────────────────────────────────────────────────────────────
    "beneishMTimeline": {
        "kind": "trend",
        "title": "Beneish M (현재 비발행)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "quality",
        "seriesPlan": [
            {
                "key": "mScore",
                "label": "Beneish M-Score",
                "color": COLORS[2],
                "intent": "primary",
                "unit": "",
                "type": "line",
                "analysisCall": {
                    "module": "financial._earningsQualityDeepBeneish",
                    "fn": "calcBeneishTimeline",
                    "outputKey": "history.mScore",
                    "outputType": "timeseries",
                },
            },
        ],
        "options": {
            "refLines": [],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "원식 LTD/current maturities/tax payable/순수 감가상각의 공급자 공통 의미가 없어 현재 점수를 발행하지 않는다.",
    },
    # ─────────────────────────────────────────────────────────────
    # 30. Penman ROE 분해 — ROCE = RNOA + FLEV × SPREAD.
    #     adapter penmanRoeBars → calcPenmanDecomposition.
    # ─────────────────────────────────────────────────────────────
    "penmanRoeDecomp": {
        "kind": "trend",
        "title": "Penman ROE 분해",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [],
        "dataSpec": {"adapter": "penmanRoeBars"},
        "options": {"stacked": True, "unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "ROCE = RNOA (영업력) + FLEV × SPREAD (레버리지 효과). 진성 고수익 = RNOA > 15% + FLEV < 0.5. 레버리지 의존 = FLEV > 1 + RNOA 보통. Penman & Nissim (2001) 정통.",
    },
    # ─────────────────────────────────────────────────────────────
    # 31. ROIC vs WACC gap — 가치창출 판정.
    #     adapter roicWaccGap → calcRoicTimeline. WACC 8% 가정.
    # ─────────────────────────────────────────────────────────────
    "roicWaccGap": {
        "kind": "trend",
        "title": "ROIC vs WACC",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [],
        "dataSpec": {"adapter": "roicWaccGap"},
        "options": {"unit": "%"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "Spread = ROIC − WACC. 양수 지속 = 경제적 가치 창출 (Damodaran). 음수 = 자본 파괴. WACC 단순 가정 8% (한국 평균). 정밀 WACC 필요 시 별도 카드.",
    },
    # ─────────────────────────────────────────────────────────────
    # 32. Piotroski F-Score 시계열 — 9 binary 점수.
    #     calcPiotroskiTimeline analysisCall.
    # ─────────────────────────────────────────────────────────────
    "piotroskiFScore": {
        "kind": "trend",
        "title": "Piotroski F-Score",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "quality",
        "seriesPlan": [
            {
                "key": "fScore",
                "label": "F-Score (0~9)",
                "color": COLORS[3],
                "intent": "primary",
                "unit": "점",
                "type": "bar",
                "analysisCall": {
                    "module": "financial.scorecard",
                    "fn": "calcPiotroskiTimeline",
                    "outputKey": "history.score",
                    "outputType": "timeseries",
                },
            },
        ],
        "options": {
            "refLines": [
                {"value": 7, "label": "7 (강건)", "intent": "positive"},
                {"value": 3, "label": "3 (위험)", "intent": "negative"},
            ],
        },
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "Piotroski 2000 정통 9 binary (수익성 4 + 건전성 3 + 효율성 2). ≥ 7 = 펀더멘털 강건, ≤ 3 = 부실 신호. 시계열 추세 ↑ = 개선, ↓ = 악화.",
    },
    # ─────────────────────────────────────────────────────────────
    # 33. 부문별 매출 — top 6 stacked bar.
    #     adapter segmentBreakdown → calcSegmentTrend.
    # ─────────────────────────────────────────────────────────────
    "segmentRevenue": {
        "kind": "trend",
        "title": "부문별 매출",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "growth",
        "seriesPlan": [],
        "dataSpec": {"adapter": "segmentBreakdown"},
        "options": {"stacked": True, "unit": "원"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "사업보고서 III '사업의 내용' top 6 부문 매출 시계열. 부문 단일 의존 = 사업 집중 위험. 부문 다각화 추세는 안정성 신호.",
    },
    # ─────────────────────────────────────────────────────────────
    # 34. 사업 집중도 — HHI + top1 비중.
    #     adapter segmentConcentration → calcConcentration.
    # ─────────────────────────────────────────────────────────────
    "segmentConcentration": {
        "kind": "trend",
        "title": "사업 집중도",
        "topic": "IS",
        "tab": "financial",
        "subCategory": "risk",
        "seriesPlan": [],
        "dataSpec": {"adapter": "segmentConcentration"},
        "options": {"unit": ""},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "HHI (Herfindahl) > 5000 = 고집중 (단일 사업 위험). 1위 부문 비중 ↑ = 사업 집중. 분산 추세 = 다각화 진행.",
    },
    # ─────────────────────────────────────────────────────────────
    # 35. 영업레버리지 + 안전마진 — DOL bar + 안전마진 line.
    #     adapter dolBreakeven → calcOperatingLeverage + calcBreakevenEstimate.
    # ─────────────────────────────────────────────────────────────
    "operatingLeverage": {
        "kind": "trend",
        "title": "영업레버리지",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "profitability",
        "seriesPlan": [],
        "dataSpec": {"adapter": "dolBreakeven"},
        "options": {"unit": "배"},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "DOL = 영업이익 변화율 / 매출 변화율. DOL > 3 = 고정비 부담 큼 (제조업). DOL < 1.5 = 변동비 중심 (서비스). 안전마진 = (매출 − BEP)/매출. > 50% 안정.",
    },
    # ─────────────────────────────────────────────────────────────
    # 36. Distress ensemble — Altman 계열 한 표 + 적용 가능한 독립 모형.
    #     adapter distressEnsembleGauge → calcDistressEnsemble.
    # ─────────────────────────────────────────────────────────────
    "distressEnsemble": {
        "kind": "gauge",
        "title": "부도 위험 (적용 모델)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "credit",
        "seriesPlan": [],
        "dataSpec": {"adapter": "distressEnsembleGauge"},
        "options": {},
        "layout": {"colSpan": 3, "rowSpan": 3},
        "help": "Altman Z/Z''는 같은 계열이라 한 표만 집계하고 Ohlson·Springate·Zmijewski 중 산출 가능한 모델과 다수결한다. 일치도 < 60%는 모델 간 불일치다.",
    },
    # ─────────────────────────────────────────────────────────────
    # HERO. Snowflake 5-axis 정통 점수 radar (Simply Wall St 패턴).
    #     adapter snowflakeRadar — peer 불필요 절대 임계값.
    #     FINANCE_DASHBOARD_KEYS 에 박지 않음 → 헤더 아래 hero 자리 별도 render.
    # ─────────────────────────────────────────────────────────────
    "snowflakeRadar": {
        "kind": "radar",
        "componentType": "RadarChart",
        "title": "회사 본질 5축 (정통 절대 임계값)",
        "topic": "ratios",
        "tab": "financial",
        "subCategory": "overview",
        "seriesPlan": [],
        "dataSpec": {"adapter": "snowflakeRadar"},
        "options": {},
        "layout": {"colSpan": 3, "rowSpan": 4},
        "help": "5 정통 axis 0~10 점수 — 수익성(ROE)·자본효율(ROIC)·안정성(자기자본/자산)·유동성(유동비율)·현금흐름(FCF/매출). peer 비교 없이 절대 임계값으로 industry-agnostic 평가. 최근 4 분기 평균.",
    },
}
"""재무제표 dashboard 38 카드 — 정통 9 신설 (2026-05-19)."""


FINANCE_DASHBOARD_KEYS: list[str] = [
    # ─ 01 자본구조 · 자산구조 — 자금조달과 자산 운용. ─
    "assetComposition",  # full row hero (분해 stack)
    "bsMirror",  # 회계 등식 시각 검증 (diverging)
    "liabilityDetail",
    "equityDetail",
    "incomeBreakdown",
    "workingCapitalDays",
    "stabilityRatio",  # 자본구조 안정성 (자기자본/부채 ratio)
    "liquidityTrend",  # 유동성 (유동/당좌비율)
    "leverageTrend",  # 레버리지 (부채/자본·부채/자산)
    # ─ 02 영업 효율 · 자본 효율 — 본업 수익성. ─
    "marginTrend",
    "returnTrend",  # ROE/ROA/ROIC 3종 (보강)
    "dupont5Step",
    "penmanRoeDecomp",
    "roicWaccGap",
    "costStructureTrend",
    "turnoverTrend",
    "operatingLeverage",
    "taxWalk",
    "effectiveTaxRate",  # 영업/세전/순 마진 layering (보강)
    "segmentRevenue",
    # ─ 03 현금 일생 · 자본배분 — 번 돈은 어디로. ─
    "cashflowSigned",
    "fcfTrend",
    "capitalAllocation",
    "payoutRatio",  # 배당/순이익 + 배당/영업CF (보강)
    "earningsQuality",  # CFO/NI + CFO/매출 (보강)
    "sloanAccruals",  # 발생액 + 매출채권 증가/매출 (보강)
    "netDebt",  # 순차입금 + 차입금/자본 dual axis (보강)
    "interestCoverage",  # 영업이익/이자 + 영업CF/이자 (보강)
    # ─ 04 성장의 질 · 이상신호 — 성장이 진짜인가. ─
    "growthYoy",
    "equityGrowth",  # 자본 YoY + 매출 YoY 비교 (보강)
    "segmentConcentration",
]
"""34 카드 / 5 section / 12 row. 모든 row col 합 = 12 강행.
01 자본+자산구조 (3 row) / 02 영업·자본 효율 (4 row) / 03 현금 일생·자본배분 (2 row)
04 재무 안정·부도 위험 (2 row) / 05 성장의 질·이상신호 (1 row).

데이터 sparse 폐기 4 (2026-05-19, 데이터 충실도 검증 후):
- beneishMTimeline (annual 7/40 회수 = 17%), piotroskiFScore (10/40 = 25%)
- rndIntensity (005930 0/40 = 0%, R&D 별도 보고 없음)
- riskAnomaly (0 series 발생)

신설 유지 5 (충실도 80%+):
- dupont5Step (3단→5단), penmanRoeDecomp, roicWaccGap, operatingLeverage,
- segmentRevenue, segmentConcentration, distressEnsemble (gauge)."""


# OVERVIEW_KEYS — 재무제표분석 1 view 의 curated 카드 셋트.
# 현재 폐기 후 단일 view 라 FINANCE_DASHBOARD_KEYS 전체와 동일.
# 후속 PR 에서 관점 (perspective) 박을 때 OVERVIEW 는 *축약 셋트*, FINANCE_DASHBOARD 는 *전체* 로 분기 가능.
OVERVIEW_KEYS: list[str] = list(FINANCE_DASHBOARD_KEYS)


__all__ = ["FINANCE_CARDS", "FINANCE_DASHBOARD_KEYS", "OVERVIEW_KEYS"]
