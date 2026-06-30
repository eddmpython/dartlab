<script lang="ts">
	// panel 셀(raw DART XML) 렌더 · ui/web CellContent 이식. content-sniffing: html table / narrative.
	import DOMPurify from 'dompurify';
	import {
		normalizeDartXml,
		SANITIZE_CONFIG,
		splitHtmlAndText,
		absorbCaptionUnitFromText,
		stripInlineTags
	} from '../lib/cell';
	import { highlightParts } from '../lib/searchEvidence';

	let { value, highlightTerms = [] }: { value: string; highlightTerms?: string[] } = $props();

	type Seg = { kind: 'htmltable'; html: string; caption: string; unit: string } | { kind: 'text'; text: string };

	function clean(html: string): string {
		return DOMPurify.sanitize(html, SANITIZE_CONFIG) as unknown as string;
	}

	function build(v: string, highlight: string[]): Seg[] {
		if (!v || !v.trim()) return [];
		const html = normalizeDartXml(v);
		if (/<\s*table[\s>]/i.test(html)) {
			const out: Seg[] = [];
			let pendingCaption = '';
			let pendingUnit = '';
			for (const [kind, body] of splitHtmlAndText(html)) {
				if (kind === 'text') {
					const { caption, unit, remaining } = absorbCaptionUnitFromText(stripInlineTags(body));
					if (caption) pendingCaption = pendingCaption ? `${pendingCaption} · ${caption}` : caption;
					if (unit) pendingUnit = pendingUnit || unit;
					if (remaining) out.push({ kind: 'text', text: remaining.replace(/&cr;/g, ' ') });
				} else {
					out.push({ kind: 'htmltable', html: clean(body), caption: pendingCaption, unit: pendingUnit });
					pendingCaption = '';
					pendingUnit = '';
				}
			}
			if (pendingCaption || pendingUnit) out.push({ kind: 'htmltable', html: '', caption: pendingCaption, unit: pendingUnit });
			return out;
		}
		if (!/<[a-zA-Z]/.test(html)) return [{ kind: 'text', text: html.replace(/&cr;/g, ' ') }];
		if (highlight.length) return [{ kind: 'text', text: stripInlineTags(html).replace(/&cr;/g, ' ') }];
		return [{ kind: 'htmltable', html: clean(html), caption: '', unit: '' }];
	}

	const segments = $derived(build(value, highlightTerms));
</script>

{#if segments.length}
	<div class="cell-content">
		{#each segments as seg, i (i)}
			{#if seg.kind === 'text'}
				<div class="narrative">
					{#if highlightTerms.length}
						{#each highlightParts(seg.text, highlightTerms) as part}
							{#if part.hit}<mark>{part.text}</mark>{:else}{part.text}{/if}
						{/each}
					{:else}
						{seg.text}
					{/if}
				</div>
			{:else}
				<div class="table-block">
					{#if seg.caption || seg.unit}
						<div class="caption-row">
							<div class="caption">{seg.caption}</div>
							{#if seg.unit}<div class="unit">{seg.unit}</div>{/if}
						</div>
					{/if}
					{#if seg.html}
						<!-- eslint-disable-next-line svelte/no-at-html-tags -->
						<div class="dartlab-html">{@html seg.html}</div>
					{/if}
				</div>
			{/if}
		{/each}
	</div>
{/if}

<style>
	.cell-content {
		display: flex;
		flex-direction: column;
		gap: 10px;
	}
	.narrative {
		white-space: pre-wrap;
		overflow-wrap: anywhere;
		font-size: 13px;
		line-height: 1.55;
		color: #cbd5e1;
	}
	.narrative mark {
		padding: 0 2px;
		border-radius: 3px;
		background: rgba(251, 191, 36, 0.22);
		color: #fef3c7;
	}
	.table-block {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.caption-row {
		display: flex;
		align-items: baseline;
		justify-content: space-between;
		gap: 8px;
		font-size: 11px;
	}
	.caption {
		font-weight: 600;
		color: #e2e8f0;
	}
	.unit {
		color: #94a3b8;
	}
	.dartlab-html {
		overflow-x: auto;
		font-size: 12px;
		color: #cbd5e1;
	}
	.dartlab-html :global(table) {
		border-collapse: collapse;
	}
	.dartlab-html :global(td),
	.dartlab-html :global(th) {
		border: 1px solid #1e2433;
		padding: 3px 6px;
		vertical-align: top;
	}
	/* 원본 XML 이 숫자 셀에 ALIGN="RIGHT" 보유(실측 96/96) · author text-align 으로 덮어쓰지 않고 원본 align 존중
	   (feedback_xml_native_truth). align 없는 셀만 기본 좌측(표제·텍스트). 숫자=우측은 원본이 이미 가진 정렬. */
	.dartlab-html :global(td:not([align])),
	.dartlab-html :global(th:not([align])) {
		text-align: left;
	}
	.dartlab-html :global(th) {
		background: rgba(15, 23, 42, 0.6);
		font-weight: 600;
		color: #e2e8f0;
	}
	/* 원본 XML 문서구조 반영 · 절 제목(TITLE) 크게, 소항목 헤딩(USERMARK F-14↑) 볼드+위 줄바꿈, 인라인 볼드. */
	.dartlab-html :global(.dm-title) {
		font-size: 14.5px;
		font-weight: 700;
		color: #f1f5f9;
		margin: 2px 0 7px;
	}
	.dartlab-html :global(.dm-h) {
		display: block;
		margin-top: 9px;
		font-size: 13px;
		font-weight: 700;
		color: #e2e8f0;
	}
	.dartlab-html :global(.dm-b) {
		font-weight: 700;
		color: #e2e8f0;
	}
</style>
