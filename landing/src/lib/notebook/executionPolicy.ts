import type {
	Cell,
	CellOutput,
	Notebook,
	NotebookExecutionMode,
	NotebookExecutionPolicy
} from './stores/notebookStore';

const REACTIVE_POLICY: NotebookExecutionPolicy = {
	mode: 'reactive',
	autoRun: true
};

const BLOG_POST_POLICY: NotebookExecutionPolicy = {
	mode: 'sequential',
	autoRun: false
};

export function isBlogPostNotebook(notebook: Pick<Notebook, 'id' | 'metadata'>): boolean {
	return notebook.id.startsWith('post:') || notebook.metadata.sourceKind === 'blog-post';
}

export function resolveNotebookExecutionPolicy(
	notebook: Pick<Notebook, 'id' | 'metadata'>
): NotebookExecutionPolicy {
	const isBlogPost = isBlogPostNotebook(notebook);
	const fallback = isBlogPost ? BLOG_POST_POLICY : REACTIVE_POLICY;
	const stored = notebook.metadata.execution;
	const mode: NotebookExecutionMode =
		stored?.mode === 'reactive' || stored?.mode === 'sequential'
			? stored.mode
			: fallback.mode;

	return {
		mode,
		// 블로그 글은 반복 정의를 포함하는 순차 교재다. 오래된 저장본에 true가 남아 있어도
		// 페이지 진입만으로 공시 조회를 다시 실행하지 않는다.
		autoRun: isBlogPost ? false : stored?.autoRun ?? fallback.autoRun
	};
}

export function normalizeNotebookExecutionPolicy(notebook: Notebook): Notebook {
	const execution = resolveNotebookExecutionPolicy(notebook);
	const sourceKind = isBlogPostNotebook(notebook)
		? 'blog-post'
		: notebook.metadata.sourceKind;

	if (
		notebook.metadata.execution?.mode === execution.mode &&
		notebook.metadata.execution.autoRun === execution.autoRun &&
		notebook.metadata.sourceKind === sourceKind
	) {
		return notebook;
	}

	return {
		...notebook,
		metadata: {
			...notebook.metadata,
			...(sourceKind ? { sourceKind } : {}),
			execution
		}
	};
}

export function withNotebookExecutionMode(
	notebook: Notebook,
	mode: NotebookExecutionMode
): Notebook {
	const execution = resolveNotebookExecutionPolicy(notebook);
	return {
		...notebook,
		metadata: {
			...notebook.metadata,
			execution: {
				...execution,
				mode
			}
		}
	};
}

export function prepareNotebookForLoad(data: Notebook): {
	notebook: Notebook;
	outputs: Map<string, CellOutput>;
} {
	const normalized = normalizeNotebookExecutionPolicy(data);
	const execution = resolveNotebookExecutionPolicy(normalized);
	const outputs = new Map<string, CellOutput>();

	for (const cell of normalized.cells) {
		const staleReactiveError =
			execution.mode === 'sequential' &&
			cell.output?.type === 'error' &&
			cell.output.data.startsWith('Multiple definitions error:');
		if (cell.output && !staleReactiveError) {
			outputs.set(cell.id, cell.output);
		}
	}

	const cells = normalized.cells.map(({ output: _output, ...cell }) => cell as Cell);
	return {
		notebook: {
			...normalized,
			cells
		},
		outputs
	};
}
