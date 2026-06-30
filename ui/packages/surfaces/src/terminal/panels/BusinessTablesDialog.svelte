<script lang="ts">
	// 사업 서술 표 상세. 생산능력·가동률·원재료·주요제품·매출수주 (II.사업의내용 HTML 표 격자전개).
	// 데이터 = panel contentRaw 런타임 직독(reportSource.businessTables). 종합점수·판정 0(NEVER-CLAIM).
	import type { Company, Lang } from '../lib/types';
	import type { BusinessTable } from '@dartlab/ui-contracts';

	interface Props {
		co: Company;
		lang: Lang;
		tables: BusinessTable[];
		onClose: () => void;
	}
	let { co, lang, tables, onClose }: Props = $props();
	const T = (kr: string, en: string): string => (lang === 'en' ? en : kr);

	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});

	const TOPIC_LABEL: Record<string, { kr: string; en: string }> = {
		salesOrder: { kr: '매출·수주 실적', en: 'SALES & ORDERS' },
		rawMaterial: { kr: '원재료·생산설비', en: 'MATERIALS & PRODUCTION' },
		productService: { kr: '주요 제품·서비스', en: 'KEY PRODUCTS' }
	};
	const isNum = (s: string): boolean => /\d{2,}/.test(s);
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div class="scrModal btModal" role="dialog" aria-modal="true" tabindex="-1" aria-label={T('사업 표 상세', 'business tables')} onclick={(e) => e.stopPropagation()}>
		<div class="scrHead">
			<span class="scrTitle">{T('사업 서술 표', 'BUSINESS TABLES')} · {co.name.kr}</span>
			<span class="btHeadMeta">{T('II.사업의내용 · 최신 사업보고서', 'business overview · latest annual')}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>
		<div class="btBody">
			{#each tables as t (t.topic)}
				<div class="btCard">
					<div class="btCardHd">
						<span class="btCardTitle">{T(TOPIC_LABEL[t.topic]?.kr ?? t.title, TOPIC_LABEL[t.topic]?.en ?? t.title)}</span>
						<span class="dim">· {t.title} · {t.period}</span>
					</div>
					<div class="btScroll">
						<table class="btTbl">
							<thead>
								<tr>{#each t.headers as h, i (i)}<th class={i === 0 ? 'l' : 'r'}>{h}</th>{/each}</tr>
							</thead>
							<tbody>
								{#each t.rows as row, ri (ri)}
									<tr>{#each row as cell, ci (ci)}<td class={ci === 0 ? 'l' : isNum(cell) ? 'r mono' : 'l'}>{cell}</td>{/each}</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/each}
			{#if !tables.length}
				<div class="storyEmpty">{T('사업 서술 표 미공시.', 'no business tables.')}</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.btHeadMeta {
		font-family: var(--cond);
		font-size: 9.5px;
		color: var(--dimmer);
		letter-spacing: 0.03em;
	}
	.btBody {
		overflow: auto;
		padding: 4px 2px;
	}
	.btCard {
		margin-bottom: 14px;
	}
	.btCardHd {
		display: flex;
		align-items: baseline;
		gap: 6px;
		margin: 2px 0 5px;
	}
	.btCardTitle {
		font-family: var(--cond);
		font-size: 12px;
		font-weight: 700;
		color: var(--fg);
		letter-spacing: 0.02em;
	}
	.btCardHd .dim {
		font-size: 10px;
		color: var(--dim);
	}
	.btScroll {
		overflow-x: auto;
	}
	.btTbl {
		width: 100%;
		border-collapse: collapse;
		font-family: var(--mono);
		font-size: 10.5px;
	}
	.btTbl th {
		font-family: var(--cond);
		font-size: 9px;
		letter-spacing: 0.03em;
		color: var(--dimmer);
		font-weight: 600;
		padding: 2px 7px;
		border-bottom: 1px solid var(--bd);
		white-space: nowrap;
	}
	.btTbl td {
		padding: 3px 7px;
		border-bottom: 1px solid color-mix(in srgb, var(--bd) 40%, transparent);
		color: var(--txt);
		white-space: nowrap;
		max-width: 220px;
		overflow: hidden;
		text-overflow: ellipsis;
	}
	.btTbl tbody tr:hover td {
		background: rgba(91, 155, 240, 0.06);
	}
	.btTbl .r {
		text-align: right;
	}
	.btTbl .l {
		text-align: left;
	}
</style>
