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
			answer: 'DartLab is an open-source Python library that automatically analyzes Korean DART and US SEC EDGAR disclosure data. It horizontalizes annual reports, financial statements, and disclosure text into a single company map (sections).'
		},
		{
			question: 'How can I analyze DART disclosure data?',
			answer: 'Create a Company object with a stock code like dartlab.Company("005930"). All report sections are automatically aligned into a topic x period matrix. Use show(topic) to query specific topics and diff() to detect text changes across periods.'
		},
		{
			question: 'Does it support EDGAR 10-K and 10-Q?',
			answer: 'Yes. Use a ticker like dartlab.Company("AAPL") to analyze US 10-K/10-Q filings. EDGAR sections mapping rate is 100%, verified across 974 companies. Same interface as DART (sections, show, trace).'
		},
		{
			question: 'What are sections?',
			answer: 'sections is the entire disclosure document horizontalized into a topic (subject) x period (time) matrix. All text and tables from business description, financial statements, audit reports, etc. are aligned side by side across periods. Samsung Electronics has 329 topics across 106 periods.'
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
	<meta name="description" content="DartLab is an open-source Python library for analyzing Korean DART and US SEC EDGAR disclosure data. Provides sections horizontalization, show/trace queries, diff change detection, and AI workflows." />
	<meta name="keywords" content="DART, OpenDART, EDGAR, financial analysis, annual report, Python, Korean stocks, disclosure parsing, dartlab, sections" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — {brand.description}" />
	<meta property="og:description" content="Analyze Korean DART and US SEC EDGAR disclosures into one company map. Open-source Python library with sections horizontalization, show/trace queries, and AI workflows." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab — {brand.description}" />
	<meta name="twitter:description" content="Analyze DART and SEC EDGAR disclosures into one company map. sections horizontalization, show/trace queries, AI-ready." />
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
