<script lang="ts">
	import { base } from '$app/paths';
	import { getPost, findPrevNext } from '$lib/blog/posts';
	import { Calendar, ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { onMount, tick } from 'svelte';

	let { data } = $props();

	interface TocItem {
		id: string;
		text: string;
		level: number;
	}

	let tocItems: TocItem[] = $state([]);
	let activeId = $state('');
	let articleEl: HTMLElement | undefined = $state();

	function extractToc() {
		if (!articleEl) return;
		const headings = articleEl.querySelectorAll('h2, h3');
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
				level: h.tagName === 'H2' ? 2 : 3
			});
		});
		tocItems = items;
	}

	function observeHeadings() {
		if (!articleEl) return;
		const headings = articleEl.querySelectorAll('h2, h3');
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

	function addCopyButtons() {
		if (!articleEl) return;
		articleEl.querySelectorAll('pre').forEach((pre) => {
			if (pre.querySelector('.copy-btn')) return;
			const wrapper = document.createElement('div');
			wrapper.style.position = 'relative';
			pre.parentNode?.insertBefore(wrapper, pre);
			wrapper.appendChild(pre);

			const btn = document.createElement('button');
			btn.className = 'copy-btn';
			btn.textContent = 'Copy';
			btn.addEventListener('click', () => {
				const code = pre.querySelector('code');
				const text = (code || pre).textContent || '';
				navigator.clipboard.writeText(text).then(() => {
					btn.textContent = 'Copied!';
					setTimeout(() => {
						btn.textContent = 'Copy';
					}, 2000);
				});
			});
			wrapper.appendChild(btn);
		});
	}

	let cleanup: (() => void) | undefined;
	let mounted = false;

	onMount(() => {
		mounted = true;
		return () => {
			mounted = false;
			cleanup?.();
		};
	});

	const Component = $derived(data.component);
	const meta = $derived(data.metadata ?? {});
	const postInfo = $derived(getPost(data.slug));
	const prevNext = $derived(findPrevNext(data.slug));

	let giscusEl: HTMLElement | undefined = $state();

	$effect(() => {
		if (!mounted) return;
		Component;
		data;
		tick().then(() => {
			if (!mounted) return;
			addCopyButtons();
			extractToc();
			cleanup?.();
			cleanup = observeHeadings();
			if (tocItems.length === 0 && articleEl) {
				setTimeout(() => {
					extractToc();
					cleanup?.();
					cleanup = observeHeadings();
				}, 200);
			}
		});
	});

	function scrollToHeading(id: string) {
		const el = document.getElementById(id);
		if (el) {
			el.scrollIntoView({ behavior: 'smooth', block: 'start' });
		}
	}

	$effect(() => {
		if (!giscusEl || !mounted) return;
		giscusEl.innerHTML = '';
		const script = document.createElement('script');
		script.src = 'https://giscus.app/client.js';
		script.setAttribute('data-repo', 'eddmpython/dartlab');
		script.setAttribute('data-repo-id', 'R_kgDORgID2A');
		script.setAttribute('data-category', 'General');
		script.setAttribute('data-category-id', 'DIC_kwDORgID2M4C38mI');
		script.setAttribute('data-mapping', 'pathname');
		script.setAttribute('data-strict', '0');
		script.setAttribute('data-reactions-enabled', '1');
		script.setAttribute('data-emit-metadata', '0');
		script.setAttribute('data-input-position', 'top');
		script.setAttribute('data-theme', 'dark_dimmed');
		script.setAttribute('data-lang', 'ko');
		script.setAttribute('crossorigin', 'anonymous');
		script.async = true;
		giscusEl.appendChild(script);
	});
</script>

<svelte:head>
	<title>{meta?.title ?? 'Blog'} — DartLab</title>
	{#if meta?.description}
		<meta name="description" content={meta.description} />
	{:else}
		<meta name="description" content="DartLab Blog — {meta?.title ?? ''}" />
	{/if}
</svelte:head>

{#if data.status === 404}
	<div class="not-found">
		<h1>404</h1>
		<p>포스트를 찾을 수 없습니다.</p>
		<a href="{base}/blog/">블로그로 돌아가기</a>
	</div>
{:else}
	<div class="blog-post-layout">
		<div class="blog-post-col">
			<header class="post-header">
				{#if postInfo?.thumbnail}
					<img
						src="{base}{postInfo.thumbnail}"
						alt={meta?.title ?? ''}
						class="post-avatar"
						width="96"
						height="96"
					/>
				{/if}
				{#if postInfo?.date}
					<div class="post-date">
						<Calendar size={13} />
						{new Date(postInfo.date).toLocaleDateString('ko-KR', {
							year: 'numeric',
							month: 'long',
							day: 'numeric'
						})}
					</div>
				{/if}
			</header>

			<article class="blog-article" bind:this={articleEl}>
				{#if Component}
					<Component />
				{/if}
			</article>

			{#if prevNext.prev || prevNext.next}
				<nav class="post-nav">
					{#if prevNext.prev}
						<a href="{base}/blog/{prevNext.prev.slug}" class="post-nav-link prev">
							<span class="post-nav-label"><ChevronLeft size={14} /> 이전 포스트</span>
							<span class="post-nav-title">{prevNext.prev.title}</span>
						</a>
					{:else}
						<div></div>
					{/if}
					{#if prevNext.next}
						<a href="{base}/blog/{prevNext.next.slug}" class="post-nav-link next">
							<span class="post-nav-label">다음 포스트 <ChevronRight size={14} /></span>
							<span class="post-nav-title">{prevNext.next.title}</span>
						</a>
					{:else}
						<div></div>
					{/if}
				</nav>
			{/if}

			<div class="giscus-container" bind:this={giscusEl}></div>

			<footer class="post-footer">
				<a href="{base}/blog/" class="back-link">&larr; 모든 포스트 보기</a>
			</footer>
		</div>

		<aside class="blog-toc">
			{#if tocItems.length > 0}
				<div class="blog-toc-inner">
					<span class="blog-toc-heading">On this page</span>
					<nav class="blog-toc-list">
						{#each tocItems as item}
							<button
								class="blog-toc-item"
								class:h3={item.level === 3}
								class:active={activeId === item.id}
								onclick={() => scrollToHeading(item.id)}
							>
								{item.text}
							</button>
						{/each}
					</nav>
				</div>
			{/if}
		</aside>
	</div>
{/if}

<style>
	.not-found {
		text-align: center;
		padding: 4rem 2rem;
	}
	.not-found h1 {
		font-size: 4rem;
		font-weight: 800;
		background: linear-gradient(135deg, #ea4647, #f87171);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}
	.not-found p { color: #94a3b8; margin: 1rem 0; }
	.not-found a { color: #ea4647; text-decoration: none; }

	.blog-post-layout {
		position: relative;
		max-width: 1280px;
		margin: 0 auto;
		padding: 0 1.5rem;
	}

	.blog-post-col {
		max-width: 1060px;
		margin: 0 auto;
		padding: 0 2rem;
	}

	/* Post header */
	.post-header {
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
		margin-bottom: 2rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}

	.post-avatar {
		width: 96px;
		height: 96px;
		border-radius: 50%;
		border: 2px solid rgba(234, 70, 71, 0.2);
		margin-bottom: 1rem;
	}

	.post-date {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.8rem;
		color: #64748b;
	}

	/* Article typography — mirrors docs layout */
	.blog-article :global(h1) {
		font-size: 2rem;
		font-weight: 800;
		margin-bottom: 0.5rem;
		background: linear-gradient(135deg, #f1f5f9, #94a3b8);
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
		text-align: center;
	}

	.blog-article :global(h2) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-top: 3.5rem;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
		color: #f1f5f9;
	}

	.blog-article :global(h3) {
		font-size: 1.2rem;
		font-weight: 600;
		margin-top: 2.5rem;
		margin-bottom: 0.75rem;
		color: #e2e8f0;
	}

	.blog-article :global(h4) {
		font-size: 1rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: #cbd5e1;
	}

	.blog-article :global(p) {
		line-height: 1.8;
		color: #94a3b8;
		margin-bottom: 1rem;
	}

	.blog-article :global(a) { color: #ea4647; text-decoration: none; }
	.blog-article :global(a:hover) { text-decoration: underline; }

	.blog-article :global(strong) { color: #e2e8f0; }

	.blog-article :global(code:not(pre code)) {
		background: rgba(148, 163, 184, 0.1);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.875em;
		font-family: 'JetBrains Mono', monospace;
		color: #e2e8f0;
	}

	.blog-article :global(pre) {
		background: #0d1117 !important;
		border: 1px solid rgba(30, 36, 51, 0.8);
		border-radius: 8px;
		padding: 1rem;
		overflow-x: auto;
		margin: 1rem 0;
		font-size: 0.85rem;
	}

	.blog-article :global(pre code) {
		background: none !important;
		padding: 0;
		font-family: 'JetBrains Mono', monospace;
	}

	.blog-article :global(ul), .blog-article :global(ol) {
		padding-left: 1.5rem;
		margin-bottom: 1rem;
		color: #94a3b8;
	}

	.blog-article :global(li) {
		line-height: 1.8;
		margin-bottom: 0.25rem;
	}

	.blog-article :global(table) {
		width: 100%;
		border-collapse: collapse;
		margin: 1.5rem 0;
		font-size: 0.875rem;
	}

	.blog-article :global(th) {
		text-align: left;
		padding: 0.75rem 1rem;
		border-bottom: 2px solid rgba(30, 36, 51, 0.8);
		color: #f1f5f9;
		font-weight: 600;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.blog-article :global(td) {
		padding: 0.6rem 1rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.5);
		color: #94a3b8;
	}

	.blog-article :global(tr:hover td) {
		background: rgba(148, 163, 184, 0.03);
	}

	.blog-article :global(blockquote) {
		border-left: 3px solid #ea4647;
		padding: 0.5rem 1rem;
		margin: 1rem 0;
		background: rgba(234, 70, 71, 0.05);
		border-radius: 0 6px 6px 0;
	}

	.blog-article :global(blockquote p) { color: #cbd5e1; margin: 0; }

	.blog-article :global(hr) {
		border: none;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
		margin: 3rem 0;
	}

	.blog-article :global(img) { max-width: 100%; border-radius: 8px; }

	/* Copy button */
	:global(.copy-btn) {
		position: absolute;
		top: 8px;
		right: 8px;
		padding: 4px 10px;
		font-size: 0.7rem;
		font-family: 'JetBrains Mono', monospace;
		background: rgba(148, 163, 184, 0.15);
		color: #94a3b8;
		border: 1px solid rgba(148, 163, 184, 0.2);
		border-radius: 4px;
		cursor: pointer;
		opacity: 0;
		transition: opacity 0.15s, background 0.15s;
		z-index: 1;
	}
	:global(.copy-btn:hover) {
		background: rgba(234, 70, 71, 0.2);
		color: #ea4647;
		border-color: rgba(234, 70, 71, 0.4);
	}
	:global(div:hover > .copy-btn) {
		opacity: 1;
	}

	/* ToC */
	.blog-toc {
		position: fixed;
		top: 72px;
		right: calc((100vw - 1280px) / 2 + 1.5rem);
		width: 200px;
		max-height: calc(100vh - 90px);
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(148, 163, 184, 0.15) transparent;
	}

	.blog-toc-inner { padding-top: 0.5rem; }

	.blog-toc-heading {
		display: block;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: #64748b;
		margin-bottom: 0.6rem;
	}

	.blog-toc-list {
		display: flex;
		flex-direction: column;
	}

	.blog-toc-item {
		display: block;
		width: 100%;
		text-align: left;
		padding: 0.2rem 0 0.2rem 0.6rem;
		font-size: 0.75rem;
		color: #64748b;
		background: none;
		border: none;
		border-left: 2px solid transparent;
		cursor: pointer;
		transition: all 0.12s;
		line-height: 1.4;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.blog-toc-item:hover { color: #cbd5e1; }
	.blog-toc-item.active { color: #ea4647; border-left-color: #ea4647; }
	.blog-toc-item.h3 { padding-left: 1.1rem; font-size: 0.72rem; }

	/* Prev/Next navigation */
	.post-nav {
		display: grid;
		grid-template-columns: 1fr 1fr;
		gap: 1rem;
		margin-top: 3rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
	}

	.post-nav-link {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		padding: 1rem;
		border: 1px solid rgba(30, 36, 51, 0.6);
		border-radius: 8px;
		text-decoration: none;
		transition: all 0.15s;
	}
	.post-nav-link:hover {
		border-color: rgba(234, 70, 71, 0.3);
		background: rgba(234, 70, 71, 0.03);
	}

	.post-nav-link.next { text-align: right; }

	.post-nav-label {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		font-size: 0.75rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
	.post-nav-link.next .post-nav-label { justify-content: flex-end; }

	.post-nav-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: #e2e8f0;
	}
	.post-nav-link:hover .post-nav-title { color: #ea4647; }

	/* Giscus */
	.giscus-container {
		margin-top: 3rem;
		padding-top: 2rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
	}

	/* Footer */
	.post-footer {
		margin-top: 2rem;
		padding-top: 1.5rem;
	}

	.back-link {
		font-size: 0.875rem;
		color: #94a3b8;
		text-decoration: none;
		transition: color 0.15s;
	}
	.back-link:hover { color: #ea4647; }

	@media (max-width: 1400px) {
		.blog-toc { display: none; }
	}

	@media (max-width: 1100px) {
		.blog-post-layout { padding: 0 1rem; }
		.blog-post-col { padding: 0; }
		.post-nav { grid-template-columns: 1fr; }
	}
</style>
