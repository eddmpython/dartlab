<script lang="ts">
	// 백테스트 보고서 · 다이얼로그 폐기, CenterStack 하단(재무그래프 자리) 인라인 tearsheet. 차트는 위에 고정·공시.
	// 탭 아닌 스택 섹션(거래표 spine 상시) + 정직 헤더 띠(증거등급·명세스탬프). 단일종목 변형(시장=동일엔진·index벤치, 유니버스=별도 본문).
	// BacktestDialog 본문 도출 그대로 흡수(eq/bhq/dd/oosDecay/tradeStats/cumPct/worstTrades) · 새 통계 0, 재배치.
	import type { PortfolioBtResult, StrategySlot, BtFullRef } from '../lib/backtest';
	import { GOV_ATTRIBUTION } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';
	import EquityChart from './EquityChart.svelte';
	import { tradeShuffleCone } from './tradeShuffle';
	import MonthlyReturnsHeatmap from './MonthlyReturnsHeatmap.svelte';
	import TradeScatter from './TradeScatter.svelte';
	import YearlyReturnsBars from './YearlyReturnsBars.svelte';
	import ReturnHistogram from './ReturnHistogram.svelte';

	interface Props {
		pf: PortfolioBtResult;
		slots: StrategySlot[];
		focus: number;
		period: string;
		withCosts: boolean;
		adjusted: boolean;
		candleTs: string[];
		scope: 'single' | 'market' | 'universe';
		fullRef?: BtFullRef | null; // 커스텀 구간 전체기간 대조(G3 체리피킹 가드) · 있으면 '이 구간 vs 전체' 배너
		lang: Lang;
		onFocus: (i: number) => void;
		onFocusBar?: (t: string) => void;
		onBack: () => void; // 재무그래프로 복귀(모드 끔)
		tearsheetOpen?: boolean; // 무거운 통계(자산곡선·MC·월별·분포·MAE·보조지표) 접힘 · 상시 도크(밴드·히어로·매매표)와 분리
		onToggleTearsheet?: () => void;
		hoverTs?: string | null; // 차트 crosshair 가 거래봉 위면 그 진입일(YYYYMMDD) · 그 매매행 co-highlight (역 hover-sync)
	}
	let { pf, slots, focus, period, withCosts, adjusted, candleTs, scope, fullRef = null, lang, onFocus, onFocusBar, onBack, tearsheetOpen = false, onToggleTearsheet, hoverTs = null }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	const focusId = $derived(slots[focus]?.id ?? slots[0]?.id);
	const result = $derived(pf.slots.find((s) => s.id === focusId)?.result ?? pf.slots[0].result);
	const stratColor = $derived(slots.find((s) => s.id === focusId)?.color ?? '#fbbf24');
	const combo = $derived(pf.combo);
	const multi = $derived(pf.slots.length >= 2);
	const metaOf = (id: string) => slots.find((s) => s.id === id);
	const idxOf = (id: string) => slots.findIndex((s) => s.id === id);
	const m = $derived(result.metrics);
	const rs = $derived(result.runSpec);
	const oos = $derived(result.oos);
	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const cls = (v: number) => (v > 0 ? 'tUp' : v < 0 ? 'tDn' : 'tNeu');
	const fmtD = (t: string) => (t && t.length >= 8 ? `${t.slice(0, 4)}.${t.slice(4, 6)}.${t.slice(6, 8)}` : '·');
	const num = (v: number, d = 0) => v.toLocaleString('en-US', { maximumFractionDigits: d });
	const beats = $derived(m.retPct >= result.bh.retPct);
	// 경고 enum → 한국어 라벨(영문 토큰 누수 차단). BtChip WARN_TOKEN 과 동일 어휘.
	const warnLabel = (k: string) => (k === 'splitSuspect' ? T('분할의심', 'split?') : k === 'shortRange' ? T('기간 부족', 'short range') : k === 'fewTrades' ? T('표본 부족', 'few trades') : k === 'costsOff' ? T('비용 미포함', 'costs off') : k);

	const eq = $derived(result.equity.filter((v): v is number => v != null));
	const bhq = $derived(result.bhEquity.filter((v): v is number => v != null));
	const nBars = $derived(eq.length);
	const tsWin = $derived(candleTs.slice(result.startIdx, result.startIdx + nBars));
	const dd = $derived.by(() => {
		let peak = -Infinity;
		return eq.map((v) => {
			if (v > peak) peak = v;
			return peak > 0 ? (v / peak - 1) * 100 : 0;
		});
	});
	const splitFrac = $derived.by<number | null>(() => {
		if (!oos || nBars < 2) return null;
		const rel = oos.splitIdx - result.startIdx;
		if (rel <= 0 || rel >= nBars) return null;
		return rel / (nBars - 1);
	});
	const eqRange = $derived.by(() => {
		const all = [...eq, ...bhq];
		if (!all.length) return { lo: 90, hi: 110 };
		let lo = Math.min(...all);
		let hi = Math.max(...all);
		if (hi - lo < 1) { lo -= 1; hi += 1; }
		return { lo, hi };
	});
	const ddMin = $derived(dd.length ? Math.min(...dd, -1) : -1);
	const cumPct = $derived.by(() => {
		let acc = 1;
		return result.trades.map((t) => {
			acc *= 1 + t.retPct / 100;
			return (acc - 1) * 100;
		});
	});
	const worstTrades = $derived([...result.trades].sort((a, b) => a.retPct - b.retPct).slice(0, 6));
	const tradeStats = $derived.by(() => {
		const ts = result.trades.filter((t) => t.maePct != null);
		if (!result.trades.length) return null;
		const exp = result.trades.reduce((s, t) => s + t.retPct, 0) / result.trades.length;
		const mae = ts.length ? ts.reduce((s, t) => s + (t.maePct ?? 0), 0) / ts.length : null;
		const mfe = ts.length ? ts.reduce((s, t) => s + (t.mfePct ?? 0), 0) / ts.length : null;
		return { exp, mae, mfe };
	});
	const recovered = $derived(result.mddWindow?.recoverIdx != null);
	const oosDecay = $derived.by<number | null>(() => {
		if (!oos || oos.train.sharpe == null || oos.test.sharpe == null || oos.train.sharpe <= 0) return null;
		return (oos.test.sharpe / oos.train.sharpe - 1) * 100;
	});

	// ★증거 등급 · 표본이 헤드라인(수익률 아님). 봉<252 또는 거래<10 = 일화(1경로), OOS 있으면 다구간 서술.
	const evidence = $derived.by(() => {
		const trades = m.tradeCount;
		if (nBars < 60 || trades < 5) return { tier: T('일화 · 1경로', 'anecdote · 1 path'), tone: 'evDn' };
		if (nBars < 252 || trades < 10) return { tier: T('서술적 · 표본 얕음', 'descriptive · thin'), tone: 'evMid' };
		if (oos) return { tier: T('서술적 · 학습/검증 분할', 'descriptive · train/test'), tone: 'evUp' };
		return { tier: T('서술적 · 단일구간', 'descriptive · single window'), tone: 'evMid' };
	});

	// 약한 증거(일화·1경로) = 헤드라인 수익률을 중립색으로 · 큰 초록이 "진짜 우위"로 오독되지 않게(NEVER-CLAIM).
	const weakTier = $derived(evidence.tone === 'evDn');
	const clsT = (v: number) => (weakTier ? 'tNeu' : cls(v));
	// Calmar = CAGR / |MDD| · 이미 계산된 m 값 재사용(엔진 단일슬롯 metrics 엔 없어 여기서 도출).
	const calmar = $derived(m.cagrPct != null && m.mddPct < 0 ? m.cagrPct / Math.abs(m.mddPct) : null);
	// 청산(실현) 거래만 · 승률 분수 표기를 엔진 winRatePct(청산 기준)와 일치.
	const closedTrades = $derived(result.trades.filter((t) => !t.open));
	// 사유 색 · 손절=빨강·익절=초록·신호=중립·미청산=흐림 (4의미를 한 회색에서 분리, 손절 스캔성).
	const reasonCls = (r: string) => (r === 'stop' ? 'tDn' : r === 'take' ? 'tUp' : r === 'finalMark' ? 'dim' : 'tNeu');
	const reasonLbl = (r: string) => (r === 'finalMark' ? T('미청산', 'open') : r === 'stop' ? T('손절', 'stop') : r === 'take' ? T('익절', 'take') : T('신호', 'signal'));
	// 거래표 합계 푸터 · 눈으로 계산하던 총계·평균을 sticky 푸터로(밀도표 강화, 운영자 #1 요구).
	const tradeSummary = $derived.by(() => {
		const tr = result.trades;
		if (!tr.length) return null;
		const closed = tr.filter((t) => !t.open);
		const wins = closed.filter((t) => t.retPct > 0).length;
		return {
			n: tr.length,
			closedN: closed.length,
			winPct: closed.length ? (wins / closed.length) * 100 : null,
			avgRet: tr.reduce((a, t) => a + t.retPct, 0) / tr.length,
			avgHold: Math.round(tr.reduce((a, t) => a + t.holdDays, 0) / tr.length),
			finalCum: cumPct.length ? cumPct[cumPct.length - 1] : 0
		};
	});

	// 거래순서 몬테카를로(경로운) · 실현 거래만 재배열. 표본<15면 null(거짓 좁은 밴드 차단).
	const mcCone = $derived.by(() => tradeShuffleCone(result.trades.map((t) => t.retPct)));

	// 청산사유 분해 · 사유별 건수·평균손익(신규 통계 0, exitReason 이미 기록). 손절이 너무 자주 끊는지·수익이 어디서 났는지 한 줄.
	// 사유 ≥2 일 때만(전부 신호청산이면 거래표 사유열과 중복 → 생략). 막대=평균손익 크기, 색=사유.
	const exitBreakdown = $derived.by(() => {
		const by = new Map<string, { n: number; sum: number }>();
		for (const t of result.trades) {
			const e = by.get(t.exitReason) ?? { n: 0, sum: 0 };
			e.n += 1; e.sum += t.retPct;
			by.set(t.exitReason, e);
		}
		const rows = (['stop', 'take', 'signal', 'finalMark'] as const).filter((r) => by.has(r)).map((r) => ({ reason: r, n: by.get(r)!.n, avg: by.get(r)!.sum / by.get(r)!.n }));
		const maxAbs = Math.max(1, ...rows.map((r) => Math.abs(r.avg)));
		return rows.length >= 2 ? rows.map((r) => ({ ...r, w: (Math.abs(r.avg) / maxAbs) * 100 })) : null;
	});

	function jumpToBar(t: string) { onFocusBar?.(t); }

	function exportCsv() {
		const head = ['entry', 'entryPx', 'exit', 'exitPx', 'retPct', 'maePct', 'mfePct', 'cumPct', 'holdDays', 'exitReason'];
		const rows = result.trades.map((t, i) => [t.entryT, t.entryPx.toFixed(2), t.exitT ?? '', t.exitPx != null ? t.exitPx.toFixed(2) : '', t.retPct.toFixed(2), t.maePct != null ? t.maePct.toFixed(2) : '', t.mfePct != null ? t.mfePct.toFixed(2) : '', cumPct[i].toFixed(2), t.holdDays, t.exitReason]);
		const csv = [head, ...rows].map((r) => r.join(',')).join('\n');
		const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `backtest_${rs?.symbol.code ?? 'trades'}_${rs?.dataAsOf ?? ''}.csv`;
		a.click();
		URL.revokeObjectURL(url);
	}
	const scopeLabel = $derived(scope === 'market' ? T('시장(지수)', 'market') : scope === 'universe' ? T('유니버스', 'universe') : T('단일종목', 'single stock'));
</script>

<div class="btReport">
	<!-- 마스트헤드 · 보고서 제목 + 스코프 + 재무로 복귀 -->
	<div class="brHead">
		<span class="brMark" aria-hidden="true"></span>
		<span class="brTitle">{T('백테스트 보고서', 'BACKTEST REPORT')}</span>
		<span class="brScope">{scopeLabel}</span>
		<span class="brHeadline mono">
			<b class={clsT(m.retPct)}>{slots.find((s) => s.id === focusId)?.label ?? ''} {sgn(m.retPct)}%</b>
			<i>vs</i><b class={cls(result.bh.retPct)}>{T('보유', 'B&H')} {sgn(result.bh.retPct)}%</b>
			<em class={'brExcess ' + cls(m.retPct - result.bh.retPct)}>{sgn(m.retPct - result.bh.retPct)}%p</em>
		</span>
		<button class="brBack" onclick={onBack} title={T('재무 그래프로 복귀', 'back to financials')}>{T('재무로 ↩', 'financials ↩')}</button>
	</div>

	{#if multi}
		<div class="brTabs">
			{#each pf.slots as s (s.id)}
				{@const meta = metaOf(s.id)}
				<button class="brTab" class:on={s.id === focusId} onclick={() => onFocus(idxOf(s.id))}>
					<i class="brSw" style={`background:${meta?.color ?? '#8b919e'}`}></i>{meta?.label ?? s.id}
					<em class={cls(s.result.metrics.retPct)}>{sgn(s.result.metrics.retPct)}%</em>
				</button>
			{/each}
		</div>
	{/if}

	<!-- ★정직 헤더 띠 (상존·11px+) · 증거등급이 헤드라인, 수익률은 부차 -->
	<div class="brHonest">
		<span class={'brEv ' + evidence.tone}>{evidence.tier}</span>
		<span class="brStamp">{T('체결 t+1 시가', 'fill t+1 open')}</span>
		<span class="brStamp">{withCosts ? T('비용 반영', 'costs on') : T('⚠ 비용 미포함', '⚠ costs off')}</span>
		<span class="brStamp">{adjusted ? T('배당미반영·수정주가', 'div excl·adj') : T('배당미반영·무수정주가', 'div excl·unadj')}</span>
		{#if oos}<span class="brStamp">{T('학습/검증 분할', 'train/test split')}</span>{:else if rs}<span class="brStamp">{T('구간', 'window')} {fmtD(rs.range.from)}~{fmtD(rs.range.to)} · {rs.range.bars}{T('봉', 'b')}</span>{:else}<span class="brStamp">{T('단일구간', 'single window')}</span>{/if}
		{#if rs}<span class="brStamp">{T('기준일', 'as of')} {fmtD(rs.dataAsOf)}</span>{/if}
		{#each result.warnings as w (w.kind)}<span class="brWarn">⚠ {warnLabel(w.kind)}</span>{/each}
	</div>

	{#if combo}
		<div class="brBanner mag">{T('동일가중 조합 (리밸런싱 없음) · 단일종목 = 타이밍 분산이지 자산 분산 아님', 'equal-weight combo · timing not asset diversification')} · {T('수익률', 'return')} <b class={'mono ' + cls(combo.metrics.retPct)}>{sgn(combo.metrics.retPct)}%</b></div>
	{/if}
	{#if !beats}<div class="brBanner lag">{T('이 구간에선 단순 보유(B&H)가 전략을 앞섰습니다.', 'buy & hold beat the strategy over this window.')}</div>{/if}
	{#if fullRef}
		{@const winExcess = m.retPct - result.bh.retPct}
		{@const fullExcess = fullRef.retPct - fullRef.bhRetPct}
		<!-- G3 체리피킹 대조 · 선택 구간은 전체의 일부. 같은 전략을 전체 기간에 돌린 결과를 병기해 표본운/구간선택 편향을 구조적으로 자백. -->
		<div class="brBanner cherry">
			<b>{T('구간 선택 주의', 'window-pick check')}</b> · {T('선택 구간은 전체의 일부입니다. 같은 전략 전체', 'this is a slice; same strategy over the full period')} <i>({fmtD(fullRef.fromT)}~{fmtD(fullRef.toT)})</i>: {T('전략', 'strat')} <b class={'mono ' + cls(fullRef.retPct)}>{sgn(fullRef.retPct)}%</b> {T('vs 보유', 'vs B&H')} <b class={'mono ' + cls(fullRef.bhRetPct)}>{sgn(fullRef.bhRetPct)}%</b>{#if fullRef.cagrPct != null} · CAGR <b class="mono">{sgn(fullRef.cagrPct)}%</b>{/if}
			{#if winExcess > fullExcess + 3}<span class="brCherryFlag">⚠ {T('이 구간이 전체 기간보다 전략에 유리해 보입니다 · 체리피킹 위험', 'this window flatters the strategy vs the full period · cherry-pick risk')}</span>{/if}
		</div>
	{/if}

	<!-- 히어로 5 카드 -->
	<div class="brHero">
		<div class="brCard hero"><span>{T('보유(B&H) 대비', 'vs buy & hold')}</span><b class={'mono ' + clsT(m.retPct - result.bh.retPct)}>{sgn(m.retPct - result.bh.retPct)}%p</b>{#if weakTier}<em>{T('일화 · 색 보류', 'anecdote · muted')}</em>{:else}<em>{T('전략 ' + sgn(m.retPct) + '% · 보유 ' + sgn(result.bh.retPct) + '%', 'strat ' + sgn(m.retPct) + '% · B&H ' + sgn(result.bh.retPct) + '%')}</em>{/if}</div>
		<div class="brCard"><span>CAGR</span><b class={'mono ' + (m.cagrPct != null ? clsT(m.cagrPct) : 'tNeu')}>{m.cagrPct != null ? sgn(m.cagrPct) + '%' : '·'}</b></div>
		<div class="brCard"><span>{T('최대 낙폭', 'max DD')}</span><b class="mono tDn">{m.mddPct.toFixed(1)}%</b></div>
		<div class="brCard"><span>Sharpe</span><b class="mono">{m.sharpe != null ? m.sharpe.toFixed(2) : '·'}</b></div>
		{#if scope === 'market'}
			<div class="brCard"><span>{T('노출', 'exposure')}</span><b class="mono">{m.exposurePct.toFixed(0)}%</b></div>
		{:else if closedTrades.length === 0}
			<div class="brCard"><span>{T('승률', 'win rate')}</span><b class="mono tNeu">{result.trades.length ? T('미청산', 'open') : T('·', '·')}</b><em>{result.trades.length ? T('청산 거래 없음', 'no closed trade') : T('신호 미발생', 'no signal')}</em></div>
		{:else}
			<div class="brCard"><span>{T('승률', 'win rate')}</span><b class="mono">{m.winRatePct != null ? m.winRatePct.toFixed(0) + '%' : '·'}</b><em>{closedTrades.filter((t) => t.retPct > 0).length}/{closedTrades.length} {T('청산', 'closed')}</em></div>
		{/if}
	</div>

	<!-- 일자별 거래표 (spine·상시) -->
	<section class="brSec">
		<div class="brSecHd">{T('거래 내역', 'trades')} <span class="brN">{m.tradeCount}</span><button class="brCsv" onclick={exportCsv}>{T('CSV', 'CSV')}</button><span class="brHint">{T('행 클릭 → 차트 진입봉', 'row → chart bar')}</span></div>
		{#if exitBreakdown}
			<!-- 청산사유 분해 · 사유별 건수+평균손익(막대=평균 크기·색=사유). 손절이 자주 끊는지/수익이 어디서 났는지 한눈에. -->
			<div class="brExit">
				{#each exitBreakdown as e (e.reason)}
					<div class="brExitRow" title={T('평균 손익', 'avg P&L per exit')}>
						<span class={'brExitLbl ' + reasonCls(e.reason)}>{reasonLbl(e.reason)}</span>
						<span class="brExitN">{e.n}{T('건', '')}</span>
						<span class="brExitBar"><i class={e.avg >= 0 ? 'u' : 'd'} style={`width:${e.w}%`}></i></span>
						<span class={'brExitAvg mono ' + cls(e.avg)}>{sgn(e.avg)}%</span>
					</div>
				{/each}
			</div>
		{/if}
		{#if result.trades.length}
			<div class="brTableWrap">
				<table class="brTable mono">
					<thead><tr><th>#</th><th>{T('진입', 'entry')}</th><th class="r">{T('진입가', 'in')}</th><th>{T('청산', 'exit')}</th><th class="r">{T('청산가', 'out')}</th><th class="r">{T('수익률', 'ret')}</th><th class="r" title={T('보유 중 최대역행(MAE)', 'max adverse')}>MAE</th><th class="r" title={T('보유 중 최대순행(MFE)', 'max favorable')}>MFE</th><th class="r">{T('누적', 'cum')}</th><th class="r">{T('보유', 'd')}</th><th>{T('사유', 'why')}</th></tr></thead>
					<tbody>
						{#each result.trades.slice().reverse() as t, i (t.entryT)}
							{@const cum = cumPct[result.trades.length - 1 - i]}
							<tr class={'brRowT' + (t.retPct > 0 ? ' winRow' : t.retPct < 0 ? ' lossRow' : '') + (hoverTs === t.entryT ? ' hl' : '')} onclick={() => jumpToBar(t.entryT)} title={T('차트로 이동', 'jump to chart')}>
								<td class="dim">{result.trades.length - i}</td>
								<td>{fmtD(t.entryT)}</td>
								<td class="r">{num(t.entryPx)}</td>
								<td>{t.exitT ? fmtD(t.exitT) : T('보유중', 'open')}</td>
								<td class="r">{t.exitPx != null ? num(t.exitPx) : '·'}</td>
								<td class={'r ' + cls(t.retPct)}>{sgn(t.retPct)}%</td>
								<td class="r tDn">{t.maePct != null ? t.maePct.toFixed(1) + '%' : '·'}</td>
								<td class="r tUp">{t.mfePct != null ? '+' + t.mfePct.toFixed(1) + '%' : '·'}</td>
								<td class={'r ' + cls(cum)}>{sgn(cum)}%</td>
								<td class="r">{t.holdDays}</td>
								<td class={reasonCls(t.exitReason)}>{reasonLbl(t.exitReason)}</td>
							</tr>
						{/each}
					</tbody>
					{#if tradeSummary}
						<tfoot><tr class="brFoot">
							<td colspan="5">Σ {tradeSummary.n}{T('건', '')} · {T('승률', 'win')} {tradeSummary.winPct != null ? tradeSummary.winPct.toFixed(0) + '%' : '·'} <i>({tradeSummary.closedN}{T(' 청산', ' closed')})</i></td>
							<td class={'r ' + cls(tradeSummary.avgRet)}>{sgn(tradeSummary.avgRet)}%</td>
							<td class="r dim" colspan="2">{T('평균', 'avg')}</td>
							<td class={'r ' + cls(tradeSummary.finalCum)}>{sgn(tradeSummary.finalCum)}%</td>
							<td class="r">{tradeSummary.avgHold}</td>
							<td></td>
						</tr></tfoot>
					{/if}
				</table>
			</div>
		{:else}
			<div class="brEmpty">{T('이 구간에서 진입 거래가 없습니다.', 'no entries in this window.')}</div>
		{/if}
	</section>


	<!-- 매매표가 선두(차트 바로 아래·운영자 #1). 무거운 통계는 ▸상세통계 토글로 분리(인라인 하이브리드). -->
	<button class="brTearToggle" onclick={() => onToggleTearsheet?.()} aria-expanded={tearsheetOpen}><span class="brTearCaret">{tearsheetOpen ? '▾' : '▸'}</span> {tearsheetOpen ? T('상세 통계 접기', 'hide tearsheet') : T('상세 통계 · 자산곡선·몬테카를로·월별·분포·MAE·보조지표', 'detailed tearsheet · equity·MC·monthly·dist·MAE·metrics')}</button>
	{#if tearsheetOpen}
	<!-- 자산곡선 (verdict 시각) + OOS -->
	<section class="brSec">
		<div class="brSecHd">{T('자산 곡선 · 계좌가치 (시작 = 100)', 'equity curve (start = 100)')}</div>
		<EquityChart {eq} {bhq} {dd} ts={tsWin} {splitFrac} {eqRange} {ddMin} {stratColor} {lang} />
		{#if oos}
			<div class="brOosLine">{T('학습 → 검증(OOS)', 'train → test (OOS)')} · {T('수익률', 'ret')} <b class={cls(oos.train.retPct)}>{sgn(oos.train.retPct)}%</b> → <b class={cls(oos.test.retPct)}>{sgn(oos.test.retPct)}%</b>{#if oosDecay != null} · <b class={'brDecay ' + (oosDecay < -2 ? 'tDn' : oosDecay > 2 ? 'tUp' : 'tNeu')}>Sharpe {oosDecay >= 0 ? '+' : ''}{oosDecay.toFixed(0)}%</b>{/if} <i>{T('고정 파라미터 · walk-forward 아님', 'fixed params · not walk-forward')}</i></div>
		{/if}
	</section>

	<!-- 거래순서 몬테카를로(경로운) · 한 경로는 한 번의 운. 표본<15면 정직하게 생략. -->
	{#if mcCone}
		<section class="brSec">
			<div class="brSecHd">{T('거래순서 몬테카를로 · 경로운', 'trade-shuffle Monte Carlo · path luck')}</div>
			<div class="brMc">
				<span>{T('최종수익 5~95%', 'terminal 5-95%')} <b class={cls(mcCone.p5)}>{sgn(mcCone.p5, 0)}%</b> ~ <b class={cls(mcCone.p95)}>{sgn(mcCone.p95, 0)}%</b> <i>({T('중앙', 'median')} {sgn(mcCone.p50, 0)}%)</i></span>
				<span>{T('최악 5% 최대낙폭', 'MDD worst 5%')} <b class="tDn">{mcCone.mddP95.toFixed(0)}%</b></span>
				<i class="brMcNote">{T('실현 거래 순서만 재배열 · 예측 아님. 헤드라인은 한 경로(운)일 뿐 · 자본은 최악낙폭 기준.', 'reshuffle of realized trades only · not a forecast; the headline is one lucky path.')}</i>
			</div>
		</section>
	{/if}

	<!-- 소형 다중 · 월별·연간·분포. 표본 짧으면(일화) 1~2칸 히트맵=과잉분석 신호라 한 줄로 생략. -->
	{#if weakTier}
		<div class="brShortNote">{T('표본이 짧아 월별·연간 분해 생략 · 한 경로의 일화', 'sample too short for monthly/yearly breakdown · one anecdotal path')}</div>
	{:else}
		<section class="brSec">
			<div class="brSecHd">{T('월별 수익률', 'monthly returns')}</div>
			<MonthlyReturnsHeatmap {eq} ts={tsWin} {lang} />
		</section>
		<section class="brSec">
			<div class="brSecHd">{T('연간 수익률 · 전략 vs 보유', 'yearly returns')}</div>
			<YearlyReturnsBars {eq} {bhq} ts={tsWin} {lang} />
		</section>
	{/if}
	{#if result.trades.length >= 2}
		<section class="brSec">
			<div class="brSecHd">{T('거래 수익률 분포', 'trade return distribution')}</div>
			<ReturnHistogram rets={result.trades.map((t) => t.retPct)} {lang} />
		</section>
	{/if}

	<!-- 거래별 MAE 산점 -->
	{#if result.trades.some((t) => t.maePct != null)}
		<section class="brSec">
			<div class="brSecHd">{T('거래별 위험·보상 (MAE 산점)', 'per-trade MAE scatter')}</div>
			<TradeScatter trades={result.trades} {lang} onPick={jumpToBar} />
		</section>
	{/if}

	<!-- 보조 지표 -->
	<section class="brSec">
		<div class="brSecHd">{T('보조 지표', 'secondary metrics')}</div>
		<div class="brGrid">
			<div class="brRow"><span>{T('보유(B&H)', 'buy & hold')}</span><b class={'mono ' + cls(result.bh.retPct)}>{sgn(result.bh.retPct)}%</b></div>
			<div class="brRow"><span>{T('전략 순수익', 'net return')}</span><b class={'mono ' + clsT(m.retPct)}>{sgn(m.retPct)}%</b></div>
			<div class="brRow"><span>Sortino</span><b class="mono">{m.sortino != null ? m.sortino.toFixed(2) : '·'}</b></div>
			<div class="brRow"><span>{T('손익비', 'profit factor')}</span><b class="mono">{m.profitFactor != null ? m.profitFactor.toFixed(2) : '·'}</b></div>
			{#if tradeStats}<div class="brRow"><span>{T('기대값/거래', 'expectancy')}</span><b class={'mono ' + (tradeStats.exp >= 0 ? 'tUp' : 'tDn')}>{tradeStats.exp >= 0 ? '+' : ''}{tradeStats.exp.toFixed(2)}%</b></div>{/if}
			<div class="brRow"><span>{T('비용 드래그', 'cost drag')}</span><b class="mono tDn">{m.costDragPct.toFixed(1)}%p</b></div>
			<div class="brRow"><span>{T('최장 수면', 'longest underwater')}</span><b class="mono">{m.mddDays != null ? m.mddDays + T('일', 'd') : '·'}</b></div>
			<div class="brRow"><span>{T('회복', 'recovered')}</span><b class={'mono ' + (recovered ? 'tUp' : 'tDn')}>{recovered ? T('회복함', 'yes') : T('미회복', 'no')}</b></div>
			<div class="brRow"><span>{T('베타', 'beta')}</span><b class="mono">{m.beta != null ? m.beta.toFixed(2) : '·'}</b></div>
			<div class="brRow"><span>{T('알파(연)', 'alpha p.a.')}</span><b class={'mono ' + (m.alphaPct != null ? cls(m.alphaPct) : 'tNeu')}>{m.alphaPct != null ? sgn(m.alphaPct) + '%' : '·'}</b></div>
			<div class="brRow"><span>Calmar</span><b class="mono">{calmar != null ? calmar.toFixed(2) : '·'}</b></div>
			<div class="brRow"><span>{T('정보비율', 'info ratio')}</span><b class="mono">{m.infoRatio != null ? m.infoRatio.toFixed(2) : '·'}</b></div>
		</div>
	</section>

	{/if}

	<!-- 가정·RunSpec -->
	<section class="brSec">
		<div class="brSecHd">{T('체결·데이터 가정', 'assumptions')}</div>
		<ul class="brAssume">
			<li>{T('신호 t일 종가 → t+1일 시가 체결 (미래참조 구조적 차단)', 'signal close(t) → fill open(t+1) · look-ahead blocked')}</li>
			<li>{withCosts ? T('비용 반영 · 수수료 0.015% + 거래세 0.15% + 슬리피지 0.1%', 'costs on') : T('⚠ 비용 미포함 · 실거래 대비 낙관', '⚠ costs excluded')}</li>
			<li>{T('벤치마크 = 보유(B&H), 동일 비용', 'benchmark = buy & hold, same costs')}</li>
			<li class="warn">{T('⚠ 배당 미반영', '⚠ dividends excluded')} · {adjusted ? T('수정주가', 'adjusted') : T('⚠ 무수정주가 · 분할 시 B&H 왜곡', '⚠ unadjusted')}</li>
		</ul>
		{#if rs}<div class="brSpec mono"><span>{T('종목', 'symbol')}: {rs.symbol.name ?? ''} {rs.symbol.code}</span><span>{T('구간', 'range')}: {fmtD(rs.range.from)} ~ {fmtD(rs.range.to)} · {rs.range.bars}{T('봉', ' bars')}</span><span>{T('데이터', 'source')}: {rs.dataSource} · {T('엔진', 'engine')} {rs.engineVersion}</span></div>{/if}
		<div class="brFoot">⚠ {T('과거 가정 노출형 시뮬레이션 · 미래 수익 보장 없음 · 추천 아님', 'assumption-exposed historical simulation · not advice')} │ {GOV_ATTRIBUTION}</div>
	</section>
</div>

<style>
	.btReport { display: flex; flex-direction: column; gap: 10px; padding: 4px 2px 14px; }
	.brHead { display: flex; align-items: center; gap: 9px; flex-wrap: wrap; }
	.brMark { width: 4px; height: 18px; border-radius: 2px; background: var(--amber, var(--amber)); }
	.brTitle { font-size: 12px; font-weight: 700; letter-spacing: 0.05em; color: var(--dl-ink, #c8cfdb); }
	.brScope { font-size: 10.5px; color: var(--dim, #8b94a3); border: 1px solid var(--dl-line, #1b2130); border-radius: 9px; padding: 1px 8px; }
	.brHeadline { margin-left: auto; display: flex; align-items: baseline; gap: 8px; font-size: 16px; font-weight: 700; font-variant-numeric: tabular-nums; }
	.brHeadline i { font-style: normal; font-size: 10px; font-weight: 400; color: var(--dimmer, #5b6573); }
	.brExcess { font-style: normal; font-size: 12px; font-weight: 700; padding: 1px 7px; border-radius: 9px; border: 1px solid var(--dl-line, #1b2130); }
	.brBack { background: none; border: 1px solid var(--dl-line-strong, #2a3142); color: #aeb6c2; font-size: 11px; padding: 2px 10px; border-radius: 3px; cursor: pointer; font-family: inherit; }
	.brBack:hover { color: var(--dl-ink, #c8cfdb); border-color: #3a4456; }
	.brTabs { display: flex; gap: 4px; flex-wrap: wrap; }
	.brTab { display: inline-flex; align-items: center; gap: 6px; background: none; border: 1px solid var(--dl-line, #1b2130); border-radius: 5px; padding: 3px 9px; cursor: pointer; font-family: inherit; font-size: 11px; color: #aeb6c2; }
	.brTab.on { background: rgba(255, 255, 255, 0.03); color: var(--dl-ink, #c8cfdb); border-color: #2a3142; }
	.brTab .brSw { width: 9px; height: 9px; border-radius: 2px; }
	.brTab em { font-style: normal; font-family: var(--dl-font-mono, monospace); font-size: 11px; }
	.brHonest { display: flex; flex-wrap: wrap; align-items: center; gap: 5px; padding: 5px 0; border-top: 1px solid var(--dl-line, #1b2130); border-bottom: 1px solid var(--dl-line, #1b2130); }
	.brEv { font-size: 11.5px; font-weight: 700; padding: 1px 9px; border-radius: 4px; }
	.brEv.evUp { color: var(--up, #34d399); background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.35); }
	.brEv.evMid { color: #aeb6c2; background: rgba(255, 255, 255, 0.04); border: 1px solid var(--dl-line, #1b2130); }
	.brEv.evDn { color: var(--amber, var(--amber)); background: rgba(var(--amber-rgb), 0.1); border: 1px solid rgba(var(--amber-rgb), 0.4); }
	.brStamp { font-size: 11px; color: #8b94a3; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--dl-line, #1b2130); border-radius: 3px; padding: 0 6px; }
	.brWarn { font-size: 11px; color: var(--amber, var(--amber)); border: 1px solid rgba(var(--amber-rgb), 0.35); border-radius: 3px; padding: 0 6px; }
	.brBanner { font-size: 11px; border-radius: 4px; padding: 6px 11px; line-height: 1.5; }
	.brBanner.mag { color: #cbb4f5; background: rgba(232, 121, 249, 0.07); border: 1px solid rgba(232, 121, 249, 0.25); }
	.brBanner.lag { color: #fbbf77; background: rgba(var(--amber-rgb), 0.08); border: 1px solid rgba(var(--amber-rgb), 0.3); }
	/* G3 체리피킹 대조 · 이 구간 vs 전체 기간 병기(표본운 구조적 자백). */
	.brBanner.cherry { color: #d7c4a8; background: rgba(var(--amber-rgb), 0.06); border: 1px solid rgba(var(--amber-rgb), 0.28); display: flex; flex-wrap: wrap; align-items: baseline; gap: 5px; }
	.brBanner.cherry i { font-style: normal; color: var(--dimmer, #5b6573); font-size: 11px; }
	.brCherryFlag { flex-basis: 100%; color: var(--amber, var(--amber)); font-size: 11px; }
	.brHero { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 8px; }
	.brCard { display: flex; flex-direction: column; gap: 2px; padding: 9px 11px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--dl-line, #1b2130); border-radius: 5px; }
	/* 히어로 카드 #1 = 보유 대비 초과수익 · 백테스트의 진짜 답. 앰버 좌측 액센트 + 가장 큰 숫자(CAGR 압도 차단). */
	.brCard.hero { border-left: 3px solid var(--amber, var(--amber)); background: rgba(var(--amber-rgb), 0.04); }
	.brCard.hero > b { font-size: 27px; }
	.brCard.hero > span { color: var(--amber, var(--amber)); font-weight: 600; }
	.brCard > span { font-size: 11px; color: var(--dim, #8b94a3); }
	.brCard > b { font-size: 21px; font-weight: 700; line-height: 1.1; color: var(--dl-ink, #c8cfdb); font-variant-numeric: tabular-nums; }
	.brCard > em { font-style: normal; font-size: 11px; color: var(--dimmer, #5b6573); font-family: var(--dl-font-mono, monospace); }
	/* 상세 통계 토글 · 무거운 tearsheet 접힘(매매표 선두 유지). */
	.brTearToggle { width: 100%; text-align: left; font-size: 11.5px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--dl-line, #1b2130); border-radius: 5px; padding: 7px 11px; cursor: pointer; font-family: inherit; color: #aeb6c2; }
	.brTearToggle:hover { border-color: #2a3142; color: var(--dl-ink, #c8cfdb); }
	.brTearCaret { color: var(--amber, var(--amber)); font-weight: 700; margin-right: 4px; }
	.brSec { display: flex; flex-direction: column; gap: 7px; }
	.brSecHd { font-size: 11.5px; font-weight: 700; letter-spacing: 0.04em; color: #aeb6c2; text-transform: uppercase; display: flex; align-items: center; gap: 9px; }
	.brN { font-family: var(--dl-font-mono, monospace); font-size: 11px; color: var(--dimmer, #5b6573); font-weight: 400; }
	.brCsv { background: none; border: 1px solid var(--dl-line-strong, #2a3142); color: #aeb6c2; font-size: 11px; padding: 1px 8px; border-radius: 3px; cursor: pointer; font-family: inherit; }
	.brHint { font-size: 10px; color: var(--dimmer, #5b6573); font-weight: 400; text-transform: none; letter-spacing: 0; margin-left: auto; }
	.brMc { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 16px; font-size: 12px; color: #aeb6c2; font-variant-numeric: tabular-nums; padding: 7px 11px; background: rgba(255, 255, 255, 0.02); border: 1px solid var(--dl-line, #1b2130); border-radius: 5px; }
	.brMc b { font-weight: 700; }
	.brMc i { font-style: normal; color: var(--dimmer, #5b6573); font-size: 10.5px; }
	.brMcNote { flex-basis: 100%; line-height: 1.5; }
	.brShortNote { font-size: 11px; color: var(--dim, #8b94a3); padding: 4px 2px; line-height: 1.5; }
	.brOosLine { font-size: 11.5px; color: #aeb6c2; font-variant-numeric: tabular-nums; }
	.brOosLine i { font-style: normal; font-size: 11px; color: var(--dimmer, #5b6573); margin-left: 4px; }
	.brOosLine b { font-weight: 700; }
	.brDecay { font-family: var(--dl-font-mono, monospace); }
	.brGrid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 4px 14px; }
	.brRow { display: flex; justify-content: space-between; align-items: baseline; padding: 4px 9px; background: rgba(255, 255, 255, 0.015); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; font-size: 12.5px; }
	.brRow > span { color: #aeb6c2; }
	.brRow > b { font-weight: 700; color: var(--dl-ink, #c8cfdb); font-variant-numeric: tabular-nums; }
	.brTableWrap { max-height: 340px; overflow-y: auto; overflow-x: auto; border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; }
	.brTable { width: 100%; border-collapse: collapse; font-size: 12.5px; font-variant-numeric: tabular-nums; }
	.brTable thead th { position: sticky; top: 0; background: var(--dl-bg-raised, #0e141f); text-align: left; color: #8b94a3; font-weight: 600; padding: 4px 7px; border-bottom: 1px solid var(--dl-line-strong, #2a3142); font-size: 11px; white-space: nowrap; }
	.brTable th.r, .brTable td.r { text-align: right; }
	.brTable td { padding: 3px 7px; border-bottom: 1px solid rgba(27, 33, 48, 0.6); color: #aeb6c2; white-space: nowrap; }
	/* 승패 좌측 엣지 액센트(전체 워시 아님 · 색 규율) + 사유 색은 셀 클래스(tUp/tDn/tNeu/dim) */
	.brRowT.winRow td:first-child { box-shadow: inset 2px 0 0 var(--up, #34d399); }
	.brRowT.lossRow td:first-child { box-shadow: inset 2px 0 0 var(--dn, #f0616f); }
	/* sticky 합계 푸터 · thead 와 대칭(하단 고정). */
	.brTable tfoot td { position: sticky; bottom: 0; background: var(--dl-bg-raised, #0e141f); border-top: 1px solid var(--dl-line-strong, #2a3142); padding: 5px 7px; font-weight: 700; color: var(--dl-ink, #c8cfdb); }
	.brTable tfoot i { font-style: normal; font-weight: 400; color: var(--dimmer, #5b6573); }
	.brTable td.dim { color: var(--dimmer, #5b6573); }
	.brRowT { cursor: pointer; }
	.brRowT:hover td { background: rgba(96, 165, 250, 0.1); }
	/* 역 hover-sync · 차트 crosshair 가 이 거래봉 위면 행 강조(앰버=crosshair 색). 차트↔표 루프 완성. */
	.brRowT.hl td { background: rgba(var(--amber-rgb), 0.16); }
	.brEmpty { font-size: 11px; color: var(--dimmer, #5b6573); padding: 14px; text-align: center; }
	/* 청산사유 분해 · 사유별 건수+평균손익 막대(신규 통계 0, exitReason 표면화). */
	.brExit { display: flex; flex-direction: column; gap: 3px; padding: 5px 9px; background: rgba(255, 255, 255, 0.015); border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; }
	.brExitRow { display: flex; align-items: center; gap: 8px; font-size: 11.5px; font-variant-numeric: tabular-nums; }
	.brExitLbl { flex: 0 0 44px; font-weight: 600; }
	.brExitN { flex: 0 0 40px; color: var(--dim, #8b94a3); font-family: var(--dl-font-mono, monospace); }
	.brExitBar { flex: 1 1 auto; height: 7px; background: rgba(255, 255, 255, 0.03); border-radius: 4px; overflow: hidden; }
	.brExitBar i { display: block; height: 100%; border-radius: 4px; }
	.brExitBar i.u { background: var(--up, #34d399); }
	.brExitBar i.d { background: var(--dn, #f0616f); }
	.brExitAvg { flex: 0 0 56px; text-align: right; font-weight: 700; }
	.brAssume { margin: 0; padding-left: 16px; display: flex; flex-direction: column; gap: 3px; }
	.brAssume li { font-size: 11.5px; color: #aeb6c2; line-height: 1.5; }
	.brAssume li.warn { color: var(--amber, var(--amber)); }
	.brSpec { display: flex; flex-direction: column; gap: 2px; font-size: 11px; color: #8b94a3; margin-top: 4px; }
	.brFoot { font-size: 11px; color: var(--dimmer, #5b6573); margin-top: 6px; line-height: 1.5; }
	.tUp { color: var(--up, #34d399); }
	.tDn { color: var(--dn, #f0616f); }
	.tNeu { color: #aeb6c2; }
</style>
