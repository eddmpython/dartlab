<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { BarChart3, FileText, Link2 } from 'lucide-svelte';
</script>

<section id="features" class="py-24 px-6">
	<div class="mx-auto max-w-5xl">
		<div class="text-center mb-16">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">Architecture</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">전자공시를 분석하는 세 가지 레이어</h2>
			<p class="text-dl-text-muted text-lg">숫자에서 텍스트로, 텍스트에서 인사이트로</p>
		</div>

		<div class="grid md:grid-cols-3 gap-6">
			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-11 h-11 rounded-xl bg-dl-primary/10 flex items-center justify-center mb-4">
					<BarChart3 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-primary mb-2">Layer 1</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">정량 분석</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					Bridge Matching으로 누적 재무제표에서 개별 분기 실적을 역산한다. 14개 모듈, 260+ 상장사.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						동일 기업 내 계정명 자동 추적
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						분기 역산 (Q1~Q4)
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						변경점 자동 탐지
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">출시됨</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-accent/40 hover:shadow-dl-accent/5">
				<div class="w-11 h-11 rounded-xl bg-dl-accent/10 flex items-center justify-center mb-4">
					<FileText class="w-5 h-5 text-dl-accent" />
				</div>
				<div class="text-xs font-mono text-dl-accent mb-2">Layer 2</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">정성 분석</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					별도 프로젝트에서 개발 중인 전문 텍스트 분석 모듈을 DartLab에 통합 배치할 예정이다.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						섹션별 텍스트 diff
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						위험 요인 추적
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						감사의견 변경 감지
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge>배치 예정</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-11 h-11 rounded-xl bg-gradient-to-br from-dl-primary/10 to-dl-accent/10 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent mb-2">Layer 3</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">교차 검증</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					정량 변동과 정성 변화를 연결하여 리스크 시그널을 자동으로 탐지한다.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						실적 변동 ↔ 텍스트 설명
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						리스크 시그널 선행 분석
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						감사의견 ↔ 신뢰도 판단
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge>개발 중</Badge>
				</div>
			</Card>
		</div>
	</div>
</section>
