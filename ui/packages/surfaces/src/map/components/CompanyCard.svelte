<script lang="ts">
	import Sparkline from './Sparkline.svelte';
	import RadarChart from './RadarChart.svelte';
	import FreshnessBadge from './FreshnessBadge.svelte';
	import CompanyCardDeep from './CompanyCardDeep.svelte';

	interface Props {
		// ecosystem.json 노드 (기본 정보 + scan 지표 4종)
		node: any;
		// companies/{code}.json (있으면 풍부한 데이터, 없으면 null)
		detail: any | null;
		loading?: boolean;
		// industryStats.json[node.industry] · 업종 분포 통계
		industryStat?: any | null;
		// meta.json.dataAsOf · 신선도 표시
		dataAsOf?: Record<string, string | null | undefined> | null;
		// 비교에 추가 콜백
		onAddCompare?: (stockCode: string) => void;
		// 닫기
		onClose?: () => void;
		// "띄우기" · 플로팅 윈도우로 detach
		onDetach?: (stockCode: string) => void;
		compareDisabled?: boolean;
		// 플로팅 모드에선 "띄우기" 버튼 숨김
		detached?: boolean;
		// 충격 시뮬레이션
		onShock?: (stockCode: string) => void;
		// movers 이상 신호 (이 회사에 해당하면)
		moverSignal?: string | null;
		// 셸 base 경로(블로그 링크 등 에셋) · $app/paths 무결합(포터블 surface). 셸이 주입.
		basePath?: string;
	}

	let {
		node,
		detail,
		loading = false,
		industryStat = null,
		dataAsOf = null,
		onAddCompare,
		onClose,
		onDetach,
		compareDisabled = false,
		detached = false,
		onShock,
		moverSignal = null,
		basePath = ''
	}: Props = $props();

	let aiExpanded = $state(false);
	let activeTab: 'summary' | 'deep' = $state('summary');

	function fmtKor(v: number | null | undefined, suffix = '원'): string {
		if (v === null || v === undefined || isNaN(v)) return '-';
		const abs = Math.abs(v);
		if (abs >= 1e12) return `${(v / 1e12).toFixed(1)}조${suffix}`;
		if (abs >= 1e8) return `${Math.round(v / 1e8).toLocaleString()}억${suffix}`;
		return `${v.toLocaleString()}${suffix}`;
	}

	function pct(v: number | null | undefined, digits = 1): string {
		if (v === null || v === undefined || isNaN(v)) return '-';
		return `${v.toFixed(digits)}%`;
	}

	// 5년 시계열 (있으면)
	let financials = $derived(detail?.financials5y || []);
	let years = $derived(financials.map((f: any) => String(f.year ?? '').slice(-2)));
	let salesSeries = $derived(financials.map((f: any) => f.sales ?? null));
	let opSeries = $derived(financials.map((f: any) => f.operating_profit ?? null));
	let netSeries = $derived(financials.map((f: any) => f.net_profit ?? null));
	let latest = $derived(financials.length ? financials[financials.length - 1] : null);

	// peer 분위 (industryRank 가 있으면 → percentile)
	let peerPct = $derived.by(() => {
		if (!node?.industryRank || !node?.industryPeerCount) return null;
		const rank = node.industryRank;
		const peer = node.industryPeerCount;
		// rank 1 = top → percentile 100, rank N = bottom → 0
		return Math.round(((peer - rank) / (peer - 1 || 1)) * 100);
	});

	// 5축 레이더 데이터 (수익성/성장/안정성/품질/지배구조)
	let radarAxes = $derived.by(() => {
		// 수익성: ROE → 0~100 (ROE -10=0, 20=100)
		const profitScore = node.roe != null ? Math.min(100, Math.max(0, ((node.roe + 10) / 30) * 100)) : 50;
		// 성장: CAGR → 0~100 (-10=0, 30=100)
		const growthScore = node.revCagr != null ? Math.min(100, Math.max(0, ((node.revCagr + 10) / 40) * 100)) : 50;
		// 안정성: 부채비율 역변환 (50=100, 400=0)
		const stabilityScore = node.debtRatio != null ? Math.min(100, Math.max(0, ((400 - node.debtRatio) / 350) * 100)) : 50;
		// 품질: 등급 → 점수
		const qMap: Record<string, number> = { '우수': 90, '양호': 70, '보통': 50, '주의': 30, '위험': 10 };
		const qualityScore = qMap[node.qualGrade] ?? 50;
		// 지배구조: 등급 → 점수
		const gMap: Record<string, number> = { 'A': 90, 'B': 70, 'C': 50, 'D': 30, 'E': 10 };
		const govScore = gMap[node.govGrade] ?? 50;

		return [
			{ label: '수익성', value: profitScore, benchmark: 50 },
			{ label: '성장', value: growthScore, benchmark: 50 },
			{ label: '안정성', value: stabilityScore, benchmark: 50 },
			{ label: '품질', value: qualityScore, benchmark: 50 },
			{ label: '지배구조', value: govScore, benchmark: 50 }
		];
	});

	// 레이더에 표시할 데이터가 있는지 확인
	let hasRadarData = $derived(
		node.roe != null || node.revCagr != null || node.debtRatio != null
	);

	let supplyInsights = $derived(detail?.supplyInsights || {});
	let aiInsight = $derived(detail?.aiInsight || null);
	let blogPosts = $derived(detail?.blogPosts || []);

	// 정밀 거래 Top 5 (amount 큰 순)
	let topPreciseEdges = $derived.by(() => {
		const all: any[] = [];
		for (const s of detail?.suppliers || []) {
			if (s.amount && s.amount > 0) all.push({ ...s, kind: '공급' });
		}
		for (const c of detail?.customers || []) {
			if (c.amount && c.amount > 0) all.push({ ...c, kind: '고객' });
		}
		all.sort((a, b) => (b.amount || 0) - (a.amount || 0));
		return all.slice(0, 5);
	});

	function colorByMetric(value: number | null, kind: 'roe' | 'op' | 'debt' | 'cagr'): string {
		if (value === null || value === undefined) return '#64748b';
		if (kind === 'debt') {
			if (value >= 200) return '#ef4444';
			if (value >= 100) return '#f59e0b';
			return '#10b981';
		}
		// roe/op/cagr: positive = good
		const thresholds = { roe: [0, 10, 20], op: [0, 10, 20], cagr: [0, 10, 20] }[kind];
		if (value >= thresholds[2]) return '#10b981';
		if (value >= thresholds[1]) return '#84cc16';
		if (value >= thresholds[0]) return '#f59e0b';
		return '#ef4444';
	}

	// ── 업종 정규화 ──
	// industryStat.distribution[metric] = {n, p10, p25, median, p75, p90, mean, std}
	// 반환: 백분위(0~100), z-score, 색상 · 표본 작으면 null
	function normalize(
		value: number | null | undefined,
		metric: 'roe' | 'opMargin' | 'debtRatio' | 'revCagr'
	): { percentile: number; zScore: number; color: string; n: number } | null {
		if (value === null || value === undefined || isNaN(value)) return null;
		const dist = industryStat?.distribution?.[metric];
		if (!dist || dist.n < 3) return null;

		// 선형 보간 백분위 계산
		const quantiles = [
			{ q: 10, v: dist.p10 },
			{ q: 25, v: dist.p25 },
			{ q: 50, v: dist.median },
			{ q: 75, v: dist.p75 },
			{ q: 90, v: dist.p90 }
		];
		let percentile: number;
		if (value <= quantiles[0].v) percentile = 10 * (value / (quantiles[0].v || 1));
		else if (value >= quantiles[4].v) percentile = 90 + 10 * Math.min(1, (value - quantiles[4].v) / Math.abs(quantiles[4].v - quantiles[2].v || 1));
		else {
			percentile = 90;
			for (let i = 0; i < quantiles.length - 1; i++) {
				if (value >= quantiles[i].v && value <= quantiles[i + 1].v) {
					const span = quantiles[i + 1].v - quantiles[i].v || 1;
					percentile = quantiles[i].q + (value - quantiles[i].v) / span * (quantiles[i + 1].q - quantiles[i].q);
					break;
				}
			}
		}
		percentile = Math.max(0, Math.min(100, percentile));

		const zScore = dist.std > 0 ? (value - dist.mean) / dist.std : 0;

		// 역방향(debtRatio) 고려 · 낮을수록 좋음
		const invert = metric === 'debtRatio';
		const goodness = invert ? 100 - percentile : percentile;
		let color: string;
		if (goodness >= 80) color = '#10b981';
		else if (goodness >= 50) color = '#84cc16';
		else if (goodness >= 20) color = '#f59e0b';
		else color = '#ef4444';

		return { percentile, zScore, color, n: dist.n };
	}

	function hhiBucket(hhi: number | null | undefined): { label: string; color: string; pct: number } {
		if (hhi === null || hhi === undefined) return { label: '-', color: '#64748b', pct: 0 };
		// HHI 0~10000. 1500 미만 분산, 2500+ 집중
		if (hhi >= 2500) return { label: '집중', color: '#ef4444', pct: Math.min(100, hhi / 100) };
		if (hhi >= 1500) return { label: '주의', color: '#f59e0b', pct: hhi / 100 };
		return { label: '분산', color: '#10b981', pct: hhi / 100 };
	}

	let hhiInfo = $derived(hhiBucket(supplyInsights?.hhi));
</script>

<div class="card">
	{#if !detached}
		<button class="close" onclick={() => onClose?.()} aria-label="닫기">✕</button>

		<!-- 1. Header -->
		<div class="head">
			<div class="head-title-row">
				<h2>{node.label}</h2>
				{#if dataAsOf}
					<FreshnessBadge {dataAsOf} variant="dot" />
				{/if}
			</div>
			<p class="code">{node.id}</p>
			<div class="badges">
				<span class="badge industry" style:background="{node.color}20" style:color={node.color}>
					{node.industryName}
				</span>
				{#if node.stageName || node.stage}
					<span class="badge stage">{node.stageName || node.stage}</span>
				{/if}
				{#if node.role}<span class="badge role">{node.role}</span>{/if}
				{#if node.stream}<span class="badge stream">{node.stream}</span>{/if}
			</div>
		</div>
	{:else}
		<!-- FloatingCard 안: 배지만 간결하게 -->
		<div class="badges" style="padding-top: 4px;">
			<span class="badge industry" style:background="{node.color}20" style:color={node.color}>
				{node.industryName}
			</span>
			{#if node.stageName || node.stage}
				<span class="badge stage">{node.stageName || node.stage}</span>
			{/if}
			{#if node.role}<span class="badge role">{node.role}</span>{/if}
			{#if node.stream}<span class="badge stream">{node.stream}</span>{/if}
		</div>
	{/if}

	{#if loading}
		<div class="loading">상세 데이터 로드 중…</div>
	{/if}

	<!-- T1: 3초 요약 (headline) -->
	<div class="t1-summary">
		<!-- 방향성 배지 -->
		{#if blogPosts[0]?.direction}
			{@const dir = blogPosts[0].direction}
			<span class="direction-badge {dir === '상승' || dir === 'bullish' ? 'up' : dir === '악화' || dir === 'bearish' ? 'down' : 'hold'}">
				{dir}
			</span>
		{/if}
		{#if aiInsight?.verdict || blogPosts[0]?.verdict}
			<div class="t1-verdict">
				{aiInsight?.verdict || blogPosts[0]?.verdict}
			</div>
		{:else if aiInsight?.strengths?.[0]}
			<div class="t1-verdict">
				{aiInsight.strengths[0]}
			</div>
		{:else}
			{@const normRoe = normalize(node.roe, 'roe')}
			<div class="t1-verdict auto">
				{#if node.roe !== null && node.roe !== undefined}ROE {pct(node.roe)}{#if normRoe} (상위 {(100 - normRoe.percentile).toFixed(0)}%){/if}{/if}{#if node.revenueYoyPct !== null && node.revenueYoyPct !== undefined} · 매출 YoY {node.revenueYoyPct > 0 ? '+' : ''}{node.revenueYoyPct.toFixed(1)}%{/if}{#if node.debtGrade} · {node.debtGrade}{/if}
			</div>
		{/if}
		<div class="t1-grid">
			{#if node.revenue}
				<div class="t1-cell">
					<div class="t1-k">매출</div>
					<div class="t1-v">{fmtKor(node.revenue)}</div>
					{#if node.revenueYoyPct !== null && node.revenueYoyPct !== undefined}
						<div class="t1-d" style:color={node.revenueYoyPct > 0 ? '#34d399' : '#f87171'}>
							YoY {node.revenueYoyPct > 0 ? '+' : ''}{node.revenueYoyPct.toFixed(1)}%
						</div>
					{/if}
				</div>
			{/if}
			{#if node.roe !== null && node.roe !== undefined}
				<div class="t1-cell">
					<div class="t1-k">ROE</div>
					<div class="t1-v" style:color={colorByMetric(node.roe, 'roe')}>{pct(node.roe)}</div>
					{#if node.roeDelta !== null && node.roeDelta !== undefined}
						<div class="t1-d" style:color={node.roeDelta > 0 ? '#34d399' : '#f87171'}>
							YoY {node.roeDelta > 0 ? '+' : ''}{node.roeDelta}%p
						</div>
					{/if}
				</div>
			{/if}
			{#if node.industryRank}
				<div class="t1-cell">
					<div class="t1-k">산업 내</div>
					<div class="t1-v">{node.industryRank}위</div>
					<div class="t1-d">/ {node.industryPeerCount}사</div>
				</div>
			{/if}
		</div>

		<!-- 신용등급 + movers 경고 (승격) -->
		<div class="priority-badges">
			{#if detail?.creditMetrics?.grade || detail?.creditMetrics?.creditGrade}
				{@const cg = detail.creditMetrics.grade || detail.creditMetrics.creditGrade}
				<span class="priority-badge credit" title="dartlab 신용등급 (dCR)">
					dCR {cg}
				</span>
			{/if}
			{#if moverSignal}
				{@const sigLabel = ({ profitImprove: '수익성 개선', profitDecline: '수익성 악화', revenueSpike: '매출 급증', revenueDrop: '매출 급락', debtStress: '부채 스트레스', extremeWarning: '극단 경고' })[moverSignal] || moverSignal}
				{@const sigType = moverSignal.includes('Improve') || moverSignal === 'revenueSpike' ? 'good' : moverSignal === 'extremeWarning' ? 'warn' : 'bad'}
				<span class="priority-badge mover {sigType}" title="이번 회계연도 급변 감지">
					⚡ {sigLabel}
				</span>
			{/if}
		</div>

		<!-- scan 배지행 -->
		<div class="scan-badges">
			{#if node.govGrade}<span class="scan-badge" title="지배구조 등급">G:{node.govGrade}</span>{/if}
			{#if node.cfPattern}<span class="scan-badge" title="현금흐름 패턴">CF:{node.cfPattern}</span>{/if}
			{#if node.auditRisk}<span class="scan-badge" title="감사 리스크">{node.auditRisk}</span>{/if}
			{#if node.qualGrade}<span class="scan-badge" title="이익 질">Q:{node.qualGrade}</span>{/if}
			{#if node.liqGrade}<span class="scan-badge" title="유동성">L:{node.liqGrade}</span>{/if}
			{#if node.capClass}<span class="scan-badge" title="주주환원 분류">{node.capClass}</span>{/if}
			{#if node.empCount}<span class="scan-badge" title="직원수">{node.empCount.toLocaleString()}명</span>{/if}
		</div>
	</div>

	<!-- 탭 바 -->
	<div class="tab-bar">
		<button class="tab-btn" class:active={activeTab === 'summary'} onclick={() => (activeTab = 'summary')}>요약</button>
		<button class="tab-btn" class:active={activeTab === 'deep'} onclick={() => (activeTab = 'deep')}>심층</button>
	</div>

	{#if activeTab === 'summary'}
	<!-- 블로그 포스트 (있으면 맨 위에 강조) -->
	{#if blogPosts.length > 0}
		<div class="blog-banner">
			<div class="banner-title">📝 이 회사 심층 분석 글</div>
			{#each blogPosts.slice(0, 2) as post}
				<a class="blog-card featured" href="{basePath}/blog/{post.slug}" target="_blank" rel="noopener">
					<div class="blog-title">{post.title}</div>
					{#if post.verdict}
						<div class="blog-verdict">{post.verdict}</div>
					{/if}
					<div class="blog-meta">
						{#if post.direction}<span class="blog-tag">{post.direction}</span>{/if}
						{#if post.archetype}<span class="blog-tag">{post.archetype}</span>{/if}
						<span class="blog-cta">읽으러 가기 →</span>
					</div>
				</a>
			{/each}
		</div>
	{/if}

	<!-- 2. 재무 한눈에 -->
	{#if latest}
		<div class="section">
			<h3>재무 한눈에 <span class="year">{latest.year}년</span></h3>
			<div class="fin-grid">
				<div class="fin-cell">
					<div class="fin-k">매출</div>
					<div class="fin-v">{fmtKor(latest.sales)}</div>
				</div>
				<div class="fin-cell">
					<div class="fin-k">영업이익</div>
					<div class="fin-v" style:color={latest.operating_profit < 0 ? '#ef4444' : '#10b981'}>
						{fmtKor(latest.operating_profit)}
					</div>
				</div>
				<div class="fin-cell">
					<div class="fin-k">순이익</div>
					<div class="fin-v" style:color={latest.net_profit < 0 ? '#ef4444' : '#10b981'}>
						{fmtKor(latest.net_profit)}
					</div>
				</div>
				<div class="fin-cell">
					<div class="fin-k">총자산</div>
					<div class="fin-v">{fmtKor(latest.total_assets)}</div>
				</div>
			</div>
		</div>

		<!-- 3. 5년 sparkline -->
		<div class="section">
			<h3>5년 추이</h3>
			<Sparkline
				labels={years}
				series={[
					{ label: '매출', color: '#60a5fa', values: salesSeries },
					{ label: '영업이익', color: '#34d399', values: opSeries },
					{ label: '순이익', color: '#fbbf24', values: netSeries }
				]}
				periodLabel={`${financials[0]?.year ?? ''}~${financials[financials.length - 1]?.year ?? ''} 연도말 기준 · 출처 DART`}
			/>
		</div>
	{:else if !loading}
		<!-- enriched JSON 없는 회사 (top500 외) · 노드 정보만 표시 -->
		{#if node.revenue}
			<div class="section">
				<h3>매출</h3>
				<div class="fin-cell">
					<div class="fin-v">{fmtKor(node.revenue)}</div>
				</div>
			</div>
		{/if}
	{/if}

	<!-- 3.5 레이더 차트 (5축 한눈에) -->
	{#if hasRadarData}
		<div class="section radar-section">
			<h3>체력 진단</h3>
			<div class="radar-wrap">
				<RadarChart axes={radarAxes} size={140} />
				<span class="radar-hint">업종 평균(회색) vs 이 회사(빨강)</span>
			</div>
		</div>
	{/if}

	<!-- 4. scan 스코어 + peer 분위 -->
	{#if node.roe !== null || node.opMargin !== null || node.debtRatio !== null || node.revCagr !== null}
		<div class="section">
			<h3>
				재무 스코어
				{#if peerPct !== null}
					<span class="peer">산업 분위 {peerPct}%</span>
				{/if}
			</h3>
			<div class="scan-grid">
				{#each [
					{ key: 'roe', metric: 'roe', label: 'ROE', val: node.roe, grade: node.profGrade, delta: node.roeDelta, deltaUnit: '%p', invertDelta: false, fmt: (v: number) => pct(v) },
					{ key: 'op', metric: 'opMargin', label: '영업이익률', val: node.opMargin, grade: '', delta: node.opMarginDelta, deltaUnit: '%p', invertDelta: false, fmt: (v: number) => pct(v) },
					{ key: 'debt', metric: 'debtRatio', label: '부채비율', val: node.debtRatio, grade: node.debtGrade, delta: node.debtRatioDelta, deltaUnit: '%p', invertDelta: true, fmt: (v: number) => pct(v, 0) },
					{ key: 'cagr', metric: 'revCagr', label: '매출 CAGR', val: node.revCagr, grade: node.growthGrade, delta: null, deltaUnit: '', invertDelta: false, fmt: (v: number) => pct(v) }
				] as row (row.key)}
					{#if row.val !== null && row.val !== undefined}
						{@const norm = normalize(row.val, row.metric as any)}
						{@const dExtreme = row.delta !== null && row.delta !== undefined && Math.abs(row.delta) > 50}
						{@const dGood = row.delta !== null && row.delta !== undefined && (row.invertDelta ? row.delta < 0 : row.delta > 0)}
						<div class="scan-row">
							<div class="scan-line1">
								<span class="scan-k">{row.label}</span>
								<span
									class="scan-v"
									style:color={norm?.color || colorByMetric(row.val, row.key as any)}
								>
									{row.fmt(row.val)}
								</span>
								{#if row.delta !== null && row.delta !== undefined}
									<span
										class="scan-delta {dExtreme ? 'extreme' : dGood ? 'good' : 'bad'}"
										title={dExtreme
											? `전년 대비 ${row.delta > 0 ? '+' : ''}${row.delta}${row.deltaUnit} · 극단적 변화, 1회성/재분류 가능성 확인`
											: `전년 대비 ${row.delta > 0 ? '+' : ''}${row.delta}${row.deltaUnit}`}
									>
										{dExtreme ? '⚠ ' : dGood ? '▲ ' : '▼ '}{row.delta > 0 ? '+' : ''}{row.delta}{row.deltaUnit}
									</span>
								{/if}
								{#if row.grade}<span class="scan-grade">{row.grade}</span>{/if}
								{#if norm}
									<span class="scan-pct" title={`업종 n=${norm.n} · z=${norm.zScore.toFixed(2)}σ`}>
										상위 {(100 - norm.percentile).toFixed(0)}%
									</span>
								{/if}
							</div>
							{#if norm}
								<div class="scan-gauge" title={`업종 percentile ${norm.percentile.toFixed(0)}`}>
									<div
										class="scan-gauge-fill"
										style:width="{row.metric === 'debtRatio' ? 100 - norm.percentile : norm.percentile}%"
										style:background={norm.color}
									></div>
								</div>
							{/if}
						</div>
					{/if}
				{/each}
				{#if node.revenueYoyPct !== null && node.revenueYoyPct !== undefined}
					<div class="scan-row">
						<div class="scan-line1">
							<span class="scan-k">매출 YoY</span>
							<span
								class="scan-v"
								style:color={node.revenueYoyPct > 0 ? '#10b981' : '#ef4444'}
							>
								{node.revenueYoyPct > 0 ? '+' : ''}{node.revenueYoyPct.toFixed(1)}%
							</span>
							<span class="scan-grade">
								{#if node.deltaYear}{node.deltaYear - 1}→{node.deltaYear}{/if}
							</span>
						</div>
					</div>
				{/if}
			</div>
			{#if node.industryRank}
				<div class="rank-line">
					{node.industryName} 매출 순위 <strong>{node.industryRank}위</strong>
					/ {node.industryPeerCount}사
					{#if node.marketShare}· 상장사매출비중 {node.marketShare.toFixed(1)}%{/if}
				</div>
			{/if}
		</div>
	{/if}

	<!-- 5. 공급망 분석 -->
	{#if detail && supplyInsights && (supplyInsights.hhi !== undefined || supplyInsights.supplierCount)}
		<div class="section">
			<h3>공급망 구조</h3>

			<div class="hhi-card">
				<div class="hhi-head">
					<span class="hhi-label">공급 집중도</span>
					<span class="hhi-bucket" style:color={hhiInfo.color}>
						{hhiInfo.label}
						{#if supplyInsights.hhi !== null && supplyInsights.hhi !== undefined}
							· HHI {Math.round(supplyInsights.hhi)}
						{/if}
					</span>
				</div>
				<div class="gauge">
					<div class="gauge-fill" style:width="{Math.min(100, hhiInfo.pct)}%" style:background={hhiInfo.color}></div>
				</div>
				<div class="hhi-note">
					Top1 의존 <strong>{pct(supplyInsights.top1Ratio)}</strong> · Top3 <strong>{pct(supplyInsights.top3Ratio)}</strong>
				</div>
			</div>

			<div class="sup-grid">
				<div class="sup-cell">
					<div class="sup-k">공급사</div>
					<div class="sup-v">{supplyInsights.supplierCount ?? '-'}사</div>
				</div>
				<div class="sup-cell">
					<div class="sup-k">고객사</div>
					<div class="sup-v">{supplyInsights.customerCount ?? '-'}사</div>
				</div>
				<div class="sup-cell">
					<div class="sup-k">정밀 엣지</div>
					<div class="sup-v">{supplyInsights.preciseEdgeCount ?? '-'}</div>
				</div>
				<div class="sup-cell">
					<div class="sup-k">산업 다양성</div>
					<div class="sup-v">{supplyInsights.industryDiversity ?? '-'}</div>
				</div>
			</div>

			{#if supplyInsights.topSupplyIndustries?.length}
				<div class="bar-list">
					<div class="bar-title">상위 공급 산업</div>
					{#each supplyInsights.topSupplyIndustries.slice(0, 5) as item}
						{@const max = supplyInsights.topSupplyIndustries[0]?.amount || 1}
						<div class="bar-row">
							<span class="bar-name">{item.name || item.industry}</span>
							<div class="bar-track">
								<div class="bar-fill" style:width="{(item.amount / max) * 100}%"></div>
							</div>
							<span class="bar-val">{fmtKor((item.amount || 0) * 1e8, '')}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}

	<!-- 핵심 거래 Top 5 -->
	{#if topPreciseEdges.length > 0}
		<div class="section">
			<h3>핵심 거래 (정밀 Top 5)</h3>
			<ul class="edge-list">
				{#each topPreciseEdges as e}
					<li>
						<div class="edge-row">
							<span class="edge-kind {e.kind === '공급' ? 'sup' : 'cus'}">{e.kind}</span>
							<strong>{e.corpName || e.partner?.label || '-'}</strong>
							{#if e.product}<span class="edge-prod">· {e.product}</span>{/if}
						</div>
						<div class="edge-amt">
							{Math.round(e.amount).toLocaleString()}억원
							{#if e.ratio}<span class="edge-ratio">({e.ratio}%)</span>{/if}
						</div>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- 5.5 2-hop 공급망 (있으면) -->
	{#if detail?.hop2?.hop2Neighbors?.length}
		<div class="section">
			<h3>
				2-hop 공급망
				{#if detail.hop2.hub}<span class="hop2-hub-tag">허브 · 제한됨</span>{/if}
			</h3>
			<p class="hop2-note">1-hop 이웃을 통해 연결된 회사 Top 10 · "내 공급사의 공급사"</p>
			<ul class="hop2-list">
				{#each detail.hop2.hop2Neighbors.slice(0, 10) as h (h.stockCode)}
					<li>
						<button class="hop2-far" onclick={() => onDetach?.(h.stockCode)}>{h.corpName}</button>
						<span class="hop2-via">경유: {h.viaName}</span>
					</li>
				{/each}
			</ul>
		</div>
	{/if}

	<!-- 6. AI 인사이트 + 블로그 -->
	{#if aiInsight}
		<div class="section">
			<h3>AI 분석</h3>
			{#if aiInsight.strengths?.length}
				<div class="chips">
					{#each aiInsight.strengths.slice(0, 4) as s}
						<span class="chip strength">✓ {s}</span>
					{/each}
				</div>
			{/if}
			{#if aiInsight.weaknesses?.length}
				<div class="chips">
					{#each aiInsight.weaknesses.slice(0, 4) as w}
						<span class="chip weak">⚠ {w}</span>
					{/each}
				</div>
			{/if}
			{#if aiInsight.narrative}
				<div class="narrative" class:expanded={aiExpanded}>
					{aiInsight.narrative}
				</div>
				{#if aiInsight.narrative.length > 200}
					<button class="more" onclick={() => (aiExpanded = !aiExpanded)}>
						{aiExpanded ? '▲ 접기' : '▼ 더보기'}
					</button>
				{/if}
			{/if}
		</div>
	{/if}

	<!-- 추가 블로그 포스트 (2개 초과 시) -->
	{#if blogPosts.length > 2}
		<div class="section">
			<h3>다른 분석 글 ({blogPosts.length - 2})</h3>
			{#each blogPosts.slice(2) as post}
				<a class="blog-card" href="{basePath}/blog/{post.slug}" target="_blank" rel="noopener">
					<div class="blog-title">{post.title}</div>
					{#if post.verdict}
						<div class="blog-verdict">{post.verdict}</div>
					{/if}
					<div class="blog-meta">
						{#if post.direction}<span class="blog-tag">{post.direction}</span>{/if}
						{#if post.archetype}<span class="blog-tag">{post.archetype}</span>{/if}
					</div>
				</a>
			{/each}
		</div>
	{/if}

	<!-- 비슷한 3사 추천 -->
	{#if detail?.peers?.length}
		<div class="section peers-rec">
			<h3>비슷한 회사</h3>
			<div class="peers-list">
				{#each detail.peers.slice(0, 3) as p (p.stockCode)}
					<button class="peer-chip" onclick={() => onDetach?.(p.stockCode) || onAddCompare?.(p.stockCode)}>
						<span class="peer-name">{p.corpName}</span>
						{#if p.revenue}<span class="peer-rev">{fmtKor(p.revenue * 1e8, '')}</span>{/if}
					</button>
				{/each}
			</div>
		</div>
	{/if}

	{:else}
	<CompanyCardDeep {node} {detail} {peerPct} />
	{/if}

	<!-- Disclaimer footer -->
	<div class="disclaimer">
		dartlab 은 공시·재무 데이터를 시각화합니다. 투자 자문 아님. 투자 결정은
		<a href="https://dart.fss.or.kr/" target="_blank" rel="noopener">DART 원본</a>
		과 증권사 리포트와 함께 내리세요.
		{#if dataAsOf?.dart || dataAsOf?.finance}
			<span class="src">· 데이터 최대 3h 지연</span>
		{/if}
	</div>
</div>

<style>
	.card {
		display: flex;
		flex-direction: column;
		gap: 0;
		padding: 10px 12px 16px;
		color: #f1f5f9;
		position: relative;
	}
	.close {
		position: absolute;
		top: 12px;
		right: 12px;
		background: none;
		border: none;
		font-size: 18px;
		cursor: pointer;
		color: #64748b;
		z-index: 2;
	}
	.close:hover {
		color: #f1f5f9;
	}

	.head-title-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}
	.head h2 {
		margin: 0;
		font-size: 16px;
		color: #f1f5f9;
	}
	.code {
		margin: 2px 0 8px;
		font-family: monospace;
		color: #64748b;
		font-size: 12px;
	}
	.badges {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		margin-bottom: 8px;
	}
	.badge {
		font-size: 11px;
		padding: 2px 8px;
		border-radius: 4px;
		font-weight: 500;
	}
	.badge.stage {
		background: rgba(52, 211, 153, 0.15);
		color: #34d399;
	}
	.badge.role {
		background: rgba(var(--amber-rgb), 0.12);
		color: var(--amber);
	}
	.badge.stream {
		background: rgba(167, 139, 250, 0.15);
		color: #a78bfa;
	}

	.loading {
		padding: 12px;
		color: #64748b;
		font-size: 12px;
		text-align: center;
	}

	/* T1: 3초 요약 · dartlab brand gradient */
	.t1-summary {
		margin-top: 12px;
		padding: 12px 14px;
		background: linear-gradient(135deg, rgba(234, 70, 71, 0.06), rgba(var(--amber-rgb), 0.04));
		border: 1px solid rgba(234, 70, 71, 0.15);
		border-radius: 8px;
	}
	.t1-verdict {
		font-size: 13px;
		line-height: 1.5;
		color: #f1f5f9;
		padding: 6px 0;
		margin-bottom: 8px;
		border-bottom: 1px dashed rgba(96, 165, 250, 0.2);
		font-weight: 500;
	}
	.t1-verdict.auto {
		color: #cbd5e1;
		font-size: 12px;
		font-family: monospace;
	}
	.direction-badge {
		display: inline-block;
		font-size: 11px;
		font-weight: 700;
		padding: 2px 10px;
		border-radius: 999px;
		margin-bottom: 6px;
	}
	.direction-badge.up {
		background: rgba(52, 211, 153, 0.18);
		color: #34d399;
	}
	.direction-badge.hold {
		background: rgba(251, 191, 36, 0.18);
		color: #fbbf24;
	}
	.direction-badge.down {
		background: rgba(239, 68, 68, 0.18);
		color: #f87171;
	}
	.priority-badges {
		display: flex;
		gap: 6px;
		flex-wrap: wrap;
		margin-top: 8px;
	}
	.priority-badge {
		font-size: 11px;
		font-weight: 600;
		padding: 3px 10px;
		border-radius: 4px;
	}
	.priority-badge.credit {
		background: rgba(96, 165, 250, 0.12);
		color: var(--color-dl-blue);
		border: 1px solid rgba(96, 165, 250, 0.25);
	}
	.priority-badge.mover.good {
		background: rgba(16, 185, 129, 0.12);
		color: var(--color-dl-success);
		border: 1px solid rgba(16, 185, 129, 0.25);
	}
	.priority-badge.mover.bad {
		background: rgba(239, 68, 68, 0.12);
		color: var(--color-dl-danger);
		border: 1px solid rgba(239, 68, 68, 0.25);
	}
	.priority-badge.mover.warn {
		background: rgba(251, 191, 36, 0.12);
		color: var(--color-dl-warning);
		border: 1px solid rgba(251, 191, 36, 0.25);
	}
	.radar-section {
		text-align: center;
	}
	.radar-wrap {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 4px;
	}
	.radar-hint {
		font-size: 9px;
		color: var(--color-dl-text-dim);
	}
	.scan-badges {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-top: 8px;
	}
	.scan-badge {
		font-size: 10px;
		padding: 2px 8px;
		border-radius: 4px;
		font-weight: 500;
		font-family: monospace;
		background: rgba(255, 255, 255, 0.06);
		border: 1px solid #1e2433;
		color: #cbd5e1;
		cursor: help;
	}
	.t1-grid {
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 8px;
	}
	.t1-cell {
		text-align: center;
	}
	.t1-k {
		font-size: 10px;
		color: #94a3b8;
		margin-bottom: 2px;
	}
	.t1-v {
		font-size: 16px;
		font-weight: 700;
		color: #f1f5f9;
		font-family: monospace;
	}
	.t1-d {
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
		margin-top: 2px;
	}

	.section {
		margin-top: 10px;
		padding-top: 10px;
		border-top: 1px solid #1e2433;
	}
	.section:first-of-type {
		border-top: none;
	}
	.section h3 {
		font-size: 11px;
		font-weight: 600;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin: 0 0 8px;
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.section h3 .year,
	.section h3 .peer {
		font-weight: 400;
		color: #64748b;
		text-transform: none;
	}

	.fin-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: 4px;
	}
	.sup-grid {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 6px;
	}
	.fin-cell,
	.sup-cell {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		padding: 8px 10px;
	}
	.fin-k,
	.sup-k {
		font-size: 10px;
		color: #94a3b8;
		margin-bottom: 2px;
	}
	.fin-v {
		font-size: 14px;
		font-weight: 600;
		color: #f1f5f9;
		font-family: monospace;
	}
	.sup-v {
		font-size: 13px;
		font-weight: 600;
		color: #f1f5f9;
	}

	.scan-grid {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.scan-row {
		display: flex;
		flex-direction: column;
		gap: 4px;
		padding: 6px 8px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 4px;
		font-size: 12px;
	}
	.scan-line1 {
		display: grid;
		grid-template-columns: 80px auto 1fr auto;
		align-items: center;
		gap: 8px;
	}
	.scan-k {
		color: #94a3b8;
	}
	.scan-v {
		font-weight: 600;
		font-family: monospace;
	}
	.scan-grade {
		color: #64748b;
		font-size: 11px;
	}
	.scan-pct {
		font-size: 10px;
		color: #64748b;
		font-family: monospace;
		text-align: right;
		cursor: help;
	}
	.scan-delta {
		font-size: 10px;
		font-family: monospace;
		font-weight: 600;
		padding: 1px 6px;
		border-radius: 3px;
		cursor: help;
	}
	.scan-delta.good {
		background: rgba(52, 211, 153, 0.12);
		color: #34d399;
	}
	.scan-delta.bad {
		background: rgba(239, 68, 68, 0.12);
		color: #f87171;
	}
	.scan-delta.extreme {
		background: rgba(251, 191, 36, 0.15);
		color: #fbbf24;
	}
	.scan-gauge {
		height: 4px;
		background: #1e2433;
		border-radius: 2px;
		overflow: hidden;
	}
	.scan-gauge-fill {
		height: 100%;
		transition: width 0.3s;
	}
	.rank-line {
		margin-top: 8px;
		font-size: 11px;
		color: #94a3b8;
	}
	.rank-line strong {
		color: #f1f5f9;
	}

	.hhi-card {
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 8px;
		padding: 10px 12px;
		margin-bottom: 8px;
	}
	.hhi-head {
		display: flex;
		justify-content: space-between;
		align-items: baseline;
		margin-bottom: 6px;
	}
	.hhi-label {
		font-size: 11px;
		color: #94a3b8;
	}
	.hhi-bucket {
		font-size: 13px;
		font-weight: 600;
	}
	.gauge {
		height: 6px;
		background: #1e2433;
		border-radius: 3px;
		overflow: hidden;
	}
	.gauge-fill {
		height: 100%;
		transition: width 0.3s;
	}
	.hhi-note {
		margin-top: 6px;
		font-size: 11px;
		color: #94a3b8;
	}
	.hhi-note strong {
		color: #f1f5f9;
	}

	.bar-list {
		margin-top: 10px;
	}
	.bar-title {
		font-size: 10px;
		color: #94a3b8;
		text-transform: uppercase;
		margin-bottom: 4px;
	}
	.bar-row {
		display: grid;
		grid-template-columns: 80px 1fr 60px;
		align-items: center;
		gap: 6px;
		padding: 3px 0;
		font-size: 11px;
	}
	.bar-name {
		color: #cbd5e1;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.bar-track {
		height: 6px;
		background: #1e2433;
		border-radius: 3px;
		overflow: hidden;
	}
	.bar-fill {
		height: 100%;
		background: #60a5fa;
	}
	.bar-val {
		text-align: right;
		color: #f1f5f9;
		font-family: monospace;
		font-size: 10px;
	}

	.edge-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.edge-list li {
		padding: 6px 0;
		border-bottom: 1px solid #1e2433;
	}
	.edge-list li:last-child {
		border-bottom: none;
	}
	.edge-row {
		display: flex;
		gap: 6px;
		align-items: baseline;
		font-size: 12px;
		color: #cbd5e1;
	}
	.edge-row strong {
		color: #f1f5f9;
	}
	.edge-kind {
		font-size: 10px;
		padding: 1px 5px;
		border-radius: 3px;
		font-weight: 600;
	}
	.edge-kind.sup {
		background: rgba(var(--amber-rgb), 0.15);
		color: var(--amber);
	}
	.edge-kind.cus {
		background: rgba(96, 165, 250, 0.15);
		color: #60a5fa;
	}
	.edge-prod {
		color: #94a3b8;
		font-size: 11px;
	}
	.edge-amt {
		font-size: 12px;
		color: #fbbf24;
		margin-top: 2px;
		font-family: monospace;
	}
	.edge-ratio {
		color: #64748b;
		font-size: 10px;
		margin-left: 4px;
	}

	/* 2-hop 섹션 */
	.hop2-hub-tag {
		font-size: 9px;
		padding: 1px 6px;
		background: rgba(251, 191, 36, 0.15);
		color: #fbbf24;
		border-radius: 3px;
		font-weight: 500;
		margin-left: 6px;
	}
	.hop2-note {
		margin: 0 0 8px;
		font-size: 11px;
		color: #64748b;
		line-height: 1.5;
	}
	.hop2-list {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.hop2-list li {
		display: flex;
		justify-content: space-between;
		gap: 8px;
		padding: 5px 0;
		border-bottom: 1px dashed #1e2433;
		font-size: 12px;
	}
	.hop2-list li:last-child {
		border-bottom: none;
	}
	.hop2-far {
		background: none;
		border: none;
		padding: 0;
		color: var(--color-dl-blue);
		font-weight: 500;
		font-size: inherit;
		cursor: pointer;
		text-align: left;
	}
	.hop2-far:hover {
		text-decoration: underline;
	}
	.hop2-via {
		color: #64748b;
		font-size: 10px;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-bottom: 6px;
	}
	.chip {
		font-size: 11px;
		padding: 3px 7px;
		border-radius: 4px;
	}
	.chip.strength {
		background: rgba(52, 211, 153, 0.12);
		color: #34d399;
	}
	.chip.weak {
		background: rgba(239, 68, 68, 0.12);
		color: #f87171;
	}
	.narrative {
		font-size: 12px;
		color: #cbd5e1;
		line-height: 1.6;
		max-height: 80px;
		overflow: hidden;
		position: relative;
	}
	.narrative:not(.expanded)::after {
		content: '';
		position: absolute;
		bottom: 0;
		left: 0;
		right: 0;
		height: 20px;
		background: linear-gradient(transparent, #0f1219);
	}
	.narrative.expanded {
		max-height: none;
	}
	.more {
		background: none;
		border: none;
		color: #60a5fa;
		font-size: 11px;
		cursor: pointer;
		padding: 4px 0;
	}

	.blog-banner {
		margin-top: 12px;
		padding: 10px 12px;
		background: linear-gradient(135deg, rgba(96, 165, 250, 0.12), rgba(52, 211, 153, 0.08));
		border: 1px solid rgba(96, 165, 250, 0.3);
		border-radius: 8px;
	}
	.banner-title {
		font-size: 11px;
		color: #60a5fa;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.03em;
		margin-bottom: 8px;
	}
	.blog-card {
		display: block;
		text-decoration: none;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		padding: 10px 12px;
		margin-bottom: 6px;
		transition: border-color 0.15s, background 0.15s;
	}
	.blog-card:hover {
		border-color: #60a5fa;
		background: #0b1120;
	}
	.blog-card.featured {
		border-color: rgba(96, 165, 250, 0.4);
	}
	.blog-card.featured:hover {
		border-color: #60a5fa;
		box-shadow: 0 0 0 1px #60a5fa;
	}
	.blog-cta {
		color: #60a5fa;
		font-weight: 600;
		font-size: 10px;
		margin-left: auto;
	}
	.blog-title {
		font-size: 13px;
		color: #f1f5f9;
		font-weight: 600;
	}
	.blog-verdict {
		margin-top: 4px;
		font-size: 11px;
		color: #cbd5e1;
		line-height: 1.4;
	}
	.blog-meta {
		display: flex;
		gap: 4px;
		margin-top: 6px;
	}
	.blog-tag {
		font-size: 10px;
		padding: 1px 6px;
		background: rgba(96, 165, 250, 0.12);
		color: #60a5fa;
		border-radius: 3px;
	}

	/* 비슷한 회사 추천 */
	.peers-rec h3 {
		margin-bottom: 6px;
	}
	.peers-list {
		display: flex;
		gap: 4px;
		flex-wrap: wrap;
	}
	.peer-chip {
		display: inline-flex;
		gap: 4px;
		align-items: center;
		padding: 4px 10px;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		color: #60a5fa;
		font-size: 11px;
		cursor: pointer;
	}
	.peer-chip:hover {
		background: rgba(96, 165, 250, 0.08);
		border-color: #334155;
	}
	.peer-rev {
		color: #64748b;
		font-family: monospace;
		font-size: 10px;
	}

	.disclaimer {
		margin-top: 16px;
		padding-top: 12px;
		border-top: 1px dashed #1e2433;
		font-size: 10px;
		line-height: 1.5;
		color: #475569;
	}
	.disclaimer a {
		color: #60a5fa;
		text-decoration: none;
	}
	.disclaimer a:hover {
		text-decoration: underline;
	}
	.disclaimer .src {
		color: #64748b;
	}

	/* 탭 바 */
	.tab-bar {
		display: flex;
		gap: 0;
		border-bottom: 1px solid var(--color-dl-border);
		margin: 0 -16px;
		padding: 0 16px;
	}
	.tab-btn {
		flex: 1;
		background: none;
		border: none;
		border-bottom: 2px solid transparent;
		padding: 8px 0;
		font-size: 13px;
		font-weight: 600;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		transition: all 0.15s;
	}
	.tab-btn:hover {
		color: var(--color-dl-text-muted);
	}
	.tab-btn.active {
		color: var(--color-dl-primary-light);
		border-bottom-color: var(--color-dl-primary);
	}

</style>
