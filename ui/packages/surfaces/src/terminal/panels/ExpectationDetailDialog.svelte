<script lang="ts">
	// 추정·기대 상세 (밀도 화면) · 우측 재무 아래 "추정" 패널의 상세보기 목적지.
	// ★핵심 통찰: 실적 표는 실적만(운영자 규율). 추정은 전량 이곳에서 밀도 있게 본다.
	//   (1) 추정 3표(IS/BS/CF) 계정 x 기간(연간/분기 토글) x 시나리오(보수 p25/기준 p50/낙관 p75)
	//   (2) 채점 트랙레코드: 봉인 구간 vs 도착 실제값 · 구간적중/이탈 (검증척추)
	//   (3) 시장 기대(매크로 팬) + 방법·계보·정직 규율.
	// 데이터는 라이브러리 발행 뷰(estimateStatements)+원장(expectations/scores) 직독분을 부모가 주입.
	// 신규 계산 0 · 모달 크롬은 전역 .scrimWrap/.scrModal/.scrHead/.scrClose 재사용.
	import type {
		EstimateStatementRow,
		ExpectationRow,
		ExpectationScoreRow,
		ExpectationScorecard
	} from '@dartlab/ui-contracts';
	import type { Company, Lang } from '../lib/types';

	interface Props {
		co: Company;
		lang: Lang;
		estimates: EstimateStatementRow[] | null;
		expectations: ExpectationRow[];
		scores: ExpectationScoreRow[];
		scorecard: ExpectationScorecard | null;
		onClose: () => void;
	}
	let { co, lang, estimates, expectations, scores, scorecard, onClose }: Props = $props();

	type StmtK = 'IS' | 'BS' | 'CF';
	const STMT_LABEL: Record<StmtK, { kr: string; en: string }> = {
		IS: { kr: '손익', en: 'Income' },
		BS: { kr: '재무상태', en: 'Balance' },
		CF: { kr: '현금흐름', en: 'Cash flow' }
	};
	const QUANTILE_TABS: { q: 25 | 50 | 75; kr: string; en: string }[] = [
		{ q: 25, kr: '보수', en: 'Bear' },
		{ q: 50, kr: '기준', en: 'Base' },
		{ q: 75, kr: '낙관', en: 'Bull' }
	];
	let stmt = $state<StmtK>('IS');
	let periodKind = $state<'FY' | 'Q'>('FY');
	let scenario = $state<25 | 50 | 75>(50);

	const rows = $derived(estimates ?? []);
	const hasFy = $derived(rows.some((r) => r.periodKind === 'FY'));
	const hasQ = $derived(rows.some((r) => r.periodKind === 'Q'));

	// 조(兆) 단위 표기 · value 는 원. 절대값 1조 미만은 소수 2자리.
	const toJo = (won: number) => won / 1e12;
	const fmtJo = (won: number | undefined): string => {
		if (won == null) return '·';
		const v = toJo(won);
		const a = Math.abs(v);
		return (a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2));
	};

	// 선택된 statement + periodKind 의 밀도 격자: 행=계정(sortOrder), 열=기간, 셀={p25,p50,p75}.
	const grid = $derived.by(() => {
		const sel = rows.filter((r) => r.statement === stmt && r.periodKind === periodKind);
		if (!sel.length) return null;
		const periods = [...new Set(sel.map((r) => r.targetPeriod))].sort();
		const rowMap = new Map<string, { labelKr: string; labelEn: string; sortOrder: number; cells: Map<string, Record<number, number>> }>();
		for (const r of sel) {
			let row = rowMap.get(r.rowKey);
			if (!row) {
				row = { labelKr: r.labelKr, labelEn: r.labelEn, sortOrder: r.sortOrder, cells: new Map() };
				rowMap.set(r.rowKey, row);
			}
			const cell = row.cells.get(r.targetPeriod) ?? {};
			cell[r.quantile] = r.value;
			row.cells.set(r.targetPeriod, cell);
		}
		const rowList = [...rowMap.values()].sort((a, b) => a.sortOrder - b.sortOrder);
		// 기간 라벨: 연간 FY2026 -> FY26, 분기 2026Q3 -> 26Q3
		const pLabel = (p: string) => (p.startsWith('FY') ? `FY${p.slice(4)}` : p.slice(2));
		return { periods, pLabel, rowList };
	});

	// 채점 트랙레코드: 이 회사 + 시장(매크로) 봉인 기대 중 채점 도착분. 봉인 구간 vs 실제 + 판정.
	const EXP_VAR_LABEL: Record<string, { kr: string; en: string }> = {
		'KR.CPI': { kr: '물가(CPI)', en: 'CPI' },
		'KR.BASE_RATE': { kr: '기준금리', en: 'Base rate' },
		'KR.USDKRW': { kr: '원/달러', en: 'USDKRW' }
	};
	const METRIC_LABEL: Record<string, { kr: string; en: string }> = {
		revenue: { kr: '매출', en: 'Revenue' },
		operatingProfit: { kr: '영업이익', en: 'Op profit' },
		netIncome: { kr: '순이익', en: 'Net income' }
	};
	const varLabel = (v: string): string => {
		if (EXP_VAR_LABEL[v]) return lang === 'en' ? EXP_VAR_LABEL[v].en : EXP_VAR_LABEL[v].kr;
		const m = METRIC_LABEL[v.split('.')[1] ?? ''];
		return m ? (lang === 'en' ? m.en : m.kr) : v;
	};
	const isMacro = (v: string) => v.startsWith('KR.');
	const fmtLevel = (v: number, variable: string): string =>
		isMacro(variable) ? (variable === 'KR.BASE_RATE' ? v.toFixed(2) : variable === 'KR.USDKRW' ? v.toFixed(0) : v.toFixed(1)) : fmtJo(v);

	const track = $derived.by(() => {
		const scoreById = new Map(scores.filter((s) => !s.error).map((s) => [s.expectationId, s]));
		const mine = expectations.filter(
			(e) => e.kind === 'quantiles' && (e.variable.startsWith(co.code + '.') || isMacro(e.variable)) && scoreById.has(e.expectationId)
		);
		return mine
			.map((e) => ({ e, s: scoreById.get(e.expectationId)! }))
			.sort((a, b) => (a.s.scoredAt < b.s.scoredAt ? 1 : -1))
			.slice(0, 20);
	});

	// 시장 기대(매크로): 변수별 최신 발행에서 미채점(미래) 최소 horizon 1행.
	const market = $derived.by(() => {
		const scoreById = new Set(scores.map((s) => s.expectationId));
		return Object.keys(EXP_VAR_LABEL)
			.map((sid) => {
				const cand = expectations.filter((e) => e.variable === sid && e.kind === 'quantiles' && e.issuedLive);
				if (!cand.length) return null;
				const latest = cand.reduce((m, r) => (r.issuedAt > m ? r.issuedAt : m), '');
				const future = cand.filter((r) => r.issuedAt === latest && !scoreById.has(r.expectationId)).sort((a, b) => a.horizon - b.horizon);
				return future[0] ? { sid, r: future[0] } : null;
			})
			.filter((x): x is { sid: string; r: ExpectationRow } => x !== null);
	});

	// 방법·계보: 이 회사 봉인 기대의 엔진·경고 요약(중복 제거).
	const methodNote = $derived.by(() => {
		const mine = expectations.filter((e) => e.variable.startsWith(co.code + '.'));
		const warns = new Set<string>();
		for (const e of mine) for (const w of e.warnings) warns.add(w);
		return { count: mine.length, warns: [...warns] };
	});
	const WARN_LABEL: Record<string, { kr: string; en: string }> = {
		scenarioQuantileApprox: { kr: '시나리오→분위 정규근사', en: 'scenario→quantile normal approx' },
		revenueQuantileMapped: { kr: '매출 분위 캐스케이드', en: 'revenue-quantile cascade' },
		seasonalSplitOfAnnual: { kr: '연간의 계절 분해', en: 'seasonal split of annual' },
		quarterEndedAtIssue: { kr: 'nowcast(분기말 경과·미공시)', en: 'nowcast (quarter ended, unpublished)' },
		flatSeasonalityFallback: { kr: '계절성 표본부족→균등', en: 'flat seasonality fallback' }
	};
	const warnText = (w: string) => (WARN_LABEL[w] ? (lang === 'en' ? WARN_LABEL[w].en : WARN_LABEL[w].kr) : w);

	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div class="scrModal expDlg" role="dialog" aria-modal="true" aria-label={lang === 'en' ? 'Estimates detail' : '추정 상세'} onclick={(e) => e.stopPropagation()}>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'ESTIMATES & EXPECTATIONS' : '추정 · 기대 상세'}</span>
			<span class="expWho">{co.name.kr}<i>{co.code} · {co.sector.kr}</i></span>
			<span class="expLens">{lang === 'en' ? 'sealed at issuance · scored after · library-owned view' : '발행시점 봉인 · 사후 채점 · 라이브러리 뷰'}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		<div class="expDlgBody">
			<!-- (1) 추정 3표 -->
			<section class="expBlock">
				<div class="expBlockHead">
					<span class="expBlockTitle">{lang === 'en' ? 'Estimated statements' : '추정 재무제표'}</span>
					<span class="expSeg">{#each (['IS', 'BS', 'CF'] as StmtK[]) as k (k)}<button class={stmt === k ? 'on' : ''} onclick={() => (stmt = k)}>{lang === 'en' ? STMT_LABEL[k].en : STMT_LABEL[k].kr}</button>{/each}</span>
					<span class="expSeg">
						{#if hasFy}<button class={periodKind === 'FY' ? 'on' : ''} onclick={() => (periodKind = 'FY')}>{lang === 'en' ? 'Annual' : '연간'}</button>{/if}
						{#if hasQ}<button class={periodKind === 'Q' ? 'on' : ''} onclick={() => (periodKind = 'Q')}>{lang === 'en' ? 'Quarterly' : '분기'}</button>{/if}
					</span>
					<span class="expSeg scenSeg">{#each QUANTILE_TABS as t (t.q)}<button class={scenario === t.q ? 'on scen' + t.q : 'scen' + t.q} onclick={() => (scenario = t.q)} title={`p${t.q}`}>{lang === 'en' ? t.en : t.kr}</button>{/each}</span>
				</div>
				{#if grid}
					<div class="expTblScroll"><table class="expDlgTable">
						<thead><tr><th class="acct">{lang === 'en' ? 'ACCOUNT' : '계정'}</th>{#each grid.periods as p (p)}<th class="r">{grid.pLabel(p)}<i>E</i></th>{/each}</tr></thead>
						<tbody>
							{#each grid.rowList as row (row.labelEn)}
								<tr>
									<td class="acct">{lang === 'en' ? row.labelEn : row.labelKr}</td>
									{#each grid.periods as p (p)}
										{@const c = row.cells.get(p)}
										{@const primary = c?.[scenario]}
										<td class="r mono" title={c?.[25] != null && c?.[75] != null ? `25~75%: ${fmtJo(c[25])} ~ ${fmtJo(c[75])}` : undefined}>
											{#if primary != null}<b class={primary < 0 ? 'tDn' : ''}>{fmtJo(primary)}</b><span class="band">{fmtJo(c?.[25])}~{fmtJo(c?.[75])}</span>{:else}·{/if}
										</td>
									{/each}
								</tr>
							{/each}
						</tbody>
					</table></div>
					<div class="expUnit">{lang === 'en' ? 'unit: KRW trillion · bold = selected scenario · below = 25~75% band' : '단위: 조원 · 굵은 값 = 선택 시나리오 · 아래 = 25~75% 구간'}</div>
				{:else}
					<div class="expEmpty">{lang === 'en' ? 'no sealed estimates for this statement/period yet' : '이 표·기간의 봉인 추정 없음 (분기 sweep 대기)'}</div>
				{/if}
			</section>

			<div class="expTwoCol">
				<!-- (2) 채점 트랙레코드 -->
				<section class="expBlock">
					<div class="expBlockHead"><span class="expBlockTitle">{lang === 'en' ? 'Track record · sealed band vs actual' : '채점 · 봉인 구간 vs 실제'}</span></div>
					{#if track.length}
						<table class="expDlgTable compact">
							<thead><tr><th>{lang === 'en' ? 'metric' : '지표'}</th><th>{lang === 'en' ? 'target' : '대상'}</th><th class="r">p25~p75</th><th class="r">{lang === 'en' ? 'actual' : '실제'}</th><th class="r">{lang === 'en' ? 'verdict' : '판정'}</th></tr></thead>
							<tbody>
								{#each track as x (x.e.expectationId)}
									{@const q = x.e.quantiles}
									<tr>
										<td>{varLabel(x.e.variable)}</td>
										<td class="mono">{x.e.targetPeriod}</td>
										<td class="r mono expDim">{q ? `${fmtLevel(q[25], x.e.variable)}~${fmtLevel(q[75], x.e.variable)}` : '·'}</td>
										<td class="r mono"><b>{x.s.actual != null ? fmtLevel(Number(x.s.actual), x.e.variable) : '·'}</b></td>
										<td class="r"><span class={x.s.coverageHit90 ? 'tUp' : 'tWarn'}>{x.s.coverageHit90 ? (lang === 'en' ? 'in band' : '적중') : (lang === 'en' ? 'missed' : '이탈')}</span>{#if x.s.skill != null}<span class="skill" title="skill vs naive baseline"> {x.s.skill > 0 ? '+' : ''}{x.s.skill.toFixed(2)}</span>{/if}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{:else}
						<div class="expEmpty">{lang === 'en' ? 'no scored expectations arrived yet' : '아직 채점 도착분 없음'}</div>
					{/if}
				</section>

				<!-- (3) 시장 기대 + 방법 -->
				<section class="expBlock">
					<div class="expBlockHead"><span class="expBlockTitle">{lang === 'en' ? 'Market fan · macro' : '시장 기대 · 매크로'}</span></div>
					{#if market.length}
						<table class="expDlgTable compact">
							<thead><tr><th>{lang === 'en' ? 'variable' : '변수'}</th><th>{lang === 'en' ? 'target' : '대상'}</th><th class="r">p50</th><th class="r">p25~p75</th></tr></thead>
							<tbody>
								{#each market as m (m.sid)}
									{@const q = m.r.quantiles}
									<tr>
										<td>{varLabel(m.sid)}</td>
										<td class="mono">{m.r.targetPeriod}</td>
										<td class="r mono"><b>{q ? fmtLevel(q[50], m.sid) : '·'}</b></td>
										<td class="r mono expDim">{q ? `${fmtLevel(q[25], m.sid)}~${fmtLevel(q[75], m.sid)}` : '·'}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{:else}
						<div class="expEmpty">{lang === 'en' ? 'no macro fan issued' : '매크로 팬 미발행'}</div>
					{/if}
					<div class="expMethod">
						<div class="expMethodHead">{lang === 'en' ? 'method · lineage' : '방법 · 계보'}</div>
						<div class="expMethodBody">
							{lang === 'en'
								? 'Estimates re-run the unchanged engines through forecast inputs (revenue driver → proforma cascade), sealed at issuance and never edited.'
								: '추정은 입력(매출 드라이버 → proforma 전개)만 예측하고 엔진을 그대로 재실행한 결과입니다. 발행 순간 봉인되며 사후 수정 불가.'}
							{#each methodNote.warns as w (w)}<span class="warnTag">{warnText(w)}</span>{/each}
						</div>
						{#if scorecard}
							<div class="expMethodBody dim">{lang === 'en'
								? `${scorecard.totals.issued} issued · ${scorecard.totals.scored} scored · ${scorecard.totals.unscored} pending. Calibration claims wait for the sample gate.`
								: `발행 ${scorecard.totals.issued} · 채점 ${scorecard.totals.scored} · 대기 ${scorecard.totals.unscored}. 적중률 주장은 표본 게이트 이후에만.`}</div>
						{/if}
					</div>
				</section>
			</div>
		</div>
	</div>
</div>

<style>
	.expDlg {
		width: min(96vw, 1180px);
		max-height: 92vh;
		display: flex;
		flex-direction: column;
	}
	.expWho {
		font-family: var(--cond);
		font-weight: 700;
		font-size: 13px;
		color: var(--txt);
		margin-left: 10px;
	}
	.expWho i {
		font-style: normal;
		font-weight: 400;
		font-size: 10.5px;
		color: var(--dim);
		margin-left: 6px;
	}
	.expLens {
		margin-left: auto;
		margin-right: 12px;
		font-family: var(--mono);
		font-size: 9.5px;
		color: var(--dimmer);
	}
	.expDlgBody {
		overflow-y: auto;
		padding: 10px 12px 14px;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.expBlock {
		border: 1px solid var(--bd);
		border-radius: 3px;
		background: var(--panel);
	}
	.expBlockHead {
		display: flex;
		align-items: center;
		gap: 10px;
		flex-wrap: wrap;
		padding: 6px 9px;
		border-bottom: 1px solid var(--bd);
	}
	.expBlockTitle {
		font-family: var(--mono);
		font-size: 10px;
		font-weight: 700;
		letter-spacing: 0.4px;
		text-transform: uppercase;
		color: var(--dim);
	}
	.expSeg {
		display: inline-flex;
		gap: 0;
		border: 1px solid var(--bd);
		border-radius: 3px;
		overflow: hidden;
	}
	.expSeg button {
		font-family: var(--cond);
		font-size: 10.5px;
		font-weight: 600;
		padding: 2px 9px;
		background: transparent;
		color: var(--dim);
		border: 0;
		border-right: 1px solid var(--bd);
		cursor: pointer;
	}
	.expSeg button:last-child {
		border-right: 0;
	}
	.expSeg button.on {
		background: rgba(var(--amber-rgb), 0.16);
		color: var(--amber);
	}
	.scenSeg button.scen25.on {
		background: rgba(var(--dn-rgb, 240, 90, 90), 0.18);
		color: var(--dn);
	}
	.scenSeg button.scen75.on {
		background: rgba(var(--up-rgb, 90, 200, 120), 0.18);
		color: var(--up);
	}
	.expTblScroll {
		overflow-x: auto;
		max-height: 340px;
		overflow-y: auto;
	}
	.expDlgTable {
		width: 100%;
		border-collapse: collapse;
	}
	.expDlgTable th {
		font-family: var(--mono);
		font-size: 9px;
		font-weight: 600;
		color: var(--dimmer);
		text-align: left;
		padding: 3px 8px;
		border-bottom: 1px solid var(--dl-line);
		position: sticky;
		top: 0;
		background: var(--panel);
		white-space: nowrap;
	}
	.expDlgTable th.r,
	.expDlgTable td.r {
		text-align: right;
	}
	.expDlgTable th i {
		font-style: normal;
		color: var(--amber);
		margin-left: 2px;
	}
	.expDlgTable td {
		font-family: var(--mono);
		font-size: 10.5px;
		color: var(--txt);
		padding: 3px 8px;
		border-bottom: 1px solid var(--dl-line);
		white-space: nowrap;
		vertical-align: top;
	}
	.expDlgTable td.acct,
	.expDlgTable th.acct {
		font-family: var(--cond);
		font-weight: 600;
		color: var(--amber);
		position: sticky;
		left: 0;
		background: var(--panel);
		z-index: 1;
	}
	.expDlgTable td b {
		font-weight: 600;
		font-size: 11.5px;
	}
	.expDlgTable .band {
		display: block;
		font-size: 8.5px;
		color: var(--dimmer);
		line-height: 1.35;
	}
	.expDlgTable.compact td,
	.expDlgTable.compact th {
		padding: 2.5px 8px;
	}
	.expDim {
		color: var(--dimmer);
	}
	.skill {
		color: var(--dim);
		font-size: 9px;
	}
	.expUnit,
	.expEmpty {
		font-family: var(--mono);
		font-size: 9px;
		color: var(--dimmer);
		padding: 5px 9px;
	}
	.expTwoCol {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 12px;
	}
	.expMethod {
		padding: 7px 9px;
		border-top: 1px solid var(--bd);
	}
	.expMethodHead {
		font-family: var(--mono);
		font-size: 9px;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.3px;
		color: var(--dim);
		margin-bottom: 3px;
	}
	.expMethodBody {
		font-family: var(--cond);
		font-size: 10.5px;
		line-height: 1.5;
		color: var(--txt);
	}
	.expMethodBody.dim {
		color: var(--dimmer);
		margin-top: 4px;
	}
	.warnTag {
		display: inline-block;
		font-family: var(--mono);
		font-size: 8.5px;
		color: var(--amber);
		background: rgba(var(--amber-rgb), 0.1);
		border-radius: 2px;
		padding: 0 5px;
		margin: 2px 3px 0 0;
	}
	@media (max-width: 720px) {
		.expTwoCol {
			grid-template-columns: 1fr;
		}
	}
</style>
