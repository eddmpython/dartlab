<script lang="ts">
	import { base } from '$app/paths';
	import {
		pyodideStore,
		initPyodide,
		runCode,
		setProviderKey
	} from '$lib/stores/pyodide.svelte';

	let stockCode = $state('005930');
	let output = $state('');
	let running = $state(false);

	let aiProvider = $state('gemini');
	let apiKey = $state('');
	let aiLoading = $state(false);

	async function start() {
		if (pyodideStore.status === 'loading' || pyodideStore.status === 'ready') return;
		try {
			await initPyodide(stockCode);
		} catch {
			/* store has errorMsg */
		}
	}

	async function run(code: string) {
		if (pyodideStore.status !== 'ready' || running) return;
		running = true;
		const r = await runCode(code);
		output = r.output || (r.ok ? '(결과 없음)' : '(오류)');
		running = false;
	}

	async function runAsk() {
		if (pyodideStore.status !== 'ready' || !apiKey.trim() || aiLoading) return;
		aiLoading = true;
		try {
			await setProviderKey(aiProvider, apiKey.trim());
			const r = await runCode(`
import traceback, io
try:
    answer = dartlab.ask("${pyodideStore.currentStock} 수익성 분석해줘", provider="${aiProvider}", stream=False)
    if answer:
        print(answer)
    else:
        print("응답 없음")
except Exception:
    buf = io.StringIO(); traceback.print_exc(file=buf); print(buf.getvalue())
`);
			output = r.output;
		} finally {
			aiLoading = false;
		}
	}

	const commands = [
		{ label: 'show IS', desc: '손익계산서', code: 'print(c.show("IS"))' },
		{ label: 'show BS', desc: '재무상태표', code: 'print(c.show("BS"))' },
		{ label: 'show CF', desc: '현금흐름표', code: 'print(c.show("CF"))' },
		{
			label: 'analysis',
			desc: '수익성 분석',
			code: `r = c.analysis("financial", "수익성")
if r:
    for k,v in r.items(): print(f"  {k}: {type(v).__name__}")`
		},
		{
			label: 'review',
			desc: '6막 보고서',
			code: `import traceback, io
try:
    print(c.story("수익성").toMarkdown())
except Exception:
    buf = io.StringIO(); traceback.print_exc(file=buf); print(buf.getvalue())`
		}
	];

	const stepLabels: Record<string, string> = {
		pyodide: 'Pyodide 엔진',
		packages: '패키지 로드',
		wheel: 'dartlab 설치',
		data: '데이터 다운로드',
		init: '초기화',
		done: '완료'
	};
</script>

<svelte:head>
	<title>Playground · dartlab 전자공시 재무분석</title>
	<meta
		name="description"
		content="브라우저에서 바로 실행하는 한국 전자공시 재무분석. 설치 없이 dartlab을 체험하세요."
	/>
</svelte:head>

<div class="min-h-screen bg-dl-bg-dark text-dl-text">
	<div class="mx-auto max-w-4xl px-6 pt-20 pb-16">
		<div class="mb-10">
			<a
				href="{base}/"
				class="text-dl-text-muted text-sm hover:text-dl-text transition-colors">← dartlab</a
			>
			<h1 class="text-3xl font-bold mt-3 mb-2">Playground</h1>
			<p class="text-dl-text-muted">브라우저에서 바로 실행. 설치 없음.</p>
		</div>

		{#if pyodideStore.status !== 'ready'}
			<div class="rounded-lg border border-dl-border bg-dl-bg-card p-6 mb-6">
				<div class="flex items-center gap-3 mb-5">
					<input
						type="text"
						bind:value={stockCode}
						placeholder="종목코드"
						disabled={pyodideStore.status === 'loading'}
						class="w-28 px-3 py-2 rounded bg-dl-bg-dark border border-dl-border text-dl-text font-mono text-sm focus:border-dl-primary outline-none"
					/>
					<button
						onclick={start}
						disabled={pyodideStore.status === 'loading'}
						class="px-5 py-2 rounded font-medium text-sm transition-colors
							{pyodideStore.status === 'loading'
							? 'bg-dl-bg-dark text-dl-text-muted cursor-wait'
							: 'bg-dl-primary text-white hover:bg-dl-primary-dark cursor-pointer'}"
					>
						{#if pyodideStore.status === 'loading'}초기화 중...{:else}시작{/if}
					</button>
				</div>

				{#if pyodideStore.status === 'loading' || pyodideStore.status === 'idle'}
					<div class="flex items-center gap-2 text-sm text-dl-primary mb-2">
						<span class="animate-spin">{pyodideStore.status === 'loading' ? '⟳' : ''}</span>
						<span>{stepLabels[pyodideStore.step] || pyodideStore.step || '대기'}</span>
						<span class="text-dl-text-dim ml-auto"
							>{Math.round(pyodideStore.progress * 100)}%</span
						>
					</div>
					<div class="h-1 bg-dl-bg-dark rounded overflow-hidden mb-3">
						<div
							class="h-full bg-dl-primary transition-all"
							style:width="{pyodideStore.progress * 100}%"
						></div>
					</div>
				{/if}

				{#if pyodideStore.status === 'error'}
					<div class="rounded border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-400">
						<div class="font-medium mb-1">초기화 실패</div>
						<div class="text-xs whitespace-pre-wrap">{pyodideStore.errorMsg}</div>
					</div>
				{/if}
			</div>
		{/if}

		{#if pyodideStore.status === 'ready'}
			<div class="rounded-lg border border-dl-border bg-dl-bg-card p-5 mb-4">
				<div class="flex flex-wrap gap-2 mb-4">
					{#each commands as cmd}
						<button
							onclick={() => run(cmd.code)}
							disabled={running}
							class="px-3 py-1.5 rounded text-sm border border-dl-border bg-dl-bg-dark
								hover:border-dl-primary hover:text-dl-primary transition-colors cursor-pointer
								disabled:opacity-50 disabled:cursor-wait"
							title={cmd.desc}
						>
							{cmd.label}
						</button>
					{/each}
				</div>

				<div class="flex items-center gap-2 pt-3 border-t border-dl-border">
					<select
						bind:value={aiProvider}
						class="px-2 py-1.5 rounded text-sm bg-dl-bg-dark border border-dl-border text-dl-text"
					>
						<option value="gemini">Gemini</option>
						<option value="openai">OpenAI</option>
					</select>
					<input
						type="password"
						bind:value={apiKey}
						placeholder="API 키"
						class="flex-1 max-w-xs px-3 py-1.5 rounded text-sm bg-dl-bg-dark border border-dl-border text-dl-text font-mono focus:border-dl-primary outline-none"
					/>
					<button
						onclick={runAsk}
						disabled={aiLoading || !apiKey.trim()}
						class="px-4 py-1.5 rounded text-sm font-medium transition-colors cursor-pointer
							{aiLoading
							? 'bg-dl-bg-dark text-dl-text-muted cursor-wait'
							: !apiKey.trim()
								? 'bg-dl-bg-dark text-dl-text-dim cursor-not-allowed'
								: 'bg-dl-accent text-white hover:bg-dl-accent-light'}"
					>
						{#if aiLoading}분석 중...{:else}AI ask{/if}
					</button>
				</div>
			</div>
		{/if}

		<pre
			class="rounded-lg bg-dl-bg-card border border-dl-border p-4 min-h-48 max-h-[60vh] overflow-y-auto text-xs font-mono text-dl-text-muted leading-relaxed whitespace-pre-wrap">{output ||
				pyodideStore.logs.join('\n')}</pre>
	</div>
</div>
