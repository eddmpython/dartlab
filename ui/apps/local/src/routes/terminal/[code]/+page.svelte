<script lang="ts">
	import { createEngine, TerminalSurface, type RawData } from '@dartlab/ui-surfaces/terminal';
	import { getLocalRuntime } from '$lib/runtime/localRuntime';
	import { localHosts, localLinks } from '$lib/shell/terminalShell';
	import type { PageData } from './$types';

	let { data }: { data: PageData } = $props();

	// 로컬 셸 runtime 주입 — surface 는 포트만 본다(전역 locator 없음). 데이터는 /api, AI 는 /api/agent.
	const runtime = getLocalRuntime();
	const eng = $derived(createEngine(data.raw as RawData));
	const ready = $derived(
		!!data.raw.finance.years.length && Object.keys(data.raw.prices.data).length > 0
	);
</script>

<svelte:head>
	<title>Terminal · {data.code} — dartlab local</title>
</svelte:head>

{#if ready}
	<div data-qa="terminal-surface">
		<TerminalSurface {eng} {runtime} hosts={localHosts} links={localLinks} initial={data.code} />
	</div>
{:else}
	<div class="loading" data-qa="terminal-loading">로컬 서버(/api) 연결 중 …</div>
{/if}

<style>
	[data-qa='terminal-surface'] {
		height: 100vh;
	}
	.loading {
		height: 100vh;
		display: flex;
		align-items: center;
		justify-content: center;
		background: var(--dl-bg-base, #0f0f10);
		color: var(--dl-ink-mute, #6b7280);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 12px;
	}
</style>
