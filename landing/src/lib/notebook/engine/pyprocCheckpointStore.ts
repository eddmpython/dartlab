import type { PyprocMachine, ReactiveController } from 'pyproc';
import type { CheckpointInfo } from './executionEngine';

const WASM_PAGE_BYTES = 65_536;

/**
 * 노트북의 문자열 id 체크포인트 계약을 pyproc machine.history에 연결한다.
 *
 * pyproc은 부팅 직후 내부 기준 체크포인트(cp0)를 만든다. 그 노드는 사용자 목록에서 숨기고,
 * 노트북이 명시적으로 만든 노드만 label과 함께 노출한다. 과거 노드를 복원한 뒤 새 노드를
 * 만들면 pyproc의 부모 트리를 그대로 따라 분기가 생긴다.
 */
export class PyprocCheckpointStore {
	private readonly entries = new Map<number, CheckpointInfo>();
	private readonly reactive: ReactiveController;

	constructor(private readonly machine: PyprocMachine) {
		this.reactive = machine.runtime.enableReactive();
	}

	create(label = 'checkpoint'): CheckpointInfo {
		const checkpoint = this.machine.history.checkpoint();
		const parent = checkpoint.parent === undefined ? null : this.entries.get(checkpoint.parent) ?? null;
		const info: CheckpointInfo = {
			id: this.id(checkpoint.index),
			parentId: parent?.id ?? null,
			label,
			pageCount: Math.ceil(this.machine.runtime.memory.byteLength() / WASM_PAGE_BYTES),
			changedPages: checkpoint.changedPages,
			deltaBytes: checkpoint.kind === 'delta' ? checkpoint.deltaBytes : 0,
			baseBytes: checkpoint.kind === 'base' ? checkpoint.deltaBytes : 0
		};
		this.entries.set(checkpoint.index, info);
		return { ...info };
	}

	restore(id: string): { id: string; pagesWritten: number; bytesWritten: number } {
		const index = this.requireIndex(id);
		const restored = this.machine.history.restore(index);
		return {
			id,
			pagesWritten: restored.pagesWritten,
			bytesWritten: Math.round(restored.mbWritten * 1_048_576)
		};
	}

	list(): CheckpointInfo[] {
		return Array.from(this.entries.values(), (entry) => ({ ...entry }));
	}

	clear(): void {
		this.reactive.dispose();
		this.entries.clear();
	}

	private id(index: number): string {
		return `pyproc-${index}`;
	}

	private requireIndex(id: string): number {
		const match = /^pyproc-(\d+)$/.exec(id);
		const index = match ? Number(match[1]) : Number.NaN;
		if (!Number.isInteger(index) || !this.entries.has(index)) {
			throw new Error(`unknown checkpoint ${id}`);
		}
		return index;
	}
}
