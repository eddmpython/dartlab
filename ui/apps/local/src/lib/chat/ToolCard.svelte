<script lang="ts">
	// 작업대 카드. LLM 이 자율 호출한 도구 한 건을 ChatGPT/Claude 의 tool-use 블록처럼 표현한다.
	// 진행중이면 spinner + 이름, 완료면 접힌 카드. 클릭하면 입력(args)과 결과(표/마크다운/stdout)를 펼친다.
	import type { ToolBlock } from '$lib/chat/chatStore.svelte';
	import Markdown from '$lib/chat/Markdown.svelte';

	let { tool }: { tool: ToolBlock } = $props();
	let open = $state(false);

	// 도구 표시명을 한국어 라벨로. 없으면 원본 이름 그대로.
	const LABELS: Record<string, string> = {
		RunPython: '코드 실행',
		'run python': '코드 실행',
		EngineCall: '엔진 호출',
		'engine call': '엔진 호출',
		ReadSkill: '스킬 조회',
		'read skill': '스킬 조회',
		GetSkillBody: '스킬 본문',
		ReadCapability: 'API 조회',
		'read capability': 'API 조회',
		WebSearch: '웹 검색',
		'web search': '웹 검색',
		Read: '파일 인용',
		SaveArtifact: '산출물 저장',
		CompileVisual: '차트 생성',
		CompileFinancialDashboard: '재무 대시보드',
		PeerCompareN: '동종사 비교',
		DCFValuation: 'DCF 가치평가',
		SensitivityAnalysis: '민감도 분석',
		ScenarioCompareN: '시나리오 비교',
		CreditScorecard: '신용 스코어카드',
		RegressionForecast: '회귀 예측',
		SearchPastSessions: '과거 세션 검색',
		Verify: '근거 검증',
		verify: '근거 검증'
	};

	const label = $derived(LABELS[tool.name] ?? tool.name);

	// 입력 요약. RunPython 은 code, EngineCall 은 apiRef, 그 외는 JSON.
	const argCode = $derived.by(() => {
		const a = tool.args ?? {};
		if (typeof a.code === 'string' && a.code.trim()) return a.code;
		const keys = Object.keys(a);
		if (keys.length === 0) return '';
		try {
			return JSON.stringify(a, null, 2);
		} catch {
			return '';
		}
	});

	const hasBody = $derived(
		!!(tool.markdown || tool.stdout || (tool.tableHead && tool.tableHead.length) || argCode || tool.error)
	);

	function cell(v: unknown): string {
		if (v === null || v === undefined) return '';
		if (typeof v === 'object') {
			try {
				return JSON.stringify(v);
			} catch {
				return String(v);
			}
		}
		return String(v);
	}
</script>

<div class="tool" class:err={tool.status === 'error'}>
	<button
		class="head"
		onclick={() => (open = !open)}
		disabled={!hasBody && tool.status !== 'running'}
		aria-expanded={open}
	>
		<span class="ico" class:spin={tool.status === 'running'}>
			{#if tool.status === 'running'}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
			{:else if tool.status === 'error'}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
			{:else}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
			{/if}
		</span>
		<span class="name">{label}</span>
		{#if tool.summary}<span class="sum">{tool.summary}</span>{/if}
		<span class="sp"></span>
		{#if hasBody}
			<svg class="chev" class:open viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
		{/if}
	</button>

	{#if open && hasBody}
		<div class="body">
			{#if argCode}
				<div class="seg">
					<div class="segh">입력 · {tool.name}</div>
					<pre class="code"><code>{argCode}</code></pre>
				</div>
			{/if}
			{#if tool.error}
				<div class="seg">
					<div class="segh">오류</div>
					<div class="errline">{tool.error}</div>
				</div>
			{/if}
			{#if tool.markdown}
				<div class="seg">
					<div class="segh">결과</div>
					<Markdown text={tool.markdown} />
				</div>
			{:else if tool.tableHead && tool.tableHead.length}
				<div class="seg">
					<div class="segh">결과{tool.tableRows ? ` (총 ${tool.tableRows}행 중 ${tool.tableHead.length}행)` : ''}</div>
					<div class="tblwrap">
						<table>
							<tbody>
								{#each tool.tableHead as row, ri (ri)}
									<tr>
										{#if Array.isArray(row)}
											{#each row as c, ci (ci)}<td>{cell(c)}</td>{/each}
										{:else}
											<td>{cell(row)}</td>
										{/if}
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{:else if tool.stdout}
				<div class="seg">
					<div class="segh">출력</div>
					<pre class="code"><code>{tool.stdout}</code></pre>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.tool {
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 9px;
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 55%, transparent);
		overflow: hidden;
	}
	.tool.err {
		border-color: color-mix(in srgb, var(--dl-bad, #ff6b6b) 35%, var(--dl-line, #2a2c33));
	}
	.head {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		width: 100%;
		padding: 0.4rem 0.6rem;
		border: none;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.78rem;
		text-align: left;
		cursor: pointer;
	}
	.head:disabled {
		cursor: default;
	}
	.head:hover:not(:disabled) {
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 70%, transparent);
	}
	.ico {
		display: inline-flex;
		flex-shrink: 0;
		color: var(--dl-good, #4ade80);
	}
	.tool.err .ico {
		color: var(--dl-bad, #ff6b6b);
	}
	.ico.spin {
		color: var(--dl-info, #6ab0ff);
		animation: spin 0.9s linear infinite;
	}
	@keyframes spin {
		to {
			transform: rotate(360deg);
		}
	}
	.name {
		font-weight: 600;
		color: var(--dl-ink, #e7e7ea);
		flex-shrink: 0;
	}
	.sum {
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
		min-width: 0;
	}
	.sp {
		flex: 1;
	}
	.chev {
		flex-shrink: 0;
		transition: transform 0.15s ease;
	}
	.chev.open {
		transform: rotate(180deg);
	}
	.body {
		padding: 0.2rem 0.7rem 0.7rem;
		border-top: 1px solid var(--dl-line, #2a2c33);
		display: flex;
		flex-direction: column;
		gap: 0.6rem;
	}
	.seg {
		display: flex;
		flex-direction: column;
		gap: 0.3rem;
	}
	.segh {
		font-size: 0.68rem;
		font-weight: 600;
		text-transform: uppercase;
		letter-spacing: 0.04em;
		color: var(--dl-ink-mute, #6b7280);
		margin-top: 0.4rem;
	}
	.code {
		margin: 0;
		padding: 0.6rem 0.7rem;
		max-height: 20rem;
		overflow: auto;
		background: var(--dl-bg-base, #0f0f10);
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 7px;
		font-size: 0.74rem;
		line-height: 1.55;
		white-space: pre;
	}
	.code code {
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		color: var(--dl-ink, #e7e7ea);
	}
	.errline {
		font-size: 0.78rem;
		color: var(--dl-bad, #ff6b6b);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
	}
	.tblwrap {
		overflow-x: auto;
	}
	.tblwrap table {
		border-collapse: collapse;
		font-size: 0.74rem;
		width: max-content;
		max-width: 100%;
	}
	.tblwrap td {
		padding: 0.3rem 0.55rem;
		border: 1px solid var(--dl-line, #2a2c33);
		white-space: nowrap;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	.tblwrap tr:first-child td {
		color: var(--dl-ink, #e7e7ea);
		font-weight: 600;
		background: var(--dl-bg-raised, #16171a);
	}
</style>
