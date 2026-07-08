<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();

	const label = $derived((config.label as string) || 'Upload file');
	const multiple = $derived(Boolean(config.multiple));
	const filetypes = $derived((config.filetypes as string[]) || []);

	const acceptStr = $derived(filetypes.length > 0 ? filetypes.join(',') : '');
	const fileNames = $derived(
		Array.isArray(value) ? (value as { name: string }[]).map((f) => f.name) : []
	);

	async function handleFiles(e: Event) {
		const input = e.target as HTMLInputElement;
		const files = input.files;
		if (!files || files.length === 0) return;

		const results: { name: string; contents: string; size: number; type: string }[] = [];
		for (let i = 0; i < files.length; i++) {
			const f = files[i];
			const text = await f.text();
			results.push({
				name: f.name,
				contents: text,
				size: f.size,
				type: f.type
			});
		}

		onChange(multiple ? results : results[0] ?? null);
	}
</script>

<div class="file-widget">
	{#if label}
		<span class="widget-label">{label}</span>
	{/if}
	<label class="file-upload-btn">
		<input
			type="file"
			accept={acceptStr}
			{multiple}
			onchange={handleFiles}
			class="file-hidden"
		/>
		<span class="file-btn-text">Choose file{multiple ? 's' : ''}</span>
	</label>
	{#if fileNames.length > 0}
		<div class="file-names">
			{#each fileNames as name}
				<span class="file-tag">{name}</span>
			{/each}
		</div>
	{/if}
</div>

<style>
	.file-widget {
		display: inline-flex;
		flex-direction: column;
		gap: 6px;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.file-upload-btn {
		display: inline-flex;
		align-items: center;
		cursor: pointer;
	}

	.file-hidden {
		display: none;
	}

	.file-btn-text {
		padding: 6px 14px;
		border: 1px solid var(--nb-border);
		border-radius: 6px;
		background: var(--nb-card);
		color: var(--nb-text-secondary);
		font-size: 12px;
		transition: all 0.15s ease;
	}

	.file-btn-text:hover {
		border-color: var(--nb-pink);
		color: var(--nb-pink);
	}

	.file-names {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}

	.file-tag {
		padding: 2px 8px;
		background: var(--nb-surface);
		border-radius: 4px;
		font-size: 11px;
		color: var(--nb-text);
		font-family: var(--dl-font-mono);
	}
</style>
