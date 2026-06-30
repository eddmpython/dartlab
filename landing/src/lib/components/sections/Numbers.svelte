<script lang="ts">
	const features = [
		{ title: '한국 DART', desc: '모든 공시를 미리 구조화' },
		{ title: '미국 SEC EDGAR', desc: '같은 인터페이스, 다른 나라' },
		{ title: '계정 정규화', desc: '하나의 매출액, 수십 가지 변형 아님' },
		{ title: '섹션 표준화', desc: '모든 변형을 같은 토픽으로 매핑' },
		{ title: '자동 구조화', desc: '원본 공시 → DataFrame. 클렌징 불필요.' },
		{ title: '비율 사전계산', desc: '수익성·유동성·가치평가 · 로드 시 준비 완료' }
	];
</script>

<section class="py-20 px-6 relative overflow-hidden">
	<div class="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_rgba(234,70,71,0.04)_0%,_transparent_60%)]"></div>

	<div class="relative max-w-5xl mx-auto">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">이미 끝나 있는 것</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text">구조화 완료, 바로 사용</h2>
		</div>

		<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each features as f}
				<div class="relative px-5 py-5 rounded-lg border border-dl-border/50 bg-dl-bg-card/30 hover:border-dl-primary/30 hover:bg-dl-bg-card/60 transition-all duration-300">
					<div class="flex items-start gap-3">
						<span class="mt-1 w-1.5 h-1.5 rounded-full bg-dl-primary shrink-0"></span>
						<div>
							<div class="text-sm font-semibold text-dl-text mb-1">{f.title}</div>
							<div class="text-xs text-dl-text-muted leading-relaxed">{f.desc}</div>
						</div>
					</div>
				</div>
			{/each}
		</div>
	</div>
</section>
