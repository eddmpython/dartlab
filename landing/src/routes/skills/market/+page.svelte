<script lang="ts">
	import { base } from '$app/paths';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { brand } from '$lib/brand';
	import { buildAbsoluteUrl, buildBreadcrumbJsonLd, buildWebsiteJsonLd } from '$lib/seo';
	import {
		displayTier,
		marketSkillMatches,
		marketTierOrder,
		marketTierTitle,
		type MarketIndex,
		type MarketSkill
	} from '$lib/skills/marketCatalog';
	import { ArrowRight, ExternalLink, Search, ShieldAlert } from 'lucide-svelte';

	let { data } = $props<{ data: { market: MarketIndex } }>();

	const market = $derived(data.market);
	const skills = $derived((market.skills ?? []) as MarketSkill[]);
	let selectedTier = $state('all');
	let query = $state('');

	const visibleSkills = $derived(
		skills.filter((skill) => {
			const tierOk = selectedTier === 'all' || displayTier(skill) === selectedTier;
			return tierOk && marketSkillMatches(skill, query);
		})
	);
	const acceptedCount = $derived(skills.filter((skill) => skill.itemPath).length);
	const draftCount = $derived(skills.length - acceptedCount);

	function countTier(tier: string): number {
		return skills.filter((skill) => displayTier(skill) === tier).length;
	}

	const pageTitle = 'DartLab Skill Market · 커뮤니티 분석 질문';
	const pageDesc =
		'GitHub Discussions 에 공유된 분석 질문을 DartLab Forge 가 커뮤니티 스킬 후보로 구조화한 정적 Skill Market.';
	const pageUrl = buildAbsoluteUrl('skills/market');
	const jsonLd = JSON.stringify([
		buildWebsiteJsonLd(),
		buildBreadcrumbJsonLd([
			{ name: 'DartLab', url: brand.url },
			{ name: 'Skill Catalog', url: buildAbsoluteUrl('skills') },
			{ name: 'Skill Market', url: pageUrl }
		])
	]);
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<Header context="skills" />

<main class="market-page">
	<nav class="breadcrumb" aria-label="breadcrumb">
		<a href="{base}/skills">Skill Catalog</a>
		<span>/</span>
		<span>Skill Market</span>
	</nav>

	<section class="hero">
		<p class="kicker">Community Skill Market</p>
		<h1>분석 질문을 공유 자산으로 바꾼다</h1>
		<p class="lead">
			Skill Market 은 GitHub Discussions 의 자연어 제안을 DartLab Forge 가 구조화한
			커뮤니티 지식층이다. 공식 Skill OS 와 분리되며, trust tier 와 원문 출처를 함께 본다.
		</p>
		<div class="notice">
			<ShieldAlert size={16} />
			<span>커뮤니티 스킬은 외부 작성물이다. curated 이전에는 공식 Skill OS 와 같은 신뢰 계층으로 취급하지 않는다.</span>
		</div>
		<div class="actions">
			<a class="primary-link" href="https://github.com/eddmpython/dartlab/discussions" target="_blank" rel="noopener noreferrer">
				분석 질문 공유 <ExternalLink size={14} />
			</a>
			<a class="secondary-link" href="{base}/skills/operation.skillMarket">운영 규칙 보기</a>
		</div>
	</section>

	<section class="toolbar" aria-label="Skill Market filter">
		<div class="search">
			<Search size={14} />
			<input bind:value={query} placeholder="market skill 검색..." />
		</div>
		<div class="tabs">
			<button class:active={selectedTier === 'all'} onclick={() => (selectedTier = 'all')} type="button">
				All <span>{skills.length}</span>
			</button>
			{#each marketTierOrder as tier}
				<button class:active={selectedTier === tier} onclick={() => (selectedTier = tier)} type="button">
					{marketTierTitle[tier]} <span>{countTier(tier)}</span>
				</button>
			{/each}
		</div>
	</section>

	<section class="meta-strip" aria-label="Market metadata">
		<div>
			<span>Generated</span>
			<strong>{market.meta?.generatedAt ?? 'not yet'}</strong>
		</div>
		<div>
			<span>Source</span>
			<strong>{market.meta?.source ?? 'github-discussions'}</strong>
		</div>
		<div>
			<span>Count</span>
			<strong>{market.meta?.skillCount ?? skills.length}</strong>
		</div>
		<div>
			<span>Accepted</span>
			<strong>{acceptedCount}</strong>
		</div>
		<div>
			<span>Draft</span>
			<strong>{draftCount}</strong>
		</div>
	</section>

	{#if visibleSkills.length === 0}
		<section class="empty">
			<h2>아직 노출할 커뮤니티 스킬이 없다</h2>
			<p>{market.meta?.emptyReason ?? 'Skill Market 카테고리에 Discussion 이 생기면 Forge 가 이 페이지를 채운다.'}</p>
		</section>
	{:else}
		<section class="grid" aria-label="Market skills">
			{#each visibleSkills as skill}
				<a class="skill-card" class:draft={!skill.itemPath} href="{base}/skills/market/{skill.id}">
					<div class="card-head">
						<span class="tier">{displayTier(skill)}</span>
						<span class="author">{skill.itemPath ? 'accepted snapshot' : 'discussion draft'} · @{skill.author ?? 'unknown'}</span>
					</div>
					<h2>{skill.title}</h2>
					<p>{skill.summary ?? skill.intent}</p>
					<div class="chips">
						{#each (skill.mappedBuiltinSkills ?? []).slice(0, 3) as mapped}
							<span>{mapped}</span>
						{/each}
					</div>
					<div class="card-foot">
						<span>{skill.itemPath ? 'Skill Market snapshot' : '아직 실행 후보 아님'}</span>
						<ArrowRight size={14} />
					</div>
				</a>
			{/each}
		</section>
	{/if}
</main>

<Footer />

<style>
	.market-page {
		min-height: 100vh;
		max-width: 1180px;
		margin: 0 auto;
		padding: 6.5rem 1.25rem 4rem;
		color: var(--dl-ink);
	}

	.breadcrumb {
		display: flex;
		gap: 0.4rem;
		margin-bottom: 1.25rem;
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.78rem;
	}

	.breadcrumb a {
		color: var(--dl-ink-mute);
		text-decoration: none;
	}

	.hero {
		margin-bottom: 1.5rem;
		padding-bottom: 1.25rem;
		border-bottom: 1px solid var(--dl-line);
	}

	.kicker {
		margin: 0 0 0.5rem;
		color: var(--dl-orange);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
	}

	h1 {
		margin: 0 0 0.8rem;
		font-size: clamp(2rem, 4vw, 3.1rem);
		line-height: 1.1;
		color: var(--dl-ink-print);
	}

	.lead {
		max-width: 62rem;
		margin: 0 0 1rem;
		color: var(--dl-ink-mute);
		line-height: 1.7;
	}

	.notice {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		max-width: 62rem;
		margin: 0 0 1rem;
		padding: 0.7rem 0.85rem;
		border: 1px solid rgba(251, 146, 60, 0.35);
		border-radius: 6px;
		background: rgba(251, 146, 60, 0.08);
		color: var(--dl-ink-mute);
		font-size: 0.85rem;
	}

	.actions {
		display: flex;
		gap: 0.6rem;
		flex-wrap: wrap;
	}

	.primary-link,
	.secondary-link {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.55rem 0.8rem;
		border-radius: 6px;
		text-decoration: none;
		font-size: 0.86rem;
	}

	.primary-link {
		background: var(--dl-orange);
		color: #111827;
		font-weight: 700;
	}

	.secondary-link {
		border: 1px solid var(--dl-line-strong);
		color: var(--dl-ink-mute);
	}

	.toolbar {
		display: grid;
		grid-template-columns: minmax(240px, 0.65fr) minmax(0, 1fr);
		gap: 0.85rem;
		align-items: center;
		margin-bottom: 1rem;
	}

	.search {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		padding: 0.5rem 0.7rem;
		border: 1px solid var(--dl-line);
		border-radius: 6px;
		background: var(--dl-bg-raised);
	}

	.search input {
		width: 100%;
		border: 0;
		outline: 0;
		background: transparent;
		color: var(--dl-ink);
		font: inherit;
	}

	.tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 0.45rem;
		justify-content: flex-end;
	}

	.tabs button {
		padding: 0.45rem 0.65rem;
		border: 1px solid var(--dl-line);
		border-radius: 999px;
		background: var(--dl-bg-raised);
		color: var(--dl-ink-mute);
		cursor: pointer;
	}

	.tabs button.active {
		border-color: var(--dl-orange);
		color: var(--dl-orange);
	}

	.tabs span {
		margin-left: 0.25rem;
		color: var(--dl-ink-dim);
	}

	.meta-strip {
		display: grid;
		grid-template-columns: repeat(5, 1fr);
		gap: 0.75rem;
		margin-bottom: 1.1rem;
	}

	.meta-strip div {
		padding: 0.75rem;
		border: 1px solid var(--dl-line);
		border-radius: 6px;
		background: var(--dl-bg-raised);
	}

	.meta-strip span {
		display: block;
		margin-bottom: 0.25rem;
		color: var(--dl-ink-dim);
		font-size: 0.72rem;
		text-transform: uppercase;
	}

	.meta-strip strong {
		color: var(--dl-ink-print);
		font-size: 0.86rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 0.85rem;
	}

	.skill-card {
		display: flex;
		min-height: 13.5rem;
		flex-direction: column;
		padding: 1rem;
		border: 1px solid var(--dl-line);
		border-radius: 8px;
		background: var(--dl-bg-raised);
		color: inherit;
		text-decoration: none;
	}

	.skill-card.draft {
		border-style: dashed;
		background: rgba(255, 255, 255, 0.025);
	}

	.card-head,
	.card-foot {
		display: flex;
		justify-content: space-between;
		gap: 0.65rem;
		align-items: center;
	}

	.tier {
		color: var(--dl-orange);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
	}

	.author,
	.card-foot {
		color: var(--dl-ink-dim);
		font-size: 0.76rem;
	}

	.skill-card h2 {
		margin: 0.75rem 0 0.45rem;
		color: var(--dl-ink-print);
		font-size: 1rem;
	}

	.skill-card p {
		margin: 0;
		color: var(--dl-ink-mute);
		font-size: 0.86rem;
		line-height: 1.55;
	}

	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
		margin: auto 0 0.85rem;
		padding-top: 0.85rem;
	}

	.chips span {
		padding: 0.18rem 0.45rem;
		border: 1px solid var(--dl-line);
		border-radius: 5px;
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.66rem;
	}

	.empty {
		padding: 2rem;
		border: 1px solid var(--dl-line);
		border-radius: 8px;
		background: var(--dl-bg-raised);
		text-align: center;
	}

	.empty h2 {
		margin: 0 0 0.5rem;
		color: var(--dl-ink-print);
	}

	.empty p {
		margin: 0;
		color: var(--dl-ink-mute);
	}

	@media (max-width: 820px) {
		.toolbar,
		.meta-strip {
			grid-template-columns: 1fr;
		}

		.tabs {
			justify-content: flex-start;
		}
	}
</style>
