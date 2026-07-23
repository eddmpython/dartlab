import { describe, expect, it, vi } from 'vitest';
import type { PyprocMachine } from 'pyproc';
import { PyprocCheckpointStore } from './pyprocCheckpointStore';

function fakeMachine() {
	let next = 1;
	let live = 0;
	const parents = new Map<number, number | undefined>([[0, undefined]]);
	const dispose = vi.fn(() => {
		next = 0;
		live = -1;
		parents.clear();
	});
	const checkpoint = vi.fn(() => {
		const index = next++;
		const parent = live < 0 ? undefined : live;
		parents.set(index, parent);
		live = index;
		return {
			index,
			parent,
			changedPages: index + 1,
			deltaBytes: index === 0 ? 131_072 : 65_536,
			kind: index === 0 ? 'base' as const : 'delta' as const,
			sp: null,
			restore: vi.fn()
		};
	});
	const restore = vi.fn((index: number) => {
		live = index;
		return { pagesWritten: 2, mbWritten: 0.13, rehashed: true };
	});
	const machine = {
		runtime: {
			memory: { byteLength: () => 262_144 },
			enableReactive: () => ({ dispose })
		},
		history: { checkpoint, restore }
	} as unknown as PyprocMachine;
	return { machine, checkpoint, restore, dispose };
}

describe('PyprocCheckpointStore', () => {
	it('내부 cp0을 숨기고 사용자 label과 부모 분기를 보존한다', () => {
		const { machine, restore } = fakeMachine();
		const store = new PyprocCheckpointStore(machine);

		const a = store.create('A');
		const b = store.create('B');
		store.restore(a.id);
		const branch = store.create('branch');

		expect(a).toMatchObject({ id: 'pyproc-1', parentId: null, label: 'A', pageCount: 4 });
		expect(b.parentId).toBe(a.id);
		expect(branch.parentId).toBe(a.id);
		expect(store.list().map((entry) => entry.label)).toEqual(['A', 'B', 'branch']);
		expect(restore).toHaveBeenCalledWith(1);
	});

	it('clear 후 새 기준 노드로 다시 시작한다', () => {
		const { machine, dispose } = fakeMachine();
		const store = new PyprocCheckpointStore(machine);
		store.create('old');

		store.clear();
		const fresh = store.create('fresh');

		expect(dispose).toHaveBeenCalledOnce();
		expect(fresh).toMatchObject({
			id: 'pyproc-0',
			parentId: null,
			baseBytes: 131_072,
			deltaBytes: 0
		});
	});

	it('목록 밖 id 복원을 거부한다', () => {
		const { machine } = fakeMachine();
		const store = new PyprocCheckpointStore(machine);
		expect(() => store.restore('pyproc-99')).toThrow('unknown checkpoint');
	});
});
