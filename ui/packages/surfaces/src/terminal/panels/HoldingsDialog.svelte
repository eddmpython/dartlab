<script lang="ts">
	// 출자 관계 · 양방향 관계망 다이얼로그. 위=나를 소유한 주주(reverse)·중앙=본체·아래=내가 출자한 자회사(forward, tier 레인).
	// 모든 변수를 채널에 배정: 크기=장부가/지분, 색=이익기여(forward)·주주유형(reverse), 테두리=상장, 모양=법인/개인, 엣지=지분%·방향.
	// 좌표는 holdings.ts buildNetworkLayout(순수). 정직: 매수/목표주가·인과 금지, 개인주주 익명, 근사 명기, null '·' 분리.
	import type { Company, Lang } from '../lib/types';
	import type { InvestmentPeriod, InvestmentRow, InvestmentTrendYear, ShareholderKind, ShareholdersView } from '@dartlab/ui-contracts';
	import { buildHoldingsModel, buildNetworkLayout, mutualCodes, type ListedLookup, type HoldingTier, type HoldingsRow, type NetNode } from '../lib/holdings';
	import { fmtKRW } from '../lib/engine';

	interface Props {
		co: Company;
		year: string;
		rows: InvestmentRow[];
		trend: InvestmentTrendYear[];
		periods: InvestmentPeriod[]; // forward 시계열 (year,quarter)
		shareholders: ShareholdersView | null; // 최신기 (timeline 비었을 때 fallback)
		shPeriods: ShareholdersView[]; // reverse 시계열
		lang: Lang;
		lookupListed: ListedLookup;
		onPick: (code: string) => void;
		onClose: () => void;
	}
	let { co, year, rows, periods, shareholders, shPeriods, lang, lookupListed, onPick, onClose }: Props = $props();
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);

	// 본체 재무 주입(원) · 시총 = mktcapRaw, 순익 = 시총/PER 근사(둘 다 원). PER null·≤0 → parentNet=null → contribShare 생략.
	const parentMktcap = $derived(co.price.mktcapRaw ?? null);
	const parentNet = $derived(co.fundamentals.per && co.fundamentals.per > 0 && co.price.mktcapRaw ? co.price.mktcapRaw / co.fundamentals.per : null);

	// ── 기간 시계열 (연도/분기) · 관계망·표 탭이 공유하는 단일 기간 컨트롤 ──
	const qr = (q: string) => (q === '4분기' ? 4 : q === '3분기' ? 3 : q === '2분기' ? 2 : 1);
	let gran = $state<'year' | 'quarter'>('year');
	let periodIdx = $state(-1); // -1 = 최신(기본). selIdx 에서 보정
	let playing = $state(false);
	interface TLEntry { year: string; quarter: string; label: string; fwdRows: InvestmentRow[]; sh: ShareholdersView | null; }
	const timeline = $derived.by<TLEntry[]>(() => {
		// 타법인 출자(forward)가 주체 · forward 보고 기간만 타임라인. 1·3분기 보고서는 출자 상세가 비어(invValid 필터로 제외)
		// periods 에 애초에 없으므로 빈 기간이 끼지 않는다. reverse(주주)는 같은 (year,quarter) exact → 없으면 같은 연도 best quarter 매칭.
		const revAt = (year: string, quarter: string): ShareholdersView | null => {
			const exact = shPeriods.find((s) => s.year === year && s.quarter === quarter);
			if (exact) return exact;
			return shPeriods.filter((s) => s.year === year).sort((a, b) => qr(b.quarter) - qr(a.quarter))[0] ?? null;
		};
		if (gran === 'quarter') {
			return periods
				.map((p) => ({ year: p.year, quarter: p.quarter, label: p.year + ' ' + p.quarter.replace('분기', 'Q'), fwdRows: p.rows, sh: revAt(p.year, p.quarter) }))
				.sort((a, b) => a.year.localeCompare(b.year) || qr(a.quarter) - qr(b.quarter));
		}
		const years = [...new Set(periods.map((p) => p.year))];
		return years
			.map((y) => {
				const f = periods.filter((p) => p.year === y).sort((a, b) => qr(b.quarter) - qr(a.quarter))[0];
				return { year: y, quarter: f.quarter, label: y, fwdRows: f.rows, sh: revAt(y, f.quarter) };
			})
			.sort((a, b) => a.year.localeCompare(b.year));
	});
	const selIdx = $derived(timeline.length ? (periodIdx < 0 || periodIdx >= timeline.length ? timeline.length - 1 : periodIdx) : -1);
	const sel = $derived(selIdx >= 0 ? timeline[selIdx] : null);
	const isLatest = $derived(selIdx === timeline.length - 1); // 시가 채널은 최신기만(현재가 기반)
	const selRows = $derived(timeline.length ? (sel?.fwdRows ?? []) : rows);
	const selSh = $derived(timeline.length ? (sel?.sh ?? null) : shareholders);

	const m = $derived(buildHoldingsModel(sel?.label ?? year, selRows, lookupListed, isLatest ? parentMktcap : null, isLatest ? parentNet : null, isLatest));
	// 회사 전환 시 기간/재생 리셋
	$effect(() => { void co.code; periodIdx = -1; playing = false; });
	const togglePlay = () => {
		if (playing) { playing = false; return; }
		if (selIdx >= timeline.length - 1) periodIdx = 0; // 끝이면 처음(과거)부터
		playing = true;
	};
	// 재생 · 기간 자동 스텝(끝에서 정지). effect 본문 tracked read 는 playing/timeline 뿐(periodIdx 는 콜백 내부라 매 스텝 effect 재실행 안 함).
	$effect(() => {
		if (!playing || timeline.length === 0) return;
		const id = setInterval(() => {
			const cur = periodIdx < 0 ? timeline.length - 1 : periodIdx;
			if (cur >= timeline.length - 1) { playing = false; return; }
			periodIdx = cur + 1;
		}, 900);
		return () => clearInterval(id);
	});

	const TIER_LABEL: Record<HoldingTier, { kr: string; en: string; cls: string }> = {
		consolidated: { kr: '연결', en: 'CONS', cls: 'tUp' },
		equity: { kr: '지분법', en: 'EQ', cls: 'tGood' },
		simple: { kr: '단순', en: 'SIMPLE', cls: 'tNeu' },
		unknown: { kr: '분류불가', en: 'n/a', cls: 'tNeu' }
	};
	const KIND_LABEL: Record<ShareholderKind, { kr: string; en: string }> = {
		institution: { kr: '기관', en: 'inst' },
		corp: { kr: '법인', en: 'corp' },
		gov: { kr: '정부·연기금', en: 'gov' },
		treasury: { kr: '자기주식', en: 'treasury' },
		person: { kr: '개인', en: 'person' }
	};
	// 주주 유형 색 · reverse 노드(상장/이익기여 무관, 유형으로 구분).
	const HOLDER_COLOR: Record<ShareholderKind, string> = {
		institution: '#8b5cf6',
		corp: '#5b9bf0',
		gov: '#10b981',
		treasury: '#6b7280',
		person: '#9ca3af'
	};
	const krw = (v: number | null) => (v == null ? '·' : fmtKRW(v));
	// 표 금액 컬럼 · 억원 고정 단위(컬럼 내 단위 통일 → 행 간 비교 가능). 10억 미만 1자리·이상 정수+콤마, 부호 보존. (fmtKRW 의 조/억/원 적응 표기는 컬럼에서 섞여 비교 불가)
	const eok = (v: number | null) => {
		if (v == null) return '·';
		const a = Math.abs(v) / 1e8;
		const s = a < 10 ? a.toLocaleString('en-US', { maximumFractionDigits: 1 }) : Math.round(a).toLocaleString('en-US');
		return (v < 0 ? '-' : '') + s;
	};
	const ratioCls = (r: number | null, mid = 1) => (r == null ? 'tNeu' : r > mid ? 'tUp' : r < mid ? 'tDn' : 'tNeu');
	// 이익기여 부호 색 (forward) · 흑자 녹/적자 적/미상 회.
	const signColor = (v: number | null) => (v == null ? 'var(--dim)' : v > 0 ? 'var(--up)' : v < 0 ? 'var(--dn)' : 'var(--dim)');
	const clip = (s: string, n = 8) => {
		const c = (s || '').replace(/\(주\)|㈜|주식회사/g, '').trim();
		return c.length > n ? c.slice(0, n - 1) + '…' : c;
	};
	const maxEarn = $derived(Math.max(...m.rows.map((r) => Math.abs(r.equityEarn ?? 0)), 1));
	// 적자 자회사 장부가 비중 · "딱 보고 아는 한 문장"(판정 아닌 사실 기술). 단일 SSOT = holdings.ts(헤더·다이얼로그 공용, G4).
	const lossBook = $derived(m.lossBook);
	const lossPct = $derived(m.lossPct);

	// reverse 법인·기관 주주 · 상장 해소(클릭 이동용). 개인은 익명 집계라 named 에 없음.
	const reverseNamed = $derived(
		(selSh?.named ?? []).map((sh) => {
			if (sh.kind === 'corp' || sh.kind === 'institution') {
				const lk = lookupListed(sh.name);
				if (lk) return { ...sh, code: lk.code };
			}
			return sh;
		})
	);

	let tab = $state<'net' | 'table'>('net');
	let helpOpen = $state(false);
	let mapW = $state(0);
	let mapH = $state(0);
	let hoverName = $state<string | null>(null);
	let hx = $state(0);
	let hy = $state(0);
	// 그래프 탭은 본문을 가득 채운다(탭 분리 → 스크롤 제거 → 그래프 확대 → 회사명 상시 라벨 수용). 높이는 캔버스 실측, 미측정 시 460.
	const NET_H = $derived(mapH || 460);
	const layout = $derived(mapW ? buildNetworkLayout(m.rows, m.maxBook, reverseNamed, selSh?.person ?? null, mapW, NET_H) : null);
	// 상호출자(2-cycle) · 선택 기간에서 forward∩reverse 종목코드 교집합(상장 상호보유만). 노드 배지 + 닫힌 고리 커넥터.
	const mutual = $derived(mutualCodes(m.rows, reverseNamed));
	const mutualLinks = $derived.by(() => {
		if (!layout || !mutual.size) return [] as { code: string; x1: number; y1: number; x2: number; y2: number; cx: number; cy: number }[];
		const fwd = new Map<string, NetNode>();
		const rev = new Map<string, NetNode>();
		for (const n of layout.nodes) {
			if (n.kind === 'forward' && n.h?.code) fwd.set(n.h.code, n);
			else if (n.kind === 'reverseNamed' && n.sh?.code) rev.set(n.sh.code, n);
		}
		const out: { code: string; x1: number; y1: number; x2: number; y2: number; cx: number; cy: number }[] = [];
		for (const code of mutual) {
			const f = fwd.get(code);
			const r = rev.get(code);
			if (!f || !r) continue;
			const avg = (f.x + r.x) / 2;
			const side = avg < mapW / 2 ? -1 : 1; // 가까운 바깥쪽으로 볼록(닫힌 고리)
			out.push({ code, x1: r.x, y1: r.y, x2: f.x, y2: f.y, cx: Math.max(14, Math.min(mapW - 14, avg + side * 80)), cy: (r.y + f.y) / 2 });
		}
		return out;
	});
	// 호버 툴팁 · 상시 라벨 대신 회사명 + 기본정보. hoverName 으로 forward/reverse 노드 데이터 조회.
	const hoverFwd = $derived(hoverName ? (m.rows.find((h) => h.name === hoverName) ?? null) : null);
	const hoverRev = $derived(hoverName && !hoverFwd ? (reverseNamed.find((s) => s.name === hoverName) ?? null) : null);

	$effect(() => {
		const onKey = (e: KeyboardEvent) => {
			if (e.key === 'Escape') onClose();
		};
		window.addEventListener('keydown', onKey);
		return () => window.removeEventListener('keydown', onKey);
	});
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<div class="scrModal hdModal" role="dialog" aria-modal="true" aria-label={T('출자 관계', 'holdings relationship')} onclick={(e) => e.stopPropagation()}>
		<div class="scrHead">
			<span class="scrTitle">{T('출자 관계', 'HOLDINGS · relationship')} · {co.name.kr} · {m.year}</span>
			<span class="hdSub dim">{T('피출자사', 'holdings')} {m.rows.length}{T('개', '')}{#if selSh} · {T('주주', 'holders')} {reverseNamed.length + (selSh.person ? 1 : 0)}{/if}</span>
			<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
		</div>

		<div class="hdBody">
			<!-- 3축 요약: 성격·위계 / 가치(상장지분 시가) / 효율(이익기여) -->
			<div class="hdSummary">
				<div class="hdSumCard">
					<div class="hdSumLbl">{T('성격 · 위계', 'TIER')}</div>
					<div class="hdTierRow">
						{#if m.counts.consolidated}<span class="hdTier tUp">{T('연결', 'cons')} {m.counts.consolidated}</span>{/if}
						{#if m.counts.equity}<span class="hdTier tGood">{T('지분법', 'eq')} {m.counts.equity}</span>{/if}
						{#if m.counts.simple}<span class="hdTier tNeu">{T('단순', 'simple')} {m.counts.simple}</span>{/if}
						{#if m.counts.unknown}<span class="hdTier tNeu">{T('분류불가', 'n/a')} {m.counts.unknown}</span>{/if}
					</div>
					<div class="hdSumSub dim">{T('상장', 'listed')} {m.counts.listed} · {T('비상장', 'unlisted')} {m.counts.unlisted}{m.counts.loss ? ' · ' + T('적자피출자', 'loss') + ' ' + m.counts.loss : ''}</div>
				</div>
				<div class="hdSumCard">
					<div class="hdSumLbl">{T('가치 · 상장 보유지분 시가', 'VALUE · listed stake')}</div>
					<div class="hdSumV mono">{isLatest ? krw(m.listedStakeSum) : '·'}</div>
					<div class="hdSumSub dim">{isLatest ? (m.pctOfParentCap != null ? T('본체 시총 대비 ', 'of parent cap ') + m.pctOfParentCap.toFixed(1) + '%' : T('본체 시총 대비 · (미산출)', 'parent cap n/a')) : T('현재가 기반 · 최신기만', 'current price · latest only')}</div>
				</div>
				<div class="hdSumCard">
					<div class="hdSumLbl">{T('효율 · 지분법 이익기여(근사)', 'EFFICIENCY · equity earnings (approx)')}</div>
					<div class={'hdSumV mono ' + (m.sumEquityEarn > 0 ? 'tUp' : m.sumEquityEarn < 0 ? 'tDn' : 'tNeu')}>{krw(m.sumEquityEarn)}</div>
					<div class="hdSumSub dim">{m.contribShare != null ? T('본체 순익 대비 ', 'of parent net ') + m.contribShare.toFixed(1) + '%' : T('본체 순익 대비 · (참고·미산출)', 'parent net n/a')}</div>
				</div>
			</div>

			{#if timeline.length > 1}
				<!-- 공통 기간 컨트롤 · 관계망·표 탭 공유. 연도(각 연도 사업보고서 우선)/분기(보고된 것만) 토글 + 칩. -->
				<div class="hdPeriodBar">
					<button class={'hdPlay ' + (playing ? 'on' : '')} onclick={togglePlay} aria-label={T('재생 · 기간 자동 변화', 'play · auto-step periods')} title={T('재생 · 기간 자동 변화', 'play · auto-step periods')}>{playing ? '⏸' : '▶'}</button>
					<span class="hdGran">
						<button class={'hdGranBtn ' + (gran === 'year' ? 'on' : '')} onclick={() => (gran = 'year')}>{T('연도', 'Year')}</button>
						<button class={'hdGranBtn ' + (gran === 'quarter' ? 'on' : '')} onclick={() => (gran = 'quarter')}>{T('분기', 'Qtr')}</button>
					</span>
					<span class="hdChips">
						{#each timeline as t, i (t.label)}
							<button class={'hdChip ' + (i === selIdx ? 'on' : '')} onclick={() => (periodIdx = i)}>{t.label}</button>
						{/each}
					</span>
					{#if !isLatest}<span class="hdPbNote dim">{T('과거 · 출자 구조 변화(시가 아님)', 'past · structure change, not market value')}</span>{/if}
				</div>
			{/if}

			<nav class="hdTabs" aria-label={T('관계망/표 전환', 'network/table')}>
				<button class={'hdTab ' + (tab === 'net' ? 'on' : '')} onclick={() => (tab = 'net')}>{T('관계망', 'NETWORK')}</button>
				<button class={'hdTab ' + (tab === 'table' ? 'on' : '')} onclick={() => (tab = 'table')}>{T('표', 'TABLE')} <span class="hdTabN">{m.rows.length}{#if selSh} · {reverseNamed.length + (selSh.person ? 1 : 0)}{/if}</span></button>
			</nav>

			{#if tab === 'net'}
			<!-- 양방향 관계망 · 위=주주(누가 나를 소유)·중앙=본체·아래=자회사(tier 레인). 노드 호버 → 툴팁. 회사명 상시 라벨. -->
			<div class="hdMapSec hdPane">
				<div class="hdMapTitle">
					<span class="hdMapH">{T('관계망', 'Network')}</span>
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<span class="hdHelp" tabindex="0" role="button" aria-label={T('읽는 법 · 데이터 품질', 'how to read · data quality')} onmouseenter={() => (helpOpen = true)} onmouseleave={() => (helpOpen = false)} onfocus={() => (helpOpen = true)} onblur={() => (helpOpen = false)}>!</span>
					{#if lossPct != null && lossBook > 0}<span class="hdTake tDn">{T('적자 피출자', 'loss-making')} {krw(lossBook)} ({lossPct.toFixed(0)}%)</span>{/if}
					{#if m.pctOfParentCap != null}<span class="hdTake dim">{T('상장지분 = 본체 시총', 'listed stake = parent cap')} {m.pctOfParentCap.toFixed(1)}%</span>{/if}
					{#if helpOpen}
						<div class="hdHelpPop">
							<div class="hdHelpH">{T('뭘 봐야 하나', 'What to look at')}</div>
							<ul>
								<li>{T('위 = 나를 소유한 주주 · 중앙 = 본체 · 아래 = 내가 출자한 회사', 'top = holders · center = this company · bottom = investees')}</li>
								<li>{T('아래 레인 = 회계 관계: 연결(지분 ≥50%) · 지분법(20~50%) · 단순(<20%)', 'lanes = consolidated (≥50%) · equity (20-50%) · simple (<20%)')}</li>
								<li>{T('노드 크기 = 장부가 · 색 = 이익기여 흑자(녹)/적자(적) · ★ = 경영참여', 'size = book value · color = profit(green)/loss(red) · ★ = mgmt intent')}</li>
								<li>{T('굵은 테두리 = 시가>장부(숨은가치)·시가<장부(잠재손상) · 실선 노드 = 상장(클릭 → 종목 이동)', 'thick border = mkt vs book gap · solid node = listed (click to open)')}</li>
								<li>{T('엣지 굵기 = 지분율 · ↔ = 상호출자(서로 지분 보유, 상장 상호보유만)', 'edge width = stake % · ↔ = cross-holding (mutual, listed only)')}</li>
							</ul>
							<div class="hdHelpH">{T('데이터 품질 · 한계', 'Data quality · limits')}</div>
							<ul>
								<li>{T('이익기여 = 지분법 근사 (내부거래·공정가치 미반영)', 'equity earnings are an approximation')}</li>
								<li>{T('시가지분 = 상장 해소 피출자사만 · 비상장은 장부가만', 'market stake covers listed investees only')}</li>
								<li>{T('피출자 순익 = 최근 1기 단일값 · 본체 순익 연결/별도 미구분(참고)', 'target net = latest single period only')}</li>
								<li>{T('개인주주 익명 집계 · 미해소·null 은 0 대체 없이 분리', 'individuals aggregated · nulls kept separate')}</li>
								<li>{T('과거 기간 = 출자 구조 변화(시가 아님) · 분기 = 보고된 것만', 'past periods = structure change (not market value) · quarters = reported only')}</li>
							<li>{T('상호출자는 상장 상호보유만 · 다단계 순환(A→B→C→A)은 미지원', 'cross-holding = listed mutual only · multi-hop cycles unsupported')}</li>
															</ul>
						</div>
					{/if}
				</div>
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div class="hdNetCanvas" bind:clientWidth={mapW} bind:clientHeight={mapH} role="presentation" onmousemove={(e) => { hx = e.clientX; hy = e.clientY; }}>
					{#if layout}
						<svg width={mapW} height={NET_H} role="img" aria-label={T('출자 관계망', 'holdings network')}>
							<!-- 레인 구분선 + 라벨 (forward tier) -->
							{#each layout.lanes as L (L.tier)}
								<line x1="6" y1={L.y} x2={mapW - 6} y2={L.y} stroke="var(--bd)" stroke-width="1" stroke-dasharray="2 5" opacity="0.4" />
								<text class="hdLaneLab" x="8" y={L.cy} dominant-baseline="middle">{T(TIER_LABEL[L.tier].kr, TIER_LABEL[L.tier].en)}<tspan class="hdLaneSub"> {L.count}{T('사', '')} · {krw(L.book)}</tspan></text>
							{/each}
							<!-- 엣지 (주주→본체 위, 본체→자회사 아래) -->
							{#each layout.edges as e (e.key)}
								<line x1={e.x1} y1={e.y1} x2={e.x2} y2={e.y2} stroke={(hoverName && layout.nodes.some((n) => (n.h?.name === hoverName || n.sh?.name === hoverName) && (n.x === e.x2 || n.x === e.x1))) ? 'var(--amber)' : e.up ? '#8b5cf6' : 'var(--dim)'} stroke-width={e.w} stroke-opacity={hoverName ? 0.12 : e.up ? 0.4 : 0.28} stroke-dasharray={e.dashed ? '2 2' : 'none'} />
							{/each}
							<!-- 상호출자 닫힌 고리 · 위(주주) 인스턴스 ↔ 아래(피출자) 인스턴스 곡선 연결 -->
							{#each mutualLinks as ml (ml.code)}
								<path d={`M ${ml.x1} ${ml.y1} Q ${ml.cx} ${ml.cy} ${ml.x2} ${ml.y2}`} fill="none" stroke="var(--amber)" stroke-width="1.6" stroke-opacity={hoverName ? 0.2 : 0.6} stroke-dasharray="4 3" />
							{/each}
							<!-- 노드 -->
							{#each layout.nodes as n (n.key)}
								{#if n.kind === 'forward' && n.h}
									{@const h = n.h}
									{@const dim = hoverName && hoverName !== h.name}
									{@const tt = h.name + ' · ' + (h.stakePct != null ? h.stakePct.toFixed(1) + '%' : '·') + ' · ' + T('장부', 'book') + ' ' + krw(h.bookValue) + (h.marketStake != null ? ' · ' + T('시가', 'mkt') + ' ' + krw(h.marketStake) + (h.gapRatio != null ? '(' + h.gapRatio.toFixed(1) + '×)' : '') : '') + (h.equityEarn != null ? ' · ' + T('이익기여', 'earn') + ' ' + (h.equityEarn < 0 ? '-' : '') + fmtKRW(Math.abs(h.equityEarn)) : '') + (h.purpose ? ' · ' + h.purpose : '')}
									{#if h.code}
										<g class="hdNode click" role="button" tabindex={0} aria-label={h.name} onmouseenter={() => (hoverName = h.name)} onmouseleave={() => (hoverName = null)} onclick={() => onPick(h.code!)} onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick(h.code!); } }}>
											<circle cx={n.x} cy={n.y} r={n.r} fill={signColor(h.equityEarn)} fill-opacity={dim ? 0.25 : 0.9} stroke={hoverName === h.name ? 'var(--amber)' : h.gapRatio != null && h.gapRatio > 1.15 ? 'var(--up)' : h.gapRatio != null && h.gapRatio < 0.85 ? 'var(--dn)' : 'rgba(255,255,255,0.6)'} stroke-width={hoverName === h.name || (h.gapRatio != null && (h.gapRatio > 1.15 || h.gapRatio < 0.85)) ? 2.4 : 1.2} />
											{#if h.intent}<circle cx={n.x + n.r * 0.66} cy={n.y - n.r * 0.66} r="2.4" fill="var(--amber)" />{/if}
											{#if h.code && mutual.has(h.code)}<text class="hdMutual" x={n.x - n.r * 0.7} y={n.y - n.r * 0.4} text-anchor="middle">↔</text>{/if}
											<title>{tt}</title>
										</g>
									{:else}
										<!-- svelte-ignore a11y_no_static_element_interactions -->
										<g class="hdNode" role="img" aria-label={h.name} onmouseenter={() => (hoverName = h.name)} onmouseleave={() => (hoverName = null)}>
											<circle cx={n.x} cy={n.y} r={n.r} fill={signColor(h.equityEarn)} fill-opacity={dim ? 0.2 : 0.7} stroke={hoverName === h.name ? 'var(--amber)' : 'var(--bd)'} stroke-width={hoverName === h.name ? 2.4 : 1} stroke-dasharray="2 2" />
											{#if h.intent}<circle cx={n.x + n.r * 0.66} cy={n.y - n.r * 0.66} r="2.4" fill="var(--amber)" />{/if}
											<title>{tt}</title>
										</g>
									{/if}
									<text class={'hdNodeLab' + (hoverName === h.name ? ' hl' : '')} x={n.x} y={n.y + n.r + 12} text-anchor="middle">{clip(h.name, 11)}</text>
										{#if h.stakePct != null}<text class="hdNodeSub" x={n.x} y={n.y + n.r + 22} text-anchor="middle">{h.stakePct.toFixed(1)}%</text>{/if}
								{:else if n.kind === 'reverseNamed' && n.sh}
									{@const sh = n.sh}
									{@const dim = hoverName && hoverName !== sh.name}
									{@const tt = sh.name + ' · ' + KIND_LABEL[sh.kind][lang === 'en' ? 'en' : 'kr'] + (sh.relate ? ' · ' + sh.relate : '') + ' · ' + (sh.ratio != null ? sh.ratio.toFixed(2) + '%' : '·')}
									{#if n.code}
										<g class="hdNode click" role="button" tabindex={0} aria-label={sh.name} onmouseenter={() => (hoverName = sh.name)} onmouseleave={() => (hoverName = null)} onclick={() => onPick(n.code!)} onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onPick(n.code!); } }}>
											<rect x={n.x - n.r} y={n.y - n.r} width={n.r * 2} height={n.r * 2} rx="3" fill={HOLDER_COLOR[sh.kind]} fill-opacity={dim ? 0.25 : 0.9} stroke={hoverName === sh.name ? 'var(--amber)' : 'rgba(255,255,255,0.6)'} stroke-width={hoverName === sh.name ? 2.4 : 1.2} />
											{#if n.code && mutual.has(n.code)}<text class="hdMutual" x={n.x + n.r * 0.7} y={n.y - n.r * 0.45} text-anchor="middle">↔</text>{/if}
											<title>{tt}</title>
										</g>
									{:else}
										<!-- svelte-ignore a11y_no_static_element_interactions -->
										<g class="hdNode" role="img" aria-label={sh.name} onmouseenter={() => (hoverName = sh.name)} onmouseleave={() => (hoverName = null)}>
											<rect x={n.x - n.r} y={n.y - n.r} width={n.r * 2} height={n.r * 2} rx="3" fill={HOLDER_COLOR[sh.kind]} fill-opacity={dim ? 0.2 : 0.85} stroke={hoverName === sh.name ? 'var(--amber)' : 'var(--bd)'} stroke-width={hoverName === sh.name ? 2.4 : 1} />
											<title>{tt}</title>
										</g>
									{/if}
									<text class={'hdNodeLab' + (hoverName === sh.name ? ' hl' : '')} x={n.x} y={n.y - n.r - 16} text-anchor="middle">{clip(sh.name, 11)}</text>
										{#if sh.ratio != null}<text class="hdNodeSub" x={n.x} y={n.y - n.r - 6} text-anchor="middle">{sh.ratio.toFixed(1)}%</text>{/if}
								{:else if n.kind === 'reversePerson' && n.person}
									<!-- svelte-ignore a11y_no_static_element_interactions -->
									<g class="hdNode" role="img" aria-label={T('특수관계인 개인', 'individuals')}>
										<rect x={n.x - n.r} y={n.y - n.r} width={n.r * 2} height={n.r * 2} transform={`rotate(45 ${n.x} ${n.y})`} fill={HOLDER_COLOR.person} fill-opacity="0.7" stroke="var(--bd)" stroke-width="1" />
										<title>{T('특수관계인 개인', 'related individuals')} {n.person.count}{T('인', '')} · {n.person.ratio != null ? n.person.ratio.toFixed(2) + '%' : '·'} ({T('익명 집계', 'aggregated')})</title>
									</g>
									<text class="hdNodeLab" x={n.x} y={n.y - n.r - 16} text-anchor="middle">{T('개인', 'person')} {n.person.count}{T('인', '')}</text>
						{#if n.person.ratio != null}<text class="hdNodeSub" x={n.x} y={n.y - n.r - 6} text-anchor="middle">{n.person.ratio.toFixed(1)}%</text>{/if}
								{/if}
							{/each}
							<!-- 집계 캡슐 (tier 초과분) -->
							{#each layout.capsules as c (c.tier)}
								<g class="hdNode">
									<rect x={c.x} y={c.y - 13} width="58" height="26" rx="4" fill="var(--panel)" stroke="var(--bd)" stroke-width="1" stroke-dasharray="2 2" />
									<text class="hdCapLab" x={c.x + 29} y={c.y - 2} text-anchor="middle">+{c.count}{T('사', '')}</text>
									<text class="hdCapSub" x={c.x + 29} y={c.y + 8} text-anchor="middle">{krw(c.book)}</text>
								</g>
							{/each}
							<!-- 중앙 본체 -->
							<circle cx={layout.focal.x} cy={layout.focal.y} r={layout.focal.r} fill="var(--panel)" stroke="var(--amber)" stroke-width="2.5" />
							<text class="hdFocalLab" x={layout.focal.x} y={layout.focal.y + 3} text-anchor="middle">{clip(co.name.kr, 7)}</text>
						</svg>
					{/if}
					{#if hoverFwd || hoverRev}
						<div class="hdTip" style:left={`${hx + 14}px`} style:top={`${hy + 12}px`}>
							{#if hoverFwd}
								<b>{hoverFwd.name}</b>
								<div class="hdTipR"><span>{T('성격', 'tier')}</span><span>{T(TIER_LABEL[hoverFwd.tier].kr, TIER_LABEL[hoverFwd.tier].en)}{hoverFwd.intent ? ' · ' + T('경영참여', 'intent') : ''}</span></div>
								<div class="hdTipR"><span>{T('지분', 'stake')}</span><span class="mono">{hoverFwd.stakePct != null ? hoverFwd.stakePct.toFixed(1) + '%' : '·'}</span></div>
								<div class="hdTipR"><span>{T('장부가', 'book')}</span><span class="mono">{krw(hoverFwd.bookValue)}</span></div>
								{#if hoverFwd.marketStake != null}<div class="hdTipR"><span>{T('시가지분', 'mkt')}</span><span class="mono">{krw(hoverFwd.marketStake)}{hoverFwd.gapRatio != null ? ` (${hoverFwd.gapRatio.toFixed(1)}×)` : ''}</span></div>{/if}
								<div class="hdTipR"><span>{T('피출자순익', 'net')}</span><span class="mono">{hoverFwd.targetNet != null ? (hoverFwd.targetNet < 0 ? '-' : '') + fmtKRW(Math.abs(hoverFwd.targetNet)) : '·'}</span></div>
								<div class="hdTipR"><span>{T('이익기여', 'earn')}</span><span class="mono">{hoverFwd.equityEarn != null ? (hoverFwd.equityEarn < 0 ? '-' : '') + fmtKRW(Math.abs(hoverFwd.equityEarn)) : '·'}</span></div>
								{#if hoverFwd.code}<div class="hdTipGo">{T('클릭 → 종목 이동', 'click → open')}</div>{/if}
							{:else if hoverRev}
								<b>{hoverRev.name}</b>
								<div class="hdTipR"><span>{T('유형', 'kind')}</span><span>{T(KIND_LABEL[hoverRev.kind].kr, KIND_LABEL[hoverRev.kind].en)}</span></div>
								{#if hoverRev.relate}<div class="hdTipR"><span>{T('관계', 'relate')}</span><span>{hoverRev.relate}</span></div>{/if}
								<div class="hdTipR"><span>{T('지분', 'stake')}</span><span class="mono">{hoverRev.ratio != null ? hoverRev.ratio.toFixed(2) + '%' : '·'}</span></div>
								{#if hoverRev.code}<div class="hdTipGo">{T('클릭 → 종목 이동', 'click → open')}</div>{/if}
							{/if}
						</div>
					{/if}
				</div>
				<div class="hdLegend dim">
					<span><i class="lg" style:background="var(--up)"></i>{T('흑자', 'profit')}</span>
					<span><i class="lg" style:background="var(--dn)"></i>{T('적자', 'loss')}</span>
					<span><i class="lg sq" style:background="#8b5cf6"></i>{T('기관', 'inst')}</span>
					<span><i class="lg sq" style:background="#5b9bf0"></i>{T('법인', 'corp')}</span>
					<span><i class="lg dia"></i>{T('개인(익명)', 'person')}</span>
					<span>{T('★=경영참여 · 굵은 테두리=시가/장부 괴리', '★=intent · thick border=mkt/book gap')}</span>
					{#if mutual.size}<span><i class="lg" style:background="var(--amber)"></i>{T('↔ 상호출자(상장 상호보유)', '↔ cross-holding (listed)')}</span>{/if}
				</div>
				{#if !selSh}<div class="hdMapNote dim">{T('이 기간 주주 데이터 없음 · 위쪽(소유 구조) 생략.', 'No holder data for this period · upstream omitted.')}</div>{/if}
			</div>
			{:else}
			<div class="hdPane hdTablePane">
			<!-- forward 출자 표 (정밀 수치) -->
			<div class="hdScroll">
				<table class="finTable hdTable">
					<thead>
						<tr>
							<th class="finAcct">{T('피출자사', 'INVESTEE')}</th>
							<th>{T('성격', 'TIER')}</th>
							<th class="r">{T('지분', 'STAKE')}</th>
							<th class="r">{T('장부가(억)', 'BOOK(억)')}</th>
							<th class="r">{T('시가지분(억)', 'MKT(억)')}</th>
							<th class="r" title={T('시가/장부 (>1 숨은가치, <1 잠재손상) · 상장만', 'market/book')}>{T('시가/장부', 'M/B')}</th>
							<th class="r" title={T('장부/취득 (>1 평가이익 누적, <1 손상가능)', 'book/cost')}>{T('장부/취득', 'B/C')}</th>
							<th class="r">{T('피출자순익(억)', 'TGT NET(억)')}</th>
							<th class="r" title={T('지분법 이익기여 근사 (지분% × 피출자순익)', 'equity earnings approx')}>{T('이익기여(억)', 'EQ EARN(억)')}</th>
							<th class="r" title={T('이익기여/장부가', 'eq earn / book')}>{T('투자ROIC', 'iROIC')}</th>
						</tr>
					</thead>
					<tbody>
						{#each m.rows as h, i (h.name + '#' + i)}
							<tr class={(h.tier === 'consolidated' ? 'finKey ' : '') + (hoverName === h.name ? 'hlRow' : '')}>
								<td class="finAcct" title={h.purpose}>
									{#if h.code}
										<button type="button" class="hdLink" onclick={() => onPick(h.code!)}>{h.name}</button>
									{:else}{h.name}{/if}
									{#if h.intent}<span class="hdIntent" title={T('경영참여 의사', 'management intent')}>{T('경영참여', 'intent')}</span>{/if}
								</td>
								<td><span class={'hdTierMini ' + TIER_LABEL[h.tier].cls}>{T(TIER_LABEL[h.tier].kr, TIER_LABEL[h.tier].en)}</span></td>
								<td class="r mono">{h.stakePct != null ? h.stakePct.toFixed(1) + '%' : '·'}</td>
								<td class="r mono">{eok(h.bookValue)}</td>
								<td class="r mono">{eok(h.marketStake)}</td>
								<td class={'r mono ' + ratioCls(h.gapRatio)}>{h.gapRatio != null ? h.gapRatio.toFixed(2) + '×' : '·'}</td>
								<td class={'r mono ' + ratioCls(h.markRatio)}>{h.markRatio != null ? h.markRatio.toFixed(2) + '×' : '·'}</td>
								<td class={'r mono ' + (h.targetNet != null && h.targetNet < 0 ? 'tDn' : '')}>{eok(h.targetNet)}</td>
								<td class={'r mono ' + (h.equityEarn != null && h.equityEarn < 0 ? 'tDn' : h.equityEarn != null && h.equityEarn > 0 ? 'tUp' : '')}>{eok(h.equityEarn)}</td>
								<td class={'r mono ' + (h.investROIC != null ? (h.investROIC > 0 ? 'tUp' : h.investROIC < 0 ? 'tDn' : 'tNeu') : 'tNeu')}>{h.investROIC != null ? (h.investROIC * 100).toFixed(1) + '%' : '·'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>

			<!-- reverse 최대주주 표 (누가 이 회사를 소유) · 개인 익명 집계 -->
			{#if selSh && (reverseNamed.length || selSh.person)}
				<div class="hdScroll hdOwners">
					<div class="hdOwnTitle dim">{T('최대주주 · 누가 이 회사를 소유하나', 'OWNERS · who owns this company')} · {sel?.label ?? selSh.year}{#if selSh.totalPct != null} · {T('합산', 'total')} {selSh.totalPct.toFixed(1)}%{/if}</div>
					<table class="finTable hdTable">
						<thead>
							<tr><th class="finAcct">{T('주주', 'HOLDER')}</th><th>{T('유형', 'KIND')}</th><th>{T('관계', 'RELATE')}</th><th class="r">{T('지분', 'STAKE')}</th><th class="r">{T('주식수', 'SHARES')}</th></tr>
						</thead>
						<tbody>
							{#each reverseNamed as h (h.name)}
								<tr class={(h.kind === 'corp' && (h.ratio ?? 0) >= 30 ? 'finKey ' : '') + (hoverName === h.name ? 'hlRow' : '')}>
									<td class="finAcct">{#if h.code}<button type="button" class="hdLink" onclick={() => onPick(h.code!)}>{h.name}</button>{:else}{h.name}{/if}</td>
									<td><span class="hdTierMini">{T(KIND_LABEL[h.kind].kr, KIND_LABEL[h.kind].en)}</span></td>
									<td class="dim">{h.relate || '·'}</td>
									<td class="r mono">{h.ratio != null ? h.ratio.toFixed(2) + '%' : '·'}</td>
									<td class="r mono">{h.shares != null ? h.shares.toLocaleString('en-US') : '·'}</td>
								</tr>
							{/each}
							{#if selSh.person}
								<tr>
									<td class="finAcct dim">{T('특수관계인 개인', 'related individuals')} {selSh.person.count}{T('인', '')}</td>
									<td><span class="hdTierMini">{T('개인', 'person')}</span></td>
									<td class="dim">{T('익명 집계', 'aggregated')}</td>
									<td class="r mono">{selSh.person.ratio != null ? selSh.person.ratio.toFixed(2) + '%' : '·'}</td>
									<td class="r mono">{selSh.person.shares != null ? selSh.person.shares.toLocaleString('en-US') : '·'}</td>
								</tr>
							{/if}
						</tbody>
					</table>
				</div>
			{/if}

			</div>
			{/if}

			<div class="hdNote dim">
				{T(
					'report · 타법인 출자현황 + 최대주주현황. 이익기여=지분법 근사(내부거래·공정가치 미반영), 시가지분=상장 해소 피출자사만, 피출자 순익=최근 1기. 개인주주는 개인정보 보호로 익명 집계. 미해소·null 은 0 대체 없이 분리.',
					'report · holdings + major holders. Equity earnings are approximate; market stake covers listed only; target net is latest period. Individual holders are aggregated for privacy. Nulls not coerced to zero. Not a verdict or price target.'
				)}
			</div>
		</div>
	</div>
</div>

<style>
	.hdModal {
		width: min(1240px, 96vw);
		height: 90vh;
		display: flex;
		flex-direction: column;
	}
	.hdSub {
		font-size: 10px;
		margin-left: auto;
		margin-right: 10px;
	}
	.hdBody {
		flex: 1;
		min-height: 0;
		display: flex;
		flex-direction: column;
		overflow: hidden;
		padding: 10px 12px 12px;
	}
	.hdSummary {
		flex: none;
		display: grid;
		grid-template-columns: repeat(3, 1fr);
		gap: 8px;
		margin-bottom: 10px;
	}
	/* 탭 · 관계망(그래프) / 표 전환. 스크롤 대신 분리해 그래프 탭이 본문을 가득 채운다. */
	.hdTabs {
		flex: none;
		display: flex;
		gap: 2px;
		border-bottom: 1px solid var(--bd);
		margin-bottom: 8px;
	}
	.hdTab {
		background: none;
		border: 1px solid transparent;
		border-bottom: none;
		border-radius: 3px 3px 0 0;
		color: var(--dim);
		font-family: var(--cond, inherit);
		font-size: 12px;
		font-weight: 600;
		letter-spacing: 0.3px;
		padding: 5px 14px;
		cursor: pointer;
		margin-bottom: -1px;
	}
	.hdTab:hover {
		color: var(--txt);
	}
	.hdTab.on {
		color: var(--amber);
		border-color: var(--bd);
		border-bottom-color: var(--dl-bg-raised, #0e141f);
		background: rgba(245, 158, 11, 0.06);
	}
	.hdTabN {
		font-size: 9.5px;
		color: var(--dimmer, #6b7280);
		font-weight: 400;
	}
	/* 공통 기간 컨트롤 · 관계망·표 공유. 연/분기 토글 + 기간 칩(+ P3 재생). */
	.hdPeriodBar {
		flex: none;
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 6px 10px;
		margin-bottom: 8px;
	}
	.hdGran {
		display: inline-flex;
		gap: 2px;
	}
	.hdGranBtn {
		background: none;
		border: 1px solid var(--bd);
		border-radius: 3px;
		color: var(--dim);
		font-family: var(--cond, inherit);
		font-size: 10px;
		font-weight: 600;
		padding: 2px 8px;
		cursor: pointer;
	}
	.hdGranBtn.on {
		color: var(--amber);
		border-color: var(--amber);
		background: rgba(245, 158, 11, 0.08);
	}
	.hdChips {
		display: inline-flex;
		flex-wrap: wrap;
		gap: 3px;
	}
	.hdChip {
		background: none;
		border: 1px solid var(--bd);
		border-radius: 3px;
		color: var(--dim);
		font-family: var(--mono);
		font-size: 10px;
		padding: 2px 7px;
		cursor: pointer;
	}
	.hdChip:hover {
		color: var(--txt);
	}
	.hdChip.on {
		color: var(--amber);
		border-color: var(--amber);
		background: rgba(245, 158, 11, 0.1);
		font-weight: 700;
	}
	.hdPbNote {
		font-size: 9px;
	}
	.hdPlay {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 22px;
		height: 20px;
		border: 1px solid var(--bd);
		border-radius: 3px;
		background: none;
		color: var(--dim);
		font-size: 10px;
		line-height: 1;
		cursor: pointer;
	}
	.hdPlay:hover,
	.hdPlay.on {
		color: var(--amber);
		border-color: var(--amber);
		background: rgba(245, 158, 11, 0.08);
	}
	.hdPane {
		flex: 1;
		min-height: 0;
	}
	.hdTablePane {
		overflow-y: auto;
	}
	.hdSumCard {
		border: 1px solid var(--bd);
		border-radius: 3px;
		padding: 7px 9px;
		background: var(--dl-bg-base, rgba(255, 255, 255, 0.02));
	}
	.hdSumLbl {
		font-size: 9px;
		color: var(--dim);
		letter-spacing: 0.4px;
		text-transform: uppercase;
		margin-bottom: 4px;
	}
	.hdSumV {
		font-size: 15px;
		font-weight: 700;
	}
	.hdSumSub {
		font-size: 9.5px;
		margin-top: 2px;
	}
	.hdTierRow {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
	}
	.hdTier {
		font-size: 11px;
		font-weight: 700;
		border: 1px solid currentColor;
		border-radius: 2px;
		padding: 1px 5px;
	}
	.hdMapSec {
		display: flex;
		flex-direction: column;
		min-height: 0;
	}
	.hdMapTitle {
		flex: none;
		position: relative;
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 8px;
		font-size: 9px;
		margin-bottom: 6px;
		line-height: 1.35;
	}
	.hdMapH {
		font-size: 11.5px;
		font-weight: 700;
		color: var(--txt);
		letter-spacing: 0.3px;
	}
	.hdHelp {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: 15px;
		height: 15px;
		border-radius: 50%;
		border: 1px solid var(--bd);
		color: var(--dim);
		font-size: 10px;
		font-weight: 700;
		line-height: 1;
		cursor: help;
	}
	.hdHelp:hover,
	.hdHelp:focus {
		color: var(--amber);
		border-color: var(--amber);
		outline: none;
	}
	.hdTake {
		font-size: 9.5px;
	}
	.hdHelpPop {
		position: absolute;
		top: 21px;
		left: 0;
		z-index: 330;
		width: min(460px, 92vw);
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 5px;
		padding: 9px 12px 8px;
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.55);
		line-height: 1.5;
	}
	.hdHelpH {
		font-size: 9px;
		font-weight: 700;
		color: var(--amber);
		letter-spacing: 0.4px;
		text-transform: uppercase;
		margin: 6px 0 3px;
	}
	.hdHelpH:first-child {
		margin-top: 0;
	}
	.hdHelpPop ul {
		margin: 0;
		padding-left: 15px;
	}
	.hdHelpPop li {
		font-size: 9.5px;
		color: var(--txt);
		margin: 1.5px 0;
	}
	.hdNetCanvas {
		flex: 1;
		min-height: 0;
		background: var(--dl-bg-base, rgba(255, 255, 255, 0.02));
		border: 1px solid var(--bd);
		border-radius: 3px;
		padding: 0;
	}
	.hdNetCanvas svg {
		display: block;
	}
	.hdNode.click {
		cursor: pointer;
	}
	.hdNode circle,
	.hdNode rect {
		/* 기간 전환·재생 시 노드가 미끄러지듯 이동(Chromium: cx/cy/r/x/y 트랜지션; 미지원 브라우저는 snap · 기능 동일). physics 0. */
		transition: fill-opacity 0.12s, cx 0.5s ease, cy 0.5s ease, r 0.5s ease, x 0.5s ease, y 0.5s ease, width 0.5s ease, height 0.5s ease;
	}
	.hdNetCanvas line {
		transition: x1 0.5s ease, y1 0.5s ease, x2 0.5s ease, y2 0.5s ease;
	}
	.hdNodeLab,
	.hdNodeSub {
		transition: x 0.45s ease, y 0.45s ease;
	}
	.hdLaneLab {
		font-size: 10px;
		font-weight: 700;
		fill: var(--txt);
		pointer-events: none;
	}
	.hdLaneSub {
		font-weight: 400;
		fill: var(--dimmer, #6b7280);
		font-size: 8.5px;
	}
	.hdNodeLab {
		font-size: 8.5px;
		fill: var(--txt);
		paint-order: stroke;
		stroke: var(--dl-bg-base, #05070d);
		stroke-width: 2.5px;
		pointer-events: none;
	}
	.hdNodeLab.hl {
		fill: var(--amber, var(--amber));
		font-weight: 700;
	}
	.hdNodeSub {
		font-size: 7.5px;
		fill: var(--dimmer, #6b7280);
		font-family: var(--mono);
		paint-order: stroke;
		stroke: var(--dl-bg-base, #05070d);
		stroke-width: 2px;
		pointer-events: none;
	}
	.hdMutual {
		font-size: 11px;
		font-weight: 700;
		fill: var(--amber);
		paint-order: stroke;
		stroke: var(--dl-bg-base, #05070d);
		stroke-width: 2px;
		pointer-events: none;
	}
	.hdFocalLab {
		font-size: 10px;
		font-weight: 700;
		fill: var(--txt);
		paint-order: stroke;
		stroke: var(--panel);
		stroke-width: 2px;
		pointer-events: none;
	}
	.hdCapLab {
		font-size: 9px;
		font-weight: 700;
		fill: var(--dim);
		pointer-events: none;
	}
	.hdCapSub {
		font-size: 7.5px;
		fill: var(--dimmer, #6b7280);
		font-family: var(--mono);
		pointer-events: none;
	}
	.hdLegend {
		flex: none;
		display: flex;
		flex-wrap: wrap;
		gap: 4px 12px;
		font-size: 8.5px;
		margin-top: 6px;
	}
	.hdLegend span {
		display: inline-flex;
		align-items: center;
		gap: 3px;
	}
	.hdLegend .lg {
		width: 9px;
		height: 9px;
		border-radius: 50%;
		display: inline-block;
	}
	.hdLegend .lg.sq {
		border-radius: 2px;
	}
	.hdLegend .lg.dia {
		width: 8px;
		height: 8px;
		background: #9ca3af;
		transform: rotate(45deg);
	}
	.hdMapNote {
		flex: none;
		font-size: 9px;
		margin-top: 5px;
		line-height: 1.4;
	}
	.hdScroll {
		overflow-x: auto;
	}
	.hdOwners {
		margin-top: 10px;
	}
	.hdOwnTitle {
		font-size: 9px;
		margin-bottom: 4px;
	}
	.hdTable {
		width: 100%;
		font-size: 11px;
	}
	.hdLink {
		background: none;
		border: none;
		color: var(--accent, #5b9bf0);
		cursor: pointer;
		padding: 0;
		font: inherit;
		text-align: left;
	}
	.hdLink:hover {
		text-decoration: underline;
	}
	.hdIntent {
		font-size: 8px;
		color: var(--amber, var(--amber));
		border: 1px solid rgba(var(--amber-rgb), 0.4);
		border-radius: 2px;
		padding: 0 3px;
		margin-left: 5px;
		vertical-align: 1px;
	}
	.hdTierMini {
		font-size: 9.5px;
		font-weight: 700;
	}
	.hdNote {
		flex: none;
		font-size: 9px;
		line-height: 1.5;
		margin-top: 8px;
		padding-top: 6px;
		border-top: 1px solid var(--bd);
	}
	.hdTable tbody tr.hlRow {
		background: rgba(var(--amber-rgb), 0.13);
	}
	.hdTip {
		position: fixed;
		z-index: 320;
		pointer-events: none;
		background: var(--dl-bg-raised, #0e141f);
		border: 1px solid var(--dl-line-strong, #2a3142);
		border-radius: 4px;
		padding: 7px 9px;
		font-size: 10px;
		color: var(--txt);
		box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
		min-width: 162px;
		max-width: 244px;
	}
	.hdTip b {
		font-size: 11px;
		display: block;
		margin-bottom: 4px;
	}
	.hdTipR {
		display: flex;
		justify-content: space-between;
		gap: 12px;
		line-height: 1.55;
	}
	.hdTipR span:first-child {
		color: var(--dim);
	}
	.hdTipGo {
		margin-top: 4px;
		font-size: 9px;
		color: var(--amber);
	}
	.hdTip .mono {
		font-family: var(--mono);
	}
</style>
