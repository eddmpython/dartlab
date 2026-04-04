<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import { findPrevNext, findSeriesPrevNext, getCategoryPath, getPost, getRelatedPostsByCategory, getSeriesPath } from '$lib/blog/posts';
	import { buildAbsoluteUrl, buildArticleJsonLd, buildBreadcrumbJsonLd, buildFaqJsonLd, parseFaqFromMarkdown } from '$lib/seo';
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
	let tocVisible = $state(true);
	let footerEl: HTMLElement | undefined = $state();

	function observeFooter() {
		if (!footerEl) return;
		const observer = new IntersectionObserver(
			(entries) => {
				for (const entry of entries) {
					tocVisible = !entry.isIntersecting;
				}
			},
			{ threshold: 0 }
		);
		observer.observe(footerEl);
		return () => observer.disconnect();
	}

	let footerCleanup: (() => void) | undefined;

	onMount(() => {
		mounted = true;
		return () => {
			mounted = false;
			cleanup?.();
			footerCleanup?.();
		};
	});

	const Component = $derived(data.component);
	const meta = $derived(data.metadata ?? {});
	const postInfo = $derived(getPost(data.slug));
	const prevNext = $derived(findPrevNext(data.slug));
	const seriesPrevNext = $derived(findSeriesPrevNext(data.slug));
	const relatedCategoryPosts = $derived(getRelatedPostsByCategory(data.slug, 3));

	const pageTitle = $derived(`${meta?.title ?? 'Blog'} — DartLab 전자공시 분석`);
	const pageDesc = $derived(meta?.description ?? `DartLab Blog — ${meta?.title ?? ''}`);
	const pageUrl = $derived(`${brand.url}blog/${data.slug}`);
	const pageImage = $derived(postInfo?.thumbnail ? `${brand.url}${postInfo.thumbnail.replace(/^\//, '')}` : `${brand.url}og-image.png`);
	const faqItems = $derived(parseFaqFromMarkdown(data.rawMarkdown ?? ''));
	const jsonLd = $derived(
		JSON.stringify([
			buildArticleJsonLd({
				type: 'BlogPosting',
				title: meta?.title ?? '',
				description: pageDesc,
				url: pageUrl,
				image: pageImage,
				datePublished: postInfo?.date ?? '',
				section: postInfo?.categoryLabel ?? '',
				keywords: [postInfo?.categoryLabel, postInfo?.seriesLabel, ...(meta?.keywords ?? []), '전자공시', 'DartLab'].filter(Boolean),
				isPartOf: postInfo ? `${brand.url}blog/category/${postInfo.category}` : `${brand.url}blog/`
			}),
			buildBreadcrumbJsonLd([
				{ name: 'DartLab', url: brand.url },
				{ name: 'Blog', url: buildAbsoluteUrl('blog/') },
				{ name: meta?.title ?? 'Blog', url: pageUrl }
			]),
			...(faqItems.length > 0 ? [buildFaqJsonLd(faqItems)] : [])
		])
	);

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
			footerCleanup?.();
			footerCleanup = observeFooter();
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
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="article" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content={pageImage} />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />
	{#if postInfo?.date}
		<meta property="article:published_time" content={postInfo.date} />
	{/if}
	<meta property="article:author" content="eddmpython" />
	<meta name="keywords" content={[postInfo?.categoryLabel, postInfo?.seriesLabel, ...(meta?.keywords ?? []), '전자공시', 'DartLab', 'DART'].filter(Boolean).join(', ')} />
	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={pageTitle} />
	<meta name="twitter:description" content={pageDesc} />
	<meta name="twitter:image" content={pageImage} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
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
					<picture>
						<source srcset="{base}{postInfo.thumbnail.replace('.png', '.webp')}" type="image/webp" />
						<img
							src="{base}{postInfo.thumbnail}"
							alt={meta?.title ?? ''}
							class="post-avatar"
							width="96"
							height="96"
							loading="lazy"
							decoding="async"
						/>
					</picture>
				{/if}
				{#if postInfo}
					<div class="post-meta-row">
						<a href="{base}{getCategoryPath(postInfo.category)}" class="post-badge">{postInfo.categoryLabel}</a>
						{#if postInfo.seriesLabel}
							<a href="{base}{getSeriesPath(postInfo.series)}" class="post-series">
								{postInfo.seriesLabel}
								{#if postInfo.seriesOrder}
									<span class="post-series-order">#{postInfo.seriesOrder}</span>
								{/if}
							</a>
						{/if}
					</div>
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
				{#if meta?.description}
					<div class="post-summary" aria-label="포스트 핵심 요약">
						<span class="post-summary-kicker">Quick Summary</span>
						<p>{meta.description}</p>
					</div>
				{/if}
			</header>

			<article class="blog-article" bind:this={articleEl}>
				{#if Component}
					<Component />
				{/if}
			</article>

			{#if seriesPrevNext.prev || seriesPrevNext.next}
				<section class="series-nav">
					<div class="series-nav-heading">같은 시리즈에서 이어 읽기</div>
					<div class="series-nav-grid">
						{#if seriesPrevNext.prev}
							<a href="{base}/blog/{seriesPrevNext.prev.slug}" class="series-card">
								<span class="series-card-label">이전 시리즈 글</span>
								<span class="series-card-title">{seriesPrevNext.prev.title}</span>
							</a>
						{/if}
						{#if seriesPrevNext.next}
							<a href="{base}/blog/{seriesPrevNext.next.slug}" class="series-card">
								<span class="series-card-label">다음 시리즈 글</span>
								<span class="series-card-title">{seriesPrevNext.next.title}</span>
							</a>
						{/if}
					</div>
				</section>
			{/if}

			{#if relatedCategoryPosts.length > 0}
				<section class="brand-loop">
					<div class="brand-loop-copy">
						<div class="brand-loop-kicker">DartLab</div>
						<h2 class="brand-loop-title">같은 카테고리에서 더 읽기</h2>
						<p class="brand-loop-desc">
							DartLab은 {postInfo?.categoryLabel} 카테고리 안에서 글이 서로 이어지도록 설계합니다.
							다음 글로 넘어가며 구조와 맥락을 같이 쌓는 방식입니다.
						</p>
					</div>
					<div class="brand-loop-links">
						{#each relatedCategoryPosts as post}
							<a href="{base}/blog/{post.slug}" class="brand-loop-card">
								<span class="brand-loop-card-series">{post.seriesLabel ?? post.categoryLabel}</span>
								<span class="brand-loop-card-title">{post.title}</span>
							</a>
						{/each}
					</div>
				</section>
			{/if}

			<section class="product-bridge">
				<div class="product-bridge-copy">
					<div class="product-bridge-kicker">DartLab Product</div>
					<h2 class="product-bridge-title">이 글의 판단을 실제 데이터 흐름으로 옮기기</h2>
					<p class="product-bridge-desc">
						DartLab은 전자공시를 읽는 법을 코드와 데이터로 연결하기 위해 만든 제품입니다.
						사업보고서 텍스트, 재무 시계열, 정기보고서 데이터를 한 흐름에서 다루도록 설계했습니다.
					</p>
				</div>
				<div class="product-bridge-links">
					<a href="{base}/docs/getting-started/quickstart" class="product-bridge-link primary">Quickstart</a>
					<a href="{base}/docs/getting-started/installation" class="product-bridge-link">설치 가이드</a>
					<a href="{base}/docs/api/overview" class="product-bridge-link">API Overview</a>
					<a href="{base}/docs/tutorials/disclosure" class="product-bridge-link">공시 텍스트 튜토리얼</a>
				</div>
			</section>

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

			<footer class="post-footer" bind:this={footerEl}>
				<a href="{base}/blog/" class="back-link">&larr; 모든 포스트 보기</a>
			</footer>
		</div>

		<aside class="blog-toc" class:toc-hidden={!tocVisible}>
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
		--content-max-width: 860px;
		--toc-width: 200px;
		position: relative;
		max-width: calc(var(--content-max-width) + var(--toc-width) + 2rem);
		margin: 0 auto;
		padding: 0;
		display: grid;
		grid-template-columns: minmax(0, var(--content-max-width)) var(--toc-width);
		gap: 2rem;
		justify-content: center;
		align-items: start;
	}

	.blog-post-col {
		min-width: 0;
		max-width: none;
		margin: 0;
		padding: 0;
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

	.post-summary {
		width: min(100%, 720px);
		margin-top: 1rem;
		padding: 1rem 1.1rem;
		border-radius: 14px;
		border: 1px solid rgba(234, 70, 71, 0.22);
		background: linear-gradient(135deg, rgba(234, 70, 71, 0.12), rgba(15, 18, 25, 0.96));
		box-shadow: 0 18px 40px rgba(3, 5, 9, 0.24);
	}

	.post-summary-kicker {
		display: inline-block;
		margin-bottom: 0.45rem;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #fdba74;
	}

	.post-summary p {
		margin: 0;
		font-size: 0.98rem;
		line-height: 1.7;
		color: #e2e8f0;
	}

	.post-avatar {
		width: 96px;
		height: 96px;
		border-radius: 50%;
		border: 2px solid rgba(234, 70, 71, 0.2);
		margin-bottom: 1rem;
	}

	.post-meta-row {
		display: flex;
		flex-wrap: wrap;
		justify-content: center;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.post-badge,
	.post-series {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.35rem 0.7rem;
		border-radius: 999px;
		font-size: 0.72rem;
		font-weight: 700;
		letter-spacing: 0.04em;
		text-transform: uppercase;
	}

	.post-badge {
		background: rgba(234, 70, 71, 0.12);
		border: 1px solid rgba(234, 70, 71, 0.24);
		color: #fda4a4;
		text-decoration: none;
	}

	.post-series {
		background: rgba(148, 163, 184, 0.08);
		border: 1px solid rgba(148, 163, 184, 0.14);
		color: #cbd5e1;
		text-decoration: none;
	}

	.post-series-order {
		color: #94a3b8;
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
		margin-bottom: 2rem;
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
		display: table;
		width: 100%;
		max-width: 100%;
		table-layout: fixed;
		border-collapse: separate;
		border-spacing: 0;
		margin: 1.75rem 0;
		font-size: 0.9rem;
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0)),
			rgba(15, 18, 25, 0.92);
		border: 1px solid rgba(30, 36, 51, 0.95);
		border-radius: 18px;
		box-shadow:
			0 18px 40px rgba(3, 5, 9, 0.28),
			inset 0 1px 0 rgba(255, 255, 255, 0.03);
		-webkit-overflow-scrolling: touch;
	}

	.blog-article :global(table tbody),
	.blog-article :global(table thead) {
		width: auto;
	}

	.blog-article :global(thead) {
		background: linear-gradient(180deg, rgba(234, 70, 71, 0.12), rgba(234, 70, 71, 0.04));
	}

	.blog-article :global(th) {
		text-align: left;
		padding: 0.95rem 1rem;
		border-bottom: 1px solid rgba(234, 70, 71, 0.18);
		color: #f1f5f9;
		font-weight: 700;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		white-space: nowrap;
	}

	.blog-article :global(td) {
		padding: 0.85rem 1rem;
		border-bottom: 1px solid rgba(30, 36, 51, 0.72);
		color: #cbd5e1;
		background: rgba(255, 255, 255, 0.01);
		vertical-align: top;
	}

	.blog-article :global(tbody tr:last-child td) {
		border-bottom: none;
	}

	.blog-article :global(th:first-child) {
		border-top-left-radius: 18px;
	}

	.blog-article :global(th:last-child) {
		border-top-right-radius: 18px;
	}

	.blog-article :global(tbody tr:last-child td:first-child) {
		border-bottom-left-radius: 18px;
	}

	.blog-article :global(tbody tr:last-child td:last-child) {
		border-bottom-right-radius: 18px;
	}

	.blog-article :global(tr:hover td) {
		background: rgba(148, 163, 184, 0.05);
	}

	.blog-article :global(td strong), .blog-article :global(th strong) {
		color: #f8fafc;
	}

	.blog-article :global(caption) {
		caption-side: top;
		text-align: left;
		padding: 0 0.25rem 0.75rem;
		font-size: 0.78rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: #64748b;
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

	.blog-article :global(img) { max-width: 100%; border-radius: 8px; display: block; margin: 1.5rem auto; }
	.blog-article :global(svg),
	.blog-article :global(canvas),
	.blog-article :global(iframe) {
		max-width: 100%;
	}

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

	.blog-toc {
		position: sticky;
		top: 72px;
		width: var(--toc-width);
		height: fit-content;
		max-height: calc(100vh - 90px);
		overflow-y: auto;
		scrollbar-width: thin;
		scrollbar-color: rgba(148, 163, 184, 0.15) transparent;
		transition: opacity 0.2s;
	}

	.blog-toc.toc-hidden {
		opacity: 0;
		pointer-events: none;
		transition: opacity 0.2s;
	}

	.blog-toc-inner {
		padding-top: 0.5rem;
		padding-left: 1rem;
		border-left: 1px solid rgba(30, 36, 51, 0.8);
	}

	.blog-toc-heading {
		display: block;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: #64748b;
		margin-bottom: 0;
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

	.brand-loop {
		margin-top: 3rem;
		padding-top: 1.6rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
	}

	.brand-loop-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.4rem;
	}

	.brand-loop-title {
		font-size: 1.2rem;
		font-weight: 800;
		color: #f8fafc;
		margin-bottom: 0.5rem;
	}

	.brand-loop-desc {
		color: #94a3b8;
		line-height: 1.75;
		margin-bottom: 1rem;
	}

	.brand-loop-links {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.85rem;
	}

	.brand-loop-card {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 0.95rem 1rem;
		border-radius: 12px;
		border: 1px solid rgba(30, 36, 51, 0.7);
		background: rgba(15, 18, 25, 0.75);
		text-decoration: none;
	}

	.brand-loop-card-series {
		font-size: 0.7rem;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 700;
	}

	.brand-loop-card-title {
		font-size: 0.94rem;
		font-weight: 700;
		color: #e2e8f0;
	}

	.series-nav {
		margin-top: 3rem;
		padding-top: 1.5rem;
		border-top: 1px solid rgba(30, 36, 51, 0.8);
	}

	.series-nav-heading {
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: #64748b;
		margin-bottom: 0.85rem;
	}

	.series-nav-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 0.9rem;
	}

	.series-card {
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		padding: 1rem;
		border-radius: 12px;
		border: 1px solid rgba(30, 36, 51, 0.7);
		background: rgba(15, 18, 25, 0.75);
		text-decoration: none;
		transition: border-color 0.15s, transform 0.15s;
	}

	.series-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
		transform: translateY(-1px);
	}

	.series-card-label {
		font-size: 0.72rem;
		color: #64748b;
	}

	.series-card-title {
		font-size: 0.95rem;
		font-weight: 700;
		color: #e2e8f0;
	}

	.product-bridge {
		margin-top: 3rem;
		padding: 1.5rem;
		border-radius: 18px;
		border: 1px solid rgba(234, 70, 71, 0.16);
		background:
			linear-gradient(135deg, rgba(234, 70, 71, 0.08), rgba(251, 146, 60, 0.04)),
			rgba(15, 18, 25, 0.94);
	}

	.product-bridge-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: #ea4647;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.4rem;
	}

	.product-bridge-title {
		font-size: 1.2rem;
		font-weight: 800;
		color: #f8fafc;
		margin-bottom: 0.5rem;
	}

	.product-bridge-desc {
		color: #cbd5e1;
		line-height: 1.75;
	}

	.product-bridge-links {
		display: flex;
		flex-wrap: wrap;
		gap: 0.7rem;
		margin-top: 1rem;
	}

	.product-bridge-link {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		padding: 0.72rem 1rem;
		border-radius: 999px;
		border: 1px solid rgba(148, 163, 184, 0.16);
		background: rgba(148, 163, 184, 0.06);
		color: #e2e8f0;
		text-decoration: none;
		font-weight: 700;
	}

	.product-bridge-link.primary {
		background: rgba(234, 70, 71, 0.14);
		border-color: rgba(234, 70, 71, 0.28);
		color: #fda4a4;
	}

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

	@media (max-width: 1200px) {
		.blog-toc { display: none; }
		.blog-post-layout {
			max-width: min(var(--content-max-width), 100%);
			grid-template-columns: 1fr;
		}
	}

	@media (max-width: 1100px) {
		.brand-loop-links { grid-template-columns: 1fr; }
		.series-nav-grid { grid-template-columns: 1fr; }
		.post-nav { grid-template-columns: 1fr; }
	}

	@media (max-width: 480px) {
		.post-header {
			margin-bottom: 1.5rem;
			padding-bottom: 1.25rem;
		}
	}
</style>
