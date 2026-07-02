<script lang="ts">
	// 일반(비전체화면) 모드 차트 크롬 · 기간 칩(좌상) + 드롭다운 4개(지표·그리기·표시·백테스트) + 전체화면.
	// 상태는 ChartCtl 단일 SSOT 공유 · 전체화면 리본(ChartRibbon)과 같은 인스턴스.
	import type { Lang } from '../lib/types';
	import { type ChartCtl, type IndexControl, OVERLAY_ALL, SUB_GROUPS, ECON_MAX, PERIODS, TFS, YMODES, CANDLES, DRAW_TOOLS, SUB_HINT, OVERLAY_HINT } from './chartState.svelte';
	import { MACRO_SERIES } from '@dartlab/ui-contracts';
	import { ECON_COLORS } from './econOverlay';
	import { MARKET_INDEX_COLORS } from '../lib/marketIndex';
	import { EVENT_CATS } from '../lib/eventRail';
	import { IND_DEFS, paramSummary } from './indicatorParams';
	import IndParamEditor from './IndParamEditor.svelte';

	interface Props {
		ctl: ChartCtl;
		lang: Lang;
		hasBand: boolean;
		railCatCounts?: Record<string, number>; // 이벤트 레일 카테고리별 건수 (필터 드롭다운 · 0 카테고리 숨김·카운트 표기)
		onDraw: (name: string) => void;
		onClearDraw: () => void;
		onSnapshot?: () => void; // PNG 저장 · 전체화면 전용 잠금 해제 (발견성)
		onCsv?: () => void; // 가격 시계열 CSV(표) 저장 · 부모가 활성 조건일 때만 넘김(index/HA/리플레이면 undefined=미렌더)
		subject?: 'price' | 'index'; // 'index' = BT·매물대 비활성(지수는 거래 대상 아님, 01 §4.2-4.3)
		indexLine?: boolean; // US 지수(종가전용) = candleStyle 'area' 고정(세그먼트 disabled, 01 §3.6)
		indexCtl?: IndexControl; // 주가/지수 토글 + 지수 picker (CenterStack 소유 → 컨트롤 바 한 줄에 통합)
		coMovers?: { id: string; corr: number; n: number }[]; // 종목↔거시 동행(상관) 순위 · ECON 메뉴 "동행 상위" (인과 아님)
		marketCoMovers?: { id: string; name: string; corr: number; n: number }[]; // 종목↔국내 시장지수 동행(베타) · 거시와 별도 행, 인과 아님
	}
	let { ctl, lang, hasBand, railCatCounts = {}, onDraw, onClearDraw, onSnapshot, onCsv, subject = 'price', indexLine = false, indexCtl, coMovers = [], marketCoMovers = [] }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	// 동행(상관) 우선순위 · coMovers 있으면 전 목록을 |corr| 내림차순 재배치(없으면 선언순). corr 없는 시리즈는 -1 로 하단.
	const corrById = $derived(new Map(coMovers.map((c) => [c.id, c])));
	const econOrdered = $derived.by(() => {
		const list = MACRO_SERIES.map((s) => ({ s, cm: corrById.get(s.id) ?? null }));
		if (!coMovers.length) return list;
		return list.sort((a, b) => (b.cm ? Math.abs(b.cm.corr) : -1) - (a.cm ? Math.abs(a.cm.corr) : -1));
	});
	// 지수 카탈로그 → 시장군 그룹(select optgroup, KOSPI/KOSDAQ/KRX/US 순) · "뭐가 있는지" 브라우징.
	const idxGroups = $derived.by(() => {
		const cat = indexCtl?.catalog ?? [];
		const order = ['KOSPI', 'KOSDAQ', 'KRX', 'US'];
		const lbl: Record<string, string> = { KOSPI: 'KOSPI', KOSDAQ: 'KOSDAQ', KRX: 'KRX', US: lang === 'en' ? 'US' : '미국' };
		const by = new Map<string, typeof cat>();
		for (const r of cat) { const m = String(r.market); if (!by.has(m)) by.set(m, []); by.get(m)!.push(r); }
		const keys = [...order.filter((m) => by.has(m)), ...[...by.keys()].filter((m) => !order.includes(m))];
		return keys.map((m) => ({ market: m, label: lbl[m] ?? m, items: [...by.get(m)!].sort((a, b) => a.name.localeCompare(b.name)) }));
	});
	const styleShown = $derived(indexLine ? 'area' : ctl.candleStyle); // US 지수면 'area'(라인) 강조 · disabled 세그먼트 정합
	let menu = $state<'none' | 'ind' | 'econ' | 'draw' | 'view' | 'rail'>('none');
	// ★전략 백테스트 = persistent dock (transient 드롭다운 menu 와 분리). 차트 클릭 auto-close 면제 →
	// 설정·차트 동시 가시(보면서 고침). 닫힘은 ✕·BT 토글뿐. (02 §1 persistent dock)
	let editing = $state<string | null>(null); // IND 메뉴 내 인라인 파라미터 편집 대상
	const hasParams = (k: string) => (IND_DEFS[k]?.params.length ?? 0) > 0;
	$effect(() => {
		if (menu !== 'ind') editing = null;
	});
</script>

<svelte:window onclick={() => (menu !== 'none' ? (menu = 'none') : null)} />

<!-- 차트 컨트롤 바 · 그래프 위 전용 행(absolute 오버레이 폐기, 밀도 배치). 좌=기간·봉주기, 우=지표·표시·BT 도구. -->
<div class="chartTopBar">
{#if indexCtl}
	<!-- 주체 토글 + 지수 picker · CenterStack indexCtl (한 줄 통합). 지수 시 검색 결과 칩 / 비면 큐레이트 9 그룹 칩. -->
	<span class="segGroup idxToggle">
		<button class={indexCtl.subject === 'price' ? 'seg on' : 'seg'} onclick={() => indexCtl.setSubject('price')}>{T('주가', 'Price')}</button>
		<button class={indexCtl.subject === 'index' ? 'seg on' : 'seg'} onclick={() => indexCtl.setSubject('index')}>{T('지수', 'Index')}</button>
	</span>
	{#if indexCtl.subject === 'index'}
		<!-- 지수 select · 시장군 그룹으로 전체(KR 165 + US) 브라우징(운영자: 뭐가 있는지 모름 → 목록). -->
		<select class="idxSelect mono" title={T('지수 선택', 'pick index')} onchange={(e) => { const r = indexCtl.catalog.find((x) => x.code === e.currentTarget.value); if (r) indexCtl.pick(r); }}>
			{#each idxGroups as g (g.market)}
				<optgroup label={g.label}>
					{#each g.items as r (r.code)}
						<option value={r.code} selected={indexCtl.indexRef?.code === r.code}>{r.name}</option>
					{/each}
				</optgroup>
			{/each}
		</select>
		<span class="cbDiv"></span>
	{/if}
{/if}
<!-- 기간 + 봉 주기 (좌) · segGroup 자체 위젯 (리본과 동일 패턴) -->
<div class="chartBar">
	<span class="segGroup" role="radiogroup">{#each PERIODS as p (p)}<button class={ctl.period === p ? 'seg on' : 'seg'} onclick={() => (ctl.period = p)}>{p}</button>{/each}</span>
	<span class="cbDiv"></span>
	<span class="segGroup" role="radiogroup">{#each TFS as t (t.v)}<button class={ctl.tf === t.v ? 'seg on' : 'seg'} disabled={ctl.btReportMode} title={ctl.btReportMode ? T('백테스트 · 일봉 고정', 'backtest · daily only') : T('봉 주기', 'timeframe')} onclick={() => !ctl.btReportMode && (ctl.tf = t.v)}>{T(t.kr, t.en)}</button>{/each}</span>
</div>

<!-- 우상 도구 -->
<div class="chartTools" onclick={(e) => e.stopPropagation()}>
	<!-- 경제지표(ECON) 를 보조지표(IND) 앞에 · 발견성 위계 우선(04 §4: 거시 맥락 먼저). econ=candle_pane 내부 indicator, sub=별도 pane 라 그리기 충돌 0. -->
	<div class="ctWrap">
		<button class={ctl.econ.length ? 'chartTool on' : 'chartTool'} onclick={() => (menu = menu === 'econ' ? 'none' : 'econ')} title={T('경제지표 겹쳐보기', 'Economy overlay')}>{T('경제지표', 'ECON')}</button>
		{#if menu === 'econ'}
			<div class="ctMenu ctMenuWide">
				<div class="ctMenuLbl">{T('경제지표 겹쳐보기 (최대 3 · 자기정규화)', 'Economy overlay (max 3 · self-scaled)')}</div>
					{#if marketCoMovers.length}
						<!-- 국내 시장지수 동행(베타) · 거시 driver 와 분리(지수 상관은 거의 최상위라 섞으면 거시를 가림). ⚠ 인과 아님. -->
						<div class="ctMenuLbl ctMenuGrp">{T('· 국내 시장 동행 (베타 · 인과 아님)', '· domestic market beta (not causation)')}</div>
						<div class="ctRow ctRowWrap">
							{#each marketCoMovers as mc (mc.id)}
								{@const mon = ctl.econ.includes(mc.id)}
								{@const mblocked = !mon && ctl.econ.length >= ECON_MAX}
								<button class={mon ? 'mItem on' : 'mItem'} disabled={mblocked}
									style={mon ? `background:transparent;color:${MARKET_INDEX_COLORS[mc.id]};border-color:${MARKET_INDEX_COLORS[mc.id]};font-weight:600` : ''}
									title={mblocked ? T('경제지표는 동시 3개까지', 'up to 3 economy series') : T(`최근 ${mc.n}개월 상관 ${mc.corr}`, `${mc.n}mo corr ${mc.corr}`)}
									onclick={() => ctl.toggleEcon(mc.id)}>{mc.name} <span class="coCorr" class:neg={mc.corr < 0}>{mc.corr > 0 ? '+' : ''}{mc.corr.toFixed(2)}</span></button>
							{/each}
						</div>
					{/if}
					{#if coMovers.length}
						<!-- 이 종목 월수익률과 상관 높은 순. ⚠ 상관일 뿐 인과(견인) 아님 · 가까운 봉 구간 기준. -->
						<div class="ctMenuLbl ctMenuGrp">{T('· 이 종목과 동행 상관 높은 순 (인과 아님)', '· ordered by co-movement with this stock (not causation)')}</div>
					{/if}
				<div class="ctRow ctRowWrap">
					{#each econOrdered as e (e.s.id)}
						{@const on = ctl.econ.includes(e.s.id)}
						{@const blocked = !on && ctl.econ.length >= ECON_MAX}
						<button class={on ? 'mItem on' : 'mItem'} disabled={blocked}
							style={on ? `background:transparent;color:${ECON_COLORS[e.s.id]};border-color:${ECON_COLORS[e.s.id]};font-weight:600` : ''}
							title={blocked ? T('경제지표는 동시 3개까지', 'up to 3 economy series') : e.cm ? T(`최근 ${e.cm.n}개월 상관 ${e.cm.corr}`, `${e.cm.n}mo corr ${e.cm.corr}`) : ''}
							onclick={() => ctl.toggleEcon(e.s.id)}>{T(e.s.kr, e.s.en)}{#if e.cm && Math.abs(e.cm.corr) >= 0.2} <span class="coCorr" class:neg={e.cm.corr < 0}>{e.cm.corr > 0 ? '+' : ''}{e.cm.corr.toFixed(2)}</span>{#if e.s.group} <span class="coGrp">{e.s.group}</span>{/if}{/if}</button>
					{/each}
				</div>
				{#if ctl.econ.length >= ECON_MAX}<div class="ctMenuLbl ctMenuGrp">{T('· 동시 3개까지 · 해제 후 추가', '· max 3 at once · remove one to add')}</div>{/if}
			</div>
		{/if}
	</div>
	<div class="ctWrap">
		<button class={ctl.overlays.length || ctl.subs.length ? 'chartTool on' : 'chartTool'} onclick={() => (menu = menu === 'ind' ? 'none' : 'ind')} title={T('보조지표 · 주가 오버레이 + 하단 페인', 'Indicators')}>{T('보조지표', 'IND')}</button>
		{#if menu === 'ind'}
			<div class="ctMenu ctMenuWide">
				<div class="ctMenuLbl">{T('주가 오버레이 (다중)', 'Price overlay (multi)')}</div>
				<div class="ctRow ctRowWrap">
					{#each OVERLAY_ALL as o (o)}
						{@const on = ctl.overlays.includes(o)}
						<button class={on ? 'mItem on' : 'mItem'} title={OVERLAY_HINT[o] ?? ''} onclick={() => ctl.toggleOverlay(o)}>{o}</button>
						{#if on && hasParams(o)}<button class="mItem mGear" title={T('파라미터', 'params')} onclick={() => (editing = editing === o ? null : o)}>⚙</button>{/if}
					{/each}
				</div>
				<div class="ctMenuLbl">{T('보조 지표 (다중)', 'Sub indicators (multi)')}</div>
				<!-- 활성 지표 상단 고정 (ON 칩 + ⚙ 파라미터) · 22종 평면벽 대신 SUB_GROUPS 조직(ChartRibbon:210-217 동일 패턴 이식, 04 §3). -->
				{#if ctl.subs.length}
					<div class="ctRow ctRowWrap">
						{#each ctl.subs as k (k)}
							<button class="mItem on" title={SUB_HINT[k] ?? ''} onclick={() => ctl.toggleSub(k)}>{k}</button>
							{#if hasParams(k)}<button class="mItem mGear" title={T('파라미터', 'params')} onclick={() => (editing = editing === k ? null : k)}>⚙</button>{/if}
						{/each}
					</div>
				{/if}
				{#each SUB_GROUPS as g (g.kr)}
					{@const avail = g.keys.filter((k) => !ctl.subs.includes(k))}
					{#if avail.length}
						<div class="ctMenuLbl ctMenuGrp">{T(g.kr, g.en)}</div>
						<div class="ctRow ctRowWrap">
							{#each avail as k (k)}
								<button class="mItem" title={SUB_HINT[k] ?? ''} onclick={() => ctl.toggleSub(k)}>{k}</button>
							{/each}
						</div>
					{/if}
				{/each}
				{#if editing}
					<IndParamEditor {ctl} {lang} name={editing} />
				{/if}
				{#if ctl.overlays.length || ctl.subs.length || ctl.econ.length}
					<div class="ctRow"><button class="mItem mClear" onclick={() => ctl.clearAllIndicators()}>{T('지표 전체 해제', 'Clear all')}</button></div>
				{/if}
			</div>
		{/if}
	</div>
	<div class="ctWrap">
		<button class={ctl.drawCount ? 'chartTool on' : 'chartTool'} onclick={() => (menu = menu === 'draw' ? 'none' : 'draw')} title={T('그리기', 'Draw')}>{T('그리기', 'DRAW')}</button>
		{#if menu === 'draw'}
			<div class="ctMenu">
				<div class="ctRow ctRowWrap">{#each DRAW_TOOLS as d (d.name)}<button class="mItem" onclick={() => { menu = 'none'; onDraw(d.name); }}>{T(d.kr, d.en)}</button>{/each}</div>
				<div class="ctRow"><button class={ctl.magnet ? 'mItem on' : 'mItem'} onclick={() => (ctl.magnet = !ctl.magnet)} title={T('가까운 봉에 스냅', 'snap to bar')}>{T('자석', 'Magnet')}</button><button class="mItem mClear" onclick={() => { menu = 'none'; onClearDraw(); }}>{T('전체 지우기', 'Clear')}</button></div>
			</div>
		{/if}
	</div>
	<div class="ctWrap">
		<button class={ctl.candleStyle !== 'candle_solid' || ctl.yMode !== 'normal' || ctl.showEvents || ctl.showBand || ctl.showRefs || ctl.showVP || !ctl.adj ? 'chartTool on' : 'chartTool'} onclick={() => (menu = menu === 'view' ? 'none' : 'view')} title={T('표시 설정', 'View')}>{T('표시', 'VIEW')}</button>
		{#if menu === 'view'}
			<div class="ctMenu">
				<div class="ctMenuLbl">{T('캔들', 'Candle')}</div>
				<div class="ctRow">{#each CANDLES as cs (cs.v)}<button class={styleShown === cs.v ? 'mItem on' : 'mItem'} disabled={indexLine} title={indexLine ? T('종가 전용 · 라인 고정', 'close-only · line') : ''} onclick={() => !indexLine && (ctl.candleStyle = cs.v)}>{T(cs.kr, cs.en)}</button>{/each}</div>
				<div class="ctMenuLbl">{T('Y축', 'Y axis')}</div>
				<div class="ctRow">{#each YMODES as y (y.v)}<button class={ctl.yMode === y.v ? 'mItem on' : 'mItem'} onclick={() => (ctl.yMode = y.v)}>{T(y.kr, y.en)}</button>{/each}</div>
				<div class="ctMenuLbl">{T('가격', 'Price')}</div>
				<div class="ctRow"><button class={ctl.adj ? 'mItem on' : 'mItem'} onclick={() => (ctl.adj = !ctl.adj)}>{T('수정주가', 'Adjusted')}</button><button class={ctl.showRefs ? 'mItem on' : 'mItem'} onclick={() => (ctl.showRefs = !ctl.showRefs)}>{T('52주·전일 기준선', '52w/prev refs')}</button><button class={ctl.showVP && subject !== 'index' ? 'mItem on' : 'mItem'} disabled={subject === 'index'} title={subject === 'index' ? T('지수는 매물대 없음', 'no volume profile for indices') : ''} onclick={() => subject !== 'index' && (ctl.showVP = !ctl.showVP)}>{T('매물대', 'Vol Profile')}</button></div>
				<div class="ctMenuLbl">{T('마커', 'Markers')}</div>
				<div class="ctRow"><button class={ctl.showEvents ? 'mItem on' : 'mItem'} onclick={() => (ctl.showEvents = !ctl.showEvents)}>{T('실적 발표', 'Earnings')}</button><button class={ctl.showBand ? 'mItem on' : 'mItem'} disabled={!hasBand} onclick={() => hasBand && (ctl.showBand = !ctl.showBand)}>{T('적정주가 밴드', 'Fair band')}</button></div>
			</div>
		{/if}
	</div>
	<div class="ctWrap">
		<button class={!ctl.railAllOn ? 'chartTool on' : 'chartTool'} onclick={() => (menu = menu === 'rail' ? 'none' : 'rail')} title={T('이벤트 레일 · 차트 하단 공시 종류 필터', 'Event rail · filter disclosures shown under the chart')}>{T('이벤트레일', 'RAIL')}</button>
		{#if menu === 'rail'}
			<div class="ctMenu">
				<div class="ctMenuLbl">{T('이벤트 레일 · 표시할 공시 종류', 'Event rail · types to show')}</div>
				<div class="ctRow ctRowWrap">
					<button class={ctl.railAllOn ? 'mItem on' : 'mItem'} onclick={() => ctl.showAllRailCats()}>{T('전체', 'All')}</button>
					{#each EVENT_CATS as c (c.key)}
						{#if (railCatCounts[c.key] ?? 0) > 0}
							<button class={ctl.railCatOn(c.key) ? 'mItem on' : 'mItem'} onclick={() => ctl.toggleRailCat(c.key)}>{T(c.kr, c.en)} <span class="dim">{railCatCounts[c.key]}</span></button>
						{/if}
					{/each}
				</div>
				<div class="ctMenuLbl">{T('· DART 공시그룹 근사 분류. 뉴스·다른 이벤트는 추후 추가', '· approx DART groups · news & more later')}</div>
			</div>
		{/if}
	</div>
	<div class="ctWrap">
		<button class={(ctl.btDockOpen || ctl.btStrategies.length) && subject !== 'index' ? 'chartTool on' : 'chartTool'} disabled={subject === 'index'} onclick={() => { if (subject === 'index') return; ctl.btDockOpen = !ctl.btDockOpen; ctl.btReportMode = ctl.btDockOpen; menu = 'none'; }} title={subject === 'index' ? T('지수는 거래 대상 아님', 'index not tradable') : T('전략 백테스트 · 차트 좌측 영구 패널(차트 조작해도 안 닫힘)', 'Strategy Lab · persistent left panel (survives chart interaction)')}>{T('백테스트', 'BT')}</button>
	</div>
	{#if onCsv}
		<button class="chartTool" onclick={() => onCsv?.()} title={T('가격 시계열 CSV(표) 저장 · 차트가 그리는 봉 그대로', 'save price CSV')} aria-label="csv">{T('표', 'CSV')}</button>
	{/if}
	<button class="chartTool" onclick={() => onSnapshot?.()} title={T('차트 PNG 저장 (출처 띠 포함)', 'save PNG')} aria-label="snapshot">
		<svg viewBox="0 0 16 16" width="12" height="12" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round" aria-hidden="true"><path d="M2 5h2.4L6 3.2h4L11.6 5H14v8H2z"/><circle cx="8" cy="8.6" r="2.5"/></svg>
	</button>
	<button class="chartTool" onclick={() => (ctl.full = true)} title={T('전체화면 (Shift+F)', 'Fullscreen (Shift+F)')} aria-label="fullscreen">{T('상세보기', 'detail')}</button>
</div>
</div>
