// 오리진 레지스트리 · 데이터 워크벤치 SSOT 의 "어디서 가져오나" 단일 표. (mainPlan/data-workbench-ssot 02·03)
// P1: HF 계열(hf·hfRange) 만 등록 · 기존 origin.ts(HF URL SSOT)를 흡수.
// P2: news·naver 워커 등록 · newsSource/naverPriceSource 가 각자 복제하던 env 게이트 + dev 프록시 URL
//   조립을 여기로 흡수. 미배선(localApi·duckdbHf)은 후속 wave. 미등록 호출은 명시 throw(배선순서 가드).
//   landingJson(landing JSON arm)은 origin 에서 제외 · loadJson(dartlabData)이 영속 cacheStore + 다중URL
//   폴백(local↔HF) + base 전역에 의존하는 별도 arm 이라, 코어 단일-URL origin 추상·전역금지를 어기지 않게
//   sibling 으로 둔다(dual-SSOT, 설계 패널 적대검증 결론. mainPlan/_done/data-workbench-ssot/07).
import { hfUrl, hfRangeUrl, hfMediaUrl, hfRevisionUrl } from './hf';

// vite env 안전 접근 · runtime 패키지 tsc 는 vite/client 타입 없이 검사된다(origin.ts 동일 패턴, 소비 앱이 번들 시 치환).
const viteEnv = (import.meta as { env?: Record<string, string | boolean | undefined> }).env;

// 워커 프록시 base URL(가역 빌드-env 게이트). 비우면 미설정 · 호출측이 originConfigured 로 미동작([]) 판정.
//   news = CF 워커 /news 라우트(전 환경 동일, dev 폴백 없음 · /__news 미들웨어는 구현된 적 없음).
//   marketNews = CF 워커 /market-news 라우트(전 환경 동일, 네이버 검색 라이브 · newsWorker 동형 게이트).
//   marketFilings = CF 워커 /market-filings 라우트(전 환경 동일, DART list 라이브 당일 공시 · 동형 게이트).
//   naver = dev 는 Vite /__naver 미들웨어(브라우저 CORS 우회), 프로덕션은 CF 프록시 /naver 라우트.
const NEWS_PROXY = ((viteEnv?.VITE_DARTLAB_NEWS_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
const MARKET_NEWS_PROXY = ((viteEnv?.VITE_DARTLAB_MARKET_NEWS_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
const MARKET_FILINGS_PROXY = ((viteEnv?.VITE_DARTLAB_MARKET_FILINGS_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
//   ipoFilings = CF 워커 /ipo-filings 라우트(전 환경 동일, DART list corp_cls=E 라이브 · 동형 게이트).
//     상장 전 발행사는 HF bake(Y/K 한정)에 없어 이 라이브 read-through 가 퍼블릭 유일 데이터원(베이크 0).
const IPO_FILINGS_PROXY = ((viteEnv?.VITE_DARTLAB_IPO_FILINGS_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
const NAVER_PROXY = ((viteEnv?.VITE_DARTLAB_NAVER_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
//   csvWorker = CF 워커 /v1/{dir}/{id}.{csv|tsv} 라우트(라이브 데이터 API, parquet→CSV/TSV 온더플라이).
//     미설정 → Tier2 비활성, 데이터센터는 Tier1 다운로드만 노출(dev=퍼블릭 기준 무중단). mainPlan/data-download-center 03.
const CSV_PROXY = ((viteEnv?.VITE_DARTLAB_CSV_PROXY as string | undefined) ?? '').replace(/\/+$/, '');
const naverDev = Boolean(viteEnv?.DEV);
// gov 주가 dev 라이브 fill 게이트(naverDev 동형) · dev 만 /__gov 미들웨어 존재, 프로덕션은 읽기 전용.
const govDev = Boolean(viteEnv?.DEV);

export type OriginId =
	| 'hf'
	| 'hfRange'
	| 'hfRevisionRange'
	| 'hfApi'
	| 'hfMedia'
	| 'podcastMedia'
	| 'localApi'
	| 'newsWorker'
	| 'marketNewsWorker'
	| 'marketFilingsWorker'
	| 'ipoFilingsWorker'
	| 'naverWorker'
	| 'duckdbHf'
	| 'govDev'
	| 'csvWorker';

/** 캐시 정책 · 오리진별 차등(정직 TTL, 04 §정직 TTL). scope='none' = 무캐시.
 *  ('persist' 는 선언만 하고 미구현이던 죽은 scope라 제거 · 영속 캐시는 JSON arm(dartlabData.loadJson)이
 *   cacheStore 로 직접·더 풍부하게[2-tier stale] 담당. 코어에 접지 않는 dual-SSOT 결정, mainPlan/_done.) */
export interface CachePolicy {
	scope: 'memory' | 'none';
	ttlMs: number;
	maxEntries?: number;
}

interface OriginDef {
	resolve: (path: string) => string;
	defaultCache: CachePolicy;
	/** 게이트형 오리진(env 미설정 시 미동작). 미정의 = 항상 설정됨. */
	configured?: () => boolean;
}

const MIN = 60_000;

// 워커 라우트 URL 조립 · path = 종목 코드. 둘 다 `?code=<encoded>` 쿼리(옛 newsEndpoint/naverEndpoint 동일).
// path 는 종목코드, 또는 "코드\t회사명"(회사명 있으면 라이브 RSS 검색어 q 로 워커에 전달). resolve(path) 시그니처 유지.
const newsWorkerUrl = (spec: string): string => {
	const tab = spec.indexOf('\t');
	const code = tab >= 0 ? spec.slice(0, tab) : spec;
	const name = tab >= 0 ? spec.slice(tab + 1) : '';
	const q = name ? `&q=${encodeURIComponent(name)}` : '';
	return `${NEWS_PROXY}?code=${encodeURIComponent(code)}${q}`;
};
// market-news 워커 · path = 시장 코드(KR/US). 종목 워커와 달리 라이브 RSS 검색이라 code 대신 market 쿼리.
const marketNewsWorkerUrl = (market: string): string => `${MARKET_NEWS_PROXY}?market=${encodeURIComponent(market)}`;
// market-filings 워커 · 쿼리 없는 고정 라우트(당일 전체 공시). resolve(path) 의 path 무시.
const marketFilingsWorkerUrl = (): string => MARKET_FILINGS_PROXY;
// ipo-filings 워커 · 쿼리 없는 고정 라우트(최근 85일 corp_cls=E 지분증권 신고 목록). path 무시.
const ipoFilingsWorkerUrl = (): string => IPO_FILINGS_PROXY;
const naverWorkerUrl = (code: string): string => {
	const q = `code=${encodeURIComponent(code)}`;
	return naverDev ? `/__naver?${q}` : `${NAVER_PROXY}?${q}`;
};

// hf=소형 통파일/seed(프록시 엣지캐시 경로), hfRange=byte-range(직결). origin.ts 정책 그대로 흡수.
// newsWorker·naverWorker=언론사 저작권 archive 워커 read(라이브 표시) · 신선도형이라 짧은 TTL.
// 팟캐스트 미디어 base(R2 dartlab-podcast, r2.dev 공개) · channel.yaml r2.baseUrl 미러. index.json(크로스링크)·feed·오디오·커버 서빙.
const PODCAST_BASE = ((viteEnv?.VITE_DARTLAB_PODCAST_BASE as string | undefined) ?? 'https://pub-ef732bbc413941dd80734f96e0cfe95d.r2.dev').replace(/\/+$/, '');
const HF_DATASET_API = 'https://huggingface.co/api/datasets/eddmpython/dartlab-data';

const ORIGINS: Partial<Record<OriginId, OriginDef>> = {
	hf: { resolve: hfUrl, defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 64 } },
	hfRange: { resolve: hfRangeUrl, defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 128 } },
	hfRevisionRange: {
		resolve: (path) => {
			const separator = path.indexOf('/');
			if (separator <= 0) throw new Error('[origins] hfRevisionRange path는 revision/file 형식이어야 합니다.');
			return hfRevisionUrl(path.slice(0, separator), path.slice(separator + 1));
		},
		defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 64 }
	},
	hfApi: {
		resolve: (path) => path.startsWith('?')
			? `${HF_DATASET_API}${path}`
			: `${HF_DATASET_API}/${path.replace(/^\/+/, '')}`,
		defaultCache: { scope: 'memory', ttlMs: 10 * MIN, maxEntries: 8 }
	},
	// hfMedia=중앙 media repo(HF 직결). objects는 불변이고 manifests는 런타임 파생 뷰다.
	hfMedia: { resolve: hfMediaUrl, defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 64 } },
	// 팟캐스트 크로스링크 index.json · 미디어(R2 r2.dev). 비게이트(항상 설정 · 폴백 base 있음). index.json 은 호출부가 no-cache 로 읽음.
	podcastMedia: {
		resolve: (path) => `${PODCAST_BASE}/${path.replace(/^\/+/, '')}`,
		defaultCache: { scope: 'memory', ttlMs: 30 * MIN, maxEntries: 8 }
	},
	newsWorker: {
		resolve: newsWorkerUrl,
		defaultCache: { scope: 'memory', ttlMs: 10 * MIN, maxEntries: 64 },
		configured: () => Boolean(NEWS_PROXY) // 프록시 미설정 → 미동작(빈 섹션), dev 폴백 없음
	},
	// market-news 라이브 RSS 워커 · HF 누적 shard 위에 머지되는 오버레이라, 미설정/실패해도 HF base 는 보임.
	marketNewsWorker: {
		resolve: marketNewsWorkerUrl,
		defaultCache: { scope: 'memory', ttlMs: 10 * MIN, maxEntries: 8 },
		configured: () => Boolean(MARKET_NEWS_PROXY)
	},
	// market-filings 라이브 DART 공시 워커 · HF 누적 위 머지 오버레이. 미설정/실패해도 HF base 는 보임.
	marketFilingsWorker: {
		resolve: marketFilingsWorkerUrl,
		defaultCache: { scope: 'memory', ttlMs: 5 * MIN, maxEntries: 1 },
		configured: () => Boolean(MARKET_FILINGS_PROXY)
	},
	// ipo-filings 라이브 워커 · 상장 전 발행사(E)는 HF base 자체가 없음 → 미설정 = 발굴 목록 빈값([]).
	ipoFilingsWorker: {
		resolve: ipoFilingsWorkerUrl,
		defaultCache: { scope: 'memory', ttlMs: 30 * MIN, maxEntries: 1 },
		configured: () => Boolean(IPO_FILINGS_PROXY)
	},
	naverWorker: {
		resolve: naverWorkerUrl,
		defaultCache: { scope: 'memory', ttlMs: 10 * MIN, maxEntries: 64 },
		configured: () => naverDev || Boolean(NAVER_PROXY) // dev=미들웨어 / 프로덕션=프록시 설정 시
	},
	// dev 전용 gov 주가 라이브 fill · Vite /__gov 미들웨어가 data.go.kr 호출→정규화→HF 업로드 후 GovCandleFile 반환.
	// path=종목코드. naverWorker(/__naver) 동형. 무캐시(즉시 HF 반영 · 다음 read 가 HF 캐시). 프로덕션 미동작(읽기 전용).
	govDev: {
		resolve: (code) => `/__gov?code=${encodeURIComponent(code)}`,
		defaultCache: { scope: 'none', ttlMs: 0 },
		configured: () => govDev
	},
	// 라이브 데이터 API 워커 · path = `{dir}/{id}.{csv|tsv}[?cols=&tail=&head=&freq=]`. 데이터센터 링크빌더가
	// 이 origin 으로 Tier2 =IMPORTDATA URL 을 만든다(직접 조립 금지, uiDataWiring 가드 준수). 미설정 → Tier1 만.
	csvWorker: {
		resolve: (path) => `${CSV_PROXY}/v1/${path.replace(/^\/+/, '')}`,
		defaultCache: { scope: 'memory', ttlMs: 60 * MIN, maxEntries: 64 },
		configured: () => Boolean(CSV_PROXY)
	}
};

/** 오리진 상대경로 → 절대 URL. 미등록 오리진은 throw(P2 등록 또는 배선순서 위반 노출). */
export function originUrl(id: OriginId, path: string): string {
	const def = ORIGINS[id];
	if (!def) throw new Error(`[origins] '${id}' 미등록 · data/origins/registry 에 추가하거나 배선순서 확인(P2).`);
	return def.resolve(path);
}

/** 오리진 기본 캐시 정책(호출부 override 가능). 미등록은 undefined. */
export function originCache(id: OriginId): CachePolicy | undefined {
	return ORIGINS[id]?.defaultCache;
}

/** 게이트형 오리진이 설정(배선)됐는지. false = 미동작([] 반환, 코어 호출 생략). 비게이트 오리진은 항상 true. */
export function originConfigured(id: OriginId): boolean {
	const def = ORIGINS[id];
	if (!def) return false;
	return def.configured ? def.configured() : true;
}
