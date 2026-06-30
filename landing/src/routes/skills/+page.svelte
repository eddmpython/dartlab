<script lang="ts">
	import { base } from '$app/paths';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import CategorySidebar from '$lib/components/skills/CategorySidebar.svelte';
	import SkillCardGrid from '$lib/components/skills/SkillCardGrid.svelte';
	import { skills } from '$lib/skills/catalog';
	import { buildAbsoluteUrl, buildBreadcrumbJsonLd, buildWebsiteJsonLd } from '$lib/seo';
	import { brand } from '$lib/brand';
	import { Search, Sparkles, ArrowRight } from 'lucide-svelte';

	interface RuntimeEntry { status?: string; }
	interface SkillDoc {
		id: string;
		title: string;
		category: string;
		categoryTitle?: string;
		status: string;
		purpose: string;
		runtimeCompatibility?: Record<string, RuntimeEntry>;
	}

	// 진입 skill · 처음 방문자가 어디부터 봐야 하는지 명시.
	const entryIds = ['start.dartlabSkillOs', 'start.installUv', 'start.quickStart'];
	const entrySkills = entryIds
		.map((id) => skills.find((s) => s.id === id))
		.filter((s): s is SkillDoc => s !== undefined);

	let selectedCategory = $state('all');
	let selectedSubGroup = $state<string | null>(null);
	let query = $state('');

	function openGlobalSearch() {
		window.dispatchEvent(new Event('open-command-palette'));
	}

	function selectSkillFilter(category: string, subGroup: string | null) {
		selectedCategory = category;
		selectedSubGroup = subGroup;
	}

	const pageTitle = 'DartLab Skills · 작업 체계 카탈로그';
	const pageDesc =
		'DartLab 분석 절차 · 엔진 능력 · 운영 규칙 · 확장 절차를 카테고리로 골라 입력 · 출력 · 검증 · 실행 순서를 한 화면에서 읽는 skill catalog. 사람과 LLM 이 같은 표면을 본다.';
	const pageUrl = buildAbsoluteUrl('skills');
	const jsonLd = JSON.stringify([
		buildWebsiteJsonLd(),
		buildBreadcrumbJsonLd([
			{ name: 'DartLab', url: brand.url },
			{ name: 'Skill Catalog', url: pageUrl }
		])
	]);
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="website" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<Header context="skills" />

<main class="skill-page">
	<section class="hero">
		<p class="kicker">Skills</p>
		<h1>DartLab Skills 작업 체계</h1>
		<p class="lead">
			무엇을 분석하거나 운영하려는지 먼저 고른다. 각 skill 은 입력 · 출력 · 검증 기준 · 실행 순서를
			한 화면에 묶는다. 사람과 LLM 이 같은 표면을 본다 · 외부 API 문서를 직접 뒤지지 않는다.
		</p>
		<p class="lead-graph">
			<a href="{base}/skills/graph" class="graph-link">
				<Sparkles size={14} />
				<span>그래프로 보기 · 257 노드 클릭 탐색</span>
				<ArrowRight size={14} />
			</a>
		</p>
		<p class="lead-market">
			<a href="{base}/skills/market" class="market-link">
				<Sparkles size={14} />
				<span>Community Skill Market · 분석 질문을 공유 자산으로 보기</span>
				<ArrowRight size={14} />
			</a>
		</p>

		<div class="search-row">
			<button class="cmdk-btn" onclick={openGlobalSearch} type="button">
				<Search size={14} />
				<span>전역 검색</span>
				<kbd>⌘K</kbd>
			</button>
			<input
				type="text"
				bind:value={query}
				placeholder="현재 카테고리 안에서 검색..."
				class="local-search"
			/>
		</div>
	</section>

	{#if entrySkills.length > 0}
		<section class="entry-block" aria-label="첫 진입">
			<header class="entry-head">
				<Sparkles size={14} class="entry-icon" />
				<h2>처음 왔다면 · 진입 순서</h2>
			</header>
			<ol class="entry-grid">
				{#each entrySkills as skill, i}
					<li>
						<a href="{base}/skills/{skill.id}" class="entry-card">
							<span class="step">{i + 1}</span>
							<div class="entry-body">
								<h3>{skill.title}</h3>
								<p>{skill.purpose}</p>
								<div class="entry-foot">
									<code>{skill.id}</code>
									<ArrowRight size={12} class="arrow" />
								</div>
							</div>
						</a>
					</li>
				{/each}
			</ol>
		</section>
	{/if}

	<section class="catalog" aria-label="전체 카탈로그">
		<header class="catalog-head">
			<h2>전체 카탈로그</h2>
			<p class="catalog-sub">
				5 카테고리 · 시작 (Start) · 실행 환경 (Runtime) · 운영 규칙 (Operation) · 엔진 (Engines) · 레시피 (Recipes)
			</p>
		</header>

		<div class="layout">
			<CategorySidebar bind:selectedCategory bind:selectedSubGroup onSelect={selectSkillFilter} />
			<SkillCardGrid {skills} {selectedCategory} {selectedSubGroup} {query} />
		</div>
	</section>
</main>

<Footer />

<style>
	.skill-page {
		min-height: 100vh;
		max-width: none;
		margin: 0 auto;
		padding: 6.5rem 1.25rem 4rem;
		background:
			radial-gradient(circle at 18% 0%, rgba(234, 70, 71, 0.1), transparent 30rem),
			radial-gradient(circle at 82% 12%, rgba(251, 146, 60, 0.08), transparent 26rem),
			var(--dl-bg-base);
		color: var(--dl-ink);
	}

	.hero {
		max-width: var(--dl-w-wide);
		margin: 0 auto 2.5rem;
	}

	.kicker {
		margin: 0 0 0.5rem;
		color: var(--dl-accent);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	h1 {
		margin: 0 0 0.85rem;
		font-family: var(--dl-font-head);
		font-size: clamp(2rem, 4vw, 3.2rem);
		line-height: 1.1;
		color: var(--dl-ink-print);
		letter-spacing: -0.01em;
	}

	.lead {
		max-width: 60rem;
		margin: 0 0 1.5rem;
		color: var(--dl-ink-mute);
		font-size: 1rem;
		line-height: 1.7;
	}

	.search-row {
		display: flex;
		align-items: center;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.lead-market,
	.lead-graph {
		margin: 0 0 0.8rem;
	}

	.market-link,
	.graph-link {
		display: inline-flex;
		align-items: center;
		gap: 0.4rem;
		color: var(--dl-accent);
		font-size: 0.86rem;
		text-decoration: none;
	}

	.market-link:hover,
	.graph-link:hover {
		text-decoration: underline;
		text-underline-offset: 3px;
	}

	.cmdk-btn {
		display: inline-flex;
		align-items: center;
		gap: 0.45rem;
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--dl-line-strong);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
		font-size: 0.85rem;
		cursor: pointer;
		transition: border-color var(--dl-dur-hover), color var(--dl-dur-hover);
	}

	.cmdk-btn:hover {
		border-color: var(--dl-accent);
		color: var(--dl-ink);
	}

	.cmdk-btn kbd {
		padding: 0.05rem 0.35rem;
		border: 1px solid var(--dl-line-strong);
		border-radius: 3px;
		background: var(--dl-bg-modal);
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.7rem;
	}

	.local-search {
		flex: 1;
		min-width: 220px;
		padding: 0.55rem 0.85rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
		color: var(--dl-ink);
		font-size: 0.88rem;
		font-family: var(--dl-font-ui);
	}

	.local-search:focus {
		outline: none;
		border-color: var(--dl-accent);
	}

	.local-search::placeholder {
		color: var(--dl-ink-dim);
	}

	.entry-block {
		max-width: var(--dl-w-wide);
		margin: 0 auto 2.5rem;
		padding: 1.4rem 1.5rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-lg);
		background: linear-gradient(
			135deg,
			rgba(251, 146, 60, 0.06),
			rgba(15, 18, 25, 0.6)
		);
	}

	.entry-head {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.entry-head h2 {
		margin: 0;
		font-size: 1rem;
		color: var(--dl-ink-print);
		font-weight: 600;
	}

	.entry-block :global(.entry-icon) {
		color: var(--dl-accent);
	}

	.entry-grid {
		list-style: none;
		margin: 0;
		padding: 0;
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
		gap: 0.75rem;
	}

	.entry-card {
		display: flex;
		gap: 0.75rem;
		align-items: flex-start;
		padding: 0.95rem 1rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: var(--dl-bg-raised);
		text-decoration: none;
		color: inherit;
		transition: border-color var(--dl-dur-hover), background var(--dl-dur-hover),
			transform var(--dl-dur-hover);
	}

	.entry-card:hover {
		border-color: var(--dl-accent);
		background: var(--dl-bg-overlay);
		transform: translateY(-1px);
	}

	.step {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border-radius: 50%;
		background: var(--dl-orange-soft);
		color: var(--dl-accent);
		font-family: var(--dl-font-mono);
		font-size: 0.75rem;
		font-weight: 700;
	}

	.entry-body {
		flex: 1;
		min-width: 0;
	}

	.entry-body h3 {
		margin: 0 0 0.3rem;
		font-size: 0.9rem;
		color: var(--dl-ink-print);
		font-weight: 600;
	}

	.entry-body p {
		margin: 0 0 0.5rem;
		font-size: 0.78rem;
		line-height: 1.5;
		color: var(--dl-ink-mute);
		display: -webkit-box;
		line-clamp: 2;
		-webkit-line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.entry-foot {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 0.4rem;
	}

	.entry-foot code {
		font-family: var(--dl-font-mono);
		font-size: 0.66rem;
		color: var(--dl-ink-dim);
	}

	.entry-card :global(.arrow) {
		color: var(--dl-ink-faint);
		transition: color var(--dl-dur-hover), transform var(--dl-dur-hover);
	}

	.entry-card:hover :global(.arrow) {
		color: var(--dl-accent);
		transform: translateX(2px);
	}

	.catalog {
		max-width: var(--dl-w-wide);
		margin: 0 auto;
	}

	.catalog-head {
		margin-bottom: 1.25rem;
		padding-bottom: 0.85rem;
		border-bottom: 1px solid var(--dl-line);
	}

	.catalog-head h2 {
		margin: 0 0 0.3rem;
		font-size: 1.15rem;
		color: var(--dl-ink-print);
		font-weight: 600;
	}

	.catalog-sub {
		margin: 0;
		font-size: 0.82rem;
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
	}

	.layout {
		display: grid;
		grid-template-columns: minmax(220px, 260px) minmax(0, 1fr);
		gap: 1.5rem;
		align-items: start;
	}

	@media (max-width: 920px) {
		.layout {
			grid-template-columns: 1fr;
		}
	}
</style>
