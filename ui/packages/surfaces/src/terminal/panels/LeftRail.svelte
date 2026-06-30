<script lang="ts">
	import type { Candle } from '@dartlab/ui-contracts';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { Engine, IndustryMacro } from '../lib/engine';
	import ScatterMap, { type ScatterPt } from './ScatterMap.svelte';
	import type { EcoNode, Lang } from '../lib/types';
	import Panel from '../ui/Panel.svelte';
	import ScreenerModal from './ScreenerModal.svelte';
	import FinTypeLegendDialog from './FinTypeLegendDialog.svelte'; // 유형 칩 범례 · TYPE 컬럼 ⓘ 에서 연다
	import Watchlist from './Watchlist.svelte'; // 공시 워치 · 큐레이션 종목 신선도 모니터 (recentMap 공유)
	import MarketFeed from './MarketFeed.svelte'; // 시장 공시 피드 · 전상장사 3개월 수시공시(워치=내 종목 / 피드=시장 전체)
	import MacroRegimePanel from './MacroRegimePanel.svelte'; // 거시 국면 글랜스 · 좌측 최상단(깔때기 꼭대기)
	import MacroRegimeDialog from './MacroRegimeDialog.svelte'; // 거시 국면 상세 · 판정·모델·고밀도 지표차트
	import { buildMacroGlanceView, buildRegimeView } from '../lib/macroLens'; // 국면 view-model (macro.json 라이브)
	import { computeMacroSim } from '../lib/macroSimCompute'; // 거시 전망 BVAR · 브라우저 런타임 계산(별도 배선·발행 0)
	import { watchlist } from '../lib/watchlist.svelte'; // 워치 카운트 · 하단 탭 라벨 배지
	import { finTypeOf, displayPair } from '../lib/finType'; // 재무 유형 라벨 SSOT (기준=data/finType.ts 한 곳)
	import { chgClass, sign, sparkPts } from '../ui/helpers';

	interface Props {
		eng: Engine;
		lang: Lang;
		active: string;
		onPick: (code: string) => void;
		onIndustry?: (id: string) => void; // 산업 sweep 행 클릭 → IndustryDialog
		onFilingSearch?: () => void; // 공시 본문 검색(⌘⇧F) 다이얼로그 열기 · 시장공시 피드 위 트리거
		sectorFilter: string;
		bottomTab: 'screener' | 'watch';
		onSectorFilter: (id: string) => void;
		onBottomTab: (tab: 'screener' | 'watch') => void;
	}
	let { eng, lang, active, onPick, onIndustry, onFilingSearch, sectorFilter, bottomTab, onSectorFilter, onBottomTab }: Props = $props();
	const rt = useDartLabRuntime();
	const base = rt.env.basePath;
	const tcls = (t: string) => (({ up: 'tUp', good: 'tGood', neutral: 'tNeu', warn: 'tWarn', down: 'tDn' }) as Record<string, string>)[t] || 'tNeu';

	// ── 거시 국면 · 좌측 최상단 글랜스(econoVision 개념: 판정+근거+확신도). 데이터 = macro.json 라이브(이미 산출). ──
	// 옛 마켓펄스(RegimeQuadrant 2점 격자)가 버린 quadrant·assets·confidence·전이를 살린다. 깊이는 다이얼로그.
	const macro = $derived(eng.raw.macro);
	const macroTailwinds = $derived(eng.sectorTailwinds());
	const macroGlance = $derived(buildMacroGlanceView(macro, macroTailwinds, { mode: 'compact' }));
	const regimeView = $derived(buildRegimeView(macro, null));
	let macroOpen = $state(false);
	// 거시 전망 시뮬 · 런타임 BVAR(이미 로드된 raw observations). HF publish·별도 데이터 배선 0.
	// getSeriesRaw = yoy 미적용 원시 index(Python 엔진과 동일 입력 → fan parity).
	const loadSim = (m: 'KR' | 'US') => computeMacroSim(m, (id) => rt.macro.getSeriesRaw(id));

	// scan 와 동일 universe: finance+prices 보유 회사 (eng 불변 → 1 회 산출 후 캐시)
	const nodes = $derived(
		(eng.raw.eco?.nodes || []).filter((n) => eng.raw.finance.companies[n.id] && eng.priceOf(n.id))
	);
	// 소문자 회사명 사전 · 키 입력마다 nameOf().toLowerCase() 재계산 방지 (1 회 산출)
	const lowerNames = $derived(new Map(nodes.map((n) => [n.id, (eng.nameOf(n.id) || '').toLowerCase()])));

	// ── 통합 스크리너: 스파크라인(30거래일) + 1Y 수익률 + 유형 라벨 2칩 한 행 (제품급 조건검색기).
	// ROE·영업이익 수치 컬럼은 라벨(finType 체인)로 대체 · 수치 다조건은 상세검색 모달 소관. ──
	let screenerOpen = $state(false);
	let finLegendOpen = $state(false); // 유형 칩 범례 다이얼로그
	// 30거래일 스파크 · recent.parquet 전종목 1파일 (티커 스트립과 어댑터 캐시 공유, 추가 다운로드 0)
	let recentMap = $state<Record<string, Candle[]> | null>(null);
	rt.price.govRecent().then((m) => (recentMap = m));

	// 조건 검색 · query 즉시 반영(입력 반응성) + queryD 140ms 디바운스(무거운 rows 재계산 억제)
	let query = $state('');
	let queryD = $state('');
	$effect(() => {
		const q = query;
		const t = setTimeout(() => (queryD = q), 140);
		return () => clearTimeout(t);
	});
	let market = $state(''); // '' | 'KOSPI' | 'KOSDAQ'
	const MKT: Record<string, string> = { KOSPI: '유가증권', KOSDAQ: '코스닥' };
	const matchFilter = (n: EcoNode): boolean => {
		if (queryD) {
			const q = queryD.trim().toLowerCase();
			const name = lowerNames.get(n.id) || '';
			if (!name.includes(q) && !n.id.includes(queryD.trim())) return false;
		}
		if (market && n.market !== MKT[market]) return false;
		if (sectorFilter && n.industry !== sectorFilter) return false;
		return true;
	};
	// 정렬 = 1Y 수익률 단일 (prices). 수치 다조건 정렬·필터는 상세검색 모달이 담당.
	const r1yOf = (n: EcoNode): number | null => { const px = eng.priceOf(n.id); return px ? ((px.return1y as number | null) ?? null) : null; };
	interface Row { n: EcoNode; r1y: number | null; }
	const rows = $derived(
		nodes
			.filter(matchFilter)
			.map((n): Row => ({ n, r1y: r1yOf(n) }))
			.filter((r) => r.r1y != null)
			.sort((a, b) => (b.r1y as number) - (a.r1y as number))
			.slice(0, 80)
	);

	const setSector = (id: string) => onSectorFilter(id);

	// ── 산업 sweep · 거시 깔때기 산업층. 34산업을 선택 렌즈로 cross-section 비교(섹터 시세 히트맵 대체). ──
	// 전부 baked 합성(industryStats·ecosystem·gov 시총), 새 fetch 0. 측정근거=_attempts/macroIndustrySweep.
	const industryIds = $derived([...new Set((eng.raw.eco?.nodes || []).map((n) => n.industry))]);
	const sweepAll = $derived(industryIds.map((id) => eng.industryMacro(id)).filter((m): m is IndustryMacro => m != null));
	// 미니 지형도 · 산업 = (영업이익률 중앙값 × 마진 격차 IQR). 위치=구조 관측. 현재 종목 산업 강조·클릭=스크리너 필터+상세.
	const industryPts = $derived.by((): ScatterPt[] =>
		sweepAll
			.filter((s) => s.count >= 10 && s.dist.opMargin?.median != null && s.dist.revCagr?.median != null)
			.map((s) => ({ id: s.id, x: s.dist.opMargin!.median, y: s.dist.revCagr!.median, size: s.count, label: lang === 'en' ? s.en : s.kr, faint: s.count < 15 }))
	);
	const curIndustry = $derived(sectorFilter || (eng.raw.eco?.nodes || []).find((n) => n.id === active)?.industry || '');
	const activeSectorName = $derived(sectorFilter ? (sweepAll.find((s) => s.id === sectorFilter)?.kr || sectorFilter) : '');
	function pickIndustry(id: string) {
		setSector(id); // 스크리너 필터(기존 깔때기) · 한 번 더 누르면 해제
		onIndustry?.(id); // IndustryDialog 열기(신규)
	}
</script>

<!-- 거시 국면 · 깔때기 꼭대기(매크로→산업→종목). 판정 1줄+근거+확신도 글랜스, 깊이는 다이얼로그(모델·고밀도 지표차트). -->
{#if macro}
	<Panel {lang} className="eMacro" title={{ kr: '거시 국면', en: 'MACRO REGIME' }}>
		{#snippet right()}
			<button class="finFullBtn" onclick={() => (macroOpen = true)} title={lang === 'en' ? 'detail · models & charts' : '상세보기 · 모델·지표차트'}>{lang === 'en' ? 'detail' : '상세보기'}</button>
		{/snippet}
		<MacroRegimePanel regime={macroGlance.regime} {lang} />
	</Panel>
{/if}

<!-- 산업 sweep · 거시 깔때기 산업층(매크로→★산업→종목). 패널 = 미니 지형도(읽기 아닌 *시각화*).
     전 산업을 (수익 수준×마진 격차) 점구름으로 · 현재 산업 강조·클릭=스크리너 필터+상세. 상세는 다이얼로그. -->
<Panel {lang} className="eIndustry" prov="real" title={{ kr: '산업 스윕', en: 'INDUSTRY SWEEP' }} sub={{ kr: '구조 · 클릭=상세', en: 'structure · click=detail' }}>
	{#snippet right()}
		<button class="finFullBtn" onclick={() => onIndustry?.('')} title={lang === 'en' ? 'detail · all industries' : '상세보기 · 전체 산업'}>{lang === 'en' ? 'detail' : '상세보기'}</button>
	{/snippet}
	<div class="swMap">
		<ScatterMap pts={industryPts} compact compactH={132} highlightId={curIndustry} onPick={pickIndustry} xLabel="" yLabel="" zeroX />
	</div>
</Panel>

<!-- 시장 공시 피드 · 산업 아래 *전상장사* 최근 3개월 수시공시. 우측 단일기업/좌측 워치(내 종목)와 다른
     시장 전체 멘탈모델. 공시 본문 검색(⌘⇧F)은 이 패널 헤더 아래로 배치(읽기↔찾기 한 쌍). 고정높이·내부 스크롤. -->
<MarketFeed {lang} {active} {onPick} {onFilingSearch} />

<!-- 하단 통합 · 스크리너 ⇄ 공시 워치 탭. 워치가 무한 증가해 스크리너를 가리던 문제 해소
     (한 자리를 탭으로 공유 · 각 탭이 잔여 높이 전부 차지 · 내부 스크롤). 탭 바가 패널 헤더 역할. -->
<section class="panel eQuant fillCol">
	<header class="panelHead leftTabHead">
		<button class={'leftTab' + (bottomTab === 'screener' ? ' on' : '')} onclick={() => onBottomTab('screener')}>{lang === 'en' ? 'SCREENER' : '스크리너'}</button>
		<button class={'leftTab' + (bottomTab === 'watch' ? ' on' : '')} onclick={() => onBottomTab('watch')}>{lang === 'en' ? 'WATCH' : '공시 워치'}{#if watchlist.count}<span class="leftTabN">{watchlist.count}</span>{/if}</button>
		<span class="panelRight">
			{#if bottomTab === 'screener'}<button class="scrOpenBtn" onclick={() => (screenerOpen = true)} title="상용급 다조건 검색">{lang === 'en' ? 'SCREEN' : '상세검색'}</button><a class="lensScan" href="{base}/scan" target="_blank" rel="noopener" title="전체 조건 조사 · scan 보드">{lang === 'en' ? 'scan ↗' : '조건조사 ↗'}</a>{/if}
		</span>
	</header>
	<div class="panelBody flush">
		{#if bottomTab === 'screener'}
			<div class="filtRow">
				<input class="filtInput" placeholder={lang === 'en' ? 'name/code' : '이름·코드'} bind:value={query} spellcheck={false} />
				<select class="filtSel" bind:value={market}><option value="">{lang === 'en' ? 'all market' : '전체 시장'}</option><option value="KOSPI">KOSPI</option><option value="KOSDAQ">KOSDAQ</option></select>
			</div>
			{#if sectorFilter}
				<div class="filtChipRow"><button class="filtChip" onclick={() => setSector(sectorFilter)}>{lang === 'en' ? 'sector: ' : '섹터: '}{activeSectorName} ✕</button></div>
			{/if}
			<!-- 컬럼 헤더 · 정렬 1Y 고정 (수치 다조건은 상세검색) -->
			<div class="rkHead">
				<span class="rkHN">#</span>
				<span class="rkHName">{lang === 'en' ? 'Company' : '종목'}</span>
				<span class="rkHCol">{lang === 'en' ? '30D' : '추세'}</span>
				<span class="rkHCol on">1Y ▼</span>
				<button class="rkHCol rkHType" onclick={() => (finLegendOpen = true)} title={lang === 'en' ? 'What these type labels mean · criteria' : '유형 라벨 기준 보기'}>{lang === 'en' ? 'TYPE' : '유형'} <span class="rkHTypeI">ⓘ</span></button>
			</div>
			<div class="rankList">
				{#each rows as r, i (r.n.id)}
					{@const fts = displayPair(finTypeOf(r.n, eng.raw.finance.companies[r.n.id], eng.priceOf(r.n.id)))}
					{@const sp = recentMap?.[r.n.id]}
					<div class={'rankRow' + (active === r.n.id ? ' on' : '')} role="button" tabindex="0" onclick={() => onPick(r.n.id)} onkeydown={(e) => e.key === 'Enter' && onPick(r.n.id)}>
						<span class="rkN mono">{i + 1}</span>
						<span class="rkName"><b>{eng.nameOf(r.n.id)}</b><span class="rkInd">{r.n.industryName || ''}</span></span>
						<span class="rkSpark">{#if sp && sp.length > 1}<svg class={chgClass(r.r1y)} viewBox="0 0 34 11" preserveAspectRatio="none" aria-hidden="true"><polyline points={sparkPts(sp.map((k) => k.c))} fill="none" stroke="currentColor" stroke-width="1.1" /></svg>{/if}</span>
						<span class={'rkCol mono ' + chgClass(r.r1y)}>{r.r1y == null ? '·' : sign(r.r1y, 0) + '%'}</span>
						<span class="rkChips">
							{#each fts as ft (ft.name)}<span class={'rkChip ' + tcls(ft.tone)} title={ft.criteriaKr}>{ft.name}</span>{/each}
						</span>
					</div>
				{/each}
			</div>
		{:else}
			<Watchlist bare {eng} {lang} {active} {onPick} {recentMap} />
		{/if}
	</div>
</section>

<ScreenerModal {eng} {lang} open={screenerOpen} onClose={() => (screenerOpen = false)} onPick={(c) => { onPick(c); screenerOpen = false; }} />
{#if finLegendOpen}<FinTypeLegendDialog {lang} onClose={() => (finLegendOpen = false)} />{/if}
{#if macroOpen && macro}<MacroRegimeDialog {macro} regime={macroGlance.regime} {regimeView} {lang} loadSeries={(id) => rt.macro.getSeries(id)} {loadSim} onClose={() => (macroOpen = false)} />{/if}
