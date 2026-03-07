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
	<title>DartLab — DART 전자공시 문서를 완벽하게 분석하는 Python 라이브러리</title>
	<meta name="description" content="DART 전자공시 문서를 완벽하게 분석하는 Python 라이브러리. 재무제표, 사업보고서, 감사의견까지 숫자와 텍스트를 모두 파싱하고 시계열로 정렬한다. 260+ 상장사 데이터 제공." />
	<meta name="keywords" content="DART, 전자공시, 공시분석, 재무제표, 사업보고서, Python, 금융데이터, 한국주식, 공시파싱, dartlab" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — DART 전자공시 분석 Python 라이브러리" />
	<meta property="og:description" content="전자공시 문서를 완벽하게 분석한다. 재무제표·사업보고서·감사의견까지, 숫자와 텍스트를 모두 파싱하고 시계열로 정렬하는 오픈소스 라이브러리." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/icon-512.png" />
	<meta property="og:image:width" content="512" />
	<meta property="og:image:height" content="512" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary" />
	<meta name="twitter:title" content="DartLab — DART 전자공시 분석 Python 라이브러리" />
	<meta name="twitter:description" content="전자공시 문서를 완벽하게 분석한다. 재무제표부터 감사의견까지, 260+ 상장사 데이터 제공." />
	<meta name="twitter:image" content="https://eddmpython.github.io/dartlab/icon-512.png" />

	{@html `<script type="application/ld+json">${JSON.stringify({
		"@context": "https://schema.org",
		"@type": "SoftwareApplication",
		"name": "DartLab",
		"alternateName": "DART 전자공시 분석 라이브러리",
		"applicationCategory": "DeveloperApplication",
		"operatingSystem": "Windows, macOS, Linux",
		"description": "DART 전자공시 문서를 완벽하게 분석하는 Python 라이브러리. 재무제표, 사업보고서, 감사의견 등 숫자와 텍스트를 모두 파싱하고 시계열로 정렬한다.",
		"url": "https://eddmpython.github.io/dartlab/",
		"downloadUrl": "https://pypi.org/project/dartlab/",
		"softwareVersion": "0.1.2",
		"inLanguage": "ko",
		"author": { "@type": "Person", "name": "eddmpython", "url": "https://github.com/eddmpython" },
		"offers": { "@type": "Offer", "price": "0", "priceCurrency": "USD" },
		"license": "https://opensource.org/licenses/MIT",
		"programmingLanguage": "Python",
		"codeRepository": "https://github.com/eddmpython/dartlab",
		"keywords": ["DART", "전자공시", "재무제표", "공시분석", "사업보고서", "Python"]
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
