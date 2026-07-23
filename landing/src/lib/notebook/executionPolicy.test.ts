import { describe, expect, it } from 'vitest';

import type { Notebook } from './stores/notebookStore';
import {
	normalizeNotebookExecutionPolicy,
	prepareNotebookForLoad,
	resolveNotebookExecutionPolicy,
	withNotebookExecutionMode
} from './executionPolicy';

function makeNotebook(id: string, metadata: Partial<Notebook['metadata']> = {}): Notebook {
	return {
		id,
		title: '테스트',
		cells: [],
		metadata: {
			createdAt: '2026-07-23T00:00:00.000Z',
			updatedAt: '2026-07-23T00:00:00.000Z',
			...metadata
		}
	};
}

describe('resolveNotebookExecutionPolicy', () => {
	it('일반 노트북은 기존 반응형 자동 실행 계약을 유지한다', () => {
		expect(resolveNotebookExecutionPolicy(makeNotebook('local-1'))).toEqual({
			mode: 'reactive',
			autoRun: true
		});
	});

	it('옛 post 저장본도 순차 실행과 무자동실행으로 해석한다', () => {
		expect(resolveNotebookExecutionPolicy(makeNotebook('post:lesson'))).toEqual({
			mode: 'sequential',
			autoRun: false
		});
	});

	it('블로그 저장본에 오래된 autoRun true가 있어도 자동 실행하지 않는다', () => {
		const notebook = makeNotebook('post:lesson', {
			execution: {
				mode: 'reactive',
				autoRun: true
			}
		});
		expect(resolveNotebookExecutionPolicy(notebook)).toEqual({
			mode: 'reactive',
			autoRun: false
		});
	});
});

describe('normalizeNotebookExecutionPolicy', () => {
	it('옛 post 저장본에 명시 정책과 출처를 보강한다', () => {
		const normalized = normalizeNotebookExecutionPolicy(makeNotebook('post:lesson'));
		expect(normalized.metadata.sourceKind).toBe('blog-post');
		expect(normalized.metadata.execution).toEqual({
			mode: 'sequential',
			autoRun: false
		});
	});

	it('사용자가 고른 실행 모드는 보존하고 블로그 자동 실행만 막는다', () => {
		const notebook = makeNotebook('post:lesson', {
			sourceKind: 'blog-post',
			execution: {
				mode: 'reactive',
				autoRun: false
			}
		});
		expect(normalizeNotebookExecutionPolicy(notebook)).toBe(notebook);
	});

	it('모드 변경은 다른 메타데이터와 자동 실행 정책을 보존한다', () => {
		const notebook = makeNotebook('local-1', {
			category: 'analysis',
			execution: {
				mode: 'reactive',
				autoRun: false
			}
		});
		const sequential = withNotebookExecutionMode(notebook, 'sequential');
		expect(sequential.metadata.category).toBe('analysis');
		expect(sequential.metadata.execution).toEqual({
			mode: 'sequential',
			autoRun: false
		});
	});
});

describe('prepareNotebookForLoad', () => {
	it('옛 블로그 저장본의 반응형 검증 오류만 제거하고 실제 출력은 보존한다', () => {
		const legacy: Notebook = {
			...makeNotebook('post:lesson'),
			cells: [
				{
					id: 'a',
					type: 'code',
					content: 'c = 1',
					output: {
						type: 'error',
						data: 'Multiple definitions error: [c] is defined in multiple cells.',
						executedAt: '2026-07-23T00:00:00.000Z'
					}
				},
				{
					id: 'b',
					type: 'code',
					content: 'c = 2',
					output: {
						type: 'text',
						data: '2',
						executedAt: '2026-07-23T00:00:01.000Z'
					}
				}
			]
		};

		const prepared = prepareNotebookForLoad(legacy);

		expect(prepared.notebook.metadata.execution).toEqual({
			mode: 'sequential',
			autoRun: false
		});
		expect(prepared.outputs.has('a')).toBe(false);
		expect(prepared.outputs.get('b')?.data).toBe('2');
		expect(prepared.notebook.cells.every((cell) => cell.output === undefined)).toBe(true);
	});
});
