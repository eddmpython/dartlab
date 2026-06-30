<script lang="ts">
	// 상용급 조건검색 · 주가·재무·등급 프리빌드 전필드 다조건 AND 스크리너 (eco + prices).
	// scan 보드 이동 없이 터미널 안에서 즉시. 결과 클릭 → 종목 로드.
	import type { Engine } from '../lib/engine';
	import type { EcoNode, Lang } from '../lib/types';
	import { chgClass } from '../ui/helpers';
	import { finTypeOf } from '../lib/finType'; // 재무 유형 라벨 SSOT · 좌측 레일과 동일 판정

	interface Props {
		eng: Engine;
		lang: Lang;
		open: boolean;
		onClose: () => void;
		onPick: (code: string) => void;
	}
	let { eng, lang, open, onClose, onPick }: Props = $props();

	type Px = ReturnType<Engine['priceOf']>;
	interface FieldDef {
		key: string;
		kr: string;
		en: string;
		group: 'price' | 'fin' | 'cat';
		unit: string;
		num?: (n: EcoNode, px: Px) => number | null;
		cat?: (n: EcoNode) => string | null;
	}
	const F: FieldDef[] = [
		// 주가
		{ key: 'ret1m', kr: '1개월 수익률', en: '1M return', group: 'price', unit: '%', num: (_n, p) => p?.return1m ?? null },
		{ key: 'ret3m', kr: '3개월 수익률', en: '3M return', group: 'price', unit: '%', num: (_n, p) => p?.return3m ?? null },
		{ key: 'ret1y', kr: '1년 수익률', en: '1Y return', group: 'price', unit: '%', num: (_n, p) => p?.return1y ?? null },
		{ key: 'vol1y', kr: '변동성 σ', en: 'volatility', group: 'price', unit: '', num: (_n, p) => p?.volatility1y ?? null },
		{ key: 'mktcap', kr: '시가총액', en: 'mkt cap', group: 'price', unit: '조', num: (_n, p) => (p?.marketCap != null ? p.marketCap / 1e12 : null) },
		{ key: 'w52pos', kr: '52주 위치', en: '52w pos', group: 'price', unit: '%', num: (_n, p) => (p && p.week52High != null && p.week52Low != null && p.week52High > p.week52Low ? Math.max(0, Math.min(100, ((p.currentPrice - p.week52Low) / (p.week52High - p.week52Low)) * 100)) : null) },
		{ key: 'foreign', kr: '외국인 지분', en: 'foreign %', group: 'price', unit: '%', num: (_n, p) => p?.foreignPct ?? null },
		{ key: 'beta', kr: '베타', en: 'beta', group: 'price', unit: '', num: (_n, p) => p?.beta ?? null },
		// 재무·지표
		{ key: 'roe', kr: 'ROE', en: 'ROE', group: 'fin', unit: '%', num: (n) => n.roe ?? null },
		{ key: 'opMargin', kr: '영업이익률', en: 'OP margin', group: 'fin', unit: '%', num: (n) => n.opMargin ?? null },
		{ key: 'revCagr', kr: '매출성장 CAGR', en: 'rev CAGR', group: 'fin', unit: '%', num: (n) => n.revCagr ?? null },
		{ key: 'marketShare', kr: '상장사매출비중', en: 'rev share(listed)', group: 'fin', unit: '%', num: (n) => n.marketShare ?? null },
		{ key: 'debtRatio', kr: '부채비율', en: 'debt ratio', group: 'fin', unit: '%', num: (n) => n.debtRatio ?? null },
		{ key: 'revenue', kr: '매출 규모', en: 'revenue', group: 'fin', unit: '조', num: (n) => (n.revenue != null ? n.revenue / 10000 : null) },
		{ key: 'roeDelta', kr: 'ROE 증감', en: 'ROE Δ', group: 'fin', unit: '%p', num: (n) => n.roeDelta ?? null },
		{ key: 'revYoy', kr: '매출 YoY', en: 'rev YoY', group: 'fin', unit: '%', num: (n) => n.revenueYoyPct ?? null },
		{ key: 'rank', kr: '업종 순위', en: 'industry rank', group: 'fin', unit: '위', num: (n) => n.industryRank ?? null },
		// 등급·범주
		{ key: 'market', kr: '시장', en: 'market', group: 'cat', unit: '', cat: (n) => (n.market === '유가증권' ? 'KOSPI' : n.market === '코스닥' ? 'KOSDAQ' : n.market ?? null) },
		{ key: 'sector', kr: '업종', en: 'sector', group: 'cat', unit: '', cat: (n) => n.industryName ?? null },
		{ key: 'finType', kr: '재무 유형', en: 'fin type', group: 'cat', unit: '', cat: (n) => finTypeOf(n, eng.raw.finance.companies[n.id], eng.priceOf(n.id)).primary?.name ?? null },
		{ key: 'profGrade', kr: '수익성 등급', en: 'profitability', group: 'cat', unit: '', cat: (n) => n.profGrade ?? null },
		{ key: 'growthGrade', kr: '성장성 등급', en: 'growth', group: 'cat', unit: '', cat: (n) => n.growthGrade ?? null },
		{ key: 'govGrade', kr: '거버넌스 등급', en: 'governance', group: 'cat', unit: '', cat: (n) => n.govGrade ?? null },
		{ key: 'qualGrade', kr: '이익질 등급', en: 'quality', group: 'cat', unit: '', cat: (n) => n.qualGrade ?? null },
		{ key: 'liqGrade', kr: '유동성 등급', en: 'liquidity', group: 'cat', unit: '', cat: (n) => n.liqGrade ?? null },
		{ key: 'cfPattern', kr: '현금흐름 패턴', en: 'CF pattern', group: 'cat', unit: '', cat: (n) => n.cfPattern ?? null },
		{ key: 'stability', kr: '경영 안정성', en: 'stability', group: 'cat', unit: '', cat: (n) => n.stability ?? null }
	];
	const byKey = Object.fromEntries(F.map((f) => [f.key, f]));
	const fmtNum = (f: FieldDef, v: number | null): string => {
		if (v == null) return '·';
		if (f.unit === '조') return v.toFixed(1) + '조';
		if (f.unit === '위') return v.toFixed(0) + '위';
		if (f.unit === '') return v.toFixed(2);
		return v.toFixed(1) + f.unit;
	};

	const nodes = $derived((eng.raw.eco?.nodes || []).filter((n) => eng.raw.finance.companies[n.id] && eng.priceOf(n.id)));
	// 범주 옵션 (universe 에서 distinct)
	const catOptions = (key: string): string[] => {
		const f = byKey[key];
		if (!f?.cat) return [];
		const s = new Set<string>();
		for (const n of nodes) { const v = f.cat(n); if (v) s.add(v); }
		return Array.from(s).sort();
	};

	interface Cond { id: number; field: string; op: '>=' | '<=' | 'is'; v: string }
	let seq = 0;
	let conds = $state<Cond[]>([{ id: seq++, field: 'roe', op: '>=', v: '10' }]);
	let sortKey = $state('mktcap');
	let sortDir = $state<'desc' | 'asc'>('desc');

	function addCond() { conds = [...conds, { id: seq++, field: 'opMargin', op: '>=', v: '' }]; }
	function removeCond(id: number) { conds = conds.filter((c) => c.id !== id); }
	function onFieldChange(c: Cond) {
		const f = byKey[c.field];
		c.op = f?.group === 'cat' ? 'is' : '>=';
		c.v = f?.group === 'cat' ? (catOptions(c.field)[0] ?? '') : '';
		conds = [...conds];
	}

	function pass(n: EcoNode, px: Px): boolean {
		for (const c of conds) {
			const f = byKey[c.field];
			if (!f) continue;
			if (f.group === 'cat') {
				if (!c.v) continue;
				if (f.cat!(n) !== c.v) return false;
			} else {
				if (c.v === '' || c.v == null) continue;
				const val = f.num!(n, px);
				const thr = Number(c.v);
				if (val == null || !Number.isFinite(thr)) return false;
				if (c.op === '>=' && !(val >= thr)) return false;
				if (c.op === '<=' && !(val <= thr)) return false;
			}
		}
		return true;
	}

	// 표시 컬럼 = 활성 수치 조건 필드 + sortKey (dedup, ≤4)
	const cols = $derived.by(() => {
		const out: string[] = [];
		const add = (k: string) => { const f = byKey[k]; if (f && f.group !== 'cat' && !out.includes(k)) out.push(k); };
		add(sortKey);
		for (const c of conds) add(c.field);
		return out.slice(0, 4);
	});

	const results = $derived.by(() => {
		const sf = byKey[sortKey];
		const rows = nodes
			.map((n) => ({ n, px: eng.priceOf(n.id) }))
			.filter((r) => pass(r.n, r.px))
			.map((r) => ({ n: r.n, px: r.px, sv: sf?.num ? sf.num(r.n, r.px) : null }));
		rows.sort((a, b) => {
			const av = a.sv, bv = b.sv;
			if (av == null && bv == null) return 0;
			if (av == null) return 1;
			if (bv == null) return -1;
			return sortDir === 'desc' ? bv - av : av - bv;
		});
		return rows.slice(0, 150);
	});
	const total = $derived(nodes.filter((n) => pass(n, eng.priceOf(n.id))).length);

	function choose(code: string) { onPick(code); }
	function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose(); }
</script>

<svelte:window onkeydown={open ? onKey : undefined} />

{#if open}
	<div class="scrimWrap" role="presentation" onclick={onClose}>
		<div class="scrModal" role="dialog" aria-modal="true" aria-label="조건검색" onclick={(e) => e.stopPropagation()}>
			<div class="scrHead">
				<span class="scrTitle">{lang === 'en' ? 'SCREENER' : '조건검색'}</span>
				<span class="scrCount">{lang === 'en' ? 'matches' : '조건 충족'} <b class="tAmber">{total.toLocaleString()}</b> / {nodes.length.toLocaleString()}</span>
				<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
			</div>

			<div class="scrConds">
				{#each conds as c (c.id)}
					{@const f = byKey[c.field]}
					<div class="scrCond">
						<select class="scrSel field" bind:value={c.field} onchange={() => onFieldChange(c)}>
							<optgroup label={lang === 'en' ? 'Price' : '주가'}>
								{#each F.filter((x) => x.group === 'price') as x (x.key)}<option value={x.key}>{lang === 'en' ? x.en : x.kr}</option>{/each}
							</optgroup>
							<optgroup label={lang === 'en' ? 'Financial' : '재무·지표'}>
								{#each F.filter((x) => x.group === 'fin') as x (x.key)}<option value={x.key}>{lang === 'en' ? x.en : x.kr}</option>{/each}
							</optgroup>
							<optgroup label={lang === 'en' ? 'Grade/Category' : '등급·범주'}>
								{#each F.filter((x) => x.group === 'cat') as x (x.key)}<option value={x.key}>{lang === 'en' ? x.en : x.kr}</option>{/each}
							</optgroup>
						</select>
						{#if f?.group === 'cat'}
							<span class="scrOp">=</span>
							<select class="scrSel val" bind:value={c.v}>
								{#each catOptions(c.field) as o (o)}<option value={o}>{o}</option>{/each}
							</select>
						{:else}
							<select class="scrSel op" bind:value={c.op}>
								<option value=">=">≥</option>
								<option value="<=">≤</option>
							</select>
							<input class="scrNum mono" type="number" bind:value={c.v} placeholder="·" />
							<span class="scrUnit">{f?.unit}</span>
						{/if}
						<button class="scrDel" onclick={() => removeCond(c.id)} aria-label="remove">✕</button>
					</div>
				{/each}
				<button class="scrAdd" onclick={addCond}>+ {lang === 'en' ? 'add condition' : '조건 추가'}</button>
			</div>

			<div class="scrSortRow">
				<span class="scrSortLbl">{lang === 'en' ? 'sort' : '정렬'}</span>
				<select class="scrSel sort" bind:value={sortKey}>
					{#each F.filter((x) => x.group !== 'cat') as x (x.key)}<option value={x.key}>{lang === 'en' ? x.en : x.kr}</option>{/each}
				</select>
				<button class="scrDirBtn" onclick={() => (sortDir = sortDir === 'desc' ? 'asc' : 'desc')}>{sortDir === 'desc' ? '▼ 높은순' : '▲ 낮은순'}</button>
				<span class="scrShown">{lang === 'en' ? 'showing' : '표시'} {results.length}</span>
			</div>

			<div class="scrResults">
				<table class="scrTable">
					<thead>
						<tr>
							<th class="r">#</th>
							<th class="l">{lang === 'en' ? 'Company' : '종목'}</th>
							{#each cols as k (k)}<th class="r">{lang === 'en' ? byKey[k].en : byKey[k].kr}</th>{/each}
						</tr>
					</thead>
					<tbody>
						{#each results as r, i (r.n.id)}
							<tr onclick={() => choose(r.n.id)}>
								<td class="r mono dim">{i + 1}</td>
								<td class="l"><b>{eng.nameOf(r.n.id)}</b><span class="scrInd">{r.n.industryName || ''}</span></td>
								{#each cols as k (k)}
									{@const f = byKey[k]}
									{@const v = f.num ? f.num(r.n, r.px) : null}
									<td class={'r mono ' + ((k === 'ret1m' || k === 'ret3m' || k === 'ret1y' || k === 'revYoy' || k === 'roeDelta') ? chgClass(v) : '')}>{fmtNum(f, v)}</td>
								{/each}
							</tr>
						{/each}
						{#if results.length === 0}
							<tr><td colspan={cols.length + 2} class="scrEmpty">{lang === 'en' ? 'no matches · loosen conditions' : '조건 충족 종목 없음 · 조건 완화'}</td></tr>
						{/if}
					</tbody>
				</table>
			</div>
		</div>
	</div>
{/if}
