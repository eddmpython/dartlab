<script lang="ts">
	import { base } from '$app/paths';
	import { onMount, tick } from 'svelte';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { brand } from '$lib/brand';
	import { buildAbsoluteUrl, buildBreadcrumbJsonLd, buildWebsiteJsonLd } from '$lib/seo';
	import { findRelatedSkills, isCatalogSkillId } from '$lib/skills/catalog';
	import { ArrowLeft, ExternalLink } from 'lucide-svelte';
	import ProcedureStepper from '$lib/components/skills/sections/ProcedureStepper.svelte';
	import EvidenceChecklist from '$lib/components/skills/sections/EvidenceChecklist.svelte';
	import DoNotDo from '$lib/components/skills/sections/DoNotDo.svelte';
	import UsageExamples from '$lib/components/skills/sections/UsageExamples.svelte';
	import RuntimeMatrix from '$lib/components/skills/sections/RuntimeMatrix.svelte';
	import RecipeSteps from '$lib/components/skills/sections/RecipeSteps.svelte';

	let { data } = $props();

	const Component = $derived(data.component);
	const meta = $derived(data.meta);
	const id = $derived(data.id);
	const sourcePath = $derived(data.sourcePath);

	const related = $derived(findRelatedSkills(id, 6));

	interface TocItem { id: string; text: string; level: number; }
	let tocItems: TocItem[] = $state([]);
	let activeId = $state('');
	let articleEl: HTMLElement | undefined = $state();

	function extractToc() {
		if (!articleEl) return;
		const headings = articleEl.querySelectorAll('h1, h2, h3');
		const items: TocItem[] = [];
		headings.forEach((h) => {
			if (!h.id) {
				h.id = (h.textContent ?? '')
					.trim()
					.toLowerCase()
					.replace(/[^a-z0-9가-힣]+/g, '-')
					.replace(/(^-|-$)/g, '');
			}
			items.push({
				id: h.id,
				text: (h.textContent ?? '').trim(),
				level: h.tagName === 'H1' ? 1 : h.tagName === 'H2' ? 2 : 3
			});
		});
		tocItems = items;
	}

	function observeHeadings() {
		if (!articleEl) return;
		const headings = articleEl.querySelectorAll('h1, h2, h3');
		if (headings.length === 0) return;
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					if (entry.isIntersecting) {
						activeId = entry.target.id;
						break;
					}
				}
			},
			{ rootMargin: '-80px 0px -70% 0px', threshold: 0 }
		);
		headings.forEach((h) => observer.observe(h));
		return () => observer.disconnect();
	}

	onMount(() => {
		let cleanup: (() => void) | undefined;
		let retryTimer: ReturnType<typeof setTimeout> | undefined;
		const refreshToc = () => {
			cleanup?.();
			extractToc();
			cleanup = observeHeadings();
		};
		tick().then(() => {
			refreshToc();
			retryTimer = setTimeout(refreshToc, 250);
		});
		return () => {
			if (retryTimer) clearTimeout(retryTimer);
			cleanup?.();
		};
	});

	const pageTitle = $derived(`${meta.title} · DartLab Skills`);
	const pageDesc = $derived(meta.purpose);
	const pageUrl = $derived(buildAbsoluteUrl(`skills/${id}`));

	const jsonLd = $derived(
		JSON.stringify([
			buildWebsiteJsonLd(),
			buildBreadcrumbJsonLd([
				{ name: 'DartLab', url: brand.url },
				{ name: 'Skill Catalog', url: buildAbsoluteUrl('skills') },
				{ name: meta.title, url: pageUrl }
			])
		])
	);

	const githubUrl = $derived.by(() => {
		if (!sourcePath) return '';
		const idx = sourcePath.indexOf('src/dartlab/skills/');
		const tail = idx >= 0 ? sourcePath.slice(idx) : sourcePath.replace(/\\/g, '/');
		return `https://github.com/eddmpython/dartlab/blob/master/${tail}`;
	});

	function refLink(value: string): { href: string | null; label: string } {
		if (isCatalogSkillId(value)) {
			return { href: `${base}/skills/${value}`, label: value };
		}
		return { href: null, label: value };
	}

	function scrollToSection(sectionId: string) {
		const target = document.getElementById(sectionId);
		if (!target) return;
		target.scrollIntoView({ behavior: 'smooth', block: 'start' });
		history.replaceState(null, '', `#${sectionId}`);
		activeId = sectionId;
	}
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="article" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<Header context="skills" />

<main class="skill-detail-page">
	<nav class="breadcrumb" aria-label="breadcrumb">
		<a href="{base}/skills"><ArrowLeft size={14} /> Skill Catalog</a>
		<span>/</span>
		<span>{meta.categoryTitle ?? meta.category}</span>
	</nav>

	<header class="skill-head">
		<div class="identity-row">
			<code>{id}</code>
			<span class="kicker">{meta.categoryTitle ?? meta.category}</span>
			{#if meta.kind === 'recipe'}
				<span class="recipe-badge">Recipe</span>
			{/if}
			<span class="status">{meta.status}</span>
		</div>
		<h1>{meta.title}</h1>
		<p class="purpose">{meta.purpose}</p>
		<div class="id-row">
			{#if githubUrl}
				<a class="source-link" href={githubUrl} target="_blank" rel="noopener noreferrer">
					GitHub 원본 <ExternalLink size={12} />
				</a>
			{/if}
		</div>
	</header>

	<div class="layout">
		<aside class="meta-card" aria-label="Skill metadata">
			{#if tocItems.length > 0}
				<section class="toc-section">
					<h3>이 페이지</h3>
					<ul class="toc">
						{#each tocItems as item}
							<li class="toc-l{item.level}">
								<button
									type="button"
									class:active={activeId === item.id}
									onclick={() => scrollToSection(item.id)}
								>
									{item.text}
								</button>
							</li>
						{/each}
					</ul>
				</section>
			{/if}

			{#if meta.whenToUse?.length}
				<section>
					<h3>언제 쓰나</h3>
					<ul>
						{#each meta.whenToUse.slice(0, 8) as item}<li>{item}</li>{/each}
					</ul>
				</section>
			{/if}

			{#if meta.requiredEvidence?.length}
				<section>
					<h3>필요한 근거</h3>
					<div class="chip-row">
						{#each meta.requiredEvidence as item}<span>{item}</span>{/each}
					</div>
				</section>
			{/if}

			{#if (meta.apiRefs?.length ?? 0) + (meta.toolRefs?.length ?? 0) > 0}
				<section>
					<h3>API · Tool</h3>
					<div class="chip-row">
						{#each [...(meta.apiRefs ?? []), ...(meta.toolRefs ?? [])] as item}
							{@const link = refLink(item)}
							{#if link.href}
								<a href={link.href} class="ref-chip">{link.label}</a>
							{:else}
								<span>{link.label}</span>
							{/if}
						{/each}
					</div>
				</section>
			{/if}

			{#if meta.knowledgeRefs?.length}
				<section>
					<h3>관련 skill</h3>
					<div class="chip-row">
						{#each meta.knowledgeRefs as item}
							{@const link = refLink(item)}
							{#if link.href}
								<a href={link.href} class="ref-chip">{link.label}</a>
							{:else}
								<span>{link.label}</span>
							{/if}
						{/each}
					</div>
				</section>
			{/if}

			{#if meta.sourceRefs?.length}
				<section>
					<h3>원본 출처</h3>
					<div class="chip-row">
						{#each meta.sourceRefs as item}<span>{item}</span>{/each}
					</div>
				</section>
			{/if}

			{#if related.length}
				<section>
					<h3>같은 카테고리</h3>
					<ul class="related-list">
						{#each related as r}
							<li><a href="{base}/skills/{r.id}">{r.title}</a></li>
						{/each}
					</ul>
				</section>
			{/if}
		</aside>

		<article class="body" aria-label="Skill body" bind:this={articleEl}>
			<section class="overview-card" aria-label="Skill summary">
				<p class="overview-label">이 스킬</p>
				<h2>{meta.title}</h2>
				<p>{meta.purpose}</p>
				<div class="overview-meta">
					<span>{meta.categoryTitle ?? meta.category}</span>
					<span>{meta.status}</span>
					<code>{id}</code>
				</div>
			</section>
			<RecipeSteps
				recipeSteps={meta.recipeSteps ?? []}
				linkedSkills={meta.linkedSkills ?? []}
			/>
			<ProcedureStepper steps={meta.procedure ?? []} />
			<UsageExamples examples={meta.examples ?? []} />
			<EvidenceChecklist
				items={meta.expectedOutputs ?? []}
				title="기대 결과"
				kicker="출력"
			/>

			<div class="prose">
				{#if Component}
					<Component />
				{/if}
			</div>

			<RuntimeMatrix runtimeCompatibility={meta.runtimeCompatibility ?? {}} />
			<DoNotDo failureModes={meta.failureModes ?? []} forbidden={meta.forbidden ?? []} />
		</article>
	</div>
</main>

<Footer />

<style>
	.skill-detail-page {
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

	.breadcrumb {
		max-width: 1240px;
		margin-left: auto;
		margin-right: auto;
		display: flex;
		align-items: center;
		gap: 0.4rem;
		margin-bottom: 1.25rem;
		color: var(--dl-ink-dim);
		font-size: 0.8rem;
		font-family: var(--dl-font-mono);
	}

	.breadcrumb a {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		color: var(--dl-ink-mute);
		text-decoration: none;
	}

	.breadcrumb a:hover {
		color: var(--dl-orange);
	}

	.skill-head {
		max-width: 1240px;
		margin-left: auto;
		margin-right: auto;
		margin-bottom: 1.75rem;
		padding-bottom: 1.25rem;
		border-bottom: 1px solid var(--dl-line);
	}

	.identity-row {
		display: flex;
		align-items: center;
		gap: 0.55rem;
		margin-bottom: 0.5rem;
		flex-wrap: wrap;
	}

	.kicker {
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.08em;
		color: var(--dl-orange);
	}

	.status {
		padding: 0.1rem 0.45rem;
		border-radius: 4px;
		background: var(--dl-orange-soft);
		color: var(--dl-orange);
		font-size: 0.68rem;
		font-family: var(--dl-font-mono);
	}

	.recipe-badge {
		padding: 0.1rem 0.5rem;
		border-radius: 999px;
		background: var(--dl-grad-heat);
		color: var(--dl-ink-print);
		font-size: 0.66rem;
		font-weight: 700;
		font-family: var(--dl-font-mono);
		letter-spacing: 0.04em;
	}

	.skill-head h1 {
		margin: 0 0 0.6rem;
		font-family: var(--dl-font-head);
		font-size: clamp(1.75rem, 3.4vw, 2.6rem);
		line-height: 1.15;
		color: var(--dl-ink-print);
	}

	.purpose {
		margin: 0 0 0.7rem;
		max-width: 60rem;
		color: var(--dl-ink-mute);
		font-size: 1rem;
		line-height: 1.7;
	}

	.id-row {
		display: flex;
		align-items: center;
		gap: 0.85rem;
		flex-wrap: wrap;
	}

	.identity-row code {
		padding: 0.18rem 0.5rem;
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
		font-family: var(--dl-font-mono);
		font-size: 0.78rem;
	}

	.source-link {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		color: var(--dl-orange);
		font-size: 0.78rem;
		text-decoration: none;
	}

	.source-link:hover {
		text-decoration: underline;
	}

	.layout {
		max-width: 1240px;
		margin-left: auto;
		margin-right: auto;
		display: grid;
		grid-template-columns: minmax(260px, 0.85fr) minmax(0, 2fr);
		gap: 1.5rem;
		align-items: start;
	}

	.meta-card {
		position: sticky;
		top: 4.5rem;
		padding: 1.1rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: rgba(22, 23, 26, 0.82);
	}

	.meta-card section + section {
		margin-top: 1.1rem;
		padding-top: 1.1rem;
		border-top: 1px solid var(--dl-line);
	}

	.meta-card h3 {
		margin: 0 0 0.55rem;
		color: var(--dl-ink-print);
		font-size: 0.85rem;
	}

	.meta-card ul {
		margin: 0;
		padding-left: 1.05rem;
		color: var(--dl-ink-mute);
		font-size: 0.82rem;
		line-height: 1.6;
	}

	.meta-card li + li {
		margin-top: 0.28rem;
	}

	.related-list {
		list-style: none;
		padding-left: 0;
	}

	.related-list a {
		color: var(--dl-ink-mute);
		text-decoration: none;
	}

	.related-list a:hover {
		color: var(--dl-orange);
	}

	.chip-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.35rem;
	}

	.chip-row span,
	.chip-row .ref-chip {
		display: inline-flex;
		align-items: center;
		min-height: 1.55rem;
		padding: 0.18rem 0.5rem;
		border: 1px solid var(--dl-line-strong);
		border-radius: 6px;
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-mute);
		font-size: 0.74rem;
		text-decoration: none;
	}

	.chip-row .ref-chip:hover {
		border-color: rgba(251, 146, 60, 0.5);
		color: var(--dl-orange);
	}

	.body {
		padding: 1.4rem 1.6rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		background: rgba(22, 23, 26, 0.86);
		color: var(--dl-ink);
		line-height: 1.75;
	}

	.overview-card {
		margin: 0 0 1.4rem;
		padding: 1.2rem 1.35rem;
		border: 1px solid rgba(251, 146, 60, 0.28);
		border-left: 3px solid var(--dl-orange);
		border-radius: var(--dl-r-md);
		background: linear-gradient(135deg, rgba(251, 146, 60, 0.08), rgba(15, 15, 16, 0.62));
	}

	.overview-label {
		margin: 0 0 0.35rem;
		color: var(--dl-orange);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	.overview-card h2 {
		margin: 0 0 0.45rem;
		color: var(--dl-ink-print);
		font-size: 1.35rem;
		line-height: 1.25;
	}

	.overview-card p:not(.overview-label) {
		margin: 0;
		color: var(--dl-ink-mute);
		line-height: 1.65;
	}

	.overview-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.4rem;
		margin-top: 0.8rem;
	}

	.overview-meta span,
	.overview-meta code {
		padding: 0.18rem 0.48rem;
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-raised);
		color: var(--dl-ink-dim);
		font-family: var(--dl-font-mono);
		font-size: 0.72rem;
	}

	.body :global(h1),
	.body :global(h2),
	.body :global(h3),
	.body :global(h4) {
		color: var(--dl-ink-print);
		margin-top: 1.6rem;
		margin-bottom: 0.7rem;
	}

	.body :global(h1) { font-size: 1.6rem; }
	.body :global(h2) { font-size: 1.25rem; }
	.body :global(h3) { font-size: 1.05rem; }
	.body :global(h4) { font-size: 0.95rem; color: var(--dl-orange); }

	.body :global(p) { margin: 0.7rem 0; color: var(--dl-ink-mute); }
	.body :global(ul), .body :global(ol) { padding-left: 1.4rem; color: var(--dl-ink-mute); }
	.body :global(li) { margin: 0.25rem 0; }
	.body :global(code) {
		padding: 0.1rem 0.35rem;
		border-radius: 4px;
		background: var(--dl-bg-overlay);
		font-family: var(--dl-font-mono);
		font-size: 0.86em;
		color: var(--dl-warn);
	}
	.body :global(pre) {
		padding: 0.95rem 1.1rem;
		border-radius: 7px;
		background: var(--dl-bg-deep);
		overflow-x: auto;
		font-size: 0.82rem;
	}
	.body :global(pre code) {
		background: transparent;
		padding: 0;
		color: inherit;
	}
	.body :global(table) {
		width: 100%;
		margin: 0.85rem 0;
		border-collapse: collapse;
		font-size: 0.86rem;
	}
	.body :global(th), .body :global(td) {
		padding: 0.45rem 0.7rem;
		border: 1px solid var(--dl-line);
		text-align: left;
	}
	.body :global(th) {
		background: var(--dl-bg-overlay);
		color: var(--dl-ink-print);
	}
	.body :global(blockquote) {
		margin: 0.85rem 0;
		padding: 0.55rem 0.95rem;
		border-left: 3px solid rgba(251, 146, 60, 0.55);
		background: rgba(251, 146, 60, 0.06);
		color: var(--dl-ink-mute);
	}
	.body :global(a) {
		color: var(--dl-orange);
		text-decoration: underline;
		text-decoration-thickness: 1px;
		text-underline-offset: 3px;
	}

	.toc-section h3 {
		margin: 0 0 0.55rem;
		color: var(--dl-ink-print);
		font-size: 0.85rem;
	}

	.toc {
		list-style: none;
		margin: 0;
		padding: 0;
		max-height: 18rem;
		overflow-y: auto;
		padding-right: 0.4rem;
	}

	.toc li {
		margin: 0.18rem 0;
	}

	.toc button {
		display: block;
		width: 100%;
		padding: 0.18rem 0.4rem;
		border-left: 2px solid transparent;
		border-top: 0;
		border-right: 0;
		border-bottom: 0;
		background: transparent;
		color: var(--dl-ink-mute);
		font-size: 0.8rem;
		line-height: 1.45;
		text-align: left;
		text-decoration: none;
		cursor: pointer;
		transition: color 180ms ease, border-color 180ms ease;
	}

	.toc button:hover {
		color: var(--dl-orange);
	}

	.toc button.active {
		color: var(--dl-orange);
		border-left-color: var(--dl-orange);
		background: rgba(251, 146, 60, 0.06);
	}

	.toc .toc-l2 button { padding-left: 0.85rem; }
	.toc .toc-l3 button { padding-left: 1.4rem; font-size: 0.74rem; }

	.prose {
		margin: 0.5rem 0;
	}

	@media (max-width: 920px) {
		.layout { grid-template-columns: 1fr; }
		.meta-card { position: static; }
	}
</style>
