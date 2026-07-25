<script lang="ts">
	import { Card } from '$lib/components/ui/card';

	const benchmarks = [
		{
			label: 'Company 생성',
			time: '~2 초',
			bar: 25,
			detail: '데이터 로드 + sections 빌드'
		},
		{
			label: 'sections 쿼리',
			time: '<100ms',
			bar: 5,
			detail: '329 토픽 × 106 기간 즉시'
		},
		{
			label: 'panel(topic)',
			time: '<50ms',
			bar: 3,
			detail: '단일 토픽 블록 추출'
		},
		{
			label: 'BS / IS / CF',
			time: '<100ms',
			bar: 5,
			detail: '정규화된 재무제표'
		},
		{
			label: 'ratios 시계열',
			time: '<200ms',
			bar: 10,
			detail: 'TTM 기반 trailing 계산'
		},
		{
			label: 'diff(topic)',
			time: '<300ms',
			bar: 15,
			detail: '기간 대비 텍스트 비교'
		}
	];

	const techSpecs = [
		{ label: '런타임', value: 'Polars (Pandas 아님)' },
		{ label: '데이터 포맷', value: 'Parquet (컬럼나)' },
		{ label: '자동 다운로드', value: 'HuggingFace Datasets' },
		{ label: '증분', value: 'mtime 기반 delta sync' },
		{ label: '캐시', value: 'Company 객체 재사용' },
		{ label: 'Python', value: '3.12+ 필요' }
	];
</script>

<section class="py-24 px-6">
	<div class="max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">성능</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-3">단순하기 때문에 빠르다</h2>
			<p class="text-dl-text-muted text-lg">Polars + Parquet + 단일 구조 = 불필요한 변환 0</p>
		</div>

		<div class="grid lg:grid-cols-5 gap-6">
			<!-- Benchmark Bars -->
			<div class="lg:col-span-3">
				<div class="rounded-lg border border-dl-border bg-dl-bg-card/50 p-6">
					<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">응답 시간 (삼성전자)</div>
					<div class="space-y-4">
						{#each benchmarks as b}
							<div>
								<div class="flex items-center justify-between mb-1.5">
									<span class="text-sm text-dl-text">{b.label}</span>
									<span class="text-sm font-mono font-bold text-dl-primary">{b.time}</span>
								</div>
								<div class="h-2 rounded-full bg-dl-bg-darker overflow-hidden">
									<div
										class="h-full rounded-full bg-gradient-to-r from-dl-primary to-dl-accent transition-all duration-700"
										style="width: {b.bar}%"
									></div>
								</div>
								<div class="text-[10px] text-dl-text-dim mt-1">{b.detail}</div>
							</div>
						{/each}
					</div>
				</div>
			</div>

			<!-- Tech Specs -->
			<div class="lg:col-span-2">
				<Card hover={false}>
					<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">기술 스택</div>
					<div class="space-y-3">
						{#each techSpecs as spec}
							<div class="flex items-start justify-between gap-3">
								<span class="text-sm text-dl-text-dim shrink-0">{spec.label}</span>
								<span class="text-sm text-dl-text font-mono text-right">{spec.value}</span>
							</div>
						{/each}
					</div>
				</Card>

				<Card hover={false} class="mt-4">
					<div class="text-xs font-mono text-dl-text-dim mb-3 uppercase tracking-wider">왜 빠른가</div>
					<div class="space-y-2 text-sm text-dl-text-muted leading-relaxed">
						<p><span class="text-dl-text font-medium">단일 구조.</span> 모든 쿼리가 sections 위에서 실행 · 데이터 변환 불필요.</p>
						<p><span class="text-dl-text font-medium">Polars.</span> Pandas 대비 5~10 배 빠른 DataFrame 연산.</p>
						<p><span class="text-dl-text font-medium">Parquet.</span> 컬럼나 포맷 · 필요한 컬럼만 읽는다.</p>
					</div>
				</Card>
			</div>
		</div>
	</div>
</section>
