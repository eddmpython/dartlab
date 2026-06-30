<script lang="ts">
	import { base } from '$app/paths';
	import { Card } from '$lib/components/ui/card';
	import { Badge } from '$lib/components/ui/badge';
	import { BarChart3, FileText, Link2 } from 'lucide-svelte';
</script>

<section id="features" class="py-24 px-6">
	<div class="mx-auto max-w-6xl">
		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">통합 아키텍처</span>
			<h2 class="text-3xl md:text-4xl font-bold text-dl-text mb-4">전문 금융 자율 작업대 + 분석 엔진 + Skill OS 환류</h2>
			<p class="text-dl-text-muted text-lg">1 차 데이터 (DART · SEC EDGAR · 향후 EDINET) → 분석 엔진 → 자율 작업대 → 시장 검증 → 사람 환류.</p>
		</div>

		<div class="mb-20 flex justify-center">
			<img
				src="{base}/architecture.svg"
				alt="DartLab 통합 아키텍처 · 입구 · 자율 작업대 (chat-native + 운용 자원 3 종) · story 종합 · 공식 분석 5 (analysis · credit · macro · quant · industry) · 횡단 처리 3 (gather · company · scan) · core · 외부 1 차 소스 · 3 자 진화 루프"
				class="max-w-3xl w-full h-auto rounded-xl border border-dl-border bg-dl-bg-card shadow-2xl"
				loading="lazy"
				width="800"
				height="1340"
			/>
			<p class="text-center text-xs text-dl-text-dim mt-4">
				① 사람·외부 LLM (MCP) → ② 입구 두 갈래 → ③ 자율 작업대 + 운용 자원 3 종 (Skill OS · Capability · Tools 11) → ④ story 종합 → ⑤ 분석 엔진 5 → ⑥ 횡단 처리 3 → ⑦ core → ⑧ 외부 1 차 소스 · ⑨ 3 자 진화 루프
			</p>
		</div>

		<div class="text-center mb-12">
			<span class="text-xs font-semibold uppercase tracking-widest text-dl-accent mb-3 block">Company 레이어 · 4 네임스페이스</span>
			<h3 class="text-2xl md:text-3xl font-bold text-dl-text mb-3">하나의 회사, 4 개 네임스페이스</h3>
			<p class="text-dl-text-muted">지도는 그대로. 소스 책임만 다르다.</p>
		</div>

		<div class="grid md:grid-cols-2 xl:grid-cols-4 gap-6">
			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-dl-accent/10 flex items-center justify-center mb-4">
					<FileText class="w-5 h-5 text-dl-accent" />
				</div>
				<div class="text-xs font-mono text-dl-accent mb-2">docs</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">구조 spine</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					섹션 경계, 서술형 본문, retrieval 블록, 그리고 회사 지도가 공시에 발붙이게 하는 원본 증거 레이어를 관리한다.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`panel` 표준 spine
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`retrievalBlocks` · `contextSlices`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						서술형 · 상세 토픽
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">출시됨</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-accent/40 hover:shadow-dl-accent/5">
				<div class="w-10 h-10 rounded-md bg-dl-primary/10 flex items-center justify-center mb-4">
					<BarChart3 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-primary mb-2">finance</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">공식 숫자</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					재무상태표·손익계산서·현금흐름표·비율·비교 가능 시계열을 관리한다. 숫자 토픽은 여기 값이 우선.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						정규화된 재무제표
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						분기 비교 시계열
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						숫자 토픽 소스 권위
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">출시됨</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-gradient-to-br from-dl-success/10 to-dl-success/20 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono text-dl-success mb-2">report</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">정형 공시</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					감사·배당·임직원·임원 등 정기보고서 정형 API 관리. 이 토픽은 docs 가 1차 권위가 아니다.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						정기보고서 API
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						정형 거버넌스 데이터
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-success"></span>
						보고서 토픽 소스 권위
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">출시됨</Badge>
				</div>
			</Card>

			<Card class="hover:border-dl-primary/40 hover:shadow-dl-primary/5">
				<div class="w-10 h-10 rounded-md bg-gradient-to-br from-dl-primary/10 to-dl-accent/10 flex items-center justify-center mb-4">
					<Link2 class="w-5 h-5 text-dl-primary" />
				</div>
				<div class="text-xs font-mono bg-gradient-to-r from-dl-primary to-dl-accent bg-clip-text text-transparent mb-2">profile</div>
				<h3 class="text-lg font-bold text-dl-text mb-2">머지된 Company 레이어</h3>
				<p class="text-sm text-dl-text-muted leading-relaxed mb-4">
					사용자가 기본으로 보는 것: 같은 panel spine 위에 만든 단일 Company 표면. 지금은 Python 워크플로우, 다음은 AI 인터페이스.
				</p>
				<div class="space-y-2 text-xs text-dl-text-dim">
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						`c.panel(topic)`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-accent"></span>
						`c.show(...)`
					</div>
					<div class="flex items-center gap-2">
						<span class="w-1 h-1 rounded-full bg-dl-primary"></span>
						`c.trace(...)`
					</div>
				</div>
				<div class="mt-4 pt-3 border-t border-dl-border">
					<Badge variant="success">Current Default</Badge>
				</div>
			</Card>
		</div>
	</div>
</section>
