<script lang="ts">
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import Hero from '$lib/components/sections/Hero.svelte';
	import Numbers from '$lib/components/sections/Numbers.svelte';
	import Problem from '$lib/components/sections/Problem.svelte';
	import AccountPipeline from '$lib/components/sections/AccountPipeline.svelte';
	import Alignment from '$lib/components/sections/Alignment.svelte';
	import Layers from '$lib/components/sections/Layers.svelte';
	import Workflow from '$lib/components/sections/Workflow.svelte';
	import CodeDemo from '$lib/components/sections/CodeDemo.svelte';
	import AskDemo from '$lib/components/sections/AskDemo.svelte';
	import DataShowcase from '$lib/components/sections/DataShowcase.svelte';
	import ModuleCatalog from '$lib/components/sections/ModuleCatalog.svelte';
	import DartVsEdgar from '$lib/components/sections/DartVsEdgar.svelte';
	import Performance from '$lib/components/sections/Performance.svelte';
	import Stability from '$lib/components/sections/Stability.svelte';
	import UseCases from '$lib/components/sections/UseCases.svelte';
	import Install from '$lib/components/sections/Install.svelte';
	import CTA from '$lib/components/sections/CTA.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildSourceCodeJsonLd, buildWebsiteJsonLd, buildFaqJsonLd } from '$lib/seo';
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
		},
		{
			question: 'Do I need to write code to use DartLab?',
			answer: 'No. The CLI command "dartlab ask" lets you ask questions in natural language — e.g. dartlab ask "삼성전자 재무건전성 분석해줘". DartLab automatically structures company data and feeds it to an LLM. For deeper analysis and custom workflows, Python gives you full control.'
		},
		{
			question: '전자공시 분석 도구가 뭔가요?',
			answer: 'DartLab은 DART 전자공시와 미국 SEC EDGAR 공시 문서를 자동으로 파싱하여 재무제표, 서술형 텍스트, 정형 보고서를 하나의 구조화된 회사 맵으로 만드는 오픈소스 Python 라이브러리입니다. 종목코드 하나면 2,700개 이상의 한국 기업과 970개 이상의 미국 기업 데이터에 접근할 수 있습니다.'
		},
		{
			question: '사업보고서를 자동으로 분석할 수 있나요?',
			answer: '네. DartLab은 사업보고서의 모든 섹션을 topic × period DataFrame으로 자동 구조화합니다. 연간, 반기, 분기 보고서를 기간별로 수평 비교할 수 있고, 재무제표, 배당, 임원현황, 부문정보 등 44개 모듈을 show() 한 줄로 조회합니다.'
		},
		{
			question: '재무제표 데이터를 Python으로 어떻게 가져오나요?',
			answer: 'pip install dartlab 후 import dartlab; c = dartlab.Company("005930") 한 줄이면 삼성전자 재무제표에 접근할 수 있습니다. c.BS(재무상태표), c.IS(손익계산서), c.CF(현금흐름표)로 XBRL 정규화된 재무 데이터를 바로 사용합니다. 데이터는 자동 다운로드됩니다.'
		}
	];

	const homepageJsonLd = JSON.stringify([
		buildOrganizationJsonLd(),
		buildWebsiteJsonLd(),
		buildSoftwareApplicationJsonLd(),
		buildSourceCodeJsonLd(),
		buildFaqJsonLd(homepageFaq)
	]);
</script>

<svelte:head>
	<title>DartLab — {brand.description}</title>
	<meta name="description" content="Stop reading 200-page PDFs. DartLab turns Korean DART and US EDGAR filings into structured, comparable data — financials, text, and reports in one Python object. 2,700+ Korean and 970+ US companies ready to analyze." />
	<meta name="keywords" content="DART, OpenDART, EDGAR, financial analysis, annual report, Python, Korean stocks, disclosure parsing, dartlab, sections, company analysis, financial data, 전자공시, 사업보고서, 재무제표, 공시분석, 다트, DART전자공시, 한국주식분석" />
	<link rel="canonical" href="https://eddmpython.github.io/dartlab/" />

	<meta property="og:type" content="website" />
	<meta property="og:title" content="DartLab — {brand.description}" />
	<meta property="og:description" content="DART 전자공시와 EDGAR 공시를 하나의 회사 맵으로 바꾸는 Python 라이브러리. 종목코드 하나면 2,700개 한국 기업과 970개 미국 기업의 재무제표, 사업보고서, 공시 텍스트를 구조화된 데이터로 분석합니다." />
	<meta property="og:url" content="https://eddmpython.github.io/dartlab/" />
	<meta property="og:site_name" content="DartLab" />
	<meta property="og:image" content="https://eddmpython.github.io/dartlab/og-image.png" />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="ko_KR" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content="DartLab — {brand.description}" />
	<meta name="twitter:description" content="DART 전자공시와 EDGAR 공시를 하나의 회사 맵으로 바꾸는 Python 라이브러리. 종목코드 하나면 2,700개 한국 기업과 970개 미국 기업의 재무제표, 사업보고서를 구조화된 데이터로 분석합니다." />
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
	<AccountPipeline />
	<Alignment />
	<Layers />

	<!-- 3. How -->
	<Workflow />
	<CodeDemo />
	<AskDemo />
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
