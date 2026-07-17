import { describe, expect, it } from 'vitest';
import { parseKnowledgeArticle } from './knowledgeArticle';

describe('Universe knowledge article parser', () => {
	it('turns bounded Skill OS markdown into safe structured blocks', () => {
		const blocks = parseKnowledgeArticle('## 판단\n\n첫 문장입니다.\n둘째 문장입니다.\n\n- 근거 A\n- 근거 B\n\n```python\ndartlab.scan("fields")\n```');
		expect(blocks).toEqual([
			{ kind: 'heading', level: 3, text: '판단' },
			{ kind: 'paragraph', text: '첫 문장입니다. 둘째 문장입니다.' },
			{ kind: 'list', items: ['근거 A', '근거 B'] },
			{ kind: 'code', language: 'python', text: 'dartlab.scan("fields")' }
		]);
	});

	it('fails bounded when an article contains excessive sections', () => {
		const blocks = parseKnowledgeArticle(Array.from({ length: 200 }, (_, index) => `## ${index}`).join('\n'), 12);
		expect(blocks).toHaveLength(12);
	});
});
