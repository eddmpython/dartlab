// public adapter · static/HF 데이터 포트 실구현 조립 (책임 경계 02 §9.1).
// silent fallback 금지: 모든 포트 메서드는 단일 경로다. 공유 엔진(duckdb-wasm 계열) 의존 메서드는
// 셸(landing)이 `shared` 로 주입한다 · 어댑터가 landing 을 역방향 import 하지 않기 위한 필수 계약.
// 아직 surface 가 소비하지 않는 포트(navigation·storage·map·ai)는 명시적 throw 게이트 유지.
// search(공시 본문 검색)는 단계-8 에서 createSearchPort 로 배선 · 무서버 HF sidecar byte-range fetch.
import type {
	CompanyChange,
	CompanyPort,
	DartLabRuntime,
	FilingPort,
	FinancePort,
	IpoPort,
	LiveCompanyReportFact,
	NewsPort,
	PricePort,
	ProductIndexItem,
	RuntimeEnvironment,
	ScanPort,
	ViewerPort
} from '@dartlab/ui-contracts';
import { resolveMarket } from '@dartlab/ui-contracts';
import { loadGovCandles, loadGovRecent } from './sources/govPriceSource';
import { loadEdgarCandles, loadEdgarRecent } from './sources/edgarPriceSource';
import { loadNaverFresh } from './sources/naverPriceSource';
import { loadInitialOHLCV, loadOlderYear, loadedCandles, mergeDedup, seedCandles } from './sources/priceSource';
import { createPublicIndexPort } from './sources/indexSource';
import { loadTerminalFinance } from './sources/financeSource';
import { createHfMacroPort } from './sources/macroSource';
import { loadCompanyRelations } from './sources/relationsSource';
import { loadIndustryProfitPool } from './sources/industryPoolSource';
import { loadHfProductIndexMap } from './sources/productIndexSource';
import { loadCompanyRegularFilings } from './sources/regularFilingsSource';
import { loadCompanyNonRegularFilings, loadMarketFeed, loadRecentFilingsForCodes } from './sources/nonRegularFilingsSource';
import { loadIpoFilings } from './sources/ipoFilingsSource';
import { createDataCore, type DataCore } from '../../data/fetch/request';
import { createSearchPort } from '../../data/search/filingSearch';
import { loadCompanyNews } from './sources/newsSource';
import { loadMarketNews } from './sources/marketNewsSource';
import { createReportSource } from './sources/reportSource';
import { publicExportPort, type PublicExportShared } from './sources/exportSource';
import { localStoragePort } from '../local/sources/storageSource';

/** 공유 엔진 의존 메서드 · companyLive(reportFacts)·duckSql(changes) 는 landing 잔류라 셸이 주입. */
export interface PublicRuntimeSharedPorts {
	reportFacts(code: string): Promise<LiveCompanyReportFact[]>;
	changes(code: string, limit?: number): Promise<CompanyChange[]>;
}

export interface PublicRuntimeOptions {
	env: Omit<RuntimeEnvironment, 'kind'>;
	shared: PublicRuntimeSharedPorts;
	/** 공개 셸의 뷰어 노출 형태 · landing = 임베드 컴포넌트(urlForCompany → null). */
	viewer: ViewerPort;
	/** table-export · generate 가 wrap 할 브라우저 워크북 빌더(surfaces buildWorkbook, bundle-bound). 셸 주입.
	 *  미주입이면 listExportableTables·양식 CRUD 는 동작, generate 만 정직히 throw(배선 순서 가드). */
	exportShared?: PublicExportShared;
}

function notWiredYet(what: string, stage: string): never {
	throw new Error(`[public adapter] ${what} 는 ${stage}에서 구현된다 · 이 호출이 보이면 배선 순서 위반이다.`);
}

// 전 종목 productIndex 는 Map 소스를 Record(JSON-safe 계약)로 1 회 변환해 공유.
// (Map→Record 변환은 transform · 무거운 read 는 코어가 캐시·dedup. 이 메모이즈는 변환 결과 1회 재사용 한정.)
let productIndexPromise: Promise<Record<string, ProductIndexItem> | null> | null = null;
function loadProductIndexRecord(core: DataCore): Promise<Record<string, ProductIndexItem> | null> {
	productIndexPromise ??= (async () => {
		try {
			const map = await loadHfProductIndexMap(core);
			return Object.fromEntries(map);
		} catch {
			return null;
		}
	})();
	return productIndexPromise;
}

// 로컬 어댑터도 이 포트를 그대로 재사용한다 · gov HF + recent + naver fresh 는 백엔드 0(브라우저 단일 경로)
// 라, 로컬 :8400 미가동이어도 차트가 퍼블릭과 동일하게 뜬다(finance·macro·company 와 같은 "깃헙페이지 자산 공유").
export function publicPricePort(core?: DataCore): PricePort {
	return {
		// 회사파일(전종목 주간 파생, 전체 이력) ∥ recent(최근 30거래일 전종목 슬림 1파일) ∥ 네이버 fresh tail
		// 병렬 → 병합. 회사파일이 주간 갱신이어도 recent tail 이 최신 거래일을, 네이버 fresh 가 gov 미발행
		// 최신일(금요일치=월요일 발행)을 보장. mergeDedup 은 stable sort + 선두 우선이라 겹치는 날은 gov 가
		// 이기고 네이버는 gap(미발행일)만 채움 · gov=네이버 동일값이라 점프 없음. 둘 다 미스면 date/ 폴백.
		// dev 미스는 /__gov 라이브 채움, 네이버 fresh 는 /__naver(dev)·CF 프록시(프로덕션) 경로.
		async initial(code, year) {
			// US(EDGAR) = 회사별 OHLCV 통파일 전체이력 1발 seed (Yahoo bake, edgar/prices/company). KRX 연도샤드·gov·네이버 경로 무관.
			const m = resolveMarket(code);
			if (m.market === 'US' && m.ticker) {
				const [base, recent] = await Promise.all([loadEdgarCandles(m.ticker, core), loadEdgarRecent(core)]);
				const merged = mergeDedup(base ?? [], recent?.[m.ticker] ?? []);
				return merged.length ? seedCandles(code, merged) : null;
			}
			const c = code.trim();
			const [gov, recent, fresh] = await Promise.all([loadGovCandles(c, core), loadGovRecent(core), loadNaverFresh(c, core)]);
			const tail = recent?.[c] ?? [];
			if ((gov && gov.length) || tail.length || fresh.length) return seedCandles(c, mergeDedup(gov ?? [], tail, fresh));
			return loadInitialOHLCV(c, year, core);
		},
		// US 는 initial 이 통파일 전체이력을 이미 seed · 좌측 팬 추가 백필 없음([]). KR 만 gov/prices/date 연도샤드 prepend.
		older: (code, targetYear) => (resolveMarket(code).market === 'US' ? Promise.resolve([]) : loadOlderYear(code, targetYear, core)),
		loaded: loadedCandles, // code-keyed 캐시 공유 · US ticker ∩ KR 6자리코드 모양 무충돌
		govCandles: (code) => (resolveMarket(code).market === 'US' ? Promise.resolve(null) : loadGovCandles(code, core)), // gov(공공누리) = KR 전용
		govRecent: () => loadGovRecent(core)
	};
}

function publicCompanyPort(shared: PublicRuntimeSharedPorts, core: DataCore): CompanyPort {
	return {
		async products(code) {
			const rec = await loadProductIndexRecord(core);
			return rec?.[code.trim()] ?? null;
		},
		productIndex: () => loadProductIndexRecord(core),
		relations: loadCompanyRelations,
		reportFacts: shared.reportFacts,
		industryProfitPool: loadIndustryProfitPool
	};
}

function publicFilingPort(core: DataCore): FilingPort {
	return {
		regular: (code, limit = 500) => loadCompanyRegularFilings(core, code, limit),
		nonRegular: (code) => loadCompanyNonRegularFilings(core, code), // 전 이력 · fetch 코어(캐시·dedup), 전역 1파일 stock_code 필터
		recentForCodes: (codes) => loadRecentFilingsForCodes(core, codes), // 워치 신선도 · fetch 코어(HF allFilings 배치·10분 TTL·dedup)
		marketFeed: () => loadMarketFeed(core), // 시장 공시 피드 · 전상장사 3개월 통파일 1 GET(market_recent.parquet)
		// panel 격자 3종은 공개 뷰어 코드(landing)가 단계-6(뷰어 추출)에서 어댑터로 들어온다.
		panelToc: () => notWiredYet('filing.panelToc', '단계-6(viewer 추출)'),
		panelInit: () => notWiredYet('filing.panelInit', '단계-6(viewer 추출)'),
		panelGrid: () => notWiredYet('filing.panelGrid', '단계-6(viewer 추출)')
	};
}

function publicFinancePort(core: DataCore): FinancePort {
	return { bundle: (code, scope) => loadTerminalFinance(core, code, scope) };
}

// 로컬 어댑터도 그대로 재사용 · 뉴스는 private 라 브라우저 직독 불가, 퍼블릭·로컬 모두 워커(/news) 단일 경로.
// core 미주입 호출(ui/web 레거시)은 loadCompanyNews 의 모듈 폴백 코어를 쓴다(govCore 동형).
export function publicNewsPort(core?: DataCore): NewsPort {
	return {
		forCompany: (code, name) => loadCompanyNews(code, core, name), // 종목별 = byCompany 아카이브 + RSS 라이브 머지
		market: () => loadMarketNews(core) // 시장 전체 = public rss 아카이브 최근 shard 직독
	};
}

// IPO · 발굴 목록은 라이브 워커(/ipo-filings) 공통배선. 단건 리포트는 무거운 본문 런타임 파싱이라
// 로컬 상위집합(/api) 전용 · surface 가 env.kind==='local' 로 진입을 게이트한다(filing.panel* 동형).
function publicIpoPort(core: DataCore): IpoPort {
	return {
		recent: () => loadIpoFilings(core),
		report: () => notWiredYet('ipo.report', '로컬 상위집합(/api 런타임 파싱) 전용 · env.kind 게이트')
	};
}

function publicScanPort(shared: PublicRuntimeSharedPorts): ScanPort {
	return {
		changes: shared.changes,
		listTableSources: () => notWiredYet('scan.listTableSources', '단계-8(scan 추출)'),
		getPresets: () => notWiredYet('scan.getPresets', '단계-8(scan 추출)'),
		savePreset: () => notWiredYet('scan.savePreset', '단계-8(scan 추출)')
	};
}

export function createPublicRuntime(options: PublicRuntimeOptions): DartLabRuntime {
	const env: RuntimeEnvironment = { ...options.env, kind: 'public' };
	const dataCore = createDataCore(); // 데이터 워크벤치 SSOT 코어(어댑터당 1) · RuntimeCache·RequestDedup 실배선
	return {
		env,
		company: publicCompanyPort(options.shared, dataCore),
		price: publicPricePort(dataCore),
		index: createPublicIndexPort(dataCore),
		filing: publicFilingPort(dataCore),
		news: publicNewsPort(dataCore),
		finance: publicFinancePort(dataCore),
		viewer: options.viewer,
		macro: createHfMacroPort(dataCore),
		report: createReportSource(dataCore),
		scan: publicScanPort(options.shared),
		ipo: publicIpoPort(dataCore),
		export: publicExportPort(localStoragePort(), options.exportShared),
		get map() {
			return notWiredYet('map', '단계-8(map 추출)');
		},
		// 공시 본문 검색 · HF sidecar(postings/meta.bin) byte-range fetch, 무서버(:8400 불요, 로컬과 동일 코어·경로).
		search: createSearchPort(dataCore),
		get ai() {
			return notWiredYet('ai', '단계-7(ask 추출)');
		},
		get services() {
			return notWiredYet('services', '단계-5(서비스 레지스트리 배선)');
		},
		get navigation() {
			return notWiredYet('navigation', '단계-4a-3(셸 내비 주입)');
		},
		get storage() {
			return notWiredYet('storage', '단계-4a-3(셸 스토리지 주입)');
		},
		telemetry: { event() {} },
		featureFlags: { isEnabled: () => false }
	};
}
