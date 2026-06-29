<script lang="ts">
	// 전체화면 전문가 리본 (증권사 HTS 상단 툴바 표준) — 2단 상시 노출.
	// Row1 = 보는 방법(종목·기간·캔들·축·마커·ECON), Row2 = 분석 작업대(오버레이/페인 활성 칩+카탈로그·그리기·BT).
	// 상태 = ChartCtl 단일 SSOT (일반 메뉴와 공유 — 리본에서 켠 지표가 일반 메뉴에도 켜져 있다).
	import type { Lang } from '../lib/types';
	import { type ChartCtl, type OverlayKey, type SubKey, OVERLAY_ALL, SUB_GROUPS, PERIODS, TFS, YMODES, CANDLES, SUB_HINT, OVERLAY_HINT } from './chartState.svelte';
	import { MACRO_SERIES } from '@dartlab/ui-contracts';
	import { ECON_COLORS } from './econOverlay';
	import { MARKET_INDEX_REFS, MARKET_INDEX_COLORS } from '../lib/marketIndex';
	import { EVENT_CATS } from '../lib/eventRail';
	import { CMP_COLORS } from './compareOverlay';
	import { paramSummary, IND_DEFS } from './indicatorParams';
	import { loadTemplates, saveTemplate, deleteTemplate, applyTemplate } from './templateStore';
	import IndParamEditor from './IndParamEditor.svelte';

	interface Props {
		ctl: ChartCtl;
		lang: Lang;
		hasBand: boolean;
		name: string;
		code: string;
		// 표시 시계열 기준 (리플레이 절단 반영 — PriceChart.ribbonInfo): 현재가·전일대비·기준일·52주
		info: { last: number; prev: number | null; date: string; hi: number; lo: number; live?: boolean; provider?: string; status?: string } | null;
		notice?: string | null; // 자동 tf 상향·백필 진행 등 상태 피드백 1줄
		peers?: { code: string; name: string }[];
		cmpRows?: { name: string; code: string; r: (number | null)[] }[]; // VS 팝오버 기간 수익률 (1M/3M/6M/1Y)
		railCatCounts?: Record<string, number>; // 이벤트 레일 카테고리별 건수 (필터 팝오버)
		canJump?: boolean;
		onSnapshot?: () => void;
		onReplay?: () => void; // 바 리플레이 진입 (시작점 환산은 PriceChart — viewLen 보유 주체)
		onJump?: () => void; // 심볼 점프 팔레트 열기 (⌘K·/)
		onHelp?: () => void; // 단축키 도움말 (?)
		subject?: 'price' | 'index'; // 'index' = BT·매물대·VS 비활성(지수, 01 §4.2-4.3·§5.1)
		indexLine?: boolean; // US 지수(종가전용) = candleStyle 'area' 고정(세그먼트 disabled, 01 §3.6)
	}
	let { ctl, lang, hasBand, name, code, info, notice = null, peers = [], cmpRows = [], railCatCounts = {}, canJump = false, onSnapshot, onReplay, onJump, onHelp, subject = 'price', indexLine = false }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const styleShown = $derived(indexLine ? 'area' : ctl.candleStyle); // US 지수면 'area'(라인) 강조 — disabled 세그먼트 정합
	const fmtN = (v: number) => v.toLocaleString('en-US', { maximumFractionDigits: 0 });
	const fmtD = (t: string) => /^\d{8}$/.test(t) ? `${t.slice(0, 4)}-${t.slice(4, 6)}-${t.slice(6, 8)}` : t.slice(0, 16).replace('T', ' ');
	const chg = $derived(info && info.prev ? ((info.last / info.prev) - 1) * 100 : null);
	const pos52 = $derived(info && info.hi > info.lo ? Math.max(0, Math.min(100, ((info.last - info.lo) / (info.hi - info.lo)) * 100)) : null);
	const quoteSource = $derived(!info?.live ? 'EOD' : info.provider === 'kis' ? 'KIS' : info.provider === 'naver' ? 'NAVER' : 'LIVE');
	const CMP_RET_LBL = ['1M', '3M', '6M', '1Y'];
	let pop = $state<string>('none'); // 'econ' | 'ovAdd' | 'subAdd' | 'bt' | 'vs' | 'tmpl' | `edit:${지표명}`
	const offOverlays = $derived(OVERLAY_ALL.filter((o) => !ctl.overlays.includes(o)));
	const hasParams = (k: string) => (IND_DEFS[k]?.params.length ?? 0) > 0;
	// 차트틀 — localStorage 다중 슬롯 (templateStore). 목록은 본 컴포넌트 로컬 미러.
	let templates = $state(loadTemplates());
	let tmplName = $state('');
	// 리본 실측 높이 → .chartWrap --crH — 좁은 창에서 리본이 3~4줄로 불어나 차트를 덮는
	// 기하 결함 수선 (고정 78px 패딩 폐지). DrawToolbar top 도 같은 변수를 쓴다.
	let ribbonEl = $state<HTMLElement | null>(null);
	let ribbonH = $state(0);
	$effect(() => {
		const h = ribbonH;
		const wrap = ribbonEl?.closest('.chartWrap') as HTMLElement | null;
		if (wrap && h > 0) wrap.style.setProperty('--crH', `${h}px`);
	});
</script>

<svelte:window onclick={() => (pop !== 'none' ? (pop = 'none') : null)} />
<header class="chartRibbon" bind:this={ribbonEl} bind:clientHeight={ribbonH} onclick={(e) => e.stopPropagation()}>
	<div class="crRow">
		<div class="crGrp crSym" role={canJump ? 'button' : undefined} tabindex={canJump ? 0 : undefined} title={canJump ? T('종목 점프 (⌘K · /)', 'symbol jump (⌘K · /)') : undefined}
			onclick={() => canJump && onJump?.()} onkeydown={(e) => canJump && e.key === 'Enter' && onJump?.()}>
			<b>{name}</b><span class="mono dim">{code}</span>{#if canJump}<span class="crJumpHint">⌄</span>{/if}
			{#if info}
				<span class="mono crLast">{fmtN(info.last)}</span>
				{#if chg != null}<span class={'mono ' + (chg >= 0 ? 'tUp' : 'tDn')}>{chg >= 0 ? '+' : ''}{chg.toFixed(1)}%{info.prev != null ? ` (${chg >= 0 ? '+' : '−'}${fmtN(Math.abs(info.last - info.prev))})` : ''}</span>{/if}
				<span class="crEod mono" title={info.live ? T(`웹 현재가 · ${info.status ?? '확인 중'}`, `web quote · ${info.status ?? 'unknown'}`) : T('일별 종가 기준(EOD) — 이 차트의 마지막 데이터 일자', 'end-of-day — last data date')}>{quoteSource} {fmtD(info.date)}</span>
				{#if pos52 != null}
					<span class="cr52" title={T(`52주 위치 ${pos52.toFixed(0)}% (저 ${fmtN(info.lo)} ~ 고 ${fmtN(info.hi)})`, `52w position ${pos52.toFixed(0)}%`)}>
						<i class="cr52Lbl">52W</i><span class="cr52Track"><span class="cr52Now" style={`left:${pos52}%`}></span></span>
					</span>
				{/if}
			{/if}
		</div>
		<div class="crGrp"><span class="segGroup" role="radiogroup">{#each PERIODS as p (p)}<button class={ctl.period === p ? 'seg on' : 'seg'} onclick={() => (ctl.period = p)}>{p}</button>{/each}</span></div>
		<div class="crGrp"><span class="segGroup" role="radiogroup">{#each TFS as t (t.v)}<button class={ctl.tf === t.v ? 'seg on' : 'seg'} disabled={ctl.btReportMode} title={ctl.btReportMode ? T('백테스트 — 일봉 고정', 'backtest — daily only') : T('봉 주기', 'timeframe')} onclick={() => !ctl.btReportMode && (ctl.tf = t.v)}>{T(t.kr, t.en)}</button>{/each}</span></div>
		<div class="crGrp"><span class="segGroup" role="radiogroup">{#each CANDLES as cs (cs.v)}<button class={styleShown === cs.v ? 'seg on' : 'seg'} disabled={indexLine} title={indexLine ? T('종가 전용 — 라인 고정', 'close-only — line') : ''} onclick={() => !indexLine && (ctl.candleStyle = cs.v)}>{T(cs.kr, cs.en)}</button>{/each}</span></div>
		<div class="crGrp"><span class="segGroup" role="radiogroup">{#each YMODES as y (y.v)}<button class={ctl.yMode === y.v ? 'seg on' : 'seg'} onclick={() => (ctl.yMode = y.v)}>{T(y.kr, y.en)}</button>{/each}</span></div>
		<div class="crGrp">
			<button class={ctl.adj ? 'cbtn tg on' : 'cbtn tg'} onclick={() => (ctl.adj = !ctl.adj)} title={T('수정주가 (분할·증자 보정)', 'adjusted price')}>{T('수정', 'ADJ')}</button>
			<button class={ctl.showEvents ? 'cbtn tg on' : 'cbtn tg'} onclick={() => (ctl.showEvents = !ctl.showEvents)} title={T('실적 발표 마커', 'earnings markers')}>{T('실적', 'EARN')}</button>
			<button class={ctl.showBand ? 'cbtn tg on' : 'cbtn tg'} disabled={!hasBand} onclick={() => hasBand && (ctl.showBand = !ctl.showBand)} title={T('적정주가 밴드', 'fair-value band')}>{T('밴드', 'BAND')}</button>
			<button class={ctl.showRefs ? 'cbtn tg on' : 'cbtn tg'} onclick={() => (ctl.showRefs = !ctl.showRefs)} title={T('52주 고저·전일종가 기준선', '52w hi/lo · prev close')}>{T('기준', 'REF')}</button>
			<button class={ctl.showVP && subject !== 'index' ? 'cbtn tg on' : 'cbtn tg'} disabled={subject === 'index'} onclick={() => subject !== 'index' && (ctl.showVP = !ctl.showVP)} title={subject === 'index' ? T('지수는 매물대 없음', 'no volume profile for indices') : T('매물대 (가시구간 거래대금 가중 + POC)', 'volume profile (visible range)')}>{T('매물대', 'VP')}</button>
		</div>
		<div class="crGrp crPop">
			<button class={ctl.compares.length && subject !== 'index' ? 'cbtn tg on' : 'cbtn tg'} disabled={subject === 'index'} onclick={() => subject !== 'index' && (pop = pop === 'vs' ? 'none' : 'vs')} title={subject === 'index' ? T('지수 비교는 추후', 'index compare later') : ''}>{T('종목비교', 'VS')} ▾</button>
			{#if pop === 'vs'}
				<div class="crMenu">
					<div class="ctMenuLbl">{T('종목비교 (최대 3 · % 축 자동)', 'Compare (max 3 · % axis)')}</div>
					<div class="ctRow ctRowWrap">
						{#if peers.length}
							{#each peers as p (p.code)}
								{@const ci = ctl.compares.findIndex((x) => x.code === p.code)}
								<button class={ci >= 0 ? 'mItem on' : 'mItem'}
									style={ci >= 0 ? `background:transparent;color:${CMP_COLORS[ci]};border-color:${CMP_COLORS[ci]};font-weight:600` : ''}
									onclick={() => ctl.toggleCompare(p)}>{p.name}</button>
							{/each}
						{:else}
							<span class="dim" style="font-size:9px">{T('동종업계 데이터 없음', 'no peer data')}</span>
						{/if}
					</div>
					{#if cmpRows.length}
						<!-- 기간 수익률 미니표 — 본주 + 선택 피어 (이미 로드한 캔들 재사용, 수정주가 동일 보정) -->
						<div class="ctMenuLbl">{T('기간 수익률 (수정주가 기준)', 'Period returns (adjusted)')}</div>
						<table class="cmpRetTbl mono">
							<thead><tr><th></th>{#each CMP_RET_LBL as l (l)}<th>{l}</th>{/each}</tr></thead>
							<tbody>
								{#each cmpRows as row, ri (row.code)}
									<tr>
										<td class="cmpRetNm" style={ri > 0 ? `color:${CMP_COLORS[ri - 1]}` : ''}>{row.name}</td>
										{#each row.r as v, i (i)}<td class={v == null ? 'dim' : v >= 0 ? 'tUp' : 'tDn'}>{v == null ? '—' : (v >= 0 ? '+' : '') + v.toFixed(1) + '%'}</td>{/each}
									</tr>
								{/each}
							</tbody>
						</table>
					{/if}
				</div>
			{/if}
		</div>
		<div class="crGrp crPop">
			<button class={ctl.econ.length ? 'cbtn tg on' : 'cbtn tg'} onclick={() => (pop = pop === 'econ' ? 'none' : 'econ')}>{T('경제지표', 'ECON')} ▾</button>
			{#if pop === 'econ'}
				<div class="crMenu">
					<div class="ctMenuLbl">{T('경제지표 (최대 3 · 자기정규화)', 'Economy (max 3 · self-scaled)')}</div>
					<div class="ctMenuLbl ctMenuGrp">{T('국내 시장 동행 (베타 · 인과 아님)', 'Domestic market beta (not causation)')}</div>
					<div class="ctRow ctRowWrap">
						{#each MARKET_INDEX_REFS as r (r.code)}
							<button class={ctl.econ.includes(r.code) ? 'mItem on' : 'mItem'}
								style={ctl.econ.includes(r.code) ? `background:transparent;color:${MARKET_INDEX_COLORS[r.code]};border-color:${MARKET_INDEX_COLORS[r.code]};font-weight:600` : ''}
								onclick={() => ctl.toggleEcon(r.code)}>{r.name}</button>
						{/each}
					</div>
					<div class="ctRow ctRowWrap">
						{#each MACRO_SERIES as s (s.id)}
							<button class={ctl.econ.includes(s.id) ? 'mItem on' : 'mItem'}
								style={ctl.econ.includes(s.id) ? `background:transparent;color:${ECON_COLORS[s.id]};border-color:${ECON_COLORS[s.id]};font-weight:600` : ''}
								onclick={() => ctl.toggleEcon(s.id)}>{T(s.kr, s.en)}</button>
						{/each}
					</div>
				</div>
			{/if}
		</div>
		<div class="crGrp crPop">
			<button class={!ctl.railAllOn ? 'cbtn tg on' : 'cbtn tg'} onclick={() => (pop = pop === 'rail' ? 'none' : 'rail')} title={T('이벤트 레일 — 하단 공시 종류 필터', 'event rail — filter disclosures')}>{T('이벤트레일', 'RAIL')} ▾</button>
			{#if pop === 'rail'}
				<div class="crMenu">
					<div class="ctMenuLbl">{T('이벤트 레일 — 표시할 공시 종류', 'Event rail — types to show')}</div>
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
		<div class="crGrp">
			{#if ctl.replay.on}
				<button class="cbtn" onclick={() => ctl.replayRestart()} title={T('시작점 복귀', 'restart')}>⏮</button>
				<button class="cbtn" onclick={() => ctl.replayStepBack()} title={T('한 봉 뒤로 (←)', 'step back (←)')}>◀</button>
				<button class={ctl.replay.playing ? 'cbtn on' : 'cbtn'} onclick={() => (ctl.replay.playing = !ctl.replay.playing)} title={T('재생/정지 (Space)', 'play/pause (Space)')}>{ctl.replay.playing ? '⏸' : '▶'}</button>
				<button class="cbtn" onclick={() => ctl.replayStep()} title={T('한 봉 전진 (→)', 'step (→)')}>▶▶</button>
				<button class="cbtn" onclick={() => (ctl.replayMs = ctl.replayMs === 400 ? 150 : 400)} title={T('재생 속도', 'speed')}>{ctl.replayMs === 400 ? '1×' : '2.5×'}</button>
				<span class="mono rpPos" title={T('리플레이 현재 봉 날짜', 'current replay bar')}>{info ? fmtD(info.date) : `${ctl.replay.idx + 1}/${ctl.replay.len}`}</span>
				<button class="cbtn" onclick={() => ctl.replayExit()} title={T('리플레이 종료 (R·ESC)', 'exit replay (R/ESC)')}>✕</button>
			{:else}
				<button class="cbtn" onclick={() => onReplay?.()} title={T('바 리플레이 (R) — 과거 시점부터 한 봉씩 재생', 'bar replay (R)')}>{T('리플레이', 'Replay')}</button>
			{/if}
		</div>
		{#if notice}<span class="crNotice">{notice}</span>{/if}
		<button class="crClose cbtn cIco" onclick={() => onHelp?.()} title={T('단축키·숨은 기능 (?)', 'shortcuts (?)')} aria-label="help">?</button>
		<button class="cbtn cIco" onclick={() => onSnapshot?.()} title={T('차트 PNG 저장 (S)', 'save PNG (S)')} aria-label="snapshot">
			<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linejoin="round"><path d="M2 5h2.4L6 3.2h4L11.6 5H14v8H2z"/><circle cx="8" cy="8.6" r="2.5"/></svg>
		</button>
		<button class="cbtn cIco" onclick={() => (ctl.full = false)} title={T('닫기 (F·ESC)', 'close (F/ESC)')} aria-label="exit fullscreen">
			<svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"><path d="M3.5 3.5l9 9M12.5 3.5l-9 9"/></svg>
		</button>
	</div>
	<div class="crRow">
		<div class="crGrp crChips">
			<span class="crLbl">{T('주가지표', 'OVERLAY')}</span>
			{#each ctl.overlays as k (k)}
				<span class="crPop crChipPair">
					<button class="crChip" title={OVERLAY_HINT[k] ?? ''} disabled={!hasParams(k)} onclick={() => (pop = pop === `edit:${k}` ? 'none' : `edit:${k}`)}>{k}{paramSummary(k, ctl.indParams[k])}</button>
					<button class="crChip x" title={T('제거', 'remove')} onclick={() => ctl.toggleOverlay(k)}>×</button>
					{#if pop === `edit:${k}`}<div class="crMenu"><IndParamEditor {ctl} {lang} name={k} onRemove={() => { ctl.toggleOverlay(k as OverlayKey); pop = 'none'; }} /></div>{/if}
				</span>
			{/each}
			<span class="crPop">
				<button class="crAdd" onclick={() => (pop = pop === 'ovAdd' ? 'none' : 'ovAdd')}>＋</button>
				{#if pop === 'ovAdd'}
					<div class="crMenu">
						<div class="ctRow ctRowWrap">{#each offOverlays as o (o)}<button class="mItem" title={OVERLAY_HINT[o] ?? ''} onclick={() => { ctl.toggleOverlay(o); pop = 'none'; }}>{o}{OVERLAY_HINT[o] ? ` ${OVERLAY_HINT[o]}` : ''}</button>{/each}</div>
					</div>
				{/if}
			</span>
		</div>
		<div class="crGrp crChips">
			<span class="crLbl">{T('보조지표', 'PANE')}</span>
			{#each ctl.subs as k (k)}
				<span class="crPop crChipPair">
					<button class="crChip" title={SUB_HINT[k] ?? ''} disabled={!hasParams(k)} onclick={() => (pop = pop === `edit:${k}` ? 'none' : `edit:${k}`)}>{k}{paramSummary(k, ctl.indParams[k])}</button>
					<button class="crChip x" title={T('제거', 'remove')} onclick={() => ctl.toggleSub(k)}>×</button>
					{#if pop === `edit:${k}`}<div class="crMenu"><IndParamEditor {ctl} {lang} name={k} onRemove={() => { ctl.toggleSub(k as SubKey); pop = 'none'; }} /></div>{/if}
				</span>
			{/each}
			<span class="crPop">
				<button class="crAdd" onclick={() => (pop = pop === 'subAdd' ? 'none' : 'subAdd')}>＋</button>
				{#if pop === 'subAdd'}
					<div class="crMenu crMenuWideR">
						{#each SUB_GROUPS as g (g.kr)}
							<div class="ctMenuLbl">{T(g.kr, g.en)}</div>
							<div class="ctRow ctRowWrap">
								{#each g.keys.filter((k) => !ctl.subs.includes(k)) as k (k)}
									<button class="mItem" onclick={() => { ctl.toggleSub(k); pop = 'none'; }}>{k}{SUB_HINT[k] ? ` ${SUB_HINT[k]}` : ''}</button>
								{/each}
							</div>
						{/each}
					</div>
				{/if}
			</span>
		</div>
		<div class="crGrp">
			<!-- BT = 차트 좌측 영구 도크(StrategyDock) 토글. 전체화면에서도 도크가 차트 좌측에 마운트(차트는 안 건드림·일봉 안내는 도크 안). -->
			<button class={(ctl.btDockOpen || ctl.btStrategies.length) && subject !== 'index' ? 'crChip on' : 'crAdd'} disabled={subject === 'index'} title={subject === 'index' ? T('지수는 거래 대상 아님', 'index not tradable') : T('전략 백테스트 — 차트 좌측 영구 패널', 'Strategy backtest — persistent left panel')} onclick={() => { if (subject === 'index') return; ctl.btDockOpen = !ctl.btDockOpen; ctl.btReportMode = ctl.btDockOpen; pop = 'none'; }}>
				{ctl.btStrategies.length ? T('전략 백테스트', 'Backtest') : `＋ ${T('전략 백테스트', 'Backtest')}`}
			</button>
		</div>
		<div class="crGrp crPop">
			<button class={templates.length ? 'cbtn on' : 'cbtn'} onclick={() => (pop = pop === 'tmpl' ? 'none' : 'tmpl')} title={T('차트틀 — 지표·축·봉주기 설정 저장/적용', 'chart templates')}>{T('틀', 'TMPL')} ▾</button>
			{#if pop === 'tmpl'}
				<div class="crMenu crMenuR">
					<div class="ctMenuLbl">{T('차트틀 (지표·파라미터·축·캔들·봉주기 · 최대 12)', 'Templates (indicators · axis · tf · max 12)')}</div>
					<input
						class="tmplInput"
						placeholder={T('현재 설정 이름 입력 후 Enter', 'name current setup + Enter')}
						bind:value={tmplName}
						onkeydown={(e) => {
							if (e.key === 'Enter' && tmplName.trim()) {
								templates = saveTemplate(ctl, tmplName.trim());
								tmplName = '';
							}
						}}
					/>
					{#each templates as t (t.name)}
						<div class="tmplRow">
							<button class="mItem" title={`${t.overlays.join('·') || '—'} / ${t.subs.join('·') || '—'} · ${t.tf}`} onclick={() => { applyTemplate(ctl, t); pop = 'none'; }}>{t.name}</button>
							<button class="crChip x" title={T('삭제', 'delete')} onclick={() => (templates = deleteTemplate(t.name))}>×</button>
						</div>
					{:else}
						<span class="dim" style="font-size:9px">{T('저장된 틀 없음 — 위에 이름 입력', 'no templates yet')}</span>
					{/each}
				</div>
			{/if}
		</div>
	</div>
</header>
