const PAGE_BYTES = 65_536;

export interface WasmMemoryModule {
	HEAPU8: Uint8Array;
	_emscripten_stack_get_current?: () => number;
	_emscripten_stack_restore?: (pointer: number) => void;
}

export interface CheckpointInfo {
	id: string;
	parentId: string | null;
	label: string;
	pageCount: number;
	changedPages: number;
	deltaBytes: number;
	baseBytes: number;
}

interface CheckpointNode extends CheckpointInfo {
	hashes: Uint32Array;
	base: Uint8Array | null;
	delta: Map<number, Uint8Array>;
	stackPointer: number | null;
}

function hashPage(words: Uint32Array, start: number, end: number): number {
	let value = 2_166_136_261 >>> 0;
	for (let index = start; index < end; index += 1) {
		value = Math.imul((value ^ words[index]) >>> 0, 16_777_619) >>> 0;
	}
	return value;
}

function fingerprint(parentId: string, hashes: Uint32Array): string {
	let value = 2_166_136_261 >>> 0;
	for (let index = 0; index < parentId.length; index += 1) {
		value = Math.imul((value ^ parentId.charCodeAt(index)) >>> 0, 16_777_619) >>> 0;
	}
	for (const hash of hashes) value = Math.imul((value ^ hash) >>> 0, 16_777_619) >>> 0;
	return value.toString(16).padStart(8, '0');
}

/**
 * Capabilities: WASM 선형 메모리를 content-addressed 체크포인트 그래프로 보관한다.
 * Args: module은 Pyodide의 메모리 표면, maxStoredBytes는 그래프 전체 메모리 상한이다.
 * Returns: create와 restore는 저장 상태와 실제 write 비용을 정형 객체로 반환한다.
 * Example: root를 만든 뒤 상태 A와 B를 각각 commit하고 id로 전환한다.
 * Guide: 노트북 기본 실행에는 켜지 않는다. 명시적 실험 capability로만 사용한다.
 * SeeAlso: tests/_attempts/webNotebookRuntime.
 * Requires: 셀 실행 경계의 idle WASM 스택과 동일한 Pyodide 모듈 인스턴스.
 * AIContext: 오류 rollback은 저장된 live 해시가 아니라 현재 힙을 다시 완전 해시해야 정확하다.
 * LLM Specifications: AntiPatterns=무제한 delta, OutputSchema=CheckpointInfo, Prerequisites=idle kernel,
 * Freshness=runtime local, Dataflow=heap to page hashes to delta graph, TargetMarkets=none.
 */
export class CheckpointGraph {
	private readonly nodes = new Map<string, CheckpointNode>();
	private liveId: string | null = null;
	private storedBytes = 0;

	constructor(
		private readonly module: WasmMemoryModule,
		private readonly maxStoredBytes = 256 * 1024 * 1024
	) {}

	create(label = 'checkpoint'): CheckpointInfo {
		if (!this.liveId) return this.captureRoot(label);
		const parent = this.requireNode(this.liveId);
		const heap = this.module.HEAPU8;
		const hashes = this.pageHashes();
		const delta = new Map<number, Uint8Array>();
		let deltaBytes = 0;
		for (let page = 0; page < hashes.length; page += 1) {
			if (page < parent.hashes.length && hashes[page] === parent.hashes[page]) continue;
			const start = page * PAGE_BYTES;
			const bytes = heap.slice(start, Math.min(start + PAGE_BYTES, heap.length));
			delta.set(page, bytes);
			deltaBytes += bytes.length;
		}
		this.assertCapacity(deltaBytes);
		const id = `state-${fingerprint(parent.id, hashes)}`;
		const existing = this.nodes.get(id);
		if (existing) {
			this.liveId = id;
			return this.info(existing);
		}
		const node: CheckpointNode = {
			id,
			parentId: parent.id,
			label,
			pageCount: hashes.length,
			changedPages: delta.size,
			deltaBytes,
			baseBytes: 0,
			hashes,
			base: null,
			delta,
			stackPointer: this.stackPointer()
		};
		this.nodes.set(id, node);
		this.liveId = id;
		this.storedBytes += deltaBytes;
		return this.info(node);
	}

	restore(id: string): { id: string; pagesWritten: number; bytesWritten: number } {
		const target = this.requireNode(id);
		if (!this.liveId) throw new Error('checkpoint graph has no live state');
		const liveHashes = this.pageHashes();
		let pagesWritten = 0;
		let bytesWritten = 0;
		for (let page = 0; page < target.hashes.length; page += 1) {
			if (page < liveHashes.length && liveHashes[page] === target.hashes[page]) continue;
			const bytes = this.pageBytes(id, page);
			this.module.HEAPU8.set(bytes, page * PAGE_BYTES);
			pagesWritten += 1;
			bytesWritten += bytes.length;
		}
		if (target.stackPointer !== null) this.module._emscripten_stack_restore?.(target.stackPointer);
		this.liveId = id;
		return { id, pagesWritten, bytesWritten };
	}

	list(): CheckpointInfo[] {
		return Array.from(this.nodes.values(), (node) => this.info(node));
	}

	clear(): void {
		this.nodes.clear();
		this.liveId = null;
		this.storedBytes = 0;
	}

	private captureRoot(label: string): CheckpointInfo {
		const heap = this.module.HEAPU8;
		this.assertCapacity(heap.length);
		const hashes = this.pageHashes();
		const id = `root-${fingerprint(label, hashes)}`;
		const node: CheckpointNode = {
			id,
			parentId: null,
			label,
			pageCount: hashes.length,
			changedPages: 0,
			deltaBytes: 0,
			baseBytes: heap.length,
			hashes,
			base: heap.slice(),
			delta: new Map(),
			stackPointer: this.stackPointer()
		};
		this.nodes.set(id, node);
		this.liveId = id;
		this.storedBytes = heap.length;
		return this.info(node);
	}

	private pageHashes(): Uint32Array {
		const heap = this.module.HEAPU8;
		const words = new Uint32Array(heap.buffer, 0, Math.floor(heap.length / 4));
		const wordsPerPage = PAGE_BYTES / 4;
		const pageCount = Math.ceil(heap.length / PAGE_BYTES);
		const hashes = new Uint32Array(pageCount);
		for (let page = 0; page < pageCount; page += 1) {
			const start = page * wordsPerPage;
			const end = Math.min(start + wordsPerPage, words.length);
			hashes[page] = hashPage(words, start, end);
		}
		return hashes;
	}

	private pageBytes(id: string, page: number): Uint8Array {
		let node: CheckpointNode | undefined = this.requireNode(id);
		while (node) {
			const bytes = node.delta.get(page);
			if (bytes) return bytes;
			if (node.base) {
				const start = page * PAGE_BYTES;
				return node.base.subarray(start, Math.min(start + PAGE_BYTES, node.base.length));
			}
			node = node.parentId ? this.nodes.get(node.parentId) : undefined;
		}
		throw new Error(`page ${page} is missing from checkpoint ${id}`);
	}

	private requireNode(id: string): CheckpointNode {
		const node = this.nodes.get(id);
		if (!node) throw new Error(`unknown checkpoint ${id}`);
		return node;
	}

	private assertCapacity(additionalBytes: number): void {
		if (this.storedBytes + additionalBytes > this.maxStoredBytes) {
			throw new Error(`checkpoint memory limit exceeded: ${this.maxStoredBytes} bytes`);
		}
	}

	private stackPointer(): number | null {
		return this.module._emscripten_stack_get_current?.() ?? null;
	}

	private info(node: CheckpointNode): CheckpointInfo {
		return {
			id: node.id,
			parentId: node.parentId,
			label: node.label,
			pageCount: node.pageCount,
			changedPages: node.changedPages,
			deltaBytes: node.deltaBytes,
			baseBytes: node.baseBytes
		};
	}
}
