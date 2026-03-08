<script lang="ts">
	import { base } from '$app/paths';
	import { Github } from 'lucide-svelte';
	import DocFooter from '$lib/components/DocFooter.svelte';

	let { children } = $props();
</script>

<div class="dl-blog">
	<header class="dl-blog-header">
		<div class="dl-blog-header-inner">
			<div class="dl-blog-header-left">
				<a href="{base}/" class="dl-blog-logo">
					<img src="{base}/avatar.png" alt="DartLab" width="30" height="30" class="dl-blog-logo-img" />
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

	<main class="dl-blog-main">
		{@render children()}
	</main>

	<DocFooter />
</div>

<style>
	:global(body) {
		margin: 0;
		background: #050811;
		color: #f1f5f9;
	}

	.dl-blog {
		min-height: 100vh;
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
		max-width: 1100px;
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

	.dl-blog-header-right {
		display: flex;
		align-items: center;
		gap: 0.5rem;
	}

	.dl-blog-icon-link {
		color: #64748b;
		display: flex;
		padding: 0.25rem;
		transition: color 0.15s;
	}
	.dl-blog-icon-link:hover { color: #f1f5f9; }

	.dl-blog-main {
		max-width: 1100px;
		margin: 0 auto;
		padding: 2.5rem 1.5rem 6rem;
	}

	@media (max-width: 480px) {
		.dl-blog-logo-text { display: none; }
		.dl-blog-divider { display: none; }
	}
</style>
