<script lang="ts">
	// table-export 선택 바구니 드로어 · AskDrawer 와 같은 우측 380px 슬롯(상호배타). 선택한 표들을 시트 목록으로
	// 보여주고, 시트명 인라인 편집(31자)·모드 토글(수평/원본)·드래그 정렬·기간 표시·제거를 제공한다.
	// [내보내기] = deriveWorkbookInput → buildWorkbook → 진짜 .xlsx 바이트 → downloadBlob. 빈 선택은 안내(크래시 0).
	import { GripVertical, X, Download, FileSpreadsheet } from 'lucide-svelte';
	import { buildWorkbook } from '../lib/xlsx';
	import { downloadBlob } from '../lib/dataExport';
	import { deriveWorkbookInput, trimLabel, type SelectionStore, type SheetSelection } from '../lib/export/selection.svelte';
	import type { PanelBundle } from '../lib/types';

	let {
		store,
		bundle,
		corpName,
		basePath = '',
		tier = 'public',
		onclose
	}: {
		store: SelectionStore;
		bundle: PanelBundle | null;
		corpName: string;
		basePath?: string;
		tier?: 'public' | 'local'; // 03 §7 · public 은 [설치 ↗] hint, local 은 완전판(hint 없음). 숨기지 않고 라벨만.
		onclose: () => void;
	} = $props();

	const LABEL_MAX = 31;
	const XLSX_MIME = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';

	// order 순 선택 목록 (드래그 정렬 반영).
	const list = $derived(store.ordered());

	// 라이브 카운트 · 시트 수(출처 포함 시 +1) + 회사·시점 요약. 빈 선택 시 0.
	const sheetCount = $derived(list.length + (store.includeSource && list.length ? 1 : 0));
	const periodSummary = $derived.by(() => {
		const ps = new Set<string>();
		for (const s of list) {
			if (s.periods === 'all') {
				for (const p of bundle?.periods ?? []) ps.add(p);
			} else {
				for (const p of s.periods) ps.add(p);
			}
		}
		if (ps.size === 0) return '';
		const sorted = [...ps].sort((a, b) => (a < b ? 1 : a > b ? -1 : 0));
		return sorted.length === 1 ? sorted[0] : `${sorted[0]}~${sorted[sorted.length - 1]}`;
	});

	let exporting = $state(false);
	let exportErr = $state<string | null>(null);

	function doExport() {
		exportErr = null;
		if (!bundle || list.length === 0) return;
		exporting = true;
		try {
			const sheets = deriveWorkbookInput(list, bundle, store.includeSource);
			if (sheets.length === 0) {
				exportErr = '선택한 표에서 내보낼 데이터를 찾지 못했습니다.';
				return;
			}
			const bytes = buildWorkbook(sheets);
			const safe = (corpName || bundle.stockCode).replace(/[\\/:*?"<>|]/g, '_');
			downloadBlob(bytes, `${safe}_공시표.xlsx`, XLSX_MIME);
			// 선택 유지(연속 내보내기) · PRD §5. 닫지 않는다.
		} catch (e) {
			exportErr = e instanceof Error ? e.message : String(e);
		} finally {
			exporting = false;
		}
	}

	// 시트명 인라인 편집 · contenteditable 대신 input(IME·커서 안정). 31자 트림 + 카운터 빨강 경고.
	function onLabelInput(s: SheetSelection, e: Event) {
		const el = e.currentTarget as HTMLInputElement;
		const trimmed = trimLabel(el.value);
		if (trimmed !== el.value) el.value = trimmed; // 31자 초과 입력 즉시 자름
		store.setLabel(s.id, trimmed);
	}

	// ── 드래그 정렬 · HTML5 DnD, 핸들 그립으로만 시작. dragover 시 그 항목 위로 재배치. ──
	let dragId = $state<string | null>(null);
	function onDragStart(id: string, e: DragEvent) {
		dragId = id;
		if (e.dataTransfer) {
			e.dataTransfer.effectAllowed = 'move';
			e.dataTransfer.setData('text/plain', id); // Firefox 는 데이터 필요
		}
	}
	function onDragOver(id: string, e: DragEvent) {
		if (!dragId || dragId === id) return;
		e.preventDefault();
		if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
	}
	function onDrop(id: string, e: DragEvent) {
		e.preventDefault();
		if (dragId && dragId !== id) store.reorder(dragId, id);
		dragId = null;
	}
	function onDragEnd() {
		dragId = null;
	}

	function periodLabel(s: SheetSelection): string {
		if (s.periods === 'all') {
			const ps = bundle?.periods ?? [];
			return ps.length ? `${ps[0]}~${ps[ps.length - 1]} · 전 기간` : '전 기간';
		}
		return s.periods.join(' · ');
	}
</script>

<aside class="export-drawer">
	<header class="ed-head">
		<FileSpreadsheet size={17} color="var(--dl-accent)" />
		<strong>표 내보내기</strong>
		<span class="ed-count">{list.length}개</span>
		<button type="button" class="ed-x" onclick={onclose} aria-label="닫기"><X size={15} /></button>
	</header>

	<div class="ed-scroll">
		{#if list.length === 0}
			<div class="onboard">
				<picture>
					<source srcset="{basePath}/avatar-study.webp" type="image/webp" />
					<img class="ob-ava" src="{basePath}/avatar-study.png" alt="" width="64" height="64" />
				</picture>
				<p class="ob-title">내보낼 표를 고르세요</p>
				<p class="ob-sub">격자에서 표 셀의 좌상단 <b>체크박스</b>를 누르면 여기에 시트로 담깁니다. 시트명·순서·모드(수평/원본)를 바꿔 진짜 엑셀(.xlsx)로 받습니다.</p>
			</div>
		{:else}
			<ul class="sheet-list">
				{#each list as s (s.id)}
					<li
						class="sheet"
						class:dragging={dragId === s.id}
						role="listitem"
						ondragover={(e) => onDragOver(s.id, e)}
						ondrop={(e) => onDrop(s.id, e)}
					>
						<div class="sh-row1">
							<span
								class="grip"
								role="button"
								tabindex="-1"
								aria-label="드래그로 순서 변경"
								title="드래그로 순서 변경"
								draggable="true"
								ondragstart={(e) => onDragStart(s.id, e)}
								ondragend={onDragEnd}
							>
								<GripVertical size={14} />
							</span>
							<input
								class="sh-name"
								class:warn={[...s.label].length >= LABEL_MAX}
								value={s.label}
								maxlength={LABEL_MAX}
								spellcheck="false"
								aria-label="시트명"
								oninput={(e) => onLabelInput(s, e)}
							/>
							<span class="sh-counter" class:warn={[...s.label].length >= LABEL_MAX}>{[...s.label].length}/{LABEL_MAX}</span>
							<button type="button" class="sh-x" title="이 표 빼기" onclick={() => store.remove(s.id)}><X size={13} /></button>
						</div>
						<div class="sh-row2">
							<div class="mode-toggle" role="radiogroup" aria-label="내보내기 구조">
								<button
									type="button"
									class="mode-opt"
									class:on={s.mode === 'horizontalized'}
									role="radio"
									aria-checked={s.mode === 'horizontalized'}
									title="전 기간을 가로로 · 행=항목, 열=시점(텍스트 블록만, 표는 원본 폴백)"
									onclick={() => store.setMode(s.id, 'horizontalized')}
								>{s.mode === 'horizontalized' ? '◉' : '○'} 수평</button>
								<button
									type="button"
									class="mode-opt"
									class:on={s.mode === 'asFiled'}
									role="radio"
									aria-checked={s.mode === 'asFiled'}
									title="원본 표 구조 그대로(병합셀 보존)"
									onclick={() => store.setMode(s.id, 'asFiled')}
								>{s.mode === 'asFiled' ? '◉' : '○'} 원본</button>
							</div>
							<span class="period-chip" title="포함 시점">{periodLabel(s)}</span>
						</div>
					</li>
				{/each}
			</ul>
		{/if}
	</div>

	<footer class="ed-foot">
		<button
			type="button"
			class="opt-row"
			class:on={store.includeSource}
			onclick={() => (store.includeSource = !store.includeSource)}
			title="어떤 회사·시점·섹션을 어떤 모드로 뽑았는지 기록한 '출처' 시트를 1장 추가합니다."
		>
			<span class="cb">{store.includeSource ? '☑' : '☐'}</span> 출처 시트 포함
		</button>

		{#if exportErr}<p class="ed-err">{exportErr}</p>{/if}

		<div class="ed-action">
			<button type="button" class="export-btn" disabled={list.length === 0 || exporting} onclick={doExport}>
				<Download size={15} /> 내보내기
			</button>
			<span class="live-count">
				{#if list.length === 0}
					표를 선택하세요
				{:else}
					{sheetCount}시트{periodSummary ? ` · ${periodSummary}` : ''}
				{/if}
			</span>
		</div>
		{#if tier === 'local'}
			<p class="ed-note">엔진 완전판 .xlsx · 자동너비·음수 빨강·풍부한 서식</p>
		{:else}
			<p class="ed-note ed-tier">
				이 브라우저 내보내기 = 빠른 .xlsx · 서버 전송 0. 자동너비·음수 빨강·풍부한 서식의 완전판은 로컬 터미널 dartlab.
				<a class="ed-install" href="https://eddmpython.github.io/dartlab" target="_blank" rel="noopener">설치 ↗</a>
			</p>
		{/if}
	</footer>
</aside>

<style>
	.export-drawer {
		min-width: 0;
		min-height: 0;
		height: 100%;
		display: flex;
		flex-direction: column;
		border-left: 1px solid #1e2433;
		background: #070b14;
		animation: edslide 0.18s ease-out;
	}
	@keyframes edslide {
		from {
			transform: translateX(24px);
			opacity: 0.4;
		}
		to {
			transform: translateX(0);
			opacity: 1;
		}
	}
	.ed-head {
		display: flex;
		align-items: center;
		gap: 8px;
		padding: 10px 12px;
		border-bottom: 1px solid #1e2433;
		flex-shrink: 0;
	}
	.ed-head strong {
		font-size: 13px;
		color: #f1f5f9;
		font-weight: 800;
	}
	.ed-count {
		padding: 1px 8px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		background: #050811;
		color: #94a3b8;
		font-size: 10px;
		font-weight: 600;
	}
	.ed-x {
		margin-left: auto;
		display: grid;
		place-items: center;
		width: 26px;
		height: 26px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: transparent;
		color: #94a3b8;
		cursor: pointer;
	}
	.ed-x:hover {
		border-color: rgba(var(--amber-rgb), 0.5);
		color: var(--amber);
	}

	.ed-scroll {
		flex: 1 1 auto;
		min-height: 0;
		overflow-y: auto;
		padding: 10px;
	}

	/* 빈 안내 · 격자 체크박스 유도 */
	.onboard {
		margin: auto;
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 10px;
		text-align: center;
		padding: 28px 14px;
	}
	.ob-ava {
		border-radius: 50%;
		opacity: 0.95;
	}
	.ob-title {
		margin: 0;
		font-size: 13px;
		font-weight: 700;
		color: #e2e8f0;
	}
	.ob-sub {
		margin: 0;
		font-size: 11.5px;
		line-height: 1.6;
		color: #94a3b8;
	}
	.ob-sub b {
		color: var(--dl-accent-light);
	}

	.sheet-list {
		list-style: none;
		margin: 0;
		padding: 0;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.sheet {
		border: 1px solid #1e2433;
		border-radius: 8px;
		background: #0a0e18;
		padding: 8px 9px;
		display: flex;
		flex-direction: column;
		gap: 7px;
	}
	.sheet.dragging {
		opacity: 0.5;
		border-color: rgba(var(--amber-rgb), 0.5);
	}
	.sh-row1 {
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.grip {
		display: inline-flex;
		align-items: center;
		color: #475569;
		cursor: grab;
		flex-shrink: 0;
	}
	.grip:active {
		cursor: grabbing;
	}
	.grip:hover {
		color: #94a3b8;
	}
	.sh-name {
		flex: 1 1 auto;
		min-width: 0;
		padding: 4px 7px;
		border: 1px solid #263145;
		border-radius: 5px;
		background: #050811;
		color: #f1f5f9;
		font: inherit;
		font-size: 12px;
		outline: none;
	}
	.sh-name:focus {
		border-color: var(--amber);
	}
	.sh-name.warn {
		border-color: rgba(248, 113, 113, 0.6);
	}
	.sh-counter {
		flex-shrink: 0;
		font-size: 9.5px;
		color: #475569;
		font-variant-numeric: tabular-nums;
	}
	.sh-counter.warn {
		color: #f87171;
	}
	.sh-x {
		flex-shrink: 0;
		display: grid;
		place-items: center;
		width: 22px;
		height: 22px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: transparent;
		color: #64748b;
		cursor: pointer;
	}
	.sh-x:hover {
		border-color: rgba(248, 113, 113, 0.5);
		color: #f87171;
	}
	.sh-row2 {
		display: flex;
		align-items: center;
		gap: 8px;
		flex-wrap: wrap;
		padding-left: 20px; /* grip 폭만큼 들여 라벨과 정렬 */
	}
	.mode-toggle {
		display: inline-flex;
		gap: 2px;
		padding: 2px;
		border: 1px solid #1e2433;
		border-radius: 6px;
		background: #050811;
	}
	.mode-opt {
		padding: 3px 8px;
		border: none;
		border-radius: 4px;
		background: transparent;
		color: #94a3b8;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
		white-space: nowrap;
	}
	.mode-opt:hover {
		color: #cbd5e1;
	}
	.mode-opt.on {
		background: rgba(var(--amber-rgb), 0.14);
		color: var(--amber);
		font-weight: 600;
	}
	.period-chip {
		max-width: 100%;
		padding: 2px 8px;
		border: 1px solid #1e2433;
		border-radius: 999px;
		background: #050811;
		color: #94a3b8;
		font-size: 10px;
		font-family: monospace;
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
	}

	.ed-foot {
		flex-shrink: 0;
		border-top: 1px solid #1e2433;
		padding: 10px 12px;
		display: flex;
		flex-direction: column;
		gap: 8px;
	}
	.opt-row {
		align-self: flex-start;
		padding: 2px 4px;
		border: none;
		background: transparent;
		color: #94a3b8;
		font: inherit;
		font-size: 11.5px;
		cursor: pointer;
	}
	.opt-row:hover {
		color: #cbd5e1;
	}
	.opt-row.on {
		color: #34d399;
	}
	.opt-row .cb {
		font-size: 12px;
	}
	.ed-err {
		margin: 0;
		color: #f87171;
		font-size: 11px;
		line-height: 1.5;
	}
	.ed-action {
		display: flex;
		align-items: center;
		gap: 10px;
	}
	.export-btn {
		display: inline-flex;
		align-items: center;
		gap: 7px;
		padding: 9px 16px;
		border: none;
		border-radius: 8px;
		background: var(--amber);
		color: #1a1206;
		font: inherit;
		font-size: 13px;
		font-weight: 700;
		cursor: pointer;
	}
	.export-btn:hover:not(:disabled) {
		background: var(--dl-accent-light);
	}
	.export-btn:disabled {
		opacity: 0.45;
		cursor: default;
	}
	.live-count {
		font-size: 11px;
		color: #94a3b8;
		font-variant-numeric: tabular-nums;
	}
	.ed-note {
		margin: 0;
		font-size: 10px;
		color: #475569;
		line-height: 1.4;
	}
	.ed-tier {
		color: #64748b;
		line-height: 1.5;
	}
	.ed-install {
		color: var(--amber);
		text-decoration: none;
		font-weight: 600;
		white-space: nowrap;
	}
	.ed-install:hover {
		text-decoration: underline;
	}

	/* 모바일 · 드로어가 부모(+page @media)에서 전체화면 오버레이. 터치 타깃 확대. */
	@media (max-width: 880px) {
		.ed-x {
			width: 40px;
			height: 40px;
		}
		.export-btn {
			min-height: 48px;
		}
		.sh-x {
			width: 32px;
			height: 32px;
		}
	}
</style>
