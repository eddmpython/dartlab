<script lang="ts">
	// 첫 화면: 소개 한 섹션, 왼쪽으로 흐르는 기업이야기 표지 줄, 12편씩 나눠 받는 최신 글 목록.
	// 라이브러리 소개 섹션들은 /developers 로 옮겼다. 자료는 +page.server.ts 가 빌드할 때 골라 넣는다.
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import HomeIntro from '$lib/components/home/HomeIntro.svelte';
	import StoryStrip from '$lib/components/home/StoryStrip.svelte';
	import PostFeed from '$lib/components/home/PostFeed.svelte';
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildSourceCodeJsonLd, buildWebsiteJsonLd } from '$lib/seo';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	const homepageJsonLd = JSON.stringify([
		buildOrganizationJsonLd(),
		buildWebsiteJsonLd(),
		buildSoftwareApplicationJsonLd(),
		buildSourceCodeJsonLd()
	]);
</script>

<svelte:head>
	<title>DartLab · {brand.description}</title>
	<meta name="description" content="기업의 이야기는 공시에 있다. DartLab 은 종목코드 하나로 한국 DART 와 미국 SEC EDGAR 공시를 구조화·비교 가능한 데이터로 만든다 · Python 한 줄." />
	<meta name="keywords" content="DART, OpenDART, EDGAR, financial analysis, annual report, Python, Korean stocks, disclosure parsing, dartlab, sections, company analysis, financial data, 전자공시, 사업보고서, 재무제표, 공시분석, 다트, DART전자공시, 한국주식분석" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab · {brand.description}" />
	<meta property="og:description" content="기업의 모든 진실은 공시에 있다. DartLab은 DART 전자공시와 EDGAR 공시를 읽을 수 있게 만든다. 종목코드 하나로 한국·미국 상장기업의 재무제표, 사업보고서를 구조화된 데이터로." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab · {brand.description}" />
	<meta name="twitter:description" content="기업의 모든 진실은 공시에 있다. DartLab은 DART 전자공시와 EDGAR 공시를 읽을 수 있게 만든다. 종목코드 하나로 한국·미국 상장기업의 재무제표, 사업보고서를 구조화된 데이터로." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />

	{@html `<script type="application/ld+json">${homepageJsonLd}</script>`}
</svelte:head>

<Header />
<main class="overflow-x-hidden">
	<HomeIntro storyIndex={data.storyIndex} />
	<StoryStrip items={data.strip} />
	<PostFeed initial={data.feed} pages={data.feedPages} />
	<Footer />
</main>
