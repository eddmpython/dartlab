<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { navigation, type NavItem } from '$lib/docs/navigation';
	import type { Snippet } from 'svelte';

	let { children }: { children: Snippet } = $props();
	let mobileOpen = $state(false);
	let expandedSections = $state<Set<string>>(new Set());

	const currentPath = $derived(page.url.pathname);
	const isIndex = $derived(currentPath === `${base}/docs` || currentPath === `${base}/docs/`);

	const currentSection = $derived(
		navigation.find(
			(nav) =>
				nav.items?.some((item) => currentPath.endsWith(item.href)) ??
				currentPath.endsWith(nav.href)
		)
	);

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

	function isActive(href: string): boolean {
		return currentPath.endsWith(href);
	}
</script>

<div class="docs-shell">
	<header class="docs-header">
		<div class="header-inner">
			<a href="{base}/" class="logo">
				<img src="{base}/icon-final.png" alt="DartLab" width="24" height="24" />
				<span class="logo-text">DartLab</span>
			</a>
			<nav class="header-nav">
				<a href="{base}/docs" class="nav-link" class:active={isIndex}>문서</a>
				<a href="https://github.com/eddmpython/dartlab" class="nav-link" target="_blank" rel="noopener">GitHub</a>
			</nav>
			<button class="mobile-toggle" onclick={() => (mobileOpen = !mobileOpen)}>
				{mobileOpen ? '✕' : '☰'}
			</button>
		</div>
	</header>

	<div class="docs-body" class:full-width={isIndex}>
		{#if !isIndex}
			<aside class="sidebar" class:open={mobileOpen}>
				<nav>
					{#each navigation as section}
						{#if section.items && section.items.length > 0}
							<button
								class="section-btn"
								onclick={() => toggleSection(section.href)}
							>
								<span>{section.title}</span>
								<span class="chevron" class:expanded={expandedSections.has(section.href)}>›</span>
							</button>
							{#if expandedSections.has(section.href)}
								<ul class="section-items">
									{#each section.items as item}
										<li>
											<a
												href="{base}{item.href}"
												class:active={isActive(item.href)}
												onclick={() => (mobileOpen = false)}
											>{item.title}</a>
										</li>
									{/each}
								</ul>
							{/if}
						{:else}
							<a
								href="{base}{section.href}"
								class="section-link"
								class:active={isActive(section.href)}
								onclick={() => (mobileOpen = false)}
							>{section.title}</a>
						{/if}
					{/each}
				</nav>
			</aside>
		{/if}

		<main class="docs-main">
			{@render children()}
		</main>
	</div>
</div>

<style>
	.docs-shell {
		min-height: 100vh;
		display: flex;
		flex-direction: column;
	}

	.docs-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background: rgba(12, 10, 9, 0.85);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid #292524;
		height: 56px;
	}
	.header-inner {
		max-width: 1400px;
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 100%;
	}
	.logo {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		text-decoration: none;
	}
	.logo img {
		border-radius: 4px;
	}
	.logo-text {
		font-weight: 700;
		font-size: 1.1rem;
		color: #fafaf9;
	}
	.header-nav {
		display: flex;
		gap: 1.5rem;
	}
	.nav-link {
		color: #a8a29e;
		text-decoration: none;
		font-size: 0.875rem;
		font-weight: 500;
		transition: color 0.15s;
	}
	.nav-link:hover,
	.nav-link.active {
		color: #fafaf9;
	}
	.mobile-toggle {
		display: none;
		background: none;
		border: none;
		color: #fafaf9;
		font-size: 1.25rem;
		cursor: pointer;
	}

	.docs-body {
		display: grid;
		grid-template-columns: 220px 1fr;
		flex: 1;
		max-width: 1400px;
		margin: 0 auto;
		width: 100%;
	}
	.docs-body.full-width {
		grid-template-columns: 1fr;
	}

	.sidebar {
		position: sticky;
		top: 56px;
		height: calc(100vh - 56px);
		overflow-y: auto;
		padding: 1.5rem 1rem;
		border-right: 1px solid #292524;
	}
	.section-btn {
		display: flex;
		align-items: center;
		justify-content: space-between;
		width: 100%;
		padding: 0.5rem 0.5rem;
		background: none;
		border: none;
		color: #d6d3d1;
		font-size: 0.85rem;
		font-weight: 600;
		cursor: pointer;
		border-radius: 4px;
		transition: background 0.15s;
	}
	.section-btn:hover {
		background: #1c1917;
	}
	.chevron {
		font-size: 0.9rem;
		transition: transform 0.2s;
		color: #78716c;
	}
	.chevron.expanded {
		transform: rotate(90deg);
	}
	.section-items {
		list-style: none;
		padding: 0;
		margin: 0 0 0.5rem;
	}
	.section-items li a {
		display: block;
		padding: 0.3rem 0.5rem 0.3rem 1.25rem;
		color: #a8a29e;
		text-decoration: none;
		font-size: 0.825rem;
		border-left: 2px solid transparent;
		transition: all 0.15s;
	}
	.section-items li a:hover {
		color: #d6d3d1;
	}
	.section-items li a.active {
		color: #f59e0b;
		border-left-color: #f59e0b;
	}
	.section-link {
		display: block;
		padding: 0.5rem 0.5rem;
		color: #d6d3d1;
		text-decoration: none;
		font-size: 0.85rem;
		font-weight: 600;
		border-radius: 4px;
	}
	.section-link:hover {
		background: #1c1917;
	}
	.section-link.active {
		color: #f59e0b;
	}

	.docs-main {
		min-width: 0;
		overflow-x: hidden;
	}

	@media (max-width: 1024px) {
		.docs-body {
			grid-template-columns: 1fr;
		}
		.sidebar {
			display: none;
			position: fixed;
			top: 56px;
			left: 0;
			width: 280px;
			height: calc(100vh - 56px);
			z-index: 40;
			background: #0c0a09;
			border-right: 1px solid #292524;
		}
		.sidebar.open {
			display: block;
		}
		.mobile-toggle {
			display: block;
		}
		.header-nav {
			display: none;
		}
	}
</style>
