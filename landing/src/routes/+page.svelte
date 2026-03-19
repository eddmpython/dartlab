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
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildWebsiteJsonLd, buildFaqJsonLd } from '$lib/seo';
	import type { FaqItem } from '$lib/seo';

	const homepageFaq: FaqItem[] = [
		{
			question: 'DartLab이란 무엇인가?',
			answer: 'DartLab은 한국 DART 전자공시와 미국 SEC EDGAR 공시 데이터를 자동 분석하는 오픈소스 Python 라이브러리입니다. 사업보고서, 재무제표, 공시 텍스트를 기간별로 수평화하여 하나의 회사 맵(sections)으로 만듭니다.'
		},
		{
			question: 'DART 전자공시 데이터를 어떻게 분석할 수 있나?',
			answer: 'dartlab.Company("005930")처럼 종목코드로 Company 객체를 만들면 사업보고서의 모든 섹션이 topic x period 매트릭스로 자동 정렬됩니다. show(topic)으로 특정 주제를 조회하고, diff()로 기간별 텍스트 변화를 감지할 수 있습니다.'
		},
		{
			question: 'EDGAR 10-K, 10-Q도 분석할 수 있나?',
			answer: '네. dartlab.Company("AAPL")처럼 ticker로 미국 기업의 10-K/10-Q를 분석할 수 있습니다. EDGAR sections 매핑률 100%, 974종목 검증 완료. DART와 동일한 인터페이스(sections, show, trace)를 사용합니다.'
		},
		{
			question: 'sections란 무엇인가?',
			answer: 'sections는 공시 문서 전체를 topic(주제) x period(기간) 매트릭스로 수평화한 것입니다. 사업의 내용, 재무제표, 감사보고서 등 모든 섹션의 텍스트와 테이블이 기간별로 나란히 정렬됩니다. 삼성전자 기준 329개 topic, 106개 기간.'
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
	<meta name="description" content="DartLab은 한국 DART 전자공시와 미국 SEC EDGAR 공시 데이터를 자동 분석하는 오픈소스 Python 라이브러리다. sections 수평화, show/trace 조회, diff 변화 감지, AI 워크플로우를 제공한다." />
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
	<meta name="twitter:description" content="DART 전자공시와 SEC EDGAR 공시를 하나의 회사 맵으로 분석하는 Python 라이브러리. sections 수평화, show/trace 조회, AI-ready." />
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
