<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { EditorState } from '@codemirror/state';
	import { EditorView, keymap, lineNumbers, highlightActiveLine } from '@codemirror/view';
	import { python } from '@codemirror/lang-python';
	import { autocompletion, startCompletion, type CompletionContext } from '@codemirror/autocomplete';
	import { getCompletions } from '../stores/executionStore';
	import { defaultKeymap, indentWithTab } from '@codemirror/commands';
	import { syntaxHighlighting, bracketMatching, HighlightStyle } from '@codemirror/language';
	import { tags } from '@lezer/highlight';

	interface Props {
		content: string;
		isActive: boolean;
		isRunning: boolean;
		onContentChange: (content: string) => void;
		onRun: () => void;
		onRunAndMove: () => void;
	}

	let { content, isActive, isRunning, onContentChange, onRun, onRunAndMove }: Props = $props();

	let editorContainer: HTMLDivElement;
	let view: EditorView | null = null;
	let currentTheme = $state('dark');

	function detectTheme(): string {
		if (typeof document === 'undefined') return 'dark';
		return document.documentElement.getAttribute('data-theme') || 'dark';
	}

	const darkEditorTheme = EditorView.theme({
		'&': {
			fontSize: '0.9rem',
			backgroundColor: 'transparent',
		},
		'.cm-content': {
			fontFamily: "'Fira Code', 'Cascadia Code', monospace",
			padding: '8px 0',
			caretColor: '#ff2d95',
		},
		'.cm-gutters': {
			backgroundColor: 'transparent',
			color: '#6b7094',
			border: 'none',
			minWidth: '36px',
		},
		'.cm-activeLine': {
			backgroundColor: 'rgba(255, 255, 255, 0.03)',
		},
		'.cm-activeLineGutter': {
			backgroundColor: 'transparent',
			color: '#9898b0',
		},
		'&.cm-focused': {
			outline: 'none',
		},
		'.cm-cursor': {
			borderLeftColor: '#ff2d95',
		},
		'.cm-selectionBackground': {
			backgroundColor: 'rgba(255, 45, 149, 0.15) !important',
		},
		'.cm-line': {
			padding: '0 12px 0 4px',
		},
		'.cm-tooltip': {
			backgroundColor: '#1a1a2e',
			border: '1px solid #2a2a4a',
			borderRadius: '8px',
			boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
		},
		'.cm-tooltip-autocomplete > ul': {
			fontFamily: "'Fira Code', 'Cascadia Code', monospace",
			fontSize: '13px',
		},
		'.cm-tooltip-autocomplete > ul > li': {
			padding: '4px 8px',
		},
		'.cm-tooltip-autocomplete > ul > li[aria-selected]': {
			backgroundColor: 'rgba(255, 45, 149, 0.15)',
			color: '#e8e8f0',
		},
		'.cm-completionIcon': {
			opacity: '0.6',
		},
	});

	const darkSyntax = HighlightStyle.define([
		{ tag: tags.keyword, color: '#c678dd', fontWeight: '500' },
		{ tag: tags.string, color: '#98c379' },
		{ tag: tags.number, color: '#d19a66' },
		{ tag: tags.bool, color: '#d19a66' },
		{ tag: tags.null, color: '#d19a66' },
		{ tag: tags.comment, color: '#5c6370', fontStyle: 'italic' },
		{ tag: tags.function(tags.variableName), color: '#61afef' },
		{ tag: tags.className, color: '#61afef' },
		{ tag: tags.typeName, color: '#56b6c2' },
		{ tag: tags.operator, color: '#56b6c2', fontWeight: '500' },
		{ tag: tags.propertyName, color: '#e5c07b' },
		{ tag: tags.definition(tags.variableName), color: '#e06c75' },
		{ tag: tags.variableName, color: '#abb2bf' },
		{ tag: tags.self, color: '#e06c75' },
		{ tag: tags.special(tags.variableName), color: '#e06c75' },
	]);

	const lightEditorTheme = EditorView.theme({
		'&': {
			fontSize: '0.9rem',
			backgroundColor: 'transparent',
		},
		'.cm-content': {
			fontFamily: "'Fira Code', 'Cascadia Code', monospace",
			padding: '8px 0',
			caretColor: '#d6336c',
			color: '#1a1a2e',
		},
		'.cm-gutters': {
			backgroundColor: 'transparent',
			color: '#9ca3af',
			border: 'none',
			minWidth: '36px',
		},
		'.cm-activeLine': {
			backgroundColor: 'rgba(0, 0, 0, 0.02)',
		},
		'.cm-activeLineGutter': {
			backgroundColor: 'transparent',
			color: '#4b5563',
		},
		'&.cm-focused': {
			outline: 'none',
		},
		'.cm-cursor': {
			borderLeftColor: '#d6336c',
		},
		'.cm-selectionBackground': {
			backgroundColor: 'rgba(214, 51, 108, 0.12) !important',
		},
		'.cm-line': {
			padding: '0 12px 0 4px',
		},
		'.cm-tooltip': {
			backgroundColor: '#ffffff',
			border: '1px solid #e5e7eb',
			borderRadius: '8px',
			boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
		},
		'.cm-tooltip-autocomplete > ul': {
			fontFamily: "'Fira Code', 'Cascadia Code', monospace",
			fontSize: '13px',
		},
		'.cm-tooltip-autocomplete > ul > li': {
			padding: '4px 8px',
		},
		'.cm-tooltip-autocomplete > ul > li[aria-selected]': {
			backgroundColor: 'rgba(214, 51, 108, 0.1)',
			color: '#1a1a2e',
		},
		'.cm-completionIcon': {
			opacity: '0.6',
		},
	});

	const lightSyntax = HighlightStyle.define([
		{ tag: tags.keyword, color: '#7c3aed', fontWeight: '500' },
		{ tag: tags.string, color: '#a11' },
		{ tag: tags.number, color: '#164' },
		{ tag: tags.bool, color: '#219' },
		{ tag: tags.null, color: '#219' },
		{ tag: tags.comment, color: '#a0a1a7', fontStyle: 'italic' },
		{ tag: tags.function(tags.variableName), color: '#00c' },
		{ tag: tags.className, color: '#085' },
		{ tag: tags.typeName, color: '#00f' },
		{ tag: tags.operator, color: '#a2f', fontWeight: '500' },
		{ tag: tags.propertyName, color: '#05a' },
		{ tag: tags.definition(tags.variableName), color: '#e45649' },
		{ tag: tags.variableName, color: '#383a42' },
		{ tag: tags.self, color: '#e45649' },
		{ tag: tags.special(tags.variableName), color: '#e45649' },
	]);

	async function pythonCompletionSource(context: CompletionContext) {
		const line = context.state.doc.lineAt(context.pos);
		const textBefore = line.text.slice(0, context.pos - line.from);

		const dotMatch = textBefore.match(/([a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)\.(\w*)$/);
		if (dotMatch) {
			const objName = dotMatch[1];
			const partial = dotMatch[2];
			const from = context.pos - partial.length;
			try {
				const items = await getCompletions(objName);
				if (items.length === 0) return null;
				return {
					from,
					options: items.map((item) => ({
						label: item.label,
						type: item.type,
					})),
					validFor: /^\w*$/,
				};
			} catch {
				return null;
			}
		}

		const wordMatch = textBefore.match(/([a-zA-Z_]\w*)$/);
		if (wordMatch && wordMatch[1].length >= 2) {
			const partial = wordMatch[1];
			const from = context.pos - partial.length;
			try {
				const items = await getCompletions('');
				if (items.length === 0) return null;
				return {
					from,
					options: items
						.filter((item) => item.label.startsWith(partial))
						.map((item) => ({
							label: item.label,
							type: item.type,
						})),
					validFor: /^\w*$/,
				};
			} catch {
				return null;
			}
		}

		return null;
	}

	function createEditor() {
		if (!editorContainer) return;

		const cellKeymap = keymap.of([
			{
				key: 'Shift-Enter',
				run: () => {
					onRunAndMove();
					return true;
				},
			},
			{
				key: 'Ctrl-Enter',
				run: () => {
					onRun();
					return true;
				},
			},
		]);

		const extensions = [
			cellKeymap,
			keymap.of([...defaultKeymap, indentWithTab]),
			lineNumbers(),
			highlightActiveLine(),
			bracketMatching(),
			autocompletion({
				override: [pythonCompletionSource],
				activateOnTyping: true,
				activateOnTypingDelay: 100,
			}),
			python(),
			EditorView.updateListener.of((update) => {
				if (update.docChanged) {
					onContentChange(update.state.doc.toString());

					let hasDot = false;
					update.changes.iterChanges((_fromA, _toA, _fromB, _toB, inserted) => {
						if (inserted.toString().includes('.')) {
							hasDot = true;
						}
					});
					if (hasDot) {
						setTimeout(() => {
							if (update.view.hasFocus) {
								startCompletion(update.view);
							}
						}, 80);
					}
				}
			}),
		];

		if (currentTheme === 'dark') {
			extensions.push(darkEditorTheme, syntaxHighlighting(darkSyntax));
		} else {
			extensions.push(lightEditorTheme, syntaxHighlighting(lightSyntax));
		}

		const state = EditorState.create({
			doc: content,
			extensions,
		});

		view = new EditorView({
			state,
			parent: editorContainer,
		});
	}

	let observer: MutationObserver | null = null;

	onMount(() => {
		currentTheme = detectTheme();
		createEditor();

		observer = new MutationObserver((mutations) => {
			for (const m of mutations) {
				if (m.attributeName === 'data-theme') {
					const newTheme = detectTheme();
					if (newTheme !== currentTheme) {
						currentTheme = newTheme;
						const doc = view?.state.doc.toString() || content;
						view?.destroy();
						view = null;
						createEditor();
						const nextView: EditorView | null = view as EditorView | null;
						if (nextView && doc !== content) {
							nextView.dispatch({
								changes: { from: 0, to: nextView.state.doc.length, insert: doc },
							});
						}
					}
				}
			}
		});
		observer.observe(document.documentElement, { attributes: true });
	});

	onDestroy(() => {
		observer?.disconnect();
		view?.destroy();
	});

	$effect(() => {
		if (isActive && view) {
			view.focus();
		}
	});

	$effect(() => {
		const currentView = view;
		if (currentView && content !== currentView.state.doc.toString()) {
			currentView.dispatch({
				changes: {
					from: 0,
					to: currentView.state.doc.length,
					insert: content,
				},
			});
		}
	});
</script>

<div class="code-cell">
	<div class="editor-wrapper" bind:this={editorContainer}></div>
</div>

<style>
	.code-cell {
		position: relative;
		min-height: 36px;
	}

	.editor-wrapper {
		min-height: 36px;
	}
</style>
