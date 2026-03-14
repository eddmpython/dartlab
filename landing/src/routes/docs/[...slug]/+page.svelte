<script lang="ts">
	import { base } from '$app/paths';
	import { page } from '$app/state';
	import { brand } from '$lib/brand';
	import { findPrevNext } from '$lib/docs/navigation';
	import {
		buildAbsoluteUrl,
		buildArticleJsonLd,
		buildBreadcrumbJsonLd,
		buildFaqJsonLd,
		buildOrganizationJsonLd,
		buildPersonJsonLd,
		parseFaqFromMarkdown
	} from '$lib/seo';
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';
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

		const observer = new IntersectionObserver((entries) => {
			for (const entry of entries) {
				if (entry.isIntersecting) {
					activeId = entry.target.id;
					break;
				}
			}
		}, { rootMargin: '-80px 0px -70% 0px', threshold: 0 });

		headings.forEach(h => observer.observe(h));
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
					setTimeout(() => { btn.textContent = 'Copy'; }, 2000);
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
	const prevNext = $derived(findPrevNext(page.url.pathname));
	const pageTitle = $derived(`${meta?.title ?? 'Docs'} — DartLab 전자공시 문서`);
	const pageDesc = $derived(meta?.description ?? `DartLab ${meta?.title ?? ''} 문서. DART 전자공시 데이터와 사용 예제를 설명합니다.`);
	const pageUrl = $derived(buildAbsoluteUrl(`docs/${data.slug}`));
	const pageImage = buildAbsoluteUrl('og-image.png');
	const docType = $derived(data.slug === 'about' ? 'AboutPage' : 'TechArticle');
	const docKeywords = $derived(
		['전자공시', 'DART', 'OpenDART', meta?.title ?? '', data.slug?.startsWith('api/') ? 'API reference' : 'tutorial'].filter(Boolean)
	);
	const faqItems = $derived(parseFaqFromMarkdown(data.rawMarkdown ?? ''));
	const docJsonLd = $derived(
		JSON.stringify([
			buildArticleJsonLd({
				type: docType,
				title: meta?.title ?? 'Docs',
				description: pageDesc,
				url: pageUrl,
				image: pageImage,
				section: data.slug?.split('/')[0] ?? 'docs',
				keywords: docKeywords
			}),
			buildBreadcrumbJsonLd([
				{ name: 'DartLab', url: brand.url },
				{ name: 'Docs', url: buildAbsoluteUrl('docs/') },
				{ name: meta?.title ?? 'Docs', url: pageUrl }
			]),
			...(faqItems.length > 0 ? [buildFaqJsonLd(faqItems)] : []),
			...(data.slug === 'about' ? [buildOrganizationJsonLd(), buildPersonJsonLd()] : [])
		])
	);

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
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="article" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content={pageImage} />
	<meta property="og:locale" content="ko_KR" />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDesc} />
	<meta name="twitter:image" content={pageImage} />
	{@html `<script type="application/ld+json">${docJsonLd}</script>`}
</svelte:head>

{#if data.status === 404}
	<div class="not-found">
		<h1>404</h1>
		<p>페이지를 찾을 수 없습니다.</p>
		<a href="{base}/docs/">문서 홈으로</a>
	</div>
{:else}
	<div class="doc-layout">
		<div class="doc-content-col">
			{#if meta?.description}
				<section class="doc-summary" aria-label="문서 핵심 요약">
					<span class="doc-summary-kicker">Quick Summary</span>
					<p>{meta.description}</p>
				</section>
			{/if}

			<article class="doc-article" bind:this={articleEl}>
				{#if Component}
					<Component />
				{/if}
			</article>

			{#if prevNext.prev || prevNext.next}
				<nav class="doc-pagination">
					{#if prevNext.prev}
						<a href="{base}{prevNext.prev.href}" class="doc-pagination-link prev">
							<ChevronLeft size={16} />
							<div>
								<span class="doc-pagination-label">이전</span>
								<span class="doc-pagination-title">{prevNext.prev.title}</span>
							</div>
						</a>
					{:else}
						<div></div>
					{/if}
					{#if prevNext.next}
						<a href="{base}{prevNext.next.href}" class="doc-pagination-link next">
							<div>
								<span class="doc-pagination-label">다음</span>
								<span class="doc-pagination-title">{prevNext.next.title}</span>
							</div>
							<ChevronRight size={16} />
						</a>
					{/if}
				</nav>
			{/if}
		</div>

		{#if tocItems.length > 0}
			<aside class="doc-toc">
				<div class="doc-toc-inner">
					<span class="doc-toc-heading">On this page</span>
					<nav class="doc-toc-list">
						{#each tocItems as item}
							<button
								class="doc-toc-item"
								class:h3={item.level === 3}
								class:active={activeId === item.id}
								onclick={() => scrollToHeading(item.id)}
							>
								{item.text}
							</button>
						{/each}
					</nav>
				</div>
			</aside>
		{/if}
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
	.not-found p { color: #a8a29e; margin: 1rem 0; }
	.not-found a { color: #ea4647; text-decoration: none; }

	.doc-layout {
		display: grid;
		grid-template-columns: minmax(0, var(--content-max-width)) var(--toc-width);
		gap: 2rem;
		justify-content: center;
		align-items: start;
	}

	.doc-content-col {
		min-width: 0;
	}

	.doc-summary {
		margin: 0 0 1.5rem;
		padding: 1rem 1.1rem;
		border-radius: 14px;
		border: 1px solid rgba(234, 70, 71, 0.22);
		background: linear-gradient(135deg, rgba(234, 70, 71, 0.12), rgba(15, 18, 25, 0.96));
		box-shadow: 0 18px 40px rgba(3, 5, 9, 0.26);
	}

	.doc-summary-kicker {
		display: inline-block;
		margin-bottom: 0.45rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #fdba74;
	}

	.doc-summary p {
		margin: 0;
		font-size: 0.95rem;
		line-height: 1.7;
		color: #e2e8f0;
	}

	.doc-toc {
		position: sticky;
		top: 72px;
		height: fit-content;
		max-height: calc(100vh - 90px);
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(148, 163, 184, 0.15) transparent;
	}

	.doc-toc-inner {
		padding-top: 0.5rem;
		border-left: 1px solid rgba(30, 36, 51, 0.8);
		padding-left: 1rem;
	}

	.doc-toc-heading {
		display: block;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: #64748b;
		margin-bottom: 0.6rem;
	}

	.doc-toc-list {
		display: flex;
		flex-direction: column;
	}

	.doc-toc-item {
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

	.doc-toc-item:hover {
		color: #cbd5e1;
	}

	.doc-toc-item.active {
		color: #ea4647;
		border-left-color: #ea4647;
	}

	.doc-toc-item.h3 {
		padding-left: 1.1rem;
		font-size: 0.72rem;
	}

	:global(.copy-btn) {
		position: absolute;
		top: 8px;
		right: 8px;
		padding: 4px 10px;
		font-size: 0.7rem;
		font-family: 'JetBrains Mono', monospace;
		background: rgba(168, 162, 158, 0.15);
		color: #a8a29e;
		border: 1px solid rgba(168, 162, 158, 0.2);
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

	.doc-pagination {
		display: flex;
		justify-content: space-between;
		gap: 1rem;
		margin-top: 3rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(168, 162, 158, 0.1);
	}

	.doc-pagination-link {
		display: flex;
		align-items: center;
		gap: 0.75rem;
		padding: 0.75rem 1rem;
		border-radius: 8px;
		border: 1px solid rgba(168, 162, 158, 0.1);
		text-decoration: none;
		color: #a8a29e;
		transition: all 0.15s;
		max-width: 45%;
	}

	.doc-pagination-link:hover {
		border-color: #ea4647;
		color: #ea4647;
	}

	.doc-pagination-link.next {
		margin-left: auto;
		text-align: right;
	}

	.doc-pagination-label {
		display: block;
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		color: #78716c;
	}

	.doc-pagination-title {
		display: block;
		font-size: 0.9rem;
		font-weight: 500;
	}

	@media (max-width: 1200px) {
		.doc-layout {
			grid-template-columns: 1fr;
		}
		.doc-toc {
			display: none;
		}
	}
</style>
