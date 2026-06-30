<script lang="ts">
	import { Badge } from '$lib/components/ui/badge';

	let activeCategory = $state(0);

	const categories = [
		{
			id: 'docs',
			label: 'docs',
			color: 'text-dl-accent',
			bgColor: 'bg-dl-accent/10',
			borderColor: 'border-dl-accent/30',
			desc: '서술 구조 · 섹션 경계 · retrieval 블록',
			modules: [
				{ name: 'sections', desc: '토픽 × 기간 수평화 · 회사 지도' },
				{ name: 'retrievalBlocks', desc: 'RAG 용 텍스트 블록' },
				{ name: 'contextSlices', desc: '증거 레이어 슬라이스' },
				{ name: 'companyOverview', desc: '회사 개요' },
				{ name: 'businessOverview', desc: '사업 내용' },
				{ name: 'riskManagement', desc: '위험관리' },
				{ name: 'auditOpinion', desc: '감사 의견' },
				{ name: 'segments', desc: '부문 정보' },
				{ name: 'salesOrder', desc: '영업 실적' },
				{ name: 'notes', desc: 'K-IFRS 주석 래퍼' }
			]
		},
		{
			id: 'finance',
			label: 'finance',
			color: 'text-dl-primary',
			bgColor: 'bg-dl-primary/10',
			borderColor: 'border-dl-primary/30',
			desc: '정규화된 재무제표 · 비율 · 시계열',
			modules: [
				{ name: 'BS', desc: '재무상태표' },
				{ name: 'IS', desc: '손익계산서' },
				{ name: 'CF', desc: '현금흐름표' },
				{ name: 'CIS', desc: '포괄손익계산서' },
				{ name: 'ratios', desc: '재무비율 시계열' },
				{ name: 'ratioSeries', desc: '단일 비율 추출' },
				{ name: 'timeseries', desc: '단일 계정 시계열' },
				{ name: 'statements', desc: '전 재무제표 통합 뷰' }
			]
		},
		{
			id: 'report',
			label: 'report',
			color: 'text-dl-success',
			bgColor: 'bg-dl-success/10',
			borderColor: 'border-dl-success/30',
			desc: '정형 공시 API · DART 전용',
			modules: [
				{ name: 'audit', desc: '감사인 · 감사 의견' },
				{ name: 'dividend', desc: '배당 정보' },
				{ name: 'employee', desc: '직원 통계' },
				{ name: 'executive', desc: '임원 명단' },
				{ name: 'compensation', desc: '임원 보수' },
				{ name: 'treasury', desc: '자기주식' },
				{ name: 'minority', desc: '소액주주' },
				{ name: 'largestShareholder', desc: '최대주주' },
				{ name: 'majorShareholder', desc: '5% 이상 주주' },
				{ name: 'capital', desc: '증자 · 감자' }
			]
		},
		{
			id: 'analysis',
			label: 'analysis',
			color: 'text-dl-warning',
			bgColor: 'bg-dl-warning/10',
			borderColor: 'border-dl-warning/30',
			desc: '소스 횡단 분석 엔진',
			modules: [
				{ name: 'show(topic)', desc: '토픽별 블록 인덱스 + 데이터' },
				{ name: 'trace(topic)', desc: '소스 추적 (docs/finance/report)' },
				{ name: 'diff(topic)', desc: '기간 간 텍스트 변화 감지' },
				{ name: 'insights', desc: '7 영역 등급 + 이상치 감지' },
				{ name: 'market', desc: '시가총액 순위' },
				{ name: 'sector', desc: 'WICS 섹터 분류' },
				{ name: 'profile', desc: '머지된 Company 레이어' },
				{ name: 'index', desc: '전체 토픽 인덱스' }
			]
		},
		{
			id: 'ai',
			label: 'AI + 도구',
			color: 'text-purple-400',
			bgColor: 'bg-purple-500/10',
			borderColor: 'border-purple-500/30',
			desc: 'LLM 분석 · export · CLI · 서버',
			modules: [
				{ name: 'AI 분석', desc: '7 개 provider (GPT · Claude · Ollama…)' },
				{ name: 'Excel export', desc: '전 모듈 Excel 내보내기' },
				{ name: 'Server API', desc: 'FastAPI 40+ 엔드포인트' },
				{ name: 'CLI', desc: 'ask · status · ai · excel' },
				{ name: 'Desktop', desc: 'Windows GUI 앱' },
				{ name: 'search', desc: '종목 검색 (퍼지 매칭)' }
			]
		}
	];
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">모듈 카탈로그</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">42 개 모듈, 단일 구조</h2>
			<p class="text-dl-text-muted text-lg">모든 모듈이 같은 sections spine 위. 별도 스키마 0.</p>
		</div>

		<!-- Category Tabs -->
		<div class="flex flex-wrap justify-center gap-2 mb-8">
			{#each categories as cat, i}
				<button
					onclick={() => activeCategory = i}
					class="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-mono transition-all cursor-pointer border
						{activeCategory === i
							? `${cat.bgColor} ${cat.color} ${cat.borderColor}`
							: 'bg-dl-bg-card/50 text-dl-text-dim border-dl-border hover:text-dl-text hover:border-dl-border'
						}"
				>
					<span class="w-2 h-2 rounded-full {activeCategory === i ? cat.bgColor.replace('/10', '') : 'bg-dl-text-dim/30'}"></span>
					{cat.label}
					<span class="text-[10px] opacity-60">{cat.modules.length}</span>
				</button>
			{/each}
		</div>

		<!-- Category Description -->
		<div class="text-center mb-6">
			<p class="text-sm text-dl-text-muted">{categories[activeCategory].desc}</p>
		</div>

		<!-- Module Grid -->
		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
			{#each categories[activeCategory].modules as mod, i}
				<div class="group flex items-start gap-3 px-4 py-3 rounded-lg border border-dl-border/50 bg-dl-bg-card/30 hover:border-dl-primary/20 hover:bg-dl-bg-card/60 transition-all duration-200">
					<div class="shrink-0 mt-0.5">
						<span class="flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold {categories[activeCategory].bgColor} {categories[activeCategory].color}">
							{i + 1}
						</span>
					</div>
					<div class="min-w-0">
						<div class="text-sm font-mono font-semibold text-dl-text group-hover:text-dl-primary-light transition-colors">{mod.name}</div>
						<div class="text-xs text-dl-text-dim mt-0.5">{mod.desc}</div>
					</div>
				</div>
			{/each}
		</div>

		<!-- 총 모듈 수 -->
		<div class="mt-8 text-center">
			<Badge variant="success">
				<span class="w-1.5 h-1.5 rounded-full bg-dl-success animate-pulse"></span>
				{categories.reduce((sum, c) => sum + c.modules.length, 0)} 개 모듈, 같은 sections spine 위
			</Badge>
		</div>
	</div>
</section>
