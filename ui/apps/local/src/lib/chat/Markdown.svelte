<script lang="ts">
	// marked(gfm) 로 마크다운을 렌더한다. 옛 ui/web MarkdownText(react-markdown+remark-gfm) 대응.
	// 표·헤딩·리스트·코드·인용을 제대로 그려서 "raw 파이프 표" 쓰레기 상태를 없앤다.
	import DOMPurify from 'dompurify';
	import { marked } from 'marked';

	let {
		text,
		onrefclick = () => undefined
	}: {
		text: string;
		onrefclick?: (refId: string) => void;
	} = $props();

	marked.setOptions({ gfm: true, breaks: false });

	// 로컬 추론모델(qwen3 등)이 흘리는 <think>...</think> 사고 블록 제거. 답변 본문만 보여준다.
	function stripThinking(t: string): string {
		let out = t.replace(/<think>[\s\S]*?<\/think>/gi, '');
		// 스트리밍 중 아직 닫히지 않은 <think> 이후는 잠정 숨김(닫히면 위 규칙이 처리).
		out = out.replace(/<think>[\s\S]*$/i, '');
		return out;
	}

	// 모델이 본문에 raw tool call id(`근거: call_xxx`)를 흘리는 회귀 차단. WorkLoop 칩이 이미 도구를 보여준다.
	function stripRawCallIds(t: string): string {
		let out = t.replace(/^[\s\-*•]*근거[\s:：][\s]*call_[A-Za-z0-9_]+\s*$/gm, '');
		out = out.replace(/^[\s\-*•]*\[?근거\]?\s*[:：]?\s*call_[A-Za-z0-9_]+\s*$/gm, '');
		out = out.replace(/근거[\s:：]+call_[A-Za-z0-9_]+/g, '근거');
		out = out.replace(/\n{3,}/g, '\n\n');
		return out;
	}

	// 볼드 정규화. 로컬 모델이 흘리는 `** 단어`(여는 별표 뒤 공백, left-flanking 실패)와
	// 닫힘 누락(줄 안 홀수 `**`)을 렌더 전에 보정해 raw 별표가 화면에 노출되지 않게 한다.
	function normalizeBold(t: string): string {
		let out = t.replace(/(?<=^|[^*])\*\*[ \t]+(?=\S)/gm, '**');
		out = out
			.split('\n')
			.map((line) => {
				const n = (line.match(/\*\*/g) || []).length;
				if (n % 2 === 1) {
					const i = line.lastIndexOf('**');
					return line.slice(0, i) + line.slice(i + 2);
				}
				return line;
			})
			.join('\n');
		return out;
	}

	// CommonMark flanking 보정. `**"..."**한글` 처럼 닫는 ** 뒤가 CJK 면 right-flanking 실패 -> 공백 삽입.
	// 여는 ** 는 줄시작/공백/괄호/파이프 뒤에만 온다는 lookbehind 로 닫는별+여는별 오인 쌍을 차단.
	function fixCjkBold(t: string): string {
		let out = t.replace(/(?<=^|[\s(|])\*\*\s*([^*\n]*?[^\s*])\s*\*\*/gm, '**$1**');
		out = out.replace(/(?<=^|[\s(|])(\*\*[^*\n]+?\*\*)(?=[가-힣ぁ-んァ-ヴー一-龥])/gm, '$1 ');
		return out;
	}

	// 답변 본문 ref 인용 계약 렌더. 엔진 프롬프트 §3-2 가 <kindRef:id> 각괄호 인용을 강행하므로
	// raw 노출 대신 작은 인용 chip 으로 변환한다 (스트립 아님, 계약 이행).
	const REF_LABEL: Record<string, string> = {
		tableRef: '표',
		valueRef: '값',
		dateRef: '날짜',
		docRef: '문서',
		webRef: '웹',
		skillRef: '스킬',
		sessionRef: '세션',
		artifactRef: '산출물',
		visualRef: '차트',
		verifyRef: '검증'
	};
	// 모델이 근거를 두 가지 형태로 쓴다. 계약 형태인 `<tableRef:id>` 와, 캡슐이 요구하는
	// "사용한 exact ref ID 인용" 을 따라 코드스팬에 그대로 적은 원시 id 다. 후자를 그냥 두면
	// 답변 끝에 `table:005930:IS:2025FY` 같은 긴 식별자가 여러 줄로 깔려 디버그 출력처럼 보인다.
	// 둘 다 잡아 같은 자리에서 번호 각주로 접는다. 전체 식별자는 툴팁과 클릭에 남긴다.
	// 종류를 빠뜨리면 그 하나만 원시 식별자로 남아 오히려 더 눈에 띈다. 촬영에서
	// industry 접두어가 그렇게 남는 것을 확인하고 채웠다.
	const RAW_REF_KINDS =
		'table|value|date|doc|web|execution|artifact|visual|skill|session|verify|industry|credit|source|outcome';

	function chipHtml(label: string, id: string, title: string): string {
		return (
			`<button type="button" class="refchip" value="${encodeURIComponent(id)}"` +
			` title="${title.replace(/"/g, '&quot;')}" aria-label="근거 ${label} 열기">${label}</button>`
		);
	}

	function renderRefChips(t: string): string {
		const numbers = new Map<string, number>();
		const numberOf = (id: string): number => {
			const seen = numbers.get(id);
			if (seen) return seen;
			const next = numbers.size + 1;
			numbers.set(id, next);
			return next;
		};
		return t
			.replace(
				/<(tableRef|valueRef|dateRef|docRef|webRef|skillRef|sessionRef|artifactRef|visualRef|verifyRef):([^<>\s"']+)>/g,
				(_m, kind: string, id: string) => chipHtml(REF_LABEL[kind] ?? kind, id, id)
			)
			.replace(
				// 기간 범위 ref 는 물결을 쓴다 (date:005930:IS:2023FY~2025FY). 빠뜨리면 그 하나만
				// 접히지 않고 원시 식별자로 남아 오히려 더 눈에 띈다.
				new RegExp('`(' + RAW_REF_KINDS + '):([A-Za-z0-9._:{}~\\-,]+)`', 'g'),
				(_m, kind: string, rest: string) => {
					const id = `${kind}:${rest}`;
					return chipHtml(String(numberOf(id)), id, id);
				}
			);
	}

	function handleRefClick(event: MouseEvent): void {
		const target = event.target;
		if (!(target instanceof Element)) return;
		const button = target.closest<HTMLButtonElement>('button.refchip[value]');
		if (!button) return;
		try {
			onrefclick(decodeURIComponent(button.value));
		} catch {
			// 손상된 모델 citation은 동작시키지 않는다.
		}
	}

	const html = $derived.by(() => {
		const cleaned = renderRefChips(fixCjkBold(normalizeBold(stripRawCallIds(stripThinking(text ?? '')))));
		return DOMPurify.sanitize(marked.parse(cleaned) as string, {
			ALLOWED_TAGS: [
				'p', 'br', 'strong', 'em', 'del', 'blockquote', 'hr', 'ul', 'ol', 'li', 'button',
				'h1', 'h2', 'h3', 'h4', 'code', 'pre', 'a', 'span', 'table', 'thead',
				'tbody', 'tr', 'th', 'td'
			],
			ALLOWED_ATTR: ['href', 'target', 'rel', 'class', 'title', 'type', 'value', 'aria-label'],
			ALLOW_DATA_ATTR: false
		}) as unknown as string;
	});
</script>

<!-- generated citation은 실제 button이며 이 div는 click delegation만 담당한다. -->
<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
<div class="md" role="presentation" onclick={handleRefClick}>{@html html}</div>

<style>
	.md {
		font-size: 0.92rem;
		line-height: 1.7;
		color: var(--dl-ink, #e7e7ea);
		word-break: keep-all;
		overflow-wrap: anywhere;
	}
	.md :global(> :first-child) {
		margin-top: 0;
	}
	.md :global(> :last-child) {
		margin-bottom: 0;
	}
	.md :global(p) {
		margin: 0.75rem 0;
	}
	.md :global(strong) {
		font-weight: 600;
		color: var(--dl-ink, #e7e7ea);
	}
	.md :global(em) {
		font-style: italic;
	}
	.md :global(ul),
	.md :global(ol) {
		margin: 0.75rem 0;
		padding-left: 1.5rem;
	}
	.md :global(li) {
		margin: 0.35rem 0;
	}
	.md :global(li::marker) {
		color: var(--dl-ink-mute, #6b7280);
	}
	.md :global(h1) {
		font-size: 1.25rem;
		font-weight: 700;
		letter-spacing: -0.01em;
		margin: 1.25rem 0 0.75rem;
	}
	.md :global(h2) {
		font-size: 1.1rem;
		font-weight: 600;
		letter-spacing: -0.01em;
		margin: 1.25rem 0 0.5rem;
	}
	.md :global(h3) {
		font-size: 1rem;
		font-weight: 600;
		margin: 1rem 0 0.4rem;
	}
	.md :global(h4) {
		font-size: 0.9rem;
		font-weight: 600;
		margin: 0.75rem 0 0.25rem;
	}
	.md :global(blockquote) {
		margin: 0.6rem 0;
		padding-left: 0.85rem;
		border-left: 2px solid var(--dl-line, #2a2c33);
		color: var(--dl-ink-dim, #9aa0aa);
		font-style: italic;
	}
	.md :global(hr) {
		margin: 1rem 0;
		border: none;
		border-top: 1px solid var(--dl-line, #2a2c33);
	}
	.md :global(a) {
		color: var(--dl-ink, #e7e7ea);
		text-decoration: underline;
		text-decoration-color: var(--dl-ink-mute, #6b7280);
		text-underline-offset: 2px;
	}
	.md :global(a:hover) {
		text-decoration-color: var(--dl-ink, #e7e7ea);
	}
	.md :global(code) {
		font-family: var(--dl-font-mono, ui-monospace, monospace);
		font-size: 0.86em;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 4px;
		padding: 0.1em 0.35em;
	}
	.md :global(pre) {
		margin: 0.6rem 0;
		padding: 0.85rem;
		overflow-x: auto;
		background: var(--dl-bg-raised, #16171a);
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 8px;
	}
	.md :global(pre code) {
		background: none;
		border: none;
		padding: 0;
		font-size: 0.82rem;
		line-height: 1.6;
	}
	/* GFM 표. 쓰레기였던 raw 파이프를 실제 표로. */
	.md :global(table) {
		display: block;
		width: max-content;
		max-width: 100%;
		overflow-x: auto;
		border-collapse: collapse;
		margin: 0.75rem 0;
		font-size: 0.8rem;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 8px;
	}
	.md :global(thead) {
		background: var(--dl-bg-raised, #16171a);
	}
	.md :global(th) {
		text-align: left;
		font-weight: 600;
		padding: 0.4rem 0.7rem;
		border-bottom: 1px solid var(--dl-line, #2a2c33);
		white-space: nowrap;
	}
	.md :global(td) {
		padding: 0.4rem 0.7rem;
		border-top: 1px solid var(--dl-line, #2a2c33);
		white-space: nowrap;
	}
	.md :global(tbody tr:hover) {
		background: color-mix(in srgb, var(--dl-bg-raised, #16171a) 60%, transparent);
	}
	/* 재무 답변은 기간이 여럿인 표가 잦다. 읽기 폭에 갇히면 12 기간 표가 좁게 눌려
	   가로 스크롤부터 만난다. 화면이 넓을 때만 오른쪽으로 더 뻗게 한다. 폭이 좁은 표는
	   max-content 라 그대로여서 왼쪽 정렬이 흐트러지지 않는다. */
	@media (min-width: 1180px) {
		.md :global(table) {
			max-width: calc(100% + 8rem);
		}
	}
	/* 숫자 칸은 자릿수를 맞춰 세로로 읽히게 한다. 재무 표에서 특히 중요하다. */
	.md :global(td),
	.md :global(th) {
		font-variant-numeric: tabular-nums;
	}
	/* 본문 ref 인용 chip. <kindRef:id> 계약의 표시형 (hover 시 title 로 풀 id). */
	.md :global(.refchip) {
		display: inline-flex;
		align-items: center;
		padding: 0 0.35em;
		margin: 0 0.12em;
		border: 1px solid var(--dl-line, #2a2c33);
		border-radius: 5px;
		background: var(--dl-bg-raised, #16171a);
		color: var(--dl-ink-dim, #9aa0aa);
		font-size: 0.68em;
		line-height: 1.5;
		vertical-align: 0.08em;
		font: inherit;
		cursor: pointer;
	}
	.md :global(.refchip:hover),
	.md :global(.refchip:focus-visible) {
		border-color: var(--dl-info, #6ab0ff);
		color: var(--dl-info, #6ab0ff);
		outline: none;
	}
</style>
