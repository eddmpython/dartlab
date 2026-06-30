<script lang="ts">
	import { base } from '$app/paths';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { brand } from '$lib/brand';
	import {
		buildAbsoluteUrl,
		buildBreadcrumbJsonLd,
		buildOrganizationJsonLd,
		buildPersonJsonLd,
		buildWebsiteJsonLd
	} from '$lib/seo';

	const pageTitle = 'About · DartLab';
	const pageDesc =
		'DartLab 은 한국 DART 와 미국 SEC EDGAR 공시를 구조화해 분석 가능한 데이터로 만드는 오픈소스 프로젝트다.';
	const pageUrl = buildAbsoluteUrl('about');
	const jsonLd = JSON.stringify([
		buildWebsiteJsonLd(),
		buildOrganizationJsonLd(),
		buildPersonJsonLd(),
		buildBreadcrumbJsonLd([
			{ name: 'DartLab', url: brand.url },
			{ name: 'About', url: pageUrl }
		])
	]);
</script>

<svelte:head>
	<title>{pageTitle}</title>
	<meta name="description" content={pageDesc} />
	<link rel="canonical" href={pageUrl} />
	<meta property="og:type" content="website" />
	<meta property="og:title" content={pageTitle} />
	<meta property="og:description" content={pageDesc} />
	<meta property="og:url" content={pageUrl} />
	{@html `<script type="application/ld+json">${jsonLd}</script>`}
</svelte:head>

<Header context="default" />

<main class="about-page">
	<article class="about-article">
		<header class="hero">
			<p class="kicker">About</p>
			<h1>DartLab</h1>
			<p class="lead">
				DartLab 은 한국 FSS DART 와 미국 SEC EDGAR 공시를 구조적으로 읽기 위해 만든 오픈소스
				프로젝트다. 단순 조회가 아니라 재무 숫자와 공시 문서를 단일 데이터 흐름으로 통합해 반복
				가능한 분석 토대를 만든다.
			</p>
		</header>

		<section>
			<h2>무엇을 만드는가</h2>
			<p>DartLab 은 세 계층을 한 번에 다룬다.</p>
			<ul>
				<li>재무제표·비율 같은 정량 데이터.</li>
				<li>사업보고서·감사보고서·MD&amp;A·주석 같은 정성 데이터.</li>
				<li>위 둘을 코드로 바로 재사용 가능하게 만드는 표준화 레이어.</li>
			</ul>
			<p>
				핵심 아이디어 · "공시를 어떻게 읽는가" 와 "공시를 데이터로 어떻게 쓰는가" 를 한 프로젝트
				안에서 잇는다.
			</p>
		</section>

		<section>
			<h2>왜 만들었나</h2>
			<p>
				DART 와 EDGAR 는 좋은 정보를 갖고 있지만, 대부분 웹사이트를 일일이 열어 문서를 하나씩 봐야
				한다. 투자자·연구자·개발자가 같은 작업을 반복한다. DartLab 은 이 비효율을 줄이기 위해
				시작했다.
			</p>
			<ul>
				<li>공시 문서를 topic 별로 구조화.</li>
				<li>XBRL 재무 데이터를 시계열로 정리.</li>
				<li>공시 텍스트와 숫자를 한 회사 객체 안에서 다룸.</li>
				<li>해석 방식을 블로그 글과 문서로 공개.</li>
			</ul>
		</section>

		<section>
			<h2>다루는 데이터</h2>
			<ul>
				<li>DART 공시 문서 원문.</li>
				<li>OpenDART API 와 XBRL 재무제표.</li>
				<li>DART 정기 공시 정형 데이터.</li>
				<li>SEC EDGAR 공시 원문과 XBRL 데이터.</li>
			</ul>
			<p>
				핵심 원칙은 <strong>source-aware structure</strong> · 숫자는 더 강한 source 를 우선하고,
				서술 정보는 원본 맥락 보존을 우선한다.
			</p>
		</section>

		<section>
			<h2>유지보수</h2>
			<p>
				프로젝트 작성자이자 유지보수자는 <code>eddmpython</code>. 도구와 글은 GitHub · PyPI ·
				YouTube · Threads · 블로그를 통해 지속 공개한다.
			</p>
			<ul class="links">
				<li><a href="https://github.com/eddmpython" target="_blank" rel="noopener">GitHub</a></li>
				<li><a href="https://pypi.org/user/eddmpython/" target="_blank" rel="noopener">PyPI</a></li>
				<li><a href="https://www.youtube.com/@eddmpython" target="_blank" rel="noopener">YouTube</a></li>
				<li><a href="https://www.threads.net/@eddmpython" target="_blank" rel="noopener">Threads</a></li>
				<li><a href="https://eddm.tistory.com" target="_blank" rel="noopener">Blog</a></li>
			</ul>
		</section>

		<section>
			<h2>이 사이트를 어떻게 읽나</h2>
			<p>처음 방문이라면 다음 순서가 가장 효율적이다.</p>
			<ol>
				<li><a href="{base}/skills">Skill Catalog</a> · 절차·엔진 능력·운영 규칙 진입.</li>
				<li><a href="{base}/skills/start.installUv">Installation</a> · 설치와 첫 실행.</li>
				<li><a href="{base}/skills/start.quickStart">Quick Start</a> · 8 단계 walkthrough.</li>
				<li><a href="{base}/blog">Blog</a> · 공시 해석 프레임워크와 사례.</li>
			</ol>
			<p>
				Skills 가 사용 절차·AI workflow·런타임 제약의 일차 카탈로그. 블로그는 실제 공시를 어떻게
				읽는지 해석 프레임워크를 다룬다. 함께 읽으면 빠르다.
			</p>
		</section>

		<section>
			<h2>인용과 출처</h2>
			<p>
				DartLab 문서와 블로그는 가능한 곳마다 공식 출처를 포함한다. DART · OpenDART · SEC · IFRS
				같은 1 차 출처를 우선하고, 해석과 구현은 명확히 분리한다.
			</p>
			<p>이 프로젝트를 인용할 때 다음 페이지가 좋은 시작점이다.</p>
			<ul>
				<li>Skills: <code>/skills</code></li>
				<li>Installation: <code>/skills/start.installUv</code></li>
				<li>Blog: <code>/blog/</code></li>
				<li>GitHub: <code>https://github.com/eddmpython/dartlab</code></li>
			</ul>
		</section>

		<section>
			<h2>FAQ</h2>

			<h3>DartLab 이 풀려는 문제는?</h3>
			<p>공시 데이터를 사람이 읽기만 하는 상태에서 코드와 파이프라인이 재사용할 수 있는 구조로 바꾼다.</p>

			<h3>누가 쓰면 좋은가?</h3>
			<p>투자자, 퀀트 연구자, 데이터 엔지니어, 회계/공시 자동화 개발자.</p>

			<h3>이 사이트에서 무엇을 먼저 읽나?</h3>
			<p>Installation 과 Quick Start 부터. 해석 관점이 필요하면 입문 블로그 글을 함께.</p>

			<h3>데이터 출처는?</h3>
			<p>FSS DART, OpenDART, SEC EDGAR, XBRL 원본, 정기 보고서 API.</p>

			<h3>어떻게 인용하나?</h3>
			<p>
				문서·블로그·GitHub 의 canonical URL 사용. 구현 주제는 GitHub, 해석 주제는 블로그/문서가
				적절.
			</p>
		</section>
	</article>
</main>

<Footer />

<style>
	.about-page {
		min-height: 100vh;
		max-width: var(--dl-w-article, 720px);
		margin: 0 auto;
		padding: 6.5rem 1.25rem 4rem;
		background: var(--dl-bg-base);
		color: var(--dl-ink);
	}

	.hero {
		margin-bottom: 2.5rem;
		padding-bottom: 1.5rem;
		border-bottom: 1px solid var(--dl-line);
	}

	.kicker {
		margin: 0 0 0.5rem;
		color: var(--dl-accent);
		font-size: 0.72rem;
		font-weight: 700;
		text-transform: uppercase;
		letter-spacing: 0.1em;
	}

	h1 {
		margin: 0 0 0.85rem;
		font-family: var(--dl-font-head);
		font-size: clamp(2rem, 4vw, 3rem);
		line-height: 1.1;
		color: var(--dl-ink-print);
	}

	.lead {
		margin: 0;
		max-width: 38rem;
		color: var(--dl-ink-mute);
		font-size: 1rem;
		line-height: 1.7;
	}

	section {
		margin: 2rem 0;
	}

	section h2 {
		margin: 0 0 0.75rem;
		font-size: 1.25rem;
		color: var(--dl-ink-print);
		font-weight: 600;
	}

	section h3 {
		margin: 1.1rem 0 0.4rem;
		font-size: 0.95rem;
		color: var(--dl-accent);
		font-weight: 600;
	}

	section p {
		margin: 0.5rem 0;
		font-size: 0.95rem;
		line-height: 1.7;
		color: var(--dl-ink);
	}

	section ul,
	section ol {
		margin: 0.5rem 0 0.7rem;
		padding-left: 1.4rem;
		color: var(--dl-ink);
		font-size: 0.95rem;
		line-height: 1.7;
	}

	section li {
		margin: 0.3rem 0;
	}

	.links {
		display: flex;
		gap: 1rem;
		flex-wrap: wrap;
		list-style: none;
		padding-left: 0;
	}

	.links a {
		color: var(--dl-accent);
		text-decoration: none;
		font-family: var(--dl-font-mono);
		font-size: 0.86rem;
	}

	.links a:hover {
		text-decoration: underline;
	}

	code {
		padding: 0.08rem 0.4rem;
		border-radius: var(--dl-r-sm);
		background: var(--dl-bg-overlay);
		color: var(--dl-accent);
		font-family: var(--dl-font-mono);
		font-size: 0.86em;
	}

	a {
		color: var(--dl-accent);
		text-decoration: underline;
		text-underline-offset: 3px;
	}
</style>
