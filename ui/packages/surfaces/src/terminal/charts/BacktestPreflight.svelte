<script lang="ts">
	// 백테스트 대기 프리플라이트 · 전략 0개일 때 중앙 하단(원래 재무 자리)에 "이 종목·이 창의 진실"을 실행 전 표면화.
	// 토론 만장일치: void(10px 한 줄)를 파괴적 교체 대신 → ① 이겨야 할 선(B&H) ② 백테스트 가능성 ③ 정직 가정 ④ 안내.
	// 전부 backtestPreflight() 실현치(엔진·look-ahead 0). 프리셋 수익 teaser·auto-run 금지(NEVER-CLAIM).
	import type { BtPreflight } from '../lib/backtest';
	import type { Lang } from '../lib/types';

	interface Props {
		pf: BtPreflight;
		period: string;
		lang: Lang;
	}
	let { pf, period, lang }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	const sgn = (v: number, d = 1) => (v >= 0 ? '+' : '') + v.toFixed(d);
	const cls = (v: number) => (v > 0 ? 'tUp' : v < 0 ? 'tDn' : 'tNeu');
	const fmtD = (t: string) => (t && t.length >= 8 ? `${t.slice(0, 4)}.${t.slice(4, 6)}.${t.slice(6, 8)}` : '·');
	const clean = $derived(!pf.haltBars && !pf.splitSuspect && !pf.windowShort);
</script>

<div class="btPre">
	<!-- ① 이겨야 할 선 · 이 창에서 그냥 보유(B&H) 한 결과. 전략이 못 이기면 노이즈. -->
	<div class="bpHero">
		<div class="bpHeroLbl">{T('이 창에서 ', 'over this window, ')}<b>{T('그냥 들고만 있었다면', 'just holding')}</b> <i>(B&H)</i> {T('· 전략이 이겨야 할 선', '· the line your rule must beat')}</div>
		<div class="bpNums">
			<div class="bpBig"><span>{T('보유 수익', 'B&H return')}</span><b class={'mono ' + cls(pf.bhRetPct)}>{sgn(pf.bhRetPct)}%</b></div>
			<div class="bpBig"><span>{T('최대 낙폭', 'max DD')}</span><b class="mono tDn">{pf.bhMddPct.toFixed(1)}%</b></div>
			{#if pf.bhSharpe != null}<div class="bpBig sub"><span>{T('보유 Sharpe', 'B&H Sharpe')}</span><b class="mono">{pf.bhSharpe.toFixed(2)}</b></div>{/if}
			{#if pf.annVolPct != null}<div class="bpBig sub"><span>{T('연 변동성', 'ann. vol')}</span><b class="mono">{pf.annVolPct.toFixed(0)}%</b></div>{/if}
			{#if pf.pos52wPct != null}<div class="bpBig sub"><span>{T('52주 위치', '52w pos')}</span><b class="mono">{pf.pos52wPct.toFixed(0)}%</b></div>{/if}
		</div>
	</div>

	<!-- ② 백테스트 가능성 · 거래가능 봉·구간·데이터 경고. 상업툴이 숨기는 "이게 검증 가능한가?" -->
	<div class="bpRow">
		<span class="bpK">{T('백테스트 가능성', 'backtestability')}</span>
		<span class="bpV">{T('거래가능', 'tradeable')} <b class="mono">{pf.tradeableBars}</b>{T('봉', ' bars')} <i>· {period}</i></span>
		<span class="bpV">{T('구간', 'span')} <b class="mono">{fmtD(pf.fromT)}~{fmtD(pf.toT)}</b></span>
		{#if pf.haltBars > 0}<span class="bpFlag warn">{T('정지', 'halt')} {pf.haltBars}{T('봉', '')}</span>{/if}
		{#if pf.splitSuspect}<span class="bpFlag warn">⚠ {T('분할의심', 'split?')} {fmtD(pf.splitSuspect)}</span>{/if}
		{#if pf.windowShort}<span class="bpFlag warn">⚠ {T('표본 짧음(<60봉) · Sharpe·CAGR 미산출', 'short (<60 bars) · no Sharpe/CAGR')}</span>{/if}
		{#if clean}<span class="bpFlag ok">✓ {T('깨끗', 'clean')}</span>{/if}
	</div>

	<!-- ③ 정직 가정 · 왕복비용 + 체결모델. 백테스트가 자신을 속이는 지점을 미리 못박음. -->
	<div class="bpRow">
		<span class="bpK">{T('정직 가정', 'honest assumptions')}</span>
		<span class="bpV">{T('왕복비용', 'round-trip cost')} <b class="mono tDn">{pf.roundTripPct.toFixed(2)}%</b> <i>({T('수수료·세금·슬리피지', 'fee·tax·slippage')})</i></span>
		<span class="bpV">{T('체결', 'fill')} <b>{T('신호=종가 → 다음날 시가', 'signal=close → next open')}</b> <i>({T('미래참조 차단', 'no look-ahead')})</i> · {T('정지봉 이연 · B&H 동일비용', 'halt-deferred · B&H same cost')}</span>
	</div>

	<!-- ④ 안내 · 좌측 패널로 유도(프리셋=출발점, 추천 아님). 장식 온보딩 아님. -->
	<div class="bpHint">← {T('왼쪽에서', 'on the left')} <b>{T('프리셋', 'a preset')}</b> {T('또는', 'or')} <b>{T('커스텀 규칙', 'a custom rule')}</b>{T('을 고르면 여기에 보고서가 채워집니다', ' fills the report here')} <i>· {T('프리셋 = 출발점, 추천 아님', 'preset = starting point, not advice')}</i></div>
</div>

<style>
	.btPre { display: flex; flex-direction: column; gap: 8px; padding: 9px 11px 11px; }
	/* ① 히어로 · 이겨야 할 선 */
	.bpHero { border: 1px solid var(--dl-line, #1b2130); border-radius: 6px; padding: 9px 12px; background: rgba(255, 255, 255, 0.02); }
	.bpHeroLbl { font-size: 11.5px; color: #aeb6c2; margin-bottom: 7px; }
	.bpHeroLbl b { color: var(--amber, var(--amber)); font-weight: 700; }
	.bpHeroLbl i { font-style: normal; color: var(--dimmer, #5b6573); font-size: 11px; }
	.bpNums { display: flex; flex-wrap: wrap; align-items: baseline; gap: 8px 22px; }
	.bpBig { display: flex; flex-direction: column; gap: 1px; }
	.bpBig > span { font-size: 11px; color: var(--dim, #8b94a3); }
	.bpBig > b { font-size: 24px; font-weight: 700; line-height: 1.05; font-variant-numeric: tabular-nums; color: var(--dl-ink, #c8cfdb); }
	.bpBig.sub > b { font-size: 17px; color: #aeb6c2; }
	/* ②③ 정보 행 */
	.bpRow { display: flex; flex-wrap: wrap; align-items: baseline; gap: 5px 14px; font-size: 11.5px; color: #aeb6c2; padding: 6px 2px; border-top: 1px solid var(--dl-line, #1b2130); }
	.bpK { font-size: 11px; font-weight: 700; letter-spacing: 0.03em; color: #8b94a3; text-transform: uppercase; flex: 0 0 auto; min-width: 92px; }
	.bpV { color: #aeb6c2; }
	.bpV b { color: var(--dl-ink, #c8cfdb); font-weight: 700; }
	.bpV i { font-style: normal; color: var(--dimmer, #5b6573); font-size: 11px; }
	.bpFlag { font-size: 11px; border-radius: 3px; padding: 0 6px; }
	.bpFlag.warn { color: var(--amber, var(--amber)); border: 1px solid rgba(var(--amber-rgb), 0.4); }
	.bpFlag.ok { color: var(--up, #34d399); border: 1px solid rgba(52, 211, 153, 0.35); }
	.bpHint { font-size: 11.5px; color: #8b94a3; padding-top: 2px; }
	.bpHint b { color: #a78bfa; font-weight: 600; }
	.bpHint i { font-style: normal; color: var(--dimmer, #5b6573); }
	.tUp { color: var(--up, #34d399); }
	.tDn { color: var(--dn, #f0616f); }
	.tNeu { color: #aeb6c2; }
</style>
