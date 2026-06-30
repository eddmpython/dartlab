<script lang="ts">
	// 주석 상세 · 비용 체질 + 부문별 매출. 카드별 = 100% 스택바(당기 구성 한눈에) + 분기별 구성 테이블(밀도).
	// 데이터 = panel 정부 XBRL 태그 런타임 직독(reportSource.noteSeries). 종합점수·판정 0(NEVER-CLAIM).
	import type { Company, Lang } from '../lib/types';
	import type { CompositionSeries } from '@dartlab/ui-contracts';
	import { fmtKRW } from '../lib/engine';

	interface Props {
		co: Company;
		lang: Lang;
		cost: CompositionSeries | null;
		segment: CompositionSeries | null;
		onClose: () => void;
	}
	let { co, lang, cost, segment, onClose }: Props = $props();
	const T = (kr: string, en: string): string => (lang === 'en' ? en : kr);

	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

	const PAL = ['var(--dl-cat-start)', 'var(--dl-cat-operation)', 'var(--dl-cat-engines)', 'var(--dl-cat-runtime)', 'var(--dl-cat-recipes)', 'var(--dl-accent)', 'var(--up)', 'var(--warn)'];
	const catColor = (i: number, name: string): string => (name === '기타' ? 'var(--dimmer)' : (PAL[i % PAL.length] ?? 'var(--dim)'));
	const niceName = (n: string): string => {
		if (n === '기타') return T('기타', 'other');
		const t = n.replace(/\s*및\s*/g, '·').replace(/(매입액|사용액|비용|비$)/g, '').trim();
		if (/^[A-Za-z]{1,4}$/.test(t)) return t.toUpperCase();
		return t.replace(/([a-z])([A-Z])/g, '$1 $2').slice(0, 16);
	};
	const shortPeriod = (p: string): string => p.replace(/^20/, '');

	interface TblRow {
		name: string;
		color: string;
		pcts: (number | null)[];
		latestPct: number;
		amt: number;
	}
	interface TsCol {
		label: string;
		total: number;
		segs: { name: string; color: string; pct: number }[]; // 그 기간 카테고리 비중%(스택 세그먼트)
	}
	interface TblCard {
		titleKr: string;
		titleEn: string;
		subKr: string;
		subEn: string;
		quarters: string[];
		cols: TsCol[]; // 시계열 스택 · 기간(분기)별 컬럼
		rows: TblRow[];
		latestPeriod: string;
		latestTotal: number;
		annual: boolean;
	}
	function makeCard(series: CompositionSeries | null, titleKr: string, titleEn: string, subKr: string, subEn: string): TblCard | null {
		if (!series || !series.points.length) return null;
		const pts = series.points;
		const last = pts[pts.length - 1]!;
		const rows: TblRow[] = series.categories
			.map((name, c) => ({
				name,
				color: catColor(c, name),
				pcts: pts.map((p) => p.shares[c] ?? null),
				latestPct: last.shares[c] ?? 0,
				amt: ((last.shares[c] ?? 0) / 100) * last.total
			}))
			.filter((r) => r.latestPct > 0.05) // 당기 0 인 사족 행 제거(태그 변경 잔여 등)
			.sort((a, b) => b.latestPct - a.latestPct);
		if (!rows.length) return null;
		// 시계열 스택 · 각 기간(분기)을 100% 적층 컬럼으로. 세그먼트 순서 = rows(당기 비중 desc) 고정이라 색 밴드가 기간 가로질러 흐름.
		const cols: TsCol[] = pts.map((p, j) => ({
			label: shortPeriod(p.period),
			total: p.total,
			segs: rows.map((r) => ({ name: r.name, color: r.color, pct: r.pcts[j] ?? 0 }))
		}));
		return { titleKr, titleEn, subKr, subEn, quarters: pts.map((p) => shortPeriod(p.period)), cols, rows, latestPeriod: last.period, latestTotal: last.total, annual: last.quarter === '4분기' };
	}
	const cards = $derived(
		[makeCard(cost, '비용 체질', 'COST CHASSIS', '돈을 뭐에 쓰나', 'where the money goes'), makeCard(segment, '부문별 매출', 'SEGMENT REVENUE', '어디서 버나', 'revenue by segment')].filter((c): c is TblCard => c != null)
	);
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div class="scrModal ndModal" role="dialog" aria-modal="true" tabindex="-1" aria-label={T('주석 상세', 'notes detail')} onclick={(e) => e.stopPropagation()}>
		<div class="scrHead">
			<span class="scrTitle">{T('주석', 'NOTES')} · {co.name.kr}</span>
			<span class="ndHeadMeta">{T('분기 = YTD 누적', 'quarter = YTD')}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>
		<div class="ndBody">
			{#each cards as c (c.titleEn)}
				<div class="ndHero">
					<div class="ndCardHd">
						<span class="ndCardTitle">{T(c.titleKr, c.titleEn)} <span class="dim">· {T(c.subKr, c.subEn)}</span></span>
						<span class="ndHdRight">{T('당기', 'period')} <b class="mono">{fmtKRW(c.latestTotal)}</b> · {c.latestPeriod}</span>
					</div>
					<!-- 시계열 스택 · 분기별 100% 적층 컬럼(왼→오 과거→당기). 색 = 카테고리, 밴드가 기간 가로질러 흐름. -->
					<div class="ndTs" role="img" aria-label={T(c.titleKr, c.titleEn) + ' time series'}>
						{#each c.cols as col, j (col.label)}
							<div class="ndTsCol">
								<div class="ndTsBar">
									{#each col.segs as s (s.name)}
										{#if s.pct > 0.05}<i style={`height:${s.pct}%;background:${s.color}`} title={`${col.label} · ${niceName(s.name)} ${s.pct.toFixed(1)}%`}></i>{/if}
									{/each}
								</div>
								<span class={'ndTsLbl ' + (j === c.cols.length - 1 ? 'ndCur' : '')}>{col.label}</span>
							</div>
						{/each}
					</div>
					<table class="ndTbl">
						<thead>
							<tr>
								<th class="ndTblName">{T('카테고리', 'category')}</th>
								{#each c.quarters as q (q)}<th class="r mono">{q}</th>{/each}
								<th class="r mono ndTblAmt">{T('당기', 'amt')}</th>
							</tr>
						</thead>
						<tbody>
							{#each c.rows as r (r.name)}
								<tr>
									<td class="ndTblName"><i class="ndDot" style={`background:${r.color}`}></i>{niceName(r.name)}</td>
									{#each r.pcts as p, i (i)}<td class={'r mono ' + (i === r.pcts.length - 1 ? 'ndCur' : 'dim')}>{p == null ? '·' : p.toFixed(1)}</td>{/each}
									<td class="r mono ndTblAmt">{fmtKRW(r.amt)}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/each}
			{#if !cards.length}
				<div class="storyEmpty">{T('비용 성격별·부문 주석 미공시 (또는 단일부문). 상세는 뷰어.', 'no cost-by-nature / segment note (or single-segment).')}</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.ndHeadMeta {
		font-family: var(--cond);
		font-size: 9.5px;
		color: var(--dimmer);
		letter-spacing: 0.03em;
	}
	.ndTs {
		display: flex;
		align-items: flex-end;
		gap: 5px;
		margin: 8px 0 9px;
		height: 104px;
	}
	.ndTsCol {
		flex: 1;
		display: flex;
		flex-direction: column;
		align-items: center;
		height: 100%;
		min-width: 0;
	}
	.ndTsBar {
		flex: 1;
		width: 22px;
		display: flex;
		flex-direction: column;
		border-radius: 2px;
		overflow: hidden;
		background: var(--dl-bg-deep);
	}
	.ndTsBar i {
		display: block;
		width: 100%;
		min-height: 1px;
	}
	.ndTsLbl {
		font-family: var(--mono);
		font-size: 9.5px;
		color: var(--dimmer);
		text-align: center;
		padding-top: 4px;
	}
	.ndTsLbl.ndCur {
		color: var(--fg);
		font-weight: 700;
	}
	.ndTbl {
		width: 100%;
		border-collapse: collapse;
		font-family: var(--mono);
		font-size: 11px;
	}
	.ndTbl th {
		font-family: var(--cond);
		font-size: 9px;
		letter-spacing: 0.04em;
		color: var(--dimmer);
		font-weight: 600;
		padding: 2px 7px;
		border-bottom: 1px solid var(--bd);
		text-transform: uppercase;
	}
	.ndTbl td {
		padding: 3px 7px;
		border-bottom: 1px solid color-mix(in srgb, var(--bd) 40%, transparent);
		color: var(--txt);
	}
	.ndTbl tbody tr:hover td {
		background: rgba(91, 155, 240, 0.06);
	}
	.ndTbl .r {
		text-align: right;
	}
	.ndTblName {
		text-align: left;
		white-space: nowrap;
		max-width: 180px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.ndDot {
		display: inline-block;
		width: 8px;
		height: 8px;
		border-radius: 2px;
		margin-right: 6px;
	}
	.ndTbl .dim {
		color: var(--dim);
	}
	.ndTbl .ndCur {
		color: var(--fg);
		font-weight: 600;
	}
	.ndTblAmt {
		color: var(--fg);
	}
</style>
