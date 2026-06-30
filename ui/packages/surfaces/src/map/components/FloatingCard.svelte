<script lang="ts">
	/**
	 * Floating card window · Figma/VSCode 스타일 떠있는 패널.
	 *
	 * - 헤더 드래그로 이동
	 * - 우측 하단 모서리 리사이즈 (CSS resize)
	 * - 클릭 시 최상단 (z-index 자동)
	 * - 닫기 버튼
	 * - 모바일(<768px)에서는 숨김 · 기본 우측 패널만 사용
	 */
	import type { Snippet } from 'svelte';

	interface Props {
		id: string;
		title: string;
		subtitle?: string;
		x: number;
		y: number;
		w?: number;
		h?: number;
		z?: number;
		onClose: () => void;
		onFocus?: () => void;
		onMove?: (x: number, y: number) => void;
		onResize?: (w: number, h: number) => void;
		children?: Snippet;
	}

	let {
		id,
		title,
		subtitle = '',
		x = $bindable(),
		y = $bindable(),
		w = $bindable(500),
		h = $bindable(640),
		z = 1,
		onClose,
		onFocus,
		onMove,
		onResize,
		children
	}: Props = $props();

	let rootEl: HTMLDivElement | null = $state(null);
	let dragging = $state(false);
	let dragStart = { mx: 0, my: 0, x: 0, y: 0 };
	let shaking = $state(false);
	let showHint = $state(false);
	let compact = $state(false); // compact: 헤더만, full: 전체

	function toggleCompact() {
		compact = !compact;
		if (compact) {
			h = 80;
		} else {
			h = 640;
		}
	}

	// 첫 사용 힌트 (1회만)
	$effect(() => {
		if (typeof localStorage === 'undefined') return;
		if (!localStorage.getItem('dartlab.fc.hint.done')) {
			showHint = true;
			setTimeout(() => {
				showHint = false;
				localStorage.setItem('dartlab.fc.hint.done', '1');
			}, 4000);
		}
	});

	/** 이미 열린 카드에 focus 시 흔들림 효과 */
	export function shake() {
		shaking = true;
		setTimeout(() => (shaking = false), 300);
	}

	function onHeaderMouseDown(e: MouseEvent) {
		// 닫기 버튼 등 내부 인터랙션은 제외
		if ((e.target as Element).closest('.fc-close, .fc-actions')) return;
		e.preventDefault();
		dragging = true;
		dragStart = { mx: e.clientX, my: e.clientY, x, y };
		onFocus?.();
	}

	function onWinMouseMove(e: MouseEvent) {
		if (!dragging) return;
		const nx = dragStart.x + (e.clientX - dragStart.mx);
		const ny = dragStart.y + (e.clientY - dragStart.my);
		// viewport 밖 방지
		const maxX = window.innerWidth - 80;
		const maxY = window.innerHeight - 48;
		x = Math.max(-w + 80, Math.min(maxX, nx));
		y = Math.max(0, Math.min(maxY, ny));
		onMove?.(x, y);
	}

	function onWinMouseUp() {
		dragging = false;
	}

	// ResizeObserver 로 사용자 resize 반영
	function onResizeObserved() {
		if (!rootEl) return;
		const rect = rootEl.getBoundingClientRect();
		if (Math.abs(rect.width - w) > 2 || Math.abs(rect.height - h) > 2) {
			w = rect.width;
			h = rect.height;
			onResize?.(w, h);
		}
	}

	$effect(() => {
		if (!rootEl) return;
		const ro = new ResizeObserver(onResizeObserved);
		ro.observe(rootEl);
		return () => ro.disconnect();
	});
</script>

<svelte:window onmousemove={onWinMouseMove} onmouseup={onWinMouseUp} />

<div
	bind:this={rootEl}
	class="fc"
	class:dragging
	class:shaking
	style:left="{x}px"
	style:top="{y}px"
	style:width="{w}px"
	style:height="{h}px"
	style:z-index={z}
	onmousedown={() => onFocus?.()}
	role="dialog"
	tabindex="-1"
	aria-label={title}
>
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<header class="fc-head" onmousedown={onHeaderMouseDown} ondblclick={toggleCompact}>
		<div class="fc-titles">
			<div class="fc-title">{title}</div>
			{#if subtitle}
				<div class="fc-subtitle">{subtitle}</div>
			{/if}
		</div>
		<div class="fc-actions">
			<button class="fc-close" onclick={onClose} aria-label="닫기" title="닫기">✕</button>
		</div>
	</header>
	{#if !compact}
		<div class="fc-body">
			{#if children}{@render children()}{/if}
		</div>
	{/if}
	{#if showHint}
		<div class="fc-hint">드래그로 이동 · 모서리로 크기 조절</div>
	{/if}
	<div class="fc-id">#{id}</div>
</div>

<style>
	@keyframes fc-shake {
		0%, 100% { transform: translateX(0); }
		25% { transform: translateX(-6px); }
		50% { transform: translateX(6px); }
		75% { transform: translateX(-3px); }
	}
	.fc.shaking {
		animation: fc-shake 0.3s ease;
	}
	.fc-hint {
		position: absolute;
		bottom: 28px;
		left: 50%;
		transform: translateX(-50%);
		padding: 6px 12px;
		background: rgba(234, 70, 71, 0.9);
		color: #050811;
		font-size: 11px;
		font-weight: 600;
		border-radius: 6px;
		white-space: nowrap;
		pointer-events: none;
		z-index: 2;
		animation: fadeout 4s forwards;
	}
	@keyframes fadeout {
		0%, 70% { opacity: 1; }
		100% { opacity: 0; }
	}
	.fc {
		position: fixed;
		min-width: 460px;
		min-height: 280px;
		max-width: 90vw;
		max-height: 90vh;
		background: var(--color-dl-bg-card);
		border: 1px solid var(--color-dl-border);
		border-radius: 10px;
		box-shadow: 0 20px 48px rgba(0, 0, 0, 0.6), 0 0 0 1px rgba(234, 70, 71, 0.1);
		display: flex;
		flex-direction: column;
		overflow: hidden;
		resize: both;
	}
	.fc.dragging {
		cursor: grabbing;
		opacity: 0.95;
	}

	.fc-head {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 8px 12px;
		background: linear-gradient(180deg, rgba(234, 70, 71, 0.06), transparent);
		border-bottom: 1px solid var(--color-dl-border);
		cursor: grab;
		user-select: none;
		flex-shrink: 0;
	}
	.fc.dragging .fc-head {
		cursor: grabbing;
	}
	.fc-titles {
		min-width: 0;
	}
	.fc-title {
		font-size: 13px;
		font-weight: 600;
		color: var(--color-dl-text);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.fc-subtitle {
		font-size: 10px;
		color: var(--color-dl-text-dim);
		font-family: monospace;
	}
	.fc-actions {
		display: flex;
		gap: 4px;
	}
	.fc-close {
		width: 22px;
		height: 22px;
		background: transparent;
		border: none;
		border-radius: 4px;
		color: var(--color-dl-text-dim);
		cursor: pointer;
		font-size: 12px;
	}
	.fc-close:hover {
		background: rgba(239, 68, 68, 0.12);
		color: var(--color-dl-primary-light);
	}

	.fc-body {
		flex: 1;
		overflow-y: auto;
		background: var(--color-dl-bg-card);
	}
	.fc-id {
		position: absolute;
		bottom: 2px;
		left: 6px;
		font-size: 9px;
		color: var(--color-dl-border);
		font-family: monospace;
		pointer-events: none;
	}

	@media (max-width: 768px) {
		.fc {
			display: none;
		}
	}
</style>
