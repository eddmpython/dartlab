<script lang="ts">
	import { Card } from '$lib/components/ui/card';
	import { Scale, Shield, TrendingUp, GraduationCap, Search, Bell } from 'lucide-svelte';

	const cases = [
		{ icon: Scale, color: 'text-dl-primary bg-dl-primary/10', title: '"이 회사의 진짜 신용위험은?"', desc: '공시 데이터만으로 재구성한 독립 신용평가 (dCR) · 상환능력 · 자본구조 · 유동성 · 현금흐름 품질 · 공시 리스크. 신평사 등급도, 블랙박스도 아님. 한 줄: c.credit().' },
		{ icon: TrendingUp, color: 'text-dl-success bg-dl-success/10', title: '"맥락 속의 숫자를 보여줘"', desc: '재무제표만 보면 절반의 이야기를 놓친다. DartLab 은 BS/IS/CF 옆에 그 숫자를 설명하는 서술을 같이 둔다 · 같은 회사 · 같은 타임라인 · 같은 객체.' },
		{ icon: Shield, color: 'text-dl-accent bg-dl-accent/10', title: '"전 시장을 스크리닝"', desc: '전 상장사 2,700 개를 거버넌스 · 인력 추세 · 자본 환원 · 부채 리스크로 스캔. 한 줄: dartlab.governance("all"). 필터링·랭킹·비교.' },
		{ icon: GraduationCap, color: 'text-dl-primary bg-dl-primary/10', title: '"연구용 데이터셋 만들기"', desc: '수백 개 기업의 정규화된 텍스트 + 재무 데이터. NLP · ML 학습 · 학술 연구 즉시 사용. 클렌징·정렬 불필요 · 이미 끝나 있음.' },
		{ icon: Bell, color: 'text-dl-warning bg-dl-warning/10', title: '"실제 증거 기반 AI 분석"', desc: '원본 PDF 가 아니라 구조화된 회사 컨텍스트를 LLM 에 먹인다. 7 개 provider 지원. AI 가 hallucinate 하지 않고 실제 공시 위에서 추론.' },
		{ icon: Search, color: 'text-dl-accent bg-dl-accent/10', title: '"한국·미국 동일 도구"', desc: '한국 DART 와 미국 EDGAR 가 같은 Company 인터페이스. 한 번 배워 양 시장 적용. 같은 API 로 삼성과 Apple 비교.' }
	];
</script>

<section class="py-24 px-6 bg-dl-bg-darker/50">
	<div class="max-w-6xl mx-auto text-center">
		<span class="text-xs font-semibold uppercase tracking-widest text-dl-primary mb-3 block">할 수 있는 것</span>
		<h2 class="text-3xl md:text-4xl font-bold tracking-tight text-dl-text mb-3">DartLab 이 답하는 질문</h2>
		<p class="text-dl-text-muted max-w-xl mx-auto mb-12">
			모든 질문이 같은 회사 지도에서 시작한다. glue 코드도, 컨텍스트 전환도 없다.
		</p>

		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
			{#each cases as c}
				<Card class="text-left">
					<div class="w-10 h-10 rounded-md flex items-center justify-center mb-4 {c.color}">
						<c.icon class="w-6 h-6" />
					</div>
					<h4 class="text-base font-semibold text-dl-text mb-2">{c.title}</h4>
					<p class="text-sm text-dl-text-muted leading-relaxed">{c.desc}</p>
				</Card>
			{/each}
		</div>
	</div>
</section>
