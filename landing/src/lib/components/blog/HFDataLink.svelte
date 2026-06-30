<script lang="ts">
	import { brand } from '$lib/brand';

	type DataKind = keyof typeof brand.data;

	interface Props {
		code: string;
		kind?: DataKind;
		label?: string;
	}

	let { code, kind = 'finance', label }: Props = $props();

	const entry = $derived(brand.data[kind]);

	// EDGAR 재무 데이터는 HuggingFace에 정적 업로드되지 않고 dartlab 호출 시 자동 수집됨.
	// kind="edgar"는 설명형 카드, 나머지는 parquet 직접 링크.
	const isEdgarOnDemand = $derived(kind === 'edgar');

	const parquetUrl = $derived(
		`https://huggingface.co/datasets/${brand.hfRepo}/resolve/main/${entry.dir}/${code}.parquet`
	);
	// HF 파일 블롭 페이지 · 브라우저에서 parquet을 테이블 뷰로 preview
	const blobUrl = $derived(
		`https://huggingface.co/datasets/${brand.hfRepo}/blob/main/${entry.dir}/${code}.parquet`
	);
	const datasetUrl = `https://huggingface.co/datasets/${brand.hfRepo}`;
	const parquetText = $derived(label ?? `원본 parquet · ${entry.label}`);
</script>

{#if isEdgarOnDemand}
	<div class="dl-hf-card">
		<div class="dl-hf-card-head">
			<span class="dl-hf-emoji" aria-hidden="true">🤗</span>
			<span class="dl-hf-card-title">SEC EDGAR 재무 데이터 · {code}</span>
		</div>
		<p class="dl-hf-card-body">
			EDGAR 재무 데이터는 HuggingFace에 사전 업로드되지 않습니다. dartlab이 호출 시 SEC
			Companyfacts XBRL에서 최신 분기까지 자동 수집·매핑해 로컬에 parquet로 구축합니다.
		</p>
		<pre class="dl-hf-card-code">import dartlab
c = dartlab.Company(&quot;{code}&quot;)
c.select(&quot;IS&quot;, [&quot;매출액&quot;, &quot;영업이익&quot;])  # 첫 호출 시 자동 구축</pre>
		<a class="dl-hf-card-link" href={datasetUrl} target="_blank" rel="noopener noreferrer">
			eddmpython/dartlab-data 데이터셋 보기 →
		</a>
	</div>
{:else}
	<div class="dl-hf-group">
		<div class="dl-hf-row">
			<a class="dl-hf-link dl-hf-primary" href={parquetUrl} target="_blank" rel="noopener noreferrer">
				<span class="dl-hf-emoji" aria-hidden="true">🤗</span>
				<span class="dl-hf-text">{parquetText}</span>
				<span class="dl-hf-code">{code}.parquet</span>
			</a>
			<a class="dl-hf-link dl-hf-secondary" href={blobUrl} target="_blank" rel="noopener noreferrer">
				<span aria-hidden="true">📊</span>
				<span>브라우저 테이블로 보기 (CSV 복사 가능)</span>
			</a>
		</div>
		<p class="dl-hf-hint">
			💡 Excel 365: File → Get Data → From File → From Parquet 로 바로 열립니다. Python: <code
				>pl.read_parquet(url)</code
			> · DuckDB: <code>SELECT * FROM read_parquet('url')</code>
		</p>
	</div>
{/if}

<style>
	.dl-hf-group {
		display: block;
		margin: 0.75rem 0;
	}
	.dl-hf-row {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		margin-bottom: 0.4rem;
	}
	.dl-hf-link {
		display: inline-flex;
		align-items: center;
		gap: 0.5rem;
		padding: 0.45rem 0.85rem;
		border: 1px solid var(--border, #1e2433);
		border-radius: 0.5rem;
		background: var(--bg-card, #0f1219);
		color: var(--text, #f1f5f9);
		font-size: 0.875rem;
		text-decoration: none;
		transition: border-color 0.15s, background 0.15s;
	}
	.dl-hf-link:hover {
		border-color: var(--primary, #ea4647);
		background: var(--bg-card-hover, #1a1f2b);
	}
	.dl-hf-secondary {
		font-size: 0.82rem;
		color: var(--text-muted, #94a3b8);
	}
	.dl-hf-emoji {
		font-size: 1rem;
	}
	.dl-hf-code {
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.78rem;
		color: var(--text-muted, #94a3b8);
	}
	.dl-hf-hint {
		margin: 0;
		color: var(--text-muted, #94a3b8);
		font-size: 0.78rem;
		line-height: 1.55;
	}
	.dl-hf-hint code {
		padding: 0.1rem 0.35rem;
		border-radius: 0.25rem;
		background: var(--bg-card-hover, #1a1f2b);
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.75rem;
		color: var(--text, #f1f5f9);
	}
	.dl-hf-card {
		display: block;
		padding: 0.9rem 1rem;
		border: 1px solid var(--border, #1e2433);
		border-radius: 0.6rem;
		background: var(--bg-card, #0f1219);
		margin: 0.75rem 0;
	}
	.dl-hf-card-head {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		margin-bottom: 0.5rem;
	}
	.dl-hf-card-title {
		color: var(--text, #f1f5f9);
		font-size: 0.9rem;
		font-weight: 600;
	}
	.dl-hf-card-body {
		margin: 0 0 0.6rem;
		color: var(--text-muted, #94a3b8);
		font-size: 0.82rem;
		line-height: 1.55;
	}
	.dl-hf-card-code {
		margin: 0 0 0.6rem;
		padding: 0.55rem 0.7rem;
		border-radius: 0.4rem;
		background: var(--bg-card-hover, #1a1f2b);
		color: var(--text, #f1f5f9);
		font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
		font-size: 0.78rem;
		line-height: 1.5;
		white-space: pre-wrap;
		overflow-x: auto;
	}
	.dl-hf-card-link {
		display: inline-block;
		color: var(--primary, #ea4647);
		font-size: 0.82rem;
		text-decoration: none;
	}
	.dl-hf-card-link:hover {
		text-decoration: underline;
	}
</style>
