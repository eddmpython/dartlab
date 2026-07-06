<script lang="ts">
	// 공시뷰어 데이터 다운로드 · 보고 있는 회사 panel·재무 parquet 직접 받기 + 전체 데이터셋(공개 HF).
	// ViewerStudio 에서 추출(자족 feature). hover 팝오버라 트리거 버튼(.fs-btn)+팝오버를 한 단위로 보유.
	import { Download } from 'lucide-svelte';
	import type { PanelBundle } from '../lib/types';
	import { hfUrl } from '@dartlab/ui-runtime/data/parquet/hfRange';
	import { marketForCode } from '../lib/dartUrl';
	import { panelToCsv, financeToExcel, downloadText } from '../lib/dataExport';
	import { loadFinanceStatement } from '../lib/finance/financeQuery';
	import { KIND_LABELS, type FinanceKind, type FinanceStatement } from '../lib/finance/types';

	interface Props {
		code: string;
		bundle: PanelBundle | null;
		corpName: string;
	}
	let { code, bundle, corpName }: Props = $props();

	const dlMarket = $derived(marketForCode(code));
	const panelDlUrl = $derived(hfUrl(`${dlMarket === 'US' ? 'edgar' : 'dart'}/panel/${code}.parquet`));
	const financeDlUrl = $derived(hfUrl(`dart/finance/${code}.parquet`));
	const DATASET_URL = 'https://huggingface.co/datasets/eddmpython/dartlab-data';

	// 일반인용 다운로드 · 브라우저에 로드된 데이터를 CSV/Excel 로(서버 0). 공시 수평화표=CSV, 재무제표=Excel(멀티시트).
	let financeDownloading = $state(false);
	function downloadPanelCsv() {
		if (bundle) downloadText(panelToCsv(bundle), `${corpName || code}_공시수평화.csv`, 'text/csv;charset=utf-8');
	}
	async function downloadFinanceExcel() {
		if (financeDownloading) return;
		financeDownloading = true;
		try {
			const sheets: Array<{ name: string; statement: FinanceStatement }> = [];
			for (const k of ['IS', 'BS', 'CF', 'CIS'] as FinanceKind[]) {
				const st = await loadFinanceStatement(code, dlMarket, k, 'annual', 'CFS');
				if (st && st.rows.length) sheets.push({ name: KIND_LABELS[k], statement: st });
			}
			if (sheets.length) downloadText(financeToExcel(sheets), `${corpName || code}_재무제표_연간연결.xls`, 'application/vnd.ms-excel');
		} finally {
			financeDownloading = false;
		}
	}
</script>

			<div class="data-dl">
				<button type="button" class="fs-btn"><Download size={13} /> 데이터</button>
				<div class="data-pop">
					<div class="dp-h">이 회사 데이터 · 공개 다운로드</div>
					<div class="dp-sub">보기 쉬운 형식 · Excel · Sheets · 메모장</div>
					<button type="button" class="dp-link dp-btn" onclick={downloadPanelCsv} disabled={!bundle}>공시 수평화표 <span class="dp-ext">CSV</span></button>
					{#if dlMarket !== 'US'}
						<button type="button" class="dp-link dp-btn" onclick={downloadFinanceExcel} disabled={financeDownloading}>재무제표 (IS·BS·CF·CIS) <span class="dp-ext">{financeDownloading ? '생성 중…' : 'Excel'}</span></button>
					{/if}
					<div class="dp-sub">원본 · 개발자용 (parquet)</div>
					<a class="dp-link" href={panelDlUrl} download>공시 panel <span class="dp-ext">.parquet</span></a>
					{#if dlMarket !== 'US'}
						<a class="dp-link" href={financeDlUrl} download>재무제표 <span class="dp-ext">.parquet</span></a>
					{/if}
					<a class="dp-link dp-ds" href={DATASET_URL} target="_blank" rel="noreferrer">전체 데이터셋 (모든 회사) ↗</a>
					<div class="dp-policy">
						<div>원자료 <b>{dlMarket === 'US' ? 'SEC EDGAR' : 'DART 전자공시'}</b> · 가공·수평화 <b>dartlab</b> · 배포 HuggingFace 공개 데이터셋.</div>
						<div>{dlMarket === 'US' ? '미국 정부 저작물(퍼블릭 도메인)' : '공공데이터(공공데이터법)'} · 영리·비영리 <b>자유 이용·재배포 가능</b> · <b>출처 표기 권장</b>(DART/SEC · dartlab).</div>
						<div class="dp-warn">⚠ 데이터 정확성·완전성 미보증(원자료는 공시제출인 책임) · <b>투자 판단·자문이 아닙니다</b>.</div>
						<a class="dp-terms" href={dlMarket === 'US' ? 'https://www.sec.gov/os/accessing-edgar-data' : 'https://opendart.fss.or.kr/intro/terms.do'} target="_blank" rel="noreferrer">{dlMarket === 'US' ? 'SEC EDGAR 이용조건' : 'DART 이용약관'} ↗</a>
					</div>
				</div>
			</div>

<style>
	/* .fs-btn 트리거 · ViewerStudio 툴바 클래스. Svelte scoped 라 자식이 복제(componentization 비용). */
	.fs-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		height: 30px;
		padding: 0 9px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		background: #050811;
		color: #cbd5e1;
		font: inherit;
		font-size: 11px;
		cursor: pointer;
		white-space: nowrap;
	}
	.fs-btn:hover {
		border-color: var(--amber);
		color: var(--amber);
	}

	/* 데이터 다운로드 · 버튼 hover 시 팝오버(다운로드 링크 + 정책) */
	.data-dl {
		position: relative;
	}
	.data-pop {
		position: absolute;
		top: calc(100% + 6px);
		right: 0;
		z-index: 50;
		width: 320px;
		display: none;
		flex-direction: column;
		gap: 4px;
		padding: 10px;
		background: #0a0e18;
		border: 1px solid #263145;
		border-radius: 8px;
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.5);
	}
	.data-dl:hover .data-pop,
	.data-dl:focus-within .data-pop {
		display: flex;
	}
	.dp-h {
		font-size: 10px;
		color: #94a3b8;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		margin-bottom: 2px;
	}
	.dp-link {
		display: flex;
		align-items: center;
		justify-content: space-between;
		padding: 5px 8px;
		border: 1px solid #1e2433;
		border-radius: 5px;
		color: #e2e8f0;
		font-size: 12px;
		text-decoration: none;
	}
	.dp-link:hover {
		border-color: var(--amber);
		color: var(--amber);
		background: rgba(var(--amber-rgb), 0.06);
	}
	.dp-sub {
		margin-top: 4px;
		font-size: 9px;
		color: #64748b;
		text-transform: uppercase;
		letter-spacing: 0.04em;
	}
	.dp-btn {
		width: 100%;
		font: inherit;
		font-size: 12px;
		cursor: pointer;
		text-align: left;
		background: rgba(var(--amber-rgb), 0.08);
		border-color: rgba(var(--amber-rgb), 0.4);
		color: #f1f5f9;
	}
	.dp-btn:disabled {
		opacity: 0.5;
		cursor: default;
	}
	.dp-ext {
		font-size: 10px;
		color: #94a3b8;
	}
	.dp-ds {
		color: #e2e8f0;
	}
	.dp-policy {
		display: flex;
		flex-direction: column;
		gap: 4px;
		margin-top: 4px;
		padding-top: 6px;
		border-top: 1px solid #1e2433;
		font-size: 10px;
		line-height: 1.5;
		color: #cbd5e1;
	}
	.dp-policy b {
		color: #e2e8f0;
		font-weight: 600;
	}
	.dp-warn {
		color: #fbbf24;
	}
	.dp-warn b {
		color: #fbbf24;
	}
	.dp-terms {
		align-self: flex-start;
		color: var(--amber);
		text-decoration: none;
	}
	.dp-terms:hover {
		text-decoration: underline;
	}

	/* D5 · 터치 타깃 44px(HIG). 부모 툴바와 동일 breakpoint(880px). */
	@media (max-width: 880px) {
		.fs-btn {
			min-height: 44px;
		}
	}
</style>
