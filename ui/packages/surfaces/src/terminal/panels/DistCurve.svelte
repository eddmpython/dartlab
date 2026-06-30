<script lang="ts">
	// 동종사 분포 미니 차트 + 회사 위치 마커.
	//  · hist(실도수 히스토그램) 가 있으면 그것을 그린다 · 막대 높이 = 그 구간 동종사 수(어디에 몰렸나, 봉우리·gap·왜도 그대로).
	//  · 없으면 band(p10~p90 5분위 보간) 폴백 · 정규가정 아님, 국소밀도로 왜도 반영.
	// 회사값은 범위 밖이어도 항상 보이게 마커로 표시(이상치 = 봉우리에서 떨어진 위치).
	import type { Lang, Hist } from '../lib/types';

	let {
		band = null,
		hist = null,
		value,
		p,
		unit = '',
		lang = 'kr',
		w = 150,
		h = 30,
		neutral = false
	}: {
		band?: { p10: number; p25: number; median: number; p75: number; p90: number } | null;
		hist?: Hist | null;
		value: number | null;
		p: number; // 0~100 백분위 (lowerBetter 이미 반영 · 높을수록 우수)
		unit?: string;
		lang?: Lang;
		w?: number;
		h?: number;
		neutral?: boolean; // true = 회사 마커 회색(우열 프레이밍 금지 · 가격 등 lowerBetter 모호 지표용)
	} = $props();

	const W = $derived(w);
	const H = $derived(h);
	const PAD = 3;
	const base = $derived(H - PAD);
	const innerH = $derived(H - 2 * PAD - 1);
	const fx = (frac: number): number => PAD + frac * (W - 2 * PAD);

	// 히스토그램 막대 좌표 (hist 모드).
	const bars = $derived.by(() => {
		if (!hist || !hist.bins.length) return [];
		const N = hist.bins.length;
		const bw = (W - 2 * PAD) / N;
		return hist.bins.map((bh, i) => ({ x: PAD + i * bw + bw * 0.08, w: Math.max(0.4, bw * 0.84), h: Math.max(bh > 0 ? 0.8 : 0, bh * innerH) }));
	});

	// band(5분위 보간) 폴백 좌표.
	const lo = $derived(band ? Math.min(band.p10, value ?? band.p10) : 0);
	const hi = $derived(band ? Math.max(band.p90, value ?? band.p90) : 1);
	const span = $derived(hi - lo || 1);
	const sx = (v: number): number => PAD + ((v - lo) / span) * (W - 2 * PAD);
	const areaPath = $derived.by(() => {
		if (!band) return '';
		const xs = [band.p10, band.p25, band.median, band.p75, band.p90];
		const cum = [0.1, 0.25, 0.5, 0.75, 0.9];
		const dens = xs.map((_, i) => {
			const a = Math.max(0, i - 1);
			const b = Math.min(xs.length - 1, i + 1);
			const dw = xs[b] - xs[a] || 1;
			return (cum[b] - cum[a]) / dw;
		});
		const maxD = Math.max(...dens) || 1;
		const pts = xs.map((x, i) => ({ x: sx(x), h: (dens[i] / maxD) * innerH }));
		let d = `M ${pts[0].x.toFixed(1)} ${base}`;
		for (const pt of pts) d += ` L ${pt.x.toFixed(1)} ${(base - pt.h).toFixed(1)}`;
		d += ` L ${pts[pts.length - 1].x.toFixed(1)} ${base} Z`;
		return d;
	});

	const medX = $derived(hist ? fx(hist.medianFrac) : band ? sx(band.median) : null);
	const markX = $derived(
		hist ? (hist.companyFrac != null ? fx(hist.companyFrac) : null) : band ? (value != null ? sx(value) : null) : null
	);
	const tone = $derived(neutral ? 'neu' : p >= 66 ? 'up' : p <= 33 ? 'dn' : 'mid');
	const tip = $derived(
		hist
			? `${lang === 'en' ? 'peers' : '동종사'} n=${hist.n} · ${lang === 'en' ? 'range' : '범위'} ${hist.lo.toFixed(1)}~${hist.hi.toFixed(1)}${unit === '%' ? '%' : ''}`
			: band
				? `${lang === 'en' ? 'peers' : '업종'} p10 ${band.p10.toFixed(1)} · ${lang === 'en' ? 'med' : '중앙'} ${band.median.toFixed(1)} · p90 ${band.p90.toFixed(1)}`
				: ''
	);
</script>

<svg class="dc" width="100%" height={H} viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" role="img" aria-label={tip} style={`height:${H}px`}>
	<title>{tip}</title>
	<!-- 바닥축 · 분포와 회사 마커가 *같은 축* 위임을 명시(이상치라 마커가 봉우리에서 떨어져도 동일 분포 위 위치로 읽힘). -->
	<line class="dcBase" x1="0" x2={W} y1={base} y2={base} vector-effect="non-scaling-stroke" />
	{#if hist}
		{#each bars as b, i (i)}
			<rect class="dcBar" x={b.x.toFixed(1)} y={(base - b.h).toFixed(1)} width={b.w.toFixed(1)} height={b.h.toFixed(1)} />
		{/each}
	{:else if band}
		<path class="dcArea" d={areaPath} vector-effect="non-scaling-stroke" />
	{/if}
	{#if medX != null}
		<line class="dcMed" x1={medX} x2={medX} y1={PAD} y2={H - PAD} vector-effect="non-scaling-stroke" />
	{/if}
	{#if markX != null}
		<line class={'dcMark ' + tone} x1={markX} x2={markX} y1="5" y2={H} vector-effect="non-scaling-stroke" />
		<!-- 꼭지(핀) · "여기가 이 회사" 가 박히도록 마커 상단에 삼각 헤드. -->
		<path class={'dcPin ' + tone} d={`M ${(markX - 3.2).toFixed(1)} 0 L ${(markX + 3.2).toFixed(1)} 0 L ${markX.toFixed(1)} 5.5 Z`} />
	{/if}
</svg>

<style>
	.dc {
		display: block;
		width: 100%;
		overflow: visible;
	}
	.dcArea {
		fill: rgba(139, 148, 158, 0.18);
		stroke: rgba(139, 148, 158, 0.5);
		stroke-width: 1;
	}
	.dcBar {
		fill: rgba(139, 148, 158, 0.45);
	}
	.dcBase {
		stroke: rgba(139, 148, 158, 0.3);
		stroke-width: 1;
	}
	.dcMed {
		stroke: rgba(139, 148, 158, 0.5);
		stroke-width: 1;
		stroke-dasharray: 2 2;
	}
	.dcMark {
		stroke-width: 2;
	}
	.dcMark.up {
		stroke: #3fb950;
	}
	.dcMark.dn {
		stroke: #f85149;
	}
	.dcMark.mid {
		stroke: #d29922;
	}
	.dcMark.neu {
		stroke: rgba(160, 168, 179, 0.9);
	}
	.dcPin.up {
		fill: #3fb950;
	}
	.dcPin.dn {
		fill: #f85149;
	}
	.dcPin.mid {
		fill: #d29922;
	}
	.dcPin.neu {
		fill: rgba(160, 168, 179, 0.95);
	}
</style>
