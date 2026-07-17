export type KnowledgeArticleBlock =
	| { kind: 'heading'; level: 2 | 3; text: string }
	| { kind: 'paragraph'; text: string }
	| { kind: 'list'; items: readonly string[] }
	| { kind: 'code'; language: string; text: string };

export function parseKnowledgeArticle(input: string, maxBlocks = 64): readonly KnowledgeArticleBlock[] {
	const lines = input.replace(/\r\n?/g, '\n').split('\n');
	const blocks: KnowledgeArticleBlock[] = [];
	let paragraph: string[] = [];
	let list: string[] = [];
	let code: string[] | null = null;
	let codeLanguage = '';

	function pushParagraph(): void {
		if (paragraph.length > 0) blocks.push({ kind: 'paragraph', text: paragraph.join(' ').trim() });
		paragraph = [];
	}

	function pushList(): void {
		if (list.length > 0) blocks.push({ kind: 'list', items: Object.freeze([...list]) });
		list = [];
	}

	for (const sourceLine of lines) {
		if (blocks.length >= maxBlocks) break;
		const line = sourceLine.trim();
		if (code) {
			if (line.startsWith('```')) {
				blocks.push({ kind: 'code', language: codeLanguage, text: code.join('\n') });
				code = null;
				codeLanguage = '';
			} else {
				code.push(sourceLine);
			}
			continue;
		}
		if (line.startsWith('```')) {
			pushParagraph();
			pushList();
			code = [];
			codeLanguage = line.slice(3).trim();
			continue;
		}
		const heading = /^(#{1,3})\s+(.+)$/.exec(line);
		if (heading?.[2]) {
			pushParagraph();
			pushList();
			blocks.push({ kind: 'heading', level: heading[1]?.length === 1 ? 2 : 3, text: heading[2] });
			continue;
		}
		const item = /^[-*]\s+(.+)$/.exec(line);
		if (item?.[1]) {
			pushParagraph();
			list.push(item[1]);
			continue;
		}
		if (!line) {
			pushParagraph();
			pushList();
			continue;
		}
		pushList();
		paragraph.push(line);
	}
	pushParagraph();
	pushList();
	if (code && blocks.length < maxBlocks) blocks.push({ kind: 'code', language: codeLanguage, text: code.join('\n') });
	return Object.freeze(blocks.slice(0, maxBlocks));
}
