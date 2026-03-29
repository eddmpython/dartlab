"""런타임 capabilities 카탈로그 (자동 생성).

이 파일은 scripts/generateSpec.py가 자동 생성합니다. 직접 수정 금지.
"""

CAPABILITIES: dict[str, dict] = {
    "ChartResult": {
        "kind": "class",
        "summary": "chart() 반환 객체 — 시각화 + 렌더링."
    },
    "Company": {
        "kind": "function",
        "summary": "종목코드/회사명/ticker → 적절한 Company 인스턴스 생성."
    },
    "Company.BS": {
        "aicontext": "ask()/chat()에서 자산/부채/자본 구조 분석 컨텍스트",
        "capabilities": "XBRL 정규화 재무상태표 (finance 우선)\ndocs 서술형 fallback\n최대 10년 분기별 시계열",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "summary": "재무상태표 (Balance Sheet) — 계정명 × 기간 DataFrame."
    },
    "Company.CF": {
        "aicontext": "ask()/chat()에서 현금창출력/투자/재무활동 분석 컨텍스트",
        "capabilities": "XBRL 정규화 현금흐름표 (finance 우선)\ndocs 서술형 fallback\n영업/투자/재무 활동 분류",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "summary": "현금흐름표 (Cash Flow Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.CIS": {
        "aicontext": "ask()/chat()에서 기타포괄손익/총포괄이익 분석 컨텍스트",
        "capabilities": "XBRL 정규화 포괄손익계산서 (finance 우선)\ndocs 서술형 fallback\n기타포괄손익 항목 포함",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "summary": "포괄손익계산서 (Comprehensive Income Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.IS": {
        "aicontext": "ask()/chat()에서 수익성/매출 구조 분석 컨텍스트",
        "capabilities": "XBRL 정규화 손익계산서 (finance 우선)\ndocs 서술형 fallback\n최대 10년 분기별 시계열",
        "kind": "property",
        "requires": "데이터: finance 또는 docs (자동 다운로드)",
        "summary": "손익계산서 (Income Statement) — 계정명 × 기간 DataFrame."
    },
    "Company.SCE": {
        "aicontext": "ask()/chat()에서 자본 구조 변동 분석 컨텍스트",
        "capabilities": "XBRL 정규화 자본변동표\n연결 기준 자본 구성요소별 변동\n연도별 시계열",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "자본변동표 (Statement of Changes in Equity) — 계정명 × 연도 DataFrame."
    },
    "Company.analysis": {
        "aicontext": "ask()/chat()에서 분석 결과를 컨텍스트로 주입\nreview/reviewer가 내부적으로 analysis 결과를 소비",
        "capabilities": "14축 분석: 수익구조, 자금조달, 자산구조, 현금흐름, 수익성, 성장성, 안정성, 효율성, 종합평가, 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성\n축 없이 호출 시 14축 가이드 반환\n개별 축 분석 시 Company 바인딩 (self 자동 전달)",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "재무제표 완전 분석 — 14축, 단일 종목 심층."
    },
    "Company.annual": {
        "capabilities": "BS/IS/CF 계정별 연도 시계열\n분기 데이터를 연도 단위로 집계\nfinance XBRL 정규화 기반",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "연도별 시계열 (연결 기준)."
    },
    "Company.ask": {
        "aicontext": "Tier 1 시스템 주도 분석. 질문 분류 후 엔진이 계산한 결과를\n컨텍스트로 조립하여 LLM이 해석/설명만 수행.",
        "capabilities": "엔진 계산 결과를 컨텍스트로 조립하여 LLM에 전달\n질문 분류 기반 분석 패키지 자동 선택 (financial, valuation, risk 등)\n멀티 provider 지원 (openai, ollama, codex 등)\n스트리밍 응답 지원",
        "kind": "method",
        "requires": "API 키: LLM provider API 키 (OPENAI_API_KEY 등)",
        "summary": "LLM에게 이 기업에 대해 질문."
    },
    "Company.audit": {
        "capabilities": "감사의견 추이 (적정/한정/부적정/의견거절)\n감사인 변경 이력 + 사유\n계속기업 불확실성 플래그\n핵심감사사항 (KAM) 추출\n내부회계관리제도 검토의견",
        "kind": "method",
        "requires": "데이터: docs + report (자동 다운로드)",
        "summary": "감사 리스크 종합 분석."
    },
    "Company.canHandle": {
        "kind": "method",
        "summary": "DART 종목코드(6자) 또는 한글 회사명이면 처리 가능."
    },
    "Company.capital": {
        "capabilities": "배당수익률 + 배당성향 추이\n자사주 매입/소각 이력\n총주주환원율 (배당 + 자사주)\n시장 전체 주주환원 횡단 비교",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "summary": "주주환원 분석 (배당, 자사주, 총환원율)."
    },
    "Company.chat": {
        "aicontext": "Tier 2 에이전트 모드. Tier 1 결과를 본 LLM이 부족하다고 판단하면\n저수준 tool(시계열 조회, 공시 검색 등)을 직접 호출하여 심화 분석.",
        "capabilities": "Tier 2 LLM 주도 분석 (tool calling)\nLLM이 부족한 정보를 자율적으로 도구 호출하여 보충\n원본 시계열, 공시 텍스트 검색, 복수 기업 비교 등 심화 탐색\n멀티 턴 대화 지원",
        "kind": "method",
        "requires": "API 키: tool calling 지원 LLM provider API 키",
        "summary": "에이전트 모드: LLM이 도구를 선택하여 심화 분석."
    },
    "Company.codeName": {
        "kind": "method",
        "summary": "종목코드 → 회사명 변환."
    },
    "Company.contextSlices": {
        "aicontext": "ask()/chat()의 시스템 프롬프트에 직접 주입되는 데이터\nLLM이 소비하는 최종 형태의 컨텍스트",
        "capabilities": "retrievalBlocks를 LLM 컨텍스트 윈도우에 맞게 슬라이싱\n토큰 예산 내에서 최대한 많은 관련 정보를 담는 압축 포맷\ntopic/period 기준 우선순위 정렬",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "LLM 투입용 context slice DataFrame."
    },
    "Company.cumulative": {
        "capabilities": "IS/CF 계정별 분기 누적(YTD) 시계열\nQ1→Q2→Q3→Q4 누적 합산\nfinance XBRL 정규화 기반",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "분기별 누적 시계열 (연결 기준)."
    },
    "Company.currency": {
        "kind": "property",
        "summary": "통화 코드 (DART 제공자는 항상 KRW)."
    },
    "Company.debt": {
        "capabilities": "총차입금 + 순차입금 규모\n부채비율 + 차입금의존도\n단기/장기 차입금 비율\n시장 전체 부채 구조 횡단 비교",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "summary": "부채 구조 분석 (차입금, 부채비율, 만기 구조)."
    },
    "Company.diff": {
        "capabilities": "전체 topic 변경 요약 (변경량 스코어링)\n특정 topic 기간별 변경 이력\n두 기간 줄 단위 diff (추가/삭제/변경)",
        "kind": "method",
        "requires": "데이터: docs (2개 이상 기간 필요)",
        "summary": "기간간 텍스트 변경 비교."
    },
    "Company.disclosure": {
        "capabilities": "전체 공시유형 조회 (정기, 주요사항, 발행, 지분, 외부감사 등)\n기간, 유형, 키워드 필터링\n최종보고서만 필터 (정정 이전 제외)",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "summary": "OpenDART 전체 공시 목록 조회."
    },
    "Company.eventStudy": {
        "capabilities": "공시 발표일 전후 주가 비정상 수익률 산출\n이벤트 윈도우 커스텀 가능\n공시 유형별 필터링\n통계적 유의성 검정",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)\n추가 패키지: pip install dartlab[event]",
        "summary": "공시 발표일 전후 주가 비정상 수익률(CAR) 분석."
    },
    "Company.filings": {
        "capabilities": "로컬에 보유한 공시 문서 목록\n기간별, 문서유형별 정리\nDART 뷰어 링크 포함",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "공시 문서 목록 + DART 뷰어 링크."
    },
    "Company.forecast": {
        "capabilities": "선형회귀 + CAGR + 이동평균 앙상블\n섹터별 성장률 보정\n신뢰구간 (상한/하한) 제공",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "매출 앙상블 예측 (다중 모델 가중 평균)."
    },
    "Company.gather": {
        "aicontext": "ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입\n기업 분석 시 시장 데이터 보충 자료로 활용",
        "capabilities": "price: OHLCV 주가 시계열 (KR Naver / US Yahoo)\nflow: 외국인/기관 수급 동향 (KR 전용)\nmacro: ECOS(KR) / FRED(US) 거시지표 시계열\nnews: Google News RSS 뉴스 수집\n자동 fallback 체인, circuit breaker, TTL 캐시",
        "kind": "method",
        "requires": "price/flow/news: 없음 (공개 API)\nmacro: API 키 -- ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)",
        "summary": "외부 시장 데이터 수집 — 4축 (price/flow/macro/news)."
    },
    "Company.getRatios": {
        "kind": "method",
        "summary": "Deprecated — use ``c.ratios`` property instead."
    },
    "Company.getTimeseries": {
        "kind": "method",
        "summary": "Deprecated — use ``c.timeseries`` property instead."
    },
    "Company.governance": {
        "capabilities": "사외이사 비율 + 감사위원회 구성\n최대주주 지분율 + 특수관계인\n시장 전체 거버넌스 횡단 비교",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "summary": "지배구조 분석 (이사회, 감사위원, 최대주주)."
    },
    "Company.index": {
        "aicontext": "LLM이 Company 전체 구조를 파악하는 핵심 진입점\nask()에서 어떤 데이터를 참조할지 결정하는 기초 정보",
        "capabilities": "docs sections + finance + report 전체를 하나의 목차로 통합\n각 항목의 chapter, topic, label, kind, source, periods, shape, preview 제공\nsections 메타데이터 + 존재 확인만으로 구성 (파서 미호출, lazy)\nviewer/렌더러가 소비하는 메타데이터 원천",
        "kind": "property",
        "requires": "데이터: docs/finance/report 중 하나 이상 (자동 다운로드)",
        "summary": "현재 공개 Company 구조 인덱스 DataFrame -- 전체 데이터 목차."
    },
    "Company.insights": {
        "capabilities": "7영역 등급 평가 (실적, 수익성, 성장, 안정성, 현금흐름, 효율, 밸류에이션)\n이상치 자동 탐지 (급변, 임계 초과)\n텍스트 요약 + 투자 프로파일 분류",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "종합 인사이트 분석 (7영역 등급 + 이상치 + 요약)."
    },
    "Company.keywordTrend": {
        "capabilities": "공시 텍스트에서 키워드 빈도 추이 분석\n54개 내장 키워드 세트 (AI, ESG, 탄소중립 등)\ntopic별 x 기간별 빈도 매트릭스\n복수 키워드 동시 검색",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "공시 텍스트 키워드 빈도 추이 (topic x period x keyword)."
    },
    "Company.listing": {
        "capabilities": "KOSPI + KOSDAQ 전체 상장법인\n종목코드, 종목명, 시장구분, 업종",
        "kind": "method",
        "requires": "데이터: listing (자동 다운로드)",
        "summary": "KRX 전체 상장법인 목록 (KIND 기준)."
    },
    "Company.liveFilings": {
        "capabilities": "OpenDART API 실시간 공시 조회\n기간, 건수, 키워드 필터링\n정규화된 컬럼 (docId, filedAt, title, formType 등)",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "summary": "OpenDART 기준 실시간 공시 목록 조회."
    },
    "Company.market": {
        "kind": "property",
        "summary": "시장 코드 (DART 제공자는 항상 KR)."
    },
    "Company.network": {
        "capabilities": "그룹 계열사 목록 (members)\n출자/피출자 연결 + 지분율 (edges)\n순환출자 경로 탐지 (cycles)\nego 서브그래프 (peers)\n인터랙티브 네트워크 시각화 (브라우저)",
        "kind": "method",
        "requires": "데이터: DART 대량보유/임원 공시 (자동 수집)",
        "summary": "관계 네트워크 (지분출자 + 그룹 계열사 지도)."
    },
    "Company.news": {
        "capabilities": "Google News RSS 기반 뉴스 수집\n제목, 날짜, 소스, 링크\n기간 조절 가능",
        "kind": "method",
        "requires": "없음 (공개 RSS)",
        "summary": "최근 뉴스 수집."
    },
    "Company.notes": {
        "capabilities": "K-IFRS 재무제표 주석(notes) 데이터 접근\n주석 항목별 조회",
        "kind": "property",
        "requires": "데이터: HuggingFace finance parquet (자동 다운로드)",
        "summary": "K-IFRS 주석사항 접근자."
    },
    "Company.priority": {
        "kind": "method",
        "summary": "낮을수록 먼저 시도. DART=10 (기본 provider)."
    },
    "Company.profile": {
        "aicontext": "c.sections는 내부적으로 profile.sections를 반환\n분석/리뷰에서 통합된 데이터를 소비하는 기본 경로",
        "capabilities": "docs sections를 spine으로, finance/report 데이터를 merge하여 통합 뷰 제공\nprofile.sections로 source 우선순위(finance > report > docs) 적용된 sections 접근\nprofile.show(topic)으로 merge된 결과 조회",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드). finance/report는 있으면 자동 merge.",
        "summary": "docs spine + finance/report merge layer -- 통합 프로필 접근자."
    },
    "Company.rank": {
        "capabilities": "전체 시장 내 매출/자산 순위\n섹터 내 상대 순위\n매출 성장률 기반 규모 분류 (large/mid/small)",
        "kind": "property",
        "requires": "데이터: buildSnapshot() 사전 실행 필요",
        "summary": "전체 시장 + 섹터 내 규모 순위 (매출/자산/성장률)."
    },
    "Company.ratioSeries": {
        "capabilities": "수익성/안정성/성장성/효율성/밸류에이션 비율\n연도별 dict 구조 (timeseries/annual과 동일 형태)\nfinance XBRL 기반 정확한 비율",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "재무비율 연도별 시계열 (IS/BS/CF와 동일한 dict 구조)."
    },
    "Company.ratios": {
        "capabilities": "수익성/안정성/성장성/효율성/밸류에이션 5대 분류\n분기별 시계열 비율 자동 계산\nfinance XBRL 기반 정확한 비율",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "재무비율 시계열 (분류/항목 × 기간 DataFrame)."
    },
    "Company.rawDocs": {
        "capabilities": "HuggingFace docs 카테고리 원본 데이터 직접 접근\n가공/정규화 이전 상태 그대로 반환",
        "kind": "property",
        "requires": "데이터: HuggingFace docs parquet (자동 다운로드)",
        "summary": "공시 문서 원본 parquet 전체 (가공 전)."
    },
    "Company.rawFinance": {
        "capabilities": "HuggingFace finance 카테고리 원본 데이터 직접 접근\nXBRL 정규화 이전 상태 그대로 반환",
        "kind": "property",
        "requires": "데이터: HuggingFace finance parquet (자동 다운로드)",
        "summary": "재무제표 원본 parquet 전체 (가공 전)."
    },
    "Company.rawReport": {
        "capabilities": "HuggingFace report 카테고리 원본 데이터 직접 접근\n정기보고서 API 데이터 가공 이전 상태 반환",
        "kind": "property",
        "requires": "데이터: HuggingFace report parquet (자동 다운로드)",
        "summary": "정기보고서 원본 parquet 전체 (가공 전)."
    },
    "Company.readFiling": {
        "capabilities": "접수번호(str) 직접 지정 또는 DataFrame row 자동 파싱\n전문 텍스트 또는 ZIP 기반 구조화 섹션 반환\n텍스트 길이 제한 (truncation) 지원",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "summary": "접수번호 또는 liveFilings row로 공시 원문을 읽는다."
    },
    "Company.research": {
        "capabilities": "재무 분석 (수익성, 성장, 안정성, 현금흐름)\n시장 포지션 + 섹터 비교\n공시 기반 정성 분석 (사업모델, 리스크)\n섹션별 선택적 생성",
        "kind": "method",
        "requires": "데이터: finance + docs (자동 다운로드)",
        "summary": "종합 기업분석 리포트 (재무 + 시장 + 공시 통합)."
    },
    "Company.resolve": {
        "kind": "method",
        "summary": "종목코드 또는 회사명 → 종목코드 변환."
    },
    "Company.retrievalBlocks": {
        "aicontext": "ask()/chat()에서 원문 기반 답변 생성 시 소스로 사용\nretrieval 기반 컨텍스트 주입의 원천 데이터",
        "capabilities": "docs 원문을 markdown 형태 그대로 보존한 검색용 블록\n각 블록은 topic/subtopic/period 단위로 분할\nRAG, 벡터 검색, 원문 참조에 최적화된 포맷",
        "kind": "property",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "원문 markdown 보존 retrieval block DataFrame."
    },
    "Company.review": {
        "aicontext": "reviewer()가 이 결과를 소비하여 AI 해석 생성\nask()에서 재무분석 컨텍스트로 활용",
        "capabilities": "14개 섹션 전체 보고서 (수익구조~재무정합성)\n단일 섹션 지정 가능\n4개 출력 형식 (rich, html, markdown, json)\n섹션간 순환 서사 자동 감지\n레이아웃 커스텀",
        "kind": "method",
        "requires": "데이터: finance + report (자동 다운로드)",
        "summary": "재무제표 구조화 보고서 — 14개 섹션 데이터 검토서."
    },
    "Company.reviewer": {
        "aicontext": "review() 결과(재무비율, 추세, 동종업계 비교)를 LLM에 제공\nLLM이 각 섹션을 해석하여 종합의견 생성\nguide 파라미터로 분석 관점 커스텀",
        "capabilities": "review() 데이터 위에 AI 섹션별 종합의견 추가\n도메인 특화 가이드로 분석 관점 지정 가능\n각 섹션 시작에 AI 해석 삽입",
        "kind": "method",
        "requires": "AI: provider 설정 (dartlab.setup() 참조)\n데이터: finance + report (자동 다운로드)",
        "summary": "AI 분석 보고서 — review() + 섹션별 AI 종합의견."
    },
    "Company.sce": {
        "kind": "property",
        "summary": "자본변동표 DataFrame (연결 기준)."
    },
    "Company.sceMatrix": {
        "capabilities": "원인(cause) × 세부(detail) × 연도 3차원 매트릭스\n자본 구성요소별 변동 원인 추적\nfinance XBRL 정규화 기반",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "자본변동표 연도별 매트릭스 (연결 기준)."
    },
    "Company.search": {
        "kind": "method",
        "summary": "회사명 부분 검색 (KIND 목록 기준)."
    },
    "Company.sections": {
        "aicontext": "회사 전체 지도 — 모든 분석의 출발점\nask()/chat()에서 topic 탐색 컨텍스트",
        "capabilities": "topic × period 수평화 통합 DataFrame\ndocs/finance/report 3-source 병합\nshow(topic)/trace(topic)/diff() 의 근간 데이터",
        "kind": "property",
        "requires": "데이터: docs (필수), finance/report (선택, 자동 다운로드)",
        "summary": "sections — docs + finance + report 통합 지도."
    },
    "Company.sector": {
        "capabilities": "WICS 11대 섹터 + 하위 산업그룹 자동 분류\nKIND 업종명 + 주요제품 키워드 기반 매칭\noverride 테이블 우선 → 키워드 → 업종명 순 fallback",
        "kind": "property",
        "requires": "데이터: KIND 상장사 목록 (자동 로드)",
        "summary": "WICS 투자 섹터 분류 (KIND 업종 + 키워드 기반)."
    },
    "Company.sectorParams": {
        "capabilities": "섹터별 할인율, 성장률, PER 멀티플 제공\n섹터 분류 결과에 연동된 파라미터 자동 선택",
        "kind": "property",
        "requires": "데이터: sector 분류 결과 (자동 연산)",
        "summary": "현재 종목의 섹터별 밸류에이션 파라미터."
    },
    "Company.select": {
        "capabilities": "show() 결과에서 특정 계정/항목만 추출\n기간 필터링 (특정 연도만)\n.chart() 체이닝으로 바로 시각화\n한글/영문 계정명 모두 지원",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "show() 결과에서 행(indList) + 열(colList) 필터."
    },
    "Company.show": {
        "capabilities": "120+ topic 접근 (재무제표, 사업내용, 지배구조, 임원현황 등)\n기간별 수평화 (topic × period 매트릭스)\n블록 단위 drill-down (목차 → 상세)\ndocs/finance/report 3개 소스 자동 통합\n세로 뷰 (period 리스트 전달 시)",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드). finance topic은 finance 데이터도 필요.",
        "summary": "topic의 데이터를 반환."
    },
    "Company.simulation": {
        "capabilities": "기본 시나리오: 금리인상, 경기침체, 원화약세, 수요급감 등\n시나리오별 매출/영업이익/현금흐름 영향 추정\n섹터 민감도 반영",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "경제 시나리오 시뮬레이션 (거시경제 충격 → 재무 영향)."
    },
    "Company.sources": {
        "capabilities": "3개 데이터 source(docs, finance, report) 존재 여부/규모 한눈에 확인\n각 source의 row/col 수와 shape 문자열 제공\n데이터 로드 전 가용성 사전 점검",
        "kind": "property",
        "requires": "없음 (메타데이터만 조회, 데이터 파싱 불필요)",
        "summary": "docs/finance/report 3개 source의 가용 현황 요약."
    },
    "Company.status": {
        "capabilities": "로컬 데이터 현황 (종목별 docs/finance/report 보유 여부)\n최종 업데이트 일시",
        "kind": "method",
        "summary": "로컬에 보유한 전체 종목 인덱스."
    },
    "Company.table": {
        "capabilities": "docs 원문의 markdown table을 Polars DataFrame으로 변환\nsubtopic 지정으로 특정 표만 추출\nnumeric 모드로 금액 문자열을 float 변환\nperiod 필터로 특정 기간 컬럼만 선택",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "subtopic wide 셀의 markdown table을 구조화 DataFrame으로 파싱."
    },
    "Company.timeseries": {
        "capabilities": "BS/IS/CF 계정별 분기 standalone 시계열\n최대 10년 분기별 데이터\nfinance XBRL 정규화 기반",
        "kind": "property",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "분기별 standalone 시계열 (연결 기준)."
    },
    "Company.topics": {
        "aicontext": "LLM이 가용 topic 목록을 파악하는 데 사용\n분석 범위 결정 시 참조",
        "capabilities": "docs/finance/report 모든 source의 topic을 하나의 DataFrame으로 통합\nchapter 순서대로 정렬, 각 topic의 블록 수/기간 수/최신 기간 표시\n어떤 데이터가 있는지 한눈에 파악",
        "kind": "property",
        "requires": "데이터: docs/finance/report 중 하나 이상 (자동 다운로드)",
        "summary": "topic별 요약 DataFrame -- 전체 데이터 지도."
    },
    "Company.trace": {
        "capabilities": "topic별 데이터 출처 확인 (docs, finance, report)\n출처 선택 이유 (우선순위, fallback 경로)\n각 출처별 데이터 행 수, 기간 수, 커버리지",
        "kind": "method",
        "requires": "데이터: docs + finance + report (보유한 것만 추적)",
        "summary": "topic 데이터의 출처(docs/finance/report)와 선택 근거 추적."
    },
    "Company.update": {
        "capabilities": "DART API로 최신 공시 확인 후 누락분만 수집\n카테고리별 선택 수집",
        "kind": "method",
        "requires": "API 키: DART_API_KEY",
        "summary": "누락된 최신 공시를 증분 수집."
    },
    "Company.valuation": {
        "capabilities": "DCF (현금흐름 할인) 모델\nDDM (배당 할인) 모델\n상대가치 (PER/PBR/EV-EBITDA) 비교\n모델별 적정가 + 종합 가중 평균",
        "kind": "method",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "종합 밸류에이션 (DCF + DDM + 상대가치)."
    },
    "Company.view": {
        "capabilities": "로컬 서버 기반 공시 뷰어 실행\n브라우저에서 sections/index 탐색",
        "kind": "method",
        "requires": "데이터: HuggingFace docs parquet (자동 다운로드)",
        "summary": "브라우저에서 공시 뷰어를 엽니다."
    },
    "Company.watch": {
        "capabilities": "전체 topic 변화 중요도 스코어링\n텍스트 변화량 + 재무 영향 통합 평가\n특정 topic 상세 변화 내역",
        "kind": "method",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "공시 변화 감지 — 중요도 스코어링 기반 변화 요약."
    },
    "Company.workforce": {
        "capabilities": "직원수 + 정규직/비정규직 비율\n평균 급여 + 1인당 매출\n평균 근속연수\n시장 전체 인력 횡단 비교",
        "kind": "method",
        "requires": "데이터: DART 정기보고서 (자동 수집)",
        "summary": "인력/급여 분석 (직원수, 평균급여, 근속연수)."
    },
    "Fred": {
        "kind": "class",
        "summary": "FRED 경제지표 facade."
    },
    "OpenDart": {
        "kind": "class",
        "summary": "OpenDART API 통합 클라이언트."
    },
    "OpenEdgar": {
        "kind": "class",
        "summary": "SEC public API facade."
    },
    "Review": {
        "kind": "class",
        "summary": "분석 리뷰 — AnalysisReport + core/Report 통합."
    },
    "SelectResult": {
        "kind": "class",
        "summary": "select() 반환 객체 — DataFrame 위임 + 체이닝."
    },
    "analysis": {
        "aicontext": "reviewer()가 analysis 결과를 소비하여 AI 해석 생성\nask()에서 재무분석 컨텍스트로 활용\n70개 calc* 함수의 개별 결과를 LLM에 주입 가능",
        "capabilities": "Part 1 — 사업구조: 수익구조, 자금조달, 자산구조, 현금흐름\nPart 2 — 핵심비율: 수익성, 성장성, 안정성, 효율성, 종합평가\nPart 3 — 심화분석: 이익품질, 비용구조, 자본배분, 투자효율, 재무정합성\n각 축은 Company를 받아 dict를 반환하는 순수 함수 집합\nreview()가 이 결과를 소비하여 구조화 보고서 생성",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "재무제표 완전 분석 — 14축, 단일 종목 심층."
    },
    "ask": {
        "aicontext": "재무비율, 추세, 동종업계 비교를 자동 계산하여 LLM에 제공\nsections 서술형 데이터 + finance 숫자 데이터 동시 주입\ntool calling provider에서는 LLM이 추가 데이터 자율 탐색",
        "capabilities": "자연어로 기업 분석 질문 (종목 자동 감지)\n스트리밍 출력 (기본) / 배치 반환 / Generator 직접 제어\n엔진 자동 계산 → LLM 해석 (Engine-First)\n데이터 모듈 include/exclude로 분석 범위 제어\n자체 검증 (reflect=True)",
        "kind": "function",
        "requires": "AI: provider 설정 (dartlab.setup() 참조)",
        "summary": "LLM에게 기업에 대해 질문."
    },
    "audit": {
        "capabilities": "감사의견 추이 (최근 5년, 적정/한정/부적정/의견거절)\n감사인 변경 이력 + 변경 사유\n계속기업 불확실성 플래그\n핵심감사사항 (KAM) 추출\n내부회계관리제도 검토의견",
        "kind": "function",
        "requires": "데이터: docs + report (자동 다운로드)",
        "summary": "감사 Red Flag 분석."
    },
    "capital": {
        "capabilities": "전체 상장사 주주환원 정책 횡단 비교\n배당수익률, 배당성향, 자사주 매입/소각 이력\n유상증자/무상증자 이력",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "summary": "한국 상장사 전체 주주환원 스캔."
    },
    "chart": {
        "capabilities": "revenue: 매출 + 영업이익률 콤보\ncashflow: OCF/ICF/FCF 폭포\ndividend: DPS + 배당수익률 + 배당성향\nbalance: 자산/부채/자본 구성\nprofitability: ROE, 영업이익률, 순이익률\nradar: 10영역 인사이트 레이더\nratio: 주요 재무비율 스파크라인\nheatmap: 공시 변화 히트맵\nauto: 가용 데이터 기반 전체 차트",
        "kind": "function",
        "requires": "데이터: Company (자동 다운로드)\n패키지: plotly (pip install dartlab[charts])",
        "summary": "시각화 엔진 -- Plotly 기반 재무 차트."
    },
    "chat": {
        "aicontext": "ask()와 동일한 기본 컨텍스트 + 저수준 도구 접근\nLLM이 부족하다 판단하면 추가 데이터 자율 수집",
        "capabilities": "LLM이 dartlab 도구를 자율적으로 선택/실행\n원본 공시 탐색, 계정 시계열 비교, 섹터 통계 등 심화 분석\n최대 N회 도구 호출 반복 (multi-turn)\n도구 호출/결과 콜백으로 UI 연동",
        "kind": "function",
        "requires": "AI: provider 설정 (tool calling 지원 provider 권장)",
        "summary": "에이전트 모드: LLM이 도구를 선택하여 심화 분석."
    },
    "codeToName": {
        "kind": "function",
        "summary": "종목코드 → 회사명."
    },
    "collect": {
        "capabilities": "종목별 DART 공시 데이터 직접 수집 (finance, docs, report)\n멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)\n증분 수집 — 이미 있는 데이터는 건너뜀\n카테고리별 선택 수집",
        "kind": "function",
        "requires": "API 키: DART_API_KEY",
        "summary": "지정 종목 DART 데이터 수집 (OpenAPI)."
    },
    "collectAll": {
        "capabilities": "전체 상장종목 DART 공시 데이터 일괄 수집\n미수집 종목만 선별 수집 (mode=\"new\") 또는 전체 재수집 (mode=\"all\")\n멀티키 병렬 수집 (DART_API_KEYS 쉼표 구분)\n카테고리별 선택 (finance, docs, report)",
        "kind": "function",
        "requires": "API 키: DART_API_KEY",
        "summary": "전체 상장종목 DART 데이터 일괄 수집."
    },
    "config": {
        "kind": "module",
        "summary": "dartlab 전역 설정."
    },
    "core": {
        "kind": "module",
        "summary": ""
    },
    "dataDir": {
        "kind": "module",
        "summary": "str(object='') -> str"
    },
    "debt": {
        "capabilities": "전체 상장사 부채 구조 횡단 비교\n부채비율, 차입금 의존도, 이자보상배율\n단기/장기 차입금 구성, 사채 발행 현황",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "summary": "한국 상장사 전체 부채 구조 스캔."
    },
    "digest": {
        "capabilities": "전체 상장사 공시 변화 중요도 순위\n섹터별 필터링\n텍스트 변화량 + 재무 변화 통합 스코어링\nDataFrame/마크다운/JSON 출력",
        "kind": "function",
        "requires": "데이터: docs (dartlab.downloadAll(\"docs\")로 사전 다운로드)",
        "summary": "시장 전체 공시 변화 다이제스트."
    },
    "downloadAll": {
        "capabilities": "HuggingFace 사전 구축 데이터 일괄 다운로드\nfinance (~600MB, 2700+종목), docs (~8GB, 2500+종목), report (~320MB, 2700+종목)\n이어받기/병렬 다운로드 지원 (huggingface_hub)\n전사 분석(scanAccount, governance, digest 등)에 필요한 데이터 사전 준비",
        "kind": "function",
        "requires": "없음 (HuggingFace 공개 데이터셋)",
        "summary": "HuggingFace에서 전체 시장 데이터 다운로드."
    },
    "forecast": {
        "capabilities": "매출 시계열 기반 앙상블 예측 (ARIMA + 선형 + 지��평활)\n업종 성장률 가중 보정\n신뢰구간 (80%, 95%) 제공\n최대 N년 전망 (기본 3년)",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "매출 앙상블 예측."
    },
    "fuzzySearch": {
        "kind": "function",
        "summary": "한글 fuzzy 종목 검색 — 초성 매칭 + Levenshtein 거리."
    },
    "gather": {
        "aicontext": "ask()/chat()에서 주가/수급/거시 데이터를 컨텍스트로 주입 가능\n기업 분석 시 시장 데이터 보충 자료로 활용",
        "capabilities": "price: OHLCV 시계열 (KR Naver/US Yahoo, 기본 1년, 최대 6000거래일)\nflow: 외국인/기관 수급 동향 (KR 전용, Naver)\nmacro: ECOS(KR 12개) / FRED(US 25개) 거시지표 시계열\nnews: Google News RSS 뉴스 수집 (최근 30일)\n자동 fallback 체인, circuit breaker, TTL 캐시",
        "kind": "function",
        "requires": "price/flow/news: 없음 (공개 API)\nmacro: API 키 — ECOS_API_KEY (KR) 또는 FRED_API_KEY (US)",
        "summary": "외부 시장 데이터 통합 수집 — 4축, 전부 Polars DataFrame."
    },
    "getKindList": {
        "kind": "function",
        "summary": "KRX KIND 상장법인 전체 목록."
    },
    "governance": {
        "capabilities": "전체 상장사 지배구조 횡단 비교\n최대주주 지분율, 사외이사 비율, 감사위원회 설치 여부\n지분 변동 추이, 특수관계인 거래",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "summary": "한국 상장사 전체 지배구조 스캔."
    },
    "insights": {
        "capabilities": "수익성, 성장성, 안정성, 효율성, 현금흐름, 밸류에이션, 배당 — 7영역\n각 영역 A~F 등급 부여 + 근거 지표\n종합 등급 + 강점/약점 요약\n동종업계 백분위 위치",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "7영역 등급 분석."
    },
    "listing": {
        "capabilities": "KR 전체 상장법인 목록 (KOSPI + KOSDAQ)\n종목코드, 종목명, 시장구분, 업종 포함\nUS listing은 향후 지원 예정",
        "kind": "function",
        "requires": "데이터: listing (자동 다운로드)",
        "summary": "전체 상장법인 목록."
    },
    "llm": {
        "kind": "module",
        "summary": "LLM 기반 기업분석 엔진."
    },
    "nameToCode": {
        "kind": "function",
        "summary": "회사명 → 종목코드. 정확히 일치하는 첫 번째 결과."
    },
    "network": {
        "capabilities": "상장사 간 지분 관계 네트워크 시각화\n브라우저에서 인터랙티브 그래프 표시\n노드(기업) + 엣지(지분 관계) 구조",
        "kind": "function",
        "requires": "데이터: docs (자동 다운로드)",
        "summary": "한국 상장사 전체 관계 지도."
    },
    "plugins": {
        "capabilities": "설치된 dartlab 플러그인 자동 탐색\n플러그인 메타데이터 (이름, 버전, 제공 topic) 조회",
        "kind": "function",
        "requires": "없음",
        "summary": "로드된 플러그인 목록 반환."
    },
    "reload_plugins": {
        "capabilities": "새로 설치한 플러그인 즉시 인식 (세션 재시작 불필요)\nentry_points 재스캔",
        "kind": "function",
        "requires": "없음",
        "summary": "플러그인 재스캔 — pip install 후 재시작 없이 즉시 인식."
    },
    "research": {
        "capabilities": "재무분석 + 시장분석 통합 리포트\n섹션별 선택 생성 가능\n재무비율 추세, 동종업계 비교, 시장 포지션\n구조화된 마크다운 출력",
        "kind": "function",
        "requires": "데이터: finance + docs (자동 다운로드)",
        "summary": "종합 기업분석 리포트."
    },
    "scan": {
        "aicontext": "ask()/chat()에서 시장 전체 데이터를 컨텍스트로 주입\n종목간 비교 분석의 데이터 소스",
        "capabilities": "governance: 최대주주 지분, 사외이사, 감사위원회\nworkforce: 임직원 수, 평균급여, 근속연수\ncapital: 배당수익률, 배당성향, 자사주\ndebt: 부채비율, 차입금 의존도, 이자보상\naccount: 전종목 단일 계정 시계열 (매출액, 영업이익 등)\nratio: 전종목 단일 재무비율 시계열 (ROE, 영업이익률 등)\nscreen: 재무 조건 스크리닝\npeer: 동종업계 피어 그룹\naudit: 감사의견, 감사인 변경\ninsider: 최대주주 변동, 자기주식\nnetwork: 기업 관계 네트워크\nwatch: 공시 변화 모니터링\ndigest: 시장 전체 변화 다이제스트",
        "kind": "function",
        "requires": "데이터: 축별로 다름 (dartlab.downloadAll() 참조)\ngovernance/workforce/capital/debt/audit/insider: report\naccount/ratio/screen: finance\nnetwork/watch/digest: docs",
        "summary": "시장 전체 횡단분석 — 13축, 전부 Polars DataFrame."
    },
    "scanAccount": {
        "capabilities": "전체 상장종목의 특정 계정 시계열 횡단 비교\n한글/영문 계정명 모두 지원 (\"매출액\" = \"sales\")\nDART(KR) + EDGAR(US) 양쪽 지원\n분기별/연간 선택, 연결/별도 선택",
        "kind": "function",
        "requires": "데이터: finance (dartlab.downloadAll(\"finance\")로 사전 다운로드)",
        "summary": "전종목 단일 계정 시계열."
    },
    "scanRatio": {
        "capabilities": "전체 상장종목의 특정 재무비율 시계열 횡단 비교\nROE, 영업이익률, 부채비율 등 주요 비율 지원\nDART(KR) + EDGAR(US) 양쪽 지원\n분기별/연간 선택",
        "kind": "function",
        "requires": "데이터: finance (dartlab.downloadAll(\"finance\")로 사전 다운로드)",
        "summary": "전종목 단일 재무비율 시계열."
    },
    "search": {
        "capabilities": "한글 입력 시 DART 종목 검색 (종목명, 종목코드)\n영문 입력 시 EDGAR 종목 검색 (ticker, 회사명)\n부분 일치, 초성 검색 지원 (KR)",
        "kind": "function",
        "requires": "데이터: listing (자동 다운로드)",
        "summary": "종목 검색 (KR + US 통합)."
    },
    "searchName": {
        "kind": "function",
        "summary": "회사명 부분 검색."
    },
    "setup": {
        "capabilities": "전체 AI provider 설정 현황 테이블 표시\nprovider별 대화형 설정 (키 입력 → .env 저장)\nChatGPT OAuth 브라우저 로그인\nOpenAI/Gemini/Groq/Cerebras/Mistral API 키 설정\nOllama 로컬 LLM 설치 안내",
        "kind": "function",
        "requires": "없음",
        "summary": "AI provider 설정 안내 + 인터랙티브 설정."
    },
    "simulation": {
        "capabilities": "거시경제 시나리오별 재무 영향 시뮬레이션\n기본 시나리오: 금리 인상, 경기 침체, 원��재 급등, 환율 변동\n매출/영업이익/순이익 변동 추정\n업종별 민감도 차등 적용",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "경제 시나리오 시뮬레이션."
    },
    "table": {
        "capabilities": "yoy: 전년 동기 대비 변동률\nsummary: 평균/CAGR/추세 요약\npivot: 계정별 피벗 테이블\nformat: 한국어 단위 포맷팅\ngrowth: 성장률 행렬\nratio: 재무비율 계산",
        "kind": "function",
        "summary": "테이블 가공 엔진 -- DataFrame 변환/포맷팅."
    },
    "text": {
        "kind": "module",
        "summary": "텍스트 분석 도구."
    },
    "valuation": {
        "capabilities": "DCF (잉여현금흐름 할인 모형)\nDDM (배당할인 모형)\n상대가치 (PER/PBR/EV-EBITDA 동종업계 비교)\n적정주가 범위 산출",
        "kind": "function",
        "requires": "데이터: finance (자동 다운로드)",
        "summary": "종합 밸류에이션 (DCF + DDM + 상대가치)."
    },
    "verbose": {
        "kind": "module",
        "summary": "bool(x) -> bool"
    },
    "workforce": {
        "capabilities": "전체 상장사 임직원 현황 횡단 비교\n임직원 수, 평균 근속연수, 평균 급여, 성별 비율\n업종별/규모별 비교",
        "kind": "function",
        "requires": "데이터: report (dartlab.downloadAll(\"report\")로 사전 다운로드)",
        "summary": "한국 상장사 전체 인력/급여 스캔."
    }
}
