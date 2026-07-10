<script lang="ts">
	import { base } from '$app/paths';
	import { brand } from '$lib/brand';
	import SubjectHub from '$lib/subjects/SubjectHub.svelte';
	import BlogActionBar from '$lib/blog/BlogActionBar.svelte';
	import { findPrevNext, findSeriesPrevNext, getCategoryPath, getPost, getPostRaw, getRelatedPostsByCategory, getSeriesPath } from '$lib/blog/posts';
	import { buildAbsoluteUrl, buildArticleJsonLd, buildBreadcrumbJsonLd, buildFaqJsonLd, parseFaqFromMarkdown } from '$lib/seo';
	import { Calendar, ChevronLeft, ChevronRight } from 'lucide-svelte';
	import { goto } from '$app/navigation';
	import { mount, onMount, setContext, tick, unmount } from 'svelte';
	import RunnableCode from '$lib/blog/RunnableCode.svelte';
	import { markdownToNotebook, postNotebookId } from '$lib/notebook/fromMarkdown';
	import { getNotebook, putNotebook } from '$lib/notebook/storage/localStore';

	let { data } = $props();

	// 회사글 재무(빌드타임 SSOT) 를 마크다운 내 <CompanyFinancials> 에 context 로 전달 · getter 라 client 네비게이션에도 반응.
	// 라이브 테이블은 분기 기준(companyQuarter) 이 먼저, 5개년 궤적(companyFinance) 은 컨텍스트.
	setContext('blogCompanyFinance', () => data.companyFinance);
	setContext('blogCompanyQuarter', () => data.companyQuarter);

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
		const headings = articleEl.querySelectorAll('h1, h2');
		const items: TocItem[] = [];
		headings.forEach((h) => {
			if (!h.id) {
				h.id = (h.textContent ?? '')
					.trim()
					.toLowerCase()
					.replace(/[^a-z0-9가-힣]+/g, '-')
					.replace(/(^-|-$)/g, '');
			}
			const text = (h.textContent ?? '').trim();
			items.push({
				id: h.id,
				text,
				level: h.tagName === 'H1' ? 1 : 2
			});
		});
		tocItems = items;
	}

	function observeHeadings() {
		if (!articleEl) return;
		const headings = articleEl.querySelectorAll('h1, h2');
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

	/**
	 * dartlab 이야기 본문의 python 블록을 실행 셀로 승격시킨다.
	 *
	 * 코드 원본은 markdown 코드펜스 하나뿐이고, 여기서는 그 아래에 실행 막대만 붙인다. 셀을 따로
	 * 굽지 않으므로 글을 고치면 실행되는 코드도 함께 바뀐다. 다른 카테고리 글의 코드블록은 읽는
	 * 예시라 손대지 않는다.
	 */
	function mountRunnableCells() {
		if (!articleEl || postInfo?.category !== 'dartlab-stories') return;
		const blocks = [...articleEl.querySelectorAll<HTMLElement>('pre[data-lang="python"]')];
		const codes = blocks.map((pre) => pre.textContent ?? '');
		blocks.forEach((pre, i) => {
			const host = pre.parentElement as HTMLElement | null;
			if (!host || host.dataset.runnable) return;
			host.dataset.runnable = '1';
			const target = document.createElement('div');
			host.after(target);
			runnables.push(
				mount(RunnableCode, {
					target,
					props: {
						code: codes[i],
						// 글 순서가 곧 실행 순서다. 중간 셀을 먼저 눌러도 앞 셀이 알아서 선행 실행된다.
						prereq: codes.slice(0, i),
						onOpenNotebook: i === 0 ? openAsNotebook : undefined
					}
				})
			);
		});
	}

	/** 이 글을 노트북 하나로. 글마다 안정 id 라 두 번 눌러도 사본이 늘지 않고 하던 곳으로 간다. */
	async function openAsNotebook() {
		const raw = getPostRaw(slug);
		if (!raw) return;
		const id = postNotebookId(slug);
		if (!(await getNotebook(id))) {
			await putNotebook(markdownToNotebook(raw, slug, postInfo?.title ?? slug, postInfo?.description ?? ''));
		}
		await goto(`${base}/notebooks/${id}`);
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
	let runnables: Record<string, unknown>[] = [];
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
			runnables.forEach((c) => void unmount(c));
			runnables = [];
		};
	});

	const Component = $derived(data.component);
	const meta = $derived(data.metadata ?? {});
	const slug = $derived(data.slug ?? '');
	const postInfo = $derived(getPost(slug));
	const prevNext = $derived(findPrevNext(slug));
	const seriesPrevNext = $derived(findSeriesPrevNext(slug));
	const relatedCategoryPosts = $derived(getRelatedPostsByCategory(slug, 3));
	// 주제 허브 join 키 · 회사글=stockCode, 주제글=topicSlug(프론트매터). 관련 팟캐스트 슬롯 채움(없으면 미표시).
	const subjectCode = $derived(String((meta as Record<string, unknown>)?.stockCode ?? '').trim());
	const subjectTopic = $derived(String((meta as Record<string, unknown>)?.topicSlug ?? '').trim());

	const pageTitle = $derived(`${meta?.title ?? 'Blog'} · DartLab 전자공시 분석`);
	const pageDesc = $derived(meta?.description ?? `DartLab Blog · ${meta?.title ?? ''}`);
	const pageUrl = $derived(`${brand.url}blog/${slug}`);
	const pageImage = $derived(
		postInfo?.ogImage ? `${brand.url}${postInfo.ogImage.replace(/^\//, '')}` :
		postInfo?.thumbnail ? `${brand.url}${postInfo.thumbnail.replace(/^\//, '')}` :
		`${brand.url}og-image.png`
	);
	const faqItems = $derived(parseFaqFromMarkdown(data.rawMarkdown ?? ''));
	// frontmatter tags 파싱: YAML 배열은 mdsvex가 string으로 줄 수 있음 → 둘 다 처리
	const frontmatterTags = $derived((() => {
		const t: unknown = (meta as Record<string, unknown>)?.tags;
		if (Array.isArray(t)) return t.map(String);
		if (typeof t === 'string') return t.split(/[,\n]/).map((s) => s.trim().replace(/^[-"']|["']$/g, '')).filter(Boolean);
		return [] as string[];
	})());
	const allKeywords = $derived(
		Array.from(new Set([
			postInfo?.categoryLabel,
			postInfo?.seriesLabel,
			...frontmatterTags,
			...(((meta as Record<string, unknown>)?.keywords as string[] | undefined) ?? []),
			'전자공시',
			'DartLab',
			'DART',
		].filter(Boolean) as string[]))
	);
	// 본문 단어 수 추정 (Article schema wordCount)
	const wordCount = $derived((() => {
		const raw = data.rawMarkdown ?? '';
		const cleaned = raw
			.replace(/^---[\s\S]*?---/, '')
			.replace(/```[\s\S]*?```/g, ' ')
			.replace(/!\[[^\]]*\]\([^)]+\)/g, ' ')
			.replace(/\[[^\]]+\]\([^)]+\)/g, ' ')
			.replace(/[#>*`|_-]/g, ' ');
		return cleaned.replace(/\s+/g, ' ').trim().length;
	})());
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
				keywords: allKeywords,
				isPartOf: postInfo ? `${brand.url}blog/category/${postInfo.category}` : `${brand.url}blog/`,
				wordCount: wordCount > 0 ? wordCount : undefined,
				about: (meta as Record<string, unknown>)?.corpName
					? {
							name: String((meta as Record<string, unknown>).corpName),
							identifier: (meta as Record<string, unknown>)?.stockCode
								? `KRX:${String((meta as Record<string, unknown>).stockCode)}`
								: undefined
						}
					: undefined
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
			runnables.forEach((c) => void unmount(c));
			runnables = [];
			mountRunnableCells();
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
	{#if postInfo?.categoryLabel}
		<meta property="article:section" content={postInfo.categoryLabel} />
	{/if}
	{#each frontmatterTags as tag (tag)}
		<meta property="article:tag" content={tag} />
	{/each}
	<meta name="keywords" content={allKeywords.join(', ')} />
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
				{#if postInfo}
					<div class="post-meta-row">
						<a href="{base}{getCategoryPath(postInfo.category)}" class="post-badge">{postInfo.categoryLabel}</a>
						{#if postInfo.series}
							<a href="{base}{getSeriesPath(postInfo.series)}" class="post-series">
								{postInfo.seriesLabel ?? postInfo.series}
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
				{#if meta?.title}
					<h1 class="post-title">{meta.title}</h1>
				{/if}
				{#if meta?.description}
					<div class="post-summary" aria-label="포스트 핵심 요약">
						<span class="post-summary-kicker">Quick Summary</span>
						<p>{meta.description}</p>
					</div>
				{/if}
				<BlogActionBar stockCode={subjectCode} topicSlug={subjectTopic} shareUrl={pageUrl} shareTitle={meta?.title ?? 'DartLab'} />
			</header>

			<article class="blog-article" bind:this={articleEl}>
				{#if Component}
					<Component />
				{/if}
			</article>

			<div class="post-support">
				<hr class="post-support-divider" />
				<p class="post-disclaimer">이 글은 특정 종목의 매수·매도를 권유하지 않습니다.</p>
				<p class="post-support-cta">양질의 기업분석을 계속 공유하기 위해 노력하고 있습니다. 도움이 되셨다면 dartlab을 후원해주세요.</p>
				<a href={brand.coffee} target="_blank" rel="noopener noreferrer">
					<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" width="160" height="45" loading="lazy" decoding="async" />
				</a>
			</div>

			<SubjectHub stockCode={subjectCode} topicSlug={subjectTopic} />

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
					<a href="{base}/skills" class="product-bridge-link">Skills</a>
					<a href="{base}/docs/tutorials/disclosure" class="product-bridge-link">공시 텍스트 튜토리얼</a>
				</div>
			</section>

			<div class="giscus-container" bind:this={giscusEl}></div>

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
								title={item.text}
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
		background: linear-gradient(135deg, var(--dl-red), var(--p-red-400));
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}
	.not-found p { color: var(--dl-ink-mute); margin: 1rem 0; }
	.not-found a { color: var(--dl-red); text-decoration: none; }

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
		border-bottom: 1px solid var(--dl-mkt-border);
	}

	.post-title {
		width: min(100%, 820px);
		margin: 1.1rem 0 0.4rem;
		font-size: clamp(1.6rem, 3vw, 2.35rem);
		font-weight: 800;
		line-height: 1.28;
		color: var(--dl-ink-print);
		letter-spacing: -0.01em;
		text-align: center;
	}

	.post-summary {
		width: min(100%, 720px);
		margin-top: 1rem;
		padding: 1rem 1.1rem;
		border-radius: 14px;
		border: 1px solid rgba(234, 70, 71, 0.22);
		background: linear-gradient(135deg, rgba(234, 70, 71, 0.12), var(--dl-mkt-card));
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
		color: var(--dl-ink);
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
		color: var(--dl-ink);
		text-decoration: none;
	}

	.post-series-order {
		color: var(--dl-ink-mute);
	}

	.post-date {
		display: flex;
		align-items: center;
		gap: 0.35rem;
		font-size: 0.8rem;
		color: var(--dl-ink-dim);
	}

	/* Article typography · mirrors docs layout */
	.blog-article {
		min-width: 0;
		max-width: 100%;
		overflow-wrap: break-word;
	}

	.blog-article :global(h1) {
		font-size: 1.75rem;
		font-weight: 800;
		margin-top: 5rem;
		margin-bottom: 2rem;
		padding-top: 2rem;
		border-top: 1px solid rgba(148, 163, 184, 0.12);
		background: linear-gradient(135deg, var(--dl-ink-print), var(--dl-ink-mute));
		-webkit-background-clip: text;
		-webkit-text-fill-color: transparent;
	}

	.blog-article :global(h2) {
		font-size: 1.5rem;
		font-weight: 700;
		margin-top: 3.5rem;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid var(--dl-mkt-border);
		color: var(--dl-ink-print);
	}

	.blog-article :global(h3) {
		font-size: 1.2rem;
		font-weight: 600;
		margin-top: 2.5rem;
		margin-bottom: 0.75rem;
		color: var(--dl-ink);
	}

	.blog-article :global(h4) {
		font-size: 1rem;
		font-weight: 600;
		margin-top: 1.5rem;
		margin-bottom: 0.5rem;
		color: var(--dl-ink);
	}

	.blog-article :global(p) {
		line-height: 1.8;
		color: var(--dl-ink-mute);
		margin-bottom: 1rem;
	}

	.blog-article :global(a) { color: var(--dl-red); text-decoration: none; }
	.blog-article :global(a:hover) { text-decoration: underline; }

	.blog-article :global(strong) { color: var(--dl-ink); }

	.blog-article :global(code:not(pre code)) {
		background: rgba(148, 163, 184, 0.1);
		padding: 0.15rem 0.4rem;
		border-radius: 4px;
		font-size: 0.875em;
		font-family: 'JetBrains Mono', monospace;
		color: var(--dl-ink);
	}

	.blog-article :global(pre) {
		background: #0d1117 !important;
		border: 1px solid var(--dl-mkt-border);
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
		color: var(--dl-ink-mute);
	}

	.blog-article :global(li) {
		line-height: 1.8;
		margin-bottom: 0.25rem;
	}

	.blog-article :global(table) {
		display: table;
		width: 100%;
		max-width: 100%;
		table-layout: auto;
		border-collapse: separate;
		border-spacing: 0;
		margin: 1.75rem 0;
		font-size: 0.9rem;
		background:
			linear-gradient(180deg, rgba(255, 255, 255, 0.02), rgba(255, 255, 255, 0)),
			var(--dl-mkt-card);
		border: 1px solid var(--dl-mkt-border);
		border-radius: 18px;
		box-shadow:
			0 18px 40px rgba(3, 5, 9, 0.28),
			inset 0 1px 0 rgba(255, 255, 255, 0.03);
		-webkit-overflow-scrolling: touch;
	}

	/* thead/tbody · 컨테이너 풀폭 우선, 컨텐츠가 더 크면 가로 스크롤
	   table은 block + overflow-x auto이므로 자식이 max-content면 표 안에서만 스크롤 */

	.blog-article :global(thead) {
		background: linear-gradient(180deg, rgba(234, 70, 71, 0.12), rgba(234, 70, 71, 0.04));
	}

	.blog-article :global(th) {
		text-align: left;
		padding: 0.95rem 1rem;
		border-bottom: 1px solid rgba(234, 70, 71, 0.18);
		color: var(--dl-ink-print);
		font-weight: 700;
		font-size: 0.8rem;
		text-transform: uppercase;
		letter-spacing: 0.07em;
		white-space: nowrap;
	}

	.blog-article :global(td) {
		padding: 0.85rem 1rem;
		border-bottom: 1px solid var(--dl-mkt-border);
		color: var(--dl-ink);
		background: rgba(255, 255, 255, 0.01);
		vertical-align: top;
	}

	/* 첫 컬럼은 헤더만 nowrap (연도 라벨 등). td는 wrap 허용 · 긴 본문 셀이 다른 컬럼을 밀어내지 않도록 */
	.blog-article :global(th:first-child) {
		white-space: nowrap;
	}

	.blog-article :global(td:first-child) {
		word-break: keep-all;
		max-width: 320px;
	}

	/* 숫자 컬럼 우측 정렬 · 첫 컬럼(항목명) 제외 */
	.blog-article :global(td:not(:first-child)),
	.blog-article :global(th:not(:first-child)) {
		text-align: right;
	}

	/* 표 안의 inline code는 줄바꿈 허용 · 코드가 컬럼을 옆으로 밀어내지 않도록 */
	.blog-article :global(td code:not(pre code)),
	.blog-article :global(th code:not(pre code)) {
		white-space: normal;
		word-break: break-all;
		font-size: 0.78rem;
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
		color: var(--dl-ink-print);
	}

	.blog-article :global(caption) {
		caption-side: top;
		text-align: left;
		padding: 0 0.25rem 0.75rem;
		font-size: 0.78rem;
		font-weight: 600;
		letter-spacing: 0.04em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
	}

	.blog-article :global(blockquote) {
		border-left: 3px solid var(--dl-red);
		padding: 0.5rem 1rem;
		margin: 1rem 0;
		background: rgba(234, 70, 71, 0.05);
		border-radius: 0 6px 6px 0;
	}

	.blog-article :global(blockquote p) { color: var(--dl-ink); margin: 0; }

	.blog-article :global(hr) {
		border: none;
		border-top: 1px solid var(--dl-mkt-border);
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
		color: var(--p-slate-400); /* 코드블록(다크 섬) 위 · 라이트에서도 고정 밝은 회색 */
		border: 1px solid rgba(148, 163, 184, 0.2);
		border-radius: 4px;
		cursor: pointer;
		opacity: 0;
		transition: opacity 0.15s, background 0.15s;
		z-index: 1;
	}
	:global(.copy-btn:hover) {
		background: rgba(234, 70, 71, 0.2);
		color: var(--dl-red);
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
		border-left: 1px solid var(--dl-mkt-border);
	}

	.blog-toc-heading {
		display: block;
		font-size: 0.7rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.06em;
		color: var(--dl-ink-dim);
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
		color: var(--dl-ink-dim);
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

	.blog-toc-item:hover { color: var(--dl-ink); }
	.blog-toc-item.active { color: var(--dl-red); border-left-color: var(--dl-red); }
	.blog-toc-item.h3 { padding-left: 1.1rem; font-size: 0.72rem; }

	.brand-loop {
		margin-top: 3rem;
		padding-top: 1.6rem;
		border-top: 1px solid var(--dl-mkt-border);
	}

	.brand-loop-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--dl-red);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.4rem;
	}

	.brand-loop-title {
		font-size: 1.2rem;
		font-weight: 800;
		color: var(--dl-ink-print);
		margin-bottom: 0.5rem;
	}

	.brand-loop-desc {
		color: var(--dl-ink-mute);
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
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		text-decoration: none;
	}

	.brand-loop-card-series {
		font-size: 0.7rem;
		color: var(--dl-ink-dim);
		text-transform: uppercase;
		letter-spacing: 0.05em;
		font-weight: 700;
	}

	.brand-loop-card-title {
		font-size: 0.94rem;
		font-weight: 700;
		color: var(--dl-ink);
	}

	.series-nav {
		margin-top: 3rem;
		padding-top: 1.5rem;
		border-top: 1px solid var(--dl-mkt-border);
	}

	.series-nav-heading {
		font-size: 0.78rem;
		font-weight: 700;
		letter-spacing: 0.08em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
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
		border: 1px solid var(--dl-mkt-border);
		background: var(--dl-mkt-card);
		text-decoration: none;
		transition: border-color 0.15s, transform 0.15s;
	}

	.series-card:hover {
		border-color: rgba(234, 70, 71, 0.28);
		transform: translateY(-1px);
	}

	.series-card-label {
		font-size: 0.72rem;
		color: var(--dl-ink-dim);
	}

	.series-card-title {
		font-size: 0.95rem;
		font-weight: 700;
		color: var(--dl-ink);
	}

	.product-bridge {
		margin-top: 3rem;
		padding: 1.5rem;
		border-radius: 18px;
		border: 1px solid rgba(234, 70, 71, 0.16);
		background:
			linear-gradient(135deg, rgba(234, 70, 71, 0.08), rgba(251, 146, 60, 0.04)),
			var(--dl-mkt-card);
	}

	.product-bridge-kicker {
		font-size: 0.72rem;
		font-weight: 700;
		color: var(--dl-red);
		letter-spacing: 0.08em;
		text-transform: uppercase;
		margin-bottom: 0.4rem;
	}

	.product-bridge-title {
		font-size: 1.2rem;
		font-weight: 800;
		color: var(--dl-ink-print);
		margin-bottom: 0.5rem;
	}

	.product-bridge-desc {
		color: var(--dl-ink);
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
		color: var(--dl-ink);
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
		border-top: 1px solid var(--dl-mkt-border);
	}

	.post-nav-link {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
		padding: 1rem;
		border: 1px solid var(--dl-mkt-border);
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
		color: var(--dl-ink-dim);
		text-transform: uppercase;
		letter-spacing: 0.03em;
	}
	.post-nav-link.next .post-nav-label { justify-content: flex-end; }

	.post-nav-title {
		font-size: 0.9rem;
		font-weight: 600;
		color: var(--dl-ink);
	}
	.post-nav-link:hover .post-nav-title { color: var(--dl-red); }

	/* Support (disclaimer + coffee) */
	.post-support {
		margin-top: 3rem;
		display: flex;
		flex-direction: column;
		align-items: center;
		text-align: center;
	}
	.post-support-divider {
		width: 100%;
		border: none;
		border-top: 1px solid var(--dl-mkt-border);
		margin-bottom: 1.5rem;
	}
	.post-disclaimer {
		font-size: 0.95rem;
		color: var(--dl-red);
		line-height: 1.6;
		margin: 0;
		font-weight: 500;
	}
	.post-support-cta {
		font-size: 1rem;
		color: var(--dl-ink);
		line-height: 1.6;
		margin: 0.75rem 0 1.5rem;
	}
	.post-support a {
		display: inline-block;
	}
	.post-support img {
		display: block;
		transition: opacity 0.2s;
	}
	.post-support img:hover {
		opacity: 0.85;
	}

	/* Giscus */
	.giscus-container {
		margin-top: 3rem;
		padding-top: 2rem;
		border-top: 1px solid var(--dl-mkt-border);
	}

	/* Footer */
	.post-footer {
		margin-top: 2rem;
		padding-top: 1.5rem;
	}

	.back-link {
		font-size: 0.875rem;
		color: var(--dl-ink-mute);
		text-decoration: none;
		transition: color 0.15s;
	}
	.back-link:hover { color: var(--dl-red); }

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

	@media (max-width: 768px) {
		.blog-post-layout {
			max-width: 100vw;
			width: 100%;
			padding: 0;
			gap: 1rem;
			overflow-x: hidden;
		}
		.blog-post-col {
			max-width: 100%;
			min-width: 0;
			width: 100%;
			overflow-x: hidden;
		}
		.post-header {
			max-width: 100%;
			width: 100%;
			overflow-x: hidden;
		}
		.post-summary {
			width: 100%;
			max-width: 100%;
			padding: 0.85rem 0.95rem;
			box-sizing: border-box;
			overflow-x: hidden;
		}
		.post-summary p {
			font-size: 0.92rem;
			word-break: keep-all;
			overflow-wrap: anywhere;
		}
		/* 본문 자체 · 모든 자식이 부모 폭 넘지 않도록 */
		.blog-article {
			max-width: 100%;
			min-width: 0;
			overflow-wrap: anywhere;
			word-break: keep-all;
		}
		.blog-article :global(p),
		.blog-article :global(li),
		.blog-article :global(h1),
		.blog-article :global(h2),
		.blog-article :global(h3),
		.blog-article :global(h4),
		.blog-article :global(blockquote) {
			max-width: 100%;
			overflow-wrap: anywhere;
			word-break: keep-all;
		}
		/* pre/code 블록은 가로 스크롤 */
		.blog-article :global(pre) {
			max-width: 100%;
			overflow-x: auto;
			-webkit-overflow-scrolling: touch;
		}
		.blog-article :global(img),
		.blog-article :global(svg) {
			max-width: 100%;
			height: auto;
		}
	}

	@media (max-width: 480px) {
		.post-header {
			margin-bottom: 1.5rem;
			padding-bottom: 1.25rem;
		}
		.blog-article {
			font-size: 0.95rem;
		}
	}
</style>
