<script lang="ts">
	import { base } from '$app/paths';
	import Section from '$lib/components/ui/Section.svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Eyebrow from '$lib/components/ui/Eyebrow.svelte';
	import MonoNumber from '$lib/components/ui/MonoNumber.svelte';
	import Tag from '$lib/components/ui/Tag.svelte';
	import { fmtKrwFromEok, fmtPrice } from '@dartlab/ui-format/krw';
	import { fmtPct, fmtMul } from '@dartlab/ui-format/pct';

	// 샘플 데이터 (디자인 검증용)
	const sampleCompany = {
		code: '005930',
		name: '삼성전자',
		market: 'KOSPI',
		sector: '반도체 · 제조',
		revenue: 2904282, // 억 단위
		opMargin: 18.5,
		roe: 12.3,
		debtRatio: 78.4,
		altmanZ: 3.42,
		yoyChange: 4.7,
		verdict: { call: 'HOLD', confidence: 64 }
	};

	const sectionsAlt = [
		{ num: '01', title: '지난 5년 · LOOKING BACK', sub: '재무 시계열로 본 회사의 발자국' },
		{ num: '02', title: '품질 · QUALITY CHECK', sub: 'DuPont · ROIC vs WACC · Piotroski' },
		{ num: '03', title: '미래 · LOOKING AHEAD', sub: '4모델 블렌딩 · Bull · Base · Bear' }
	];
</script>

<svelte:head>
	<title>dartlab · /lab · 디자인 시스템 검증</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<!-- ─── editorial nav ─── -->
<header class="lab-nav">
	<div class="nav-inner">
		<a href="{base}/" class="brand">
			<span class="brand-mark">dartlab</span>
			<span class="brand-slash">/</span>
			<span class="brand-ctx">lab</span>
		</a>
		<nav class="nav-links">
			<a href="{base}/terminal" class="nav-link">/terminal</a>
			<a href="{base}/lab/viewer-search" class="nav-link">/viewer-search</a>
			<a href="{base}/lab/viewer-analyze" class="nav-link">/viewer-analyze</a>
			<a href="{base}/lab/viewer-dev/005930" class="nav-link">/viewer-dev</a>
			<a href="{base}/lab/map" class="nav-link">/map</a>
			<a href="{base}/lab/compare" class="nav-link">/compare</a>
			<a href="{base}/lab/screener" class="nav-link">/screener</a>
			<a href="{base}/lab/duckdb" class="nav-link">/duckdb</a>
		</nav>
	</div>
</header>

<!-- ─── Hero · editorial brutalist ─── -->
<section class="hero">
	<div class="hero-inner">
		<Eyebrow text="dartlab · design tokens · v1" />
		<h1 class="hero-h1">
			읽히는 재무 분석.<br />
			<span class="hero-h1-em">비교 가능한 숫자.</span><br />
			절제된 빛.
		</h1>
		<p class="hero-sub">
			1970년대 금융 저널의 지면을 OLED 패널 위에서 다시 읽는다. 한국어로, 무료로, 서버 없이.
			<br />이 페이지는 디자인 시스템 검증용. dartlab 의 새 정체성을 한 화면에 모았다.
		</p>
	</div>
</section>

<!-- ─── 섹션 데모 ─── -->
<Section
	number="01"
	eyebrow="LIVE PREVIEW"
	title="회사 한 페이지의 첫 인상"
	subtitle="회사명 · 종목코드 · 업종 · 핵심 지표 4개 + Verdict. 사용자가 30초 안에 판단할 정보."
>
	<div class="company-hero">
		<div class="ch-left">
			<div class="ch-meta">
				<span class="dl-mono">{sampleCompany.market}</span>
				<span class="ch-dot"></span>
				<span class="dl-mono">{sampleCompany.code}</span>
				<span class="ch-dot"></span>
				<span>{sampleCompany.sector}</span>
			</div>
			<h2 class="dl-h1-kr ch-name">{sampleCompany.name}</h2>
			<div class="ch-tags">
				<Tag>대형주</Tag>
				<Tag tone="info">반도체</Tag>
				<Tag tone="good" filled>성숙기</Tag>
			</div>
		</div>
		<div class="ch-right">
			<Card eyebrow="VERDICT" accent="warn">
				<div class="verdict">
					<div class="v-call">보유 · HOLD</div>
					<div class="v-conf">
						<span class="dl-label">확신도</span>
						<MonoNumber value={sampleCompany.verdict.confidence} suffix="%" tone="ink" align="left" />
					</div>
					<p class="v-line">강점과 약점이 혼재. 실적 발표 대기 구간.</p>
				</div>
			</Card>
		</div>
	</div>
</Section>

<!-- ─── KPI 그리드 · 한국 표준 컬러 + tabular-nums ─── -->
<Section
	number="02"
	eyebrow="KPI · QUALITY"
	title="핵심 지표 4축"
	subtitle="ROE · 영업이익률 · 부채비율 · Altman Z. 한국 컨벤션 (상승 빨강 · 하락 파랑)."
>
	<div class="kpi-grid">
		<Card eyebrow="ROE" padded>
			<div class="kpi-row">
				<MonoNumber value={fmtPct(sampleCompany.roe, { withSign: false })} size="xl" tone="up" align="left" />
				<Tag tone="up" filled>YoY +1.2%p</Tag>
			</div>
			<p class="kpi-note">동종 업종 중앙값 8.4% 상회</p>
		</Card>

		<Card eyebrow="영업이익률" padded>
			<div class="kpi-row">
				<MonoNumber value={fmtPct(sampleCompany.opMargin)} size="xl" tone="up" align="left" />
				<Tag tone="up" filled>+0.4%p</Tag>
			</div>
			<p class="kpi-note">5년 평균 16.8%</p>
		</Card>

		<Card eyebrow="부채비율" padded>
			<div class="kpi-row">
				<MonoNumber value={fmtPct(sampleCompany.debtRatio, { digits: 0 })} size="xl" tone="ink" align="left" />
				<Tag tone="warn">관찰</Tag>
			</div>
			<p class="kpi-note">업종 평균 65% 대비 높음</p>
		</Card>

		<Card eyebrow="Altman Z" padded>
			<div class="kpi-row">
				<MonoNumber value={fmtMul(sampleCompany.altmanZ)} size="xl" tone="good" align="left" />
				<Tag tone="good" filled>안전</Tag>
			</div>
			<p class="kpi-note">3.0 이상 = Safe Zone</p>
		</Card>
	</div>
</Section>

<!-- ─── 한국어 숫자 포맷 데모 ─── -->
<Section
	eyebrow="NUMBER FORMAT"
	title="한국어 숫자 표기 · SSOT"
	subtitle="만 단위 (10⁴) 기반. 조 · 억 · 만. 0.X 조는 X,XXX억으로 (한국 직관)."
	container="article"
>
	<table class="num-table">
		<thead>
			<tr>
				<th>raw 값 (원)</th>
				<th>fmtKrw 결과</th>
				<th>fmtKrwFromEok</th>
			</tr>
		</thead>
		<tbody>
			<tr>
				<td><MonoNumber value="290,428,242,979,141" align="right" /></td>
				<td><MonoNumber value={fmtKrwFromEok(2904282)} tone="ink" align="left" /></td>
				<td>2,904,282억</td>
			</tr>
			<tr>
				<td><MonoNumber value="850,000,000,000" align="right" /></td>
				<td><MonoNumber value={fmtKrwFromEok(8500)} tone="ink" align="left" /></td>
				<td>8,500억</td>
			</tr>
			<tr>
				<td><MonoNumber value="12,000,000" align="right" /></td>
				<td><MonoNumber value={fmtKrwFromEok(0.12)} tone="ink" align="left" /></td>
				<td>1,200만</td>
			</tr>
			<tr>
				<td><MonoNumber value="79,300" align="right" /></td>
				<td><MonoNumber value={fmtPrice(79300)} tone="ink" align="left" /></td>
				<td>주가 (₩)</td>
			</tr>
		</tbody>
	</table>
</Section>

<!-- ─── 색상 컬러 칩 ─── -->
<Section eyebrow="COLOR" title="컬러 토큰" subtitle="brand red→orange · 한국 금융 컨벤션 (up 빨강 / down 파랑) · 4단계 elevation.">
	<div class="swatch-grid">
		<div class="sw" style="background: var(--dl-bg-base)"><span>base</span><code class="dl-mono">#0F0F10</code></div>
		<div class="sw" style="background: var(--dl-bg-raised)"><span>raised</span><code class="dl-mono">#16171A</code></div>
		<div class="sw" style="background: var(--dl-bg-overlay)"><span>overlay</span><code class="dl-mono">#1D1F23</code></div>
		<div class="sw" style="background: var(--dl-bg-modal)"><span>modal</span><code class="dl-mono">#25272D</code></div>
		<div class="sw red"><span>red</span><code class="dl-mono">#EA4647</code></div>
		<div class="sw orange"><span>orange</span><code class="dl-mono">#FB923C</code></div>
		<div class="sw up"><span>up · 한국</span><code class="dl-mono">#E43F3F</code></div>
		<div class="sw down"><span>down · 한국</span><code class="dl-mono">#1D64DC</code></div>
		<div class="sw good"><span>good</span><code class="dl-mono">#34D399</code></div>
		<div class="sw warn"><span>warn</span><code class="dl-mono">#FBBF24</code></div>
		<div class="sw bad"><span>bad</span><code class="dl-mono">#EF4444</code></div>
		<div class="sw info"><span>info</span><code class="dl-mono">#60A5FA</code></div>
	</div>
</Section>

<!-- ─── 타이포 ─── -->
<Section eyebrow="TYPOGRAPHY" title="타이포 위계" subtitle="Newsreader (slab) · Pretendard Variable · JetBrains Mono.">
	<div class="type-stack">
		<div>
			<span class="dl-eyebrow">H1 · slab serif (영문)</span>
			<h1 class="dl-h1">Editorial Dark</h1>
		</div>
		<div>
			<span class="dl-eyebrow">H1 · 한글</span>
			<h1 class="dl-h1-kr">읽히는 재무 분석</h1>
		</div>
		<div>
			<span class="dl-eyebrow">H2 · 한글</span>
			<h2 class="dl-h2-kr">비교 가능한 숫자</h2>
		</div>
		<div>
			<span class="dl-eyebrow">Body · 본문 17px / line-height 1.75</span>
			<p class="dl-body">
				dartlab 은 한국 DART 공시를 기반으로 회사 한 페이지를 깊이 있게 보여주는 정적 분석 도구다.
				서버 없이, 무료로, 누구나 fork 가능하게. 숫자는 원본 그대로, 해석은 6막 인과 구조로,
				디자인은 1970년대 금융 저널의 편집 톤을 OLED 패널 위에서 다시 읽는 식으로.
			</p>
		</div>
		<div>
			<span class="dl-eyebrow">Figure · 큰 숫자 + tabular-nums</span>
			<div class="dl-figure">2,904,282</div>
		</div>
	</div>
</Section>

<footer class="lab-foot">
	<span class="dl-eyebrow">END · /lab · 다음 단계: Sankey · LayerChart 통합 · DuckDB-WASM 검증</span>
</footer>

<style>
	/* ── nav ── */
	.lab-nav {
		position: sticky;
		top: 0;
		z-index: 30;
		border-bottom: 1px solid var(--dl-line);
		background: rgba(15, 15, 16, 0.8);
		backdrop-filter: blur(14px);
		-webkit-backdrop-filter: blur(14px);
	}
	.nav-inner {
		max-width: var(--dl-w-max);
		margin-inline: auto;
		padding: var(--dl-s-3) var(--dl-s-6);
		display: flex;
		justify-content: space-between;
		align-items: center;
	}
	.brand {
		display: inline-flex;
		align-items: baseline;
		gap: var(--dl-s-2);
		text-decoration: none;
		color: var(--dl-ink);
	}
	.brand-mark {
		font-family: var(--dl-font-head);
		font-weight: 700;
		font-size: 18px;
		letter-spacing: -0.02em;
	}
	.brand-slash { color: var(--dl-ink-faint); font-weight: 300; }
	.brand-ctx {
		font-family: var(--dl-font-mono);
		font-size: 11px;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		color: var(--dl-orange);
	}
	.nav-links { display: flex; gap: var(--dl-s-2); }
	.nav-link {
		font-family: var(--dl-font-mono);
		font-size: 11px;
		color: var(--dl-ink-mute);
		text-decoration: none;
		padding: 4px 8px;
		border-radius: var(--dl-r-sm);
		transition: background var(--dl-dur-hover) var(--dl-ease), color var(--dl-dur-hover) var(--dl-ease);
	}
	.nav-link:hover { background: var(--dl-bg-overlay); color: var(--dl-orange); }

	/* ── hero ── */
	.hero {
		padding: var(--dl-s-9) var(--dl-s-6) var(--dl-s-8);
		border-bottom: 1px solid var(--dl-line);
	}
	.hero-inner {
		max-width: var(--dl-w-max);
		margin-inline: auto;
	}
	.hero-h1 {
		font-family: var(--dl-font-head);
		font-size: clamp(48px, 7vw, 96px);
		font-weight: 700;
		line-height: 1.02;
		letter-spacing: -0.035em;
		color: var(--dl-ink-print);
		margin: var(--dl-s-4) 0 var(--dl-s-5);
		text-wrap: balance;
	}
	.hero-h1-em {
		background: var(--dl-grad-heat);
		-webkit-background-clip: text;
		background-clip: text;
		color: transparent;
	}
	.hero-sub {
		font-size: 17px;
		color: var(--dl-ink-mute);
		line-height: 1.7;
		max-width: var(--dl-w-article);
		margin: 0;
	}

	/* ── company hero (section 01) ── */
	.company-hero {
		display: grid;
		grid-template-columns: 1.4fr 1fr;
		gap: var(--dl-s-6);
		align-items: start;
	}
	.ch-meta {
		display: flex;
		align-items: center;
		gap: var(--dl-s-2);
		font-size: 12px;
		color: var(--dl-ink-mute);
	}
	.ch-dot {
		width: 3px; height: 3px; border-radius: 50%;
		background: var(--dl-ink-faint);
	}
	.ch-name { margin: var(--dl-s-3) 0 var(--dl-s-4); }
	.ch-tags { display: flex; gap: var(--dl-s-2); flex-wrap: wrap; }

	.verdict {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-3);
	}
	.v-call {
		font-size: 22px;
		font-weight: 700;
		letter-spacing: -0.02em;
		color: var(--dl-warn);
	}
	.v-conf { display: flex; align-items: baseline; gap: var(--dl-s-2); }
	.v-line { font-size: 14px; color: var(--dl-ink); line-height: 1.6; margin: 0; }

	/* ── KPI grid ── */
	.kpi-grid {
		display: grid;
		grid-template-columns: repeat(4, 1fr);
		gap: var(--dl-s-3);
	}
	.kpi-row {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: var(--dl-s-2);
		margin-top: var(--dl-s-2);
	}
	.kpi-note {
		font-size: 12px;
		color: var(--dl-ink-dim);
		margin-top: var(--dl-s-3);
	}

	/* ── 숫자 표 ── */
	.num-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 14px;
	}
	.num-table th {
		text-align: left;
		font-family: var(--dl-font-mono);
		font-size: 10px;
		letter-spacing: 0.14em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
		padding: var(--dl-s-3) var(--dl-s-3);
		border-bottom: 1px solid var(--dl-line);
	}
	.num-table td {
		padding: var(--dl-s-3);
		border-bottom: 1px solid var(--dl-line);
		color: var(--dl-ink);
	}
	.num-table th:first-child, .num-table td:first-child { padding-left: 0; }

	/* ── 컬러 칩 ── */
	.swatch-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
		gap: var(--dl-s-3);
	}
	.sw {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-1);
		padding: var(--dl-s-4);
		border-radius: var(--dl-r-md);
		border: 1px solid var(--dl-line);
		font-size: 13px;
		min-height: 72px;
		justify-content: space-between;
	}
	.sw code { font-size: 11px; color: var(--dl-ink-mute); }
	.sw.red { background: var(--dl-red); color: white; }
	.sw.orange { background: var(--dl-orange); color: black; }
	.sw.up { background: var(--dl-up); color: white; }
	.sw.down { background: var(--dl-down); color: white; }
	.sw.good { background: var(--dl-good); color: black; }
	.sw.warn { background: var(--dl-warn); color: black; }
	.sw.bad { background: var(--dl-bad); color: white; }
	.sw.info { background: var(--dl-info); color: black; }
	.sw.red code, .sw.up code, .sw.down code, .sw.bad code { color: rgba(255,255,255,0.85); }
	.sw.orange code, .sw.good code, .sw.warn code, .sw.info code { color: rgba(0,0,0,0.7); }

	/* ── type stack ── */
	.type-stack {
		display: flex;
		flex-direction: column;
		gap: var(--dl-s-6);
	}
	.type-stack > div { padding-bottom: var(--dl-s-4); border-bottom: 1px solid var(--dl-line); }
	.type-stack > div:last-child { border-bottom: none; }

	/* ── foot ── */
	.lab-foot {
		padding: var(--dl-s-6) var(--dl-s-6) var(--dl-s-7);
		text-align: center;
		border-top: 1px solid var(--dl-line);
	}

	/* ── responsive ── */
	@media (max-width: 900px) {
		.company-hero { grid-template-columns: 1fr; }
		.kpi-grid { grid-template-columns: repeat(2, 1fr); }
	}
	@media (max-width: 560px) {
		.kpi-grid { grid-template-columns: 1fr; }
		.hero { padding: var(--dl-s-7) var(--dl-s-4) var(--dl-s-6); }
	}
</style>
