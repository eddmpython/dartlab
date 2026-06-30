<script lang="ts">
	import { fmtPct } from '@dartlab/ui-format/pct';
	import type { FilingPort, RegularFiling } from '@dartlab/ui-contracts';
	import type { DartDb } from './duckSql';
	import { FINANCE_COMPLETED_YEARS, financeMetricKey } from './financeAccounts';
	import { loadCompanyFinanceLitePeriods, type CompanyFinancePeriodRow } from './financeLiteRuntime';
	import { gradeTone, toneColor } from './grade';
	import type { ScanNode } from './types';

	interface Props {
		node: ScanNode;
		db: DartDb | null;
		financeLoading?: boolean;
		onClose: () => void;
		// 셸 주입 · surface 는 $app/paths·publicRuntime 무결합(포터블). filing=공시 포트(정기공시), basePath=뷰어 링크.
		filing: FilingPort;
		basePath?: string;
	}

	type Point = { year: string; label: string; [key: string]: number | string | null };
	type ChartHover = { title: string; x: number; y: number; lines: string[] };

	const DETAIL_PERIOD_LIMIT = 12;

	let { node, db: _db, financeLoading = false, onClose, filing, basePath = '' }: Props = $props();
	let filings = $state<RegularFiling[]>([]);
	let financePeriods = $state<CompanyFinancePeriodRow[]>([]);
	let filingsLoading = $state(false);
	let periodsLoading = $state(false);
	let chartHover = $state<ChartHover | null>(null);

	$effect(() => {
		const code = node.id;
		filingsLoading = true;
		void filing.regular(code, 40)
			.then((rows) => {
				if (node.id === code) filings = rows;
			})
			.catch(() => {
				if (node.id === code) filings = [];
			})
			.finally(() => {
				if (node.id === code) filingsLoading = false;
			});
		periodsLoading = true;
		void loadCompanyFinanceLitePeriods(code, fetch, DETAIL_PERIOD_LIMIT)
			.then((rows) => {
				if (node.id === code) financePeriods = rows;
			})
			.catch(() => {
				if (node.id === code) financePeriods = [];
			})
			.finally(() => {
				if (node.id === code) periodsLoading = false;
			});
	});

	function valueAt(accountId: string, year: string): number | null {
		const value = (node as Record<string, unknown>)[financeMetricKey(accountId, year)];
		return typeof value === 'number' && Number.isFinite(value) ? value : null;
	}

	function wonToEok(value: number | null): number | null {
		return value == null ? null : value / 1e8;
	}

	function periodValueAt(period: CompanyFinancePeriodRow, accountId: string): number | null {
		const value = period.values[accountId];
		return typeof value === 'number' && Number.isFinite(value) ? value : null;
	}

	let isData = $derived.by<Point[]>(() =>
		financePeriods.length
			? financePeriods.map((period) => ({
					year: period.period,
					label: period.label,
					sales: wonToEok(periodValueAt(period, 'sales')),
					op: wonToEok(periodValueAt(period, 'operating_profit')),
					net: wonToEok(periodValueAt(period, 'net_income'))
				}))
			: FINANCE_COMPLETED_YEARS.map((year) => ({
					year,
					label: year.slice(2),
					sales: wonToEok(valueAt('sales', year)),
					op: wonToEok(valueAt('operating_profit', year)),
					net: wonToEok(valueAt('net_income', year))
				}))
	);
	let bsData = $derived.by<Point[]>(() =>
		financePeriods.length
			? financePeriods.map((period) => {
					const currentLiabilities = wonToEok(periodValueAt(period, 'current_liabilities'));
					const noncurrentLiabilities = wonToEok(periodValueAt(period, 'noncurrent_liabilities'));
					const totalLiabilities = sumNullable(currentLiabilities, noncurrentLiabilities);
					const operatingLiabilities = wonToEok(periodValueAt(period, 'trade_payables'));
					const equity = wonToEok(periodValueAt(period, 'total_stockholders_equity'));
					const retainedEarnings = wonToEok(periodValueAt(period, 'retained_earnings'));
					return {
						year: period.period,
						label: period.label,
						operatingLiabilities,
						nonOperatingLiabilities: remainder(totalLiabilities, operatingLiabilities),
						retainedEarnings,
						otherEquity: remainder(equity, retainedEarnings),
						totalLiabilities,
						equity
					};
				})
			: FINANCE_COMPLETED_YEARS.map((year) => {
					const currentLiabilities = wonToEok(valueAt('current_liabilities', year));
					const noncurrentLiabilities = wonToEok(valueAt('noncurrent_liabilities', year));
					const totalLiabilities = sumNullable(currentLiabilities, noncurrentLiabilities);
					const operatingLiabilities = wonToEok(valueAt('trade_payables', year));
					const equity = wonToEok(valueAt('total_stockholders_equity', year));
					const retainedEarnings = wonToEok(valueAt('retained_earnings', year));
					return {
						year,
						label: year.slice(2),
						operatingLiabilities,
						nonOperatingLiabilities: remainder(totalLiabilities, operatingLiabilities),
						retainedEarnings,
						otherEquity: remainder(equity, retainedEarnings),
						totalLiabilities,
						equity
					};
				})
	);
	let cfData = $derived.by<Point[]>(() =>
		financePeriods.length
			? financePeriods.map((period) => ({
					year: period.period,
					label: period.label,
					ocf: wonToEok(periodValueAt(period, 'operating_cashflow')),
					icf: wonToEok(periodValueAt(period, 'investing_cashflow')),
					fcf: wonToEok(periodValueAt(period, 'financing_cashflow'))
				}))
			: FINANCE_COMPLETED_YEARS.map((year) => ({
					year,
					label: year.slice(2),
					ocf: wonToEok(valueAt('operating_cashflow', year)),
					icf: wonToEok(valueAt('investing_cashflow', year)),
					fcf: wonToEok(valueAt('financing_cashflow', year))
				}))
	);

	let hasFinance = $derived([...isData, ...bsData, ...cfData].some((row) => hasNumber(row)));
	let isMax = $derived(maxAbs(isData, ['sales', 'op', 'net']));
	let profitMax = $derived(maxAbs(isData, ['op', 'net']));
	let isOpPath = $derived(linePath(isData, 'op', profitMax));
	let isNetPath = $derived(linePath(isData, 'net', profitMax));
	let bsMax = $derived(maxStack(bsData, ['operatingLiabilities', 'nonOperatingLiabilities', 'retainedEarnings', 'otherEquity']));
	let cfMax = $derived(maxAbs(cfData, ['ocf', 'icf', 'fcf']));
	let cfOcfPath = $derived(linePath(cfData, 'ocf', cfMax));
	let cfIcfPath = $derived(linePath(cfData, 'icf', cfMax));
	let cfFcfPath = $derived(linePath(cfData, 'fcf', cfMax));

	const GRADE_COLS = [
		{ key: 'profGrade', label: '수익성' },
		{ key: 'debtGrade', label: '부채' },
		{ key: 'qualGrade', label: '이익질' },
		{ key: 'liqGrade', label: '유동성' },
		{ key: 'govGrade', label: '거버넌스' },
		{ key: 'auditRisk', label: '감사' }
	];

	function hasNumber(row: Record<string, unknown>): boolean {
		return Object.entries(row).some(([key, value]) => key !== 'year' && typeof value === 'number' && Number.isFinite(value));
	}

	function formatDate(value: string): string {
		if (!/^\d{8}$/.test(value)) return value || '·';
		return `${value.slice(0, 4)}.${value.slice(4, 6)}.${value.slice(6, 8)}`;
	}

	function handleKey(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}

	const W = 420;
	const H = 174;
	const PAD = { top: 18, right: 28, bottom: 24, left: 28 };
	const plotW = W - PAD.left - PAD.right;
	const plotH = H - PAD.top - PAD.bottom;

	function chartValues(data: Point[], keys: string[]): number[] {
		return data.flatMap((d) =>
			keys.map((k) => d[k]).filter((v): v is number => typeof v === 'number' && Number.isFinite(v))
		);
	}
	function maxAbs(data: Point[], keys: string[]): number {
		const values = chartValues(data, keys).map((v) => Math.abs(v));
		if (values.length === 0) return 1;
		const max = Math.max(...values);
		return max > 0 ? max : 1;
	}
	function maxStack(data: Point[], keys: string[]): number {
		const values = data.map((d) => keys.reduce((sum, k) => sum + Math.max(0, Number(d[k]) || 0), 0));
		if (values.length === 0) return 1;
		const max = Math.max(...values);
		return max > 0 ? max : 1;
	}
	function sumNullable(...values: Array<number | null>): number | null {
		const nums = values.filter((v): v is number => typeof v === 'number' && Number.isFinite(v));
		if (nums.length === 0) return null;
		return nums.reduce((sum, value) => sum + value, 0);
	}
	function remainder(total: number | null, part: number | null): number | null {
		if (total == null) return null;
		return Math.max(0, total - (part ?? 0));
	}
	function x(i: number, count: number): number {
		return PAD.left + (i + 0.5) * (plotW / Math.max(count, 1));
	}
	function barWidth(count: number, maxWidth: number): number {
		return Math.max(6, Math.min(maxWidth, (plotW / Math.max(count, 1)) * 0.58));
	}
	function ySigned(v: number, max: number): number {
		return PAD.top + plotH / 2 - (v / max) * (plotH / 2);
	}
	function linePath(data: Point[], key: string, max: number): string {
		const pts = data
			.map((d, i) => {
				const v = d[key];
				return typeof v === 'number' && Number.isFinite(v) ? `${x(i, data.length)},${ySigned(v, max)}` : '';
			})
			.filter(Boolean);
		return pts.length >= 2 ? `M${pts.join('L')}` : '';
	}
	function fmtAmount(v: number | null): string {
		if (v == null) return '·';
		const abs = Math.abs(v);
		const maximumFractionDigits = abs >= 100 ? 0 : 1;
		return `${v.toLocaleString('ko-KR', { maximumFractionDigits })}억원`;
	}
	function numAt(row: Point, key: string): number | null {
		const v = row?.[key];
		return typeof v === 'number' && Number.isFinite(v) ? v : null;
	}
	function showHover(e: MouseEvent, title: string, lines: string[]) {
		const rect = (e.currentTarget as SVGElement).getBoundingClientRect();
		chartHover = { title, lines, x: rect.left + rect.width / 2, y: rect.top + 8 };
	}
	function hideHover() {
		chartHover = null;
	}
</script>

<svelte:window onkeydown={handleKey} />

<aside class="detail" aria-label="회사 디테일">
	<header class="d-head">
		<div class="d-head-left">
			<span class="d-ind-dot" style:background={(node.color as string) || '#475569'}></span>
			<span class="d-label">{node.label}</span>
			<span class="d-id">{node.id}</span>
			<span class="d-ind">{node.industryName}</span>
		</div>
		<div class="d-head-right">
			<button type="button" class="d-close" onclick={onClose} aria-label="닫기 (Esc)">X</button>
		</div>
	</header>

	<div class="d-body">
		{#if (financeLoading || periodsLoading) && !hasFinance}
			<section class="d-section chart-loading">
				<div class="loading">로드 중...</div>
			</section>
		{:else}
			<section class="d-section mini-chart">
				<div class="mini-title">IS</div>
						<svg viewBox="0 0 {W} {H}">
							<line x1={PAD.left} x2={W - PAD.right} y1={PAD.top + plotH} y2={PAD.top + plotH} stroke="#334155" />
							<line x1={W - PAD.right} x2={W - PAD.right} y1={PAD.top} y2={PAD.top + plotH} stroke="#334155" stroke-dasharray="2 3" />
							{#each isData as d, i}
								{@const sales = typeof d.sales === 'number' ? d.sales : 0}
								{@const barH = (Math.max(0, sales) / isMax) * plotH}
								{@const bw = barWidth(isData.length, 30)}
								<rect
									role="presentation"
									x={x(i, isData.length) - bw / 2}
									y={PAD.top + plotH - barH}
									width={bw}
									height={barH}
									rx="2"
									fill="#2563eb"
									opacity="0.72"
									onmouseenter={(e) =>
										showHover(e, `IS ${d.label}`, [
											`매출 ${fmtAmount(numAt(d, 'sales'))}`,
											`영업이익 ${fmtAmount(numAt(d, 'op'))}`,
											`당기순이익 ${fmtAmount(numAt(d, 'net'))}`
										])}
									onmouseleave={hideHover}
								/>
								<text x={x(i, isData.length)} y={H - 5} text-anchor="middle" fill="#64748b" font-size="9">{d.label}</text>
							{/each}
							{#if isOpPath}<path d={isOpPath} fill="none" stroke="#22c55e" stroke-width="2.2" />{/if}
							{#if isNetPath}<path d={isNetPath} fill="none" stroke="#ec4899" stroke-width="2" stroke-dasharray="4 3" />{/if}
							{#each isData as d, i}
								{#if typeof d.op === 'number'}
									<circle
										role="presentation"
										cx={x(i, isData.length)}
										cy={ySigned(d.op, profitMax)}
										r="2.7"
										fill="#22c55e"
										onmouseenter={(e) =>
											showHover(e, `IS ${d.label}`, [
												`매출 ${fmtAmount(numAt(d, 'sales'))}`,
												`영업이익 ${fmtAmount(numAt(d, 'op'))}`,
												`당기순이익 ${fmtAmount(numAt(d, 'net'))}`
											])}
										onmouseleave={hideHover}
									/>
								{/if}
								{#if typeof d.net === 'number'}
									<circle
										role="presentation"
										cx={x(i, isData.length)}
										cy={ySigned(d.net, profitMax)}
										r="2.7"
										fill="#ec4899"
										onmouseenter={(e) =>
											showHover(e, `IS ${d.label}`, [
												`매출 ${fmtAmount(numAt(d, 'sales'))}`,
												`영업이익 ${fmtAmount(numAt(d, 'op'))}`,
												`당기순이익 ${fmtAmount(numAt(d, 'net'))}`
											])}
										onmouseleave={hideHover}
									/>
								{/if}
								<rect
									role="presentation"
									x={x(i, isData.length) - plotW / Math.max(isData.length, 1) / 2}
									y={PAD.top}
									width={plotW / Math.max(isData.length, 1)}
									height={plotH}
									fill="transparent"
									onmouseenter={(e) =>
										showHover(e, `IS ${d.label}`, [
											`매출 ${fmtAmount(numAt(d, 'sales'))}`,
											`영업이익 ${fmtAmount(numAt(d, 'op'))}`,
											`당기순이익 ${fmtAmount(numAt(d, 'net'))}`
										])}
									onmouseleave={hideHover}
								/>
							{/each}
							<text x="6" y="14" fill="#64748b" font-size="10">단위 억원</text>
							<text x={W - 6} y="14" text-anchor="end" fill="#64748b" font-size="10">매출/이익 별도축</text>
						</svg>
						<div class="legend"><span class="b"></span>매출액 <span class="g"></span>영업이익 <span class="o"></span>당기순이익</div>
			</section>
			<section class="d-section mini-chart">
				<div class="mini-title">BS</div>
						<svg viewBox="0 0 {W} {H}">
							{#each bsData as d, i}
								{@const bw = barWidth(bsData.length, 28)}
								{@const opLiab = typeof d.operatingLiabilities === 'number' ? Math.max(0, d.operatingLiabilities) : 0}
								{@const nonOpLiab = typeof d.nonOperatingLiabilities === 'number' ? Math.max(0, d.nonOperatingLiabilities) : 0}
								{@const retained = typeof d.retainedEarnings === 'number' ? Math.max(0, d.retainedEarnings) : 0}
								{@const otherEq = typeof d.otherEquity === 'number' ? Math.max(0, d.otherEquity) : 0}
								{@const h1 = (opLiab / bsMax) * plotH}
								{@const h2 = (nonOpLiab / bsMax) * plotH}
								{@const h3 = (retained / bsMax) * plotH}
								{@const h4 = (otherEq / bsMax) * plotH}
								<g
									role="presentation"
									onmouseenter={(e) =>
										showHover(e, `BS ${d.label}`, [
											`영업부채 ${fmtAmount(numAt(d, 'operatingLiabilities'))}`,
											`비영업부채 ${fmtAmount(numAt(d, 'nonOperatingLiabilities'))}`,
											`이익잉여금 ${fmtAmount(numAt(d, 'retainedEarnings'))}`,
											`기타자본 ${fmtAmount(numAt(d, 'otherEquity'))}`
										])}
									onmouseleave={hideHover}
								>
									<rect x={x(i, bsData.length) - bw / 2} y={PAD.top + plotH - h1} width={bw} height={h1} fill="#ef4444" opacity="0.76" />
									<rect x={x(i, bsData.length) - bw / 2} y={PAD.top + plotH - h1 - h2} width={bw} height={h2} fill="#f97316" opacity="0.74" />
									<rect x={x(i, bsData.length) - bw / 2} y={PAD.top + plotH - h1 - h2 - h3} width={bw} height={h3} fill="#22c55e" opacity="0.76" />
									<rect x={x(i, bsData.length) - bw / 2} y={PAD.top + plotH - h1 - h2 - h3 - h4} width={bw} height={h4} fill="#14b8a6" opacity="0.76" />
								</g>
								<text x={x(i, bsData.length)} y={H - 5} text-anchor="middle" fill="#64748b" font-size="9">{d.label}</text>
							{/each}
							<text x="6" y="14" fill="#64748b" font-size="10">단위 억원</text>
						</svg>
						<div class="legend"><span class="r"></span>영업부채 <span class="o"></span>비영업부채 <span class="g"></span>이익잉여금 <span class="t"></span>기타자본</div>
			</section>
			<section class="d-section mini-chart">
				<div class="mini-title">CF</div>
						<svg viewBox="0 0 {W} {H}">
							<line x1={PAD.left} x2={W - PAD.right} y1={PAD.top + plotH / 2} y2={PAD.top + plotH / 2} stroke="#334155" />
							{#if cfOcfPath}<path d={cfOcfPath} fill="none" stroke="#22c55e" stroke-width="2.2" />{/if}
							{#if cfIcfPath}<path d={cfIcfPath} fill="none" stroke="#3b82f6" stroke-width="2" stroke-dasharray="4 3" />{/if}
							{#if cfFcfPath}<path d={cfFcfPath} fill="none" stroke="#a78bfa" stroke-width="2" stroke-dasharray="2 3" />{/if}
							{#each cfData as d, i}
								{#if typeof d.ocf === 'number'}
									<circle cx={x(i, cfData.length)} cy={ySigned(d.ocf, cfMax)} r="2.6" fill="#22c55e" />
								{/if}
								{#if typeof d.icf === 'number'}
									<circle cx={x(i, cfData.length)} cy={ySigned(d.icf, cfMax)} r="2.4" fill="#3b82f6" />
								{/if}
								{#if typeof d.fcf === 'number'}
									<circle cx={x(i, cfData.length)} cy={ySigned(d.fcf, cfMax)} r="2.4" fill="#a78bfa" />
								{/if}
								<rect
									role="presentation"
									x={x(i, cfData.length) - plotW / Math.max(cfData.length, 1) / 2}
									y={PAD.top}
									width={plotW / Math.max(cfData.length, 1)}
									height={plotH}
									fill="transparent"
									onmouseenter={(e) =>
										showHover(e, `CF ${d.label}`, [
											`영업CF ${fmtAmount(numAt(d, 'ocf'))}`,
											`투자CF ${fmtAmount(numAt(d, 'icf'))}`,
											`재무CF ${fmtAmount(numAt(d, 'fcf'))}`
										])}
									onmouseleave={hideHover}
								/>
								<text x={x(i, cfData.length)} y={H - 5} text-anchor="middle" fill="#64748b" font-size="9">{d.label}</text>
							{/each}
							<text x="6" y="14" fill="#64748b" font-size="10">단위 억원</text>
						</svg>
						<div class="legend"><span class="g"></span>영업CF <span class="b"></span>투자CF <span class="p"></span>재무CF</div>
			</section>
		{/if}

		<section class="d-section grades">
			<div class="sec-title">scan 등급</div>
			<div class="grade-grid">
				{#each GRADE_COLS as g (g.key)}
					{@const v = (node as Record<string, unknown>)[g.key]}
					{@const tone = gradeTone(g.key, v)}
					<div class="grade-cell">
						<span>{g.label}</span>
						{#if v && v !== ''}
							<span class="g-chip" style:color={toneColor(tone)} style:border-color={toneColor(tone)}>{v}</span>
						{:else}
							<span class="g-chip dim">·</span>
						{/if}
					</div>
				{/each}
			</div>
			<div class="delta-row">
				<span>ROE 변화 {typeof node.roeDelta === 'number' ? fmtPct(node.roeDelta, { withSign: true, suffix: '%p' }) : '·'}</span>
				<span>OPM 변화 {typeof node.opMarginDelta === 'number' ? fmtPct(node.opMarginDelta, { withSign: true, suffix: '%p' }) : '·'}</span>
			</div>
		</section>

		<section class="d-section filings">
			<div class="filings-head">
				<span class="sec-title">최근 정기공시</span>
				<a class="viewer-btn" href={`${basePath}/viewer/company/${node.id}`} target="_blank" rel="noreferrer" title="공시뷰어로 열기 · panel 항목×기간 격자·정량재무제표">공시뷰어 ↗</a>
			</div>
			{#if filingsLoading}
				<div class="loading">로드 중...</div>
			{:else if filings.length === 0}
				<div class="empty">정기공시 없음</div>
			{:else}
				<div class="filing-list">
					{#each filings as filing (filing.rceptNo)}
						<a class="filing-row" href={filing.url} target="_blank" rel="noreferrer">
							<span class="filing-title">{filing.reportType}</span>
							<span class="filing-date">{formatDate(filing.rceptDate)}</span>
						</a>
					{/each}
				</div>
			{/if}
		</section>
	</div>
</aside>

{#if chartHover}
	<div class="chart-tip" style:left={`${chartHover.x}px`} style:top={`${chartHover.y}px`}>
		<div class="tip-title">{chartHover.title}</div>
		{#each chartHover.lines as line}
			<div>{line}</div>
		{/each}
	</div>
{/if}

<style>
	.detail {
		flex-shrink: 0;
		background: #0a0e18;
		border: 1px solid #1e2433;
		border-radius: 6px;
		overflow: hidden;
		display: flex;
		flex-direction: column;
		height: var(--scan-detail-panel-height, 340px);
		max-height: var(--scan-detail-panel-height, 340px);
		min-height: var(--scan-detail-panel-height, 340px);
	}
	.d-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 12px;
		padding: 4px 10px;
		background: #0f172a;
		border-bottom: 1px solid #1e2433;
		flex-shrink: 0;
		min-height: 30px;
	}
	.d-head-left, .d-head-right {
		display: flex;
		align-items: center;
		gap: 8px;
		min-width: 0;
	}
	.d-ind-dot {
		width: 7px;
		height: 7px;
		border-radius: 50%;
		flex-shrink: 0;
	}
	.d-label {
		font-size: 12px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.d-id, .d-ind {
		font-size: 10px;
		color: #64748b;
	}
	.d-close {
		background: transparent;
		border: none;
		color: #64748b;
		cursor: pointer;
		font-size: 12px;
	}
	.d-body {
		flex: 1;
		min-height: 0;
		display: grid;
		grid-template-columns: repeat(3, minmax(230px, 1fr)) repeat(2, minmax(170px, 0.62fr));
		gap: 6px;
		padding: 6px;
		overflow: hidden;
	}
	.d-section {
		min-width: 0;
		min-height: 0;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 5px;
		padding: 6px;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	.chart-loading {
		grid-column: span 3;
		align-items: center;
		justify-content: center;
	}
	.sec-title {
		font-size: 10px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 4px;
	}
	/* 최근 정기공시 제목 라인 · 우측에 공시뷰어 바로가기 */
	.filings-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
		margin-bottom: 4px;
	}
	.filings-head .sec-title {
		margin-bottom: 0;
	}
	.viewer-btn {
		flex-shrink: 0;
		font-size: 10px;
		color: var(--amber);
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 4px;
		padding: 2px 7px;
		text-decoration: none;
		white-space: nowrap;
	}
	.viewer-btn:hover {
		background: rgba(var(--amber-rgb), 0.12);
		border-color: var(--amber);
	}
	.mini-chart {
		min-width: 0;
		min-height: 0;
		background: #070b14;
	}
	.mini-title {
		color: #cbd5e1;
		font-size: 10px;
		font-weight: 700;
		margin-bottom: 2px;
	}
	svg {
		width: 100%;
		height: auto;
		min-height: 128px;
		display: block;
		flex: 1;
	}
	.legend {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 4px;
		color: #94a3b8;
		font-size: 8.5px;
		line-height: 1.1;
		text-align: center;
		flex-wrap: wrap;
		overflow: hidden;
	}
	.legend span {
		width: 6px;
		height: 6px;
		border-radius: 2px;
		flex-shrink: 0;
	}
	.b { background: #2563eb; }
	.g { background: #22c55e; }
	.o { background: var(--amber); }
	.r { background: #ef4444; }
	.p { background: #a78bfa; }
	.t { background: #14b8a6; }
	.chart-tip {
		position: fixed;
		z-index: 2000;
		transform: translate(-50%, calc(-100% - 8px));
		padding: 6px 8px;
		background: #020617;
		border: 1px solid #334155;
		border-radius: 4px;
		color: #cbd5e1;
		font-size: 10px;
		line-height: 1.45;
		font-family: 'JetBrains Mono', 'Fira Code', monospace;
		font-variant-numeric: tabular-nums;
		pointer-events: none;
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
	}
	.tip-title {
		margin-bottom: 3px;
		color: #f8fafc;
		font-weight: 700;
		font-family: inherit;
	}
	.grade-grid {
		display: flex;
		flex-direction: column;
		gap: 0;
		min-height: 0;
		overflow: visible;
	}
	.grade-cell, .delta-row {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 6px;
		color: #94a3b8;
		font-size: 10px;
		min-width: 0;
	}
	.grade-cell {
		min-height: 21px;
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
	}
	.grade-cell > span:first-child {
		min-width: 0;
		overflow: visible;
		white-space: nowrap;
	}
	.delta-row {
		margin-top: 5px;
		display: grid;
		grid-template-columns: 1fr;
		align-items: start;
	}
	.delta-row span {
		min-width: 0;
		overflow: visible;
		white-space: nowrap;
	}
	.g-chip {
		padding: 1px 6px;
		font-size: 10px;
		font-weight: 700;
		border: 1px solid currentColor;
		border-radius: 3px;
		white-space: nowrap;
		flex-shrink: 0;
		min-width: 38px;
		text-align: center;
	}
	.g-chip.dim {
		color: #475569;
		border-color: #1e2433;
	}
	.grades, .filings {
		overflow-y: auto;
	}
	.filing-list {
		display: flex;
		flex-direction: column;
		gap: 0;
		min-height: 0;
		flex: 1;
		overflow-y: auto;
		padding-right: 2px;
	}
	.filing-row {
		min-width: 0;
		display: grid;
		grid-template-columns: minmax(0, 1fr) 70px;
		align-items: center;
		gap: 6px;
		padding: 4px 2px;
		border-bottom: 1px solid #1e2433;
		text-decoration: none;
	}
	.filing-row:hover {
		background: rgba(var(--amber-rgb), 0.06);
	}
	.filing-title {
		color: #f1f5f9;
		font-size: 11px;
		font-weight: 700;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.filing-date {
		color: #64748b;
		font-size: 10px;
		font-family: monospace;
		text-align: right;
	}
	.loading, .empty {
		padding: 20px 8px;
		text-align: center;
		color: #475569;
		font-size: 11px;
	}
	@media (max-width: 1180px) {
		.d-body {
			grid-template-columns: 1fr;
			overflow-y: auto;
		}
		.detail {
			height: 42vh;
			min-height: var(--scan-detail-panel-height, 340px);
			max-height: 42vh;
		}
	}
</style>
