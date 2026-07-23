import { describe, expect, it } from 'vitest';

import {
	isPostNotebook,
	markdownToCells,
	markdownToNotebook,
	postNotebookId
} from './fromMarkdown';

const POST = `---
title: "테스트"
category: dartlab-stories
---

## 첫 절

산문 한 줄.

![그림](./assets/x.webp)

\`\`\`python
import dartlab
c = dartlab.Company("005930")
\`\`\`

설명이 이어진다.

\`\`\`bash
pip install dartlab
\`\`\`

\`\`\`python
c.market
\`\`\`

마지막 산문.
`;

describe('markdownToCells', () => {
	const cells = markdownToCells(POST, 'what-is-dartlab');

	it('python 코드펜스만 코드 셀이 된다', () => {
		const code = cells.filter((c) => c.type === 'code');
		expect(code).toHaveLength(2);
		expect(code[0].content).toContain('dartlab.Company("005930")');
		expect(code[1].content).toBe('c.market');
	});

	it('bash 코드펜스는 코드 셀이 아니고 산문에도 안 남는다', () => {
		const prose = cells
			.filter((c) => c.type === 'markdown')
			.map((c) => c.content)
			.join('\n');
		expect(prose).not.toContain('pip install dartlab');
	});

	it('frontmatter 와 이미지는 산문에서 걷어 낸다', () => {
		const prose = cells
			.filter((c) => c.type === 'markdown')
			.map((c) => c.content)
			.join('\n');
		expect(prose).not.toContain('category: dartlab-stories');
		expect(prose).not.toContain('./assets/x.webp');
		expect(prose).toContain('## 첫 절');
		expect(prose).toContain('마지막 산문.');
	});

	it('셀 id 는 결정적이다', () => {
		const again = markdownToCells(POST, 'what-is-dartlab');
		expect(cells.map((c) => c.id)).toEqual(again.map((c) => c.id));
		expect(cells[0].id.startsWith('what-is-dartlab::')).toBe(true);
	});
});

describe('라이브 데이터 투영 (블로그 <LiveData> -> 노트북 @[data])', () => {
	const POST_LIVE = `---
title: "t"
category: dartlab-stories
---

<script>
	import LiveData from '$lib/components/blog/LiveData.svelte';
</script>

## 절

시장 표를 본다.

<LiveData spec="scan/growth" caption="전상장사" />

끝.
`;
	const cells = markdownToCells(POST_LIVE, 'x');
	const prose = cells
		.filter((c) => c.type === 'markdown')
		.map((c) => c.content)
		.join('\n');

	it('script 스캐폴드는 셀에 안 남는다', () => {
		expect(prose).not.toContain('import LiveData');
		expect(prose).not.toContain('<script>');
	});

	it('<LiveData spec> 는 노트북 @[data] 로 투영된다(삭제 아님)', () => {
		expect(prose).toContain('@[data](scan/growth)');
		expect(prose).not.toContain('<LiveData');
	});
});

describe('postNotebookId', () => {
	it('글 하나에 노트북 하나. 두 번 눌러도 사본이 안 는다', () => {
		expect(postNotebookId('what-is-dartlab')).toBe('post:what-is-dartlab');
		expect(isPostNotebook('post:what-is-dartlab')).toBe(true);
		expect(isPostNotebook('c0ffee-uuid')).toBe(false);
	});

	it('블로그 투영은 순차 실행이고 페이지 진입 자동 실행이 없다', () => {
		const notebook = markdownToNotebook(POST, 'what-is-dartlab', '테스트', '설명');
		expect(notebook.metadata.sourceKind).toBe('blog-post');
		expect(notebook.metadata.execution).toEqual({
			mode: 'sequential',
			autoRun: false
		});
	});
});
