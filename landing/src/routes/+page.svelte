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
</script>

<svelte:head>
	<title>DartLab — {brand.description}</title>
	<meta name="description" content="A Python library for comprehensive DART disclosure analysis. Parses financial statements, annual reports, and audit opinions — both numbers and text — into time-series DataFrames. 260+ listed companies." />
	<meta name="keywords" content="DART, disclosure, financial analysis, annual report, audit opinion, Python, Korean stocks, disclosure parsing, dartlab, time series" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — {brand.description}" />
	<meta property="og:description" content="Comprehensive DART disclosure analysis. Parses financial statements, annual reports, and audit opinions into time-series DataFrames. Open-source Python library." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="en_US" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab — {brand.description}" />
	<meta name="twitter:description" content="Comprehensive DART disclosure analysis. Financial statements to audit opinions. 260+ listed companies." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/og-image.png" />

	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "SoftwareApplication",
		"name": "DartLab",
		"alternateName": "DART Disclosure Analysis Library",
		"applicationCategory": "DeveloperApplication",
		"operatingSystem": "Windows, macOS, Linux",
		"description": "A Python library for comprehensive DART disclosure analysis. Parses financial statements, annual reports, and audit opinions — both numbers and text — into time-series DataFrames.",
		"url": "https://eddmpython.github.io/dartlab/",
		"downloadUrl": "https://pypi.org/project/dartlab/",
		"softwareVersion": brand.version,
		"inLanguage": "en",
		"author": { "@type": "Person", "name": "eddmpython", "url": "https://github.com/eddmpython" },
		"offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
		"license": "https://opensource.org/licenses/MIT",
		"programmingLanguage": "Python",
		"codeRepository": "https://github.com/eddmpython/dartlab",
		"keywords": ["DART", "disclosure", "financial statements", "annual report", "audit opinion", "Python", "Korean stocks"]
	})}</script>`}
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
