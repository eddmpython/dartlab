<script lang="ts">
	import { base } from '$app/paths';
	import Notebook from '$lib/components/notebook/Notebook.svelte';
</script>

<svelte:head>
	<title>Notebook · dartlab</title>
	<meta
		name="description"
		content="브라우저에서 바로 실행하는 범용 파이썬 노트북. 설치 없이 numpy·pandas·matplotlib 을 쓰고 표와 그래프를 셀에서 확인하세요. 어디든 임베드 가능."
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
				브라우저에서 바로 실행하는 범용 파이썬 노트북. 설치 없이 <code
					class="rounded bg-dl-bg-card px-1.5 py-0.5 font-mono text-sm text-dl-text">numpy</code
				>, <code class="rounded bg-dl-bg-card px-1.5 py-0.5 font-mono text-sm text-dl-text">pandas</code
				>, <code class="rounded bg-dl-bg-card px-1.5 py-0.5 font-mono text-sm text-dl-text"
					>matplotlib</code
				> 을 그대로 쓰고, 표와 그래프가 셀 안에 렌더됩니다. 코드는 전부 브라우저 안에서만 실행됩니다.
			</p>
		</div>

		<Notebook />

		<p class="mt-8 text-xs leading-relaxed text-dl-text-dim">
			pyodide 배포 패키지(numpy, pandas, matplotlib, polars 등)는 자동 로드되고, <code
				class="font-mono">micropip</code
			> 으로 추가 설치도 됩니다. 필요하면 셀에서 dartlab 을 불러 실데이터도 다룰 수 있습니다.
		</p>
	</div>
</div>
