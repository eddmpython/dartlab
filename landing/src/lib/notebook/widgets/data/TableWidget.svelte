<script lang="ts">
	interface Props {
		config: Record<string, unknown>;
		value: unknown;
		onChange: (value: unknown) => void;
	}

	let { config, value, onChange }: Props = $props();
	void onChange;

	const label = $derived((config.label as string) || '');
	const rows = $derived.by((): Record<string, unknown>[] => normalizeRows(value));
	const columns = $derived.by((): string[] => {
		const configured = config.columns;
		if (Array.isArray(configured)) return configured.map(String);
		const keys = new Set<string>();
		for (const row of rows) {
			Object.keys(row).forEach((key) => keys.add(key));
		}
		return Array.from(keys);
	});

	function normalizeRows(input: unknown): Record<string, unknown>[] {
		if (Array.isArray(input)) {
			return input.map((row) => {
				if (row && typeof row === 'object' && !Array.isArray(row)) {
					return row as Record<string, unknown>;
				}
				return { value: row };
			});
		}
		if (input && typeof input === 'object') {
			return Object.entries(input as Record<string, unknown>).map(([key, row]) => {
				if (row && typeof row === 'object' && !Array.isArray(row)) {
					return { key, ...(row as Record<string, unknown>) };
				}
				return { key, value: row };
			});
		}
		return input == null ? [] : [{ value: input }];
	}

	function formatCell(cell: unknown): string {
		if (cell == null) return '';
		if (typeof cell === 'object') return JSON.stringify(cell);
		return String(cell);
	}
</script>

<div class="table-widget">
	{#if label}
		<div class="widget-label">{label}</div>
	{/if}
	{#if rows.length && columns.length}
		<div class="table-scroll">
			<table>
				<thead>
					<tr>
						{#each columns as column (column)}
							<th>{column}</th>
						{/each}
					</tr>
				</thead>
				<tbody>
					{#each rows as row, index (index)}
						<tr>
							{#each columns as column (column)}
								<td>{formatCell(row[column])}</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{:else}
		<div class="empty">No rows</div>
	{/if}
</div>

<style>
	.table-widget {
		display: flex;
		flex-direction: column;
		gap: 6px;
		max-width: 100%;
	}

	.widget-label {
		font-size: 12px;
		font-weight: 500;
		color: var(--nb-text-muted);
	}

	.table-scroll {
		max-width: 100%;
		overflow-x: auto;
		border: 1px solid var(--nb-border);
		border-radius: 8px;
		background: var(--nb-card);
	}

	table {
		border-collapse: collapse;
		font-size: 12px;
		color: var(--nb-text-secondary);
	}

	th,
	td {
		padding: 6px 8px;
		border-bottom: 1px solid var(--nb-border);
		white-space: nowrap;
	}

	th {
		color: var(--nb-text);
		font-weight: 600;
		background: var(--nb-surface);
	}

	tbody tr:last-child td {
		border-bottom: 0;
	}

	.empty {
		font-size: 12px;
		color: var(--nb-text-muted);
		padding: 6px 8px;
		border: 1px dashed var(--nb-border);
		border-radius: 6px;
	}
</style>
