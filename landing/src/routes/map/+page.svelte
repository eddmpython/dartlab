<script lang="ts">
	import { EcosystemMap } from '@dartlab/ui-surfaces/map';
	import { IndustryAtlas } from '@dartlab/ui-surfaces/map';
	import { IndustryDrilldown } from '@dartlab/ui-surfaces/map';
	import { CompanyCard } from '@dartlab/ui-surfaces/map';
	import { TutorialTour } from '@dartlab/ui-surfaces/map';
	import { FreshnessBadge } from '@dartlab/ui-surfaces/map';
	import { CompareTray } from '@dartlab/ui-surfaces/map';
	import { FloatingCard } from '@dartlab/ui-surfaces/map';
	import { MapCommandPalette } from '@dartlab/ui-surfaces/map';
	import { TreemapView } from '@dartlab/ui-surfaces/map';
	import { SectorHealthCard } from '@dartlab/ui-surfaces/map';
	import { ShockSimulator } from '@dartlab/ui-surfaces/map';
	import { brand } from '$lib/brand';
	import { onMount } from 'svelte';
	import { page } from '$app/state';
	import type { PageData } from './$types';
	import { base } from '$app/paths';
	import { loadJson } from '@dartlab/ui-runtime/data/dartlabData';

	let { data }: { data: PageData } = $props();
	let tourOpen = $state(false);
	let moversDismissed = $state(false);
	let cmdPaletteOpen = $state(false);

	// ── 글로벌 키보드 단축키 ──
	function globalKeyHandler(e: KeyboardEvent) {
		// 입력 중 (input/textarea/select) 이면 스킵
		const tag = (e.target as Element)?.tagName;
		if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

		// Ctrl+K 또는 / → Command Palette
		if ((e.ctrlKey && e.key === 'k') || (e.key === '/' && !e.ctrlKey && !e.metaKey)) {
			e.preventDefault();
			cmdPaletteOpen = true;
			return;
		}
		// 1~6 → colorMetric 전환
		const metricKeys: Record<string, typeof colorMetric> = {
			'1': 'industry', '2': 'roe', '3': 'opMargin',
			'4': 'debtRatio', '5': 'revCagr', '6': 'revenue',
			'7': 'govGrade', '8': 'holderPct', '9': 'marketShare'
		};
		if (metricKeys[e.key] && !e.ctrlKey && !e.metaKey) {
			colorMetric = metricKeys[e.key];
			return;
		}
		// T → treemap 뷰 토글
		if (e.key === 't' && !e.ctrlKey && !e.metaKey) {
			viewMode = viewMode === 'treemap' ? 'atlas' : 'treemap';
			return;
		}
		// ? → 투어
		if (e.key === '?' && !e.ctrlKey) {
			tourOpen = true;
			return;
		}
	}

	// 이상 신호 오버레이 토글
	let showMoversOverlay = $state(false);

	// 타임라인 슬라이더
	let timelinePeriods = $derived((data as any)?.timeline?.periods || []);
	let timelineData = $derived((data as any)?.timeline?.data || {});
	let timelineIndustryTotals = $derived((data as any)?.timeline?.industryTotals || {});
	let selectedYear: string = $state(''); // '' = 현재 (실시간)
	$effect(() => {
		// 기본값: 최신 연도 (또는 비활성)
		if (timelinePeriods.length && !selectedYear) {
			selectedYear = ''; // 현재 = 슬라이더 비활성
		}
	});

	// movers stockCode → signal type 매핑
	let moversSignalMap = $derived.by(() => {
		const m = new Map<string, string>();
		const cats = (data as any)?.movers?.categories || {};
		for (const [cat, v] of Object.entries(cats) as any) {
			for (const e of v.entries || []) {
				if (!m.has(e.stockCode)) m.set(e.stockCode, cat);
			}
		}
		return m;
	});

	// 총 변화 건수
	let moversCount = $derived.by(() => {
		const cats = (data as any)?.movers?.categories || {};
		return (Object.values(cats) as any[]).reduce((s, c: any) => s + (c.entries?.length || 0), 0);
	});

	// 산업별 movers 카운트 (atlas 뷰 변화감지 렌즈에서 사용)
	let moversByIndustry = $derived.by(() => {
		const m = new Map<string, number>();
		const stockToIndustry = new Map<string, string>();
		for (const n of data.ecosystem?.nodes || []) {
			if (n.id && n.industry) stockToIndustry.set(n.id, n.industry);
		}
		for (const stockCode of moversSignalMap.keys()) {
			const ind = stockToIndustry.get(stockCode);
			if (ind) m.set(ind, (m.get(ind) || 0) + 1);
		}
		return m;
	});

	// 스크리너 → 지도 양방향: highlight 회사들의 산업별 카운트 (atlas 산업 펄스)
	let highlightByIndustry = $derived.by(() => {
		const m = new Map<string, number>();
		if (highlightCompanies.size === 0) return m;
		const stockToIndustry = new Map<string, string>();
		for (const n of data.ecosystem?.nodes || []) {
			if (n.id && n.industry) stockToIndustry.set(n.id, n.industry);
		}
		for (const code of highlightCompanies) {
			const ind = stockToIndustry.get(code);
			if (ind) m.set(ind, (m.get(ind) || 0) + 1);
		}
		return m;
	});

	// ── 뷰 모드 ──
	// atlas: 34개 산업 노드 + 산업간 supplier flow (default)
	// companies: 기존 ecosystem 전체 2,664사
	// industry: 한 산업 내부 drill-down
	type ViewMode = 'atlas' | 'treemap' | 'companies' | 'industry';
	let viewMode: ViewMode = $state('atlas');
	let drillIndustry: string | null = $state(null);
	// 업종 체력 카드 (atlas 뷰에서 업종 클릭 시)
	let sectorHealthId: string | null = $state(null);
	let sectorHealthName: string = $state('');
	// 충격 시뮬레이션
	let shockTargetId: string | null = $state(null);
	let shockTargetName: string = $state('');
	let shockImpactMap: Map<string, number> = $state(new Map());
	let industryDetail: any = $state(null);
	let industryLoading = $state(false);

	// ── 색상 기준 ──
	type ColorMetric = 'industry' | 'roe' | 'opMargin' | 'debtRatio' | 'revCagr' | 'revenue'
		| 'govGrade' | 'qualGrade' | 'holderPct' | 'holderChange' | 'marketShare' | 'empCount';
	let colorMetric: ColorMetric = $state('roe');

	// ── 렌즈 (분석 관점) · 각 렌즈가 색·오버레이 기본값을 한꺼번에 세팅 ──
	type Lens = 'default' | 'changes';
	let lens: Lens = $state('default');
	function applyLens(next: Lens) {
		lens = next;
		if (next === 'default') {
			colorMetric = 'industry';
			showMoversOverlay = false;
		} else if (next === 'changes') {
			colorMetric = 'roe';
			showMoversOverlay = true;
		}
	}

	const GRAY = '#475569';
	// 재무 스코어 팔레트 (저→고)
	function _lerp(c1: [number, number, number], c2: [number, number, number], t: number): string {
		const r = Math.round(c1[0] + (c2[0] - c1[0]) * t);
		const g = Math.round(c1[1] + (c2[1] - c1[1]) * t);
		const b = Math.round(c1[2] + (c2[2] - c1[2]) * t);
		return `rgb(${r},${g},${b})`;
	}
	function _scale(v: number, stops: Array<[number, [number, number, number]]>): string {
		if (v <= stops[0][0]) return `rgb(${stops[0][1].join(',')})`;
		const last = stops[stops.length - 1];
		if (v >= last[0]) return `rgb(${last[1].join(',')})`;
		for (let i = 0; i < stops.length - 1; i++) {
			const [a, ca] = stops[i];
			const [b, cb] = stops[i + 1];
			if (v >= a && v <= b) return _lerp(ca, cb, (v - a) / (b - a));
		}
		return GRAY;
	}

	function colorFor(n: any, metric: ColorMetric): string {
		if (metric === 'industry' || n.isIndustry) return n.color;
		const v = n[metric];
		if (v === null || v === undefined || Number.isNaN(v)) return GRAY;
		if (metric === 'roe') {
			return _scale(v, [
				[-10, [239, 68, 68]],
				[0, [245, 158, 11]],
				[10, [132, 204, 22]],
				[20, [16, 185, 129]]
			]);
		}
		if (metric === 'opMargin') {
			return _scale(v, [
				[-5, [239, 68, 68]],
				[0, [245, 158, 11]],
				[10, [132, 204, 22]],
				[20, [16, 185, 129]]
			]);
		}
		if (metric === 'debtRatio') {
			// 역방향 (낮을수록 좋음)
			return _scale(v, [
				[50, [16, 185, 129]],
				[100, [132, 204, 22]],
				[200, [245, 158, 11]],
				[400, [239, 68, 68]]
			]);
		}
		if (metric === 'revCagr') {
			return _scale(v, [
				[-10, [239, 68, 68]],
				[0, [245, 158, 11]],
				[15, [132, 204, 22]],
				[30, [16, 185, 129]]
			]);
		}
		if (metric === 'revenue') {
			const eok = v / 1e8;
			const t = Math.max(0, Math.min(1, Math.log10(Math.max(1, eok)) / 6));
			return _scale(t, [
				[0, [30, 58, 138]],
				[0.5, [59, 130, 246]],
				[1, [147, 197, 253]]
			]);
		}
		// 등급 기반 색상 (A~E → 5단계)
		if (metric === 'govGrade' || metric === 'qualGrade') {
			const gradeMap: Record<string, number> = { 'A': 4, 'B': 3, 'C': 2, 'D': 1, 'E': 0, '우수': 4, '양호': 3, '보통': 2, '주의': 1, '위험': 0 };
			const g = gradeMap[v] ?? -1;
			if (g < 0) return GRAY;
			return _scale(g, [[0, [239, 68, 68]], [2, [245, 158, 11]], [4, [16, 185, 129]]]);
		}
		if (metric === 'holderPct') {
			return _scale(v, [[0, [59, 130, 246]], [25, [132, 204, 22]], [50, [16, 185, 129]], [75, [245, 158, 11]]]);
		}
		if (metric === 'holderChange') {
			return _scale(v, [[-10, [239, 68, 68]], [0, [100, 116, 139]], [10, [16, 185, 129]]]);
		}
		if (metric === 'marketShare') {
			return _scale(v, [[0, [30, 58, 138]], [5, [59, 130, 246]], [20, [132, 204, 22]], [50, [16, 185, 129]]]);
		}
		if (metric === 'empCount') {
			const t = Math.max(0, Math.min(1, Math.log10(Math.max(1, v)) / 5));
			return _scale(t, [[0, [100, 116, 139]], [0.5, [59, 130, 246]], [1, [147, 197, 253]]]);
		}
		return GRAY;
	}

	let allNodes = $derived(data.ecosystem.nodes);
	let allLinks = $derived(data.ecosystem.links);
	let industries = $derived(data.ecosystem.industries);

	let indColorMap = $derived(new Map(industries.map((i: any) => [i.id, i.color])));

	// 산업별 집계 · ecosystem.nodes 에서 모든 메트릭의 평균/합 산출
	const GRADE_TO_NUM: Record<string, number> = {
		A: 4, B: 3, C: 2, D: 1, E: 0,
		'우수': 4, '양호': 3, '보통': 2, '주의': 1, '위험': 0
	};
	let industryAggregates = $derived.by(() => {
		const buckets = new Map<string, any[]>();
		for (const n of data.ecosystem?.nodes || []) {
			if (!n.industry) continue;
			if (!buckets.has(n.industry)) buckets.set(n.industry, []);
			buckets.get(n.industry)!.push(n);
		}
		const out = new Map<string, Record<string, number | null>>();
		const meanOf = (nodes: any[], k: string): number | null => {
			const vs = nodes.map((n) => n[k]).filter((v) => v !== null && v !== undefined && !Number.isNaN(v));
			return vs.length ? vs.reduce((a: number, b: number) => a + b, 0) / vs.length : null;
		};
		const meanGrade = (nodes: any[], k: string): number | null => {
			const vs = nodes.map((n) => GRADE_TO_NUM[n[k]]).filter((v) => v !== undefined);
			return vs.length ? vs.reduce((a: number, b: number) => a + b, 0) / vs.length : null;
		};
		for (const [ind, ns] of buckets) {
			out.set(ind, {
				roe: meanOf(ns, 'roe'),
				opMargin: meanOf(ns, 'opMargin'),
				debtRatio: meanOf(ns, 'debtRatio'),
				revCagr: meanOf(ns, 'revCagr'),
				revenue: ns.reduce((s: number, n: any) => s + (n.revenue || 0), 0),
				empCount: ns.reduce((s: number, n: any) => s + (n.empCount || 0), 0),
				holderPct: meanOf(ns, 'holderPct'),
				holderChange: meanOf(ns, 'holderChange'),
				govGradeNum: meanGrade(ns, 'govGrade'),
				qualGradeNum: meanGrade(ns, 'qualGrade')
			});
		}
		return out;
	});

	// Atlas 산업 노드용 색 + metricValue (라벨 표시용) · colorMetric 에 따라 위 집계로
	let atlasIndustriesColored = $derived.by(() => {
		return data.atlas.industries.map((ind: any) => {
			const baseColor = indColorMap.get(ind.id) || '#9ca3af';
			if (colorMetric === 'industry') {
				return { ...ind, color: baseColor, metricValue: null };
			}

			const a = industryAggregates.get(ind.id);
			if (!a) return { ...ind, color: baseColor, metricValue: null };

			// 등급 메트릭 · 0~4 numeric 평균을 직접 색 스케일에 매핑
			if (colorMetric === 'govGrade' || colorMetric === 'qualGrade') {
				const v = colorMetric === 'govGrade' ? a.govGradeNum : a.qualGradeNum;
				if (v === null || v === undefined) {
					return { ...ind, color: baseColor, metricValue: null };
				}
				return {
					...ind,
					color: _scale(v, [
						[0, [239, 68, 68]],
						[2, [245, 158, 11]],
						[4, [16, 185, 129]]
					]),
					metricValue: v
				};
			}

			// marketShare 는 산업 단위에서 의미 없음 → 팔레트 폴백
			if (colorMetric === 'marketShare') {
				return { ...ind, color: baseColor, metricValue: null };
			}

			const v = a[colorMetric];
			if (v === null || v === undefined || Number.isNaN(v)) {
				return { ...ind, color: baseColor, metricValue: null };
			}
			return {
				...ind,
				color: colorFor({ [colorMetric]: v }, colorMetric as any),
				metricValue: v
			};
		});
	});

	// ── 필터 상태 (companies 뷰) ──
	let enabledIndustries = $state<Set<string>>(new Set());
	let initialized = $state(false);
	$effect(() => {
		if (!initialized && data?.ecosystem?.industries) {
			enabledIndustries = new Set(data.ecosystem.industries.map((i: any) => i.id));
			initialized = true;
		}
	});
	let showSupplier = $state(true);
	let showAffiliate = $state(false);
	let showInvestor = $state(false);
	let minConfidence = $state(0.6);
	let onlyWithAmount = $state(false);
	let searchQuery = $state('');

	let selectedNode: any = $state(null);
	let mapRef: any = $state(null);

	// ── 회사 상세 (companies/{code}.json fetch) ──
	let selectedDetail: any = $state(null);
	let selectedDetailLoading = $state(false);
	let selectedDetailCode: string | null = $state(null);

	async function loadCompanyDetail(stockCode: string) {
		if (selectedDetailCode === stockCode && selectedDetail) return;
		selectedDetailLoading = true;
		selectedDetailCode = stockCode;
		try {
			selectedDetail = await loadJson<any>(`map/companies/${stockCode}.json`, { fetchFn: fetch });
		} catch {
			selectedDetail = null;
		} finally {
			selectedDetailLoading = false;
		}
	}

	// ── 비교 슬롯 (최대 4사) ──
	// 맵 우측 패널의 2-way 미니 비교는 compareB 1개만 사용 (레거시)
	// 본격 비교는 compareSet + CompareTray → /compare?codes= 로
	const COMPARE_MAX = 4;
	let compareSet: any[] = $state([]); // [{node, detail}]
	let compareB: any = $state(null);
	let compareBDetail: any = $state(null);
	let comparing = $derived(!!compareB);

	async function addToCompare(stockCode: string) {
		if (!stockCode) return;
		const already = compareSet.find((x: any) => x.node?.id === stockCode);
		if (already) return;
		if (compareSet.length >= COMPARE_MAX) return; // 최대 4사

		const node = nodeFinderById(stockCode);
		if (!node) return;
		const detail = await loadJson<any>(`map/companies/${stockCode}.json`, { fetchFn: fetch });
		compareSet = [...compareSet, { node, detail }];

		// 레거시 2-way: compareB 는 compareSet 의 두 번째 회사
		if (compareSet.length >= 2 && selectedNode) {
			const other = compareSet.find((x: any) => x.node?.id !== selectedNode.id);
			if (other) {
				compareB = other.node;
				compareBDetail = other.detail;
			}
		}
	}

	function removeFromCompare(stockCode: string) {
		compareSet = compareSet.filter((x: any) => x.node?.id !== stockCode);
		if (compareB?.id === stockCode) {
			compareB = null;
			compareBDetail = null;
		}
	}

	function clearCompareAll() {
		compareSet = [];
		compareB = null;
		compareBDetail = null;
	}

	function nodeFinderById(stockCode: string): any {
		for (const n of allNodes) if (n.id === stockCode) return { ...n, color: colorFor(n, colorMetric) };
		return null;
	}

	function clearCompare() {
		compareB = null;
		compareBDetail = null;
	}

	function openCompareFull() {
		const codes = compareSet.map((x: any) => x.node?.id).filter(Boolean).join(',');
		if (codes) window.location.href = `${base}/compare?codes=${codes}`;
	}

	// ── 플로팅 카드 (띄우기 윈도우) ──
	interface FloatCard {
		id: string;
		node: any;
		detail: any | null;
		x: number;
		y: number;
		w: number;
		h: number;
		z: number;
	}
	let floatingCards: FloatCard[] = $state([]);
	let floatingZTop = $state(100);

	async function detachCard(stockCode: string) {
		// 이미 띄워져 있으면 포커스만
		const existing = floatingCards.find((c) => c.id === stockCode);
		if (existing) {
			focusFloating(stockCode);
			return;
		}
		const node = nodeFinderById(stockCode);
		if (!node) return;
		const detail = await loadJson<any>(`map/companies/${stockCode}.json`, { fetchFn: fetch });
		// 초기 배치: 우측 상단 기준 계단식 (Bloomberg 스타일)
		const n_open = floatingCards.length;
		const vw = typeof window !== 'undefined' ? window.innerWidth : 1400;
		const vh = typeof window !== 'undefined' ? window.innerHeight : 900;
		const w = 500;
		const h = Math.min(680, vh - 80);
		// 첫 카드 우측 상단. 이후 좌측 아래로 계단
		const x = Math.max(40, vw - w - 20 - n_open * 30);
		const y = Math.max(40, 60 + n_open * 30);
		floatingZTop += 1;
		floatingCards = [...floatingCards, { id: stockCode, node, detail, x, y, w, h, z: floatingZTop }];

		// 기존 패널에서 이 회사가 선택되어 있었다면 닫기 (중복 방지)
		if (selectedNode?.id === stockCode) {
			selectedNode = null;
			selectedDetail = null;
			selectedDetailCode = null;
		}
	}

	function closeFloating(stockCode: string) {
		floatingCards = floatingCards.filter((c) => c.id !== stockCode);
	}

	function focusFloating(stockCode: string) {
		floatingZTop += 1;
		floatingCards = floatingCards.map((c) =>
			c.id === stockCode ? { ...c, z: floatingZTop } : c
		);
		// 이미 열린 카드에 shake 피드백은 FloatingCard CSS 의 .shaking 으로 제어
		// detachCard 에서 existing 감지 시 이미 focusFloating 호출됨
	}

	function moveFloating(stockCode: string, x: number, y: number) {
		const idx = floatingCards.findIndex((c) => c.id === stockCode);
		if (idx >= 0) {
			floatingCards[idx].x = x;
			floatingCards[idx].y = y;
		}
	}
	function resizeFloating(stockCode: string, w: number, h: number) {
		const idx = floatingCards.findIndex((c) => c.id === stockCode);
		if (idx >= 0) {
			floatingCards[idx].w = w;
			floatingCards[idx].h = h;
		}
	}

	// ── 투어용 데모 헬퍼 ──
	async function demoSelectCompany(stockCode: string) {
		const n = nodeFinderById(stockCode);
		if (!n) return;
		selectedNode = n;
		await loadCompanyDetail(stockCode);
	}
	async function demoAddCompare(stockCode: string) {
		await addToCompare(stockCode);
	}
	function demoClearSelection() {
		selectedNode = null;
		selectedDetail = null;
		selectedDetailCode = null;
		compareB = null;
		compareBDetail = null;
	}

	// ── companies 뷰 데이터 ──
	let filteredNodes = $derived(
		allNodes
			.filter((n: any) => enabledIndustries.has(n.industry))
			.map((n: any) => ({ ...n, color: colorFor(n, colorMetric) }))
	);

	let filteredLinks = $derived(
		allLinks.filter((l: any) => {
			if (l.type === 'supplier' && !showSupplier) return false;
			if (l.type === 'affiliate' && !showAffiliate) return false;
			if (l.type === 'investor' && !showInvestor) return false;
			if (l.type === 'customer' && !showSupplier) return false;
			if (l.confidence < minConfidence) return false;
			if (onlyWithAmount && !l.amount) return false;
			return true;
		})
	);

	// ── atlas 뷰 데이터 ──
	let atlasNodes = $derived(
		data.atlas.industries.map((ind: any) => ({
			id: `ind:${ind.id}`,
			label: ind.name,
			industry: ind.id,
			industryName: ind.name,
			stage: '',
			stageName: '',
			role: '',
			stream: '',
			revenue: (ind.revenue || 0) * 1e8, // 억 → 원
			size: Math.max(8, Math.min(32, 6 + Math.log2((ind.nodeCount || 1) + 1) * 2.8)),
			color: indColorMap.get(ind.id) ?? '#9ca3af',
			isIndustry: true,
			nodeCount: ind.nodeCount,
			stageMix: ind.stageMix,
			stages: ind.stages
		}))
	);

	let atlasLinks = $derived(
		data.atlas.flows.map((f: any) => ({
			source: `ind:${f.fromIndustry}`,
			target: `ind:${f.toIndustry}`,
			type: 'supplier',
			amount: f.amount,
			ratio: null,
			product: '',
			confidence: 1,
			source_tag: 'aggregate',
			edgeCount: f.edgeCount
		}))
	);

	// ── industry(drill-down) 뷰 데이터 ──
	let stageFilter = $state<Set<string>>(new Set());
	let stageInitialized = $state<string | null>(null);

	$effect(() => {
		if (industryDetail && stageInitialized !== industryDetail.industryId) {
			stageFilter = new Set((industryDetail.stages || []).map((s: any) => s.key));
			stageInitialized = industryDetail.industryId;
		}
	});

	let industryNodes = $derived.by(() => {
		if (!industryDetail) return [];
		// 연도 선택 시 · 해당 연도 데이터가 있는 회사만 포함, revenue/opMargin 도 그 해 값으로 덮어쓰기
		const yearData: Record<string, { revenue?: number; opMargin?: number | null }> | null =
			selectedYear ? (timelineData[selectedYear] || {}) : null;
		const out: any[] = [];
		for (const s of industryDetail.stages || []) {
			if (!stageFilter.has(s.key)) continue;
			for (const n of s.nodes || []) {
				const tl = yearData ? yearData[n.stockCode] : null;
				if (yearData && !tl) continue; // 해당 연도 데이터 없는 회사 제외
				// timeline.revenue 는 원 단위, industries/*.json 의 revenue 는 억 단위
				const revWon = tl ? (tl.revenue || 0) : (n.revenue || 0) * 1e8;
				const opMargin = tl ? (tl.opMargin ?? null) : n.opMargin;
				const base: any = {
					id: n.stockCode,
					label: n.corpName,
					industry: industryDetail.industryId,
					industryName: industryDetail.name,
					stage: n.stage,
					stageName: s.name,
					role: n.role || s.role,
					stream: n.stream || s.stream,
					confidence: n.confidence,
					source: n.source,
					revenue: revWon,
					// scan 지표 (roe·debtRatio·revCagr 은 연도별 데이터 없음 → 정적 유지)
					roe: n.roe,
					opMargin,
					debtRatio: n.debtRatio,
					revCagr: n.revCagr,
					profGrade: n.profGrade,
					debtGrade: n.debtGrade,
					growthGrade: n.growthGrade,
					size: Math.max(4, Math.min(20, 3 + Math.log2(revWon / 1e10 + 1)))
				};
				base.color = colorFor(base, colorMetric);
				out.push(base);
			}
		}
		return out;
	});

	let industryLinks = $derived.by(() => {
		if (!industryDetail) return [];
		const nodeIds = new Set(industryNodes.map((n: any) => n.id));
		return (industryDetail.edges || [])
			.filter((e: any) => nodeIds.has(e.from) && nodeIds.has(e.to))
			.map((e: any) => ({
				source: e.from,
				target: e.to,
				type: e.type,
				amount: e.amount,
				ratio: e.ratio,
				product: e.product,
				confidence: e.confidence,
				source_tag: e.source
			}));
	});

	// ── 활성 뷰 데이터 ──
	let activeNodes = $derived(
		viewMode === 'atlas' ? atlasNodes : viewMode === 'industry' ? industryNodes : filteredNodes
	);
	let activeLinks = $derived(
		viewMode === 'atlas' ? atlasLinks : viewMode === 'industry' ? industryLinks : filteredLinks
	);

	// ── 뷰 전환 ──
	let loadError = $state<string | null>(null);

	async function enterIndustry(industryId: string) {
		console.log('[map] enterIndustry', industryId);
		industryLoading = true;
		drillIndustry = industryId;
		viewMode = 'industry';
		selectedNode = null;
		loadError = null;
		const path = `map/industries/${industryId}.json`;
		try {
			const detail = await loadJson<any>(path, { fetchFn: fetch });
			if (!detail) {
				loadError = `데이터 없음 · ${path}`;
				industryDetail = null;
				return;
			}
			industryDetail = detail;
			console.log(
				'[map] industryDetail loaded',
				industryDetail?.industryId,
				'stages',
				industryDetail?.stages?.length
			);
		} catch (e: any) {
			console.error('[map] fetch failed', e);
			loadError = e?.message || String(e);
			industryDetail = null;
		} finally {
			industryLoading = false;
			console.log('[map] industryLoading=false');
		}
	}

	function exitToAtlas() {
		viewMode = 'atlas';
		drillIndustry = null;
		industryDetail = null;
		selectedNode = null;
	}

	function switchView(mode: ViewMode) {
		if (mode === 'industry') return; // industry 는 enterIndustry 로만
		viewMode = mode;
		selectedNode = null;
	}

	// 충격 시뮬레이션 시작
	function startShockSim(stockCode: string) {
		const node = allNodes.find((n: any) => n.id === stockCode);
		shockTargetId = stockCode;
		shockTargetName = node?.label || stockCode;
	}

	// treemap 에서 노드 클릭 → FloatingCard
	function handleTreemapClick(node: any) {
		if (!node) return;
		if (isMobile) {
			selectedNode = node;
			loadCompanyDetail(node.id);
		} else {
			detachCard(node.id);
		}
	}

	// ── 모바일 감지 ──
	let isMobile = $state(typeof window !== 'undefined' ? window.innerWidth < 768 : false);
	let sidebarCollapsed = $state(false);

	// ── 노드 클릭 ──
	function handleNodeClick(node: any) {
		if (!node) {
			selectedNode = null;
			selectedDetail = null;
			selectedDetailCode = null;
			return;
		}
		if (node.isIndustry) {
			enterIndustry(node.industry);
			return;
		}
		if (isMobile) {
			// 모바일: 기존 고정 패널 (detail-panel)
			selectedNode = node;
			loadCompanyDetail(node.id);
		} else {
			// 데스크톱: 즉시 FloatingCard
			detachCard(node.id);
		}
	}

	// ── URL 쿼리 처리 (외부 진입: /map?focus=005930, /map?highlight=001830,005930) ──
	let urlHandled = $state(false);
	/** /screener → /map 양방향 링크 · 결과 회사 stockCode set */
	let highlightCompanies = $state<Set<string>>(new Set());
	onMount(() => {
		if (urlHandled) return;
		const focus = page.url.searchParams.get('focus');
		const cmp = page.url.searchParams.get('compare');
		const highlight = page.url.searchParams.get('highlight');
		if (highlight) {
			highlightCompanies = new Set(highlight.split(',').filter(Boolean));
		}
		if (focus) {
			if (isMobile) {
				const n = nodeFinderById(focus);
				if (n) { selectedNode = n; loadCompanyDetail(focus); }
			} else {
				detachCard(focus);
			}
		}
		if (cmp) {
			const [a, b] = cmp.split(',');
			if (a) {
				if (isMobile) {
					const na = nodeFinderById(a);
					if (na) { selectedNode = na; loadCompanyDetail(a); }
				} else {
					detachCard(a);
				}
			}
			if (b) {
				if (isMobile) { addToCompare(b); }
				else { detachCard(b); }
			}
		}
		urlHandled = true;

		// 첫 방문 튜토리얼 자동 시작
		try {
			if (!localStorage.getItem('dartlab.map.tour.done') && !focus && !cmp) {
				setTimeout(() => {
					tourOpen = true;
				}, 800);
			}
		} catch {
			/* noop */
		}
	});

	// ── 필터 통계 (companies 뷰) ──
	let filterInsights = $derived.by(() => {
		if (viewMode !== 'companies') return null;
		const nodes = filteredNodes;
		if (nodes.length === 0) return null;
		const totalRev = nodes.reduce((s: number, n: any) => s + (n.revenue || 0), 0);
		const sorted = [...nodes].sort((a: any, b: any) => (b.revenue || 0) - (a.revenue || 0));
		const top1 = sorted[0]?.revenue || 0;
		const top3 = sorted.slice(0, 3).reduce((s: number, n: any) => s + (n.revenue || 0), 0);
		const top1Ratio = totalRev > 0 ? (top1 / totalRev) * 100 : 0;
		const top3Ratio = totalRev > 0 ? (top3 / totalRev) * 100 : 0;
		const preciseEdges = filteredLinks.filter((l: any) => l.amount).length;
		const singleIndustry = enabledIndustries.size === 1;
		let singleIndId: string | null = null;
		if (singleIndustry) {
			const iter = enabledIndustries.values().next();
			singleIndId = iter.value ?? null;
		}
		return {
			count: nodes.length,
			totalRev,
			top1Name: sorted[0]?.label || '',
			top1Ratio,
			top3Ratio,
			preciseEdges,
			singleIndId
		};
	});

	function toggleIndustry(id: string) {
		const next = new Set(enabledIndustries);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		enabledIndustries = next;
	}
	function toggleAllIndustries(on: boolean) {
		enabledIndustries = on ? new Set(industries.map((i: any) => i.id)) : new Set();
	}
	function toggleStage(key: string) {
		const next = new Set(stageFilter);
		if (next.has(key)) next.delete(key);
		else next.add(key);
		stageFilter = next;
	}

	function formatRev(rev: number): string {
		if (rev >= 1e12) return `${(rev / 1e12).toFixed(1)}조원`;
		return `${Math.round(rev / 1e8).toLocaleString()}억원`;
	}

	function handleSearch() {
		if (!searchQuery.trim()) return;
		const q = searchQuery.toLowerCase();
		const pool = activeNodes;
		const match = pool.find(
			(n: any) =>
				n.label.includes(searchQuery) ||
				n.id === searchQuery ||
				n.label.toLowerCase().includes(q)
		);
		if (match && mapRef) {
			mapRef.zoomToNode(match.id);
			selectedNode = match;
		}
	}
</script>

<svelte:window onkeydown={globalKeyHandler} />

<svelte:head>
	<title>산업지도 | dartlab 전자공시</title>
	<meta
		name="description"
		content="한국 상장사 2,664사 · 34개 산업 · 공급망 18,418 관계. 10초 안에 보는 산업 생태계 지도."
	/>
	<meta property="og:type" content="website" />
	<meta property="og:title" content="dartlab 산업지도 · 한국 상장사 2,664사 생태계" />
	<meta
		property="og:description"
		content="34 산업 × 공급망 드릴다운 · 변화 감지 · 조건 검색 · 비교. 10초 안에 보는 지도."
	/>
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta name="twitter:card" content="summary_large_image" />
</svelte:head>

<div class="map-page" class:sidebar-collapsed={sidebarCollapsed}>
	<!-- 왼쪽 사이드바 -->
	<button class="collapse-toggle" onclick={() => (sidebarCollapsed = !sidebarCollapsed)} title={sidebarCollapsed ? '사이드바 열기' : '사이드바 접기'}>
		{sidebarCollapsed ? '≫' : '≪'}
	</button>
	<aside class="sidebar" class:collapsed={sidebarCollapsed}>
		<!-- 브랜드 바: 아바타 → GitHub → Coffee → 도움말 (단색 라인 아이콘 일관) -->
		<div class="brand-bar">
			<a class="brand-btn avatar" href="{base}/" title="dartlab 홈으로" aria-label="홈">
				<picture>
					<source srcset="{base}/avatar.webp" type="image/webp" />
					<img src="{base}/avatar.png" alt="dartlab" width="16" height="16" />
				</picture>
			</a>
			<a
				class="brand-btn"
				href={brand.repo}
				target="_blank"
				rel="noopener"
				title="GitHub 저장소"
				aria-label="GitHub"
			>
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<path d="M9 19c-4.3 1.4-4.3-2.5-6-3m12 5v-3.5c0-1 .1-1.4-.5-2 2.8-.3 5.5-1.4 5.5-6a4.6 4.6 0 0 0-1.3-3.2 4.2 4.2 0 0 0-.1-3.2s-1.1-.3-3.5 1.3a12 12 0 0 0-6.2 0C6.5 2.8 5.4 3.1 5.4 3.1a4.2 4.2 0 0 0-.1 3.2A4.6 4.6 0 0 0 4 9.5c0 4.6 2.7 5.7 5.5 6-.6.6-.6 1.2-.5 2V21" />
				</svg>
			</a>
			<a
				class="brand-btn"
				href={brand.coffee}
				target="_blank"
				rel="noopener"
				title="Buy Me A Coffee · 후원"
				aria-label="Buy Me A Coffee"
			>
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<path d="M17 8h1a4 4 0 1 1 0 8h-1" />
					<path d="M3 8h14v9a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4Z" />
					<line x1="6" y1="2" x2="6" y2="4" />
					<line x1="10" y1="2" x2="10" y2="4" />
					<line x1="14" y1="2" x2="14" y2="4" />
				</svg>
			</a>
			<button
				class="brand-btn help"
				onclick={() => (tourOpen = true)}
				title="가이드 투어 · 뭘 보고 어떻게 쓰는지 화면 안내"
				aria-label="가이드 투어"
			>
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
					<circle cx="12" cy="12" r="10" />
					<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
					<line x1="12" y1="17" x2="12.01" y2="17" />
				</svg>
			</button>
		</div>

		<!-- 데이터 신선도 배지 -->
		{#if data.meta?.dataAsOf}
			<div class="freshness-row">
				<FreshnessBadge dataAsOf={data.meta.dataAsOf} variant="compact" />
			</div>
		{/if}

		<div class="header">
			<h1><span class="brand-gradient">산업 생태계</span></h1>
			{#if viewMode === 'atlas'}
				<p class="sub">{data.atlas.industries.length}개 산업 · {data.atlas.flows.length}개 플로우</p>
			{:else if viewMode === 'industry' && industryDetail}
				<p class="sub">
					<button class="crumb" onclick={exitToAtlas} title="전체 산업으로">← 산업</button>
					· {industryDetail.name} · {industryDetail.nodeCount}사
				</p>
			{:else}
				<p class="sub">
					{filteredNodes.length.toLocaleString()}사 · {filteredLinks.length.toLocaleString()}관계
				</p>
			{/if}
		</div>

		<!-- 색상 기준 셀렉터 -->
		<div class="section color-switch">
			<h3>색상 기준 <span class="lens-hint">렌즈가 자동 세팅 · 직접 변경 가능</span></h3>
			<select class="metric-select" bind:value={colorMetric}>
				<optgroup label="기본">
					<option value="industry">산업 팔레트 (1)</option>
					<option value="roe">ROE (2)</option>
					<option value="opMargin">영업이익률 (3)</option>
					<option value="debtRatio">부채비율 (4)</option>
					<option value="revCagr">매출 CAGR (5)</option>
					<option value="revenue">매출 규모 (6)</option>
				</optgroup>
				<optgroup label="거버넌스·내부자">
					<option value="govGrade">지배구조 등급 (7)</option>
					<option value="qualGrade">이익 질 등급</option>
					<option value="holderPct">최대주주 지분율 (8)</option>
					<option value="holderChange">지분 변동</option>
				</optgroup>
				<optgroup label="구조">
					<option value="marketShare">상장사매출비중 (9)</option>
					<option value="empCount">직원수</option>
				</optgroup>
			</select>
			{#if colorMetric !== 'industry'}
				<div class="color-legend">
					{#if colorMetric === 'debtRatio'}
						<span class="lg-swatch" style="background:#10b981"></span>
						<span class="lg-label">낮음(건전)</span>
						<span class="lg-swatch" style="background:#ef4444"></span>
						<span class="lg-label">높음(위험)</span>
					{:else if colorMetric === 'revenue' || colorMetric === 'empCount'}
						<span class="lg-swatch" style="background:#1e3a8a"></span>
						<span class="lg-swatch" style="background:#3b82f6"></span>
						<span class="lg-swatch" style="background:#93c5fd"></span>
						<span class="lg-label">소 → 대</span>
					{:else if colorMetric === 'holderChange'}
						<span class="lg-swatch" style="background:#ef4444"></span>
						<span class="lg-label">감소</span>
						<span class="lg-swatch" style="background:#64748b"></span>
						<span class="lg-label">변동없음</span>
						<span class="lg-swatch" style="background:#10b981"></span>
						<span class="lg-label">증가</span>
					{:else if colorMetric === 'govGrade' || colorMetric === 'qualGrade'}
						<span class="lg-swatch" style="background:#ef4444"></span>
						<span class="lg-label">E/위험</span>
						<span class="lg-swatch" style="background:#f59e0b"></span>
						<span class="lg-swatch" style="background:#10b981"></span>
						<span class="lg-label">A/우수</span>
					{:else}
						<span class="lg-swatch" style="background:#ef4444"></span>
						<span class="lg-swatch" style="background:#f59e0b"></span>
						<span class="lg-swatch" style="background:#84cc16"></span>
						<span class="lg-swatch" style="background:#10b981"></span>
						<span class="lg-label">저 → 고</span>
					{/if}
				</div>
			{/if}
		</div>

		<!-- 오버레이 토글 -->
		{#if moversCount > 0}
			<div class="section overlay-toggles">
				<label class="overlay-toggle">
					<input type="checkbox" bind:checked={showMoversOverlay} />
					<span>⚡ 이상 신호 ({moversCount}건)</span>
				</label>
			</div>
		{/if}

		<!-- 관점(view) 셀렉터 -->
		<div class="section view-switch">
			<h3>관점</h3>
			<div class="view-tabs">
				<button
					class="view-tab"
					class:active={viewMode === 'atlas'}
					onclick={() => switchView('atlas')}
				>
					<span class="tab-icon">
						<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
							<circle cx="12" cy="12" r="9" />
							<circle cx="12" cy="12" r="4" />
							<circle cx="12" cy="3" r="1.5" fill="currentColor" />
							<circle cx="21" cy="12" r="1.5" fill="currentColor" />
							<circle cx="12" cy="21" r="1.5" fill="currentColor" />
							<circle cx="3" cy="12" r="1.5" fill="currentColor" />
						</svg>
					</span>
					<span class="tab-body">
						<span class="tab-title">산업 지도</span>
						<span class="hint">34개 산업 + 공급 플로우</span>
					</span>
				</button>
				<button
					class="view-tab"
					class:active={viewMode === 'treemap'}
					onclick={() => switchView('treemap')}
				>
					<span class="tab-icon">
						<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
							<rect x="3" y="3" width="8" height="10" rx="1" />
							<rect x="13" y="3" width="8" height="6" rx="1" />
							<rect x="13" y="11" width="8" height="10" rx="1" />
							<rect x="3" y="15" width="8" height="6" rx="1" />
						</svg>
					</span>
					<span class="tab-body">
						<span class="tab-title">히트맵</span>
						<span class="hint">시장 전체 한눈에 (T)</span>
					</span>
				</button>
				<!-- companies/industry 탭은 v12에서 숨김 (코드는 유지, 자동 드릴다운만) -->
				<!-- hidden: 전 회사 뷰 -->
				<!-- hidden: 산업 내부 · atlas에서 산업 클릭 시 자동 진입 -->
				{#if false}
				<button
					class="view-tab"
					class:active={viewMode === 'companies'}
					onclick={() => switchView('companies')}
				>
					<span class="tab-body">
						<span class="tab-title">전 회사</span>
						<span class="hint">2,664사 전체 그래프</span>
					</span>
				</button>
				<button
					class="view-tab"
					class:active={viewMode === 'industry'}
					disabled={!drillIndustry}
					onclick={() => drillIndustry && enterIndustry(drillIndustry)}
				>
					<span class="tab-body">
						<span class="tab-title">산업 내부</span>
						<span class="hint">
							{drillIndustry
								? `${industryDetail?.name || drillIndustry} 드릴다운`
								: '산업 클릭하여 진입'}
						</span>
					</span>
				</button>
				{/if}
			</div>
		</div>

		<!-- 검색 -->
		<div class="section">
			<input
				type="text"
				bind:value={searchQuery}
				onkeydown={(e) => e.key === 'Enter' && handleSearch()}
				placeholder={viewMode === 'atlas' ? '산업명 검색...' : '회사명/종목코드 검색...'}
				class="search"
			/>
		</div>

		<!-- atlas 뷰 전용: 산업 목록 (클릭=드릴다운) -->
		{#if viewMode === 'atlas'}
			<div class="section industries">
				<h3>산업 (클릭 → 내부 보기)</h3>
				<ul>
					{#each [...data.atlas.industries].sort((a: any, b: any) => b.nodeCount - a.nodeCount) as ind (ind.id)}
						<li>
							<button class="atlas-item" onclick={() => enterIndustry(ind.id)}>
								<span class="swatch" style="background:{indColorMap.get(ind.id) || '#9ca3af'}"
								></span>
								<span class="name">{ind.name}</span>
								<span class="count">{ind.nodeCount}사</span>
							</button>
						</li>
					{/each}
				</ul>
			</div>
		{/if}

		<!-- industry 뷰 전용: stage 필터 + 진입 회사 -->
		{#if viewMode === 'industry' && industryDetail}
			<div class="section">
				<h3>공정 필터</h3>
				<ul class="stage-list">
					{#each industryDetail.stages || [] as s (s.key)}
						<li>
							<label class="check">
								<input
									type="checkbox"
									checked={stageFilter.has(s.key)}
									onchange={() => toggleStage(s.key)}
								/>
								<span
									class="swatch"
									style="background:{s.stream === 'upstream'
										? '#8b5cf6'
										: s.stream === 'downstream'
											? '#f97316'
											: '#f8fafc'}"
								></span>
								<span class="name">{s.name}</span>
								<span class="count">{(s.nodes || []).length}</span>
							</label>
						</li>
					{/each}
				</ul>
			</div>
			<div class="section">
				<h3>총 매출 · 진입 회사</h3>
				<div class="ins-grid">
					<div class="ins-cell">
						<div class="ins-label">총 매출</div>
						<div class="ins-value">
							{formatRev((industryDetail.totalRevenue || 0) * 1e8)}
						</div>
					</div>
					<div class="ins-cell">
						<div class="ins-label">회사 수</div>
						<div class="ins-value">{industryDetail.nodeCount}사</div>
					</div>
				</div>
				<a href="{base}/industry/{industryDetail.industryId}" class="ins-link">
					산업 상세 페이지 →
				</a>
			</div>
		{/if}

		<!-- companies 뷰: 기존 엣지 타입 + 품질 필터 + 산업 토글 -->
		{#if viewMode === 'companies'}
			<div class="section">
				<h3>관계 유형</h3>
				<label class="check"
					><input type="checkbox" bind:checked={showSupplier} />
					<span class="dot supplier"></span>공급</label
				>
				<label class="check"
					><input type="checkbox" bind:checked={showAffiliate} />
					<span class="dot affiliate"></span>계열</label
				>
				<label class="check"
					><input type="checkbox" bind:checked={showInvestor} />
					<span class="dot investor"></span>투자</label
				>
			</div>
			<div class="section">
				<h3>품질 필터</h3>
				<label class="range">
					신뢰도 ≥ {minConfidence.toFixed(1)}
					<input type="range" bind:value={minConfidence} min="0" max="1" step="0.1" />
				</label>
				<label class="check">
					<input type="checkbox" bind:checked={onlyWithAmount} />
					금액 공개 엣지만
				</label>
			</div>
			{#if filterInsights}
				<div class="section insight-box">
					<h3>
						현재 선택
						<span class="info-tip" title="1억원 = 100,000,000 KRW (~$75K) / 1조원 = 10,000억원">ⓘ</span>
					</h3>
					<div class="ins-grid">
						<div class="ins-cell">
							<div class="ins-label">기업</div>
							<div class="ins-value">{filterInsights.count.toLocaleString()}사</div>
						</div>
						<div class="ins-cell">
							<div class="ins-label">총 매출</div>
							<div class="ins-value">{formatRev(filterInsights.totalRev)}</div>
						</div>
						<div class="ins-cell">
							<div class="ins-label">Top1 비중</div>
							<div class="ins-value">{filterInsights.top1Ratio.toFixed(1)}%</div>
						</div>
						<div class="ins-cell">
							<div class="ins-label">Top3 비중</div>
							<div class="ins-value">{filterInsights.top3Ratio.toFixed(1)}%</div>
						</div>
					</div>
					{#if filterInsights.top1Name}
						<div class="ins-sub">
							최대: {filterInsights.top1Name} · 정밀 엣지 {filterInsights.preciseEdges}건
						</div>
					{/if}
					{#if filterInsights.singleIndId}
						<button class="ins-link" onclick={() => enterIndustry(filterInsights!.singleIndId!)}>
							이 산업 내부 보기 →
						</button>
					{/if}
				</div>
			{/if}
			<div class="section industries">
				<h3>
					산업
					<span class="controls">
						<button onclick={() => toggleAllIndustries(true)}>전체</button>
						<button onclick={() => toggleAllIndustries(false)}>해제</button>
					</span>
				</h3>
				<ul>
					{#each industries as ind}
						<li>
							<label class="check industry-item">
								<input
									type="checkbox"
									checked={enabledIndustries.has(ind.id)}
									onchange={() => toggleIndustry(ind.id)}
								/>
								<span class="swatch" style="background:{ind.color}"></span>
								<span class="name">{ind.name}</span>
								<span class="count">{ind.count}</span>
							</label>
							<button
								class="detail-link"
								title="{ind.name} 내부 보기"
								onclick={() => enterIndustry(ind.id)}>→</button
							>
						</li>
					{/each}
				</ul>
			</div>
		{/if}
	</aside>

	<!-- 메인 지도 -->
	<main class="map-main">
		<!-- 렌즈 (분석 관점) · 떠있는 칩 오버레이 -->
		<div class="lens-overlay">
			<button
				class="lens-chip"
				class:active={lens === 'default'}
				onclick={() => applyLens('default')}
				title="산업 팔레트 + 큰 그림"
			>
				<span class="lens-icon" aria-hidden="true">●</span>
				<span class="lens-name">기본</span>
			</button>
			<button
				class="lens-chip"
				class:active={lens === 'changes'}
				onclick={() => applyLens('changes')}
				title="ROE 색 + 이상 신호 오버레이"
			>
				<span class="lens-icon" aria-hidden="true">⚡</span>
				<span class="lens-name">변화 감지</span>
			</button>
		</div>

		<!-- 변화 감지 배너 (dismissible) -->
		{#if moversCount > 0 && !moversDismissed}
			<div class="movers-banner">
				<span class="m-icon">⚡</span>
				<span class="m-text">
					이번 회계연도 급변 <strong>{moversCount}건</strong> 감지 · ROE 개선/악화 · 매출 급증/급락 · 부채 스트레스
				</span>
				<a class="m-cta" href="{base}/changes">상세 보기 →</a>
				<button class="m-close" onclick={() => (moversDismissed = true)} aria-label="닫기">✕</button>
			</div>
		{/if}

		{#if viewMode === 'industry' && industryLoading && !industryDetail}
			<div class="loading-overlay">
				<div>
					<div>산업 데이터 로드 중…</div>
					{#if loadError}
						<div class="err">{loadError}</div>
					{/if}
				</div>
			</div>
		{/if}
		{#if viewMode === 'industry' && loadError && !industryDetail}
			<div class="loading-overlay error-overlay">
				<div>
					<div>⚠ 산업 데이터 로드 실패</div>
					<div class="err">{loadError}</div>
					<button class="retry" onclick={exitToAtlas}>← atlas 로 돌아가기</button>
				</div>
			</div>
		{/if}

		{#if viewMode === 'atlas'}
			<IndustryAtlas
				industries={atlasIndustriesColored}
				flows={data.atlas.flows}
				onSelect={(ind: any) => enterIndustry(ind.id)}
				{colorMetric}
				timelineYear={selectedYear}
				industryTotalsByYear={timelineIndustryTotals}
				moversByIndustry={highlightByIndustry.size > 0 ? highlightByIndustry : (lens === 'changes' ? moversByIndustry : new Map())}
			/>
		{:else if viewMode === 'industry' && industryDetail}
			<div class="drill-breadcrumb">
				<button class="db-back" onclick={exitToAtlas} title="산업지도로 돌아가기">
					<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M19 12H5M12 19l-7-7 7-7" />
					</svg>
					<span>산업지도</span>
				</button>
				<span class="db-divider">|</span>
				<div class="db-current" style:color={String((drillIndustry && indColorMap.get(drillIndustry)) || '#fbbf24')}>
					<span class="db-name">{industryDetail.name}</span>
					{#if selectedYear && drillIndustry && timelineIndustryTotals[selectedYear]?.[drillIndustry]}
						{@const t = timelineIndustryTotals[selectedYear][drillIndustry]}
						<span class="db-meta">{selectedYear}년 · {t.count}사{t.totalRevenue ? ` · ${(t.totalRevenue / 1e12).toFixed(1)}조` : ''}</span>
					{:else}
						<span class="db-meta">{industryNodes.length || industryDetail.nodeCount}사{industryDetail.totalRevenue ? ` · ${(industryDetail.totalRevenue / 1e4).toFixed(1)}조` : ''}</span>
					{/if}
				</div>
			</div>
			<IndustryDrilldown
				nodes={industryNodes}
				links={industryLinks.map((l: any) => ({ ...l }))}
				onNodeClick={handleNodeClick}
			/>
		{:else if viewMode === 'treemap'}
			<TreemapView
				nodes={allNodes}
				industries={industries}
				{colorMetric}
				{colorFor}
				onNodeClick={handleTreemapClick}
				moversMap={showMoversOverlay ? moversSignalMap : new Map()}
				shockMap={shockImpactMap}
				timelineYear={selectedYear}
				timelineData={selectedYear ? (timelineData[selectedYear] || {}) : {}}
			/>
		{:else if viewMode === 'companies'}
			<EcosystemMap
				bind:this={mapRef}
				nodes={activeNodes}
				links={activeLinks}
				isAtlas={false}
				industriesProp={data.ecosystem.industries || []}
				industryFlows={data.ecosystem.industryFlows || []}
				onNodeClick={handleNodeClick}
				onIndustryClick={(indId) => enterIndustry(indId)}
			/>
		{/if}

		<!-- 업종 체력 카드 오버레이 -->
		{#if sectorHealthId && viewMode === 'atlas'}
			<SectorHealthCard
				industryId={sectorHealthId}
				industryName={sectorHealthName}
				stat={data.industryStats?.[sectorHealthId]}
				onDrilldown={() => { const id = sectorHealthId; sectorHealthId = null; if (id) enterIndustry(id); }}
				onClose={() => (sectorHealthId = null)}
			/>
		{/if}

		<!-- 충격 시뮬레이터 패널 -->
		{#if shockTargetId}
			<div class="shock-overlay">
				<ShockSimulator
					targetId={shockTargetId}
					targetName={shockTargetName}
					links={allLinks}
					nodes={allNodes}
					onImpactChange={(m) => (shockImpactMap = m)}
					onClose={() => { shockTargetId = null; shockImpactMap = new Map(); }}
				/>
			</div>
		{/if}

		<!-- 타임라인 바 (메인 뷰 하단 고정) -->
		{#if timelinePeriods.length > 1}
			<div class="timeline-bar">
				<span class="tl-icon" aria-hidden="true">
					<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="9" />
						<path d="M12 7v5l3 2" />
					</svg>
				</span>
				{#each timelinePeriods as yr}
					<button
						class="tl-btn"
						class:active={selectedYear === yr}
						onclick={() => (selectedYear = selectedYear === yr ? '' : yr)}
					>{yr}</button>
				{/each}
				<button
					class="tl-btn"
					class:active={!selectedYear}
					onclick={() => (selectedYear = '')}
				>현재</button>
				{#if selectedYear}
					<span class="tl-info">{selectedYear}년 · {Object.keys(timelineData[selectedYear] || {}).length}사</span>
				{/if}
			</div>
		{/if}
	</main>


	<!-- 오른쪽 상세: CompanyCard (회사 카드) -->
	{#if selectedNode && !selectedNode.isIndustry && isMobile}
		<aside class="detail-panel" class:wide={comparing}>
			<div class="card-slot">
				<CompanyCard
					basePath={base}
					node={selectedNode}
					detail={selectedDetail}
					loading={selectedDetailLoading}
					industryStat={data.industryStats?.[selectedNode.industry]}
					dataAsOf={data.meta?.dataAsOf}
					compareDisabled={comparing}
					onAddCompare={addToCompare}
					onDetach={detachCard}
					onShock={startShockSim}
					moverSignal={moversSignalMap.get(selectedNode.id) || null}
					onClose={() => handleNodeClick(null)}
				/>
			</div>
			{#if comparing && compareB}
				<div class="card-slot">
					<CompanyCard
						basePath={base}
						node={compareB}
						detail={compareBDetail}
						loading={false}
						industryStat={data.industryStats?.[compareB.industry]}
						dataAsOf={data.meta?.dataAsOf}
						compareDisabled={true}
						onDetach={detachCard}
						onClose={clearCompare}
					/>
				</div>
			{/if}
		</aside>
	{:else if selectedNode && selectedNode.isIndustry}
		<aside class="detail">
			<button class="close" onclick={() => (selectedNode = null)}>✕</button>
			<div class="detail-head">
				<h2>{selectedNode.label}</h2>
				<div class="badges">
					<span class="badge" style="background:{selectedNode.color}20; color:{selectedNode.color}">
						{selectedNode.industryName}
					</span>
				</div>
				<div class="big-stat">
					<span class="label">소속 회사</span>
					<span class="value">{selectedNode.nodeCount}사</span>
				</div>
				<div class="big-stat">
					<span class="label">산업 총 매출</span>
					<span class="value">{formatRev(selectedNode.revenue)}</span>
				</div>
				<div class="section">
					<button class="full-link" onclick={() => enterIndustry(selectedNode.industry)}>
						이 산업 내부 보기 →
					</button>
				</div>
			</div>
		</aside>
	{/if}
</div>

<CompareTray
	items={compareSet}
	maxItems={COMPARE_MAX}
	onRemove={removeFromCompare}
	onClear={clearCompareAll}
	onOpenFull={openCompareFull}
/>

<!-- 플로팅 카드 윈도우 (desktop only) -->
{#each floatingCards as fc (fc.id)}
	<FloatingCard
		id={fc.id}
		title={fc.node?.label || ''}
		subtitle="{fc.id} · {fc.node?.industryName || ''}"
		bind:x={fc.x}
		bind:y={fc.y}
		bind:w={fc.w}
		bind:h={fc.h}
		z={fc.z}
		onClose={() => closeFloating(fc.id)}
		onFocus={() => focusFloating(fc.id)}
		onMove={(x, y) => moveFloating(fc.id, x, y)}
		onResize={(w, h) => resizeFloating(fc.id, w, h)}
	>
		<CompanyCard
			basePath={base}
			node={fc.node}
			detail={fc.detail}
			loading={false}
			industryStat={data.industryStats?.[fc.node?.industry]}
			dataAsOf={data.meta?.dataAsOf}
			compareDisabled={true}
			detached={true}
			onDetach={detachCard}
			onShock={startShockSim}
			moverSignal={moversSignalMap.get(fc.id) || null}
			onClose={() => closeFloating(fc.id)}
		/>
	</FloatingCard>
{/each}

<MapCommandPalette
	open={cmdPaletteOpen}
	nodes={allNodes}
	onSelect={(code) => { isMobile ? handleNodeClick(nodeFinderById(code)) : detachCard(code); }}
	onClose={() => (cmdPaletteOpen = false)}
/>

<TutorialTour
	open={tourOpen}
	onClose={() => (tourOpen = false)}
	bind:colorMetric
	bind:viewMode
	enterIndustryAction={enterIndustry}
	selectCompanyAction={demoSelectCompany}
	addCompareAction={demoAddCompare}
	clearSelectionAction={demoClearSelection}
/>

<style>
	.map-page {
		display: grid;
		grid-template-columns: 280px 1fr;
		height: 100dvh;
		background: #050811;
		color: #f1f5f9;
		transition: grid-template-columns 0.2s;
		position: relative;
	}
	.map-page.sidebar-collapsed {
		grid-template-columns: 48px 1fr;
	}

	.collapse-toggle {
		position: absolute;
		top: 8px;
		left: calc(280px - 14px);
		width: 28px;
		height: 28px;
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 50%;
		color: #94a3b8;
		font-size: 12px;
		cursor: pointer;
		z-index: 3;
		display: flex;
		align-items: center;
		justify-content: center;
		transition: left 0.2s;
	}
	.map-page.sidebar-collapsed .collapse-toggle {
		left: calc(48px - 14px);
	}
	.collapse-toggle:hover {
		background: #1e2433;
		color: #f1f5f9;
	}

	.sidebar {
		display: flex;
		position: relative;
		flex-direction: column;
		overflow-x: hidden;
		overflow-y: auto;
		background: #0f1219;
		border-right: 1px solid #1e2433;
		padding: 16px 16px 64px;
		color: #f1f5f9;
		transition: width 0.2s, padding 0.2s;
		scrollbar-width: thin;
		scrollbar-color: #1e2433 transparent;
	}
	.sidebar::-webkit-scrollbar {
		width: 6px;
	}
	.sidebar::-webkit-scrollbar-track {
		background: transparent;
	}
	.sidebar::-webkit-scrollbar-thumb {
		background: #1e2433;
		border-radius: 3px;
	}
	.sidebar::-webkit-scrollbar-thumb:hover {
		background: #334155;
	}
	.sidebar.collapsed {
		padding: 8px 6px 16px;
		overflow: hidden;
	}
	.sidebar.collapsed > :not(.brand-bar):not(.collapse-toggle) {
		display: none;
	}
	.sidebar.collapsed .brand-bar {
		flex-direction: column;
		gap: 8px;
	}
	.sidebar.collapsed .brand-btn.help {
		margin-left: 0;
	}

	/* 브랜드 바: 모든 버튼 동일 크기/스타일 단색 라인 아이콘 */
	.brand-bar {
		display: flex;
		gap: 4px;
		align-items: center;
		padding-bottom: 12px;
		border-bottom: 1px solid #1e2433;
		margin-bottom: 12px;
	}
	.brand-btn {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		background: transparent;
		border: 1px solid transparent;
		border-radius: 6px;
		color: #94a3b8;
		text-decoration: none;
		cursor: pointer;
		transition: background 0.12s, border-color 0.12s, color 0.12s;
		padding: 0;
	}
	.brand-btn:hover {
		background: #1e2433;
		border-color: #334155;
		color: #f1f5f9;
	}
	.brand-btn.avatar {
		padding: 3px;
		overflow: hidden;
	}
	.brand-btn.avatar img {
		border-radius: 50%;
		width: 100%;
		height: 100%;
		object-fit: cover;
	}
	.brand-btn.help {
		margin-left: auto;
	}
	.freshness-row {
		padding-bottom: 8px;
		margin-bottom: 8px;
		border-bottom: 1px solid var(--color-dl-border);
	}
	.freshness-row :global(.compact) {
		flex-wrap: wrap;
		gap: 4px;
	}

	.header h1 {
		margin: 0 0 4px;
		font-size: 18px;
		font-weight: 800;
	}
	.brand-gradient {
		background: var(--dl-grad-heat);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		background-clip: text;
	}
	.header .sub {
		margin: 0;
		font-size: 12px;
		color: #94a3b8;
	}
	.crumb {
		background: none;
		border: none;
		color: #60a5fa;
		cursor: pointer;
		padding: 0;
		font-size: 12px;
	}
	.crumb:hover {
		text-decoration: underline;
	}

	.section {
		margin-top: 16px;
		padding-top: 16px;
		border-top: 1px solid #1e2433;
	}
	.section:first-of-type {
		border-top: none;
	}
	.section h3 {
		font-size: 11px;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 8px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.info-tip {
		color: #64748b;
		cursor: help;
		font-size: 11px;
		margin-left: 4px;
	}
	.info-tip:hover {
		color: #94a3b8;
	}

	/* 렌즈 (분석 관점) · 떠있는 오버레이 */
	.lens-overlay {
		position: absolute;
		top: 16px;
		left: 16px;
		display: flex;
		gap: 6px;
		padding: 6px;
		background: rgba(15, 18, 25, 0.85);
		border: 1px solid #1e2433;
		border-radius: 10px;
		backdrop-filter: blur(10px);
		-webkit-backdrop-filter: blur(10px);
		z-index: 5;
		box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
	}
	.lens-hint {
		font-size: 9px;
		color: #64748b;
		font-weight: 400;
		text-transform: none;
		letter-spacing: 0;
		margin-left: 6px;
	}
	.lens-chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		padding: 7px 12px;
		background: transparent;
		border: 1px solid transparent;
		border-radius: 7px;
		color: #94a3b8;
		font-size: 12px;
		font-weight: 600;
		cursor: pointer;
		transition: background 0.15s, border-color 0.15s, color 0.15s;
		white-space: nowrap;
	}
	.lens-chip:hover {
		background: rgba(96, 165, 250, 0.08);
		color: #f1f5f9;
	}
	.lens-chip.active {
		background: rgba(96, 165, 250, 0.18);
		border-color: rgba(96, 165, 250, 0.5);
		color: #f1f5f9;
		box-shadow: 0 0 12px rgba(96, 165, 250, 0.25);
	}
	.lens-icon {
		font-size: 11px;
		opacity: 0.9;
	}
	.lens-chip.active .lens-icon {
		color: #60a5fa;
		opacity: 1;
	}
	.lens-name {
		font-size: 12px;
	}

	/* 색상 기준 셀렉터 */
	.color-switch {
		background: rgba(234, 70, 71, 0.04);
		border-radius: 8px;
		padding: 10px 12px;
		margin-top: 16px;
		border: 1px solid rgba(234, 70, 71, 0.12);
	}
	.metric-select {
		width: 100%;
		padding: 6px 10px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #f1f5f9;
		font-size: 12px;
		cursor: pointer;
	}
	.metric-select:focus {
		outline: none;
		border-color: #34d399;
	}
	.color-legend {
		display: flex;
		align-items: center;
		gap: 3px;
		margin-top: 8px;
		font-size: 10px;
		color: #64748b;
	}
	.lg-swatch {
		width: 14px;
		height: 8px;
		border-radius: 2px;
		display: inline-block;
	}
	.lg-label {
		color: #94a3b8;
		margin: 0 4px;
	}
	/* 관점 셀렉터 */
	.view-switch {
		background: rgba(234, 70, 71, 0.03);
		border-radius: 8px;
		padding: 10px 12px;
		margin-top: 16px;
		border: 1px solid rgba(234, 70, 71, 0.1);
	}
	.view-tabs {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.view-tab {
		background: transparent;
		border: 1px solid transparent;
		color: #cbd5e1;
		padding: 8px 10px;
		border-radius: 6px;
		cursor: pointer;
		text-align: left;
		font-size: 13px;
		display: flex;
		flex-direction: row;
		align-items: center;
		gap: 10px;
	}
	.view-tab .tab-icon {
		width: 26px;
		height: 26px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		background: #1e2433;
		border-radius: 6px;
		flex-shrink: 0;
	}
	.view-tab.active .tab-icon {
		background: rgba(96, 165, 250, 0.25);
		color: #60a5fa;
	}
	.view-tab .tab-body {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	.view-tab .tab-title {
		font-weight: 500;
	}
	.view-tab.active .tab-title {
		font-weight: 600;
	}
	.view-tab:hover:not(:disabled) {
		background: rgba(96, 165, 250, 0.08);
		color: #f1f5f9;
	}
	.view-tab.active {
		background: linear-gradient(135deg, rgba(234, 70, 71, 0.12), rgba(251, 146, 60, 0.08));
		border-color: rgba(234, 70, 71, 0.4);
		color: #f1f5f9;
	}
	.view-tab.active .tab-icon {
		background: rgba(234, 70, 71, 0.2);
		color: #fb923c;
	}
	.view-tab:disabled {
		color: #475569;
		cursor: not-allowed;
	}
	.view-tab .hint {
		font-size: 10px;
		color: #64748b;
		font-weight: 400;
	}

	.controls button {
		font-size: 10px;
		padding: 2px 6px;
		background: #1e2433;
		color: #94a3b8;
		border: none;
		border-radius: 3px;
		cursor: pointer;
		margin-left: 4px;
	}
	.controls button:hover {
		background: #2a3142;
		color: #f1f5f9;
	}

	.search {
		width: 100%;
		padding: 8px 12px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		font-size: 13px;
		color: #f1f5f9;
	}
	.search::placeholder {
		color: #64748b;
	}

	.check {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		padding: 4px 0;
		cursor: pointer;
		color: #cbd5e1;
	}
	.check input {
		margin: 0;
	}
	.dot {
		width: 12px;
		height: 3px;
		border-radius: 2px;
	}
	.dot.supplier {
		background: #f97316;
	}
	.dot.affiliate {
		background: #d1d5db;
	}
	.dot.investor {
		background: #8b5cf6;
	}

	.range {
		display: block;
		font-size: 12px;
		color: #cbd5e1;
		margin-bottom: 8px;
	}
	.range input {
		width: 100%;
		margin-top: 4px;
	}

	.insight-box {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 8px;
		padding: 12px;
	}
	.insight-box h3 {
		margin: 0 0 10px;
	}
	.ins-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 8px;
	}
	.ins-cell {
		padding: 6px 8px;
		background: #0f1219;
		border-radius: 6px;
	}
	.ins-label {
		font-size: 10px;
		color: #94a3b8;
		margin-bottom: 2px;
	}
	.ins-value {
		font-size: 14px;
		font-weight: 600;
		color: #f1f5f9;
	}
	.ins-sub {
		margin-top: 8px;
		font-size: 11px;
		color: #64748b;
	}
	.ins-link {
		display: block;
		margin-top: 10px;
		padding: 6px 10px;
		background: rgba(96, 165, 250, 0.1);
		border: none;
		border-radius: 6px;
		color: #60a5fa;
		text-decoration: none;
		font-size: 12px;
		text-align: center;
		cursor: pointer;
		width: 100%;
	}
	.ins-link:hover {
		background: rgba(96, 165, 250, 0.2);
	}

	.industries ul,
	.stage-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.industries li,
	.stage-list li {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.atlas-item {
		display: flex;
		align-items: center;
		gap: 8px;
		background: transparent;
		border: none;
		color: #cbd5e1;
		font-size: 13px;
		padding: 5px 4px;
		width: 100%;
		cursor: pointer;
		text-align: left;
		border-radius: 4px;
	}
	.atlas-item:hover {
		background: rgba(96, 165, 250, 0.08);
		color: #f1f5f9;
	}
	.industry-item {
		padding: 3px 0;
		flex: 1;
	}
	.detail-link {
		background: none;
		border: none;
		color: #475569;
		text-decoration: none;
		font-size: 14px;
		padding: 2px 6px;
		border-radius: 4px;
		cursor: pointer;
	}
	.detail-link:hover {
		color: #60a5fa;
		background: rgba(96, 165, 250, 0.1);
	}
	.swatch {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.atlas-item .name,
	.industry-item .name,
	.stage-list .name {
		flex: 1;
	}
	.atlas-item .count,
	.industry-item .count,
	.stage-list .count {
		font-size: 11px;
		color: #64748b;
	}

	.map-main {
		position: relative;
		overflow: hidden;
	}

	/* 변화 감지 배너 */
	.movers-banner {
		position: absolute;
		top: 16px;
		right: 16px;
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 14px 10px 12px;
		background: rgba(5, 8, 17, 0.8);
		border: 1px solid rgba(251, 191, 36, 0.25);
		border-radius: 12px;
		color: rgba(241, 245, 249, 0.95);
		font-size: 12px;
		backdrop-filter: blur(16px) saturate(1.4);
		-webkit-backdrop-filter: blur(16px) saturate(1.4);
		box-shadow:
			0 1px 0 rgba(255, 255, 255, 0.04) inset,
			0 12px 32px -8px rgba(0, 0, 0, 0.6);
		z-index: 25;
		max-width: 440px;
	}
	.m-icon {
		font-size: 14px;
	}
	.m-text strong {
		color: #fbbf24;
	}
	.m-cta {
		color: #60a5fa;
		text-decoration: none;
		font-weight: 600;
		white-space: nowrap;
	}
	.m-cta:hover {
		color: #93c5fd;
	}
	.m-close {
		background: none;
		border: none;
		color: #64748b;
		cursor: pointer;
		font-size: 14px;
		padding: 0 4px;
	}
	.m-close:hover {
		color: #f1f5f9;
	}
	@media (max-width: 768px) {
		.movers-banner {
			font-size: 11px;
			max-width: calc(100% - 32px);
			padding: 6px 10px;
		}
		.m-text {
			display: none;
		}
	}

	.loading-overlay {
		position: absolute;
		inset: 0;
		display: flex;
		align-items: center;
		justify-content: center;
		background: rgba(5, 8, 17, 0.7);
		color: #cbd5e1;
		font-size: 14px;
		z-index: 10;
		backdrop-filter: blur(2px);
		text-align: center;
	}
	.loading-overlay .err {
		margin-top: 8px;
		color: #f87171;
		font-size: 12px;
		font-family: monospace;
		max-width: 600px;
	}
	.loading-overlay.error-overlay {
		background: rgba(127, 29, 29, 0.4);
	}
	.loading-overlay .retry {
		margin-top: 16px;
		padding: 6px 12px;
		background: rgba(96, 165, 250, 0.15);
		color: #60a5fa;
		border: 1px solid rgba(96, 165, 250, 0.4);
		border-radius: 6px;
		cursor: pointer;
		font-size: 12px;
	}
	.loading-overlay .retry:hover {
		background: rgba(96, 165, 250, 0.3);
	}

	/* Timeline Bar · 하단 중앙 editorial */
	.timeline-bar {
		position: absolute;
		bottom: 20px;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		align-items: center;
		gap: 2px;
		background: rgba(5, 8, 17, 0.85);
		backdrop-filter: blur(16px) saturate(1.4);
		-webkit-backdrop-filter: blur(16px) saturate(1.4);
		border: 1px solid rgba(255, 255, 255, 0.08);
		border-radius: 999px;
		padding: 6px 8px;
		z-index: 50;
		pointer-events: auto;
		box-shadow:
			0 1px 0 rgba(255, 255, 255, 0.04) inset,
			0 12px 32px -8px rgba(0, 0, 0, 0.6);
	}
	.tl-icon {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		margin-right: 4px;
		color: rgba(203, 213, 225, 0.5);
		font-size: 13px;
	}
	.tl-btn {
		background: transparent;
		border: none;
		color: rgba(148, 163, 184, 0.7);
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.04em;
		padding: 6px 12px;
		border-radius: 999px;
		cursor: pointer;
		transition:
			color 180ms ease,
			background 180ms ease,
			transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
		position: relative;
	}
	.tl-btn:hover {
		color: rgba(241, 245, 249, 0.95);
		background: rgba(255, 255, 255, 0.04);
	}
	.tl-btn.active {
		background: linear-gradient(
			135deg,
			var(--color-dl-primary) 0%,
			var(--color-dl-accent) 100%
		);
		color: #fff;
		font-weight: 700;
		box-shadow: 0 2px 8px rgba(234, 70, 71, 0.4);
	}
	.tl-info {
		font-family: var(--font-mono);
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.05em;
		color: rgba(148, 163, 184, 0.6);
		margin-left: 10px;
		padding-left: 10px;
		padding-right: 6px;
		border-left: 1px solid rgba(255, 255, 255, 0.08);
	}

	.overlay-toggles {
		padding: 8px 12px;
	}
	.overlay-toggle {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 12px;
		color: var(--color-dl-text-muted);
		cursor: pointer;
	}
	.overlay-toggle input {
		accent-color: var(--color-dl-primary);
	}

	/* Editorial Breadcrumb · 좌측 상단 고정 */
	.drill-breadcrumb {
		position: absolute;
		top: 16px;
		left: 16px;
		z-index: 30;
		display: flex;
		align-items: stretch;
		background: rgba(5, 8, 17, 0.75);
		backdrop-filter: blur(16px) saturate(1.4);
		-webkit-backdrop-filter: blur(16px) saturate(1.4);
		border: 1px solid rgba(255, 255, 255, 0.06);
		border-radius: 14px;
		padding: 0;
		box-shadow:
			0 1px 0 rgba(255, 255, 255, 0.04) inset,
			0 12px 32px -8px rgba(0, 0, 0, 0.6);
		overflow: hidden;
		animation: db-fade-in 280ms cubic-bezier(0.16, 1, 0.3, 1) both;
	}
	@keyframes db-fade-in {
		0% { opacity: 0; transform: translateY(-4px); }
		100% { opacity: 1; transform: translateY(0); }
	}
	.db-back {
		display: flex;
		align-items: center;
		gap: 8px;
		background: transparent;
		border: none;
		border-right: 1px solid rgba(255, 255, 255, 0.05);
		color: rgba(203, 213, 225, 0.7);
		padding: 12px 16px;
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: 11px;
		font-weight: 500;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		transition: color 180ms ease, background 180ms ease;
	}
	.db-back:hover {
		color: var(--color-dl-primary-light);
		background: linear-gradient(
			90deg,
			rgba(234, 70, 71, 0.12) 0%,
			rgba(234, 70, 71, 0) 100%
		);
	}
	.db-back svg {
		transition: transform 200ms cubic-bezier(0.16, 1, 0.3, 1);
	}
	.db-back:hover svg {
		transform: translateX(-3px);
	}
	.db-divider {
		display: none;
	}
	.db-current {
		display: flex;
		flex-direction: column;
		justify-content: center;
		padding: 10px 18px 10px 16px;
		position: relative;
		min-width: 160px;
	}
	/* 좌측에 산업 컬러 엑센트 바 */
	.db-current::before {
		content: '';
		position: absolute;
		left: 0;
		top: 20%;
		bottom: 20%;
		width: 2px;
		background: currentColor;
		opacity: 0.7;
		border-radius: 2px;
	}
	.db-name {
		color: inherit;
		font-size: 16px;
		font-weight: 700;
		letter-spacing: -0.01em;
		line-height: 1.1;
		font-family: 'Pretendard Variable', sans-serif;
	}
	.db-meta {
		font-family: var(--font-mono);
		font-size: 10px;
		color: rgba(148, 163, 184, 0.75);
		margin-top: 4px;
		letter-spacing: 0.04em;
		font-weight: 500;
	}

	.shock-overlay {
		position: absolute;
		bottom: 16px;
		right: 16px;
		width: 340px;
		z-index: 40;
	}

	.detail-panel {
		position: fixed;
		top: 0;
		right: 0;
		width: 440px;
		height: 100dvh;
		background: #0f1219;
		border-left: 1px solid #1e2433;
		overflow-y: auto;
		display: grid;
		grid-template-columns: 1fr;
		box-shadow: -4px 0 12px rgba(0, 0, 0, 0.5);
		z-index: 6;
	}
	.detail-panel.wide {
		width: 880px;
		grid-template-columns: 1fr 1fr;
	}
	.card-slot {
		border-right: 1px solid #1e2433;
		overflow-y: auto;
		max-height: 100dvh;
	}
	.detail-panel.wide .card-slot:last-child {
		border-right: none;
	}
	@media (max-width: 900px) {
		.detail-panel,
		.detail-panel.wide {
			width: 100%;
			grid-template-columns: 1fr;
		}
	}

	.detail {
		position: fixed;
		top: 0;
		right: 0;
		width: 360px;
		height: 100dvh;
		background: #0f1219;
		border-left: 1px solid #1e2433;
		padding: 16px;
		overflow-y: auto;
		box-shadow: -4px 0 12px rgba(0, 0, 0, 0.5);
		color: #f1f5f9;
	}
	.close {
		position: absolute;
		top: 12px;
		right: 12px;
		background: none;
		border: none;
		font-size: 18px;
		cursor: pointer;
		color: #64748b;
	}
	.close:hover {
		color: #f1f5f9;
	}
	.detail-head h2 {
		margin: 0;
		font-size: 20px;
		color: #f1f5f9;
	}
	.badges {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		margin-bottom: 12px;
	}
	.badge {
		font-size: 11px;
		padding: 2px 8px;
		border-radius: 4px;
		font-weight: 500;
	}
	.big-stat {
		background: #050811;
		padding: 12px;
		border-radius: 8px;
		margin-bottom: 10px;
		border: 1px solid #1e2433;
	}
	.big-stat .label {
		font-size: 11px;
		color: #94a3b8;
		display: block;
		margin-bottom: 4px;
	}
	.big-stat .value {
		font-size: 20px;
		font-weight: 600;
		color: #f1f5f9;
	}
	.full-link {
		display: inline-block;
		margin-top: 8px;
		color: #60a5fa;
		text-decoration: none;
		font-size: 13px;
		background: none;
		border: none;
		padding: 0;
		cursor: pointer;
	}
	.full-link:hover {
		text-decoration: underline;
	}

	@media (max-width: 768px) {
		.map-page {
			grid-template-columns: 1fr;
		}
		.sidebar {
			display: none;
		}
		.collapse-toggle {
			display: none;
		}
		.detail {
			width: 100%;
			top: auto;
			bottom: 0;
			height: 50vh;
			border-left: none;
			border-top: 1px solid #e5e7eb;
		}
	}
</style>
