<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { Github } from 'lucide-svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { categoryDefinitions, getCategoryPath } from '$lib/blog/posts';

	let { children } = $props();

	let currentPath = $derived(page.url.pathname.replace(base, ''));
	let currentCategory = $derived(page.data.currentCategory);
</script>

<div class="dl-blog">
	<header class="dl-blog-header">
		<div class="dl-blog-header-inner">
			<div class="dl-blog-header-left">
				<a href="{base}/" class="dl-blog-logo">
					<picture>
						<source srcset="{base}/avatar.webp" type="image/webp" />
						<img src="{base}/avatar.png" alt="DartLab" width="30" height="30" class="dl-blog-logo-img" />
					</picture>
					<span class="dl-blog-logo-text">DartLab</span>
				</a>
				<span class="dl-blog-divider">/</span>
				<a href="{base}/blog/" class="dl-blog-link">Blog</a>
			</div>
			<div class="dl-blog-header-right">
				<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener" class="dl-blog-icon-link">
					<Github size={18} />
				</a>
			</div>
		</div>
	</header>

	<div class="dl-blog-body">
		<aside class="dl-blog-sidebar">
			<div class="dl-blog-sidebar-inner">
				<div class="dl-blog-sidebar-brand">
					<div class="dl-blog-sidebar-brand-row">
						<picture>
							<source srcset="{base}/avatar.webp" type="image/webp" />
							<img src="{base}/avatar.png" alt="DartLab" width="36" height="36" class="dl-blog-sidebar-avatar" />
						</picture>
						<span class="dl-blog-sidebar-kicker">DartLab Blog</span>
					</div>
					<strong class="dl-blog-sidebar-title">Read Beyond the Numbers</strong>
					<p class="dl-blog-sidebar-desc">공시를 숫자가 아니라 구조와 맥락으로 읽는 아카이브.</p>
				</div>
				<div class="dl-blog-sidebar-product">
					<a href="{base}/docs/getting-started/quickstart" class="dl-blog-product-link primary">Quickstart</a>
					<a href="{base}/docs/api/overview" class="dl-blog-product-link">API Overview</a>
				</div>
				<nav class="dl-blog-category-nav">
					<a href="{base}/blog/" class="dl-blog-category-link" class:active={currentPath === '/blog' || currentPath === '/blog/'}>
						전체 허브
					</a>
					{#each categoryDefinitions as category}
						<a
							href="{base}{getCategoryPath(category.id)}"
							class="dl-blog-category-link"
							class:active={currentCategory === category.id || currentPath === getCategoryPath(category.id) || currentPath.startsWith(`${getCategoryPath(category.id)}/`)}
						>
							<span>{category.label}</span>
						</a>
					{/each}
				</nav>
			</div>
		</aside>

		<main class="dl-blog-main">
			{@render children()}
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

	.dl-blog {
		min-height: 100vh;
		--shell-max-width: 1400px;
		--sidebar-width: 220px;
		--content-max-width: 860px;
		--toc-width: 200px;
		--page-gutter: 1.5rem;
		--rail-gap: 2rem;
	}

	.dl-blog-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background: rgba(3, 5, 9, 0.85);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid rgba(30, 36, 51, 0.6);
	}

	.dl-blog-header-inner {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1.5rem;
		height: 56px;
	}

	.dl-blog-header-left {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-blog-logo {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		text-decoration: none;
		color: #f1f5f9;
		font-weight: 700;
		font-size: 1.05rem;
	}

	.dl-blog-logo-img { border-radius: 50%; }

	.dl-blog-divider {
		color: #1e2433;
		font-size: 1.2rem;
		font-weight: 300;
		margin: 0 0.15rem;
	}

	.dl-blog-link {
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.9rem;
		font-weight: 500;
	}

	.dl-blog-link:hover { color: #f1f5f9; }

	.dl-blog-icon-link {
		color: #64748b;
		display: flex;
		padding: 0.25rem;
		transition: color 0.15s;
	}

	.dl-blog-icon-link:hover { color: #f1f5f9; }

	.dl-blog-body {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: grid;
		grid-template-columns: var(--sidebar-width) minmax(0, 1fr);
		gap: var(--rail-gap);
		padding: 2.25rem var(--page-gutter) 6rem;
	}

	.dl-blog-sidebar {
		display: block;
	}

	.dl-blog-sidebar-inner {
		position: sticky;
		top: 84px;
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
		padding: 0.35rem 0;
	}

	.dl-blog-sidebar-brand {
		padding: 0 0.15rem 0.2rem;
	}

	.dl-blog-sidebar-brand-row {
		display: flex;
		align-items: center;
		gap: 0.65rem;
		margin-bottom: 0.5rem;
	}

	.dl-blog-sidebar-avatar {
		width: 36px;
		height: 36px;
		border-radius: 50%;
		border: 1px solid rgba(234, 70, 71, 0.22);
		box-shadow: 0 6px 18px rgba(3, 5, 9, 0.24);
		flex-shrink: 0;
	}

	.dl-blog-sidebar-kicker {
		display: block;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #ea4647;
		margin-bottom: 0;
	}

	.dl-blog-sidebar-title {
		display: block;
		font-size: 1rem;
		color: #f8fafc;
		margin-bottom: 0.45rem;
	}

	.dl-blog-sidebar-desc {
		font-size: 0.84rem;
		line-height: 1.65;
		color: #94a3b8;
		margin: 0;
	}

	.dl-blog-category-nav {
		display: flex;
		flex-direction: column;
		gap: 0.45rem;
	}

	.dl-blog-sidebar-product {
		display: flex;
		flex-direction: column;
		gap: 0.55rem;
	}

	.dl-blog-product-link {
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

	.dl-blog-product-link.primary {
		background: rgba(234, 70, 71, 0.14);
		border-color: rgba(234, 70, 71, 0.28);
		color: #fda4a4;
	}

	.dl-blog-category-link {
		display: flex;
		align-items: center;
		padding: 0.72rem 0.8rem;
		border-radius: 12px;
		border: 1px solid transparent;
		background: rgba(148, 163, 184, 0.03);
		color: #cbd5e1;
		text-decoration: none;
		font-size: 0.88rem;
		font-weight: 600;
		transition: border-color 0.15s, color 0.15s, background 0.15s;
	}

	.dl-blog-category-link:hover {
		border-color: rgba(234, 70, 71, 0.24);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.05);
	}

	.dl-blog-category-link.active {
		border-color: rgba(234, 70, 71, 0.28);
		color: #f8fafc;
		background: rgba(234, 70, 71, 0.08);
		box-shadow: inset 3px 0 0 #ea4647;
	}

	.dl-blog-main {
		min-width: 0;
	}

	@media (max-width: 960px) {
		.dl-blog-body {
			grid-template-columns: 1fr;
			gap: 1rem;
			padding: 1.5rem 0.75rem 4rem;
		}

		.dl-blog-sidebar-inner {
			position: static;
			flex-direction: row;
			align-items: center;
			overflow-x: auto;
			padding: 0.25rem 0;
		}

		.dl-blog-sidebar-brand {
			min-width: 220px;
		}

		.dl-blog-sidebar-product {
			flex-direction: row;
		}

		.dl-blog-category-nav {
			flex-direction: row;
			flex-wrap: nowrap;
		}

		.dl-blog-category-link {
			white-space: nowrap;
		}
	}

	@media (max-width: 480px) {
		.dl-blog-logo-text { display: none; }
		.dl-blog-divider { display: none; }
		.dl-blog-sidebar-brand { min-width: 180px; }
	}
</style>
