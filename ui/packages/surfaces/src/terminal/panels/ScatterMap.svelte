<script lang="ts" module>
	// 산업분석 공유 산포도 · 위치=구조 인코딩(읽기 아님). 3곳 공유: 좌측 미니맵 · 다이얼로그 지형도 · 드릴 회사 산포도.
	// 위치는 데이터(중앙값/회사값) = 사실. verdict 아님(축 라벨 중립·사분면 음영 없음·중앙값 십자 기준선만).
	export interface ScatterPt {
		id: string;
		x: number; // 가로 데이터값
		y: number; // 세로 데이터값
		size: number; // 반지름 근거(산업=멤버수, 회사=gov 시총). >=0
		tone?: string; // gradeTone('up'|'good'|'neutral'|'warn'|'down') · 없으면 중립 블루
		label: string;
		faint?: boolean; // 소표본/저신뢰 → 흐림·라벨 생략
		meta?: string; // hover 정보바 보조 텍스트
	}
	export interface TrailPath {
		id: string;
		points: { x: number; y: number }[]; // 오래된→최신(끝점=현재). 끝점은 보통 pts 의 같은 id 점과 일치
		tone?: string;
	}
</script>

<script lang="ts">
	interface Props {
		pts: ScatterPt[];
		xLabel: string;
		yLabel: string;
		compact?: boolean; // 미니(패널) 모드 · 축라벨·정보바·상시라벨 생략
		compactH?: number; // 미니 모드 viewBox 높이(기본 134) · 좌측 패널 세로공간 절약 시 축소(점 위치 보존·잘림 없음)
		showLabels?: boolean; // 상시 라벨(충돌 제거) · 지형도/회사맵 on, 미니 off
		zeroX?: boolean; // x가 음수~양수 가로지르면 0 기준선
		yFloor0?: boolean; // y축 0 시작(격차 등); 아니면 min 패딩
		highlightId?: string; // 상시 강조(현재 산업/종목)
		hint?: string; // 정보바 기본 텍스트
		trails?: TrailPath[]; // 연도별 이동 꼬리(지형도 시간축). 끝점=현재 점·꼬리=과거. 축 범위에 꼬리점 포함.
		onPick?: (id: string) => void;
	}
	let { pts, xLabel, yLabel, compact = false, compactH = 134, showLabels = false, zeroX = false, yFloor0 = false, highlightId = '', hint = '', trails = [], onPick }: Props = $props();
	let hoverId = $state('');

	const TONE: Record<string, { f: string; s: string }> = {
		up: { f: 'rgba(63,185,80,0.42)', s: '#3fb950' },
		good: { f: 'rgba(111,191,115,0.4)', s: '#6fbf73' },
		neutral: { f: 'rgba(139,147,160,0.4)', s: '#8b93a0' },
		warn: { f: 'rgba(210,153,34,0.45)', s: '#d29922' },
		down: { f: 'rgba(248,81,73,0.42)', s: '#f85149' },
		base: { f: 'rgba(106,163,255,0.42)', s: '#6aa3ff' }
	};

	const geo = $derived.by(() => {
		const ps = pts.filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
		if (ps.length < 2) return null;
		const W = compact ? 220 : 700, H = compact ? compactH : 300;
		const ml = compact ? 4 : 52, mr = compact ? 8 : 70, mt = compact ? 4 : 14, mb = compact ? 6 : 28;
		const x0 = ml, x1 = W - mr, y0 = mt, y1 = H - mb;
		const xs = ps.map((p) => p.x), ys = ps.map((p) => p.y);
		// 축 범위는 현재점 + 꼬리점 합집합으로 잡는다(꼬리가 잘리지 않게). 중앙값 십자·크기는 현재점(ps)만.
		const tps = trails.flatMap((t) => t.points).filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y));
		const bx = tps.length ? xs.concat(tps.map((p) => p.x)) : xs, by = tps.length ? ys.concat(tps.map((p) => p.y)) : ys;
		// 로버스트 축 · 극단 아웃라이어가 축을 늘려 본질 클러스터를 뭉개는 것 방지(분포 2.5~97.5% 범위).
		// 범위 밖 점은 가장자리에 클램프(드롭 아님·hover=실제값). 산업맵(중앙값·소수)엔 영향 미미.
		const q = (arr: number[], pp: number) => { const s = [...arr].sort((a, b) => a - b); const idx = (s.length - 1) * pp; const lo = Math.floor(idx), hi = Math.ceil(idx); return s[lo] + (s[hi] - s[lo]) * (idx - lo); };
		const qlo = ps.length > 40 ? 0.1 : 0.025, qhi = 1 - qlo; // 점 많으면(회사맵 100+사) 10~90%로 타이트 · 정상기업 중앙압축 방지. 소수(산업맵 29)는 극단 보존.
		let xmin = q(bx, qlo), xmax = q(bx, qhi);
		let ymin = yFloor0 ? 0 : q(by, qlo), ymax = q(by, qhi);
		if (xmax <= xmin) { xmin = Math.min(...bx); xmax = Math.max(...bx); }
		if (ymax <= ymin) { ymin = yFloor0 ? 0 : Math.min(...by); ymax = Math.max(...by); }
		const pf = compact ? 0 : 0.09; // compact 미니맵 = 그래프영역 패딩 0(점이 박스 가장자리까지·위치 불변)
		const xpad = (xmax - xmin || 1) * pf; xmin -= xpad; xmax += xpad;
		const ypad = (ymax - ymin || 1) * pf; ymax += ypad; if (!yFloor0) ymin -= ypad;
		const clamp = (v: number, a: number, c: number) => Math.max(a, Math.min(c, v));
		const maxSz = Math.max(...ps.map((p) => p.size), 1);
		const rMax = compact ? 5.5 : 13.5, rMin = compact ? 2 : 3.5;
		const sx = (v: number) => x0 + ((clamp(v, xmin, xmax) - xmin) / (xmax - xmin)) * (x1 - x0);
		const sy = (v: number) => y1 - ((clamp(v, ymin, ymax) - ymin) / (ymax - ymin)) * (y1 - y0);
		const rOf = (s: number) => rMin + (Math.sqrt(Math.max(s, 0)) / Math.sqrt(maxSz)) * (rMax - rMin);
		const med = (a: number[]) => { const s = [...a].sort((p, q) => p - q); const k = Math.floor(s.length / 2); return s.length % 2 ? s[k] : (s[k - 1] + s[k]) / 2; };
		const dots = ps.map((p) => ({ p, cx: sx(p.x), cy: sy(p.y), r: rOf(p.size), tone: TONE[p.tone || 'base'] || TONE.base, lbl: false }));
		// 라벨 충돌 제거(greedy): 큰 점 우선, 겹치면 라벨만 숨김(점 유지·hover full). 위치 불변(정직).
		if (showLabels) {
			const placed: { x1: number; y1: number; x2: number; y2: number }[] = [];
			[...dots].sort((a, b) => b.r - a.r).forEach((d) => {
				if (d.p.faint) return;
				const nm = (d.p.label || '').slice(0, 5);
				const lx = d.cx + d.r + (compact ? 2 : 6), ly = d.cy - 7, lw = nm.length * 9.5 + 12, lh = 14;
				const box = { x1: lx, y1: ly, x2: lx + lw, y2: ly + lh };
				const hit = placed.some((q) => !(box.x2 < q.x1 || box.x1 > q.x2 || box.y2 < q.y1 || box.y1 > q.y2));
				if (!hit) { d.lbl = true; placed.push(box); }
			});
		}
		const trailPaths = trails.map((t) => ({
			id: t.id,
			tone: TONE[t.tone || 'base'] || TONE.base,
			pts: t.points.filter((p) => Number.isFinite(p.x) && Number.isFinite(p.y)).map((p) => ({ x: sx(p.x), y: sy(p.y) }))
		})).filter((t) => t.pts.length >= 2);
		return { W, H, x0, x1, y0, y1, cx: sx(med(xs)), cy: sy(med(ys)), zx: zeroX && xmin < 0 && xmax > 0 ? sx(0) : null, dots, trailPaths, xmin, xmax, ymin, ymax };
	});
	const hover = $derived(geo ? geo.dots.find((d) => d.p.id === hoverId) ?? null : null);
	const pick = (id: string) => onPick?.(id);
</script>

{#if geo}
	{@const g = geo}
	<div class={'smWrap' + (compact ? ' sm-mini' : '')}>
		<svg viewBox={`0 0 ${g.W} ${g.H}`} class="smSvg" role="img" aria-label={`${xLabel} / ${yLabel}`}>
			<line x1={g.x0} y1={g.y1} x2={g.x1} y2={g.y1} class="smAx" />
			<line x1={g.x0} y1={g.y0} x2={g.x0} y2={g.y1} class="smAx" />
			{#if g.zx != null}<line x1={g.zx} y1={g.y0} x2={g.zx} y2={g.y1} class="smZero" />{/if}
			<line x1={g.cx} y1={g.y0} x2={g.cx} y2={g.y1} class="smCross" />
			<line x1={g.x0} y1={g.cy} x2={g.x1} y2={g.cy} class="smCross" />
			{#each g.trailPaths as t (t.id)}
				<polyline points={t.pts.map((p) => `${p.x},${p.y}`).join(' ')} fill="none" stroke={t.tone.s} class="smTrail" />
				{#each t.pts.slice(0, -1) as p}<circle cx={p.x} cy={p.y} r={compact ? 1.1 : 1.9} fill={t.tone.s} class="smTrailDot" />{/each}
			{/each}
			{#each g.dots as d (d.p.id)}
				<g class={'smDot' + (hoverId === d.p.id ? ' on' : '') + (highlightId === d.p.id ? ' hi' : '')} role="button" tabindex="0" aria-label={d.p.label}
					onclick={() => pick(d.p.id)}
					onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); pick(d.p.id); } }}
					onmouseenter={() => (hoverId = d.p.id)} onmouseleave={() => (hoverId = '')}
					onfocus={() => (hoverId = d.p.id)} onblur={() => (hoverId = '')}>
					<circle cx={d.cx} cy={d.cy} r={Math.max(d.r + 1.5, compact ? 5 : 7)} fill="transparent" />
					<circle cx={d.cx} cy={d.cy} r={d.r} class="smC" class:faint={d.p.faint} style={`fill:${d.tone.f};stroke:${d.tone.s}`} />
					{#if highlightId === d.p.id}<circle cx={d.cx} cy={d.cy} r={d.r + 3} class="smHiRing" />{/if}
					{#if d.lbl || highlightId === d.p.id}<text x={d.cx + d.r + (compact ? 2 : 6)} y={d.cy + 3} class="smLbl">{d.p.label.slice(0, compact ? 4 : 5)}</text>{/if}
				</g>
			{/each}
			{#if hover}
				<circle cx={hover.cx} cy={hover.cy} r={hover.r} class="smCtop" pointer-events="none" style={`stroke:${hover.tone.s}`} />
				<text x={hover.cx + hover.r + (compact ? 3 : 6)} y={hover.cy + 3} class="smLbl smLtop" pointer-events="none">{hover.p.label}</text>
			{/if}
			{#if !compact}
				<text x={(g.x0 + g.x1) / 2} y={g.H - 2} class="smAxLbl" text-anchor="middle">{xLabel} →</text>
				<!-- y축 라벨은 rotate(-90)로 세움 → 화살표 "→"가 회전 후 "↑"(위=값 큼)로 보임. "↑"를 쓰면 회전돼 "←"가 됨. -->
				<text x={13} y={(g.y0 + g.y1) / 2} class="smAxLbl" text-anchor="middle" transform={`rotate(-90 13 ${(g.y0 + g.y1) / 2})`}>{yLabel} →</text>
				<text x={g.x0} y={g.y1 + 11} class="smTick" text-anchor="start">{Math.round(g.xmin)}</text>
				<text x={g.x1} y={g.y1 + 11} class="smTick" text-anchor="end">{Math.round(g.xmax)}</text>
				<text x={g.x0 - 5} y={g.y1} class="smTick" text-anchor="end">{Math.round(g.ymin)}</text>
				<text x={g.x0 - 5} y={g.y0 + 8} class="smTick" text-anchor="end">{Math.round(g.ymax)}</text>
			{/if}
		</svg>
		{#if !compact}
			<div class="smInfo">
				{#if hover}
					<b>{hover.p.label}</b>{#if hover.p.meta} · {hover.p.meta}{/if} · <em>{onPick ? '클릭 → 상세' : ''}</em>
				{:else}
					{hint}
				{/if}
			</div>
		{/if}
	</div>
{:else}
	<div class="smEmpty">{compact ? '데이터 없음' : '표본 부족 · 점 2개 미만'}</div>
{/if}

<style>
	.smWrap { width: 100%; }
	.smSvg { width: 100%; height: auto; display: block; }
	/* max-height 캡 제거 · 캡이 있으면 레일이 viewBox(220px)보다 넓을 때 letterbox(좌우 여백)가 생긴다.
	   width:100%·height:auto 로 레일 폭을 꽉 채우고(원형 유지), 박스 높이는 SVG 비율을 따른다. */
	.sm-mini .smSvg { max-height: none; }
	.smAx { stroke: var(--dl-line, #2a3142); stroke-width: 1; }
	.smZero { stroke: color-mix(in srgb, var(--dl-ink, #c8cfdb) 20%, transparent); stroke-width: 1; stroke-dasharray: 1 3; }
	.smCross { stroke: color-mix(in srgb, var(--amber, var(--amber)) 24%, transparent); stroke-width: 1; stroke-dasharray: 3 3; }
	.smDot { cursor: pointer; outline: none; }
	.smC { stroke-width: 1; transition: fill 0.12s; }
	.smC.faint { opacity: 0.4; }
	.smDot.on .smC { fill-opacity: 0.95 !important; }
	.smHiRing { fill: none; stroke: var(--amber, var(--amber)); stroke-width: 1.3; }
	.smDot:focus-visible .smC { stroke: var(--amber, var(--amber)); stroke-width: 2; }
	.smCtop { fill: none; stroke-width: 2; }
	.smLbl { fill: #c2cad6; font-size: 11px; pointer-events: none; }
	.sm-mini .smLbl { font-size: 10px; }
	.smDot.on .smLbl, .smDot.hi .smLbl, .smLtop { fill: #f0f3f7; font-weight: 700; }
	.smAxLbl { fill: #d2d8e2; font-size: 10px; }
	.smTick { fill: #aab2bf; font-size: 9px; }
	.smInfo { font-size: 10.5px; color: #c2cad6; line-height: 1.45; margin-top: 14px; padding: 0 2px; min-height: 26px; }
	.smInfo b { color: #f0f3f7; }
	.smInfo em { font-style: normal; color: var(--amber, var(--amber)); }
	.smEmpty { font-size: 10px; color: #aab2bf; padding: 12px; text-align: center; }
	.smTrail { stroke-width: 1.3; stroke-opacity: 0.42; stroke-linejoin: round; stroke-linecap: round; }
	.smTrailDot { opacity: 0.5; }
</style>
