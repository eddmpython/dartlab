<script lang="ts">
	import { Plus, Search, SlidersHorizontal, X } from 'lucide-svelte';
	import { GROUP_META, METRICS_BY_KEY, METRICS_DEF } from './metrics';
	import { buildVerdictGrid } from './verdict';
	import type { FilterCond, MetricDef, ScanNode, SortKey } from './types';

	interface ApplyPayload {
		conds: FilterCond[];
		sorts: SortKey[];
		cols: string[];
	}

	interface Props {
		nodes: ScanNode[];
		onApply: (payload: ApplyPayload) => void;
	}

	let { nodes, onApply }: Props = $props();

	type DraftCond = {
		id: number;
		metric: string;
		op: FilterCond['op'];
		value: string;
		value2: string;
	};

	let nextId = 1;
	let fieldQuery = $state('');
	let drafts = $state<DraftCond[]>([]);
	let sortKey = $state('marketCap');
	let sortDir = $state<'asc' | 'desc'>('desc');

	const usableFields = METRICS_DEF.filter((m) => m.type !== 'series');
	const sortFields = usableFields.filter((m) => m.type === 'number' || m.type === 'text');

	let filteredFields = $derived.by(() => {
		const q = fieldQuery.trim().toLowerCase();
		const fields = q
			? usableFields.filter((m) =>
					[m.label, m.key, m.definition, GROUP_META[m.group as keyof typeof GROUP_META]?.label]
						.join(' ')
						.toLowerCase()
						.includes(q)
				)
			: usableFields;
		return fields.slice(0, 80);
	});

	let compiledConds = $derived.by(() => drafts.map(toCond).filter((c): c is FilterCond => Boolean(c)));
	let previewGrid = $derived(buildVerdictGrid(nodes, compiledConds, METRICS_BY_KEY));
	let previewNodes = $derived.by(() => {
		const list = previewGrid.members.slice();
		const key = sortKey;
		const dir = sortDir === 'asc' ? 1 : -1;
		list.sort((a, b) => {
			const av = comparableValue((a as Record<string, unknown>)[key]);
			const bv = comparableValue((b as Record<string, unknown>)[key]);
			if (av == null && bv == null) return a.label.localeCompare(b.label, 'ko-KR');
			if (av == null) return 1;
			if (bv == null) return -1;
			const cmp =
				typeof av === 'number' && typeof bv === 'number'
					? av - bv
					: String(av).localeCompare(String(bv), 'ko-KR', { numeric: true });
			return cmp * dir;
		});
		return list;
	});

	function opsFor(metric: string): Array<FilterCond['op']> {
		const def = METRICS_BY_KEY[metric];
		if (!def) return ['exists'];
		if (def.type === 'number') return ['>=', '<=', 'between', '==', '!=', 'exists'];
		if (def.type === 'enum') return ['==', '!=', 'exists'];
		return ['contains', '==', '!=', 'exists'];
	}

	function defaultOp(metric: string): FilterCond['op'] {
		const def = METRICS_BY_KEY[metric];
		if (def?.type === 'number') return def.higherBetter === false ? '<=' : '>=';
		if (def?.type === 'text') return 'contains';
		return '==';
	}

	function addCondition(metric = filteredFields[0]?.key ?? 'roe') {
		drafts = [
			...drafts,
			{ id: nextId++, metric, op: defaultOp(metric), value: '', value2: '' }
		];
	}

	function removeCondition(id: number) {
		drafts = drafts.filter((d) => d.id !== id);
	}

	function setPreset(kind: 'value' | 'growth' | 'quality' | 'risk' | 'revenue') {
		const preset: Record<typeof kind, { drafts: Omit<DraftCond, 'id'>[]; sort: SortKey }> = {
			value: {
				drafts: [
					{ metric: 'pbr', op: '<=', value: '1', value2: '' },
					{ metric: 'roe', op: '>=', value: '10', value2: '' },
					{ metric: 'debtRatio', op: '<=', value: '100', value2: '' }
				],
				sort: { key: 'pbr', dir: 'asc' }
			},
			growth: {
				drafts: [
					{ metric: 'revenueYoyPct', op: '>=', value: '20', value2: '' },
					{ metric: 'opMargin', op: '>=', value: '0', value2: '' }
				],
				sort: { key: 'revenueYoyPct', dir: 'desc' }
			},
			quality: {
				drafts: [
					{ metric: 'roe', op: '>=', value: '15', value2: '' },
					{ metric: 'debtRatio', op: '<=', value: '100', value2: '' }
				],
				sort: { key: 'roe', dir: 'desc' }
			},
			risk: {
				drafts: [{ metric: 'debtRatio', op: '>=', value: '200', value2: '' }],
				sort: { key: 'debtRatio', dir: 'desc' }
			},
			revenue: {
				drafts: [{ metric: 'revenueYoyPct', op: '>=', value: '10', value2: '' }],
				sort: { key: 'revenueYoyPct', dir: 'desc' }
			}
		};
		const next = preset[kind];
		drafts = next.drafts.map((d) => ({ ...d, id: nextId++ }));
		sortKey = next.sort.key;
		sortDir = next.sort.dir;
	}

	function toCond(draft: DraftCond): FilterCond | null {
		if (!draft.metric) return null;
		if (draft.op === 'exists') return { metric: draft.metric, op: 'exists' };
		const def = METRICS_BY_KEY[draft.metric];
		if (draft.op === 'between') {
			const a = parseInputValue(def, draft.value);
			const b = parseInputValue(def, draft.value2);
			if (a === null || b === null) return null;
			return { metric: draft.metric, op: 'between', value: a, value2: b };
		}
		const value = parseInputValue(def, draft.value);
		if (value === null) return null;
		return { metric: draft.metric, op: draft.op, value };
	}

	function parseInputValue(def: MetricDef | undefined, raw: string): number | string | null {
		const text = raw.trim();
		if (!text) return null;
		if (def?.type === 'number') {
			const n = Number(text.replace(/,/g, ''));
			return Number.isFinite(n) ? n : null;
		}
		return text;
	}

	// 판정은 verdict.ts SSOT 한 곳. 이 컴포넌트가 자체 evalCond 를 갖고 있던 동안
	// 메인 그리드와 미리보기의 결측 처리가 서로 달랐다 (여기는 ==/!= 에 억원 스케일 미적용).
	function comparableValue(value: unknown): unknown {
		return value;
	}

	function applyScreen() {
		const fields = new Set<string>(['label', 'id', 'market', 'industryName']);
		for (const cond of compiledConds) fields.add(cond.metric);
		if (sortKey) fields.add(sortKey);
		onApply({
			conds: compiledConds,
			sorts: sortKey ? [{ key: sortKey, dir: sortDir }] : [],
			cols: Array.from(fields)
		});
	}

	function formatValue(node: ScanNode, key: string): string {
		const def = METRICS_BY_KEY[key];
		const value = (node as Record<string, unknown>)[key];
		if (def?.format) return def.format(value);
		if (typeof value === 'number') return value.toLocaleString('ko-KR', { maximumFractionDigits: 2 });
		return String(value ?? '-');
	}
</script>

<section class="screen-builder" aria-label="스크린 조건 빌더">
	<div class="sb-left">
		<div class="sb-head">
			<div>
				<div class="sb-title">
					<SlidersHorizontal size={14} />
					스크린 빌더
				</div>
				<div class="sb-sub">{nodes.length.toLocaleString('ko-KR')}사 · 조건 {compiledConds.length}</div>
			</div>
			<button type="button" class="sb-apply" onclick={applyScreen}>적용</button>
		</div>

		<div class="preset-row" aria-label="빠른 스크린">
			<button type="button" onclick={() => setPreset('value')}>가치</button>
			<button type="button" onclick={() => setPreset('growth')}>성장</button>
			<button type="button" onclick={() => setPreset('quality')}>퀄리티</button>
			<button type="button" onclick={() => setPreset('risk')}>위험</button>
			<button type="button" onclick={() => setPreset('revenue')}>매출 증가</button>
		</div>

		<div class="field-search">
			<Search size={13} />
			<input bind:value={fieldQuery} placeholder="필드 검색: ROE, 매출, PBR, 부채..." />
		</div>

		<div class="field-list">
			{#each filteredFields as field (field.key)}
				<button type="button" class="field-row" onclick={() => addCondition(field.key)}>
					<span class="field-main">
						<span class="field-label">{field.label}</span>
						<span class="field-key">{field.key}</span>
					</span>
					<span class="field-unit">{field.unit ?? field.type}</span>
					<Plus size={13} />
				</button>
			{/each}
		</div>
	</div>

	<div class="sb-right">
		<div class="conditions">
			<div class="section-title">조건</div>
			{#if drafts.length === 0}
				<div class="empty">왼쪽 필드를 누르거나 빠른 스크린을 선택하세요.</div>
			{/if}
			{#each drafts as draft (draft.id)}
				{@const def = METRICS_BY_KEY[draft.metric]}
				<div class="cond-row">
					<select
						value={draft.metric}
						onchange={(e) => {
							draft.metric = e.currentTarget.value;
							draft.op = defaultOp(draft.metric);
							draft.value = '';
							draft.value2 = '';
						}}
					>
						{#each usableFields as field (field.key)}
							<option value={field.key}>{field.label}</option>
						{/each}
					</select>
					<select bind:value={draft.op}>
						{#each opsFor(draft.metric) as op}
							<option value={op}>{op}</option>
						{/each}
					</select>
					{#if draft.op !== 'exists'}
						<input bind:value={draft.value} placeholder={def?.unit ?? '값'} />
						{#if draft.op === 'between'}
							<input bind:value={draft.value2} placeholder="최대" />
						{/if}
					{/if}
					<button type="button" class="row-x" onclick={() => removeCondition(draft.id)} aria-label="조건 제거">
						<X size={13} />
					</button>
				</div>
			{/each}
			<button type="button" class="add-row" onclick={() => addCondition()}>
				<Plus size={13} /> 조건 추가
			</button>
		</div>

		<div class="sort-row">
			<label>
				<span>정렬</span>
				<select bind:value={sortKey}>
					{#each sortFields as field (field.key)}
						<option value={field.key}>{field.label}</option>
					{/each}
				</select>
			</label>
			<label>
				<span>방향</span>
				<select bind:value={sortDir}>
					<option value="desc">내림차순</option>
					<option value="asc">오름차순</option>
				</select>
			</label>
		</div>

		<div class="preview">
			<div class="section-title">
				미리보기 {previewNodes.length.toLocaleString('ko-KR')}사
				{#if previewGrid.excludedForMissing > 0}
					<span class="unknown-n" title="조건 미달이 아니라 데이터가 없어 판정하지 못한 종목">
						결측 {previewGrid.excludedForMissing.toLocaleString('ko-KR')}
					</span>
				{/if}
			</div>
			<div class="preview-list">
				{#each previewNodes.slice(0, 12) as node (node.id)}
					<div class="preview-row">
						<span class="dot" style:background={(node.color as string) || '#64748b'}></span>
						<span class="name">{node.label}</span>
						<span class="code">{node.id}</span>
						<span class="value">{formatValue(node, sortKey)}</span>
					</div>
				{/each}
				{#if previewNodes.length === 0}
					<div class="empty">조건에 맞는 회사가 없습니다.</div>
				{/if}
			</div>
		</div>
	</div>
</section>

<style>
	.screen-builder {
		height: 100%;
		min-height: 0;
		display: grid;
		grid-template-columns: 360px 1fr;
		gap: 12px;
		color: #cbd5e1;
	}
	.sb-left, .sb-right {
		min-height: 0;
		background: #050811;
		border: 1px solid #1e2433;
		border-radius: 6px;
		padding: 12px;
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.sb-head, .sort-row {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}
	.sb-title {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		font-size: 13px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.sb-sub {
		margin-top: 3px;
		font-size: 10px;
		color: #64748b;
	}
	.sb-apply, .preset-row button, .add-row {
		height: 28px;
		border: 1px solid rgba(var(--amber-rgb), 0.45);
		border-radius: 4px;
		background: rgba(var(--amber-rgb), 0.08);
		color: var(--amber);
		font-size: 11px;
		font-family: inherit;
		cursor: pointer;
	}
	.sb-apply {
		padding: 0 14px;
		font-weight: 700;
	}
	.preset-row {
		display: flex;
		gap: 5px;
		flex-wrap: wrap;
	}
	.preset-row button {
		padding: 0 9px;
	}
	.field-search {
		height: 32px;
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 0 10px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #0a0e18;
		color: #64748b;
	}
	input, select {
		min-width: 0;
		height: 28px;
		border: 1px solid #1e2433;
		border-radius: 4px;
		background: #0a0e18;
		color: #dbeafe;
		font-size: 11px;
		font-family: inherit;
	}
	.field-search input {
		flex: 1;
		border: none;
		background: transparent;
		outline: none;
	}
	.field-list {
		min-height: 0;
		overflow-y: auto;
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.field-row {
		display: flex;
		align-items: center;
		gap: 8px;
		width: 100%;
		padding: 7px 8px;
		border: 1px solid transparent;
		border-radius: 4px;
		background: transparent;
		color: inherit;
		text-align: left;
		cursor: pointer;
	}
	.field-row:hover {
		background: rgba(255, 255, 255, 0.03);
		border-color: #1e2433;
	}
	.field-main {
		flex: 1;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 2px;
	}
	.field-label, .name {
		font-size: 11px;
		font-weight: 600;
		color: #f1f5f9;
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.field-key, .field-unit, .code {
		font-size: 9px;
		color: #64748b;
		font-family: monospace;
	}
	.conditions {
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.section-title {
		font-size: 10px;
		font-weight: 700;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}
	.unknown-n {
		margin-left: 6px;
		color: var(--dl-warn, #fbbf24);
		font-weight: 600;
		text-transform: none;
		letter-spacing: 0;
	}
	.cond-row {
		display: grid;
		grid-template-columns: minmax(160px, 1.4fr) 78px minmax(90px, 1fr) minmax(90px, 1fr) 28px;
		gap: 6px;
		align-items: center;
	}
	.cond-row input {
		padding: 0 8px;
	}
	.row-x {
		width: 28px;
		height: 28px;
		display: inline-flex;
		align-items: center;
		justify-content: center;
		border: 1px solid #1e2433;
		border-radius: 4px;
		background: #0a0e18;
		color: #64748b;
		cursor: pointer;
	}
	.add-row {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		gap: 5px;
		width: max-content;
		padding: 0 10px;
	}
	.sort-row {
		justify-content: flex-start;
	}
	.sort-row label {
		display: flex;
		align-items: center;
		gap: 6px;
		font-size: 10px;
		color: #64748b;
	}
	.preview {
		min-height: 0;
		flex: 1;
		display: flex;
		flex-direction: column;
		gap: 6px;
	}
	.preview-list {
		min-height: 0;
		overflow-y: auto;
		border: 1px solid #1e2433;
		border-radius: 5px;
	}
	.preview-row {
		display: grid;
		grid-template-columns: 10px minmax(120px, 1fr) 70px minmax(90px, 0.8fr);
		align-items: center;
		gap: 8px;
		min-height: 28px;
		padding: 0 10px;
		border-bottom: 1px solid rgba(30, 36, 51, 0.8);
	}
	.dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
	}
	.value {
		justify-self: end;
		font-size: 10px;
		color: #22c55e;
		font-family: monospace;
	}
	.empty {
		padding: 12px;
		color: #64748b;
		font-size: 11px;
	}
	@media (max-width: 920px) {
		.screen-builder {
			grid-template-columns: 1fr;
		}
	}
</style>
