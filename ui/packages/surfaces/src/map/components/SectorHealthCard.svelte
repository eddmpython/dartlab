<script lang="ts">
	/**
	 * 업종 체력 카드 · atlas 뷰에서 업종 클릭 시 오버레이.
	 * ROE/OPM/CAGR 분포 박스플롯 + 평균 + 동종사 수.
	 */

	interface Props {
		industryId: string;
		industryName: string;
		stat: any; // industryStats[industryId]
		onDrilldown?: () => void;
		onClose?: () => void;
	}

	let { industryId, industryName, stat, onDrilldown, onClose }: Props = $props();

	const dist = $derived(stat?.distribution || {});
	const count = $derived(stat?.count || 0);

	// Box plot data for each metric
	interface BoxData {
		label: string;
		unit: string;
		p10: number;
		p25: number;
		median: number;
		p75: number;
		p90: number;
		min: number;
		max: number;
		color: string;
	}

	let boxes = $derived.by((): BoxData[] => {
		const metrics = [
			{ key: 'roe', label: 'ROE', unit: '%', color: 'var(--color-dl-success)' },
			{ key: 'opMargin', label: '영업이익률', unit: '%', color: 'var(--color-dl-blue)' },
			{ key: 'revCagr', label: '매출 CAGR', unit: '%', color: 'var(--color-dl-accent)' }
		];

		return metrics
			.filter((m) => dist[m.key])
			.map((m) => {
				const d = dist[m.key];
				return {
					label: m.label,
					unit: m.unit,
					p10: d.p10,
					p25: d.p25,
					median: d.median,
					p75: d.p75,
					p90: d.p90,
					min: d.p10 - 5,
					max: d.p90 + 5,
					color: m.color
				};
			});
	});

	// Box plot SVG helpers
	function boxX(val: number, box: BoxData, w: number): number {
		const range = box.max - box.min || 1;
		return ((val - box.min) / range) * w;
	}
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="shc" onmousedown={(e) => e.stopPropagation()}>
	<header class="shc-head">
		<div class="shc-title">
			<h3>{industryName}</h3>
			<span class="shc-count">{count}개 기업</span>
		</div>
		<button class="shc-close" onclick={() => onClose?.()} aria-label="닫기">✕</button>
	</header>

	<div class="shc-body">
		<!-- 평균 지표 -->
		<div class="shc-avgs">
			{#if stat?.avgRoe != null}
				<div class="avg-item">
					<span class="avg-label">평균 ROE</span>
					<span class="avg-value" class:positive={stat.avgRoe > 0} class:negative={stat.avgRoe < 0}>
						{stat.avgRoe.toFixed(1)}%
					</span>
				</div>
			{/if}
			{#if stat?.avgOpMargin != null}
				<div class="avg-item">
					<span class="avg-label">평균 OPM</span>
					<span class="avg-value" class:positive={stat.avgOpMargin > 0} class:negative={stat.avgOpMargin < 0}>
						{stat.avgOpMargin.toFixed(1)}%
					</span>
				</div>
			{/if}
			{#if stat?.avgCagr != null}
				<div class="avg-item">
					<span class="avg-label">매출 CAGR</span>
					<span class="avg-value" class:positive={stat.avgCagr > 0} class:negative={stat.avgCagr < 0}>
						{stat.avgCagr.toFixed(1)}%
					</span>
				</div>
			{/if}
		</div>

		<!-- 분포 박스플롯 -->
		{#each boxes as box}
			<div class="box-row">
				<span class="box-label">{box.label}</span>
				<svg class="box-svg" viewBox="0 0 200 24" preserveAspectRatio="xMidYMid meet">
					<!-- whisker line (p10 ~ p90) -->
					<line
						x1={boxX(box.p10, box, 200)}
						y1="12"
						x2={boxX(box.p90, box, 200)}
						y2="12"
						stroke="rgba(148,163,184,0.4)"
						stroke-width="1"
					/>
					<!-- box (p25 ~ p75) -->
					<rect
						x={boxX(box.p25, box, 200)}
						y="4"
						width={boxX(box.p75, box, 200) - boxX(box.p25, box, 200)}
						height="16"
						fill={box.color}
						opacity="0.25"
						rx="2"
					/>
					<!-- median line -->
					<line
						x1={boxX(box.median, box, 200)}
						y1="2"
						x2={boxX(box.median, box, 200)}
						y2="22"
						stroke={box.color}
						stroke-width="2"
					/>
					<!-- p10 / p90 ticks -->
					<line x1={boxX(box.p10, box, 200)} y1="8" x2={boxX(box.p10, box, 200)} y2="16" stroke="rgba(148,163,184,0.5)" stroke-width="1" />
					<line x1={boxX(box.p90, box, 200)} y1="8" x2={boxX(box.p90, box, 200)} y2="16" stroke="rgba(148,163,184,0.5)" stroke-width="1" />
				</svg>
				<span class="box-median">{box.median.toFixed(1)}{box.unit}</span>
			</div>
		{/each}

		<!-- Top ROE 기업 -->
		{#if stat?.topRoe?.length}
			<div class="shc-top">
				<span class="top-label">ROE Top 3</span>
				<div class="top-list">
					{#each stat.topRoe.slice(0, 3) as t}
						<span class="top-item">{t.corpName} {t.roe?.toFixed(1)}%</span>
					{/each}
				</div>
			</div>
		{/if}
	</div>

	<footer class="shc-foot">
		<button class="shc-drill" onclick={() => onDrilldown?.()}>
			업종 상세 →
		</button>
	</footer>
</div>

<style>
	.shc {
		position: absolute;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		width: 340px;
		max-height: 80vh;
		background: var(--color-dl-bg-card);
		border: 1px solid var(--color-dl-border);
		border-radius: 12px;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
		z-index: 50;
		overflow: hidden;
		display: flex;
		flex-direction: column;
	}
	.shc-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 12px 16px;
		border-bottom: 1px solid var(--color-dl-border);
		background: linear-gradient(180deg, rgba(234, 70, 71, 0.06), transparent);
	}
	.shc-title h3 {
		margin: 0;
		font-size: 15px;
		font-weight: 700;
		color: var(--color-dl-text);
	}
	.shc-count {
		font-size: 11px;
		color: var(--color-dl-text-dim);
	}
	.shc-close {
		background: none;
		border: none;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		font-size: 14px;
		padding: 4px;
		border-radius: 4px;
	}
	.shc-close:hover {
		background: rgba(239, 68, 68, 0.1);
		color: var(--color-dl-primary-light);
	}
	.shc-body {
		padding: 12px 16px;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.shc-avgs {
		display: flex;
		gap: 12px;
	}
	.avg-item {
		flex: 1;
		text-align: center;
	}
	.avg-label {
		display: block;
		font-size: 10px;
		color: var(--color-dl-text-dim);
		margin-bottom: 2px;
	}
	.avg-value {
		font-size: 16px;
		font-weight: 700;
		font-family: var(--font-mono);
		color: var(--color-dl-text-muted);
	}
	.avg-value.positive { color: var(--color-dl-success); }
	.avg-value.negative { color: var(--color-dl-danger); }

	.box-row {
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.box-label {
		width: 60px;
		font-size: 10px;
		color: var(--color-dl-text-muted);
		text-align: right;
		flex-shrink: 0;
	}
	.box-svg {
		flex: 1;
		height: 24px;
	}
	.box-median {
		width: 48px;
		font-size: 10px;
		font-family: var(--font-mono);
		color: var(--color-dl-text-muted);
		text-align: right;
		flex-shrink: 0;
	}

	.shc-top {
		border-top: 1px solid var(--color-dl-border);
		padding-top: 8px;
	}
	.top-label {
		font-size: 10px;
		color: var(--color-dl-text-dim);
		display: block;
		margin-bottom: 4px;
	}
	.top-list {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}
	.top-item {
		font-size: 11px;
		color: var(--color-dl-text-muted);
		background: rgba(148, 163, 184, 0.08);
		padding: 2px 8px;
		border-radius: 4px;
	}

	.shc-foot {
		padding: 8px 16px;
		border-top: 1px solid var(--color-dl-border);
	}
	.shc-drill {
		width: 100%;
		background: linear-gradient(135deg, var(--color-dl-primary), var(--color-dl-accent));
		border: none;
		color: white;
		font-size: 13px;
		font-weight: 600;
		padding: 8px;
		border-radius: 6px;
		cursor: pointer;
		transition: opacity 0.15s;
	}
	.shc-drill:hover {
		opacity: 0.9;
	}
</style>
