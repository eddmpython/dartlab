export interface CellAnalysis {
	cellId: string;
	defines: Set<string>;
	uses: Set<string>;
}

const PYTHON_KEYWORDS = new Set([
	'if', 'else', 'elif', 'for', 'while', 'def', 'class', 'return', 'yield',
	'import', 'from', 'as', 'try', 'except', 'finally', 'with', 'raise',
	'pass', 'break', 'continue', 'and', 'or', 'not', 'in', 'is', 'True',
	'False', 'None', 'lambda', 'del', 'global', 'nonlocal', 'assert', 'async', 'await',
]);

const PYTHON_BUILTINS = new Set([
	'print', 'range', 'len', 'type', 'int', 'str', 'float', 'list', 'dict',
	'set', 'tuple', 'bool', 'enumerate', 'zip', 'map', 'filter', 'sorted',
	'abs', 'all', 'any', 'bin', 'chr', 'dir', 'divmod', 'format', 'getattr',
	'hasattr', 'hash', 'hex', 'id', 'input', 'isinstance', 'issubclass',
	'iter', 'max', 'min', 'next', 'oct', 'open', 'ord', 'pow', 'repr',
	'reversed', 'round', 'setattr', 'slice', 'sum', 'super', 'vars',
	'self', '__name__', '__main__', 'object', 'Exception', 'ValueError',
	'TypeError', 'KeyError', 'IndexError', 'AttributeError', 'RuntimeError',
	'StopIteration', 'NotImplementedError', 'FileNotFoundError', 'IOError',
]);

export function analyzeCell(cellId: string, code: string): CellAnalysis {
	const defines = new Set<string>();
	const allUses = new Set<string>();

	const lines = code.split('\n');
	for (const line of lines) {
		const trimmed = line.trim();
		if (!trimmed || trimmed.startsWith('#')) continue;

		const assignMatch = trimmed.match(/^([a-zA-Z_]\w*)\s*=[^=]/);
		if (assignMatch) defines.add(assignMatch[1]);

		const augAssignMatch = trimmed.match(/^([a-zA-Z_]\w*)\s*[+\-*/%&|^]=|<<=|>>=|\*\*=|\/\/=/);
		if (augAssignMatch) defines.add(augAssignMatch[1]);

		const annotatedAssignMatch = trimmed.match(/^([a-zA-Z_]\w*)\s*:\s*\S.*=[^=]/);
		if (annotatedAssignMatch) defines.add(annotatedAssignMatch[1]);

		const tupleUnpackMatch = trimmed.match(/^([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)+)\s*=[^=]/);
		if (tupleUnpackMatch) {
			tupleUnpackMatch[1].split(',').forEach((v) => {
				const name = v.trim();
				if (name && /^[a-zA-Z_]\w*$/.test(name)) defines.add(name);
			});
		}

		const defMatch = trimmed.match(/^def\s+([a-zA-Z_]\w*)/);
		if (defMatch) defines.add(defMatch[1]);

		const classMatch = trimmed.match(/^class\s+([a-zA-Z_]\w*)/);
		if (classMatch) defines.add(classMatch[1]);

		const forMatch = trimmed.match(/^for\s+([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)\s+in/);
		if (forMatch) {
			forMatch[1].split(',').forEach((v) => {
				const name = v.trim();
				if (name) defines.add(name);
			});
		}

		const importMatch = trimmed.match(/^import\s+(\w+)(?:\s+as\s+(\w+))?/);
		if (importMatch) defines.add(importMatch[2] || importMatch[1]);

		const fromMatch = trimmed.match(/^from\s+\w[\w.]*\s+import\s+(.+)/);
		if (fromMatch) {
			fromMatch[1].split(',').forEach((part) => {
				const asPart = part.trim().split(/\s+as\s+/);
				const name = (asPart.length > 1 ? asPart[1] : asPart[0]).trim();
				if (name && name !== '*') defines.add(name);
			});
		}

		const withMatch = trimmed.match(/^with\s+.+\s+as\s+([a-zA-Z_]\w*)/);
		if (withMatch) defines.add(withMatch[1]);
	}

	const identifiers = code.match(/\b[a-zA-Z_]\w*\b/g) || [];
	for (const id of identifiers) {
		if (!PYTHON_KEYWORDS.has(id) && !PYTHON_BUILTINS.has(id) && !defines.has(id)) {
			allUses.add(id);
		}
	}

	return { cellId, defines, uses: allUses };
}

export interface DependencyGraph {
	analyses: Map<string, CellAnalysis>;
	children: Map<string, Set<string>>;
	parents: Map<string, Set<string>>;
}

export function buildGraph(cells: { id: string; type: string; content: string }[]): DependencyGraph {
	const analyses = new Map<string, CellAnalysis>();
	const defRegistry = new Map<string, string>();

	const codeCells = cells.filter((c) => c.type === 'code');
	for (const cell of codeCells) {
		const analysis = analyzeCell(cell.id, cell.content);
		analyses.set(cell.id, analysis);
		for (const varName of analysis.defines) {
			defRegistry.set(varName, cell.id);
		}
	}

	const children = new Map<string, Set<string>>();
	const parents = new Map<string, Set<string>>();

	for (const cell of codeCells) {
		children.set(cell.id, new Set());
		parents.set(cell.id, new Set());
	}

	for (const cell of codeCells) {
		const analysis = analyses.get(cell.id);
		if (!analysis) continue;

		for (const varName of analysis.uses) {
			const defCellId = defRegistry.get(varName);
			if (defCellId && defCellId !== cell.id) {
				children.get(defCellId)!.add(cell.id);
				parents.get(cell.id)!.add(defCellId);
			}
		}
	}

	return { analyses, children, parents };
}

export function getDescendants(graph: DependencyGraph, cellId: string): string[] {
	const visited = new Set<string>();
	const queue = [cellId];

	while (queue.length > 0) {
		const current = queue.shift()!;
		const childSet = graph.children.get(current);
		if (!childSet) continue;

		for (const child of childSet) {
			if (!visited.has(child)) {
				visited.add(child);
				queue.push(child);
			}
		}
	}

	return Array.from(visited);
}

export function topologicalSort(
	cellIds: string[],
	graph: DependencyGraph,
	cellOrder: Map<string, number>
): string[] {
	const subset = new Set(cellIds);
	const inDegree = new Map<string, number>();

	for (const id of cellIds) {
		let deg = 0;
		const parentSet = graph.parents.get(id);
		if (parentSet) {
			for (const p of parentSet) {
				if (subset.has(p)) deg++;
			}
		}
		inDegree.set(id, deg);
	}

	const sorted: string[] = [];
	const ready = cellIds
		.filter((id) => inDegree.get(id) === 0)
		.sort((a, b) => (cellOrder.get(a) ?? 0) - (cellOrder.get(b) ?? 0));

	while (ready.length > 0) {
		const current = ready.shift()!;
		sorted.push(current);

		const childSet = graph.children.get(current);
		if (!childSet) continue;

		for (const child of childSet) {
			if (!subset.has(child)) continue;
			const newDeg = (inDegree.get(child) ?? 0) - 1;
			inDegree.set(child, newDeg);
			if (newDeg === 0) {
				const insertOrder = cellOrder.get(child) ?? 0;
				let insertIdx = ready.length;
				for (let i = 0; i < ready.length; i++) {
					if ((cellOrder.get(ready[i]) ?? 0) > insertOrder) {
						insertIdx = i;
						break;
					}
				}
				ready.splice(insertIdx, 0, child);
			}
		}
	}

	if (sorted.length < cellIds.length) {
		const remaining = cellIds
			.filter((id) => !sorted.includes(id))
			.sort((a, b) => (cellOrder.get(a) ?? 0) - (cellOrder.get(b) ?? 0));
		sorted.push(...remaining);
	}

	return sorted;
}

export function getReactiveCells(
	triggeredCellId: string,
	cells: { id: string; type: string; content: string }[]
): string[] {
	const graph = buildGraph(cells);
	const descendants = getDescendants(graph, triggeredCellId);

	if (descendants.length === 0) return [];

	const cellOrder = new Map<string, number>();
	cells.forEach((c, i) => cellOrder.set(c.id, i));

	return topologicalSort(descendants, graph, cellOrder);
}

export function detectMultipleDefinitions(
	cells: { id: string; type: string; content: string }[]
): Map<string, string[]> {
	const varOwners = new Map<string, string>();
	const conflicts = new Map<string, Set<string>>();

	const codeCells = cells.filter((c) => c.type === 'code');

	for (const cell of codeCells) {
		const analysis = analyzeCell(cell.id, cell.content);
		for (const varName of analysis.defines) {
			if (varName.startsWith('_')) continue;
			const existingOwner = varOwners.get(varName);
			if (existingOwner && existingOwner !== cell.id) {
				if (!conflicts.has(existingOwner)) conflicts.set(existingOwner, new Set());
				if (!conflicts.has(cell.id)) conflicts.set(cell.id, new Set());
				conflicts.get(existingOwner)!.add(varName);
				conflicts.get(cell.id)!.add(varName);
			} else {
				varOwners.set(varName, cell.id);
			}
		}
	}

	const result = new Map<string, string[]>();
	for (const [cellId, vars] of conflicts) {
		result.set(cellId, Array.from(vars).sort());
	}
	return result;
}
