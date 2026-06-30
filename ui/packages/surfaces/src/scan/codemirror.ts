/**
 * CodeMirror 6 mount helper · SQL editor with autocomplete + dark theme.
 *
 * 사용:
 *   const view = mountCodemirror({
 *     parent: divEl,
 *     doc: initial,
 *     onChange: (val) => sql = val,
 *     onRun: () => runCell(),
 *     schemaTables: { ecosystem: ['id','label',...], prices: ['stockCode',...] }
 *   });
 *   ...
 *   view.destroy();
 */

import { EditorState, type Extension } from '@codemirror/state';
import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
import { sql } from '@codemirror/lang-sql';
import { autocompletion } from '@codemirror/autocomplete';
import { defaultKeymap, history, historyKeymap } from '@codemirror/commands';
import { oneDark } from '@codemirror/theme-one-dark';

export interface MountOptions {
	parent: HTMLElement;
	doc: string;
	onChange?: (value: string) => void;
	onRun?: (mode: 'enter' | 'shift-enter') => void;
	/** 테이블 → 컬럼 list. autocomplete schema fed. */
	schemaTables?: Record<string, string[]>;
}

export function mountCodemirror(opts: MountOptions): EditorView {
	const updateListener = EditorView.updateListener.of((u) => {
		if (u.docChanged && opts.onChange) {
			opts.onChange(u.state.doc.toString());
		}
	});

	const runKeymap = keymap.of([
		{
			key: 'Mod-Enter',
			preventDefault: true,
			run: () => {
				opts.onRun?.('enter');
				return true;
			}
		},
		{
			key: 'Shift-Enter',
			preventDefault: true,
			run: () => {
				opts.onRun?.('shift-enter');
				return true;
			}
		}
	]);

	const sqlExt = opts.schemaTables
		? sql({ schema: opts.schemaTables, upperCaseKeywords: true })
		: sql({ upperCaseKeywords: true });

	const extensions: Extension[] = [
		lineNumbers(),
		highlightActiveLine(),
		history(),
		sqlExt,
		autocompletion(),
		oneDark,
		keymap.of(defaultKeymap),
		keymap.of(historyKeymap),
		runKeymap,
		updateListener,
		EditorView.theme({
			'&': {
				fontSize: '12px',
				fontFamily: "'JetBrains Mono', monospace"
			},
			'.cm-content': {
				padding: '8px 0'
			},
			'.cm-scroller': {
				lineHeight: '1.5'
			}
		})
	];

	const state = EditorState.create({
		doc: opts.doc,
		extensions
	});

	return new EditorView({
		state,
		parent: opts.parent
	});
}

/** 외부에서 schema 변경 시 호출 · view 재구성. */
export function updateSchema(view: EditorView, _schemaTables: Record<string, string[]>) {
	// 간단한 reload · schema 변경은 드물어 dispatch 보다 destroy + remount 권장.
	// 호출자가 destroy + mountCodemirror 재호출하면 됨.
	void view;
	void _schemaTables;
}
