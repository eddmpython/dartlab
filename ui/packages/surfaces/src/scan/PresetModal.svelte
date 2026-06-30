<script lang="ts">
	/**
	 * ⌘K 프리셋 모달 · 7 안정 프리셋 + 회사명·종목코드·산업 검색.
	 *
	 * 활성 트리거: ⌘K (Mac) · Ctrl+K (Win) · `/` 키 · 헤더 버튼.
	 * 위→아래 list 단일 흐름 · 카테고리 색칩 + 한국어 자연어.
	 */
	import { onMount } from 'svelte';
	import { PRESETS, PRESET_CATEGORIES } from './presets';
	import type { Preset } from './presets';
	import type { ScanNode } from './types';

	interface Props {
		open: boolean;
		nodes: ScanNode[];
		onClose: () => void;
		onApplyPreset: (preset: Preset) => void;
	}

	let { open = $bindable(false), onClose, onApplyPreset }: Props = $props();

	let query = $state('');
	let active = $state(0);
	let inputEl: HTMLInputElement | undefined = $state(undefined);

	$effect(() => {
		if (open) {
			query = '';
			active = 0;
			setTimeout(() => inputEl?.focus(), 30);
		}
	});

	let presetMatches = $derived.by(() => {
		const q = query.trim().toLowerCase();
		if (!q) return PRESETS;
		return PRESETS.filter(
			(p) =>
				p.title.toLowerCase().includes(q) ||
				p.subtitle.toLowerCase().includes(q) ||
				p.desc.toLowerCase().includes(q)
		);
	});

	let totalItems = $derived(presetMatches.length);

	function handleKey(e: KeyboardEvent) {
		if (!open) return;
		if (e.key === 'Escape') {
			e.preventDefault();
			onClose();
		} else if (e.key === 'ArrowDown') {
			e.preventDefault();
			active = Math.min(totalItems - 1, active + 1);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			active = Math.max(0, active - 1);
		} else if (e.key === 'Enter') {
			e.preventDefault();
			selectActive();
		}
	}

	function selectActive() {
		if (active < presetMatches.length) {
			const p = presetMatches[active];
			if (p) {
				onApplyPreset(p);
				onClose();
			}
		}
	}

	function backdropClick(e: MouseEvent) {
		if (e.target === e.currentTarget) onClose();
	}

	onMount(() => {
		const onWinKey = (e: KeyboardEvent) => {
			if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
				e.preventDefault();
				open = !open;
			}
		};
		window.addEventListener('keydown', onWinKey);
		return () => window.removeEventListener('keydown', onWinKey);
	});

	function categoryColor(cat: Preset['category']): string {
		return PRESET_CATEGORIES.find((c) => c.key === cat)?.color || '#94a3b8';
	}
</script>

<svelte:window onkeydown={handleKey} />

{#if open}
	<div
		class="backdrop"
		role="dialog"
		aria-modal="true"
		aria-labelledby="cmdk-title"
		onclick={backdropClick}
		onkeydown={handleKey}
		tabindex="-1"
	>
		<div class="modal" role="document">
			<div class="search">
				<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true">
					<circle cx="11" cy="11" r="7" />
					<line x1="21" y1="21" x2="16.65" y2="16.65" />
				</svg>
				<input
					type="text"
					bind:this={inputEl}
					bind:value={query}
					placeholder="프리셋 검색…"
					class="search-input"
					id="cmdk-title"
				/>
				<kbd class="esc">ESC</kbd>
			</div>

			<div class="results">
				{#if presetMatches.length > 0}
					<div class="section-label">프리셋</div>
					{#each presetMatches as p, i (p.id)}
						<button
							type="button"
							class="item preset-item"
							class:active={active === i}
							onmouseenter={() => (active = i)}
							onclick={() => {
								onApplyPreset(p);
								onClose();
							}}
						>
							<span class="cat-bar" style:background={categoryColor(p.category)}></span>
							<div class="item-body">
								<div class="item-title">{p.title}</div>
								<div class="item-sub">{p.subtitle}</div>
								<div class="item-desc">{p.desc}</div>
							</div>
						</button>
					{/each}
				{/if}

				{#if presetMatches.length === 0}
					<div class="empty">검색 결과가 없습니다.</div>
				{/if}
			</div>

			<div class="footer">
				<span class="hint"><kbd>↑↓</kbd> 이동</span>
				<span class="hint"><kbd>Enter</kbd> 선택</span>
				<span class="hint"><kbd>⌘K</kbd> 토글</span>
			</div>
		</div>
	</div>
{/if}

<style>
	.backdrop {
		position: fixed;
		inset: 0;
		background: rgba(0, 0, 0, 0.6);
		backdrop-filter: blur(4px);
		display: flex;
		align-items: flex-start;
		justify-content: center;
		padding-top: 10vh;
		z-index: 1000;
	}
	.modal {
		width: min(640px, 92vw);
		max-height: 70vh;
		display: flex;
		flex-direction: column;
		background: #0f172a;
		border: 1px solid #334155;
		border-radius: 8px;
		box-shadow: 0 24px 48px -12px rgba(0, 0, 0, 0.7);
		overflow: hidden;
	}
	.search {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 14px 16px;
		border-bottom: 1px solid #1e2433;
		color: #94a3b8;
	}
	.search-input {
		flex: 1;
		background: transparent;
		border: none;
		color: #f1f5f9;
		font-size: 14px;
		font-family: inherit;
		outline: none;
	}
	.esc {
		font-size: 10px;
		font-family: monospace;
		padding: 2px 6px;
		background: #1e2433;
		border-radius: 3px;
		color: #94a3b8;
	}

	.results {
		flex: 1;
		overflow-y: auto;
		padding: 6px 0;
	}
	.section-label {
		padding: 8px 16px 4px;
		font-size: 10px;
		font-weight: 600;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.06em;
	}
	.item {
		display: flex;
		align-items: stretch;
		gap: 10px;
		width: 100%;
		padding: 10px 16px;
		background: transparent;
		border: none;
		color: inherit;
		cursor: pointer;
		text-align: left;
		transition: background 0.1s;
	}
	.item.active {
		background: rgba(var(--amber-rgb), 0.08);
	}
	.cat-bar {
		width: 3px;
		border-radius: 2px;
		flex-shrink: 0;
	}
	.item-body {
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 2px;
		min-width: 0;
	}
	.item-title {
		font-size: 13px;
		font-weight: 600;
		color: #f1f5f9;
	}
	.item.active .item-title {
		color: var(--amber);
	}
	.item-sub {
		font-size: 10px;
		color: #94a3b8;
		font-family: monospace;
	}
	.item-desc {
		font-size: 11px;
		color: #64748b;
		line-height: 1.5;
		margin-top: 3px;
	}

	.empty {
		padding: 24px 16px;
		text-align: center;
		color: #64748b;
		font-size: 12px;
	}

	.footer {
		display: flex;
		gap: 16px;
		padding: 8px 16px;
		border-top: 1px solid #1e2433;
		background: #0a0e18;
		font-size: 11px;
		color: #64748b;
	}
	.footer kbd {
		font-family: monospace;
		padding: 1px 5px;
		background: #1e2433;
		border-radius: 3px;
		color: #cbd5e1;
		font-size: 10px;
	}
</style>
