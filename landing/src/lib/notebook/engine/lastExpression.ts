// 셀의 마지막 식을 결과로 잡아 두는 코드 변형. 워커에서 갈라 낸 순수 함수라 테스트가 붙는다.
//
// 왜 갈랐나. 이 판정이 틀리면 셀이 **오류 없이 빈 출력**을 낸다. 아무도 모른 채 오래 살아 있었고
// (`c.select("IS", ["매출액"], freq="Y")` 가 통째로 삼켜졌다), 브라우저를 열어야만 보이는 버그였다.

/**
 * 마지막 줄이 대입문인가. 괄호 밖·따옴표 밖·주석 밖에 있는 `=` 하나면 대입이다.
 *
 * 예전에는 정규식 넷(단순·주석달린·첨자속성·튜플언팩)으로 갈랐는데 그중 `^[a-zA-Z_]\w*[\[.].*=`
 * 가 괄호 안 키워드 인자까지 삼켰다. 깊이를 세면 그 오인이 원천적으로 없다.
 */
export function isAssignment(line: string): boolean {
	if (line.startsWith('lambda ')) return false; // `lambda x=1: x` 의 기본값은 대입이 아니다
	let depth = 0;
	let quote = '';
	for (let i = 0; i < line.length; i++) {
		const ch = line[i];
		if (quote) {
			if (ch === '\\') i++;
			else if (ch === quote) quote = '';
			continue;
		}
		if (ch === '"' || ch === "'") quote = ch;
		else if (ch === '(' || ch === '[' || ch === '{') depth++;
		else if (ch === ')' || ch === ']' || ch === '}') depth--;
		else if (ch === '#') return false;
		else if (ch === '=' && depth === 0) {
			const prev = line[i - 1];
			if (line[i + 1] === '=') return false; // ==
			if (prev === '=' || prev === '!' || prev === '<' || prev === '>') return false; // 비교 연산
			if (prev === ':') return false; // walrus
			return true; // `=` 와 증강대입(`+=` `//=` 등) 둘 다 여기로 온다
		}
	}
	return false;
}

const STATEMENT_KEYWORDS = [
	'import ', 'from ', 'def ', 'class ', 'if ', 'elif ', 'else:',
	'for ', 'while ', 'try:', 'except', 'finally:', 'with ',
	'return ', 'yield ', 'raise ', 'pass', 'break', 'continue',
	'del ', 'assert ', 'global ', 'nonlocal ', 'async ', 'await ',
];

/** 마지막 줄이 식이면 `__eddmlab_result__` 에 담아 워커가 그 값을 렌더할 수 있게 한다. */
export function wrapLastExpression(code: string): string {
	const lines = code.trimEnd().split('\n');
	if (lines.length === 0) return code;
	const lastLine = lines[lines.length - 1];
	const trimmed = lastLine.trim();
	if (!trimmed || trimmed.startsWith('#')) return code;
	if (/^\s/.test(lastLine)) return code;
	if (STATEMENT_KEYWORDS.some((kw) => trimmed.startsWith(kw))) return code;
	if (isAssignment(trimmed)) return code;
	lines[lines.length - 1] = `__eddmlab_result__ = ${trimmed}`;
	return lines.join('\n') + '\n__eddmlab_result__';
}
