import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

import type { FilterCond, MetricDef, ScanNode } from './types';
import { evalVerdict } from './verdict';

interface ConformanceCase {
	id: string;
	kind: 'number' | 'text';
	unit: string;
	raw: unknown;
	condition: Omit<FilterCond, 'metric'>;
	expected: 'PASS' | 'FAIL' | 'UNKNOWN';
}

const fixtureUrl = new URL('../../../../../tests/fixtures/screenConformance.json', import.meta.url);
const cases = JSON.parse(readFileSync(fixtureUrl, 'utf8')) as ConformanceCase[];

describe('Python과 브라우저 screen 판정 의미 parity', () => {
	for (const entry of cases) {
		it(entry.id, () => {
			const metric: MetricDef = {
				key: 'value',
				label: '값',
				group: 'test',
				type: entry.kind === 'number' ? 'number' : 'text',
				unit: entry.unit,
				definition: '공유 conformance fixture',
				source: 'ecosystem'
			};
			const node: ScanNode = { id: entry.id, label: entry.id, industry: 'test', value: entry.raw };
			const condition = { metric: 'value', ...entry.condition } as FilterCond;
			if (condition.op === 'between' && Array.isArray(condition.value)) {
				const [value, value2] = condition.value;
				condition.value = value;
				condition.value2 = value2;
			}
			expect(evalVerdict(node, condition, { value: metric })).toBe(entry.expected);
		});
	}
});
