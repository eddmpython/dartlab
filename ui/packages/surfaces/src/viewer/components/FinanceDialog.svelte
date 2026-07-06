<script lang="ts">
	// 정량재무제표 다이얼로그 shell. 본문 탐색/쿼리 로직은 FinanceStatementPane 이 단일로 담당한다.
	import { X } from 'lucide-svelte';
	import { fade, scale } from 'svelte/transition';
	import FinanceStatementPane from './FinanceStatementPane.svelte';

	let { code, corpName, open, onclose }: { code: string; corpName: string; open: boolean; onclose: () => void } = $props();

	$effect(() => {
		if (!open) return;
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') {
				e.stopPropagation();
				onclose();
			}
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

{#if open}
	<button type="button" class="overlay" aria-label="닫기" onclick={onclose} transition:fade={{ duration: 150 }}></button>
	<div class="modal" role="dialog" aria-modal="true" aria-label="정량재무제표" transition:scale={{ start: 0.98, duration: 180 }}>
		<header class="mh">
			<div class="mh-title"><span class="mh-corp">{corpName || code}</span><span class="mh-sub">정량재무제표</span></div>
			<button type="button" class="mh-close" onclick={onclose} title="닫기 (Esc)"><X size={16} /></button>
		</header>
		<div class="body">
			<FinanceStatementPane {code} {corpName} showHeader={false} frameless={true} />
		</div>
	</div>
{/if}

<style>
	.overlay {
		position: fixed;
		inset: 0;
		z-index: 400;
		border: 0;
		padding: 0;
		background: rgba(2, 4, 9, 0.66);
		cursor: default;
	}
	/* --fin-* 토큰: 미정의 시 fallback = 기존 viewer 값 (픽셀 무변화).
	   터미널은 .dlTermFinSkin 래퍼가 terminal.css 토큰으로 오버라이드 · 렌더러 한몸두입구. */
	.modal {
		position: fixed;
		top: 50%;
		left: 50%;
		transform: translate(-50%, -50%);
		z-index: 401;
		width: min(1320px, 96vw);
		height: min(86vh, 920px);
		display: flex;
		flex-direction: column;
		background: var(--fin-modal-bg, #0a0e18);
		border: 1px solid var(--fin-modal-bd, #263145);
		border-radius: var(--fin-radius-lg, 10px);
		box-shadow: 0 24px 64px rgba(0, 0, 0, 0.55);
		overflow: hidden;
	}
	.mh {
		flex-shrink: 0;
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
		padding: 11px 14px;
		border-bottom: 1px solid var(--fin-bd, #1e2433);
	}
	.mh-title {
		display: flex;
		align-items: baseline;
		gap: 8px;
		min-width: 0;
	}
	.mh-corp {
		font-size: 15px;
		font-weight: 700;
		color: var(--fin-txt, #f1f5f9);
	}
	.mh-sub {
		font-size: 11px;
		color: var(--fin-dim, #cbd5e1);
	}
	.mh-sub::before {
		content: '·';
		margin-right: 6px;
		color: #64748b;
	}
	.mh-close {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 28px;
		height: 28px;
		border: 1px solid var(--fin-bd, #1e2433);
		border-radius: var(--fin-radius, 6px);
		background: transparent;
		color: var(--fin-dim, #cbd5e1);
		cursor: pointer;
	}
	.mh-close:hover {
		border-color: var(--amber);
		color: var(--amber);
	}
	.body {
		flex: 1 1 auto;
		min-height: 0;
		overflow: hidden;
	}
</style>
