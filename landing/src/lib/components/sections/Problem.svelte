<script lang="ts">
	import { Card } from '$lib/components/ui/card';
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-4xl">
		<div class="text-center mb-16">
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">전자공시의 99%는 버려지고 있다</h2>
			<p class="text-dl-text-muted text-lg">대부분의 도구는 숫자 몇 개만 뽑아간다. 나머지는?</p>
		</div>

		<div class="grid md:grid-cols-2 gap-6">
			<Card hover={false}>
				<div class="text-xs font-mono text-dl-text-dim mb-4 uppercase tracking-wider">기존 도구</div>
				<div class="space-y-3 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> 매출액
					</div>
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> 영업이익
					</div>
					<div class="flex items-center gap-3 text-dl-text-muted">
						<span class="text-dl-success">✓</span> 순이익
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 사업의 내용
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 위험 요인
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 감사의견
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 소송 / 지배구조
					</div>
					<div class="flex items-center gap-3 text-dl-text-dim">
						<span class="text-dl-warning">✗</span> 텍스트 변경 추적
					</div>
				</div>
			</Card>

			<Card hover={false} class="border-dl-primary/30 ring-1 ring-dl-primary/10 bg-gradient-to-br from-dl-bg-card to-dl-bg-card">
				<div class="text-xs font-mono text-dl-primary mb-4 uppercase tracking-wider">DartLab</div>
				<div class="space-y-3 font-mono text-sm">
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> 매출액
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> 영업이익
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-success">✓</span> 순이익
					</div>
					<div class="h-px bg-dl-border my-2"></div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 사업의 내용
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 위험 요인
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 감사의견
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 소송 / 지배구조
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-primary">✓</span> 텍스트 변경 추적
					</div>
					<div class="flex items-center gap-3 text-dl-text">
						<span class="text-dl-accent">✓</span> 정량·정성 교차 검증
					</div>
				</div>
			</Card>
		</div>
	</div>
</section>
