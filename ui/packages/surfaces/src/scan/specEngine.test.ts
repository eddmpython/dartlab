import { SCAN_SCREEN_PRESETS } from '@dartlab/ui-contracts';
import { describe, expect, it } from 'vitest';

import { financeMetricKey, financeRatioKey } from './financeAccounts';
import { materializeScreenSpec } from './specEngine';
import type { ScanNode } from './types';
import { buildVerdictGrid } from './verdict';

function node(id: string, values: Record<string, number>): ScanNode {
	return { id, label: id, industry: '반도체', ...values };
}

describe('저장된 JSON screen spec 브라우저 실행', () => {
	it('하락장 재무안전 spec이 define과 직접 조건을 함께 실행한다', () => {
		const definition = SCAN_SCREEN_PRESETS.find((item) => item.id === 'financialStabilityDrawdown')!;
		const nodes = [
			node('A', {
				icr: 3,
				[financeMetricKey('cash_and_cash_equivalents', '2025')]: 100,
				[financeMetricKey('shortterm_borrowings', '2025')]: 20,
				[financeMetricKey('total_stockholders_equity', '2025')]: 200,
				[financeRatioKey('debt_ratio', '2025')]: 50,
				[financeRatioKey('current_ratio', '2025')]: 200
			}),
			node('B', {
				icr: 1,
				[financeMetricKey('cash_and_cash_equivalents', '2025')]: 10,
				[financeMetricKey('shortterm_borrowings', '2025')]: 20,
				[financeMetricKey('total_stockholders_equity', '2025')]: 200,
				[financeRatioKey('debt_ratio', '2025')]: 50,
				[financeRatioKey('current_ratio', '2025')]: 200
			})
		];
		const projection = materializeScreenSpec(nodes, definition.spec);
		const grid = buildVerdictGrid(projection.nodes, projection.conds, projection.metrics);
		expect(grid.members.map((item) => item.id)).toEqual(['A']);
		expect((projection.nodes[0] as Record<string, unknown>)['@netCash']).toBe(80);
		expect(projection.limit).toBe(40);
	});

	it('복리 성장 spec이 3년 시계열과 업종 백분위를 계산한다', () => {
		const definition = SCAN_SCREEN_PRESETS.find((item) => item.id === 'resilientCompounders')!;
		const years = ['2022', '2023', '2024', '2025'];
		const build = (id: string, sales: number[], op: number[], debt: number[], roe: number[]) => {
			const values: Record<string, number> = {};
			for (let index = 0; index < years.length; index++) {
				values[financeMetricKey('sales', years[index])] = sales[index];
				values[financeMetricKey('operating_profit', years[index])] = op[index];
				values[financeMetricKey('total_stockholders_equity', years[index])] = 100;
				values[financeRatioKey('debt_ratio', years[index])] = debt[index];
				values[financeRatioKey('roe', years[index])] = roe[index];
			}
			return node(id, values);
		};
		const projection = materializeScreenSpec(
			[
				build('A', [100, 110, 121, 140], [5, 6, 7, 8], [70, 70, 70, 70], [10, 12, 14, 20]),
				build('B', [100, 99, 98, 97], [5, 4, -1, 2], [80, 80, 80, 80], [10, 9, 8, 7])
			],
			definition.spec
		);
		const grid = buildVerdictGrid(projection.nodes, projection.conds, projection.metrics);
		expect(grid.members.map((item) => item.id)).toEqual(['A']);
		expect((projection.nodes[0] as Record<string, unknown>)['@roeIndPct']).toBe(100);
	});
});
