<script lang="ts">
	/** Editorial slug · "Q3 2025 · 005930 · 분석 2026-04-23" 류 */
	interface Props {
		text?: string;
		mark?: boolean; // 좌측 짧은 라인
	}
	let { text = '', mark = true }: Props = $props();
</script>

<span class="eb">
	{#if mark}<span class="eb-mark" aria-hidden="true"></span>{/if}
	<span class="eb-text">{text}</span>
</span>

<style>
	.eb {
		display: inline-flex;
		align-items: center;
		gap: var(--dl-s-2);
		font-family: var(--dl-font-mono);
		font-size: 10px;
		font-weight: 500;
		letter-spacing: 0.16em;
		text-transform: uppercase;
		color: var(--dl-ink-dim);
	}
	.eb-mark {
		display: inline-block;
		width: 18px;
		height: 1px;
		background: var(--dl-grad-heat);
	}
</style>
