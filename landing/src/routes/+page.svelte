<script lang="ts">
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import Hero from '$lib/components/sections/Hero.svelte';
	import Problem from '$lib/components/sections/Problem.svelte';
	import Alignment from '$lib/components/sections/Alignment.svelte';
	import Layers from '$lib/components/sections/Layers.svelte';
	import Workflow from '$lib/components/sections/Workflow.svelte';
	import CodeDemo from '$lib/components/sections/CodeDemo.svelte';
	import ModuleCatalog from '$lib/components/sections/ModuleCatalog.svelte';
	import UseCases from '$lib/components/sections/UseCases.svelte';
	import Install from '$lib/components/sections/Install.svelte';
	import CTA from '$lib/components/sections/CTA.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildWebsiteJsonLd } from '$lib/seo';

	const homepageJsonLd = JSON.stringify([
		buildOrganizationJsonLd(),
		buildWebsiteJsonLd(),
		buildSoftwareApplicationJsonLd()
	]);
</script>

<svelte:head>
	<title>DartLab — {brand.description}</title>
	<meta name="description" content="DartLab은 한국 DART 전자공시 데이터를 재무제표, 사업보고서, 감사의견, 주석까지 구조화하는 오픈소스 Python 라이브러리다." />
	<meta name="keywords" content="전자공시, DART, OpenDART, EDGAR, financial analysis, annual report, Python, Korean stocks, disclosure parsing, dartlab" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — {brand.description}" />
	<meta property="og:description" content={brand.descriptionKo} />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab — {brand.description}" />
	<meta name="twitter:description" content="DART 전자공시 분석 Python 라이브러리. 재무제표, 사업보고서, 감사의견을 시계열 DataFrame으로. 2,700+ 상장기업." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />

	{@html `<script type="application/ld+json">${homepageJsonLd}</script>`}
</svelte:head>

<Header />
<main class="overflow-x-hidden">
	<Hero />
	<Problem />
	<Alignment />
	<Layers />
	<Workflow />
	<CodeDemo />
	<ModuleCatalog />
	<UseCases />
	<Install />
	<CTA />
	<Footer />
</main>
