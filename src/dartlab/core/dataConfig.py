"""데이터 릴리즈 중앙 설정.

디렉토리, 라벨을 1곳에서 관리.
새 카테고리 추가 시 DATA_RELEASES에 한 줄만 추가하면 전체 반영.

모든 데이터는 HuggingFace 데이터셋(eddmpython/dartlab-data)에서 제공.
"""

HF_REPO = "eddmpython/dartlab-data"
HF_BASE_URL = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

# 회사 이미지 serve SSOT - parquet 데이터(DATA_RELEASES)와 **별도** media 바이너리 repo.
# 블로그 v2(`publishBlogAssets.py`)·캐러셀(landing `/cards`)·legacy SNS staging(`sns/assets`)이
# 공용하는 이미지의 durable 원본이자 단일 serve 출처. DATA_RELEASES 에 넣지 않는 이유: 그 레지스트리는
# per-stockCode parquet 가정
# (dataLoader.download 가 전 카테고리를 `{code}.parquet` 로 순회)이라, webp 미디어를 넣으면 그
# 가정을 깨고 특수예외를 강요한다 → HF_REPO/HF_BASE_URL 과 대칭인 전용 상수로 분리.
# 업로드(sns/scripts/publish_assets_hf.py·로컬 전용)가 본 repo id 를, 서빙(ui hfMedia origin)이
# 본 base URL 을 미러(TS 는 Python import 불가라 hf.ts 가 동일 URL 을 상수로 복제·comment 로 SSOT 명시).
HF_MEDIA_REPO = "eddmpython/dartlab-media"
HF_MEDIA_BASE_URL = f"https://huggingface.co/datasets/{HF_MEDIA_REPO}/resolve/main"

DATA_RELEASES: dict[str, dict] = {
    # ── 사용자 공개 (brand.ts 동기화 대상) ──
    # ipcMirror: True 면 sync ETL 이 parquet 외에 .arrow IPC mirror artifact 도 빌드.
    # Phase D 의 pl.read_ipc(memory_map=True) 진입점이 사용. mmap 안 되는 환경 (pyodide)
    # 은 무시 후 parquet fallback.
    # DART disclosure parquet SSOT is panel. The retired docs category is not aliased.
    "panel": {
        # panel(공시 수평화) SSOT artifact - **flat** data/dart/panel/{code}.parquet (회사당 1파일,
        # 17-col). providers.dart.panel.build 가 zip→17col 생산(disclosureKey 부착) → providers.dart.panel
        # 이 read_parquet read(reader/uploader 모두 flat). EDGAR edgarPanel 과 동일 flat 정책.
        # ⚠ nested 금지: 옛 period-sharded {code}/{period}.parquet 표기는 폐기됨 - nested:True 면
        # uploader rglob 이 옛 nested 트리를 잘못 휩쓸어 reader(flat)와 어긋난다.
        "dir": "dart/panel",
        "label": "DART 공시 panel 수평화 artifact (회사당 flat, 17-col)",
        "public": True,
    },
    "finance": {
        "dir": "dart/finance",
        "label": "재무 숫자 데이터",
        "public": True,
        "ipcMirror": True,
    },
    "report": {
        "dir": "dart/report",
        "label": "정기보고서 데이터",
        "public": True,
        "ipcMirror": True,
    },
    "scan": {
        "dir": "dart/scan",
        "label": "전종목 횡단분석 프리빌드 데이터",
        "public": True,
    },
    "ipoReports": {
        # 신규상장 IPO 공모분석 리포트 (증권신고서 지분증권 6카테고리). 상장 전 발행사(corp_cls=E)는
        # allFilings(Y/K 한정)·panel 어디에도 없어 퍼블릭 런타임 파싱 불가(DART키·CORS·파이썬 파서).
        # 왓치 cron 이 buildIpoReport 로 파싱한 구조화 typed 결과를 rcept 키 단일 whole-file reports.parquet
        # 로 push(최근 윈도 rebuild, HF 증식 아님). 터미널은 reportJson 직독(reportSource 동형). sync=online.
        "dir": "dart/ipo",
        "label": "신규상장 IPO 공모분석 리포트 (증권신고서 6카테고리 파싱본)",
        "public": True,
    },
    "brokerageReports": {
        # 증권사 리서치 *메타 인덱스* (본문 0 - 제목·URL·발간일·구분·종목). pub_date 월별
        # flat {YYYYMM}.parquet. 공개 게시판 자체 스크랩(링크아웃), gather.sources.brokerage SSOT.
        "dir": "research/brokerage",
        "label": "증권사 리서치 리포트 메타 인덱스 (제목·링크·발간일·종목, 본문 없음)",
        "public": True,
    },
    "edgarDocs": {
        # plan delegated-prancing-tower PR-E7a - deprecated 마킹.
        # 안전 게이트 (4 주 sectionsParityEdgar 0 violations + D.1 2 주 + viewer
        # Playwright 0 + sync 14 일 무사고 + 운영자 명시 결정) 통과 후 PR-E7b 가 완전
        # 제거. 본 마킹 후에도 dual-write (fetchEdgarDocs) 가 계속 emit - 옛 path 호출자
        # 회귀 0 보장.
        "dir": "edgar/docs",
        "label": "SEC EDGAR 공시 문서 데이터 (deprecated - edgarSections 로 이행 중)",
        "public": True,
        "deprecated": True,
        "successor": "edgarSections",
    },
    "edgarSections": {
        # plan delegated-prancing-tower - EDGAR sections SSOT 통합 artifact.
        # nested: data/edgar/sections/{ticker}/{period}.parquet (period-sharded).
        # sectionsBuilder (PR-E2) 가 1 회 영속화 + HF push (PR-E3).
        # 런타임은 sectionsStorage.loadSectionsWide → mmap parquet → 콜드 1s 목표.
        # 2 content column: content_raw (iXBRL HTML, viewer SSOT) + content_plain (markdown, 분석 SSOT).
        "dir": "edgar/sections",
        "label": "SEC EDGAR sections SSOT artifact (period-sharded, raw+plain 2 column)",
        "public": True,
        "nested": True,
    },
    "edgarPanel": {
        # EDGAR panel(공시 수평화) SSOT artifact - DART panel 미러.
        # flat: data/edgar/panel/{ticker}.parquet (회사당 1파일, HF 폭발 회피 - DART flat 정책 미러).
        # providers.edgar.panel.build 가 SEC full-submission text → cross-market 16-col remap 생산,
        # providers.dart.panel 이 read_parquet (marketNs="us"). nested=False (flat 1파일).
        "dir": "edgar/panel",
        "label": "SEC EDGAR 공시 panel 수평화 artifact (회사당 flat, cross-market 16-col)",
        "public": True,
    },
    "edgar": {
        "dir": "edgar/finance",
        "label": "SEC EDGAR 재무 데이터 (companyfacts.zip 벌크 파생)",
        "public": True,
    },
    "edgarFinanceStmt": {
        # 터미널 재무 artifact - 파사드 Company.panel(IS/BS/CF) 표준화 산출을 DART dart/finance 동형
        # long(FINANCE_COLUMNS)으로 bake. 브라우저 터미널이 KR=dart/finance·US=edgar/financeStmt 를
        # 같은 financeSource reader 로 직독(16 카드 동일 배선). raw edgar/finance(companyfacts)는 백엔드
        # 파사드용으로 별도 유지. flat: data/edgar/financeStmt/{ticker}.parquet.
        "dir": "edgar/financeStmt",
        "label": "SEC EDGAR 터미널 재무 artifact (파사드 표준화 → DART finance 동형, 회사당 flat)",
        "public": True,
    },
    "edgarMeta": {
        "dir": "edgar/meta",
        "label": "SEC EDGAR 분기 벌크 메타 (sub/pre/tag)",
        "public": True,
    },
    "edgarPriceCompany": {
        # 터미널 주가 그래프 artifact - 회사별 일별 OHLCV 전체이력(Yahoo v8 ~10년 bake). 브라우저
        # 터미널 PriceChart 가 rt.price US 브랜치(edgarPriceSource)로 직독. KR krxPriceCompany·gov/prices/company
        # 와 동형(회사당 flat). date=Utf8 'YYYYMMDD'(Candle.t 규약)·close=Yahoo adjclose. raw companyfacts·
        # financeStmt 와 별개 축(주가는 공시 아님). flat: data/edgar/prices/company/{ticker}.parquet.
        "dir": "edgar/prices/company",
        "label": "SEC 유니버스 회사별 일별 OHLCV (터미널 주가 그래프 artifact, Yahoo bake, 회사당 flat)",
        "public": True,
    },
    "edgarTickers": {
        # ticker↔CIK 맵 - 퍼블릭 브라우저 식별자 해소(finance=cik·panel=ticker 이중키).
        # 엔진은 로컬 flat data/edgar/tickers.parquet 직독, 브라우저는 HF edgar/tickers/tickers.parquet
        # range-fetch. edgarPanel rebuild 가 publish(_publishTickers). (S0.2 edgar-parity-wiring)
        "dir": "edgar/tickers",
        "label": "SEC EDGAR ticker↔CIK 맵 (브라우저 식별자 해소)",
        "public": True,
    },
    "krxPrices": {
        "dir": "krx/prices",
        "label": "KRX 일별 전종목 OHLCV+시총+발행주식수 (raw, long parquet)",
        "public": True,
    },
    "krxPriceCompany": {
        "dir": "krx/prices/company",
        "label": "KRX 회사별 일별 OHLCV+시총 타임라인 (landing dashboard artifact)",
        "public": True,
    },
    "krxIndices": {
        "dir": "krx/indices",
        "label": "KRX 시장군별 지수 일별 OHLCV+거래대금+시가총액 (raw, long parquet)",
        "public": True,
    },
    # ── 공공데이터포털(data.go.kr) gov 축 - date/company/index 샤딩. 엔진 reader SSOT. ──
    "govPrices": {
        "dir": "gov/prices/date",
        "label": "공공데이터포털 일별 전종목 OHLCV+시총+발행주식수 (date 샤딩, KRX raw schema)",
        "public": True,
    },
    "govPriceCompany": {
        "dir": "gov/prices/company",
        "label": "공공데이터포털 회사별 일별 OHLCV+시총 타임라인 (차트 직독 artifact)",
        "public": True,
    },
    "govIndices": {
        "dir": "gov/indices/date",
        "label": "공공데이터포털 시장군별 지수 일별 OHLCV+거래대금+시가총액 (date 샤딩, KRX 지수 schema)",
        "public": True,
    },
    "govIndexPerIndex": {
        "dir": "gov/indices/index",
        "label": "공공데이터포털 지수별 일별 시계열 (지수 1개 직독 artifact)",
        "public": True,
    },
    "macroFred": {
        "dir": "macro/fred",
        "label": "FRED 거시경제 시계열 (HF 벌크, latest-revised)",
        "public": True,
    },
    "macroEcos": {
        "dir": "macro/ecos",
        "label": "ECOS 한국은행 거시경제 시계열 (HF 벌크, latest-revised)",
        "public": True,
    },
    "macroCustoms": {
        "dir": "macro/customs",
        "label": "관세청 무역통계 월별 수출입 시계열 (HF 벌크, 산업 선행지표)",
        "public": True,
    },
    "expectations": {
        "dir": "expectations",
        "label": "기대치 격자 원장 (발행 봉인 + 사후 채점, append-only, 시뮬레이터 검증척추)",
        "public": True,
    },
    "forwardTests": {
        "dir": "forwardTests",
        "label": "매출 예측 도메인 기록 (ForwardTestRecord JSON, 09 P9a/P9b 승격분)",
        "public": False,
    },
    # ── generated artifact (landing 빌드 시 HF 에서 fetch) ──
    "industryMap": {
        "dir": "landing/map",
        "label": "산업지도 JSON (landing/ SvelteKit 정적 asset)",
        "public": True,
    },
    "dashboards": {
        # mapBuild 가 매일 빌드·HF push, docs 배포가 seed - git 사본은 최후 폴백.
        # (옛 구조: git 커밋 사본만 서빙 → 2026-04-22 동결 사고의 근본 원인)
        "dir": "landing/dashboards",
        "label": "대시보드 JSON (finance·quarters·macro·meta - landing 정적 asset)",
        "public": True,
    },
    "lensProducts": {
        "dir": "landing/lenses",
        "label": "다섯 분석 렌즈 대표 제품 JSON (공개 터미널 artifact)",
        "public": True,
    },
    # ── 내부용 (brand.ts 동기화 불필요) ──
    "edgarScan": {
        "dir": "edgar/scan",
        "label": "EDGAR 전종목 scan 프리빌드 데이터",
        "public": False,
    },
    "allFilings": {
        "dir": "dart/allFilings",
        "label": "DART 전체 공시 원문 데이터",
        "public": False,
    },
    "dartOriginal": {
        # 원본=SSOT 전략([[project_original_ssot_strategy]]) - DART 정기보고서(사업·분기·반기)
        # document.xml zip 보관 (재빌드 가치 높은 분석 핵심). nested: original/dart/docs/{code}/{rcept}.zip.
        # allFilings(비정기)는 월별 parquet 이라 zip 안함. EDGAR 는 panel 만(raw 폐기).
        "dir": "original/dart/docs",
        "label": "DART 정기보고서 원본 zip (재빌드용, 비공개)",
        "public": False,  # 재배포 안전 - private repo
        "nested": True,
        "repo": "eddmpython/dartlab-dart-original",
    },
    "stemIndex": {
        "dir": "dart/stemIndex",
        "label": "Ngram+Synonym 통합 검색 인덱스",
        "public": False,
    },
    "contentIndex": {
        "dir": "dart/contentIndex",
        "label": "통합검색 content 인덱스 (음절 bigram BM25 CSR + 결정론 라우터 router.json) - 런타임 lazy pull",
        "public": True,
    },
    # ⚠ EDINET 슬롯 2종은 동결·미빌드 (frozen, unbuilt) - EDINET API 통신 불가로 빌드된 적 없는
    # phantom 슬롯. provider 도 동결(`providers/__init__.py __all__` 제외). 미래 API 복구 시 재활성.
    # (debt-honesty P2-1)
    "edinetDocs": {
        "dir": "edinet/docs",
        "label": "EDINET 공시 문서 데이터 (일본) - 동결·미빌드",
        "public": False,
    },
    "edinet": {
        "dir": "edinet/finance",
        "label": "EDINET 재무 데이터 (일본) - 동결·미빌드",
        "public": False,
    },
    "aiKnowledge": {
        "dir": "ai/knowledge",
        "label": "AI 분석 지식 (인사이트/스킬/에러패턴)",
        "public": False,
    },
    # ── 뉴스 archive - visibility-first taxonomy `news/{public,private}/{source}/`.
    #    `dir` 은 gather.sources.newsSources.NewsSourceSpec.dir 과 1:1 일치해야 함
    #    (drift 회귀: tests/gather/sources/test_newsSources.py). public 서브트리는
    #    기본 repo, private(naver)는 전용 private repo (저작권 비공개 캐시).
    "newsHeadlines": {
        # Phase A - Google News RSS 일별 헤드라인 archive (forward-only).
        # `data/news/public/rss/{market}/{YYYY}-{MM}-{DD}.parquet` 일별 sharding.
        # 본문 archive 영구 제외 (ToS) - headline + url + source + date 메타데이터만.
        # syncNewsHeadlines.py cron 박제, enrichNewsHeadlines.py (Phase B) 가 sentiment/topic 추가.
        "dir": "news/public/rss",
        "label": "Google News RSS 일별 헤드라인 archive (forward-only, 메타데이터만)",
        "public": True,
        "nested": True,
    },
    "newsEnriched": {
        # Phase B - sentiment + topic enrichment 결과 (rss 파생).
        # `data/news/public/rss_enriched/{market}/{YYYY}-{MM}-{DD}.parquet` 형제 dir.
        # raw 컬럼 + (sentiment_score, sentiment_label, model_version, topic_id, topic_label, topic_prob).
        # enrichNewsHeadlines.py cron, narrativePulse.buildNarrativePulse 가 입력.
        "dir": "news/public/rss_enriched",
        "label": "news headlines enriched (sentiment + topic, Phase B 산출)",
        "public": True,
        "nested": True,
    },
    "newsGdelt": {
        # Phase D - GDELT 2.0 GKG 글로벌 5 년 백필.
        # `data/news/public/gdelt/{market}/{YYYY}-{MM}-{DD}.parquet` 일별 sharding.
        # canonical 17컬럼 + (themes list, language, tone_raw).
        # syncGdeltBackfill.py 가 GDELT 슬롯 15-min 부터 일별 통합.
        "dir": "news/public/gdelt",
        "label": "GDELT 2.0 GKG 글로벌 뉴스 archive (URL + sentiment + themes, Phase D 백필)",
        "public": True,
        "nested": True,
    },
    "newsNaver": {
        # 네이버 검색 API 뉴스 (제목+스니펫) - 언론사 저작권, 비공개 캐시 전용.
        # `data/news/private/naver/{market}/{YYYY}-{MM}-{DD}.parquet`. KRX 선례 동형.
        # 공개 dartlab-data 안 감 → 전용 private repo. syncNaverNews.py cron.
        "dir": "news/private/naver",
        "label": "네이버 검색 API 뉴스 (제목+스니펫, private - 언론사 저작권)",
        "public": False,
        "nested": True,
        "repo": "eddmpython/dartlab-news-private",
    },
    "newsNaverEnriched": {
        # 네이버 파생 sentiment+topic (여전히 저작권 - private).
        # `data/news/private/naver_enriched/{market}/{YYYY}-{MM}-{DD}.parquet`.
        "dir": "news/private/naver_enriched",
        "label": "네이버 뉴스 enriched (sentiment + topic, private)",
        "public": False,
        "nested": True,
        "repo": "eddmpython/dartlab-news-private",
    },
}


# 다운로드 센터 노출 카탈로그.
# 보안 SSOT = 위 DATA_RELEASES 의 `public` 플래그. 노출 = public:True · flat(nested 아님) · 표형(tabular).
# 새 public flat 카테고리는 자동 노출(추가 코드 0), 새 private 은 자동 차단(public:False).
# nested(`{a}/{b}.parquet`)는 flat `/{dir}/{id}` URL 모델 밖이라 제외(news/public·edgar/sections).
# 비표형(검색 인덱스·JSON asset·deprecated)만 명시 제외.
_DOWNLOAD_EXCLUDE_DIRS = {
    "dart/contentIndex",  # 음절 bigram BM25 CSR 검색 인덱스 - 다운로드 표 아님
    "edgar/docs",  # deprecated 좀비(edgar/sections 로 이행, write 은퇴)
    "landing/map",  # 산업지도 JSON asset
    "landing/dashboards",  # 대시보드 JSON asset
    "landing/lenses",  # 분석 렌즈 제품 JSON asset
}

# shardKind - {id} 의 의미(다운로드 센터 UI 입력 + Tier2 적격 도출). 미등록 dir 은 "bulk"(단일/대형, Tier1 만).
#   company  = {종목코드|ticker}.parquet (회사당 flat)
#   series   = {시리즈|지수|월}.parquet
#   dateShard= {날짜}.parquet (전종목 대형 - Tier2 라이브 변환 불가, 413)
_DOWNLOAD_SHARD_KIND = {
    "dart/finance": "company",
    "dart/panel": "company",
    "dart/report": "company",
    "edgar/panel": "company",
    "edgar/financeStmt": "company",
    "edgar/prices/company": "company",
    "gov/prices/company": "company",
    "krx/prices/company": "company",
    "macro/fred": "series",
    "macro/ecos": "series",
    "macro/customs": "series",
    "expectations": "series",
    "gov/indices/index": "series",
    "research/brokerage": "series",
    "gov/prices/date": "dateShard",
    "gov/indices/date": "dateShard",
    # krx/prices·dart/scan·edgar/finance·edgar/meta·edgar/tickers·krx/indices = 미등록 → "bulk"(단일/대형, Tier1 만).
}


def downloadCatalog() -> list[dict]:
    """다운로드 센터 노출 카탈로그 - public·flat·표형 dir 만 (보안 SSOT).

    Capabilities:
        DATA_RELEASES 를 순회해 다운로드 센터(브라우저 Tier1·라이브 워커 Tier2)가 노출할 dir
        목록을 도출한다. 보안 경계 = `public` 플래그 단일 SSOT - public:False 는 자동 차단된다
        (private dir 6종이 공개 repo 와 same-repo 라 토큰 차단이 안 먹으므로 코드 게이트가 유일 방어).
    AIContext:
        다운로드 센터 노출 화이트리스트 런타임 도출자. 새 public flat 카테고리는
        추가 코드 0 으로 자동 노출, 새 private 은 자동 차단. TS 미러(downloadCatalog.ts)와 drift
        가드(tests/core/test_download_catalog.py)가 동기화를 강제한다.
    Guide:
        새 카테고리 노출은 DATA_RELEASES 에 public:True flat 으로 추가하면 자동. 비표형(검색 인덱스·
        JSON·deprecated)은 _DOWNLOAD_EXCLUDE_DIRS 에, {id} 의미는 _DOWNLOAD_SHARD_KIND 에 한 줄.
    When:
        다운로드 센터 카탈로그 렌더·워커 allowlist emit·drift 검증 시 호출.
    How:
        public:True · not nested · dir 미제외 인 항목만 모아 {dir, label, shardKind} 로 반환(dir 정렬).
    Requires:
        DATA_RELEASES 의 각 항목이 `dir`·`public` 키를 가진다(전 항목 충족).
    Raises:
        없음 - 빈 결과도 정상 반환.
    Args:
        없음.
    Returns:
        list[dict] - 각 {dir: str, label: str, shardKind: str}. dir 오름차순 정렬.
    Example:
        >>> dirs = {e["dir"] for e in downloadCatalog()}
        >>> "dart/finance" in dirs and "dart/allFilings" not in dirs
        True
    SeeAlso:
        DATA_RELEASES: 노출의 보안 SSOT(`public` 플래그).
        _DOWNLOAD_EXCLUDE_DIRS · _DOWNLOAD_SHARD_KIND: 비표형 제외·{id} 분류.
    """
    out: list[dict] = []
    for spec in DATA_RELEASES.values():
        if not spec.get("public"):  # private 자동 차단 (보안 SSOT)
            continue
        if spec.get("nested"):  # nested 는 flat URL 모델 밖
            continue
        directory = spec["dir"]
        if directory in _DOWNLOAD_EXCLUDE_DIRS:  # 비표형 명시 제외
            continue
        out.append(
            {
                "dir": directory,
                "label": spec["label"],
                "shardKind": _DOWNLOAD_SHARD_KIND.get(directory, "bulk"),
            }
        )
    return sorted(out, key=lambda entry: entry["dir"])


DATA_CATEGORY_ALIASES: dict[str, str] = {}


def resolveDataCategory(category: str) -> str:
    """호환 별칭(alias) 카테고리명을 활성 카테고리로 해석한다.

    Capabilities:
        옛 카테고리명(별칭)을 현행 DATA_RELEASES 키로 매핑한다. 미등록 이름은 그대로 반환해
        repoFor/hfBaseUrl 등이 graceful 하게 기본 경로로 떨어지게 한다.
    AIContext:
        카테고리 별칭이 코드 곳곳에 흩어지지 않게 해석을 단일화하는 L0 설정 함수다.
    Guide:
        새 별칭은 DATA_CATEGORY_ALIASES 한 줄로 추가하고, 호출자는 원본/별칭 무엇이든 넘긴다.
    When:
        repoFor/hfBaseUrl 등이 카테고리를 다루기 직전 정규화할 때.
    How:
        DATA_CATEGORY_ALIASES 에 있으면 그 활성 키, 없으면 입력 category 그대로 반환.
    Requires:
        없음 - 미등록 입력도 graceful 통과.
    Raises:
        없음.
    Args:
        category: 카테고리 키 또는 옛 별칭(미등록이면 입력 그대로 반환).
    Returns:
        등록된 별칭이면 활성 카테고리 키, 아니면 입력 category.
    Example:
        >>> resolveDataCategory("__unregistered__")
        '__unregistered__'
    SeeAlso:
        DATA_CATEGORY_ALIASES: 별칭→활성 카테고리 매핑.
        repoFor: 해석된 카테고리로 HF repo 를 정한다.
    """

    return DATA_CATEGORY_ALIASES.get(category, category)


def repoFor(category: str) -> str:
    """카테고리별 HuggingFace repo id - 전용 repo 가 지정됐으면 그것, 아니면 기본 HF_REPO.

    Capabilities:
        무거운 nested 카테고리(panel ~9 만 파일 · gdelt ~6 만)를 전용 repo 로 분리해 per-repo
        파일수 한계(~10 만/repo)·tree 열거 429 를 회피하기 위한 라우팅 단일 진입점.
    AIContext:
        업로드(uploadData/bulkUploadHf)·다운로드(dataLoader/ensure*FromHf) 양쪽이 repo_id 를
        하드코딩하는 대신 본 함수로 해석 → 전용 repo 전환이 dataConfig 한 곳에서 끝난다.
    Guide:
        데이터 이전(운영자 트리거) 전까지는 어떤 카테고리도 `repo` 필드를 두지 않아 전부 기본
        repo 를 공유 → 동작 무변경. 이전 완료 후 해당 카테고리에 `"repo": "..."` 한 줄 추가.
    When:
        HF 업로드/다운로드 대상 repo 를 결정할 때.
    How:
        DATA_RELEASES[category].get("repo") 가 truthy 면 그 값, 아니면 HF_REPO.
    Requires:
        없음 - 미등록 category 도 HF_REPO 로 graceful.
    Raises:
        없음.
    Args:
        category: DATA_RELEASES 카테고리 키 (미등록이어도 HF_REPO 반환).
    Returns:
        해당 카테고리 데이터가 사는 HuggingFace dataset repo id.
    Example:
        >>> repoFor("contentIndex")
        'eddmpython/dartlab-data'
    SeeAlso:
        DATA_RELEASES: 카테고리별 `repo`(선택)·`dir`·공개 여부.
        hfBaseUrl: repoFor 를 사용해 resolve URL 을 만든다.
    """
    category = resolveDataCategory(category)
    return DATA_RELEASES.get(category, {}).get("repo") or HF_REPO


def hfBaseUrl(category: str = "panel") -> str:
    """HuggingFace 데이터셋 base URL.

    Capabilities:
        DATA_RELEASES에 등록된 데이터 카테고리를 HuggingFace resolve URL로 변환한다.
    AIContext:
        데이터 다운로드 경로를 설명하거나 캐시 출처를 추적할 때 사용하는 L0 설정 함수다.
    Guide:
        새 데이터 카테고리는 DATA_RELEASES에 먼저 추가하고, 호출자는 카테고리 키만 넘긴다.
    When:
        dataLoader가 원격 parquet, zip, json 경로의 base URL을 만들 때 호출한다.
    How:
        repoFor(category) 로 repo 를 해석해 resolve base 를 만들고 DATA_RELEASES[category]["dir"] 를 붙인다.
    Requires:
        category가 DATA_RELEASES에 등록되어 있어야 한다.
    Raises:
        KeyError: category가 DATA_RELEASES에 없을 때.
    Args:
        category: DATA_RELEASES에 등록된 데이터 카테고리 키.
    Returns:
        HuggingFace resolve URL의 카테고리별 base 경로.
    Example:
        >>> hfBaseUrl("finance").endswith("/dart/finance")
        True
    SeeAlso:
        DATA_RELEASES: 카테고리별 원격 디렉터리와 공개 여부.
        dartlab.core.dataLoader.download: 반환 URL을 실제 다운로드에 사용한다.
    """
    category = resolveDataCategory(category)
    dirPath = DATA_RELEASES[category]["dir"]
    return f"https://huggingface.co/datasets/{repoFor(category)}/resolve/main/{dirPath}"
