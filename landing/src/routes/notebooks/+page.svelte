<script lang="ts">
	import { base } from '$app/paths';
	import Notebook from '$lib/components/notebook/Notebook.svelte';
</script>

<svelte:head>
	<title>Notebook · dartlab 전자공시 재무분석</title>
	<meta
		name="description"
		content="브라우저에서 바로 실행하는 dartlab 노트북. 설치 없이 셀 단위로 한국 전자공시 재무제표와 분석을 실행하고 결과를 표로 확인하세요."
	/>
</svelte:head>

<div class="min-h-screen bg-dl-bg-dark text-dl-text">
	<div class="mx-auto max-w-5xl px-6 pt-16 pb-20">
		<div class="mb-8">
			<a
				href="{base}/"
				class="text-sm text-dl-text-muted transition-colors hover:text-dl-text">← dartlab</a
			>
			<div class="mt-3 flex items-baseline gap-3">
				<h1 class="text-3xl font-bold">dartlab <span class="text-dl-primary">notebook</span></h1>
				<span
					class="rounded border border-dl-border px-2 py-0.5 font-mono text-[11px] text-dl-text-dim"
					>beta</span
				>
			</div>
			<p class="mt-2 max-w-2xl text-dl-text-muted">
				설치 없이 브라우저에서 실행하는 파이썬 노트북. 셀에 <code
					class="rounded bg-dl-bg-card px-1.5 py-0.5 font-mono text-sm text-dl-text">c.panel("IS")</code
				> 를 쓰면 실제 전자공시 재무제표가 표로 나옵니다. 커널은 dartlab pyodide, 데이터는 HuggingFace 직독.
			</p>
		</div>

		<Notebook />

		<p class="mt-8 text-xs leading-relaxed text-dl-text-dim">
			브라우저 런타임은 회사 재무제표(<code class="font-mono">c.panel</code>)·재무분석(<code
				class="font-mono">c.analysis</code
			>)과 industry / macro 축을 지원합니다. 라이브 수집(실시간 시세·뉴스)과 전종목 대형 scan 은 브라우저
			범위 밖입니다.
		</p>
	</div>
</div>
