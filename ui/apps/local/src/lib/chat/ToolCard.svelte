<script lang="ts">
	// 작업대 카드. LLM 이 자율 호출한 도구 한 건을 데스크탑 챗 앱의 tool-use 블록처럼 표현한다.
	// 본문 흐름 안에 시간순으로 놓이며 접힌 상태는 이름 + 한 줄 요약, 펼치면 입력 인자와 결과다.
	// 결과 본문은 외부 공시·웹 본문이 섞여 있으므로 HTML 로 렌더하지 않고 모노스페이스로 격리한다.
	import type { ToolPart } from '$lib/chat/chatStore.svelte';
	import { durationLabel, toolLabel } from '$lib/chat/toolLabels';

	// live = 이 카드가 진행 표시를 맡는가. 엔진이 읽기 도구를 병렬로 돌리므로 running 이 여럿일 수 있고,
	// 그때 스피너를 다 그리면 화면에서 여러 개가 동시에 돈다. 도는 것은 언제나 하나다.
	let { tool, qaId = null, live = false }: { tool: ToolPart; qaId?: string | null; live?: boolean } =
		$props();
	let open = $state(false);

	const label = $derived(toolLabel(tool.name));
	const elapsed = $derived(tool.status === 'running' ? '' : durationLabel(tool.durationMs));

	// 인자 표시 상한. 게이트웨이가 결과는 잘라 보내지만 인자는 상한 없이 통과시킨다.
	// 산출물 본문을 인자에 싣는 도구가 있어 깊은 중첩이 오면 문자열이 수 MB 가 된다.
	const ARG_LIMIT = 8000;

	// 입력 요약. 코드를 인자로 받는 도구는 코드 그대로, 그 외는 JSON 정렬본.
	const argCode = $derived.by(() => {
		const a = tool.args ?? {};
		if (typeof a.code === 'string' && a.code.trim()) return a.code.slice(0, ARG_LIMIT);
		if (Object.keys(a).length === 0) return '';
		try {
			return JSON.stringify(a, null, 2).slice(0, ARG_LIMIT);
		} catch {
			return '';
		}
	});
	const argTruncated = $derived(argCode.length >= ARG_LIMIT);

	// 게이트웨이가 잘랐다고 알려 준 항목 + 화면이 인자를 자른 경우를 한 줄로 모은다.
	const cutNotice = $derived.by(() => {
		const parts = [...(tool.truncated ?? [])];
		if (argTruncated) parts.push('입력');
		return parts.length ? `${parts.join(', ')} 일부만 표시됩니다` : '';
	});

	// 결과 평문. markdown 이 와도 해석하지 않고 원문 그대로 격리해 보여준다.
	const resultText = $derived.by(() => {
		if (tool.markdown) return tool.markdown;
		if (tool.stdout) return tool.stdout;
		if (tool.body) return tool.body;
		if (tool.values === null || tool.values === undefined) return '';
		try {
			return JSON.stringify(tool.values, null, 2);
		} catch {
			return String(tool.values);
		}
	});

	const tableRowsPreview = $derived(tool.tableHead ?? []);
	const hasBody = $derived(
		!!(argCode || tool.error || tool.stderr || resultText || tableRowsPreview.length)
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

<div class="tool" class:err={tool.status === 'error'} data-qa={qaId ?? undefined}>
	<button
		class="head"
		type="button"
		data-qa={qaId ? `${qaId}-toggle` : undefined}
		onclick={() => (open = !open)}
		disabled={!hasBody}
		aria-expanded={open}
	>
		<span class="ico" class:spin={tool.status === 'running' && live} class:wait={tool.status === 'running' && !live}>
			{#if tool.status === 'running' && live}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
			{:else if tool.status === 'running'}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2"><circle cx="12" cy="12" r="8" /></svg>
			{:else if tool.status === 'error'}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18M6 6l12 12" /></svg>
			{:else}
				<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5" /></svg>
			{/if}
		</span>
		<span class="name">{label}</span>
		{#if tool.summary}<span class="sum">{tool.summary}</span>{/if}
		<span class="sp"></span>
		{#if elapsed}<span class="dur">{elapsed}</span>{/if}
		{#if hasBody}
			<svg class="chev" class:open viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
		{/if}
	</button>

	{#if open && hasBody}
		<div class="body" data-qa={qaId ? `${qaId}-body` : undefined}>
			{#if cutNotice}
				<!-- 잘린 결과를 완전한 결과로 읽게 두지 않는다. 근거 제품에서 가장 나쁜 침묵이다. -->
				<div class="cut" data-qa={qaId ? `${qaId}-truncated` : undefined}>{cutNotice}</div>
			{/if}
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
			{#if tableRowsPreview.length}
				<div class="seg">
					<div class="segh">결과{tool.tableRows ? ` (총 ${tool.tableRows}행 중 ${tableRowsPreview.length}행)` : ''}</div>
					<div class="tblwrap">
						<table>
							<tbody>
								{#each tableRowsPreview as row, ri (ri)}
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
			{/if}
			{#if resultText}
				<div class="seg">
					<div class="segh">결과</div>
					<pre class="code"><code>{resultText}</code></pre>
				</div>
			{/if}
			{#if tool.stderr}
				<div class="seg">
					<div class="segh">표준 오류</div>
					<pre class="code"><code>{tool.stderr}</code></pre>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	/* 본문 흐름 안에 한 줄로 놓인다. 테두리 박스를 유지하면 도구 15회가 15개 박스가
	   돼 본문을 밀어낸다(운영자 지적). 경계는 hover 와 왼쪽 가이드선으로만 준다. */
	.tool {
		border-left: 1px solid var(--dl-line, #2a2c33);
		border-radius: 0;
		background: none;
		overflow: hidden;
	}
	.tool.err {
		border-left-color: color-mix(in srgb, var(--dl-bad, #ff6b6b) 55%, var(--dl-line, #2a2c33));
	}
	.head {
		display: flex;
		align-items: center;
		gap: 0.45rem;
		width: 100%;
		padding: 0.22rem 0.55rem;
		border: none;
		border-radius: 6px;
		background: none;
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.76rem;
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
		color: var(--dl-good, #34d399);
	}
	.tool.err .ico {
		color: var(--dl-bad, #ff6b6b);
	}
	.ico.spin {
		color: var(--dl-info, #6ab0ff);
		animation: spin 0.9s linear infinite;
	}
	/* 병렬 실행 대기분. 도는 대신 자리만 지킨다. */
	.ico.wait {
		color: var(--dl-ink-mute, #6b7280);
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
	.dur {
		flex-shrink: 0;
		font-variant-numeric: tabular-nums;
		color: color-mix(in srgb, var(--dl-ink-mute, #6b7280) 70%, transparent);
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
	/* 절단 고지. 경고 색을 쓰되 판때기로 만들지 않는다. 실패가 아니라 사실 통지다. */
	.cut {
		font-size: 0.68rem;
		color: var(--dl-warn, #f4b740);
		padding: 0.3rem 0.5rem;
		border-left: 2px solid var(--dl-warn, #f4b740);
		background: color-mix(in srgb, #f4b740 7%, transparent);
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
