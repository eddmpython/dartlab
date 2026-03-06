<script lang="ts">
	import Header from '$lib/components/sections/Header.svelte';
	import Hero from '$lib/components/sections/Hero.svelte';
	import Problem from '$lib/components/sections/Problem.svelte';
	import Alignment from '$lib/components/sections/Alignment.svelte';
	import Layers from '$lib/components/sections/Layers.svelte';
	import CodeDemo from '$lib/components/sections/CodeDemo.svelte';
	import Install from '$lib/components/sections/Install.svelte';
	import CTA from '$lib/components/sections/CTA.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
</script>

<svelte:head>
	<title>DartLab — 공시의 숫자 너머를 읽다</title>
	<meta name="description" content="DART 공시 문서를 완벽하게 분석하는 Python 라이브러리. 숫자와 텍스트를 모두 파싱하고, 분기·반기·사업보고서를 시계열로 정렬한다." />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — 공시의 숫자 너머를 읽다" />
	<meta property="og:description" content="DART 공시 문서를 완벽하게 분석하는 Python 라이브러리. 숫자는 결과이고, 텍스트는 원인이다." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />

	<meta name="twitter:card" content="summary" />
	<meta name="twitter:title" content="DartLab — Read Beyond the Numbers" />
	<meta name="twitter:description" content="DART 공시 문서를 완벽하게 분석하는 Python 라이브러리." />

	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "SoftwareApplication",
		"name": "DartLab",
		"applicationCategory": "DeveloperApplication",
		"operatingSystem": "Windows, macOS, Linux",
		"description": "DART 공시 문서를 완벽하게 분석하는 Python 라이브러리 — 숫자와 텍스트 모두",
		"url": "https://eddmpython.github.io/dartlab/",
		"downloadUrl": "https://pypi.org/project/dartlab/",
		"softwareVersion": "0.1.0",
		"author": { "@type": "Person", "name": "eddmpython", "url": "https://github.com/eddmpython" },
		"offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
		"license": "https://opensource.org/licenses/MIT",
		"programmingLanguage": "Python",
		"codeRepository": "https://github.com/eddmpython/dartlab"
	})}</script>`}
</svelte:head>

<Header />
<main class="overflow-x-hidden">
	<Hero />
	<Problem />
	<Alignment />
	<Layers />
	<CodeDemo />
	<Install />
	<CTA />
	<Footer />
</main>
