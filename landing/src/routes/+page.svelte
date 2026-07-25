<script lang="ts">
	import { brand } from '$lib/brand';
	import Header from '$lib/components/sections/Header.svelte';
	import Hero from '$lib/components/sections/Hero.svelte';
	import Numbers from '$lib/components/sections/Numbers.svelte';
	import IndustryMapCta from '$lib/components/sections/IndustryMapCta.svelte';
	import ScanStudioCta from '$lib/components/sections/ScanStudioCta.svelte';
	import Problem from '$lib/components/sections/Problem.svelte';
	import AccountPipeline from '$lib/components/sections/AccountPipeline.svelte';
	import Alignment from '$lib/components/sections/Alignment.svelte';
	import ViewerShowcase from '$lib/components/sections/ViewerShowcase.svelte';
	import Layers from '$lib/components/sections/Layers.svelte';
	import Workflow from '$lib/components/sections/Workflow.svelte';
	import CodeDemo from '$lib/components/sections/CodeDemo.svelte';
	import AskDemo from '$lib/components/sections/AskDemo.svelte';
	import DataShowcase from '$lib/components/sections/DataShowcase.svelte';
	import ModuleCatalog from '$lib/components/sections/ModuleCatalog.svelte';
	import SkillDocsCta from '$lib/components/sections/SkillDocsCta.svelte';
	import DartVsEdgar from '$lib/components/sections/DartVsEdgar.svelte';
	import Performance from '$lib/components/sections/Performance.svelte';
	import Stability from '$lib/components/sections/Stability.svelte';
	import UseCases from '$lib/components/sections/UseCases.svelte';
	import Install from '$lib/components/sections/Install.svelte';
	import QuickStart from '$lib/components/sections/QuickStart.svelte';
	import Notebooks from '$lib/components/sections/Notebooks.svelte';
	import CTA from '$lib/components/sections/CTA.svelte';
	import Footer from '$lib/components/sections/Footer.svelte';
	import { buildOrganizationJsonLd, buildSoftwareApplicationJsonLd, buildSourceCodeJsonLd, buildWebsiteJsonLd, buildFaqJsonLd } from '$lib/seo';
	import type { FaqItem } from '$lib/seo';

	const homepageFaq: FaqItem[] = [
		{
			question: 'DartLab 이 무엇인가요?',
			answer: 'DartLab 은 기업 공시를 구조화·비교 가능한 데이터로 만드는 오픈소스 Python 라이브러리입니다. 한국 DART 와 미국 SEC EDGAR 의 재무제표·서술 텍스트·정형 보고서를 하나의 통합 인터페이스로 다루며, PDF 를 직접 읽을 필요가 없습니다.'
		},
		{
			question: 'DartLab 은 누구를 위한 도구인가요?',
			answer: '기업 공시 데이터를 다루는 모든 사람 · 기간별로 회사를 비교하는 투자자, 재무 모델을 만드는 퀀트, 공시에서 NLP 데이터셋을 만드는 연구자, 금융 애플리케이션 개발자, LLM 에 구조화된 회사 컨텍스트가 필요한 AI 빌더.'
		},
		{
			question: '다른 금융 데이터 도구와 무엇이 다른가요?',
			answer: '대부분 도구는 재무 숫자 또는 문서 텍스트 중 하나만, 한국 또는 미국 중 한쪽만 다룹니다. DartLab 은 docs · finance · report 세 소스를 하나의 회사 지도로 결합하고, 기간으로 정렬하며, DART 와 EDGAR 모두 동일하게 동작합니다. trace() 로 모든 숫자의 출처가 드러납니다.'
		},
		{
			question: 'EDGAR 10-K · 10-Q 도 지원하나요?',
			answer: '지원합니다. dartlab.Company("AAPL") 처럼 티커를 넘기면 미국 10-K · 10-Q 분석이 가능합니다. DART 와 동일한 인터페이스 · sections · panel · trace · diff · BS · IS · CF · ratios 모두 동일하게 동작합니다.'
		},
		{
			question: '코드를 짜야만 쓸 수 있나요?',
			answer: '아닙니다. CLI 명령 "dartlab ask" 로 자연어 질문이 가능합니다 · 예: dartlab ask "삼성전자 재무건전성 분석해줘". DartLab 이 회사 데이터를 구조화해 자동으로 LLM 에 먹입니다. 심층 분석·커스텀 워크플로우는 Python 으로 가능합니다.'
		},
		{
			question: '전자공시 분석 도구가 뭔가요?',
			answer: 'DartLab 은 DART 전자공시와 미국 SEC EDGAR 공시 문서를 자동 파싱해 재무제표 · 서술형 텍스트 · 정형 보고서를 하나의 구조화된 회사 맵으로 만드는 오픈소스 Python 라이브러리입니다. 종목코드 하나로 한국·미국 상장기업 데이터에 접근합니다.'
		},
		{
			question: '사업보고서를 자동으로 분석할 수 있나요?',
			answer: '네. DartLab 은 사업보고서의 모든 섹션을 topic × period DataFrame 으로 자동 구조화합니다. 연간 · 반기 · 분기 보고서를 기간별 수평 비교할 수 있고, 재무제표 · 배당 · 임원현황 · 부문정보 등 44 개 모듈을 show() 한 줄로 조회합니다.'
		},
		{
			question: '재무제표 데이터를 Python 으로 어떻게 가져오나요?',
			answer: 'pip install dartlab 후 import dartlab; c = dartlab.Company("005930") 한 줄이면 삼성전자 재무제표에 접근할 수 있습니다. c.panel("BS") 재무상태표, c.panel("IS") 손익계산서, c.panel("CF") 현금흐름표로 XBRL 정규화된 재무 데이터를 바로 씁니다. 데이터는 자동 다운로드됩니다.'
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
	<!-- 1. Hook -->
	<Hero />
	<Numbers />
	<IndustryMapCta />
	<ScanStudioCta />

	<!-- 2. Problem → Solution -->
	<Problem />
	<AccountPipeline />
	<Alignment />
	<ViewerShowcase />
	<Layers />

	<!-- 3. How -->
	<Workflow />
	<CodeDemo />
	<AskDemo />
	<DataShowcase />

	<!-- 4. What -->
	<ModuleCatalog />
	<SkillDocsCta />
	<DartVsEdgar />
	<Performance />

	<!-- 5. Trust -->
	<Stability />
	<UseCases />

	<!-- 6. Action -->
	<Install />
	<QuickStart />
	<Notebooks />
	<CTA />
	<Footer />
</main>
