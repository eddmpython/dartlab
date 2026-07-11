import { describe, expect, it } from 'vitest';
import { CheckpointGraph, type WasmMemoryModule } from './checkpointGraph';

function memoryModule(pageCount = 2): WasmMemoryModule {
	return { HEAPU8: new Uint8Array(pageCount * 65_536) };
}

describe('CheckpointGraph', () => {
	it('restores uncommitted mutations for transactional rollback', () => {
		const module = memoryModule();
		module.HEAPU8[10] = 1;
		const graph = new CheckpointGraph(module, 1024 * 1024);
		const root = graph.create('root');
		module.HEAPU8[10] = 99;

		graph.restore(root.id);

		expect(module.HEAPU8[10]).toBe(1);
	});

	it('switches between branches from the same parent', () => {
		const module = memoryModule();
		const graph = new CheckpointGraph(module, 1024 * 1024);
		const root = graph.create('root');
		module.HEAPU8[1] = 20;
		const branchA = graph.create('a');
		graph.restore(root.id);
		module.HEAPU8[1] = 30;
		const branchB = graph.create('b');

		graph.restore(branchA.id);
		expect(module.HEAPU8[1]).toBe(20);
		graph.restore(branchB.id);
		expect(module.HEAPU8[1]).toBe(30);
		expect(graph.list().map((node) => node.parentId)).toEqual([null, root.id, root.id]);
	});

	it('blocks unbounded checkpoint storage', () => {
		const module = memoryModule();
		const graph = new CheckpointGraph(module, module.HEAPU8.length - 1);
		expect(() => graph.create('root')).toThrow('checkpoint memory limit exceeded');
	});
});
