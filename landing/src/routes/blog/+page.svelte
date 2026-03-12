<script lang="ts">
	import { base } from '$app/paths';
	import { getCategoryGroups } from '$lib/blog/posts';
	import { ArrowRight, Calendar } from 'lucide-svelte';

	const categoryGroups = getCategoryGroups();

	function formatDate(iso: string): string {
		return new Date(iso).toLocaleDateString('ko-KR', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<svelte:head>
	<title>Blog — DartLab</title>
	<meta
		name="description"
		content="DartLab 블로그 — 공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화에 관한 깊은 글."
	/>
</svelte:head>

<div class="blog-index">
	<div class="blog-index-header">
		<h1 class="blog-index-title">Blog</h1>
		<p class="blog-index-desc">공시 시스템, 사업보고서 읽기, 재무 해석, 데이터 자동화를 시리즈 단위로 정리합니다.</p>
	</div>

	<div class="category-list">
		{#each categoryGroups as category}
			<section class="category-section">
				<div class="category-header">
					<div>
						<div class="category-kicker">{category.folder}</div>
						<h2 class="category-title">{category.label}</h2>
					</div>
					<p class="category-desc">{category.description}</p>
				</div>

				<div class="blog-post-grid">
					{#each category.posts as post}
						<a href="{base}/blog/{post.slug}" class="blog-card">
							<div class="blog-card-thumb">
								<img src="{base}{post.thumbnail}" alt={post.title} width="80" height="80" />
							</div>
							<div class="blog-card-body">
								<div class="blog-card-meta">
									<span class="blog-badge">{post.categoryLabel}</span>
									{#if post.seriesLabel}
										<span class="blog-series">{post.seriesLabel}</span>
									{/if}
								</div>
								<div class="blog-card-date">
									<Calendar size={12} />
									{formatDate(post.date)}
								</div>
								<h3 class="blog-card-title">{post.title}</h3>
								<p class="blog-card-desc">{post.description}</p>
								<span class="blog-card-read">
									읽기 <ArrowRight size={14} />
								</span>
							</div>
						</a>
					{/each}
				</div>
			</section>
		{/each}
	</div>
</div>

<style>
	.blog-index {
		max-width: 960px;
		margin: 0 auto;
	}

	.blog-index-header {
		text-align: center;
		margin-bottom: 3rem;
		padding-bottom: 2rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}

	.blog-index-title {
		font-size: 2.5rem;
		font-weight: 800;
		background: linear-gradient(135deg, #f1f5f9, #94a3b8);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		margin-bottom: 0.75rem;
	}

	.blog-index-desc {
		color: #64748b;
		font-size: 1rem;
		line-height: 1.6;
	}

	.category-list {
		display: flex;
		flex-direction: column;
		gap: 2.5rem;
	}

	.category-section {
		display: flex;
		flex-direction: column;
		gap: 1.1rem;
	}

	.category-header {
		display: flex;
		justify-content: space-between;
		align-items: flex-end;
		gap: 1.5rem;
		padding-bottom: 0.85rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}

	.category-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.35rem;
	}

	.category-title {
		font-size: 1.5rem;
		font-weight: 800;
		color: #f8fafc;
	}

	.category-desc {
		max-width: 420px;
		font-size: 0.9rem;
		line-height: 1.7;
		color: #64748b;
	}

	.blog-post-grid {
		display: flex;
		flex-direction: column;
		gap: 1.25rem;
	}

	.blog-card {
		display: flex;
		gap: 1.5rem;
		align-items: flex-start;
		background: #0f1219;
		border: 1px solid #1e2433;
		border-radius: 12px;
		padding: 1.5rem;
		text-decoration: none;
		transition: border-color 0.2s, transform 0.15s, box-shadow 0.2s;
	}

	.blog-card:hover {
		border-color: rgba(234, 70, 71, 0.4);
		transform: translateY(-2px);
		box-shadow: 0 8px 24px rgba(234, 70, 71, 0.06);
	}

	.blog-card-thumb img {
		width: 72px;
		height: 72px;
		border-radius: 50%;
		object-fit: cover;
		flex-shrink: 0;
		border: 2px solid rgba(30, 36, 51, 0.8);
	}

	.blog-card-body {
		flex: 1;
		min-width: 0;
	}

	.blog-card-meta {
		display: flex;
		flex-wrap: wrap;
		gap: 0.45rem;
		margin-bottom: 0.65rem;
	}

	.blog-badge,
	.blog-series {
		display: inline-flex;
		align-items: center;
		padding: 0.25rem 0.55rem;
		border-radius: 999px;
		font-size: 0.68rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.blog-badge {
		background: rgba(234, 70, 71, 0.12);
		border: 1px solid rgba(234, 70, 71, 0.24);
		color: #fda4a4;
	}

	.blog-series {
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
	}

	.blog-card-date {
		display: flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.75rem;
		color: #64748b;
		margin-bottom: 0.5rem;
	}

	.blog-card-title {
		font-size: 1.25rem;
		font-weight: 700;
		color: #f1f5f9;
		margin-bottom: 0.5rem;
		line-height: 1.3;
	}

	.blog-card-desc {
		font-size: 0.875rem;
		color: #64748b;
		line-height: 1.65;
		margin-bottom: 0.75rem;
		display: -webkit-box;
		-webkit-line-clamp: 3;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}

	.blog-card-read {
		display: inline-flex;
		align-items: center;
		gap: 0.3rem;
		font-size: 0.8rem;
		font-weight: 600;
		color: #ea4647;
	}

	@media (max-width: 560px) {
		.category-header {
			flex-direction: column;
			align-items: flex-start;
		}

		.category-desc {
			max-width: none;
		}

		.blog-card {
			flex-direction: column;
		}

		.blog-card-thumb img {
			width: 56px;
			height: 56px;
		}
	}
</style>
