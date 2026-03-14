<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { Github, Search } from 'lucide-svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { categoryDefinitions, getCategoryPath } from '$lib/blog/posts';

	let { children } = $props();

	let currentPath = $derived(page.url.pathname.replace(base, ''));
	let currentCategory = $derived(page.data.currentCategory);

	function openSearch() {
		window.dispatchEvent(new CustomEvent('open-command-palette'));
	}
</script>

<div class="dl-blog">
	<header class="dl-blog-header">
		<div class="dl-blog-header-inner">
			<div class="dl-blog-header-left">
				<a href="{base}/" class="dl-blog-logo">
					<picture>
						<source srcset="{base}/avatar.webp" type="image/webp" />
						<img src="{base}/avatar.png" alt="DartLab" width="24" height="24" class="dl-blog-logo-img" />
					</picture>
					<span class="dl-blog-logo-text">DartLab</span>
				</a>
				<span class="dl-blog-divider">/</span>
				<a href="{base}/blog/" class="dl-blog-link">Blog</a>
			</div>
			<div class="dl-blog-header-right">
				<button class="dl-blog-search-btn" onclick={openSearch}>
					<Search size={14} />
					<span>Search...</span>
					<kbd>⌘K</kbd>
				</button>
				<a href="https://github.com/eddmpython/dartlab" target="_blank" rel="noopener" class="dl-blog-icon-link">
					<Github size={16} />
				</a>
			</div>
		</div>
	</header>

	<div class="dl-blog-body">
		<aside class="dl-blog-sidebar">
			<div class="dl-blog-sidebar-inner">
				<nav class="dl-blog-category-nav">
					<span class="dl-blog-nav-label">Categories</span>
					<a href="{base}/blog/" class="dl-blog-category-link" class:active={currentPath === '/blog' || currentPath === '/blog/'}>
						All Posts
					</a>
					{#each categoryDefinitions as category}
						<a
							href="{base}{getCategoryPath(category.id)}"
							class="dl-blog-category-link"
							class:active={currentCategory === category.id || currentPath === getCategoryPath(category.id) || currentPath.startsWith(`${getCategoryPath(category.id)}/`)}
						>
							{category.label}
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
		--page-gutter: 1.5rem;
		--rail-gap: 2rem;
	}

	.dl-blog-header {
		position: sticky;
		top: 0;
		z-index: 50;
		background: rgba(3, 5, 9, 0.92);
		backdrop-filter: blur(12px);
		border-bottom: 1px solid rgba(30, 36, 51, 0.6);
	}

	.dl-blog-header-inner {
		max-width: var(--shell-max-width);
		margin: 0 auto;
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 0 1rem;
		height: 48px;
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
		font-weight: 600;
		font-size: 0.875rem;
	}

	.dl-blog-logo-img { border-radius: 50%; }

	.dl-blog-divider {
		color: #1e2433;
		font-size: 1rem;
		font-weight: 300;
	}

	.dl-blog-link {
		color: #94a3b8;
		text-decoration: none;
		font-size: 0.8125rem;
		font-weight: 500;
	}
	.dl-blog-link:hover { color: #f1f5f9; }

	.dl-blog-header-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-blog-search-btn {
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
	.dl-blog-search-btn:hover {
		border-color: rgba(30, 36, 51, 1);
		color: #94a3b8;
	}
	.dl-blog-search-btn kbd {
		padding: 0.1rem 0.3rem;
		border-radius: 4px;
		background: rgba(5, 8, 17, 0.8);
		border: 1px solid rgba(30, 36, 51, 0.8);
		font-size: 0.625rem;
		font-family: inherit;
		line-height: 1;
		color: #64748b;
	}

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
		padding: 1.5rem var(--page-gutter) 6rem;
	}

	.dl-blog-sidebar {
		display: block;
	}

	.dl-blog-sidebar-inner {
		position: sticky;
		top: 72px;
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		padding: 0.25rem 0;
	}

	.dl-blog-nav-label {
		display: block;
		font-size: 0.6875rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #64748b;
		padding: 0.375rem 0.5rem;
	}

	.dl-blog-category-nav {
		display: flex;
		flex-direction: column;
		gap: 1px;
	}

	.dl-blog-category-link {
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

	.dl-blog-category-link:hover {
		color: #f1f5f9;
		background: rgba(17, 24, 39, 0.6);
	}

	.dl-blog-category-link.active {
		color: #f1f5f9;
		font-weight: 600;
		border-left-color: #ea4647;
		background: rgba(234, 70, 71, 0.05);
	}

	.dl-blog-main {
		min-width: 0;
	}

	@media (min-width: 768px) {
		.dl-blog-search-btn { display: flex; }
	}

	@media (max-width: 960px) {
		.dl-blog-body {
			grid-template-columns: 1fr;
			gap: 1rem;
			padding: 1.5rem 0.75rem 4rem;
		}

		.dl-blog-sidebar-inner {
			position: static;
		}

		.dl-blog-category-nav {
			flex-direction: row;
			flex-wrap: nowrap;
			overflow-x: auto;
			gap: 0;
		}

		.dl-blog-nav-label { display: none; }

		.dl-blog-category-link {
			white-space: nowrap;
			border-left: none;
			margin-left: 0;
			border-bottom: 2px solid transparent;
			border-radius: 0;
			padding: 0.5rem 0.75rem;
		}

		.dl-blog-category-link.active {
			border-left-color: transparent;
			border-bottom-color: #ea4647;
		}
	}

	@media (max-width: 480px) {
		.dl-blog-logo-text { display: none; }
		.dl-blog-divider { display: none; }
	}
</style>
