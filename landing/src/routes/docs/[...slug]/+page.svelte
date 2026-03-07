<script lang="ts">
	import { page } from '$app/state';
	import { base } from '$app/paths';
	import { tick } from 'svelte';
	import { findPrevNext } from '$lib/docs/navigation';

	interface TocItem {
		id: string;
		text: string;
		level: number;
	}

	let { data } = $props();
	let articleEl: HTMLElement | undefined = $state();
	let tocItems: TocItem[] = $state([]);
	let activeId = $state('');

	const Component = $derived(data.component);
	const prevNext = $derived(findPrevNext(page.url.pathname));

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
				navigator.clipboard.writeText(code?.textContent ?? '').then(() => {
					btn.textContent = 'Copied!';
					setTimeout(() => {
						btn.textContent = 'Copy';
					}, 2000);
				});
			});
			wrapper.appendChild(btn);
		});
	}

	$effect(() => {
		if (Component && articleEl) {
			tick().then(() => {
				setTimeout(() => {
					extractToc();
					observeHeadings();
					addCopyButtons();
				}, 200);
			});
		}
	});
</script>

<svelte:head>
	<title>{data.metadata?.title ?? 'Docs'} — DartLab 전자공시 분석</title>
	{#if data.metadata?.description}
		<meta name="description" content={data.metadata.description} />
	{:else}
		<meta name="description" content="DartLab {data.metadata?.title ?? ''} — DART 전자공시 문서 분석 Python 라이브러리 문서." />
	{/if}
</svelte:head>

<div class="doc-page">
	<article class="doc-article" bind:this={articleEl}>
		{#if Component}
			<Component />
		{/if}
	</article>

	{#if tocItems.length > 0}
		<aside class="doc-toc">
			<p class="toc-title">목차</p>
			<ul>
				{#each tocItems as item}
					<li class:toc-h3={item.level === 3}>
						<a
							href="#{item.id}"
							class:active={activeId === item.id}
						>{item.text}</a>
					</li>
				{/each}
			</ul>
		</aside>
	{/if}
</div>

{#if prevNext.prev || prevNext.next}
	<nav class="doc-pagination">
		{#if prevNext.prev}
			<a href="{base}{prevNext.prev.href}" class="prev">
				<span class="label">이전</span>
				<span class="title">{prevNext.prev.title}</span>
			</a>
		{:else}
			<div></div>
		{/if}
		{#if prevNext.next}
			<a href="{base}{prevNext.next.href}" class="next">
				<span class="label">다음</span>
				<span class="title">{prevNext.next.title}</span>
			</a>
		{/if}
	</nav>
{/if}

<style>
	.doc-page {
		display: grid;
		grid-template-columns: 1fr 200px;
		gap: 2rem;
		max-width: 1100px;
		margin: 0 auto;
		padding: 2rem 1.5rem;
	}

	.doc-article {
		min-width: 0;
		overflow-wrap: break-word;
	}

	:global(.doc-article h1) {
		font-size: 2rem;
		font-weight: 700;
		margin-bottom: 1rem;
		color: #fafaf9;
	}
	:global(.doc-article h2) {
		font-size: 1.5rem;
		font-weight: 600;
		margin-top: 2.5rem;
		margin-bottom: 0.75rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #292524;
		color: #fafaf9;
	}
	:global(.doc-article h3) {
		font-size: 1.2rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: #fafaf9;
	}
	:global(.doc-article p) {
		margin: 0.75rem 0;
		line-height: 1.75;
		color: #d6d3d1;
	}
	:global(.doc-article a) {
		color: #f59e0b;
		text-decoration: underline;
		text-underline-offset: 2px;
	}
	:global(.doc-article a:hover) {
		color: #fbbf24;
	}
	:global(.doc-article ul),
	:global(.doc-article ol) {
		margin: 0.75rem 0;
		padding-left: 1.5rem;
		color: #d6d3d1;
	}
	:global(.doc-article li) {
		margin: 0.25rem 0;
		line-height: 1.75;
	}
	:global(.doc-article code) {
		font-family: 'JetBrains Mono', 'Fira Code', ui-monospace, monospace;
		font-size: 0.875rem;
		background: #1c1917;
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		color: #fbbf24;
	}
	:global(.doc-article pre) {
		margin: 1rem 0;
		padding: 1rem;
		border-radius: 8px;
		overflow-x: auto;
		font-size: 0.875rem;
		line-height: 1.6;
		border: 1px solid #292524;
	}
	:global(.doc-article pre code) {
		background: none;
		padding: 0;
		color: inherit;
	}
	:global(.doc-article table) {
		width: 100%;
		margin: 1rem 0;
		border-collapse: collapse;
	}
	:global(.doc-article th),
	:global(.doc-article td) {
		padding: 0.5rem 0.75rem;
		border: 1px solid #292524;
		text-align: left;
		color: #d6d3d1;
	}
	:global(.doc-article th) {
		background: #1c1917;
		font-weight: 600;
		color: #fafaf9;
	}
	:global(.doc-article blockquote) {
		margin: 1rem 0;
		padding: 0.75rem 1rem;
		border-left: 3px solid #f59e0b;
		background: #1c1917;
		border-radius: 0 6px 6px 0;
		color: #d6d3d1;
	}
	:global(.doc-article hr) {
		border: none;
		border-top: 1px solid #292524;
		margin: 2rem 0;
	}

	:global(.copy-btn) {
		position: absolute;
		top: 0.5rem;
		right: 0.5rem;
		padding: 0.25rem 0.5rem;
		font-size: 0.75rem;
		background: #292524;
		color: #a8a29e;
		border: 1px solid #44403c;
		border-radius: 4px;
		cursor: pointer;
		opacity: 0;
		transition: opacity 0.2s;
	}
	:global(div:hover > .copy-btn) {
		opacity: 1;
	}
	:global(.copy-btn:hover) {
		background: #44403c;
		color: #fafaf9;
	}

	.doc-toc {
		position: sticky;
		top: 5rem;
		max-height: calc(100vh - 6rem);
		overflow-y: auto;
		font-size: 0.8rem;
	}
	.toc-title {
		font-weight: 600;
		color: #a8a29e;
		margin-bottom: 0.5rem;
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.05em;
	}
	.doc-toc ul {
		list-style: none;
		padding: 0;
		margin: 0;
	}
	.doc-toc li {
		margin: 0.15rem 0;
	}
	.toc-h3 {
		padding-left: 1rem;
	}
	.doc-toc a {
		color: #78716c;
		text-decoration: none;
		transition: color 0.15s;
		display: block;
		padding: 0.15rem 0;
	}
	.doc-toc a:hover {
		color: #d6d3d1;
	}
	.doc-toc a.active {
		color: #f59e0b;
	}

	.doc-pagination {
		display: flex;
		justify-content: space-between;
		max-width: 1100px;
		margin: 2rem auto;
		padding: 0 1.5rem 2rem;
		gap: 1rem;
	}
	.doc-pagination a {
		display: flex;
		flex-direction: column;
		padding: 1rem 1.25rem;
		border: 1px solid #292524;
		border-radius: 8px;
		text-decoration: none;
		transition: border-color 0.2s;
		min-width: 0;
	}
	.doc-pagination a:hover {
		border-color: #f59e0b;
	}
	.doc-pagination .prev {
		align-items: flex-start;
	}
	.doc-pagination .next {
		align-items: flex-end;
		margin-left: auto;
	}
	.doc-pagination .label {
		font-size: 0.75rem;
		color: #78716c;
	}
	.doc-pagination .title {
		color: #f59e0b;
		font-weight: 500;
	}

	@media (max-width: 1024px) {
		.doc-page {
			grid-template-columns: 1fr;
		}
		.doc-toc {
			display: none;
		}
	}
</style>
