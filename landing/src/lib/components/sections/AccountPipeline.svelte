<script lang="ts">
	import { Card } from '$lib/components/ui/card';

	const steps = [
		{
			step: 1,
			label: '접두사 제거',
			detail: 'ifrs-full_, dart_, ifrs_, ifrs-smes_',
			example: ['ifrs-full_Revenue', 'Revenue'],
			count: '4 종 접두사'
		},
		{
			step: 2,
			label: 'ID 동의어',
			detail: '영문 계정 ID 정규화',
			example: ['NetIncome', 'ProfitLoss'],
			count: '59 규칙'
		},
		{
			step: 3,
			label: '계정명 동의어',
			detail: '한글 계정명 통일',
			example: ['영업수익', '매출액'],
			count: '104 규칙'
		},
		{
			step: 4,
			label: '학습 매핑',
			detail: '누적 매핑 테이블',
			example: ['ProfitLoss', 'net_income'],
			count: '34,249'
		}
	];
</script>

<section class="py-24 px-6">
	<div class="mx-auto max-w-5xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block"
				>표준화</span
			>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">
				34,249 계정 매핑. 수작업 0.
			</h2>
			<p class="text-dl-text-muted text-lg max-w-2xl mx-auto">
				기업마다 다른 XBRL 계정 ID 로 공시한다. DartLab 은 4 단계 파이프라인으로
				정규화해 회사간 비교가 자동으로 동작한다.
			</p>
		</div>

		<!-- Pipeline flow -->
		<div class="grid md:grid-cols-4 gap-4 mb-10">
			{#each steps as s}
				<Card>
					<div class="flex items-center gap-2 mb-3">
						<div
							class="w-7 h-7 rounded-full bg-dl-primary/10 flex items-center justify-center text-dl-primary text-xs font-bold"
						>
							{s.step}
						</div>
						<span class="text-xs font-semibold text-dl-text">{s.label}</span>
					</div>
					<div class="text-[10px] text-dl-text-dim mb-3">{s.detail}</div>
					<div class="font-mono text-xs space-y-1">
						<div class="flex items-center gap-2">
							<span class="text-dl-text-dim">{s.example[0]}</span>
						</div>
						<div class="flex items-center gap-2">
							<span class="text-dl-primary text-[10px]">--></span>
							<span class="text-dl-text">{s.example[1]}</span>
						</div>
					</div>
					<div
						class="mt-3 pt-3 border-t border-dl-border text-center text-xs font-bold text-dl-primary tabular-nums"
					>
						{s.count}
					</div>
				</Card>
			{/each}
		</div>

		<!-- Before / After -->
		<div class="grid md:grid-cols-2 gap-4 mb-10">
			<!-- Before -->
			<Card hover={false}>
				<div class="text-[10px] font-mono text-dl-warning uppercase tracking-wider mb-3">표준화 전 · 원본 XBRL</div>
				<div class="space-y-2 font-mono text-xs">
					<div class="flex justify-between"><span class="text-dl-text-dim">삼성전자</span><span class="text-dl-text-muted">ifrs-full_Revenue</span></div>
					<div class="flex justify-between"><span class="text-dl-text-dim">SK하이닉스</span><span class="text-dl-text-muted">dart_Revenue</span></div>
					<div class="flex justify-between"><span class="text-dl-text-dim">LG에너지솔루션</span><span class="text-dl-text-muted">Revenue</span></div>
				</div>
				<div class="mt-3 pt-3 border-t border-dl-border text-xs text-dl-text-dim">같은 개념인데 3 개 회사가 3 개 다른 계정 ID</div>
			</Card>

			<!-- After -->
			<Card hover={false} class="border-dl-primary/20">
				<div class="text-[10px] font-mono text-dl-primary uppercase tracking-wider mb-3">표준화 후</div>
				<div class="space-y-2 font-mono text-xs">
					<div class="flex justify-between"><span class="text-dl-text">삼성전자</span><span class="text-dl-primary">revenue</span></div>
					<div class="flex justify-between"><span class="text-dl-text">SK하이닉스</span><span class="text-dl-primary">revenue</span></div>
					<div class="flex justify-between"><span class="text-dl-text">LG에너지솔루션</span><span class="text-dl-primary">revenue</span></div>
				</div>
				<div class="mt-3 pt-3 border-t border-dl-border text-xs text-dl-text">전부 <code class="text-dl-primary">revenue</code> 로 · 회사간 비교가 그냥 동작</div>
			</Card>
		</div>

		<!-- Result -->
		<Card hover={false} class="border-dl-primary/20 bg-dl-bg-card">
			<div class="flex flex-wrap items-center justify-center gap-6 text-center">
				<div>
					<div class="text-2xl font-black text-dl-primary tabular-nums">~97%</div>
					<div class="text-xs text-dl-text-dim">매핑율</div>
				</div>
				<div class="hidden md:block w-px h-10 bg-dl-border"></div>
				<div>
					<div class="text-2xl font-black text-dl-text tabular-nums">3,143</div>
					<div class="text-xs text-dl-text-dim">표준 계정</div>
				</div>
				<div class="hidden md:block w-px h-10 bg-dl-border"></div>
				<div>
					<div class="text-2xl font-black text-dl-text tabular-nums">34,249</div>
					<div class="text-xs text-dl-text-dim">XBRL 매핑</div>
				</div>
			</div>
		</Card>
	</div>
</section>
