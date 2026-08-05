<script lang="ts">
	// 입력창. auto-grow textarea + 전송(ArrowUp)/중단(Square) 아이콘 버튼. 옛 ui/web Composer 대응.
	// Enter 전송, Shift+Enter 줄바꿈, ESC 중단(busy 중), IME 조합 중 Enter 는 통과.
	import { tick } from 'svelte';

	let {
		value = $bindable(''),
		busy = false,
		placeholder = '질문을 입력하세요…  (Enter 전송 · Shift+Enter 줄바꿈)',
		autofocus = false,
		onsend,
		onstop
	}: {
		value?: string;
		busy?: boolean;
		placeholder?: string;
		autofocus?: boolean;
		onsend?: () => void;
		onstop?: () => void;
	} = $props();

	let ta: HTMLTextAreaElement | null = $state(null);
	let composing = $state(false);

	function autosize(): void {
		if (!ta) return;
		ta.style.height = 'auto';
		ta.style.height = `${Math.min(ta.scrollHeight, 200)}px`;
	}

	// 외부에서 value 가 바뀌어도(추천칩 클릭 등) 높이 재조정.
	$effect(() => {
		void value;
		void tick().then(autosize);
	});

	function submit(): void {
		if (busy || !value.trim()) return;
		onsend?.();
	}

	function onkeydown(e: KeyboardEvent): void {
		if (e.key === 'Escape' && busy) {
			e.preventDefault();
			onstop?.();
			return;
		}
		if (e.key === 'Enter' && !e.shiftKey && !composing) {
			e.preventDefault();
			submit();
		}
	}
</script>

<form
	class="composer"
	data-qa="chat-composer"
	onsubmit={(e) => {
		e.preventDefault();
		submit();
	}}
>
	<textarea
		bind:this={ta}
		bind:value
		{placeholder}
		rows="1"
		oninput={autosize}
		onkeydown={onkeydown}
		oncompositionstart={() => (composing = true)}
		oncompositionend={() => (composing = false)}
		{autofocus}
		data-qa="chat-input"
		data-qa-fill="true"
		data-qa-value="safe"
	></textarea><!-- svelte-ignore a11y_autofocus -->
	{#if busy}
		<button type="button" class="btn stop" data-qa="chat-stop" onclick={() => onstop?.()} aria-label="중단 (ESC)">
			<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" aria-hidden="true">
				<rect x="6" y="6" width="12" height="12" rx="2" />
			</svg>
		</button>
	{:else}
		<button type="submit" class="btn send" data-qa="chat-send" disabled={!value.trim()} aria-label="전송 (Enter)">
			<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
				<path d="M12 19V5" />
				<path d="M5 12l7-7 7 7" />
			</svg>
		</button>
	{/if}
</form>

<style>
	/* 떠 있는 입력 알약. 데스크탑 챗 앱 규범대로 깊이는 그림자로 주고 포커스는
	   테두리 색이 아니라 은은한 링으로 알린다(액센트 테두리는 경고처럼 읽힌다). */
	.composer {
		display: flex;
		align-items: flex-end;
		gap: 0.5rem;
		width: 100%;
		padding: 0.5rem 0.5rem 0.5rem 0.95rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 1.5rem;
		background: var(--dl-bg-raised, #16171a);
		box-shadow: 0 6px 20px rgba(0, 0, 0, 0.28);
		transition: border-color 0.15s ease, box-shadow 0.15s ease;
	}
	.composer:focus-within {
		border-color: color-mix(in srgb, var(--dl-ink-dim, #9aa0aa) 45%, var(--dl-line, #2a2c33));
		box-shadow: 0 6px 22px rgba(0, 0, 0, 0.34), 0 0 0 3px color-mix(in srgb, var(--dl-accent, #ff5a36) 14%, transparent);
	}
	textarea {
		flex: 1;
		resize: none;
		border: none;
		outline: none;
		background: none;
		color: var(--dl-ink, #e7e7ea);
		font: inherit;
		font-size: 0.95rem;
		line-height: 1.5;
		max-height: 200px;
		padding: 0.4rem 0;
		overflow-y: auto;
		scrollbar-width: thin;
	}
	textarea::placeholder {
		color: var(--dl-ink-mute, #6b7280);
	}
	.btn {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 2.1rem;
		height: 2.1rem;
		border-radius: 50%;
		border: none;
		cursor: pointer;
		transition: opacity 0.15s ease, background 0.15s ease;
	}
	.send {
		background: var(--dl-accent, #ff5a36);
		color: #fff;
	}
	.send:disabled {
		opacity: 0.35;
		cursor: default;
	}
	.stop {
		background: var(--dl-ink, #e7e7ea);
		color: var(--dl-bg-base, #0f0f10);
	}
</style>
