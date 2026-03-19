<script lang="ts">
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import Hero from '$lib/components/sections/Hero.svelte';
	import Numbers from '$lib/components/sections/Numbers.svelte';
	import Problem from '$lib/components/sections/Problem.svelte';
	import Alignment from '$lib/components/sections/Alignment.svelte';
	import Layers from '$lib/components/sections/Layers.svelte';
	import Workflow from '$lib/components/sections/Workflow.svelte';
	import CodeDemo from '$lib/components/sections/CodeDemo.svelte';
	import DataShowcase from '$lib/components/sections/DataShowcase.svelte';
	import ModuleCatalog from '$lib/components/sections/ModuleCatalog.svelte';
	import DartVsEdgar from '$lib/components/sections/DartVsEdgar.svelte';
	import Performance from '$lib/components/sections/Performance.svelte';
	import Stability from '$lib/components/sections/Stability.svelte';
	import UseCases from '$lib/components/sections/UseCases.svelte';
	import Install from '$lib/components/sections/Install.svelte';
	import CTA from '$lib/components/sections/CTA.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildWebsiteJsonLd, buildFaqJsonLd } from '$lib/seo';
	import type { FaqItem } from '$lib/seo';

	const homepageFaq: FaqItem[] = [
		{
			question: 'What is DartLab?',
			answer: 'DartLab is an open-source Python library that turns corporate disclosure filings into structured, comparable data. It covers 2,700+ Korean companies (DART) and 970+ US companies (EDGAR), giving you financial statements, narrative text, and structured reports in one unified interface — no PDF reading required.'
		},
		{
			question: 'Who is DartLab for?',
			answer: 'Anyone who works with corporate disclosure data — investors comparing companies across periods, quants building financial models, researchers creating NLP datasets from filings, developers building financial applications, and AI builders who need structured company context for LLMs.'
		},
		{
			question: 'How is DartLab different from other financial data tools?',
			answer: 'Most tools give you either financial numbers or document text, for either Korea or the US. DartLab combines all three data sources (docs, finance, reports) into one company map, aligns them across time periods, and works identically for both DART and EDGAR filings. trace() shows exactly where each data point came from.'
		},
		{
			question: 'Does it support EDGAR 10-K and 10-Q?',
			answer: 'Yes. Use a ticker like dartlab.Company("AAPL") to analyze US 10-K/10-Q filings. EDGAR sections mapping rate is 100%, verified across 974 companies. Same interface as DART — sections, show, trace, diff, BS, IS, CF, ratios all work identically.'
		}
	];

	const homepageJsonLd = JSON.stringify([
		buildOrganizationJsonLd(),
		buildWebsiteJsonLd(),
		buildSoftwareApplicationJsonLd(),
		buildFaqJsonLd(homepageFaq)
	]);
</script>

<svelte:head>
	<title>DartLab — {brand.description}</title>
	<meta name="description" content="Stop reading 200-page PDFs. DartLab turns Korean DART and US EDGAR filings into structured, comparable data — financials, text, and reports in one Python object. 2,700+ Korean and 970+ US companies ready to analyze." />
	<meta name="keywords" content="DART, OpenDART, EDGAR, financial analysis, annual report, Python, Korean stocks, disclosure parsing, dartlab, sections, company analysis, financial data" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — {brand.description}" />
	<meta property="og:description" content="Stop reading 200-page PDFs. Turn Korean DART and US EDGAR filings into structured data — financials, text, and reports in one Python object. 2,700+ Korean and 970+ US companies." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab — {brand.description}" />
	<meta name="twitter:description" content="Stop reading 200-page PDFs. Turn DART and EDGAR filings into structured data — financials, text, and reports in one Python object. 2,700+ companies ready." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />

	{@html `<script type="application/ld+json">${homepageJsonLd}</script>`}
</svelte:head>

<Header />
<main class="overflow-x-hidden">
	<!-- 1. Hook -->
	<Hero />
	<Numbers />

	<!-- 2. Problem → Solution -->
	<Problem />
	<Alignment />
	<Layers />

	<!-- 3. How -->
	<Workflow />
	<CodeDemo />
	<DataShowcase />

	<!-- 4. What -->
	<ModuleCatalog />
	<DartVsEdgar />
	<Performance />

	<!-- 5. Trust -->
	<Stability />
	<UseCases />

	<!-- 6. Action -->
	<Install />
	<CTA />
	<Footer />
</main>
