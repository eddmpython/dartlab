<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { SlidersHorizontal } from 'lucide-svelte';
	import Header from '$lib/components/sections/Header.svelte';
	import { FreshnessBadge } from '@dartlab/ui-surfaces/map';
	import {
		Grid,
		ColumnGroupBar,
		PresetModal,
		CellTooltip,
		Distribution,
		InsightsFeed,
		SavedSets,
		VerdictRibbon,
		encodeScanPayload,
		decodeScanPayload,
		DEFAULT_COLUMNS,
		METRICS_BY_KEY,
		PINNED_COLUMNS,
		PRESETS_BY_ID,
		buildVerdictGrid,
		nearMiss,
		relaxThreshold,
		loadEdgarNodes,
		percentilesByMarket,
		inScope,
		sortAllowed,
		MARKET_LABEL,
		type MarketScope,
		type SavedColumnSet,
		type ScanNode,
		type FilterCond,
		type SortKey,
		type MetricGroup,
		type Preset,
		type RuntimeLoader,
		type PriceMetrics,
		type ValuationMetrics,
		type DbState
	} from '@dartlab/ui-surfaces/scan';
	import { getPublicRuntime } from '$lib/runtime/publicRuntime';
	import { HF_RESOLVE, loadJson } from '@dartlab/ui-runtime/data/dartlabData';
	import type { ProductIndexItem } from '@dartlab/ui-contracts';
	import type { ValuationRuntimeMetrics } from '$lib/data/valuationRuntime';
	import type { ChangeMetrics } from '$lib/data/changesRuntime';
	import type { DartDb } from '$lib/data/duckdb';

	let { data } = $props();

	// ── State ──────────────────────────────────────────
	let hfNodes = $state.raw<ScanNode[]>([]);
	let runtimeIndustries = $state.raw<Array<{ id: string; name: string; color: string; count: number }>>([]);
	let runtimeMeta = $state<any>(null);
	let baseNodes = $derived.by(() => {
		const nodes = hfNodes.length > 0 ? hfNodes : ((data.ecosystem?.nodes || []) as ScanNode[]);
		const markets = (data.markets || {}) as Record<string, string>;
		// ecosystem.json 에 market 필드 없으면 markets.json 으로 보강
		if (Object.keys(markets).length === 0) return nodes;
		return nodes.map((n) => {
			const m = (n as any).market;
			if (m) return n;
			const code = n.id || (n as any).stockCode;
			const market = markets[code];
			return market ? ({ ...n, market } as ScanNode) : n;
		});
	});
	let industries = $derived.by(() => {
		const existing = (data.ecosystem?.industries || []) as Array<{
			id: string;
			name: string;
			color: string;
			count: number;
		}>;
		if (existing.length > 0 && hfNodes.length === 0) return existing;
		if (runtimeIndustries.length > 0) return runtimeIndustries;
		const groups = new Map<string, { id: string; name: string; color: string; count: number }>();
		for (const node of hfNodes) {
			const id = String(node.industry || node.market || 'KRX');
			const item = groups.get(id) ?? {
				id,
				name: String(node.industryName || id),
				color: String(node.color || '#94a3b8'),
				count: 0
			};
			item.count += 1;
			groups.set(id, item);
		}
		return Array.from(groups.values());
	});

	let activeColumns = $state<string[]>([...DEFAULT_COLUMNS]);
	let sorts = $state<SortKey[]>([{ key: 'marketCap', dir: 'desc' }]);
	let sort = $derived(sorts[0] ?? null);
	let dataExplorerOpen = $state(false);
	let conds = $state<FilterCond[]>([]);
	let selectedIndustries = $state<Set<string>>(new Set());
	let selectedRow = $state<string | null>(null);
	let searchQuery = $state('');
	let presetOpen = $state(false);
	let activePresetId = $state<string | null>(null);
	let runtimeState = $state<'loading' | 'ready' | 'error'>('loading');
	let runtimeError = $state<string | null>(null);
	let trendState = $state<'idle' | 'loading' | 'ready' | 'error'>('idle');
	let trendError = $state<string | null>(null);
	let DetailComponent = $state<any>(null);
	let DataExplorerComponent = $state<any>(null);
	// 유니버스 백테스터(간판① · 전종목 크로스섹셔널). lazy 모달.
	let universeOpen = $state(false);
	let UniverseBacktesterComponent = $state<any>(null);

	// ── Runtime data + opt-in DuckDB lifecycle ────────
	let dbState = $state<DbState>('idle');
	let dbError = $state<string | null>(null);
	let dartDb = $state<DartDb | null>(null);
	let dbBootStarted = false;
	let priceMetricsStarted = false;
	let valuationStarted = false;
	let priceOneYearScheduled = false;
	let runtimeWorker: Worker | null = null;
	let priceWorker: Worker | null = null;
	let changesWorker: Worker | null = null;
	let priceMap = $state.raw<Map<string, PriceMetrics>>(new Map());
	let valuationMap = $state.raw<Map<string, ValuationMetrics>>(new Map());
	let changesMap = $state.raw<Map<string, ChangeMetrics>>(new Map());
	let financeMap = $state.raw<Map<string, Partial<ScanNode>>>(new Map());
	let productMap = $state.raw<Map<string, ProductIndexItem>>(new Map());
	let loaderLoading = $state<Set<RuntimeLoader>>(new Set());
	let loaderReady = $state<Set<RuntimeLoader>>(new Set());
	let loaderError = $state<Map<RuntimeLoader, string>>(new Map());
	let pendingColumnGroups = $state<Set<MetricGroup>>(new Set());
	let loadingColumnGroups = $derived.by(() => {
		const groups = new Set<MetricGroup>();
		for (const group of pendingColumnGroups) {
			const loader = loaderForGroup(group);
			if (loader && loaderLoading.has(loader)) groups.add(group);
		}
		return groups;
	});

	// ── Cell hover tooltip ────────────────────────────
	let cellHover = $state<{
		stockCode: string;
		label: string;
		metricKey: string;
		formattedValue: string;
		spark: number[];
		x: number;
		y: number;
	} | null>(null);

	// ── Distribution panel: bin highlight (양방향) ────
	let highlightBin = $state<{ x0: number; x1: number } | null>(null);
	// 숫자 컬럼으로 정렬했을 때만 분포가 있다. 없으면 320px 트랙을 예약하지 않는다
	// (전에는 placeholder 문구만 띄운 채 가로 320px 를 상시 점유했다).
	let hasDistribution = $derived(Boolean(sort && METRICS_BY_KEY[sort.key]?.type === 'number'));

	// ── DART(KR) + EDGAR(US) ──────────────────────────
	// 기본은 KR. US 는 요청 시 edgar/scan/finance.parquet 를 브라우저가 직독해 노드를 만든다
	// (신규 베이크 0). 산업 taxonomy 가 달라 US 는 'SIC:*' 네임스페이스로 격리된다.
	let marketScope = $state<MarketScope>('KR');
	let usNodes = $state.raw<ScanNode[]>([]);
	let usState = $state<'idle' | 'loading' | 'ready' | 'error'>('idle');
	let usError = $state<string | null>(null);

	async function ensureUsNodes() {
		if (usState === 'loading' || usState === 'ready') return;
		usState = 'loading';
		usError = null;
		try {
			await bootDuckDbForExplorer();
			if (!dartDb) throw new Error(dbError ?? '브라우저가 데이터 엔진을 지원하지 않습니다');
			usNodes = await loadEdgarNodes(dartDb);
			usState = 'ready';
		} catch (err) {
			usState = 'error';
			usError = err instanceof Error ? err.message : String(err);
			usNodes = [];
		}
	}

	function setMarketScope(next: MarketScope) {
		marketScope = next;
		if (next !== 'KR') void ensureUsNodes();
		// 통화 단위 컬럼으로 정렬 중이었다면 전체 보기에서 그 정렬은 정직하지 않다. 해제한다.
		if (next === 'ALL') sorts = sorts.filter((s) => sortAllowed(METRICS_BY_KEY[s.key], 'ALL'));
		// 산업칩은 KR taxonomy 라 시장이 바뀌면 의미를 잃는다.
		selectedIndustries = new Set();
	}

	// ── Data badge · keep infrastructure names out of the user-facing UI ─
	let dbBadgeKind = $derived.by(() => {
		if (runtimeState === 'error') return 'error';
		if (runtimeState === 'loading') return 'loading';
		if (dbState === 'unsupported') return 'unsupported';
		if (dbState === 'error') return 'error';
		if (dbState === 'loading') return 'phase';
		return 'ready';
	});
	let dbBadgeText = $derived.by(() => {
		if (dbBadgeKind === 'unsupported') return '데이터 활성';
		if (dbBadgeKind === 'error') return runtimeError ?? dbError ?? '데이터 로드 실패';
		if (runtimeState === 'loading') return '데이터 로드 중';
		if (dbState === 'loading') return '데이터 준비 중';
		if (trendState === 'loading') return '데이터 계산 중';
		return '데이터 활성';
	});

	// ── Merge ecosystem with parquet maps ─────────────
	let krNodes = $derived.by(() => {
		if (
			priceMap.size === 0 &&
			valuationMap.size === 0 &&
			changesMap.size === 0 &&
			financeMap.size === 0 &&
			productMap.size === 0
		) {
			return baseNodes;
		}
		return baseNodes.map((n) => {
			const p = priceMap.get(n.id);
			const val = valuationMap.get(n.id);
			const chg = changesMap.get(n.id);
			const fin = financeMap.get(n.id);
			const prod = productMap.get(n.id);
			return {
				...n,
				...fin,
				product: prod?.product ?? (n.product as string | null | undefined) ?? null,
				productRaw: prod?.productRaw ?? (n.productRaw as string | null | undefined) ?? null,
				productPeriod: prod?.latestPeriod ?? (n.productPeriod as string | null | undefined) ?? null,
				// price (KRX)
				currentPrice: p?.currentPrice ?? (n.currentPrice as number | null | undefined) ?? null,
				return1m: p?.return1m ?? (n.return1m as number | null | undefined) ?? null,
				return3m: p?.return3m ?? (n.return3m as number | null | undefined) ?? null,
				return1y: p?.return1y ?? (n.return1y as number | null | undefined) ?? null,
				volatility1y: p?.volatility1y ?? (n.volatility1y as number | null | undefined) ?? null,
				week52High: p?.week52High ?? (n.week52High as number | null | undefined) ?? null,
				week52Low: p?.week52Low ?? (n.week52Low as number | null | undefined) ?? null,
				volumeAvg30d: p?.volumeAvg30d ?? (n.volumeAvg30d as number | null | undefined) ?? null,
				spark30: p?.spark30 ?? (n.spark30 as number[] | undefined) ?? [],
				spark60: p?.spark60 ?? (n.spark60 as number[] | undefined) ?? [],
				spark: p?.spark ?? (n.spark as number[] | undefined) ?? [],
				// valuation (Naver) · marketCap 우선 valuation, fallback KRX
				marketCap: val?.marketCap ?? p?.marketCap ?? (n.marketCap as number | null | undefined) ?? null,
				per: val?.per ?? (n.per as number | null | undefined) ?? null,
				pbr: val?.pbr ?? (n.pbr as number | null | undefined) ?? null,
				dividendYield: val?.dividendYield ?? (n.dividendYield as number | null | undefined) ?? null,
				// changes
				numericChanges1y: chg?.numericChanges1y ?? null,
				structuralChanges1y: chg?.structuralChanges1y ?? null,
				totalChanges1y: chg?.totalChanges1y ?? null,
				recentChangeYear: chg?.recentChangeYear ?? null
			} as ScanNode;
		});
	});

	// KR 노드에 parquet 런타임 맵을 병합한 뒤 US 노드를 덧댄다. US 는 자체 로더가 완성형이라
	// KR 전용 맵을 끼우지 않는다 (없는 개념을 결측처럼 보이게 만들기 때문).
	let allNodes = $derived(usNodes.length > 0 ? [...krNodes, ...usNodes] : krNodes);
	/** 조회 시장 범위만 적용한 노드. 분포·발굴 피드·프리셋의 모집단. */
	let marketNodes = $derived(marketScope === 'KR' ? krNodes : allNodes.filter((n) => inScope(n, marketScope)));

	// ── Percentiles (활성 컬럼별 p10/p90) · 셀 분위 색상용 ─
	// 시장별로 따로 뽑는다. KR 분포로 US 셀을 칠하면 히트맵이 통화 스케일차와 회계기준 차이를
	// "좋음/나쁨" 색으로 위조한다. Grid 가 행의 시장에 맞는 분포를 골라 쓴다.
	let percentilesByMkt = $derived(percentilesByMarket(allNodes, activeColumns, METRICS_BY_KEY));

	// ── Filter / sort ──────────────────────────────────
	// 조건 판정은 verdict.ts SSOT 로 이관했다. 옛 로컬 evalCond 는 결측을 비대칭 처리했고
	// (null 이 >= 에선 FAIL, != 에선 PASS) ==/!= 만 억원 스케일을 우회했다.
	function comparableValue(value: unknown): unknown {
		return value;
	}

	/** 시장 범위 + 검색어 + 산업칩을 적용한 유니버스. 조건(conds)은 판정격자가 맡는다. */
	let scopedNodes = $derived.by(() => {
		const q = searchQuery.trim().toLowerCase();
		return allNodes.filter((node) => {
			if (!inScope(node, marketScope)) return false;
			if (selectedIndustries.size > 0 && !selectedIndustries.has(node.industry as string)) {
				return false;
			}
			if (q) {
				const lblOk = node.label.toLowerCase().includes(q);
				const codeOk = node.id.includes(q);
				const indOk = (node.industryName as string)?.toLowerCase().includes(q);
				const productOk = String((node as Record<string, unknown>).product ?? '').toLowerCase().includes(q);
				if (!lblOk && !codeOk && !indOk && !productOk) return false;
			}
			return true;
		});
	});

	/** 조건 x 종목 판정격자. members / nearMiss / funnel / 결측이 전부 여기서 나온다. */
	let grid = $derived(buildVerdictGrid(scopedNodes, conds, METRICS_BY_KEY));

	/** 결측 포함 보기 = UNKNOWN 을 탈락시키지 않고 남긴다 (fail 이 하나도 없으면 통과 취급). */
	let includeUnknown = $state(false);
	/** 근접후보 보기 = 조건 하나만 놓친 종목을 members 뒤에 amber 로 붙인다. */
	let showNearMiss = $state(false);

	let nearMissRows = $derived(nearMiss(grid, 1));
	let nearMissIds = $derived(new Set(showNearMiss ? nearMissRows.map((r) => r.node.id) : []));

	let filteredNodes = $derived.by(() =>
		includeUnknown ? grid.rows.filter((r) => r.failCount === 0).map((r) => r.node) : grid.members
	);

	/** 리본의 완화 칩. 조건 임계를 역산값으로 갈아끼운다. */
	function applyRelax(condIndex: number, value: number) {
		conds = conds.map((c, i) => (i === condIndex ? { ...c, value } : c));
	}

	let selectedNode = $derived(selectedRow ? (allNodes.find((n) => n.id === selectedRow) ?? null) : null);

	/** InsightsFeed 카드 적용. 두 벌로 복사돼 있던 핸들러를 한 곳으로. */
	function applyInsight(p: { conds: FilterCond[]; sort: SortKey; cols?: string[] }) {
		conds = p.conds;
		sorts = [p.sort];
		if (p.cols) {
			const next = new Set(activeColumns);
			for (const c of p.cols) next.add(c);
			activeColumns = Array.from(next);
			void ensureLoaders(inferLoaders(p.cols));
		}
		selectedIndustries = new Set();
		activePresetId = null;
	}

	function sortNodes(list: ScanNode[]): ScanNode[] {
		if (sorts.length === 0) return list;
		return list.sort((a, b) => {
			for (const s of sorts) {
				const key = s.key;
				const dir = s.dir === 'asc' ? 1 : -1;
				const va = (a as any)[key];
				const vb = (b as any)[key];
				const ca = comparableValue(va);
				const cb = comparableValue(vb);
				if (ca == null && cb == null) continue;
				if (ca == null) return 1;
				if (cb == null) return -1;
				let cmp = 0;
				if (typeof ca === 'number' && typeof cb === 'number') cmp = ca - cb;
				else cmp = String(ca).localeCompare(String(cb), 'ko-KR', { numeric: true });
				if (cmp !== 0) return cmp * dir;
			}
			return String(a.label).localeCompare(String(b.label), 'ko-KR');
		});
	}

	// 근접후보는 통과 종목 뒤에 격리해 붙인다. 랭킹 안으로 섞으면 "통과했다" 는 거짓말이 된다.
	let sortedNodes = $derived.by(() => {
		const list = sortNodes(filteredNodes.slice());
		if (!showNearMiss || nearMissRows.length === 0) return list;
		return [...list, ...sortNodes(nearMissRows.map((r) => r.node))];
	});

	let filterOptions = $derived.by(() => {
		const map: Record<string, string[]> = {};
		for (const key of activeColumns) {
			const def = METRICS_BY_KEY[key];
			if (!def || def.type !== 'enum') continue;
			const values = new Set<string>();
			for (const node of allNodes) {
				const value = (node as Record<string, unknown>)[key];
				if (value != null && String(value).trim()) values.add(String(value));
			}
			map[key] = Array.from(values).sort((a, b) => a.localeCompare(b, 'ko-KR'));
		}
		return map;
	});

	// ── Industry chip bar ──────────────────────────────
	function toggleIndustry(id: string) {
		const next = new Set(selectedIndustries);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		selectedIndustries = next;
	}

	function clearFilters() {
		conds = [];
		selectedIndustries = new Set();
		searchQuery = '';
		activePresetId = null;
	}

	// ── Preset ─────────────────────────────────────────
	function applyPreset(p: Preset) {
		conds = [...p.conds];
		if (p.sorts.length > 0) sorts = p.sorts.slice();
		if (p.cols && p.cols.length > 0) {
			const next = new Set(activeColumns);
			for (const c of p.cols) next.add(c);
			activeColumns = Array.from(next);
		}
		void ensureLoaders(p.loaders ?? inferLoaders(p.cols ?? []));
		activePresetId = p.id;
		selectedIndustries = new Set();
	}

	function inferLoaders(cols: string[]): RuntimeLoader[] {
		const loaders = new Set<RuntimeLoader>();
		for (const col of cols) {
			const source = METRICS_BY_KEY[col]?.source;
			if (source === 'finance5y') loaders.add('finance5y');
			if (source === 'prices' || source === 'priceTrend') loaders.add('priceTrend');
			if (source === 'valuation') loaders.add('valuation');
			if (source === 'changes' || source === 'report') loaders.add('report');
		}
		return Array.from(loaders);
	}

	function loaderForGroup(group: MetricGroup): RuntimeLoader | null {
		if (
			group === 'financeIncome' ||
			group === 'financeBalance' ||
			group === 'financeCashflow' ||
			group === 'financeRatio' ||
			group === 'financeGrowth'
		) {
			return 'finance5y';
		}
		if (group === 'price') return 'priceTrend';
		if (group === 'valuation') return 'valuation';
		if (group === 'changes' || group === 'disclosure') return 'report';
		return null;
	}

	function markColumnGroupPending(group: MetricGroup, pending: boolean) {
		const next = new Set(pendingColumnGroups);
		if (pending) next.add(group);
		else next.delete(group);
		pendingColumnGroups = next;
	}

	function clearPendingGroupsForLoader(loader: RuntimeLoader) {
		const next = new Set([...pendingColumnGroups].filter((group) => loaderForGroup(group) !== loader));
		pendingColumnGroups = next;
	}

	function markLoaderLoading(loader: RuntimeLoader, loading: boolean) {
		const next = new Set(loaderLoading);
		if (loading) next.add(loader);
		else next.delete(loader);
		loaderLoading = next;
	}

	function markLoaderReady(loader: RuntimeLoader) {
		const ready = new Set(loaderReady);
		ready.add(loader);
		loaderReady = ready;
		markLoaderLoading(loader, false);
		clearPendingGroupsForLoader(loader);
	}

	function markLoaderError(loader: RuntimeLoader, error: string) {
		const errors = new Map(loaderError);
		errors.set(loader, error);
		loaderError = errors;
		markLoaderLoading(loader, false);
		clearPendingGroupsForLoader(loader);
	}

	async function ensureLoaders(loaders: RuntimeLoader[]) {
		for (const loader of loaders) {
			if (loaderReady.has(loader) || loaderLoading.has(loader)) continue;
			if (loader === 'valuation') {
				void bootValuationRuntime();
			} else if (loader === 'priceTrend') {
				void bootPriceMetrics();
			} else if (loader === 'finance5y') {
				void bootFinance5yRuntime();
			} else if (loader === 'report') {
				void bootReportRuntime();
			}
		}
	}

	// ── onMount: URL ?q= 우선, ?preset= fallback, then DuckDB ─
	onMount(() => {
		const url = new URL(page.url);
		if (url.searchParams.get('explore') === '1') openDataExplorer();
		const q = url.searchParams.get('q');
		const presetId = url.searchParams.get('preset');
		if (q) {
			const payload = decodeScanPayload(q);
			if (payload) {
				// 시장부터. US/ALL 이면 EDGAR 노드를 먼저 요청해야 조건이 그 위에서 평가된다.
				if (payload.m && payload.m !== 'KR') setMarketScope(payload.m);
				selectedIndustries = new Set(payload.i);
				conds = payload.c;
				if (payload.s.length > 0) {
					// 전체 보기에서 통화 단위 정렬은 정직하지 않다. 옛 링크가 그런 정렬을 실어와도 버린다.
					sorts = payload.s.filter((s) => sortAllowed(METRICS_BY_KEY[s.key], marketScope));
				}
				if (payload.cols.length > 0) {
					// PINNED 항상 보존 + payload cols
					const pinned = PINNED_COLUMNS;
					const rest = payload.cols.filter((k) => !pinned.includes(k));
					activeColumns = [...pinned, ...rest];
					void ensureLoaders(inferLoaders(activeColumns));
				}
				if (payload.p) activePresetId = payload.p;
				if (payload.sel) selectedRow = payload.sel;
			}
		} else if (presetId) {
			const preset = PRESETS_BY_ID.get(presetId);
			if (preset) applyPreset(preset);
		}
		void bootRuntime();
		void bootProductIndexRuntime();
		void ensureLoaders(inferLoaders(activeColumns));
		return () => {
			runtimeWorker?.terminate();
			runtimeWorker = null;
			priceWorker?.terminate();
			priceWorker = null;
			changesWorker?.terminate();
			changesWorker = null;
		};
	});

	$effect(() => {
		if (selectedRow && !DetailComponent) void loadDetailComponent();
		if (selectedRow) void ensureLoaders(['finance5y']);
	});

	// ── URL share encode (현재 상태 → ?q=) ────────────
	let shareUrl = $derived.by(() => {
		const payload = {
			v: 2 as const,
			i: Array.from(selectedIndustries),
			c: conds,
			s: sorts,
			cols: activeColumns,
			p: activePresetId ?? undefined,
			sel: selectedRow ?? undefined,
			// KR 은 기본값이라 URL 에 싣지 않는다 (옛 링크와 바이트 동일하게 유지).
			m: marketScope === 'KR' ? undefined : marketScope
		};
		const q = encodeScanPayload(payload);
		if (typeof window === 'undefined') return '';
		const url = new URL(window.location.href);
		url.searchParams.set('q', q);
		url.searchParams.delete('preset');
		return url.toString();
	});

	function loadSavedSet(s: SavedColumnSet) {
		const pinned = PINNED_COLUMNS;
		const rest = s.cols.filter((k) => !pinned.includes(k));
		activeColumns = [...pinned, ...rest];
		conds = s.conds.slice();
		if (s.sort.length > 0) sorts = s.sort.slice();
		activePresetId = null;
		void ensureLoaders(inferLoaders(activeColumns));
	}

	async function bootRuntime() {
		runtimeState = 'loading';
		runtimeError = null;
		if (typeof Worker !== 'undefined') {
			try {
				bootRuntimeWorker();
				return;
			} catch {
				runtimeWorker?.terminate();
				runtimeWorker = null;
			}
		}
		await bootRuntimeFallback();
	}

	async function bootRuntimeFallback() {
		runtimeState = 'loading';
		runtimeError = null;
		try {
			const ecosystem = await loadJson<any>('map/ecosystem.json', {
				fetchFn: fetch,
				required: true,
				preferLocal: true
			});
			hfNodes = (ecosystem?.nodes ?? []) as ScanNode[];
			runtimeState = 'ready';
			void bootRuntimeSidecars();
		} catch (err) {
			runtimeError = err instanceof Error ? err.message : String(err);
			runtimeState = 'error';
		}
	}

	function bootRuntimeWorker() {
		runtimeWorker?.terminate();
		runtimeWorker = new Worker(new URL('../../lib/scan/scanRuntime.worker.ts', import.meta.url), {
			type: 'module'
		});
		runtimeWorker.onmessage = (event: MessageEvent<any>) => {
			const msg = event.data;
			if (msg.type === 'ecosystem') {
				hfNodes = msg.nodes ?? [];
				runtimeIndustries = msg.industries ?? [];
				runtimeState = 'ready';
				return;
			}
			if (msg.type === 'sidecars') {
				hfNodes = msg.nodes ?? hfNodes;
				runtimeIndustries = msg.industries ?? runtimeIndustries;
				runtimeMeta = msg.meta ?? runtimeMeta;
				window.setTimeout(() => {
					if (!loaderReady.has('valuation') && !loaderLoading.has('valuation')) void bootValuationRuntime();
				}, 0);
				return;
			}
			if (msg.type === 'finance5y') {
				financeMap = financeRowsToMap(msg.rows ?? []);
				markLoaderReady('finance5y');
				return;
			}
			if (msg.type === 'finance5y-error') {
				markLoaderError('finance5y', msg.error ?? '재무 5Y 로드 실패');
				return;
			}
			if (msg.type === 'error') {
				runtimeError = msg.error ?? '데이터 로드 실패';
				runtimeState = 'error';
				if (hfNodes.length === 0) void bootRuntimeFallback();
			}
		};
		runtimeWorker.onerror = () => {
			runtimeError = 'scan worker 로드 실패';
			runtimeState = 'error';
			runtimeWorker?.terminate();
			runtimeWorker = null;
			void bootRuntimeFallback();
		};
		runtimeWorker.postMessage({ type: 'boot', basePath: base, hfResolve: HF_RESOLVE });
	}

	async function bootRuntimeSidecars() {
		const [prices, meta] = await Promise.all([
			// 시세 스냅샷만 HF-first · 일배치 HF 갱신을 정적 사본이 가리는 동결 방지 (terminal routeLoad 동일)
			loadJson<PriceSnapshotFile>('map/prices-snapshot.json', { fetchFn: fetch }),
			loadJson<any>('map/meta.json', { fetchFn: fetch, preferLocal: true })
		]);
		hfNodes = mergePriceSnapshot(hfNodes, prices);
		runtimeMeta = meta ?? runtimeMeta;
		window.setTimeout(() => {
			if (!loaderReady.has('valuation') && !loaderLoading.has('valuation')) void bootValuationRuntime();
		}, 0);
	}

	function bootValuationRuntime() {
		if (valuationStarted || loaderReady.has('valuation') || loaderLoading.has('valuation')) return;
		valuationStarted = true;
		markLoaderLoading('valuation', true);
		window.setTimeout(() => {
			void import('$lib/data/valuationRuntime')
				.then(({ loadHfValuationMap }) => loadHfValuationMap(fetch))
				.then((valuations) => {
					hfNodes = mergeValuationRuntime(hfNodes, valuations);
					valuationMap = valuationRuntimeToScanMap(valuations);
					markLoaderReady('valuation');
				})
				.catch((err) => {
					valuationStarted = false;
					markLoaderError('valuation', err instanceof Error ? err.message : String(err));
				});
		}, 0);
	}

	function openDataExplorer() {
		dataExplorerOpen = true;
		void loadDataExplorerComponent();
		void bootDuckDbForExplorer();
	}

	async function loadDetailComponent() {
		DetailComponent = (await import('@dartlab/ui-surfaces/scan')).Detail;
	}

	async function loadDataExplorerComponent() {
		DataExplorerComponent = (await import('@dartlab/ui-surfaces/scan')).DataExplorer;
	}

	function openUniverse() {
		universeOpen = true;
		void loadUniverseComponent();
		void bootDuckDbForExplorer(); // 유니버스 패널도 DuckDB-wasm 으로 로드(ensureDuckDb)
	}
	async function loadUniverseComponent() {
		UniverseBacktesterComponent = (await import('@dartlab/ui-surfaces/scan')).UniverseBacktester;
	}

	async function bootDuckDbForExplorer() {
		if (dbBootStarted || dartDb) return;
		dbBootStarted = true;
		dbState = 'loading';
		const { ensureDuckDb } = await import('@dartlab/ui-surfaces/scan');
		const ensure = await ensureDuckDb();
		if (ensure.error) dbError = ensure.error;
		dbState = ensure.state;
		if (ensure.db) dartDb = ensure.db;
	}

	async function bootPriceMetrics() {
		if (priceMetricsStarted || trendState === 'loading') return;
		priceMetricsStarted = true;
		markLoaderLoading('priceTrend', true);
		trendState = 'loading';
		trendError = null;
		if (typeof Worker === 'undefined') {
			await bootPriceMetricsFallback();
			return;
		}
		priceWorker?.terminate();
		priceWorker = new Worker(new URL('../../lib/data/priceRuntime.worker.ts', import.meta.url), {
			type: 'module'
		});
		priceWorker.onmessage = (event: MessageEvent<any>) => {
			const msg = event.data;
			if (msg.type === 'priceTrend') {
				const metrics = priceRecordToMap(msg.metrics ?? {});
				if (metrics.size === 0) return;
				priceMap = mergePriceMaps(priceMap, metrics);
				trendState = 'ready';
				markLoaderReady('priceTrend');
				if (msg.partial) {
					scheduleOneYearPriceTrend();
				} else {
					priceWorker?.terminate();
					priceWorker = null;
				}
				return;
			}
			if (msg.type === 'priceTrend-error') {
				trendState = 'error';
				const error = msg.error ?? '추세 데이터 로드 실패';
				trendError = error;
				priceMetricsStarted = false;
				markLoaderError('priceTrend', error);
				priceWorker?.terminate();
				priceWorker = null;
			}
		};
		priceWorker.onerror = () => {
			trendState = 'error';
			trendError = '주가 런타임 worker 로드 실패';
			priceMetricsStarted = false;
			markLoaderError('priceTrend', trendError);
			priceWorker?.terminate();
			priceWorker = null;
		};
		priceWorker.postMessage({ type: 'priceTrend', currentTailRows: 140_000, previousTailRows: 420_000 });
	}

	function scheduleOneYearPriceTrend() {
		if (priceOneYearScheduled) return;
		priceOneYearScheduled = true;
		const run = () => priceWorker?.postMessage({ type: 'priceTrend1y' });
		if ('requestIdleCallback' in window) {
			(window as any).requestIdleCallback(run, { timeout: 2500 });
		} else {
			setTimeout(run, 1800);
		}
	}

	async function bootPriceMetricsFallback() {
		try {
			const { loadCurrentPriceTail, loadOneYearPriceTail } = await import('$lib/data/priceRuntime');
			const current = await loadCurrentPriceTail({ currentTailRows: 140_000 });
			priceMap = mergePriceMaps(priceMap, priceRecordToMap(current.metrics));
			trendState = 'ready';
			markLoaderReady('priceTrend');
			window.setTimeout(() => {
				void loadOneYearPriceTail(current.rows, { previousTailRows: 420_000 }).then((oneYear) => {
					priceMap = mergePriceMaps(priceMap, priceRecordToMap(oneYear.metrics));
				});
			}, 1800);
		} catch (err) {
			trendState = 'error';
			trendError = err instanceof Error ? err.message : String(err);
			priceMetricsStarted = false;
			markLoaderError('priceTrend', trendError);
		}
	}

	async function bootFinance5yRuntime() {
		if (loaderReady.has('finance5y') || loaderLoading.has('finance5y')) return;
		markLoaderLoading('finance5y', true);
		if (runtimeWorker) {
			runtimeWorker.postMessage({ type: 'finance5y' });
			return;
		}
		try {
			const { loadFinanceLiteRuntime } = await import('@dartlab/ui-surfaces/scan');
			const result = await loadFinanceLiteRuntime(fetch);
			financeMap = financeRowsToMap(result.rows);
			markLoaderReady('finance5y');
		} catch (err) {
			markLoaderError('finance5y', err instanceof Error ? err.message : String(err));
		}
	}

	async function bootReportRuntime() {
		if (loaderReady.has('report') || loaderLoading.has('report')) return;
		markLoaderLoading('report', true);
		if (typeof Worker === 'undefined') {
			await bootReportRuntimeFallback();
			return;
		}
		changesWorker?.terminate();
		changesWorker = new Worker(new URL('../../lib/data/changesRuntime.worker.ts', import.meta.url), {
			type: 'module'
		});
		changesWorker.onmessage = (event: MessageEvent<any>) => {
			const msg = event.data;
			if (msg.type === 'changes') {
				changesMap = changeRecordToMap(msg.metrics ?? {});
				markLoaderReady('report');
				window.setTimeout(() => {
					changesWorker?.terminate();
					changesWorker = null;
				}, 1000);
				return;
			}
			if (msg.type === 'changes-error') {
				markLoaderError('report', msg.error ?? 'Report 데이터 로드 실패');
				changesWorker?.terminate();
				changesWorker = null;
			}
		};
		changesWorker.onerror = () => {
			markLoaderError('report', 'Report 런타임 worker 로드 실패');
			changesWorker?.terminate();
			changesWorker = null;
		};
		changesWorker.postMessage({ type: 'changes' });
	}

	async function bootReportRuntimeFallback() {
		try {
			const { loadHfChangesMap } = await import('$lib/data/changesRuntime');
			const result = await loadHfChangesMap({ fetchFn: fetch });
			changesMap = changeRecordToMap(result.metrics);
			markLoaderReady('report');
		} catch (err) {
			markLoaderError('report', err instanceof Error ? err.message : String(err));
		}
	}

	async function bootProductIndexRuntime() {
		try {
			const { getPublicRuntime } = await import('$lib/runtime/publicRuntime');
			const rec = await getPublicRuntime().company.productIndex();
			productMap = new Map(Object.entries(rec ?? {}));
		} catch {
			productMap = new Map();
		}
	}

	interface PriceSnapshotFile {
		builtAt?: string;
		data?: Record<string, PriceSnapshotItem>;
	}

	interface PriceSnapshotItem {
		currentPrice?: number | null;
		marketCap?: number | null;
		return1m?: number | null;
		return3m?: number | null;
		return1y?: number | null;
		volatility1y?: number | null;
		week52High?: number | null;
		week52Low?: number | null;
		volumeAvg30d?: number | null;
		foreignPct?: number | null;
		beta?: number | null;
		priceUpdated?: string | null;
	}

	function financeRowsToMap(rows: Array<Record<string, unknown> & { id?: string }>): Map<string, Partial<ScanNode>> {
		const map = new Map<string, Partial<ScanNode>>();
		for (const row of rows) {
			const id = String(row.id ?? '').trim();
			if (!id) continue;
			const { id: _id, ...rest } = row;
			map.set(id, rest as Partial<ScanNode>);
		}
		return map;
	}

	function mergePriceSnapshot(nodes: ScanNode[], snapshot: PriceSnapshotFile | null): ScanNode[] {
		const prices = snapshot?.data ?? {};
		if (Object.keys(prices).length === 0) return nodes;
		return nodes.map((node) => {
			const p = prices[node.id];
			if (!p) return node;
			return {
				...node,
				currentPrice: numberOrNull(p.currentPrice),
				marketCap: numberOrNull(p.marketCap) ?? node.marketCap ?? null,
				return1m: numberOrNull(p.return1m),
				return3m: numberOrNull(p.return3m),
				return1y: numberOrNull(p.return1y),
				volatility1y: numberOrNull(p.volatility1y),
				week52High: numberOrNull(p.week52High),
				week52Low: numberOrNull(p.week52Low),
				volumeAvg30d: numberOrNull(p.volumeAvg30d),
				foreignPct: numberOrNull(p.foreignPct),
				beta: numberOrNull(p.beta)
			} as ScanNode;
		});
	}

	function mergeValuationRuntime(
		nodes: ScanNode[],
		values: Map<string, ValuationRuntimeMetrics>
	): ScanNode[] {
		if (values.size === 0) return nodes;
		return nodes.map((node) => {
			const v = values.get(node.id);
			if (!v) return node;
			return {
				...node,
				currentPrice: node.currentPrice ?? v.currentPrice ?? null,
				marketCap: v.marketCap ?? node.marketCap ?? null,
				per: v.per,
				pbr: v.pbr,
				dividendYield: v.dividendYield
			} as ScanNode;
		});
	}

	function priceNodesToMap(nodes: ScanNode[]): Map<string, PriceMetrics> {
		const map = new Map<string, PriceMetrics>();
		for (const node of nodes) {
			if (
				node.currentPrice == null &&
				node.marketCap == null &&
				node.return1y == null &&
				node.volumeAvg30d == null
			) {
				continue;
			}
			map.set(node.id, {
				currentPrice: numberOrNull(node.currentPrice),
				marketCap: numberOrNull(node.marketCap),
				ma20: null,
				high60: null,
				low60: null,
				week52High: numberOrNull(node.week52High),
				week52Low: numberOrNull(node.week52Low),
				volumeAvg30d: numberOrNull(node.volumeAvg30d),
				volatility1y: numberOrNull(node.volatility1y),
				return1m: numberOrNull(node.return1m),
				return3m: numberOrNull(node.return3m),
				return1y: numberOrNull(node.return1y),
				spark30: Array.isArray(node.spark30) ? (node.spark30 as number[]) : [],
				spark60: Array.isArray(node.spark60) ? (node.spark60 as number[]) : [],
				spark: Array.isArray(node.spark) ? (node.spark as number[]) : []
			});
		}
		return map;
	}

	function mergePriceMaps(
		base: Map<string, PriceMetrics>,
		next: Map<string, PriceMetrics>
	): Map<string, PriceMetrics> {
		const merged = new Map(base);
		for (const [stockCode, metrics] of next.entries()) {
			const prev = merged.get(stockCode);
			merged.set(stockCode, prev ? { ...prev, ...metrics } : metrics);
		}
		return merged;
	}

	function priceRecordToMap(record: Record<string, PriceMetrics>): Map<string, PriceMetrics> {
		const map = new Map<string, PriceMetrics>();
		for (const [stockCode, metrics] of Object.entries(record)) {
			map.set(stockCode, metrics);
		}
		return map;
	}

	function changeRecordToMap(record: Record<string, ChangeMetrics>): Map<string, ChangeMetrics> {
		const map = new Map<string, ChangeMetrics>();
		for (const [stockCode, metrics] of Object.entries(record)) {
			map.set(stockCode, metrics);
		}
		return map;
	}

	function valuationRuntimeToScanMap(
		values: Map<string, ValuationRuntimeMetrics>
	): Map<string, ValuationMetrics> {
		const map = new Map<string, ValuationMetrics>();
		for (const [stockCode, v] of values.entries()) {
			map.set(stockCode, {
				per: v.per,
				pbr: v.pbr,
				dividendYield: v.dividendYield,
				marketCap: v.marketCap
			});
		}
		return map;
	}

	function numberOrNull(value: unknown): number | null {
		if (typeof value === 'number') return Number.isFinite(value) ? value : null;
		if (typeof value === 'bigint') {
			const n = Number(value);
			return Number.isFinite(n) ? n : null;
		}
		if (typeof value === 'string' && value.trim()) {
			const n = Number(value.replace(/,/g, ''));
			return Number.isFinite(n) ? n : null;
		}
		return null;
	}

	// ── Column toggle ─────────────────────────────────
	function handleColumnsChange(next: string[], group?: MetricGroup) {
		// PINNED 는 항상 맨 앞 + 보존
		const pinned = activeColumns.filter((k) => PINNED_COLUMNS.includes(k));
		const rest = next.filter((k) => !PINNED_COLUMNS.includes(k));
		const before = new Set(activeColumns);
		activeColumns = [...pinned, ...rest];
		const added = activeColumns.filter((k) => !before.has(k));
		const loaders = inferLoaders(added.length > 0 ? added : activeColumns);
		if (group) {
			const loader = loaderForGroup(group);
			markColumnGroupPending(group, Boolean(added.length > 0 && loader && loaders.includes(loader) && !loaderReady.has(loader)));
		}
		void ensureLoaders(loaders);
	}

	// ── Sort handler ──────────────────────────────────
	function handleSort(s: SortKey, append: boolean) {
		if (!append) {
			sorts = [s];
			return;
		}
		const idx = sorts.findIndex((item) => item.key === s.key);
		if (idx >= 0) {
			const next = sorts.slice();
			next[idx] = s;
			sorts = next;
		} else {
			sorts = [...sorts, s];
		}
	}

	function setColumnFilters(metric: string, nextConds: FilterCond[]) {
		conds = [...conds.filter((c) => c.metric !== metric), ...nextConds];
		activePresetId = null;
	}

	function applyScreen(payload: { conds: FilterCond[]; sorts: SortKey[]; cols: string[] }) {
		const nextCols = Array.from(new Set([...PINNED_COLUMNS, ...DEFAULT_COLUMNS, ...payload.cols]));
		activeColumns = nextCols;
		conds = payload.conds;
		if (payload.sorts.length > 0) sorts = payload.sorts;
		selectedIndustries = new Set();
		searchQuery = '';
		selectedRow = null;
		activePresetId = null;
		dataExplorerOpen = false;
		const loaderKeys = [
			...nextCols,
			...payload.conds.map((cond) => cond.metric),
			...payload.sorts.map((item) => item.key)
		];
		void ensureLoaders(inferLoaders(loaderKeys));
	}

	function removeCond(index: number) {
		conds = conds.filter((_, i) => i !== index);
		activePresetId = null;
	}

	function handleSelect(id: string) {
		selectedRow = selectedRow === id ? null : id;
	}

	function handleCellHover(info: typeof cellHover) {
		cellHover = info;
	}

	// ── Industry list (display order: 회사 수 내림) ────
	let industryDisplay = $derived(
		industries
			.map((i) => ({ id: i.id, name: i.name, color: i.color, count: i.count }))
			.sort((a, b) => b.count - a.count)
	);
</script>

<svelte:head>
	<title>Scan Studio | 전자공시 dartlab</title>
	<meta
		name="description"
		content="dartlab 의 회사를 한 화면 그리드로. 매출·영업이익률·ROE·부채·등급 + 브라우저 SQL 로 데이터 직접 조회."
	/>
</svelte:head>

<Header context="landing" />

<main class="scan-page">
	<!-- Page header strip -->
	<header class="page-head">
		<div class="page-head-left">
			<h1 class="page-title">Scan Studio</h1>
			<div class="market-switch" role="group" aria-label="조회 시장">
				{#each ['KR', 'US', 'ALL'] as const as scope (scope)}
					<button
						type="button"
						class="ms-btn"
						class:active={marketScope === scope}
						onclick={() => setMarketScope(scope)}
					>
						{MARKET_LABEL[scope]}
						{#if scope !== 'KR' && usState === 'loading'}
							<span class="ms-dot" aria-label="불러오는 중"></span>
						{/if}
					</button>
				{/each}
			</div>
			{#if usState === 'error' && marketScope !== 'KR'}
				<span class="ms-error">{usError}</span>
			{/if}
		</div>
		<div class="page-head-right">
			<button type="button" class="explore-btn" onclick={openDataExplorer}>
				<SlidersHorizontal size={14} />
				<span>데이터 탐색</span>
			</button>
			<button type="button" class="explore-btn" onclick={openUniverse} title="전종목 크로스섹셔널 백테스트 (17년 가격보존)">
				<span>유니버스 백테스트 ▸</span>
			</button>
			<span class="db-badge db-{dbBadgeKind}" title={dbError ?? trendError ?? ''}>
				<span class="db-dot"></span> {dbBadgeText}
			</span>
			<input
				type="text"
				bind:value={searchQuery}
				placeholder="회사명 / 종목코드 / 산업"
				class="search-input"
				aria-label="검색"
			/>
			<button type="button" class="cmdk-btn" onclick={() => (presetOpen = true)} aria-label="프리셋 모달 열기">
				<span>⌘K</span>
				<span class="cmdk-lbl">프리셋</span>
			</button>
			<SavedSets cols={activeColumns} {conds} {sorts} {shareUrl} onLoad={loadSavedSet} />
			{#if runtimeMeta?.dataAsOf}
				<FreshnessBadge dataAsOf={runtimeMeta.dataAsOf} variant="compact" />
			{/if}
		</div>
	</header>

	<!-- 산업칩은 KR 34 KSIC taxonomy 다. US(SIC)와 섞을 수 없어 KR 보기에서만 그린다. -->
	<div class="industry-bar" role="group" aria-label="산업 필터" class:hidden={marketScope !== 'KR'}>
		{#if selectedIndustries.size > 0 || conds.length > 0 || searchQuery}
			<button class="clear-btn" type="button" onclick={clearFilters} title="모든 필터 해제">
				✕ 초기화
			</button>
		{/if}
		<div class="industry-chips">
			{#each industryDisplay as ind (ind.id)}
				<button
					type="button"
					class="ind-chip"
					class:active={selectedIndustries.has(ind.id)}
					onclick={() => toggleIndustry(ind.id)}
					title="{ind.name} ({ind.count}사)"
				>
					<span class="ind-chip-dot" style:background={ind.color}></span>
					<span class="ind-chip-name">{ind.name}</span>
					<span class="ind-chip-count">{ind.count}</span>
				</button>
			{/each}
		</div>
	</div>

	<!-- Active preset chip -->
	{#if activePresetId}
		{@const p = PRESETS_BY_ID.get(activePresetId)}
		{#if p}
			<div class="active-preset">
				<span class="ap-label">활성 프리셋</span>
				<span class="ap-title">{p.title}</span>
				<span class="ap-sub">{p.subtitle}</span>
				<button type="button" class="ap-x" onclick={clearFilters} aria-label="프리셋 해제">✕</button>
			</div>
		{/if}
	{/if}

	<VerdictRibbon
		{grid}
		metrics={METRICS_BY_KEY}
		nearMissCount={nearMissRows.length}
		{includeUnknown}
		{showNearMiss}
		relaxFor={(i, target) => relaxThreshold(scopedNodes, conds, i, target, METRICS_BY_KEY)}
		onToggleUnknown={() => (includeUnknown = !includeUnknown)}
		onToggleNearMiss={() => (showNearMiss = !showNearMiss)}
		onRelax={applyRelax}
		onRemoveCond={removeCond}
	/>

	<!-- Column group toggle -->
	<ColumnGroupBar
		activeColumns={activeColumns}
		loadingGroups={loadingColumnGroups}
		onToggle={handleColumnsChange}
	/>

	<!-- Main grid + side panels -->
	<div class="studio" class:full-width={!hasDistribution}>
		<div class="grid-area">
			<Grid
				nodes={sortedNodes}
				columns={activeColumns}
				{sorts}
				filters={conds}
				{filterOptions}
				selectedId={selectedRow}
				markets={data.markets}
				{nearMissIds}
				{marketScope}
				percentilesByMarket={percentilesByMkt}
				onSort={handleSort}
				onFilterChange={setColumnFilters}
				onSelect={handleSelect}
				onCellHover={handleCellHover}
			/>
		</div>
		{#if hasDistribution}
			<aside class="distribution-area" aria-label="분포 패널">
				<Distribution
					nodes={marketNodes}
					filteredNodes={sortedNodes}
					metricKey={sort!.key}
					sortDir={sort!.dir}
					{highlightBin}
					onBinHover={(b) => (highlightBin = b)}
					onCompanyClick={handleSelect}
				/>
			</aside>
		{/if}
	</div>

	<!--
		하단 도크의 정보 위계.
		  행 선택 -> 그 회사의 상세가 가장 중요하다.
		  조건 없음 -> 아직 찾는 중이니 발굴 피드가 출발점이 된다.
		  조건 있음 -> 결과가 주인공이다. 도크를 접어 그 높이를 표에 돌려준다.
	-->
	{#if selectedNode}
		{#if DetailComponent}
			<DetailComponent
				node={selectedNode}
				db={dartDb}
				filing={getPublicRuntime().filing}
				basePath={base}
				financeLoading={loaderLoading.has('finance5y')}
				onClose={() => (selectedRow = null)}
			/>
		{:else}
			<div class="panel-loading">상세 패널 로드 중…</div>
		{/if}
	{:else if conds.length === 0}
		<InsightsFeed nodes={marketNodes} onApply={applyInsight} onCompanyClick={handleSelect} />
	{/if}

	<PresetModal bind:open={presetOpen} nodes={marketNodes} onClose={() => (presetOpen = false)} onApplyPreset={applyPreset} />

	{#if dataExplorerOpen}
		{#if DataExplorerComponent}
			<DataExplorerComponent
				open={dataExplorerOpen}
				onClose={() => (dataExplorerOpen = false)}
				nodes={allNodes}
				ecosystem={baseNodes as Array<Record<string, unknown>>}
				priceMap={priceMap.size > 0 ? priceMap : priceNodesToMap(baseNodes)}
				{valuationMap}
				{changesMap}
				db={dartDb}
				onApplyScreen={applyScreen}
			/>
		{:else}
			<div class="de-loading" role="status">데이터 탐색 로드 중…</div>
		{/if}
	{/if}

	{#if universeOpen}
		<div class="ub-modal" role="presentation" onclick={(e) => { if (e.target === e.currentTarget) universeOpen = false; }}>
			{#if UniverseBacktesterComponent}
				<UniverseBacktesterComponent
					onClose={() => (universeOpen = false)}
					onDrillDown={(code: string) => { window.location.href = `/lab/terminal?symbol=${code}`; }}
				/>
			{:else}
				<div class="de-loading" role="status">유니버스 백테스터 로드 중… (패널 11.9MB)</div>
			{/if}
		</div>
	{/if}

	{#if cellHover}
		<CellTooltip
			stockCode={cellHover.stockCode}
			label={cellHover.label}
			metricKey={cellHover.metricKey}
			formattedValue={cellHover.formattedValue}
			spark={cellHover.spark}
			x={cellHover.x}
			y={cellHover.y}
		/>
	{/if}
</main>

<style>
	.scan-page {
		--scan-bottom-panel-height: clamp(244px, 27vh, 278px);
		--scan-detail-panel-height: clamp(260px, 28vh, 280px);
		max-width: 100%;
		padding: 64px 20px 8px;
		display: flex;
		flex-direction: column;
		gap: 10px;
		height: 100vh;
		overflow: hidden;
	}

	.page-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 16px;
		flex-wrap: wrap;
	}
	.page-head-left {
		display: flex;
		align-items: center;
		gap: 12px;
	}
	.market-switch {
		display: inline-flex;
		border: 1px solid #1e2433;
		border-radius: 5px;
		overflow: hidden;
	}
	.ms-btn {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		height: 28px;
		padding: 0 11px;
		border: 0;
		background: #050811;
		color: #94a3b8;
		font-size: 11px;
		font-family: inherit;
		line-height: 1;
		cursor: pointer;
	}
	.ms-btn + .ms-btn {
		border-left: 1px solid #1e2433;
	}
	.ms-btn:hover {
		color: #cbd5e1;
	}
	.ms-btn.active {
		background: rgba(var(--dl-accent-rgb), 0.1);
		color: var(--dl-accent);
	}
	.ms-dot {
		width: 5px;
		height: 5px;
		border-radius: 50%;
		background: currentColor;
		animation: pulse 1.4s ease-in-out infinite;
	}
	.ms-error {
		font-size: 11px;
		color: #ef4444;
	}
	.industry-bar.hidden {
		display: none;
	}
	.page-title {
		font-size: 18px;
		font-weight: 700;
		color: #f1f5f9;
		letter-spacing: -0.02em;
		margin: 0;
	}
	.page-head-right {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.explore-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 32px;
		padding: 0 12px;
		border: 1px solid rgba(var(--dl-accent-rgb), 0.45);
		border-radius: 5px;
		background: rgba(var(--dl-accent-rgb), 0.08);
		color: var(--dl-accent);
		font-size: 12px;
		font-weight: 600;
		font-family: inherit;
		line-height: 1;
		cursor: pointer;
		white-space: nowrap;
	}
	.explore-btn:hover {
		border-color: rgba(var(--dl-accent-rgb), 0.85);
		background: rgba(var(--dl-accent-rgb), 0.13);
	}
	.search-input {
		width: 260px;
		height: 32px;
		padding: 0 12px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #f1f5f9;
		font-size: 12px;
		font-family: inherit;
		line-height: 1;
	}
	.db-badge {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 32px;
		padding: 0 12px;
		font-size: 11px;
		font-family: monospace;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #94a3b8;
		background: #050811;
		white-space: nowrap;
		line-height: 1;
	}
	.db-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: currentColor;
	}
	.db-idle, .db-loading, .db-phase { color: #fbbf24; }
	.db-loading .db-dot, .db-phase .db-dot {
		animation: pulse 1.4s ease-in-out infinite;
	}
	.db-ready { color: #22c55e; border-color: rgba(34, 197, 94, 0.3); }
	.db-unsupported { color: #94a3b8; }
	.db-error { color: #ef4444; border-color: rgba(239, 68, 68, 0.3); }
	@keyframes pulse {
		0%, 100% { opacity: 0.3; }
		50% { opacity: 1; }
	}
	.search-input:focus {
		outline: none;
		border-color: var(--dl-accent);
	}
	.cmdk-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		height: 32px;
		padding: 0 12px;
		background: #050811;
		border: 1px solid #334155;
		border-radius: 5px;
		color: #cbd5e1;
		font-size: 12px;
		cursor: pointer;
		font-family: inherit;
		line-height: 1;
	}
	.cmdk-btn:hover {
		border-color: var(--dl-accent);
		color: var(--dl-accent);
	}
	.cmdk-btn span:first-child {
		font-family: monospace;
		font-size: 10px;
		padding: 1px 5px;
		background: #1e2433;
		border-radius: 3px;
	}
	.cmdk-lbl {
		font-weight: 500;
	}

	.industry-bar {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 4px 0;
	}
	.clear-btn {
		flex-shrink: 0;
		padding: 4px 10px;
		font-size: 11px;
		color: var(--dl-accent);
		background: rgba(var(--dl-accent-rgb), 0.08);
		border: 1px solid rgba(var(--dl-accent-rgb), 0.3);
		border-radius: 4px;
		cursor: pointer;
		font-family: inherit;
	}
	.industry-chips {
		display: flex;
		gap: 4px;
		overflow-x: auto;
		padding-bottom: 4px;
		scrollbar-width: thin;
	}
	.ind-chip {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		padding: 4px 9px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 4px;
		color: #94a3b8;
		font-size: 11px;
		cursor: pointer;
		flex-shrink: 0;
		font-family: inherit;
	}
	.ind-chip:hover {
		border-color: #334155;
		color: #cbd5e1;
	}
	.ind-chip.active {
		background: rgba(var(--dl-accent-rgb), 0.08);
		border-color: rgba(var(--dl-accent-rgb), 0.5);
		color: #f1f5f9;
	}
	.ind-chip-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.ind-chip-count {
		font-family: monospace;
		font-size: 9px;
		color: #475569;
	}
	.ind-chip.active .ind-chip-count {
		color: var(--dl-accent);
	}

	.active-preset {
		display: inline-flex;
		align-items: baseline;
		gap: 8px;
		padding: 8px 12px;
		background: linear-gradient(135deg, rgba(var(--dl-accent-rgb), 0.1), rgba(var(--dl-accent-rgb), 0.04));
		border: 1px solid rgba(var(--dl-accent-rgb), 0.3);
		border-radius: 5px;
		font-size: 11px;
	}
	.ap-label {
		color: #94a3b8;
		font-size: 10px;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.ap-title {
		color: #f1f5f9;
		font-weight: 600;
		font-size: 12px;
	}
	.ap-sub {
		color: var(--dl-accent);
		font-family: monospace;
	}
	.ap-x {
		margin-left: 8px;
		background: transparent;
		border: none;
		color: #64748b;
		cursor: pointer;
		font-size: 11px;
	}
	.ap-x:hover {
		color: var(--dl-accent);
	}


	.studio {
		flex: 1 1 auto;
		min-height: 0;
		display: grid;
		grid-template-columns: 1fr 320px;
		gap: 10px;
		overflow: hidden;
	}
	/* 분포가 없으면 320px 트랙을 예약하지 않는다. 표가 그 가로폭을 가져간다. */
	.studio.full-width {
		grid-template-columns: 1fr;
		gap: 0;
	}
	.grid-area {
		min-width: 0;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}
	.distribution-area {
		min-width: 0;
		min-height: 0;
		overflow-y: auto;
	}

	.panel-loading {
		flex-shrink: 0;
		padding: 18px;
		background: #0a0e18;
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #64748b;
		font-size: 12px;
		text-align: center;
	}
	.de-loading {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(0, 0, 0, 0.55);
		color: #cbd5e1;
		font-size: 12px;
		z-index: 1000;
	}
	.ub-modal {
		position: fixed;
		inset: 0;
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding: 5vh 16px;
		overflow-y: auto;
		background: rgba(0, 0, 0, 0.55);
		z-index: 1000;
	}

	@media (max-width: 1024px) {
		.studio {
			grid-template-columns: 1fr;
		}
		.distribution-area {
			display: none;
		}
	}
</style>
