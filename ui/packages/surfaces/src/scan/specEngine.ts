import type {
	ScanDefineNode,
	ScanScreenDefinition,
	ScanScreenSpec,
	ScanSpecCondition
} from '@dartlab/ui-contracts';

import { FINANCE_COMPLETED_YEARS, financeMetricKey, financeRatioKey } from './financeAccounts';
import type { FilterCond, MetricDef, ScanNode, SortKey } from './types';
import { evalVerdict } from './verdict';

export interface ScreenSpecProjection {
	nodes: ScanNode[];
	conds: FilterCond[];
	sorts: SortKey[];
	columns: string[];
	metrics: Record<string, MetricDef>;
	loaders: Array<'finance5y'>;
	limit: number | null;
}

const RATIO_IDS: Record<string, string> = {
	roe: 'roe',
	roa: 'roa',
	debtRatio: 'debt_ratio',
	currentRatio: 'current_ratio',
	opMargin: 'op_margin',
	netMargin: 'net_margin'
};

const AXIS_KEYS: Record<string, string> = {
	'axis.debt.icr': 'icr'
};

/** 언어중립 screen spec을 현재 브라우저 노드 위에 투영한다. */
export function materializeScreenSpec(nodes: ScanNode[], spec: ScanScreenSpec): ScreenSpecProjection {
	const projected = nodes.map((node) => ({ ...node })) as ScanNode[];
	const directFields = collectDirectFields(spec);
	const metrics: Record<string, MetricDef> = {};

	for (const field of directFields) {
		for (const node of projected) {
			(node as Record<string, unknown>)[field] = directValue(node, field);
		}
		metrics[field] = metricFor(field, unitForDirect(field));
	}

	const defines = spec.define ?? {};
	for (const name of topoSort(defines)) {
		const field = `@${name}`;
		const node = defines[name];
		if (!node) continue;
		const values = evaluateDefine(projected, node);
		for (let index = 0; index < projected.length; index++) {
			(projected[index] as Record<string, unknown>)[field] = values[index];
		}
		metrics[field] = metricFor(field, unitForDefine(node));
	}

	const conds = (spec.where ?? []).map(toFilterCond);
	if ((spec.any?.length ?? 0) > 0) {
		const anyConds = spec.any!.map(toFilterCond);
		const allMetrics = { ...metrics };
		for (const node of projected) {
			const verdicts = anyConds.map((condition) => evalVerdict(node, condition, allMetrics));
			(node as Record<string, unknown>).__any__ = verdicts.includes('PASS')
				? 'PASS'
				: verdicts.includes('UNKNOWN')
					? 'UNKNOWN'
					: 'FAIL';
		}
		metrics.__any__ = {
			key: '__any__',
			label: 'OR 조건',
			group: 'screen',
			type: 'enum',
			definition: 'spec.any 조건 중 하나 이상 통과',
			source: 'ecosystem'
		};
		conds.push({ metric: '__any__', op: '==', value: 'PASS' });
	}

	return {
		nodes: projected,
		conds,
		sorts: spec.sort ? [{ key: spec.sort.field, dir: spec.sort.desc ? 'desc' : 'asc' }] : [],
		columns: columnsForSpec(spec),
		metrics,
		loaders: [...directFields].some((field) => field.startsWith('finance.')) ? ['finance5y'] : [],
		limit: typeof spec.limit === 'number' && spec.limit > 0 ? spec.limit : null
	};
}

export function screenDefinitionToPreset(definition: ScanScreenDefinition) {
	return {
		id: definition.id,
		title: definition.title,
		subtitle: definition.tags.join(' · '),
		desc: definition.evidence,
		category: definition.tags.includes('safety') ? ('safety' as const) : ('theme' as const),
		conds: [] as FilterCond[],
		sorts: [] as SortKey[],
		cols: columnsForSpec(definition.spec),
		loaders: collectDirectFields(definition.spec).size > 0 ? (['finance5y'] as Array<'finance5y'>) : [],
		spec: definition.spec,
		schemaVersion: definition.schemaVersion,
		notify: definition.notify
	};
}

function collectDirectFields(spec: ScanScreenSpec): Set<string> {
	const fields = new Set<string>();
	const add = (value: unknown) => {
		if (typeof value === 'string' && !value.startsWith('@')) fields.add(value);
	};
	for (const condition of [...(spec.where ?? []), ...(spec.any ?? [])]) add(condition.field);
	for (const field of spec.select ?? []) add(field);
	if (spec.sort) add(spec.sort.field);
	for (const node of Object.values(spec.define ?? {})) {
		add(node.field);
		add(node.left);
		add(node.right);
	}
	return fields;
}

function directValue(node: ScanNode, field: string): number | string | null {
	const record = node as Record<string, unknown>;
	if (field in record && record[field] !== undefined) return scalar(record[field]);
	const axisKey = AXIS_KEYS[field];
	if (axisKey) return scalar(record[axisKey]);
	if (field.startsWith('finance.account.')) {
		const account = field.slice('finance.account.'.length);
		return latestSeriesValue(node, accountSeries(node, account));
	}
	if (field.startsWith('finance.ratio.')) {
		const ratio = field.slice('finance.ratio.'.length);
		return latestSeriesValue(node, ratioSeries(node, ratio));
	}
	return null;
}

function seriesFor(node: ScanNode, field: string): Array<number | null> {
	if (field.startsWith('finance.account.')) {
		return accountSeries(node, field.slice('finance.account.'.length));
	}
	if (field.startsWith('finance.ratio.')) {
		return ratioSeries(node, field.slice('finance.ratio.'.length));
	}
	const value = numberOrNull((node as Record<string, unknown>)[field]);
	return [value];
}

function accountSeries(node: ScanNode, account: string): Array<number | null> {
	const record = node as Record<string, unknown>;
	return FINANCE_COMPLETED_YEARS.map((year) => numberOrNull(record[financeMetricKey(account, year)]));
}

function ratioSeries(node: ScanNode, ratio: string): Array<number | null> {
	const record = node as Record<string, unknown>;
	const ratioId = RATIO_IDS[ratio] ?? ratio;
	return FINANCE_COMPLETED_YEARS.map((year) => numberOrNull(record[financeRatioKey(ratioId, year)]));
}

function latestSeriesValue(_node: ScanNode, values: Array<number | null>): number | null {
	for (let index = values.length - 1; index >= 0; index--) {
		if (values[index] !== null) return values[index];
	}
	return null;
}

function evaluateDefine(nodes: ScanNode[], define: ScanDefineNode): Array<number | null> {
	const op = define.op;
	if (op === 'percentile' || op === 'zscore') return relativeValues(nodes, define, op);
	return nodes.map((node) => {
		if (op === 'mean' || op === 'min' || op === 'max' || op === 'yoy' || op === 'cagr' || op === 'slope') {
			const series = seriesFor(node, String(define.field ?? ''));
			const years = Math.max(1, Number(define.years ?? (op === 'yoy' ? 2 : series.length)));
			return temporalValue(series.slice(-years), op);
		}
		if (op === 'add' || op === 'sub' || op === 'mul' || op === 'div') {
			const left = operandValue(node, define.left);
			const right = operandValue(node, define.right);
			if (left === null || right === null) return null;
			if (op === 'add') return left + right;
			if (op === 'sub') return left - right;
			if (op === 'mul') return left * right;
			return right === 0 ? null : left / right;
		}
		const value = operandValue(node, define.field);
		if (value === null) return null;
		if (!op) return value;
		if (op === 'abs') return Math.abs(value);
		if (op === 'log') return value > 0 ? Math.log(value) : null;
		if (op === 'clip') return Math.min(define.max ?? Infinity, Math.max(define.min ?? -Infinity, value));
		return value;
	});
}

function relativeValues(
	nodes: ScanNode[],
	define: ScanDefineNode,
	op: 'percentile' | 'zscore'
): Array<number | null> {
	const groups = new Map<string, Array<{ index: number; value: number }>>();
	for (let index = 0; index < nodes.length; index++) {
		const value = operandValue(nodes[index], define.field);
		if (value === null) continue;
		const group = define.by === 'industry' ? String(nodes[index].industry ?? '') : '__all__';
		const entries = groups.get(group) ?? [];
		entries.push({ index, value });
		groups.set(group, entries);
	}
	const result: Array<number | null> = new Array(nodes.length).fill(null);
	for (const entries of groups.values()) {
		if (entries.length < 2) continue;
		if (op === 'percentile') {
			const sorted = [...entries].sort((a, b) => a.value - b.value);
			for (const entry of entries) {
				const equalIndexes = sorted
					.map((candidate, index) => ({ candidate, index }))
					.filter(({ candidate }) => candidate.value === entry.value)
					.map(({ index }) => index + 1);
				const averageRank = equalIndexes.reduce((sum, rank) => sum + rank, 0) / equalIndexes.length;
				result[entry.index] = (averageRank / entries.length) * 100;
			}
		} else {
			const mean = entries.reduce((sum, entry) => sum + entry.value, 0) / entries.length;
			const variance =
				entries.reduce((sum, entry) => sum + (entry.value - mean) ** 2, 0) / (entries.length - 1);
			const std = Math.sqrt(variance);
			if (std === 0) continue;
			for (const entry of entries) result[entry.index] = (entry.value - mean) / std;
		}
	}
	return result;
}

function temporalValue(values: Array<number | null>, op: string): number | null {
	const valid = values.map((value, index) => ({ value, index })).filter((item) => item.value !== null) as Array<{
		value: number;
		index: number;
	}>;
	if (valid.length === 0) return null;
	if (op === 'mean') return valid.reduce((sum, item) => sum + item.value, 0) / valid.length;
	if (op === 'min') return Math.min(...valid.map((item) => item.value));
	if (op === 'max') return Math.max(...valid.map((item) => item.value));
	if (op === 'yoy') {
		if (values.length < 2 || values.at(-2) == null || values.at(-1) == null || values.at(-2) === 0) return null;
		return (values.at(-1) as number) / (values.at(-2) as number) - 1;
	}
	if (op === 'cagr') {
		if (values.length < 2 || values[0] == null || values.at(-1) == null || values[0] <= 0 || (values.at(-1) as number) <= 0) return null;
		return ((values.at(-1) as number) / values[0]) ** (1 / (values.length - 1)) - 1;
	}
	if (valid.length < 2) return null;
	const meanX = valid.reduce((sum, item) => sum + item.index, 0) / valid.length;
	const meanY = valid.reduce((sum, item) => sum + item.value, 0) / valid.length;
	const denominator = valid.reduce((sum, item) => sum + (item.index - meanX) ** 2, 0);
	return denominator === 0
		? null
		: valid.reduce((sum, item) => sum + (item.index - meanX) * (item.value - meanY), 0) / denominator;
}

function operandValue(node: ScanNode, operand: string | number | undefined): number | null {
	if (typeof operand === 'number') return Number.isFinite(operand) ? operand : null;
	if (typeof operand !== 'string') return null;
	return numberOrNull((node as Record<string, unknown>)[operand] ?? directValue(node, operand));
}

function toFilterCond(condition: ScanSpecCondition): FilterCond {
	if (condition.op === 'between' && Array.isArray(condition.value)) {
		return { metric: condition.field, op: 'between', value: condition.value[0] as number, value2: condition.value[1] as number };
	}
	const op = condition.op === 'not_exists' ? 'exists' : condition.op;
	return { metric: condition.field, op, value: condition.value, negate: condition.op === 'not_exists' } as FilterCond;
}

function topoSort(defines: Record<string, ScanDefineNode>): string[] {
	const order: string[] = [];
	const visiting = new Set<string>();
	const visited = new Set<string>();
	const visit = (name: string) => {
		if (visited.has(name)) return;
		if (visiting.has(name)) throw new Error(`screen define cycle: @${name}`);
		const node = defines[name];
		if (!node) throw new Error(`unknown screen define: @${name}`);
		visiting.add(name);
		for (const ref of [node.field, node.left, node.right]) {
			if (typeof ref === 'string' && ref.startsWith('@')) visit(ref.slice(1));
		}
		visiting.delete(name);
		visited.add(name);
		order.push(name);
	};
	for (const name of Object.keys(defines)) visit(name);
	return order;
}

function columnsForSpec(spec: ScanScreenSpec): string[] {
	const mapped = (spec.select ?? []).map(displayMetricFor).filter((value): value is string => Boolean(value));
	return [...new Set(mapped)];
}

function displayMetricFor(field: string): string | null {
	if (field.startsWith('@')) return null;
	if (AXIS_KEYS[field]) return AXIS_KEYS[field];
	if (field.startsWith('finance.account.')) {
		return financeMetricKey(field.slice('finance.account.'.length), FINANCE_COMPLETED_YEARS.at(-1)!);
	}
	if (field.startsWith('finance.ratio.')) {
		const ratio = field.slice('finance.ratio.'.length);
		return financeRatioKey(RATIO_IDS[ratio] ?? ratio, FINANCE_COMPLETED_YEARS.at(-1)!);
	}
	return field;
}

function unitForDirect(field: string): string {
	if (field.startsWith('finance.account.')) return '원';
	if (field.startsWith('finance.ratio.')) return '%';
	if (field === 'axis.debt.icr') return '배';
	return '값';
}

function unitForDefine(node: ScanDefineNode): string {
	if (node.op === 'percentile') return '백분위';
	if (node.op === 'zscore') return '표준편차';
	if (node.op === 'cagr' || node.op === 'yoy') return '배';
	return node.field ? unitForDirect(node.field) : '값';
}

function metricFor(key: string, unit: string): MetricDef {
	return {
		key,
		label: key.startsWith('@') ? key.slice(1) : key,
		group: 'screen',
		type: 'number',
		unit,
		definition: '저장된 scan JSON spec에서 계산한 필드',
		source: 'finance5y'
	};
}

function scalar(value: unknown): number | string | null {
	if (typeof value === 'number') return Number.isFinite(value) ? value : null;
	if (typeof value === 'string') return value.trim() ? value : null;
	return null;
}

function numberOrNull(value: unknown): number | null {
	const scalarValue = scalar(value);
	if (typeof scalarValue === 'number') return scalarValue;
	if (typeof scalarValue !== 'string') return null;
	const number = Number(scalarValue.replace(/,/g, '').replace(/%|배/g, ''));
	return Number.isFinite(number) ? number : null;
}
