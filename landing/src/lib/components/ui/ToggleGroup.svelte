<script lang="ts">
	/** segmented toggle · 4뷰 토글, 기간 선택 등 */
	interface Option {
		value: string;
		label: string;
	}
	interface Props {
		options: Option[];
		value: string;
		onChange?: (v: string) => void;
		size?: 'sm' | 'md';
	}

	let { options, value, onChange, size = 'md' }: Props = $props();
</script>

<div class="tg size-{size}" role="tablist">
	{#each options as opt}
		<button
			type="button"
			role="tab"
			aria-selected={value === opt.value}
			class="tg-btn"
			class:active={value === opt.value}
			onclick={() => onChange?.(opt.value)}
		>
			{opt.label}
		</button>
	{/each}
</div>

<style>
	.tg {
		display: inline-flex;
		padding: 3px;
		background: var(--dl-bg-raised);
		border: 1px solid var(--dl-line);
		border-radius: var(--dl-r-md);
		gap: 2px;
	}
	.tg-btn {
		font-family: var(--dl-font-ui);
		font-weight: 500;
		color: var(--dl-ink-mute);
		background: transparent;
		border: none;
		border-radius: 5px;
		cursor: pointer;
		transition: background var(--dl-dur-hover) var(--dl-ease),
			color var(--dl-dur-hover) var(--dl-ease);
	}
	.size-sm .tg-btn { padding: 4px 10px; font-size: 11px; }
	.size-md .tg-btn { padding: 6px 12px; font-size: 12px; }

	.tg-btn:hover:not(.active) {
		color: var(--dl-ink);
		background: rgba(255, 255, 255, 0.03);
	}
	.tg-btn.active {
		background: var(--dl-bg-modal);
		color: var(--dl-ink-print);
		font-weight: 600;
	}
</style>
