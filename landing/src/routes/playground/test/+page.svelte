<script lang="ts">
	import { base } from '$app/paths';
	import Playground from '$lib/components/blog/Playground.svelte';
</script>

<svelte:head>
	<title>Playground 컴포넌트 검증 · dartlab</title>
	<meta name="robots" content="noindex" />
</svelte:head>

<div class="min-h-screen bg-dl-bg-dark text-dl-text">
	<div class="mx-auto max-w-3xl px-6 pt-20 pb-16">
		<a href="{base}/" class="text-dl-text-muted text-sm hover:text-dl-text">← dartlab</a>
		<h1 class="text-2xl font-bold mt-3 mb-2">Playground 컴포넌트 검증</h1>
		<p class="text-dl-text-muted text-sm mb-2">
			블로그 삽입용 <code>&lt;Playground&gt;</code> 카드 + 모달이 실제로 Pyodide 위에서 dartlab을 실행하는지 확인하는 임시 페이지.
		</p>
		<ul class="text-xs text-dl-text-dim space-y-1 mb-8 list-disc pl-5">
			<li>① 첫 카드 ▶ → 5단계 스테퍼 → 자동 실행 → 출력 확인 (8~12초)</li>
			<li>② 닫고 두 번째 카드 ▶ → 스테퍼 스킵, 즉시 실행 (싱글턴 공유 확인)</li>
			<li>③ 세 번째 카드 ▶ → 다른 종목(AAPL) → ensureCompany 동작 확인</li>
		</ul>

		<h2 class="text-sm font-semibold text-dl-text-muted mb-2">1) 삼성전자 손익계산서</h2>
		<Playground
			label="samsung-IS"
			stockCode="005930"
			code={`print(c.panel("IS"))`}
		/>

		<h2 class="text-sm font-semibold text-dl-text-muted mb-2 mt-8">2) 삼성전자 재무비율</h2>
		<Playground
			label="samsung-ratios"
			stockCode="005930"
			code={`print(c.panel("ratios"))`}
		/>

		<h2 class="text-sm font-semibold text-dl-text-muted mb-2 mt-8">3) Apple 손익계산서 (다른 종목)</h2>
		<Playground
			label="apple-IS"
			stockCode="AAPL"
			code={`print(c.panel("IS"))`}
		/>
	</div>
</div>
