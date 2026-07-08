<script lang="ts">
	// DataFrame 표 렌더 - 넓은 wide 격자를 가로 스크롤 컨테이너 안에서 보여준다.
	// 숫자 열은 우측정렬, 헤더에 dtype 배지, 하단에 shape/절단 안내.
	let {
		columns,
		dtypes,
		rows,
		nrows,
		ncols,
		truncated
	}: {
		columns: string[];
		dtypes: string[];
		rows: unknown[][];
		nrows: number;
		ncols: number;
		truncated: boolean;
	} = $props();

	const numericDtype = (t: string) =>
		/int|float|decimal|f32|f64|i8|i16|i32|i64|u8|u16|u32|u64/i.test(t);

	function fmt(v: unknown): string {
		if (v === null || v === undefined) return '';
		if (typeof v === 'number') {
			if (Number.isInteger(v)) return v.toLocaleString('en-US');
			return v.toLocaleString('en-US', { maximumFractionDigits: 4 });
		}
		return String(v);
	}
</script>

<div class="overflow-x-auto rounded border border-dl-border bg-dl-bg-dark">
	<table class="min-w-full border-collapse text-xs">
		<thead>
			<tr class="border-b border-dl-border">
				{#each columns as col, i}
					<th
						class="sticky top-0 z-10 whitespace-nowrap bg-dl-bg-card px-3 py-2 text-left font-semibold text-dl-text {numericDtype(
							dtypes[i]
						)
							? 'text-right'
							: 'text-left'}"
					>
						<div class="{numericDtype(dtypes[i]) ? 'text-right' : 'text-left'}">{col}</div>
						<div class="font-mono text-[10px] font-normal text-dl-text-dim">{dtypes[i]}</div>
					</th>
				{/each}
			</tr>
		</thead>
		<tbody>
			{#each rows as row}
				<tr class="border-b border-dl-border/50 hover:bg-dl-bg-card/50">
					{#each row as cell, i}
						<td
							class="whitespace-nowrap px-3 py-1.5 font-mono text-dl-text-muted {numericDtype(
								dtypes[i]
							)
								? 'text-right tabular-nums'
								: 'text-left'}"
						>
							{fmt(cell)}
						</td>
					{/each}
				</tr>
			{/each}
		</tbody>
	</table>
</div>
<div class="mt-1.5 flex items-center gap-2 text-[11px] text-dl-text-dim">
	<span>{nrows.toLocaleString('en-US')} rows x {ncols} cols</span>
	{#if truncated}
		<span class="text-dl-warning">상위 {rows.length}행 표시</span>
	{/if}
</div>
