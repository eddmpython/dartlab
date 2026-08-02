<script lang="ts">
	import { tick } from 'svelte';
	import type { EvidenceRef } from '@dartlab/ui-contracts';
	import type { ProductOutcomeReceipt } from '$lib/generated/agentRuntime';
	import { verifyOutcomeEvidence } from '$lib/runtime/agentRuntimeApi';

	let {
		refs,
		citedRefIds = null,
		verifiedRefIds = [],
		onverified = () => undefined
	}: {
		refs: EvidenceRef[];
		citedRefIds?: string[] | null;
		verifiedRefIds?: string[];
		onverified?: (refId: string) => void;
	} = $props();

	let open = $state(false);
	let selectedId = $state<string | null>(null);
	let detailHeading: HTMLHeadingElement | null = $state(null);
	let states = $state<Record<string, 'busy' | 'verified' | 'error'>>({});
	let errors = $state<Record<string, string>>({});
	let resolved = $state<Record<string, EvidenceRef>>({});
	let receiptDetails = $state<Record<string, ProductOutcomeReceipt>>({});

	const cited = $derived(new Set(citedRefIds ?? []));
	const verified = $derived(new Set(verifiedRefIds));
	const hasCitationDecision = $derived(citedRefIds !== null);
	const usedCount = $derived(refs.filter((ref) => cited.has(ref.id)).length);
	const selected = $derived(refs.find((ref) => ref.id === selectedId) ?? null);
	const actual = $derived(selected ? (resolved[selected.id] ?? selected) : null);
	const payloadEntries = $derived.by(() => {
		const payload = actual?.payload;
		return payload && typeof payload === 'object' && !Array.isArray(payload)
			? Object.entries(payload as Record<string, unknown>)
			: [];
	});

	const KIND_LABEL: Record<string, string> = {
		tableRef: '표',
		valueRef: '값',
		dateRef: '기준일',
		webRef: '웹',
		artifactRef: '산출물',
		visualRef: '차트',
		skillRef: '스킬',
		docRef: '문서'
	};

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
		const detail = resolved[ref.id] ?? ref;
		const payload = detail.payload as Record<string, unknown> | undefined;
		if (!payload || typeof payload !== 'object') return '';
		const parts: string[] = [];
		for (const [key, prefix] of PAYLOAD_KEYS) {
			const value = payload[key];
			if (value === null || value === undefined || value === '') continue;
			parts.push(prefix ? `${prefix}${value}` : String(value));
		}
		return parts.join(' · ');
	}

	function safeExternalUrl(value: string): string | null {
		try {
			const url = new URL(value);
			return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null;
		} catch {
			return null;
		}
	}

	function host(url: string): string {
		try {
			return new URL(url).host;
		} catch {
			return url;
		}
	}

	function formatValue(value: unknown): string {
		if (value === null) return 'null';
		if (value === undefined) return '';
		if (typeof value === 'string') return value;
		try {
			return JSON.stringify(value, null, 2);
		} catch {
			return String(value);
		}
	}

	function isVerified(refId: string): boolean {
		return states[refId] === 'verified' || verified.has(refId);
	}

	async function resolveAndVerify(ref: EvidenceRef): Promise<void> {
		if (!ref.outcomeId || states[ref.id] === 'busy' || isVerified(ref.id)) return;
		states[ref.id] = 'busy';
		delete errors[ref.id];
		try {
			const value = await verifyOutcomeEvidence(ref.outcomeId, ref.id);
			resolved[ref.id] = { ...ref, ...value.evidence };
			receiptDetails[ref.id] = value.receipt;
			states[ref.id] = 'verified';
			onverified(ref.id);
		} catch (reason) {
			states[ref.id] = 'error';
			errors[ref.id] = reason instanceof Error ? reason.message : String(reason);
		}
	}

	async function showDetail(ref: EvidenceRef): Promise<void> {
		open = true;
		selectedId = ref.id;
		await resolveAndVerify(ref);
		await tick();
		detailHeading?.focus();
	}

	export async function openRef(refId: string): Promise<void> {
		const ref = refs.find((item) => item.id === refId);
		if (ref) await showDetail(ref);
	}
</script>

<div class="ev">
	<button class="evhead" onclick={() => (open = !open)} aria-expanded={open}>
		<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" /></svg>
		<span>{hasCitationDecision ? `답변 사용 ${usedCount} · 보조 ${refs.length - usedCount}` : `수집 근거 ${refs.length}`}</span>
		{#if verified.size}<span class="verifiedCount">사용자 확인 {verified.size}</span>{/if}
		<svg class="chev" class:open viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6" /></svg>
	</button>

	{#if open}
		<ol class="list">
			{#each refs as ref, index (ref.id)}
				<li class:used={cited.has(ref.id)}>
					<span class="num">{index + 1}</span>
					<span class="kind">{KIND_LABEL[ref.kind] ?? ref.kind}</span>
					<div class="meta">
						<span class="title">{ref.title || ref.id}</span>
						<span class="useState">{hasCitationDecision ? (cited.has(ref.id) ? '답변에 사용' : '보조 근거') : '수집됨'}</span>
						{#if summarize(ref)}<span class="pay">{summarize(ref)}</span>{/if}
						{#if ref.source && safeExternalUrl(ref.source)}
							<a class="src" href={safeExternalUrl(ref.source) ?? undefined} target="_blank" rel="noopener">{host(ref.source)}</a>
						{:else if ref.source}
							<span class="src">{ref.source}</span>
						{/if}
					</div>
					<button class="verify" onclick={() => showDetail(ref)} disabled={states[ref.id] === 'busy'}>
						{states[ref.id] === 'busy' ? '확인 중' : isVerified(ref.id) ? '다시 열기' : states[ref.id] === 'error' ? '다시 확인' : '근거 열기'}
					</button>
				</li>
			{/each}
		</ol>

		{#if actual}
			<section class="detail" aria-label="exact evidence 상세">
				<header>
					<div>
						<h3 bind:this={detailHeading} tabindex="-1">{actual.title || actual.id}</h3>
						<p>{isVerified(actual.id) ? '사용자가 연 exact evidence · receipt 확인 완료' : 'exact evidence 미리보기'}</p>
					</div>
					<button class="close" onclick={() => (selectedId = null)} aria-label="근거 상세 닫기">✕</button>
				</header>
				<dl>
					<div><dt>Ref ID</dt><dd><code>{actual.id}</code></dd></div>
					<div><dt>종류</dt><dd>{KIND_LABEL[actual.kind] ?? actual.kind}</dd></div>
					<div><dt>소스 유형</dt><dd>{actual.sourceType || 'internal'}</dd></div>
					{#if actual.source}<div><dt>소스</dt><dd>{actual.source}</dd></div>{/if}
					{#if receiptDetails[actual.id]}
						<div><dt>사용자 검증</dt><dd>{receiptDetails[actual.id].state} · {new Date(receiptDetails[actual.id].updatedAt).toLocaleString('ko-KR')}</dd></div>
					{/if}
				</dl>
				<div class="payload">
					<h4>근거 내용</h4>
					{#if payloadEntries.length}
						{#each payloadEntries as [key, value] (key)}
							<div class="payloadRow"><span>{key}</span><pre>{formatValue(value)}</pre></div>
						{/each}
					{:else}
						<p class="emptyPayload">정형 payload가 없는 출처 근거입니다.</p>
					{/if}
				</div>
				{#if errors[actual.id]}<p class="detailError" role="alert">{errors[actual.id]}</p>{/if}
			</section>
		{/if}
	{/if}
</div>

<style>
	.ev { border: 1px solid var(--dl-line, #2a2c33); border-radius: 10px; background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 45%, transparent); overflow: hidden; }
	.evhead { display: flex; align-items: center; gap: .45rem; width: 100%; min-height: 2.75rem; padding: .5rem .7rem; border: 0; background: none; color: var(--dl-ink-dim, #9aa0aa); font-size: .78rem; font-weight: 600; text-align: left; cursor: pointer; }
	.evhead:hover { background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 70%, transparent); }
	.verifiedCount { color: #70d6a5; font-size: .68rem; font-weight: 500; }
	.chev { margin-left: auto; transition: transform .15s ease; }
	.chev.open { transform: rotate(180deg); }
	.list { margin: 0; padding: .35rem .65rem .65rem; list-style: none; display: grid; gap: .4rem; border-top: 1px solid var(--dl-line, #2a2c33); }
	li { display: grid; grid-template-columns: auto auto minmax(0, 1fr) auto; align-items: center; gap: .45rem; min-width: 0; padding: .2rem 0; font-size: .76rem; }
	li.used { border-left: 2px solid #70d6a5; padding-left: .45rem; }
	.num { flex-shrink: 0; width: 1.2rem; height: 1.2rem; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; background: var(--dl-bg-raised, #16171a); border: 1px solid var(--dl-line, #2a2c33); font-size: .64rem; color: var(--dl-ink-dim, #9aa0aa); }
	.kind, .useState { width: fit-content; padding: .08rem .35rem; border-radius: 4px; border: 1px solid var(--dl-line, #2a2c33); font-size: .64rem; color: var(--dl-ink-mute, #6b7280); }
	li.used .useState { color: #70d6a5; border-color: color-mix(in srgb, #70d6a5 35%, var(--dl-line, #2a2c33)); }
	.meta { min-width: 0; display: flex; flex-wrap: wrap; align-items: baseline; gap: .25rem .5rem; overflow-wrap: anywhere; }
	.title { color: var(--dl-ink, #e7e7ea); overflow: hidden; text-overflow: ellipsis; }
	.pay { color: var(--dl-ink-dim, #9aa0aa); font-family: var(--dl-font-mono, ui-monospace, monospace); font-size: .7rem; }
	.src { color: var(--dl-ink-mute, #6b7280); font-size: .7rem; text-decoration: none; overflow-wrap: anywhere; }
	a.src:hover { color: var(--dl-info, #6ab0ff); text-decoration: underline; }
	.verify, .close { min-width: 2.75rem; min-height: 2.75rem; border: 1px solid var(--dl-line, #2a2c33); border-radius: 7px; padding: .35rem .6rem; background: transparent; color: var(--dl-info, #6ab0ff); font-size: .7rem; cursor: pointer; }
	.verify:disabled { color: var(--dl-ink-mute, #6b7280); cursor: wait; }
	.detail { border-top: 1px solid var(--dl-line, #2a2c33); padding: .85rem; background: var(--dl-bg-raised, #16171a); display: grid; gap: .75rem; }
	.detail header { display: flex; align-items: flex-start; gap: .75rem; }
	.detail header > div { flex: 1; min-width: 0; }
	.detail h3 { margin: 0; color: var(--dl-ink, #e7e7ea); font-size: .9rem; overflow-wrap: anywhere; outline: none; }
	.detail header p { margin: .25rem 0 0; color: #70d6a5; font-size: .7rem; }
	.close { padding: 0; color: var(--dl-ink-dim, #9aa0aa); }
	dl { display: grid; gap: .35rem; margin: 0; }
	dl div { display: grid; grid-template-columns: 6rem minmax(0, 1fr); gap: .6rem; align-items: baseline; }
	dt { color: var(--dl-ink-mute, #6b7280); font-size: .68rem; }
	dd { min-width: 0; margin: 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .74rem; overflow-wrap: anywhere; }
	dd code { white-space: normal; overflow-wrap: anywhere; }
	.payload { display: grid; gap: .4rem; }
	.payload h4 { margin: 0; color: var(--dl-ink, #e7e7ea); font-size: .75rem; }
	.payloadRow { display: grid; grid-template-columns: minmax(5rem, .35fr) minmax(0, 1fr); gap: .65rem; padding: .45rem .55rem; border-radius: 7px; background: var(--dl-bg-base, #0f0f10); }
	.payloadRow > span { color: var(--dl-ink-mute, #6b7280); font-size: .7rem; overflow-wrap: anywhere; }
	.payloadRow pre { margin: 0; color: var(--dl-ink, #e7e7ea); font: .72rem/1.5 var(--dl-font-mono, ui-monospace, monospace); white-space: pre-wrap; overflow-wrap: anywhere; }
	.emptyPayload, .detailError { margin: 0; color: var(--dl-ink-dim, #9aa0aa); font-size: .75rem; }
	.detailError { color: var(--dl-bad, #ff6b6b); }
	@media (max-width: 520px) {
		li { grid-template-columns: auto auto minmax(0, 1fr); align-items: start; }
		.meta { grid-column: 1 / -1; }
		.verify { grid-column: 1 / -1; width: 100%; }
		dl div, .payloadRow { grid-template-columns: 1fr; gap: .2rem; }
		.detail { padding: .75rem; }
	}
</style>
