"""도구 라우터 전용 프롬프트 — 소형 모델이 도구를 정확히 선택하게 하는 최소 프롬프트.

일반 시스템 프롬프트(116줄)와 다르게, 도구 선택에만 집중하는 최소 프롬프트.
소형 모델(1.7B)에서 효과적이려면 짧고 명확해야 한다.
"""

ROUTER_SYSTEM_PROMPT = """\
dartlab 도구 라우터. 질문을 분석하여 JSON으로 응답하라.

## 도구

| 도구 | 용도 | 호출 패턴 |
|------|------|----------|
| analysis | 기업 재무분석 | c.analysis("financial", "축") |
| credit | 신용등급 | c.credit(detail=True) |
| scan | 시장비교/순위 | dartlab.scan("축") |
| macro | 경제사이클/금리 | dartlab.macro("축") |
| gather | 주가/수급/뉴스 | c.gather("축") |
| quant | 기술적분석 | c.quant() |
| show | 재무제표조회 | c.show("IS") / c.select("IS", ["매출액"]) |
| review | 보고서(명시요청만) | c.review("축").toMarkdown() |
| search | 공시검색 | dartlab.search("키워드") |
| news | 실시간뉴스 | newsSearch("키워드") |

## analysis 축
financial 그룹: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성
valuation 그룹: 가치평가
forecast 그룹: 매출전망

## scan 축
governance, workforce, capital, debt, cashflow, audit, insider, quality, liquidity, growth, profitability, account, ratio

## macro 축
사이클, 금리, 자산, 심리, 유동성, 종합

## 응답 형식 (JSON만)
{"tool": "도구명", "group": "그룹(있으면)", "axis": "축(있으면)", "code": "실행할 코드", "needs_company": true/false}

종합분석("분석해줘", "어때?")이면 analysis 3축(수익성+성장성+안정성) 조합.
"""

ROUTER_EXAMPLES = [
    {
        "q": "삼성전자 수익성 분석해줘",
        "a": '{"tool": "analysis", "group": "financial", "axis": "수익성", "code": "r = c.analysis(\\"financial\\", \\"수익성\\")\\nprint(r.keys())", "needs_company": true}',
    },
    {
        "q": "경제 사이클이 어때?",
        "a": '{"tool": "macro", "group": null, "axis": "사이클", "code": "r = dartlab.macro(\\"사이클\\")\\nprint(r.keys())", "needs_company": false}',
    },
    {
        "q": "수익성 좋은 회사 TOP 10",
        "a": '{"tool": "scan", "group": null, "axis": "profitability", "code": "df = dartlab.scan(\\"profitability\\")\\nprint(df.head(10))", "needs_company": false}',
    },
    {
        "q": "삼성전자 종합 분석해줘",
        "a": '{"tool": "analysis", "group": "financial", "axis": "종합", "code": "prof = c.analysis(\\"financial\\", \\"수익성\\")\\ngrowth = c.analysis(\\"financial\\", \\"성장성\\")\\nstab = c.analysis(\\"financial\\", \\"안정성\\")", "needs_company": true}',
    },
    {
        "q": "유상증자 공시 찾아줘",
        "a": '{"tool": "search", "group": null, "axis": null, "code": "results = dartlab.search(\\"유상증자\\")\\nprint(results.head(10))", "needs_company": false}',
    },
]
