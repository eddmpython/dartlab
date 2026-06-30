<script lang="ts">
	// 데이터 출처 모달 · 터미널 전 패널의 원천·갱신주기·라이선스를 한 표로 명시 (공공누리 출처표시 의무 포함).
	import type { Lang } from '../lib/types';
	import { GOV_ATTRIBUTION, MACRO_ATTRIBUTION } from '@dartlab/ui-contracts';
	import { fetchLastSync, fetchLastCheck, fmtSyncParts, syncTone } from '../lib/syncStatus'; // 동기화 실측(HF lastCommit) + 마지막 점검(cron 실행)

	interface Props {
		lang: Lang;
		open: boolean;
		onClose: () => void;
		// 최근 일자 · 이미 로드된 데이터에서만 (추가 fetch 0). 모르는 원천은 '·' 정직 표기.
		pricesAsOf?: string; // 주가 스냅샷 기준일
		macroAsOf?: string; // 매크로 빌드 기준일
		financeLatest?: string; // 현재 종목 재무 최신 분기 (예: 26Q1)
	}
	let { lang, open, onClose, pricesAsOf = '', macroAsOf = '', financeLatest = '' }: Props = $props();

	interface SourceRow {
		data: { kr: string; en: string };
		org: { kr: string; en: string };
		path: string; // HF 산출물 경로 (mono)
		cadence: { kr: string; en: string };
		license: { kr: string; en: string };
		latest?: () => string; // 최근 일자 · 데이터 자체의 기준일 (가용한 원천만)
		// 동기화 실측 · HF tree lastCommit (선언 주기가 아니라 마지막 실제 push 시각).
		// expectDays = 기대 주기(일) · 신선도 톤 판정 기준. cron 생존 모니터를 겸한다.
		sync?: { dir: string; file?: string; expectDays: number };
		// 마지막 점검 · 담당 워크플로의 마지막 cron 실행 시각(GitHub Actions). push(데이터 변경)와 별개로
		// "매일 점검은 살아있나" 를 본다. 분기 데이터(finance·report)는 변경 없어 push 가 드물어도 점검은 매일.
		// expectDays = cron 주기 (주중만 도는 cron 은 주말 갭 고려해 넉넉히).
		check?: { workflow: string; expectDays: number };
	}
	const ROWS: SourceRow[] = [
		{
			data: { kr: '주가·지수 일별시세 (OHLCV)', en: 'Daily prices & indices (OHLCV)' },
			org: { kr: '금융위원회·한국거래소 · 공공데이터포털', en: 'FSC · KRX · data.go.kr' },
			path: 'gov/prices · gov/indices',
			cadence: { kr: '매 영업일 EOD', en: 'EOD each trading day' },
			license: { kr: '공공누리 · 출처표시', en: 'KOGL · attribution' },
			latest: () => pricesAsOf,
			sync: { dir: 'gov/prices', file: 'recent.parquet', expectDays: 1 },
			check: { workflow: 'buildGovPriceData.yml', expectDays: 3 } // 주중만(M-F) → 주말 갭 고려
		},
		{
			data: { kr: '공시 원문·목록 (정기·수시)', en: 'Filings (regular · non-regular)' },
			org: { kr: '금융감독원 DART (OpenDART)', en: 'FSS DART (OpenDART)' },
			path: 'panel · allFilings',
			cadence: { kr: '매일 동기화', en: 'daily sync' },
			license: { kr: 'DART 이용약관', en: 'DART terms' },
			sync: { dir: 'dart/allFilings', file: 'recent.parquet', expectDays: 1 },
			check: { workflow: 'originalSync.yml', expectDays: 1 } // panel·allFilings 매일 02:00 UTC
		},
		{
			data: { kr: '공시 본문 검색 인덱스 (전문)', en: 'Filing full-text search index' },
			org: { kr: 'dartlab 자체 구축 (공시 파싱)', en: 'dartlab-built (parsed filings)' },
			path: 'dart/contentIndex',
			cadence: { kr: '매일 (증분)', en: 'daily (incremental)' },
			license: { kr: '파생 산출물', en: 'derived artifact' },
			sync: { dir: 'dart/contentIndex', file: 'manifest.json', expectDays: 1 },
			check: { workflow: 'searchIndexBuild.yml', expectDays: 1 } // 검색 코퍼스 매일 04:00 KST 증분(이번 하루 RED 가시화)
		},
		{
			data: { kr: '재무제표 (분기·연간·TTM)', en: 'Financial statements (Q · FY · TTM)' },
			org: { kr: 'DART 정기보고서 XBRL', en: 'DART XBRL filings' },
			path: 'dart/finance/{code}',
			cadence: { kr: '분기 (공시 후)', en: 'quarterly (post-filing)' },
			license: { kr: 'DART 이용약관', en: 'DART terms' },
			latest: () => (financeLatest ? `${financeLatest} (현재 종목)` : ''),
			check: { workflow: 'dataSync.yml', expectDays: 1 } // list.json 누락검사 매일 18:00 UTC (변경 없어도 점검)
		},
		{
			data: { kr: '정기보고서 팩트 (배당·자사주·임원·대주주·회사채)', en: 'Report facts (dividends · buyback · officers · owners · bonds)' },
			org: { kr: 'DART OpenAPI 정기보고서', en: 'DART OpenAPI report' },
			path: 'report',
			cadence: { kr: '분기', en: 'quarterly' },
			license: { kr: 'DART 이용약관', en: 'DART terms' },
			sync: { dir: 'dart/scan/report', expectDays: 7 },
			check: { workflow: 'dataSync.yml', expectDays: 1 } // report rcept 누락검사 매일 (변경 없어도 점검)
		},
		{
			data: { kr: '한국 매크로 (환율·기준금리·CPI·수출·경기지수)', en: 'KR macro (FX · base rate · CPI · exports · CLI)' },
			org: { kr: '한국은행 ECOS', en: 'Bank of Korea ECOS' },
			path: 'macro/ecos',
			cadence: { kr: '일·월 (지표별)', en: 'daily · monthly' },
			license: { kr: 'ECOS 오픈API', en: 'ECOS open API' },
			latest: () => macroAsOf,
			sync: { dir: 'macro/ecos', expectDays: 1 },
			check: { workflow: 'macroData.yml', expectDays: 1 } // 매일 21:30 UTC
		},
		{
			data: { kr: '미국 매크로 (국채금리·연방금리·CPI·고용)', en: 'US macro (UST · Fed funds · CPI · labor)' },
			org: { kr: 'FRED (세인트루이스 연준)', en: 'FRED (St. Louis Fed)' },
			path: 'macro/fred',
			cadence: { kr: '일·주·월 (지표별)', en: 'daily · weekly · monthly' },
			license: { kr: 'FRED API 약관', en: 'FRED API terms' },
			latest: () => macroAsOf,
			sync: { dir: 'macro/fred', expectDays: 1 },
			check: { workflow: 'macroData.yml', expectDays: 1 } // 매일 21:30 UTC
		},
		{
			data: { kr: '생태계·등급·산업분류·공급망', en: 'Ecosystem · grades · industry map · supply chain' },
			org: { kr: 'dartlab 자체 구축 (공시 파싱)', en: 'dartlab-built (parsed filings)' },
			path: 'ecosystem · map',
			cadence: { kr: '분기', en: 'quarterly' },
			license: { kr: '파생 산출물', en: 'derived artifact' },
			sync: { dir: 'landing/map', file: 'ecosystem.json', expectDays: 2 }
		},
		{
			data: { kr: '신용 dCR·적정주가·종합판정·백테스트', en: 'dCR credit · fair value · verdict · backtest' },
			org: { kr: 'dartlab 엔진 · 브라우저 계산', en: 'dartlab engine · in-browser' },
			path: '·',
			cadence: { kr: '즉시 (실데이터 입력)', en: 'instant (from real data)' },
			license: { kr: '비공식 · 투자조언 아님', en: 'unofficial · not advice' }
		}
	];
	const T = (kr: string, en: string) => (lang === 'en' ? en : kr);
	function onKey(e: KeyboardEvent) {
		if (e.key === 'Escape') onClose();
	}

	// 동기화 실측 · 모달 첫 오픈 시 1회 (syncStatus 세션 캐시), 행별 독립 스트림-인.
	// undefined=조회 중(…) / null=실패('·' 정직) / ISO=실측 시각.
	let syncAt = $state<Record<string, string | null>>({});
	// 마지막 점검 · undefined=조회 중 / null=실패('·') / {at,conclusion}=실측 cron 실행.
	let checkAt = $state<Record<string, { at: string; conclusion: string | null } | null>>({});
	let probed = false;
	$effect(() => {
		if (!open || probed) return;
		probed = true;
		for (const r of ROWS) {
			const key = r.path;
			if (r.sync) {
				void fetchLastSync(r.sync.dir, r.sync.file).then((iso) => {
					syncAt = { ...syncAt, [key]: iso };
				});
			}
			if (r.check) {
				void fetchLastCheck(r.check.workflow).then((c) => {
					checkAt = { ...checkAt, [key]: c };
				});
			}
		}
	});
</script>

<svelte:window onkeydown={open ? onKey : undefined} />

{#if open}
	<div class="scrimWrap" role="presentation" onclick={onClose}>
		<div class="scrModal srcModal" role="dialog" aria-modal="true" aria-label={T('데이터 출처', 'Data sources')} onclick={(e) => e.stopPropagation()}>
			<div class="scrHead">
				<span class="scrTitle">{T('데이터 출처', 'DATA SOURCES')}</span>
				<span class="scrCount">{ROWS.length} {T('원천 · 전 데이터 EOD/배치 (실시간 아님)', 'sources · all EOD/batch (not realtime)')}</span>
				<button class="scrClose" onclick={onClose} aria-label="close">✕</button>
			</div>
			<div class="srcBody">
				<table class="scrTable srcTable">
					<thead><tr>
						<th class="l">{T('데이터', 'DATA')}</th>
						<th class="l">{T('원천 기관', 'SOURCE')}</th>
						<th class="l">{T('산출물', 'ARTIFACT')}</th>
						<th class="l">{T('갱신', 'CADENCE')}</th>
						<th class="l">{T('데이터 기준일', 'DATA AS-OF')}</th>
						<th class="l" title={T('파이프라인 상태 · 점검: 담당 워크플로 마지막 실행(살아있나) · 변경: 데이터 마지막 push(바뀐 때). 분기 데이터는 변경이 없어도 점검이 돌면 정상.', 'pipeline status · check: last workflow run (alive?) · change: last data push (when it changed). Quarterly data can be unchanged yet healthy as long as checks keep running.')}>{T('상태', 'STATUS')}</th>
						<th class="l">{T('라이선스·조건', 'LICENSE')}</th>
					</tr></thead>
					<tbody>
						{#each ROWS as r (r.path + r.data.en)}
							<tr class="srcRow">
								<td class="l"><b>{T(r.data.kr, r.data.en)}</b></td>
								<td class="l">{T(r.org.kr, r.org.en)}</td>
								<td class="l mono srcPath">{r.path}</td>
								<td class="l">{T(r.cadence.kr, r.cadence.en)}</td>
								<td class="l mono srcLatest">{r.latest?.() || '·'}</td>
								<td class="l mono srcStat">
									{#if r.check || r.sync}
										{#if r.check}
											{@const c = checkAt[r.path]}
											<div class="statLine"><span class="statLabel">{T('점검', 'check')}</span>{#if c === undefined}<span class="dim">…</span>{:else if c === null}<span class="dim">·</span>{:else}{@const f = fmtSyncParts(c.at, lang)}<span class={'syncDot ' + syncTone(c.at, r.check.expectDays)} title={(c.conclusion ? 'run: ' + c.conclusion + ' · ' : '') + f.abs}>●</span> {f.rel}{/if}</div>
										{/if}
										{#if r.sync}
											{@const iso = syncAt[r.path]}
											<div class="statLine"><span class="statLabel">{T('변경', 'change')}</span>{#if iso === undefined}<span class="dim">…</span>{:else if iso === null}<span class="dim">·</span>{:else}{@const f = fmtSyncParts(iso, lang)}<span class={'syncDot ' + syncTone(iso, r.sync.expectDays)} title={f.abs}>●</span> {f.rel}{/if}</div>
										{/if}
									{:else}·{/if}
								</td>
								<td class="l srcLic">{T(r.license.kr, r.license.en)}</td>
							</tr>
						{/each}
					</tbody>
				</table>
				<div class="srcNotes">
					<div class="srcNote">{GOV_ATTRIBUTION} · {MACRO_ATTRIBUTION}</div>
					<div class="srcNote">{T('호스팅: HuggingFace dataset', 'Hosting: HuggingFace dataset')} <span class="mono">eddmpython/dartlab-data</span> ({T('공개', 'public')})</div>
					<div class="srcNote dim">{T('본 화면의 모든 수치는 공시·공공 데이터 기반 정보 제공 목적이며 투자 권유가 아닙니다. 투자 판단의 책임은 이용자에게 있습니다.', 'All figures are for information only, built from public filings and open data · not investment advice.')}</div>
				</div>
			</div>
		</div>
	</div>
{/if}
