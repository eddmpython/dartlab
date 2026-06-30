<script lang="ts">
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Panel</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">세로로 쌓인 공시를 하나의 수평 맵으로</h2>
			<p class="text-dl-text-muted text-lg">진짜 제품은 파서 목록이 아니라 지도다.</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6">
			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					섹션 정렬
				</div>

				<div class="space-y-3">
					{#each [
						{ label: '2023', width: 'w-full', text: 'companyOverview | business | risk', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024Q1', width: 'w-3/4', text: 'companyOverview | business', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024Q2', width: 'w-3/4', text: 'companyOverview | business', color: 'from-dl-primary/50 to-dl-primary/20', textColor: 'text-dl-primary-light' },
						{ label: '2024', width: 'w-full', text: 'companyOverview | business | risk', color: 'from-dl-accent/50 to-dl-accent/20', textColor: 'text-dl-accent-light' }
					] as bar}
						<div class="grid grid-cols-[5rem_1fr] items-center gap-3">
							<span class="text-dl-text-muted text-xs text-right font-mono">{bar.label}</span>
							<div class="h-8 rounded-md bg-dl-bg-darker overflow-hidden">
								<div
									class="h-full {bar.width} bg-gradient-to-r {bar.color} rounded-lg flex items-center justify-center"
								>
									<span class="text-[10px] {bar.textColor} font-semibold">{bar.text}</span>
								</div>
							</div>
						</div>
					{/each}
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">같은 토픽 행, 기간별 커버리지만 다름. 누락 기간은 비어있을 뿐 지도가 깨지지 않는다.</span>
				</div>
			</Card>

			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					소스 인지 머지
				</div>

				<div class="space-y-4 font-mono text-sm">
					<div class="grid grid-cols-3 gap-3 text-center">
						<div class="text-xs text-dl-text-dim">panel</div>
						<div class="text-xs text-dl-text-dim">finance</div>
						<div class="text-xs text-dl-text-dim">report</div>
					</div>

					{#each [
						{ a: 'companyOverview', b: 'BS', c: 'audit', changed: false },
						{ a: '위험 텍스트', b: 'IS', c: 'dividend', changed: false },
						{ a: 'retrievalBlocks', b: 'ratios', c: 'employee', changed: true }
					] as row}
						<div class="grid grid-cols-3 gap-3 items-center">
							<div class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate">
								{row.a}
							</div>
							<div class="px-2 py-2 rounded-lg bg-dl-bg-darker text-xs text-dl-text text-center truncate">
								{row.b}
							</div>
							<div
								class="px-2 py-2 rounded-lg text-xs text-center truncate {row.changed
									? 'bg-dl-primary/10 text-dl-primary border border-dl-primary/30'
									: 'bg-dl-bg-darker text-dl-text'}"
							>
								{row.c}
							</div>
						</div>
						{#if row.changed}
							<div class="grid grid-cols-3 gap-3 -mt-2">
								<div></div>
								<div class="flex justify-center">
									<span class="text-[10px] text-dl-primary">──→</span>
								</div>
								<div class="flex justify-center">
									<span class="text-[9px] text-dl-primary font-medium">같은 spine 으로 머지</span>
								</div>
							</div>
						{/if}
					{/each}
				</div>

				<div class="flex items-center gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">`show(...)` 과 `trace(...)` 가 같은 company spine 위에 올라간다 · 별도 구조를 만들지 않는다.</span>
				</div>
			</Card>
		</div>

		<!-- trace() + diff() · 같은 spine 위 두 도구 -->
		<div class="mt-6 grid md:grid-cols-2 gap-6">
			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					숫자 → 출처
				</div>

				<div class="font-mono text-sm space-y-2">
					<div class="text-dl-text">
						<span class="text-dl-primary">samsung</span>.<span class="text-dl-accent">trace</span>(<span class="text-dl-text-muted">"revenue"</span>)
					</div>
					<div class="pl-3 border-l border-dl-border/60 space-y-1 text-xs">
						<div class="text-dl-text-dim">primarySource: <span class="text-dl-text">finance</span></div>
						<div class="text-dl-text-dim">fallback: <span class="text-dl-text">panel</span></div>
						<div class="text-dl-text-dim">block: <span class="text-dl-text">2024 Q4 · 손익계산서</span></div>
					</div>
				</div>

				<div class="flex items-start gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">모든 숫자가 어느 공시·섹션·블록에서 왔는지 드러낸다. 블랙박스 숫자 0.</span>
				</div>
			</Card>

			<Card>
				<div class="text-xs font-mono text-dl-text-dim mb-5 uppercase tracking-wider">
					기간 → 변화
				</div>

				<div class="font-mono text-sm space-y-2">
					<div class="text-dl-text">
						<span class="text-dl-primary">samsung</span>.<span class="text-dl-accent">diff</span>(<span class="text-dl-text-muted">"riskManagement"</span>)
					</div>
					<div class="pl-3 border-l border-dl-border/60 space-y-1 text-xs">
						<div class="text-dl-text-dim">2024 → 2023</div>
						<div><span class="text-dl-success">+ 추가</span> <span class="text-dl-text">공급망 집중도</span></div>
						<div><span class="text-dl-warning">~ 수정</span> <span class="text-dl-text">환율 노출 단락</span></div>
						<div><span class="text-dl-text-dim">= 동일</span> <span class="text-dl-text-dim">감사 의견</span></div>
					</div>
				</div>

				<div class="flex items-start gap-2 mt-6 pt-4 border-t border-dl-border">
					<svg class="w-4 h-4 text-dl-primary shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
						<path stroke-linecap="round" stroke-linejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
					</svg>
					<span class="text-dl-text text-xs">기업이 기간 사이에 조용히 고친 부분이 드러난다. 눈이 아니라 텍스트로 diff.</span>
				</div>
			</Card>
		</div>
	</div>
</section>
