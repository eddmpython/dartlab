// 매크로 경제지표 시계열 · macro/{fred,ecos}/observations.parquet (HF) hyparquet 직독.
// (seriesId, date, value) 가 seriesId+date 정렬이라 seriesId 필터로 row-group pruning.
// 차트 오버레이(ECON)·KPI 티커가 공유하는 단일 로더. 전체 파일 1.5MB 이하 · 시리즈당 첫 로드 수백 ms.
// 화이트리스트·출처표시 정본은 contracts (MACRO_SERIES·MACRO_ATTRIBUTION).
import { MACRO_SERIES, type MacroLatest, type MacroPoint, type MacroPort, type MacroTransmissionEdge, type MacroTransmissionQuery, type MacroTransmissionResult } from '@dartlab/ui-contracts';
import { loadJson } from '../../../data/dartlabData';
import { moduleFallbackCore, type DataCore } from '../../../data/fetch/request';

const browser = typeof window !== 'undefined';

const defById = new Map(MACRO_SERIES.map((s) => [s.id, s]));

interface ObsRow extends Record<string, unknown> {
	seriesId?: string | null;
	date?: Date | string | null;
	value?: number | null;
}

interface MacroDashboardFile {
	transmission?: MacroTransmissionResult | null;
}

// createHfMacroPort 는 ui/web 레거시(@dartlab/ui-runtime export 소비)가 core 없이 호출하므로(시그니처 불변
// 제약), core 미주입 경로 전용 모듈 코어를 lazy 생성한다. 어댑터(createPublicRuntime/createLocalRuntime)는
// 자신의 createDataCore() 를 주입하고, 이 폴백은 ui/web 같은 셸 직접 호출에만 쓰인다(financeSource.financeRowsCore 동형).
const macroCore = moduleFallbackCore();

function toYmd(d: Date | string | null | undefined): string {
	if (d == null) return '';
	if (d instanceof Date) {
		const y = d.getUTCFullYear();
		const m = String(d.getUTCMonth() + 1).padStart(2, '0');
		const dd = String(d.getUTCDate()).padStart(2, '0');
		return `${y}${m}${dd}`;
	}
	return String(d).replace(/-/g, '').slice(0, 8);
}

// 소스 파일(166KB·1.4MB)이 작아 통째 1 회 로드 → seriesId 그룹화가 시리즈별 range-read 10회보다 빠르고 단순.
// 결과 그룹 Map(transform)은 코어가 캐시하지 않으므로 호출마다 재그룹화되지만, 무거운 parquet read 는 코어가
// 캐시(60분 TTL·LRU)·dedup 해 공유한다(macro/{src} 1회 다운로드). 같은 src 다중 시리즈가 한 read 를 나눠 쓴다.
async function loadSource(core: DataCore, src: 'fred' | 'ecos'): Promise<Map<string, MacroPoint[]>> {
	const bySeries = new Map<string, MacroPoint[]>();
	let rows: ObsRow[];
	try {
		rows = await core.requestParquetRows<ObsRow>({
			origin: 'hfRange',
			path: `macro/${src}/observations.parquet`,
			columns: ['seriesId', 'date', 'value'],
			cacheKey: `macro.obs:${src}`,
			cache: { scope: 'memory', ttlMs: 60 * 60_000, maxEntries: 8 } // 분기/월 단위 갱신 · 60분 TTL
		});
	} catch {
		return bySeries; // 빈 맵 · 호출측 null 처리
	}
	for (const r of rows) {
		const id = r.seriesId == null ? '' : String(r.seriesId);
		const d = toYmd(r.date);
		if (r.value == null) continue; // null 관측 skip (Number(null)=0 오변환 차단 · Python drop_nulls 정합)
		const v = Number(r.value);
		if (!id || d.length !== 8 || !Number.isFinite(v)) continue;
		let arr = bySeries.get(id);
		if (!arr) bySeries.set(id, (arr = []));
		arr.push({ d, v });
	}
	for (const arr of bySeries.values()) arr.sort((a, b) => a.d.localeCompare(b.d));
	return bySeries;
}

// 지수형 월간 시리즈 → 12개월 전 대비 YoY %. 월 단위 키(YYYYMM) 매칭.
function toYoy(points: MacroPoint[]): MacroPoint[] {
	const byMonth = new Map(points.map((p) => [p.d.slice(0, 6), p.v]));
	const out: MacroPoint[] = [];
	for (const p of points) {
		const ym = p.d.slice(0, 6);
		const prevY = String(+ym.slice(0, 4) - 1) + ym.slice(4, 6);
		const base = byMonth.get(prevY);
		if (base != null && base !== 0) out.push({ d: p.d, v: +(((p.v - base) / Math.abs(base)) * 100).toFixed(2) });
	}
	return out;
}

/** 시리즈 전체 이력 (오름차순, yoy 정의 시 변환 적용). null = 미존재/실패. 소스 파일 1 회 로드 공유(코어 캐시). */
export async function loadMacroSeries(id: string, core?: DataCore): Promise<MacroPoint[] | null> {
	if (!browser) return null;
	const def = defById.get(id);
	if (!def) return null;
	const bySeries = await loadSource(macroCore(core), def.src);
	let pts = bySeries.get(id) ?? [];
	if (def.yoy) pts = toYoy(pts);
	return pts.length ? pts : null;
}

/** 시리즈 *원시* 이력 (yoy 미적용 · 저장된 index/level 그대로). 거시 시뮬 BVAR 입력처럼 원본이 필요할 때.
 *  같은 observations.parquet(getSeries 와 동일 데이터·캐시) · 별도 데이터 배선 아님, yoy 뷰변환만 생략. */
export async function loadMacroSeriesRaw(id: string, core?: DataCore): Promise<MacroPoint[] | null> {
	if (!browser) return null;
	const def = defById.get(id);
	if (!def) return null;
	const bySeries = await loadSource(macroCore(core), def.src);
	const pts = bySeries.get(id) ?? [];
	return pts.length ? pts : null;
}

/**
 * IndexPort 전용 raw 채널 · fred seriesId 의 원시 (d,v) 점을 yoy 변환·MACRO_SERIES 화이트리스트 *없이* 반환.
 * loadSource('fred') 코어 read 캐시를 ECON 오버레이와 공유(파일 1 회 로드) · SP500 등 지수는 yoy 무의미라 raw.
 * 화이트리스트 게이팅은 호출측(fredIndexSource 의 US_INDEX_PRESETS)이 담당 · 임의 ID dump 아님.
 */
export async function loadFredSeriesPoints(seriesId: string, core?: DataCore): Promise<MacroPoint[] | null> {
	if (!browser) return null;
	const bySeries = await loadSource(macroCore(core), 'fred');
	const pts = bySeries.get(seriesId);
	return pts && pts.length ? pts : null;
}

// 최근 1년(일별 252·월별 12) 구간을 최대 n 점으로 다운샘플 · 스파크라인 폴리라인용.
function sparkOf(pts: MacroPoint[], n = 40): number[] {
	const daily = pts.length > 400; // 일별 시리즈 추정
	const win = pts.slice(-(daily ? 252 : 12));
	if (win.length <= n) return win.map((p) => p.v);
	const out: number[] = [];
	for (let i = 0; i < n; i++) {
		const pt = win[Math.floor((i / (n - 1)) * (win.length - 1))];
		if (pt) out.push(pt.v);
	}
	return out;
}

/** KPI 티커용 · 화이트리스트 전 시리즈의 최신값+직전 대비 변화+스파크라인. src 그룹은 1 회만 로드(코어 캐시 공유). */
export async function loadMacroLatest(core?: DataCore): Promise<MacroLatest[]> {
	if (!browser) return [];
	const c = macroCore(core);
	// src 별 그룹 Map 을 src 당 1 회만 빌드(loadMacroSeries 시리즈당 재그룹화 회피) · 무거운 read 는 코어가 공유.
	const groups = new Map<'fred' | 'ecos', Map<string, MacroPoint[]>>();
	const groupFor = async (src: 'fred' | 'ecos'): Promise<Map<string, MacroPoint[]>> => {
		let g = groups.get(src);
		if (!g) groups.set(src, (g = await loadSource(c, src)));
		return g;
	};
	const all = await Promise.all(
		MACRO_SERIES.map(async (def) => {
			const bySeries = await groupFor(def.src);
			let pts = bySeries.get(def.id) ?? [];
			if (def.yoy) pts = toYoy(pts);
			if (!pts.length) return null;
			const last = pts[pts.length - 1];
			if (!last) return null;
			const prev = pts.length > 1 ? pts[pts.length - 2] : null;
			return { def, v: last.v, d: last.d, chg: prev ? +(last.v - prev.v).toFixed(4) : null, spark: sparkOf(pts) };
		})
	);
	return all.filter((x): x is MacroLatest => x != null);
}

function marketSet(market: 'KR' | 'US', includeCrossMarket: boolean): Set<string> {
	if (market === 'US') return new Set(includeCrossMarket ? ['US', 'GLOBAL'] : ['US']);
	return new Set(includeCrossMarket ? ['KR', 'US', 'GLOBAL'] : ['KR']);
}

function edgeMatches(edge: MacroTransmissionEdge, sectorKey: string | null, markets: Set<string>): boolean {
	if (!markets.has(edge.market)) return false;
	if (!sectorKey) return true;
	return edge.sectorKeys.includes('all') || edge.sectorKeys.includes(sectorKey);
}

function filterTransmission(payload: MacroTransmissionResult, query: MacroTransmissionQuery = {}): MacroTransmissionResult {
	const market = query.market ?? payload.market ?? 'KR';
	const sectorKey = query.sectorKey ?? payload.sectorKey ?? null;
	const markets = marketSet(market, query.includeCrossMarket ?? true);
	const edges = payload.edges.filter((edge) => edgeMatches(edge, sectorKey, markets));
	const driverIds = new Set(edges.map((edge) => edge.driverId));
	return {
		...payload,
		market,
		sectorKey,
		edges,
		drivers: payload.drivers.filter((driver) => driverIds.has(driver.id)),
		sourceRefs: [...new Set(['dashboards/macro.json#transmission', ...(payload.sourceRefs ?? [])])]
	};
}

async function loadMacroTransmission(query: MacroTransmissionQuery = {}): Promise<MacroTransmissionResult | null> {
	if (!browser) return null;
	const dashboard = await loadJson<MacroDashboardFile>('dashboards/macro.json', { fetchFn: fetch, required: false });
	const payload = dashboard?.transmission;
	return payload ? filterTransmission(payload, query) : null;
}

/** HF 공개 데이터 기반 MacroPort · 거시 시계열은 회사·앱 무관이라 local 셸도 본 포트를 명시적으로 재사용한다.
 *  core 는 어댑터(createXRuntime)가 주입(전역 싱글턴 금지). 미주입(ui/web 레거시 직접 호출)은 모듈 폴백 코어.
 *  ⛔ 거시 시뮬은 본 포트에 없음 · 런타임 pyodide(landing) 가 직접 실행, 별도 데이터 배선 금지. */
export function createHfMacroPort(core?: DataCore): MacroPort {
	const c = macroCore(core);
	return {
		async listSeries() {
			return MACRO_SERIES;
		},
		getSeries: (id) => loadMacroSeries(id, c),
		getSeriesRaw: (id) => loadMacroSeriesRaw(id, c),
		getLatest: () => loadMacroLatest(c),
		getTransmission: (query) => loadMacroTransmission(query)
	};
}
