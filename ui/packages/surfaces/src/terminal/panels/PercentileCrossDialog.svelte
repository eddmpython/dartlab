<script lang="ts">
	// 유니버스 교차 백분위 다이얼로그 · 한 회사의 분야별 백분위를 *여러 잣대*(업종 / 소속시장 / 전체상장사)에서 한 좌표로.
	// ★핵심 통찰: "잣대를 바꾸니 순위가 뒤집힌다"(유니버스-민감도). scan-grade(종합평가·판정)와 레인 분리 · 본 화면은 *분포 사실(상위 N%)만, 판정 0*.
	// ★신규 능력 0: 데이터는 engine.percentileIn(code, universe)(EcoNode 전종목 raw 재필터·새 데이터 0). 모달 크롬은 전역 .scrimWrap/.scrModal/.scrHead/.scrClose 재사용.
	// 정직: composite/verdict/매수매도·목표주가 금지(scan-grade 레인). 결손 축은 "·"(0대체 금지). 가격은 펀더와 분리 격자. n<10 띠·곡선 숨김. 유니버스별 출처·cross-sector caveat 강제.
	import type { Company, Lang, Universe, UniversePercentile, PercentileMetric } from '../lib/types';
	import DistCurve from './DistCurve.svelte';

	interface Props {
		co: Company;
		lang: Lang;
		percentileIn: (code: string, universe: Universe) => UniversePercentile | null;
		onClose: () => void;
	}
	let { co, lang, percentileIn, onClose }: Props = $props();

	const UNIS: Universe[] = ['industry', 'market', 'all'];
	const MIN_N = 10; // 표본 부족 임계 · n<10 유니버스는 띠·곡선 숨김(02 정직 가드).
	const SPREAD_FLIP = 30; // 유니버스 백분위 max-min ≥ 이 값이면 "잣대 민감"(뒤집힘) 표식 ⇄.

	// 3 유니버스 산출 · 다이얼로그 열 때 1회(라이브). null(노드 없음)은 제외.
	const data = $derived(UNIS.map((u) => percentileIn(co.code, u)).filter((d): d is UniversePercentile => d != null));
	const uniName = (d: UniversePercentile): string =>
		d.universe === 'all' ? (lang === 'en' ? 'All listed' : '전체상장') : d.label;

	// 정량 행 = 비-gov 지표(거버넌스는 정성 등급으로 분리 · RightStack 패널과 동일). 행 순서 = 지표 가장 많은 유니버스 기준.
	const rowDefs = $derived.by<PercentileMetric[]>(() => {
		if (!data.length) return [];
		const best = data.reduce((a, b) => (b.metrics.length > a.metrics.length ? b : a), data[0]);
		return best.metrics.filter((m) => m.axis !== 'gov');
	});
	const uniMaps = $derived(data.map((d) => new Map(d.metrics.map((m) => [m.en, m] as const))));

	// 정성 등급 행 · union by key(순서 = 첫 유니버스).
	const qualKeys = $derived.by<{ key: string; kr: string; en: string }[]>(() => {
		const seen = new Map<string, { key: string; kr: string; en: string }>();
		for (const d of data) for (const g of d.grades) if (!seen.has(g.key)) seen.set(g.key, { key: g.key, kr: g.kr, en: g.en });
		return [...seen.values()];
	});
	const qualMaps = $derived(data.map((d) => new Map(d.grades.map((g) => [g.key, g] as const))));

	// 뒤집힘 표식 · 유니버스 백분위 max-min(분포 사실, 판정 아님). n<10 유니버스는 제외.
	const spreadOf = (en: string): number => {
		const ps = data
			.map((d, i) => (d.n >= MIN_N ? uniMaps[i].get(en)?.p : null))
			.filter((p): p is number => p != null);
		return ps.length >= 2 ? Math.max(...ps) - Math.min(...ps) : 0;
	};

	const pcCol = (p: number): string => (p >= 80 ? 'var(--up)' : p >= 55 ? 'var(--good)' : p >= 35 ? 'var(--warn)' : 'var(--dn)');
	const tcls = (t: string) => (({ up: 'tUp', good: 'tGood', neutral: 'tNeu', warn: 'tWarn', down: 'tDn' }) as Record<string, string>)[t] || 'tNeu';
	// 등급 톤 → 막대 색(터미널 토큰, 신규 색 0) · 정성 등급 분포 스택바.
	const TONE_COL: Record<string, string> = { up: 'var(--up)', good: 'var(--good)', neutral: 'var(--dim)', warn: 'var(--warn)', down: 'var(--dn)' };
	const topPct = (p: number): string => (lang === 'en' ? 'top ' + (100 - p + 1) + '%' : '상위 ' + (100 - p + 1) + '%');
	const fmtVal = (m: { unit: string; v: number | null } | undefined): string => {
		if (!m || m.v == null) return '·';
		if (m.unit === '배') return m.v.toFixed(1) + (lang === 'en' ? 'x' : '배');
		if (m.unit === '일') return m.v.toFixed(0) + (lang === 'en' ? 'd' : '일');
		if (m.unit === '') return m.v.toFixed(2);
		if (m.unit === '점') return m.v.toFixed(0);
		return m.v.toFixed(1) + (m.unit === '%' ? '%' : '');
	};
	// 값(절대 사실, 유니버스 무관) · 먼저 발견되는 유니버스에서.
	const valOf = (en: string): string => {
		for (const map of uniMaps) { const m = map.get(en); if (m) return fmtVal(m); }
		return '·';
	};
	const fmtX = (v: number | null): string => (v == null ? '·' : v.toFixed(v < 10 ? 2 : 1) + (lang === 'en' ? 'x' : '배'));

	$effect(() => {
		const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div
		class="scrModal pcxModal"
		role="dialog"
		aria-modal="true"
		aria-label={lang === 'en' ? 'Cross-universe percentile' : '유니버스 교차 백분위'}
		onclick={(e) => e.stopPropagation()}
		style={`--ucols:${data.length}`}
	>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'CROSS-UNIVERSE PERCENTILE' : '유니버스 교차 백분위'}</span>
			<span class="pcxWho">{co.name.kr}<i>{co.marketLabel} · {co.sector.kr}</i></span>
			<span class="pcxLens">{lang === 'en' ? 'distribution facts · top N%' : '분포 사실 · 상위 N%'}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		<div class="pcxBody">
			{#if !data.length}
				<div class="pcxNone">{lang === 'en' ? 'No comparison data for this company.' : '이 회사의 비교 데이터가 없습니다.'}</div>
			{:else}
				<!-- 정량 격자: 행=지표 × 열=유니버스 *분포곡선*(동종사 밀집 위치 + 이 회사 마커). 막대 아닌 분포가 1차 시각. 업종(앵커) 좌측 강조. -->
				<div class="pcxLegend">{lang === 'en'
					? 'bars = peer count (taller = more peers, p2-p98) · ▼ pin = this company · dashed = median · bottom strip: green side = better direction (not for price) · ⇄ = rank flips by universe'
					: '막대 = 동종사 수(높을수록 많이 몰림, p2~p98) · ▼ 핀 = 이 회사 · 점선 = 중앙값 · 하단 색띠: 초록 쪽 = 좋은 방향(가격 제외) · ⇄ = 잣대 따라 순위 뒤집힘'}</div>
				<!-- 컬럼 헤더 · pcxBody 직속 + sticky 라 정성/가격까지 스크롤해도 유니버스 열이 상단 고정. -->
				<div class="pcxHead">
					<span class="pcxNameH">{lang === 'en' ? 'metric · value' : '지표 · 값'}</span>
					{#each data as d, i (d.universe)}
						<span class={'pcxColH' + (d.universe === 'industry' ? ' anchor' : '')}>{uniName(d)}<i>n={d.n}</i></span>
					{/each}
				</div>
				<div class="pcxTable">
					{#each rowDefs as row (row.en)}
						{@const flip = spreadOf(row.en) >= SPREAD_FLIP}
						<div class="pcxRow">
							<span class="pcxNameCell">
								<span class="pcxName">{#if flip}<span class="pcxFlip" title={lang === 'en' ? 'lens-sensitive (rank flips by universe)' : '잣대 민감 · 유니버스 따라 순위 뒤집힘'}>⇄</span>{/if}{lang === 'en' ? row.en : row.kr}</span>
								<span class="pcxNameVal mono">{valOf(row.en)}</span>
							</span>
							{#each data as d, i (d.universe)}
								{@const m = uniMaps[i].get(row.en)}
								<span class={'pcxCell' + (d.universe === 'industry' ? ' anchor' : '')}>
									{#if d.n < MIN_N}
										<span class="pcxThin">{lang === 'en' ? 'n<10' : '표본부족'}</span>
									{:else if m && m.p != null && (m.hist || m.band)}
										<span class="pcxCurve"><DistCurve hist={m.hist} band={m.band} value={m.v} p={m.p} unit={m.unit} {lang} h={36} /><span class="pcxDir" class:low={m.lowerBetter}></span></span>
										<span class="pcxP" style={`color:${pcCol(m.p)}`}>{topPct(m.p)}</span>
									{:else if m && m.p != null}
										<span class="pcxTrack"><span class="pcxFill" style={`width:${m.p}%;background:${pcCol(m.p)}`}></span></span>
										<span class="pcxP" style={`color:${pcCol(m.p)}`}>{topPct(m.p)} <i class="pcxNoDist">{lang === 'en' ? 'rank only' : '분포없음'}</i></span>
									{:else}
										<span class="pcxDash">·</span>
									{/if}
								</span>
							{/each}
						</div>
					{/each}
				</div>

				<!-- 정성 등급 · 백분위 아님(띠 없음). 등급 칩 + 이 유니버스 내 동급 비중. 정량과 dashed 분리. -->
				{#if qualKeys.length}
					<div class="pcxQualHead">{lang === 'en' ? 'qualitative · grade & same-grade share (not a percentile)' : '정성 · 등급 · 동급 비중 (백분위 아님)'}</div>
					<div class="pcxTable">
						{#each qualKeys as q (q.key)}
							<div class="pcxRow qual">
								<span class="pcxNameCell"><span class="pcxName">{lang === 'en' ? q.en : q.kr}</span></span>
								{#each data as d, i (d.universe)}
									{@const g = qualMaps[i].get(q.key)}
									<span class={'pcxCell' + (d.universe === 'industry' ? ' anchor' : '')}>
										{#if g}
											<span class="pcxQTop"><span class={'pcxChip ' + tcls(g.tone)}>{g.v}</span>{#if g.sameShare != null}<span class="pcxShare">{lang === 'en' ? g.sameShare + '%' : '동급 ' + g.sameShare + '%'}</span>{/if}</span>
											{#if g.dist.length}
												<span class="pcxQStack" title={g.dist.filter((x) => x.share > 0).map((x) => `${x.step} ${x.share}%`).join(' · ')}>
													{#each g.dist as x (x.step)}{#if x.share > 0}<span class={'pcxQSeg' + (x.step === g.v ? ' on' : '')} style={`width:${x.share}%;background:${TONE_COL[x.tone] ?? 'var(--dim)'}`}></span>{/if}{/each}
												</span>
											{/if}
										{:else}
											<span class="pcxDash">·</span>
										{/if}
									</span>
								{/each}
							</div>
						{/each}
					</div>
				{/if}

				<!-- 가격(PER/PBR) · 펀더와 *분리*. 시장 시세 기반(펀더멘털 아님). 톤색·우열 프레이밍 없음(02 KILL#2). -->
				{#if data.some((d) => d.price.per.v != null || d.price.pbr.v != null)}
					<div class="pcxPriceHead">{lang === 'en' ? 'price (market quote · lower = cheaper)' : '가격 지표 · 시장 시세 기반 · 낮을수록 저평가'} · {co.price.asOf}</div>
					<div class="pcxTable">
						{#each [{ k: 'per', kr: 'PER', en: 'PER' }, { k: 'pbr', kr: 'PBR', en: 'PBR' }] as pr (pr.k)}
							<div class="pcxRow price">
								<span class="pcxNameCell">
									<span class="pcxName">{lang === 'en' ? pr.en : pr.kr}</span>
									<span class="pcxNameVal mono">{fmtX(pr.k === 'per' ? data[0]?.price.per.v ?? null : data[0]?.price.pbr.v ?? null)}</span>
								</span>
								{#each data as d, i (d.universe)}
									{@const ps = pr.k === 'per' ? d.price.per : d.price.pbr}
									<span class={'pcxCell' + (d.universe === 'industry' ? ' anchor' : '')}>
										{#if ps.v != null && ps.p != null && (ps.hist || ps.band) && ps.n >= MIN_N}
											<span class="pcxCurve"><DistCurve hist={ps.hist} band={ps.band} value={ps.v} p={ps.p} unit={lang === 'en' ? 'x' : '배'} {lang} h={36} neutral /></span>
											<span class="pcxP dim">{lang === 'en' ? ps.p + '%ile' : '분포 ' + ps.p + '%'}</span>
										{:else if ps.v != null && ps.p != null && ps.n >= MIN_N}
											<span class="pcxTrack"><span class="pcxFill priceFill" style={`width:${ps.p}%`}></span></span>
											<span class="pcxP dim">{lang === 'en' ? ps.p + '%ile' : '분포 ' + ps.p + '%'}</span>
										{:else}
											<span class="pcxDash">·</span>
										{/if}
									</span>
								{/each}
							</div>
						{/each}
					</div>
				{/if}

				<!-- 정직 라벨 · 출처·cross-sector·결손·BLOCKED. provenance 없는 셀 = 회귀(02 가드). -->
				<div class="pcxNotes">
					<div>※ {lang === 'en'
						? 'Industry band: industryStats · KSIC sector · equal-weight · listed primary (≠ KRX cap-weighted index). Market/All: live 5-quantile from EcoNode population.'
						: '업종 분포: industryStats · KSIC 섹터 · 동일가중 · 상장 primary (≠ KRX 시총가중 업종지수). 시장·전체: EcoNode 모집단 라이브 5분위.'}</div>
					<div>※ {lang === 'en'
						? 'All-listed mixes sectors (financials · manufacturing) → margin/ROE percentile is sector-dependent (context, not a headline). Industry is the anchor.'
						: '전체상장 = 금융·제조 혼재 → 마진·ROE 백분위는 섹터 의존(맥락용 잣대, 헤드라인 아님). 업종이 기본 앵커.'}</div>
					<div>※ {lang === 'en'
						? '"·" = absent from filings (not 0). "n<10" = sample too small (band/curve hidden).'
						: '"·" = 공시에 없음(0 아님). "표본부족" = n<10(띠·곡선 숨김).'}</div>
					<div>※ {lang === 'en'
						? 'Index membership (KOSPI200 · KOSDAQ150) is BLOCKED · constituent data absent. No "top-N by cap ≈ index" approximation (would be fabrication).'
						: '소속지수(KOSPI200·코스닥150) = BLOCKED · 구성종목 데이터 부재. "시총 상위 N = 지수 근사" 우회 안 함(위조 금지).'}</div>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.pcxModal {
		width: min(720px, 94vw);
	}
	.pcxWho {
		font-size: 12px;
		font-weight: 700;
		color: var(--dl-ink, #c8cfdb);
	}
	.pcxWho i {
		font-style: normal;
		font-weight: 400;
		margin-left: 7px;
		font-size: 10.5px;
		color: #aeb6c2;
	}
	.pcxLens {
		font-size: 10px;
		color: #aeb6c2;
		font-style: italic;
	}
	.pcxBody {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		padding: 12px 14px 16px;
	}
	.pcxNone {
		padding: 40px 0;
		text-align: center;
		font-size: 12px;
		color: #aeb6c2;
	}
	/* 행×열 격자 · head·row 동일 grid template (지표명 | 유니버스 N칸 | 값). */
	.pcxHead,
	.pcxRow {
		display: grid;
		grid-template-columns: minmax(94px, 1fr) repeat(var(--ucols, 3), minmax(0, 1fr));
		gap: 10px;
		align-items: center;
	}
	/* 컬럼 헤더 · 스크롤 고정. pcxBody 직속이라 정성/가격 섹션까지 유니버스 열이 상단에 유지된다. */
	.pcxHead {
		position: sticky;
		top: 0;
		z-index: 3;
		background: var(--dl-bg-raised, #0e141f);
		padding: 7px 6px 6px;
		border-bottom: 1px solid var(--dl-line-strong, #2a3142);
		margin-bottom: 2px;
	}
	.pcxNameH,
	.pcxColH {
		font-size: 9.5px;
		font-weight: 700;
		letter-spacing: 0.03em;
		color: #aeb6c2;
		text-transform: uppercase;
	}
	.pcxColH {
		display: flex;
		flex-direction: column;
		line-height: 1.25;
	}
	.pcxColH.anchor {
		color: var(--amber, var(--amber));
	}
	.pcxColH i {
		font-style: normal;
		font-weight: 400;
		font-size: 9px;
		font-variant-numeric: tabular-nums;
		color: #aeb6c2;
	}
	/* 분포 곡선 범례 */
	.pcxLegend {
		font-size: 9.5px;
		color: #aeb6c2;
		padding: 2px 6px 8px;
		line-height: 1.4;
	}
	.pcxRow {
		border-bottom: 1px solid var(--dl-line, #1b2130);
		padding: 7px 6px;
	}
	/* 지표 셀 = 지표명 + 그 아래 실측값(별도 값 컬럼 폐지). */
	.pcxNameCell {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	.pcxNameVal {
		font-size: 10.5px;
		font-weight: 600;
		font-variant-numeric: tabular-nums;
		color: var(--dl-ink, #c8cfdb);
	}
	.pcxName {
		font-size: 11px;
		font-weight: 600;
		color: var(--dl-ink, #c8cfdb);
		display: flex;
		align-items: center;
		gap: 3px;
		min-width: 0;
	}
	.pcxFlip {
		color: #aeb6c2;
		font-size: 11px;
		font-weight: 700;
		flex: 0 0 auto;
	}
	.pcxCell {
		display: flex;
		flex-direction: column;
		gap: 1px;
		min-width: 0;
	}
	/* 분포 히스토그램 = 1차 시각(동종사 밀집 + 회사 핀). DistCurve 가 width:100% 로 셀 채움. */
	.pcxCurve {
		position: relative;
		width: 100%;
		line-height: 0;
	}
	/* 하단 0라인 방향 색띠 · 초록 쪽 = 좋은 방향(지표 의미). 회사 핀이 이 띠 위 어디에 있는지로 좋고나쁨이 와닿음. */
	.pcxDir {
		position: absolute;
		left: 0;
		right: 0;
		bottom: 0;
		height: 3px;
		border-radius: 1px;
		background: linear-gradient(to right, rgba(248, 81, 73, 0.5), rgba(210, 153, 34, 0.32), rgba(63, 185, 80, 0.5));
	}
	.pcxDir.low {
		background: linear-gradient(to right, rgba(63, 185, 80, 0.5), rgba(210, 153, 34, 0.32), rgba(248, 81, 73, 0.5));
	}
	.pcxNoDist {
		font-style: italic;
		font-weight: 400;
		color: #aeb6c2;
	}
	.pcxTrack {
		height: 8px;
		width: 100%;
		background: var(--dl-bg-overlay, rgba(255, 255, 255, 0.05));
		border-radius: 2px;
		overflow: hidden;
	}
	.pcxFill {
		display: block;
		height: 100%;
		border-radius: 2px;
	}
	.pcxFill.priceFill {
		background: rgba(139, 148, 158, 0.55); /* 가격 = 중립 회색(우열 프레이밍 금지) */
	}
	.pcxP {
		font-size: 9px;
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-variant-numeric: tabular-nums;
		font-weight: 700;
	}
	.pcxP.dim {
		color: #aeb6c2 !important;
		font-weight: 400;
	}
	.pcxThin,
	.pcxDash {
		font-size: 9.5px;
		color: #aeb6c2;
		font-style: italic;
	}
	/* 정성 칩 + 동급비중 */
	.pcxQualHead,
	.pcxPriceHead {
		margin-top: 14px;
		padding: 6px 6px 4px;
		font-size: 9.5px;
		font-weight: 700;
		letter-spacing: 0.02em;
		color: #aeb6c2;
		border-top: 1px dashed var(--dl-line, #1b2130);
	}
	.pcxQTop {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.pcxChip {
		font-size: 10.5px;
		font-weight: 700;
		padding: 1px 7px;
		border-radius: 9px;
		border: 1px solid var(--dl-line, #1b2130);
		background: rgba(255, 255, 255, 0.03);
		white-space: nowrap;
	}
	.pcxShare {
		font-size: 9px;
		color: #aeb6c2;
		font-variant-numeric: tabular-nums;
	}
	/* 정성 등급 분포 스택바 · 등급레벨별 동종사 비중(넓은 칸 = 많이 몰림). 회사 등급 = 불투명+테두리. */
	.pcxQStack {
		display: flex;
		width: 100%;
		height: 7px;
		border-radius: 2px;
		overflow: hidden;
		background: var(--dl-bg-overlay, rgba(255, 255, 255, 0.05));
		margin-top: 2px;
	}
	.pcxQSeg {
		height: 100%;
		min-width: 1px;
		opacity: 0.45;
	}
	.pcxQSeg.on {
		opacity: 1;
		outline: 1px solid rgba(255, 255, 255, 0.65);
		outline-offset: -1px;
	}
	.pcxNotes {
		margin-top: 12px;
		padding-top: 8px;
		border-top: 1px solid var(--dl-line, #1b2130);
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.pcxNotes div {
		font-size: 9px;
		line-height: 1.45;
		color: #aeb6c2;
	}
	/* 톤 색 · 터미널 토큰(신규 색 0) */
	.tUp {
		color: var(--up);
	}
	.tGood {
		color: var(--good);
	}
	.tNeu {
		color: #aeb6c2;
	}
	.tWarn {
		color: var(--warn);
	}
	.tDn {
		color: var(--dn);
	}
</style>
