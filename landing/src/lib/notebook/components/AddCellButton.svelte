<script lang="ts">
	import type { Cell } from '../stores/notebookStore';

	interface Props {
		onAdd: (type: Cell['type']) => void;
	}

	let { onAdd }: Props = $props();

	let showMenu = $state(false);

	function handleAdd(type: Cell['type']) {
		onAdd(type);
		showMenu = false;
	}
</script>

<div class="add-cell-container">
	<div class="add-line"></div>
	<button class="add-btn" onclick={() => (showMenu = !showMenu)}>
		+
	</button>
	<div class="add-line"></div>

	{#if showMenu}
		<div class="add-menu">
			<button class="menu-item" onclick={() => handleAdd('code')}>
				<span class="menu-icon">&#60;/&#62;</span>
				Code
			</button>
			<button class="menu-item" onclick={() => handleAdd('markdown')}>
				<span class="menu-icon">M&#8595;</span>
				Markdown
			</button>
		</div>
	{/if}
</div>

<style>
	.add-cell-container {
		display: flex;
		align-items: center;
		position: relative;
		padding: 4px 0;
		opacity: 0;
		transition: opacity 0.15s ease;
	}

	.add-cell-container:hover,
	.add-cell-container:has(.add-menu) {
		opacity: 1;
	}

	.add-line {
		flex: 1;
		height: 1px;
		background: var(--nb-border);
	}

	.add-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		border: 1px solid var(--nb-border);
		border-radius: 50%;
		background: var(--nb-card);
		color: var(--nb-text-muted);
		font-size: 16px;
		line-height: 1;
		cursor: pointer;
		transition: all 0.15s ease;
		margin: 0 8px;
	}

	.add-btn:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.add-menu {
		position: absolute;
		top: 100%;
		left: 50%;
		transform: translateX(-50%);
		display: flex;
		gap: 4px;
		padding: 6px;
		background: var(--nb-card);
		border: 1px solid var(--nb-border);
		border-radius: var(--radius-md);
		box-shadow: var(--shadow-md);
		z-index: 10;
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: 6px;
		padding: 6px 12px;
		border: none;
		border-radius: var(--radius-sm);
		background: transparent;
		color: var(--nb-text-secondary);
		font-size: 13px;
		cursor: pointer;
		white-space: nowrap;
		transition: all 0.1s ease;
	}

	.menu-item:hover {
		background: var(--nb-surface);
		color: var(--nb-text);
	}

	.menu-icon {
		font-size: 12px;
		color: var(--nb-text-muted);
	}
</style>
