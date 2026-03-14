<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { navigation, type NavItem } from '$lib/docs/navigation';
	import { Github, Menu, X, ChevronRight, ChevronDown, Search } from 'lucide-svelte';
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

	function openSearch() {
		window.dispatchEvent(new CustomEvent('open-command-palette'));
	}
</script>

<div class="dl-docs">
	<header class="dl-docs-header">
		<div class="dl-docs-header-inner">
			<div class="dl-docs-header-left">
				<a href="{base}/" class="dl-docs-logo">
					<picture>
						<source srcset="{base}/avatar.webp" type="image/webp" />
						<img src="{base}/avatar.png" alt="DartLab" width="24" height="24" class="dl-docs-logo-img" />
					</picture>
					<span class="dl-docs-logo-text">DartLab</span>
				</a>
				<span class="dl-docs-divider">/</span>
				<a href="{base}/docs" class="dl-docs-link">Docs</a>
			</div>

			<div class="dl-docs-header-right">
				<button class="dl-docs-search-btn" onclick={openSearch}>
					<Search size={14} />
					<span>Search...</span>
					<kbd>⌘K</kbd>
				</button>
				<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener" class="dl-docs-icon-link">
					<Github size={16} />
				</a>
				<button class="dl-docs-mobile-btn" onclick={() => mobileNavOpen = !mobileNavOpen}>
					{#if mobileNavOpen}<X size={18} />{:else}<Menu size={18} />{/if}
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
					<nav class="dl-docs-sidebar-nav">
						{#each sidebarSections as section}
							<div class="dl-sidebar-section">
								<button
									class="dl-sidebar-section-btn"
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
		color: #f1f5f9;
	}

	.dl-docs {
		min-height: 100vh;
		--shell-max-width: 1400px;
		--sidebar-width: 240px;
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
		background: rgba(3, 5, 9, 0.92);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid rgba(30, 36, 51, 0.6);
	}

	.dl-docs-header-inner {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1rem;
		height: 48px;
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
		color: #f1f5f9;
		font-weight: 600;
		font-size: 0.875rem;
	}

	.dl-docs-logo-img { border-radius: 50%; }

	.dl-docs-divider {
		color: #1e2433;
		font-size: 1rem;
		font-weight: 300;
	}

	.dl-docs-link {
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.8125rem;
		font-weight: 500;
	}
	.dl-docs-link:hover { color: #f1f5f9; }

	.dl-docs-header-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-docs-search-btn {
		display: none;
		align-items: center;
		gap: 0.5rem;
		padding: 0.25rem 0.625rem;
		border-radius: 6px;
		border: 1px solid rgba(30, 36, 51, 0.8);
		background: rgba(15, 18, 25, 0.5);
		color: #64748b;
		font-size: 0.75rem;
		cursor: pointer;
		height: 28px;
		transition: border-color 0.15s, color 0.15s;
	}
	.dl-docs-search-btn:hover {
		border-color: rgba(30, 36, 51, 1);
		color: #94a3b8;
	}
	.dl-docs-search-btn kbd {
		padding: 0.1rem 0.3rem;
		border-radius: 4px;
		background: rgba(5, 8, 17, 0.8);
		border: 1px solid rgba(30, 36, 51, 0.8);
		font-size: 0.625rem;
		font-family: inherit;
		line-height: 1;
		color: #64748b;
	}

	.dl-docs-icon-link {
		color: #64748b;
		display: flex;
		padding: 0.25rem;
		transition: color 0.15s;
	}
	.dl-docs-icon-link:hover { color: #f1f5f9; }

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
		min-height: calc(100vh - 48px);
		padding: 1.5rem var(--page-gutter) 6rem;
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
		top: 72px;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.25rem 0;
		max-height: calc(100vh - 80px);
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(148, 163, 184, 0.1) transparent;
	}

	.dl-sidebar-section {
		margin-bottom: 0.25rem;
	}

	.dl-sidebar-section-btn {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 0.375rem 0.5rem;
		border: none;
		background: none;
		color: #94a3b8;
		font-size: 0.6875rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 6px;
		transition: color 0.15s;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.dl-sidebar-section-btn:hover {
		color: #f1f5f9;
	}

	.dl-sidebar-items {
		display: flex;
		flex-direction: column;
		gap: 1px;
		padding: 0.25rem 0 0.25rem 0;
	}

	.dl-sidebar-item {
		display: flex;
		align-items: center;
		padding: 0.375rem 0.625rem;
		font-size: 0.8125rem;
		color: #94a3b8;
		text-decoration: none;
		border-radius: 6px;
		transition: color 0.12s, background 0.12s;
		border-left: 2px solid transparent;
		margin-left: 0.25rem;
	}
	.dl-sidebar-item:hover {
		color: #f1f5f9;
		background: rgba(17, 24, 39, 0.6);
	}
	.dl-sidebar-item.active {
		color: #f1f5f9;
		font-weight: 600;
		border-left-color: #ea4647;
		background: rgba(234, 70, 71, 0.05);
	}

	.dl-sidebar-standalone {
		margin-top: 0.5rem;
		padding-top: 0.5rem;
		border-top: 1px solid rgba(30, 36, 51, 0.6);
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	/* Main content */
	.dl-docs-main {
		min-width: 0;
	}

	/* Content typography */
	.dl-docs-content :global(h1) {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 0.5rem;
		color: #f1f5f9;
	}

	.dl-docs-content :global(h2) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-top: 3.5rem;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.6);
		color: #f1f5f9;
	}

	.dl-docs-content :global(h3) {
		font-size: 1.2rem;
		font-weight: 600;
		margin-top: 2.5rem;
		margin-bottom: 0.75rem;
		color: #e2e8f0;
	}

	.dl-docs-content :global(h4) {
		font-size: 1rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: #cbd5e1;
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
		background: rgba(15, 18, 25, 0.8);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.875em;
		font-family: 'JetBrains Mono', monospace;
		color: #e2e8f0;
		border: 1px solid rgba(30, 36, 51, 0.5);
	}

	.dl-docs-content :global(pre) {
		background: #0f1219 !important;
		border: 1px solid rgba(30, 36, 51, 0.6);
		border-radius: 8px;
		padding: 1rem;
		overflow-x: auto;
		margin: 1rem 0;
		font-size: 0.85rem;
	}

	.dl-docs-content :global(pre code) {
		background: none !important;
		padding: 0;
		border: none;
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
		padding: 0.625rem 1rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
		color: #f1f5f9;
		font-weight: 600;
		font-size: 0.8rem;
	}

	.dl-docs-content :global(td) {
		padding: 0.5rem 1rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.4);
		color: #94a3b8;
	}

	.dl-docs-content :global(tr:hover td) {
		background: rgba(17, 24, 39, 0.3);
	}

	.dl-docs-content :global(blockquote) {
		border-left: 2px solid #ea4647;
		padding: 0.5rem 1rem;
		margin: 1rem 0;
		background: rgba(234, 70, 71, 0.04);
		border-radius: 0 6px 6px 0;
	}

	.dl-docs-content :global(blockquote p) { color: #cbd5e1; margin: 0; }

	.dl-docs-content :global(hr) {
		border: none;
		border-top: 1px solid rgba(30, 36, 51, 0.6);
		margin: 3rem 0;
	}

	.dl-docs-content :global(img) { max-width: 100%; border-radius: 8px; }

	/* Mobile nav */
	.dl-docs-mobile-nav {
		display: none;
		flex-direction: column;
		padding: 0.5rem 1rem 1rem;
		border-top: 1px solid rgba(30, 36, 51, 0.6);
		max-height: 60vh;
		overflow-y: auto;
	}

	.dl-docs-mobile-section {
		margin-bottom: 0.5rem;
	}

	.dl-docs-mobile-section-title {
		display: block;
		font-size: 0.6875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		padding: 0.4rem 0.5rem 0.15rem;
	}

	.dl-docs-mobile-link {
		display: block;
		padding: 0.5rem 0.5rem 0.5rem 1rem;
		font-size: 0.8125rem;
		color: #94a3b8;
		text-decoration: none;
		border-bottom: 1px solid rgba(30, 36, 51, 0.4);
	}
	.dl-docs-mobile-link:hover { color: #f1f5f9; }
	.dl-docs-mobile-link.active { color: #ea4647; }

	@media (min-width: 768px) {
		.dl-docs-search-btn { display: flex; }
	}

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
