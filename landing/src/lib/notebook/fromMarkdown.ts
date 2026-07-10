// 블로그 글 원본(markdown)을 노트북 셀로 투영한다.
//
// 글이 SSOT 다. 노트북은 그 글의 사본이 아니라 투영이고, 굽는 산출물이 없다. 독자가 "노트북으로"
// 를 누르면 그 자리에서 markdown 을 잘라 셀을 만든다. 글을 고치면 다음 투영이 저절로 따라간다.
import type { Cell, Notebook } from './stores/notebookStore';

/** 한 글에 노트북 하나. 같은 글을 두 번 눌러도 사본이 늘지 않고 하던 곳으로 돌아간다. */
export function postNotebookId(slug: string): string {
	return `post:${slug}`;
}

export function isPostNotebook(notebookId: string): boolean {
	return notebookId.startsWith('post:');
}

const FRONTMATTER = /^---\r?\n[\s\S]*?\r?\n---\r?\n/;
const PY_FENCE = /^```(?:python|py)[^\n]*\n([\s\S]*?)^```[ \t]*$/gm;
// 산문에서 걷어 낼 것: 이미지, svelte 컴포넌트 태그, 그 밖의 코드펜스.
const IMAGE = /^!\[[^\]]*\]\([^)]*\)\s*$/gm;
const COMPONENT = /^<[A-Z][\s\S]*?\/>\s*$/gm;
const OTHER_FENCE = /^```[\s\S]*?^```[ \t]*$/gm;

function cleanProse(text: string): string {
	return text
		.replace(IMAGE, '')
		.replace(COMPONENT, '')
		.replace(OTHER_FENCE, '')
		.replace(/\n{3,}/g, '\n\n')
		.trim();
}

/**
 * markdown 을 셀 배열로 자른다. python 코드펜스는 코드 셀, 그 사이 산문은 markdown 셀.
 *
 * 셀 id 는 순번으로 결정한다. 사용자가 노트북에서 셀을 고치면 그 노트북이 자기 것이 되고,
 * 다시 "노트북으로" 를 눌러도 이미 있는 노트북을 열 뿐 덮어쓰지 않는다.
 */
export function markdownToCells(raw: string, slug: string): Cell[] {
	const body = raw.replace(FRONTMATTER, '');
	const cells: Cell[] = [];
	let cursor = 0;
	let n = 0;
	const push = (type: Cell['type'], content: string) => {
		if (content) cells.push({ id: `${slug}::${n++}`, type, content });
	};

	PY_FENCE.lastIndex = 0;
	for (let m = PY_FENCE.exec(body); m; m = PY_FENCE.exec(body)) {
		push('markdown', cleanProse(body.slice(cursor, m.index)));
		push('code', m[1].trim());
		cursor = m.index + m[0].length;
	}
	push('markdown', cleanProse(body.slice(cursor)));
	return cells;
}

export function markdownToNotebook(raw: string, slug: string, title: string, description: string): Notebook {
	const now = new Date().toISOString();
	return {
		id: postNotebookId(slug),
		title,
		description,
		cells: markdownToCells(raw, slug),
		metadata: { createdAt: now, updatedAt: now }
	};
}
