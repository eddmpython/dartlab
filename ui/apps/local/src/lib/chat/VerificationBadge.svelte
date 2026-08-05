<script lang="ts">
	/**
	 * 검증 뱃지. DartLab 은 설치형 agent 의 답을 차단하지 않고 중개하며,
	 * 근거 계약 충족 여부를 이 뱃지로 표시한다. 판단은 사용자가 한다.
	 */
	let {
		status = null,
		evidenceCount = 0,
		notes = []
	}: {
		status?: 'verified' | 'unverified' | 'failed' | null;
		evidenceCount?: number;
		notes?: string[];
	} = $props();

	let open = $state(false);
</script>

{#if status}
	<div class="badge" class:verified={status === 'verified'} class:unverified={status === 'unverified'} class:failed={status === 'failed'} data-qa="verification-badge">
		{#if status === 'verified'}
			<span class="dot" aria-hidden="true"></span>
			<span>DartLab 근거 {evidenceCount}개 대조 일치</span>
		{:else if status === 'unverified'}
			<span class="dot" aria-hidden="true"></span>
			<span>근거 {evidenceCount}개 인용 · 자동 대조 미완</span>
			{#if notes.length}
				<button type="button" onclick={() => (open = !open)} aria-expanded={open}>
					{open ? '접기' : '사유'}
				</button>
			{/if}
		{:else}
			<span class="dot" aria-hidden="true"></span>
			<span>런타임이 답변을 완료하지 못했습니다</span>
		{/if}
	</div>
	{#if open && notes.length}
		<ul class="notes" data-qa="verification-notes">
			{#each notes as note}<li>{note}</li>{/each}
		</ul>
	{/if}
{/if}

<style>
	.badge {
		display: inline-flex;
		align-items: center;
		gap: .4rem;
		padding: .18rem .5rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 999px;
		font-size: .7rem;
		color: var(--dl-ink-dim, #9aa0aa);
	}
	.dot { width: .4rem; height: .4rem; border-radius: 50%; background: currentColor; }
	.verified { color: var(--dl-good, #34d399); border-color: color-mix(in srgb, var(--dl-good, #34d399) 35%, transparent); }
	.unverified { color: var(--dl-warn, #fbbf24); border-color: color-mix(in srgb, var(--dl-warn, #fbbf24) 35%, transparent); }
	.failed { color: var(--dl-bad, #ef4444); border-color: color-mix(in srgb, var(--dl-bad, #ef4444) 35%, transparent); }
	button {
		border: 0;
		background: transparent;
		padding: 0;
		color: inherit;
		font-size: .68rem;
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}
	.notes {
		margin: .35rem 0 0;
		padding-left: 1.1rem;
		color: var(--dl-ink-mute, #6b7280);
		font-size: .7rem;
		line-height: 1.5;
	}
</style>
