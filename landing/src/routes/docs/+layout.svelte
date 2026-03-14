<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { navigation, type NavItem } from '$lib/docs/navigation';
	import { Github, Menu, X, ChevronRight, ChevronDown } from 'lucide-svelte';
	import Footer from '$lib/components/sections/Footer.svelte';

	let { children } = $props();
	let mobileNavOpen = $state(false);

	let currentPath = $derived(page.url.pathname.replace(base, ''));

	let currentSection = $derived.by(() => {
		for (const section of navigation) {
			if (section.items) {
				for (const item of section.items) {
					if (currentPath === item.href || currentPath === item.href + '/') {
						return section;
					}
				}
			}
			if (currentPath === section.href || currentPath === section.href + '/') {
				return section;
			}
		}
		return undefined;
	});

	let isIndex = $derived(
		currentPath === '/docs' || currentPath === '/docs/'
	);

	const sidebarSections = navigation.filter(s => s.items && s.items.length > 0);
	const standaloneItems = navigation.filter(s => !s.items || s.items.length === 0);

	let expandedSections = $state<Set<string>>(new Set());

	$effect(() => {
		if (currentSection) {
			expandedSections = new Set([currentSection.href]);
		}
	});

	function toggleSection(href: string) {
		const next = new Set(expandedSections);
		if (next.has(href)) {
			next.delete(href);
		} else {
			next.add(href);
		}
		expandedSections = next;
	}
</script>

<div class="dl-docs">
	<header class="dl-docs-header">
		<div class="dl-docs-header-inner">
			<div class="dl-docs-header-left">
				<a href="{base}/" class="dl-docs-logo">
					<picture>
						<source srcset="{base}/avatar.webp" type="image/webp" />
						<img src="{base}/avatar.png" alt="DartLab" width="30" height="30" class="dl-docs-logo-img" />
					</picture>
					<span class="dl-docs-logo-text">DartLab</span>
				</a>
				<span class="dl-docs-divider">/</span>
				<a href="{base}/docs" class="dl-docs-link">Docs</a>
			</div>

			<div class="dl-docs-header-right">
				<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener" class="dl-docs-icon-link">
					<Github size={18} />
				</a>
				<button class="dl-docs-mobile-btn" onclick={() => mobileNavOpen = !mobileNavOpen}>
					{#if mobileNavOpen}<X size={20} />{:else}<Menu size={20} />{/if}
				</button>
			</div>
		</div>

		{#if mobileNavOpen}
			<nav class="dl-docs-mobile-nav">
				{#each sidebarSections as section}
					<div class="dl-docs-mobile-section">
						<span class="dl-docs-mobile-section-title">{section.title}</span>
						{#each section.items ?? [] as item}
							<a
								href="{base}{item.href}"
								class="dl-docs-mobile-link"
								class:active={currentPath === item.href || currentPath === item.href + '/'}
								onclick={() => mobileNavOpen = false}
							>
								{item.title}
							</a>
						{/each}
					</div>
				{/each}
				{#each standaloneItems as item}
					<a
						href="{base}{item.href}"
						class="dl-docs-mobile-link"
						class:active={currentPath === item.href}
						onclick={() => mobileNavOpen = false}
					>
						{item.title}
					</a>
				{/each}
			</nav>
		{/if}
	</header>

	<div class="dl-docs-body" class:is-index={isIndex}>
		{#if !isIndex}
			<aside class="dl-docs-sidebar">
				<div class="dl-docs-sidebar-inner">
					<div class="dl-docs-sidebar-brand">
						<span class="dl-docs-sidebar-kicker">DartLab Docs</span>
						<strong class="dl-docs-sidebar-title">Build From the Filing Graph</strong>
						<p class="dl-docs-sidebar-desc">설치부터 API 흐름까지, 공시 데이터를 코드로 연결하는 문서.</p>
					</div>
					<div class="dl-docs-sidebar-product">
						<a href="{base}/docs/getting-started/quickstart" class="dl-docs-product-link primary">Quickstart</a>
						<a href="{base}/blog/" class="dl-docs-product-link">Blog Hub</a>
					</div>
					<nav class="dl-docs-sidebar-nav">
						{#each sidebarSections as section}
							<div class="dl-sidebar-section">
								<button
									class="dl-sidebar-section-btn"
									class:active={currentSection === section}
									onclick={() => toggleSection(section.href)}
								>
									<span>{section.title}</span>
									{#if expandedSections.has(section.href)}
										<ChevronDown size={14} />
									{:else}
										<ChevronRight size={14} />
									{/if}
								</button>
								{#if expandedSections.has(section.href) && section.items}
									<div class="dl-sidebar-items">
										{#each section.items as item}
											<a
												href="{base}{item.href}"
												class="dl-sidebar-item"
												class:active={currentPath === item.href || currentPath === item.href + '/'}
											>
												{item.title}
											</a>
										{/each}
									</div>
								{/if}
							</div>
						{/each}
						<div class="dl-sidebar-standalone">
							{#each standaloneItems as item}
								<a
									href="{base}{item.href}"
									class="dl-sidebar-item"
									class:active={currentPath === item.href || currentPath === item.href + '/'}
								>
									{item.title}
								</a>
							{/each}
						</div>
					</nav>
				</div>
			</aside>
		{/if}

		<main class="dl-docs-main">
			<div class="dl-docs-content">
				{@render children()}
			</div>
		</main>
	</div>

	<Footer />
</div>

<style>
	:global(body) {
		margin: 0;
		background: #050811;
		color: #fafaf9;
	}

	.dl-docs {
		min-height: 100vh;
		--shell-max-width: 1400px;
		--sidebar-width: 220px;
		--content-max-width: 860px;
		--toc-width: 200px;
		--page-gutter: 1.5rem;
		--rail-gap: 2rem;
	}

	/* Header */
	.dl-docs-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background: rgba(3, 5, 9, 0.85);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid rgba(30, 36, 51, 0.6);
	}

	.dl-docs-header-inner {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 56px;
	}

	.dl-docs-header-left {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-docs-logo {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		text-decoration: none;
		color: #fafaf9;
		font-weight: 700;
		font-size: 1.05rem;
	}

	.dl-docs-logo-img { border-radius: 50%; }

	.dl-docs-divider {
		color: #1e2433;
		font-size: 1.2rem;
		font-weight: 300;
		margin: 0 0.15rem;
	}

	.dl-docs-link {
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
	}
	.dl-docs-link:hover { color: #fafaf9; }

	.dl-docs-header-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-docs-icon-link {
		color: #64748b;
		display: flex;
		padding: 0.25rem;
		transition: color 0.15s;
	}
	.dl-docs-icon-link:hover { color: #fafaf9; }

	.dl-docs-mobile-btn {
		display: none;
		padding: 0.25rem;
		border: none;
		background: none;
		color: #94a3b8;
		cursor: pointer;
	}

	/* Body */
	.dl-docs-body {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: grid;
		grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
		gap: var(--rail-gap);
		min-height: calc(100vh - 56px);
		padding: 2.25rem var(--page-gutter) 6rem;
	}

	.dl-docs-body.is-index {
		grid-template-columns: 1fr;
	}

	/* Sidebar */
	.dl-docs-sidebar {
		display: block;
	}

	.dl-docs-sidebar-inner {
		position: sticky;
		top: 84px;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		padding: 0.35rem 0;
		max-height: calc(100vh - 100px);
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(148, 163, 184, 0.15) transparent;
	}

	.dl-docs-sidebar-brand {
		padding: 0 0.15rem 0.2rem;
	}

	.dl-docs-sidebar-kicker {
		display: block;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #ea4647;
		margin-bottom: 0.35rem;
	}

	.dl-docs-sidebar-title {
		display: block;
		font-size: 1rem;
		color: #f8fafc;
		margin-bottom: 0.45rem;
	}

	.dl-docs-sidebar-desc {
		font-size: 0.84rem;
		line-height: 1.65;
		color: #94a3b8;
		margin: 0;
	}

	.dl-docs-sidebar-product {
		display: flex;
		flex-direction: column;
		gap: 0.55rem;
	}

	.dl-docs-product-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.68rem 0.9rem;
		border-radius: 12px;
		border: 1px solid rgba(148, 163, 184, 0.16);
		background: rgba(148, 163, 184, 0.06);
		color: #e2e8f0;
		text-decoration: none;
		font-size: 0.82rem;
		font-weight: 700;
	}

	.dl-docs-product-link.primary {
		background: rgba(234, 70, 71, 0.14);
		border-color: rgba(234, 70, 71, 0.28);
		color: #fda4a4;
	}

	.dl-sidebar-section {
		margin-bottom: 0.45rem;
	}

	.dl-sidebar-section-btn {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 0.72rem 0.8rem;
		border: 1px solid transparent;
		background: rgba(148, 163, 184, 0.03);
		color: #cbd5e1;
		font-size: 0.88rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 12px;
		transition: all 0.15s;
	}
	.dl-sidebar-section-btn:hover {
		border-color: rgba(234, 70, 71, 0.24);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.05);
	}
	.dl-sidebar-section-btn.active {
		border-color: rgba(234, 70, 71, 0.28);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.08);
		box-shadow: inset 3px 0 0 #ea4647;
	}

	.dl-sidebar-items {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		padding: 0.45rem 0 0.1rem 0.55rem;
	}

	.dl-sidebar-item {
		display: flex;
		align-items: center;
		padding: 0.68rem 0.8rem;
		font-size: 0.84rem;
		color: #cbd5e1;
		text-decoration: none;
		border-radius: 12px;
		transition: all 0.12s;
		border: 1px solid transparent;
		background: rgba(148, 163, 184, 0.03);
	}
	.dl-sidebar-item:hover {
		border-color: rgba(234, 70, 71, 0.24);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.05);
	}
	.dl-sidebar-item.active {
		border-color: rgba(234, 70, 71, 0.28);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.08);
		box-shadow: inset 3px 0 0 #ea4647;
	}

	.dl-sidebar-standalone {
		margin-top: 0.75rem;
		padding-top: 0.75rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	/* Main content */
	.dl-docs-main {
		min-width: 0;
	}

	/* Content typography */
	.dl-docs-content :global(h1) {
		font-size: 2rem;
		font-weight: 800;
		margin-bottom: 0.5rem;
		background: linear-gradient(135deg, #f1f5f9, #94a3b8);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.dl-docs-content :global(h2) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-top: 3.5rem;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(168, 162, 158, 0.1);
		color: #fafaf9;
	}

	.dl-docs-content :global(h3) {
		font-size: 1.2rem;
		font-weight: 600;
		margin-top: 2.5rem;
		margin-bottom: 0.75rem;
		color: #e7e5e4;
	}

	.dl-docs-content :global(h4) {
		font-size: 1rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: #d6d3d1;
	}

	.dl-docs-content :global(p) {
		line-height: 1.75;
		color: #94a3b8;
		margin-bottom: 1rem;
	}

	.dl-docs-content :global(a) { color: #ea4647; text-decoration: none; }
	.dl-docs-content :global(a:hover) { text-decoration: underline; }

	.dl-docs-content :global(strong) { color: #e2e8f0; }

	.dl-docs-content :global(code:not(pre code)) {
		background: rgba(148, 163, 184, 0.1);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.875em;
		font-family: 'JetBrains Mono', monospace;
		color: #e2e8f0;
	}

	.dl-docs-content :global(pre) {
		background: #0d1117 !important;
		border: 1px solid rgba(30, 36, 51, 0.8);
		border-radius: 8px;
		padding: 1rem;
		overflow-x: auto;
		margin: 1rem 0;
		font-size: 0.85rem;
	}

	.dl-docs-content :global(pre code) {
		background: none !important;
		padding: 0;
		font-family: 'JetBrains Mono', monospace;
	}

	.dl-docs-content :global(ul), .dl-docs-content :global(ol) {
		padding-left: 1.5rem;
		margin-bottom: 1rem;
		color: #94a3b8;
	}

	.dl-docs-content :global(li) {
		line-height: 1.75;
		margin-bottom: 0.25rem;
	}

	.dl-docs-content :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1.5rem 0;
		font-size: 0.875rem;
	}

	.dl-docs-content :global(th) {
		text-align: left;
		padding: 0.75rem 1rem;
		border-bottom: 2px solid rgba(30, 36, 51, 0.8);
		color: #fafaf9;
		font-weight: 600;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.dl-docs-content :global(td) {
		padding: 0.6rem 1rem;
		border-bottom: 1px solid rgba(168, 162, 158, 0.08);
		color: #94a3b8;
	}

	.dl-docs-content :global(tr:hover td) {
		background: rgba(148, 163, 184, 0.03);
	}

	.dl-docs-content :global(blockquote) {
		border-left: 3px solid #ea4647;
		padding: 0.5rem 1rem;
		margin: 1rem 0;
		background: rgba(234, 70, 71, 0.05);
		border-radius: 0 6px 6px 0;
	}

	.dl-docs-content :global(blockquote p) { color: #cbd5e1; margin: 0; }

	.dl-docs-content :global(hr) {
		border: none;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
		margin: 3rem 0;
	}

	.dl-docs-content :global(img) { max-width: 100%; border-radius: 8px; }

	/* Mobile nav */
	.dl-docs-mobile-nav {
		display: none;
		flex-direction: column;
		padding: 0.5rem 1rem 1rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
		max-height: 60vh;
		overflow-y: auto;
	}

	.dl-docs-mobile-section {
		margin-bottom: 0.5rem;
	}

	.dl-docs-mobile-section-title {
		display: block;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		padding: 0.4rem 0.5rem 0.15rem;
	}

	.dl-docs-mobile-link {
		display: block;
		padding: 0.5rem 0.5rem 0.5rem 1rem;
		font-size: 0.85rem;
		color: #94a3b8;
		text-decoration: none;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}
	.dl-docs-mobile-link:hover { color: #fafaf9; }
	.dl-docs-mobile-link.active { color: #ea4647; }

	@media (max-width: 1024px) {
		.dl-docs-body {
			grid-template-columns: 1fr;
			padding: 1.5rem 0.75rem 4rem;
		}

		.dl-docs-sidebar {
			display: none;
		}

		.dl-docs-mobile-btn { display: block; }
		.dl-docs-mobile-nav { display: flex; }

		.dl-docs-main { padding: 0; }
	}

	@media (max-width: 480px) {
		.dl-docs-logo-text { display: none; }
		.dl-docs-divider { display: none; }
		.dl-docs-body { padding: 1rem 0.75rem 3rem; }
	}
</style>
