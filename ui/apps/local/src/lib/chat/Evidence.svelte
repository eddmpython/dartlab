<script lang="ts">
	// 근거. Ask 엔진이 답변을 뒷받침하려고 확보한 ref (표/값/문서/웹) 를 각주처럼 표시한다.
	// 접힌 상태는 "근거 N" 요약, 펼치면 출처와 핵심 payload 를 보여준다 (ChatGPT/Claude 인용 벤치마크).
	import type { EvidenceRef } from '@dartlab/ui-contracts';

	let { refs }: { refs: EvidenceRef[] } = $props();
	let open = $state(false);

	const KIND_LABEL: Record<string, string> = {
		tableRef: '표',
		valueRef: '값',
		webRef: '웹',
		artifactRef: '산출물',
		visualRef: '차트',
		skillRef: '스킬',
		docRef: '문서'
	};

	// payload 에서 사람이 읽을 핵심 키만 골라 한 줄 요약.
	const PAYLOAD_KEYS: [string, string][] = [
		['stockCode', ''],
		['period', ''],
		['metric', ''],
		['value', ''],
		['unit', ''],
		['dataAsOf', '기준'],
		['page', 'p.']
	];

	function summarize(ref: EvidenceRef): string {
		const p = ref.payload as Record<string, unknown> | undefined;
		if (!p || typeof p !== 'object') return '';
		const parts: string[] = [];
		for (const [k, prefix] of PAYLOAD_KEYS) {
			const v = p[k];
			if (v === null || v === undefined || v === '') continue;
			parts.push(prefix ? `${prefix}${v}` : String(v));
		}
		return parts.join(' · ');
	}

	function host(url: string): string {
		try {
			return new URL(url).host;
		} catch {
			return url;
		}
	}
</script>

<div class="ev">
	<button class="evhead" onclick={() => (open = !open)} aria-expanded={open}>
		<svg viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
		<span>근거 {refs.length}</span>
		<svg class="chev" class:open viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
	</button>

	{#if open}
		<ol class="list">
			{#each refs as r, i (r.id)}
				<li>
					<span class="num">{i + 1}</span>
					<span class="kind">{KIND_LABEL[r.kind] ?? r.kind}</span>
					<div class="meta">
						<span class="title">{r.title || r.id}</span>
						{#if summarize(r)}<span class="pay">{summarize(r)}</span>{/if}
						{#if r.kind === 'webRef' && r.source}
							<a class="src" href={r.source} target="_blank" rel="noopener">{host(r.source)}</a>
						{:else if r.source}
							<span class="src">{r.source}</span>
						{/if}
					</div>
				</li>
			{/each}
		</ol>
	{/if}
</div>

<style>
	.ev {
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 9px;
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 45%, transparent);
		overflow: hidden;
	}
	.evhead {
		display: flex;
		align-items: center;
		gap: 0.4rem;
		width: 100%;
		padding: 0.4rem 0.6rem;
		border: none;
		background: none;
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.78rem;
		font-weight: 600;
		text-align: left;
		cursor: pointer;
	}
	.evhead:hover {
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 70%, transparent);
	}
	.chev {
		margin-left: auto;
		transition: transform 0.15s ease;
	}
	.chev.open {
		transform: rotate(180deg);
	}
	.list {
		margin: 0;
		padding: 0.1rem 0.6rem 0.55rem;
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 0.35rem;
		border-top: 1px solid var(--dl-line, #2a2c33);
	}
	li {
		display: flex;
		align-items: baseline;
		gap: 0.45rem;
		font-size: 0.76rem;
	}
	.num {
		flex-shrink: 0;
		width: 1.15rem;
		height: 1.15rem;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border-radius: 50%;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		font-size: 0.64rem;
		color: var(--dl-ink-dim, #9aa0aa);
		align-self: center;
	}
	.kind {
		flex-shrink: 0;
		padding: 0.05rem 0.35rem;
		border-radius: 4px;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		font-size: 0.64rem;
		color: var(--dl-ink-mute, #6b7280);
		align-self: center;
	}
	.meta {
		min-width: 0;
		display: flex;
		flex-wrap: wrap;
		align-items: baseline;
		gap: 0.2rem 0.5rem;
	}
	.title {
		color: var(--dl-ink, #e7e7ea);
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.pay {
		color: var(--dl-ink-dim, #9aa0aa);
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 0.7rem;
	}
	.src {
		color: var(--dl-ink-mute, #6b7280);
		font-size: 0.7rem;
		text-decoration: none;
	}
	a.src:hover {
		color: var(--dl-info, #6ab0ff);
		text-decoration: underline;
	}
</style>
