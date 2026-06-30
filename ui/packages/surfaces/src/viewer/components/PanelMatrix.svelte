<script lang="ts">
	// 수평화 매트릭스 · 행=panel 항목, 열=period. landing 디자인 언어(다크 네이비 + 오렌지).
	import CellContent from './CellContent.svelte';
	import { hasVisibleContent } from '../lib/diff';
	import type { PanelRow } from '../lib/types';

	let {
		rows,
		periods,
		dartUrlByPeriod,
		glow = null,
		highlight = null,
		selecting = false,
		rowIds = [],
		selectedIds = null,
		onToggleCell
	}: {
		rows: PanelRow[];
		periods: string[];
		dartUrlByPeriod: Record<string, string | null>;
		glow?: { rowIndex: number; period: string } | null;
		highlight?: { rowIndex: number; period: string; terms: string[] } | null;
		// ── table-export 선택 모드 ── selecting=true 면 셀 좌상단 체크박스 오버레이(레이아웃 시프트 0).
		// rowIds[i] = 표시 행 i 의 섹션 절대 selection id (ViewerStudio 가 환산해 주입). selectedIds 에 있으면 steady glow.
		selecting?: boolean;
		rowIds?: string[]; // visible 매핑 전 원본 rows 인덱스 기준 · 부모가 rows 와 같은 순서로 제공
		selectedIds?: Set<string> | null;
		onToggleCell?: (rowId: string, row: PanelRow, period: string) => void;
	} = $props();

	// 섹션 내 build-order 인덱스 보존 · 행 식별(disclosureKey/NARR)은 leafSeq 미포함이라 EDGAR 동명 narrative
	// 행이 충돌(each_key_duplicate). 별개 행이므로 둘 다 표시하되 DOM 키는 안정·유일한 원본 인덱스로.
	const visible = $derived(rows.map((r, i) => ({ r, i })).filter(({ r }) => hasVisibleContent(r, periods)));
	// 항목 라벨 열 없음 · 셀 본문(표 제목 내장)이 자기 식별. 격자는 기간 열만.
	const template = $derived(`repeat(${periods.length}, minmax(260px, 1fr))`);
	const minMatrixWidth = $derived(`${periods.length * 260}px`);

	// 검색 점프 셀 글로우 · 표시 수명을 여기서 소유한다(부모 타이머 아님). 옛 방식은 glow 설정 즉시 2.2s
	// fade 애니메이션 + 클리어 타이머가 돌아, 먼 거리 smooth 스크롤이 끝나기 전에 강조가 꺼졌다. 이제:
	// ① 섹션 변경 렌더 후(2프레임) 셀을 찾아 스크롤(없으면 재시도) ② 스크롤 도착(scrollend, 없으면 fallback)
	// 후 dwell 동안 *steady 펄스* 강조 유지 → 도착 시점에 확실히 보인다.
	const GLOW_DWELL = 2600;
	let glowKey = $state<string | null>(null);
	$effect(() => {
		const g = glow;
		if (!g) {
			glowKey = null;
			return;
		}
		const sel = `[data-cell="${g.rowIndex}|${g.period}"]`;
		let disposed = false;
		let dwell: ReturnType<typeof setTimeout> | undefined;
		let fallback: ReturnType<typeof setTimeout> | undefined;
		let scroller: (Element | Window) | null = null;
		const startDwell = () => {
			if (disposed) return;
			if (fallback) clearTimeout(fallback);
			if (scroller) scroller.removeEventListener('scrollend', startDwell as EventListener);
			dwell = setTimeout(() => {
				if (!disposed) glowKey = null;
			}, GLOW_DWELL);
		};
		const begin = (tries: number) => {
			if (disposed) return;
			const el = document.querySelector(sel);
			if (!el) {
				if (tries > 0) requestAnimationFrame(() => begin(tries - 1));
				return;
			}
			glowKey = `${g.rowIndex}|${g.period}`; // 표시 시작(steady)
			el.scrollIntoView({ block: 'center', inline: 'center', behavior: 'smooth' });
			scroller = el.closest('.matrix-scroll') ?? window;
			scroller.addEventListener('scrollend', startDwell as EventListener, { once: true });
			fallback = setTimeout(startDwell, 1400); // scrollend 미지원/미발생 대비 · 도착 후 dwell 보장
		};
		requestAnimationFrame(() => requestAnimationFrame(() => begin(8)));
		return () => {
			disposed = true;
			if (dwell) clearTimeout(dwell);
			if (fallback) clearTimeout(fallback);
			if (scroller) scroller.removeEventListener('scrollend', startDwell as EventListener);
		};
	});
</script>

{#if periods.length === 0}
	<div class="empty">기간을 선택하세요.</div>
{:else if visible.length === 0}
	<div class="empty">선택한 기간에는 이 절의 본문이 없습니다.</div>
{:else}
	<div class="matrix-scroll">
		<div class="matrix" style="grid-template-columns: {template}; min-width: max(100%, {minMatrixWidth})">
			<!-- 헤더 -->
			{#each periods as p (p)}
				<div class="cell head period-head">
					<span class="period">{p}</span>
					{#if dartUrlByPeriod[p]}
						<a class="src-link" href={dartUrlByPeriod[p]} target="_blank" rel="noreferrer noopener" title={`${p} 시점 원본 공시`}>
							원본 ↗
						</a>
					{/if}
				</div>
			{/each}

			<!-- 본문 -->
			{#each visible as { r, i } (i)}
				{@const rid = rowIds[i] ?? null}
				{@const picked = !!(rid && selectedIds?.has(rid))}
				{#each periods as p (p)}
					<div
						class="cell body-cell"
						class:glow={glowKey === `${i}|${p}`}
						class:picked={selecting && picked}
						data-cell={`${i}|${p}`}
					>
						{#if selecting && rid}
							<button
								type="button"
								class="pick-box"
								class:on={picked}
								aria-pressed={picked}
								title={picked ? '선택 해제' : '이 표를 내보내기에 추가'}
								onclick={() => onToggleCell?.(rid, r, p)}
							>
								{#if picked}✓{/if}
							</button>
						{/if}
						<CellContent value={r.cells?.[p] ?? ''} highlightTerms={highlight && highlight.rowIndex === i && highlight.period === p ? highlight.terms : []} />
					</div>
				{/each}
			{/each}
		</div>
	</div>
{/if}

<style>
	.empty {
		padding: 24px;
		text-align: center;
		font-size: 12px;
		color: #64748b;
	}
	.matrix-scroll {
		height: 100%;
		overflow: auto;
	}
	.matrix {
		display: grid;
		align-items: stretch;
		width: 100%;
	}
	.cell {
		border-bottom: 1px solid #1e2433;
		padding: 8px 10px;
		min-width: 0;
	}
	.head {
		position: sticky;
		top: 0;
		z-index: 20;
		background: #0a0e18;
		border-bottom: 1px solid #263145;
	}
	.period-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 8px;
	}
	.period {
		font-family: monospace;
		font-size: 12px;
		font-weight: 700;
		color: #f1f5f9;
	}
	.src-link {
		flex-shrink: 0;
		display: inline-flex;
		align-items: center;
		gap: 4px;
		padding: 2px 7px;
		border: 1px solid #263145;
		border-radius: 4px;
		font-size: 10px;
		color: #94a3b8;
		text-decoration: none;
		white-space: nowrap;
	}
	.src-link:hover {
		border-color: rgba(var(--amber-rgb), 0.6);
		color: var(--amber);
	}
	.body-cell {
		position: relative; /* pick-box 오버레이 앵커 (체크박스 absolute, 레이아웃 시프트 0). */
		color: #cbd5e1;
	}
	/* steady 강조 + 펄스 · 스크롤 도착 시점에 확실히 보이게(옛 t0 fade 레이스 제거). 수명은 JS(glowKey)가 제어. */
	.body-cell.glow {
		box-shadow: inset 0 0 0 2px var(--amber);
		animation: cellglow 1.1s ease-in-out infinite;
	}
	/* table-export 선택 · steady 보더(펄스 없음, glow 와 구분). 선택 유지 상시. */
	.body-cell.picked {
		box-shadow: inset 0 0 0 2px var(--amber);
		background: rgba(var(--amber-rgb), 0.08);
	}
	/* 셀 좌상단 체크박스 · fade-in, position:absolute(격자 레이아웃 시프트 0). */
	.pick-box {
		position: absolute;
		top: 5px;
		left: 5px;
		z-index: 10;
		display: grid;
		place-items: center;
		width: 20px;
		height: 20px;
		padding: 0;
		border: 1px solid #475569;
		border-radius: 4px;
		background: rgba(5, 8, 17, 0.82);
		color: var(--amber);
		font-size: 12px;
		font-weight: 700;
		line-height: 1;
		cursor: pointer;
		animation: pickfade 0.16s ease-out;
	}
	.pick-box:hover {
		border-color: var(--amber);
	}
	.pick-box.on {
		border-color: var(--amber);
		background: rgba(var(--amber-rgb), 0.9);
		color: #1a1206;
	}
	@keyframes pickfade {
		from {
			opacity: 0;
			transform: scale(0.85);
		}
		to {
			opacity: 1;
			transform: scale(1);
		}
	}
	@keyframes cellglow {
		0%,
		100% {
			background: rgba(var(--amber-rgb), 0.1);
		}
		50% {
			background: rgba(var(--amber-rgb), 0.24);
		}
	}

	/* D3 · 모바일 격자 가독성. 데스크톱(≥881px)은 inline style 의 repeat(N, minmax(260px,1fr)) 그대로(불변).
	   모바일에선 부모(+page)가 cols=1 로 강제해 periods.length=1 → 격자가 자연히 단일 컬럼(DOM 순서상 head→body
	   정렬 유지). 여기선 셀 패딩만 모바일용으로 키워 손가락·가독 여백 확보(가로스크롤 0, 풀폭 셀). 기간 전환은 리본. */
	@media (max-width: 880px) {
		.cell {
			padding: 10px 12px;
		}
	}
</style>
