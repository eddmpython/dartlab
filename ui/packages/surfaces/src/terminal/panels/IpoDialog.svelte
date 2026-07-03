<script lang="ts">
	// IPO 공모 다이얼로그 · 상장 전 발행사(corp_cls=E) 증권신고서(지분증권) 발굴 + 단건 6카테고리 공모분석.
	// 발굴 목록 = 공개·로컬 공통배선(라이브 워커 /ipo-filings, 베이크 0). 단건 리포트 = 로컬 상위집합
	// (/api 런타임 파싱)이라 env.kind==='local' 게이트 · 공개는 메타 + DART 원문 링크아웃(정직 floor).
	// 모든 수치는 신고서 원문 직추출 + 원문 자체 관계식(항등식) 자기검증 배지 · 고/저평가 단정 금지(좌표만).
	import { X } from 'lucide-svelte';
	import { useDartLabRuntime } from '@dartlab/ui-runtime';
	import type { IpoFiling, IpoReport } from '@dartlab/ui-contracts';
	import type { Lang } from '../lib/types';

	interface Props {
		lang: Lang;
		onClose: () => void;
	}
	let { lang, onClose }: Props = $props();

	const rt = useDartLabRuntime();
	const isLocal = rt.env.kind === 'local';

	let filings = $state<IpoFiling[]>([]);
	let listBusy = $state(true);
	let sel = $state<IpoFiling | null>(null);
	let report = $state<IpoReport | null>(null);
	let reportBusy = $state(false);
	let reportErr = $state(false);
	let seq = 0; // in-flight 토큰 · stale 응답 폐기

	rt.ipo.recent().then((f) => {
		filings = f;
		listBusy = false;
		if (f[0]) pickIssuer(f[0]); // 첫 발행사 자동 선택(로컬은 리포트 즉시 파싱)
	});

	function pickIssuer(f: IpoFiling): void {
		sel = f;
		if (!isLocal) return; // 공개 = 메타 + 원문 링크아웃 pane
		const my = ++seq;
		reportBusy = true;
		reportErr = false;
		report = null;
		rt.ipo
			.report({ rceptNo: f.rceptNo, corpName: f.corpName, confirmationRceptNo: f.confirmationRceptNo })
			.then((r) => {
				if (my !== seq) return;
				report = r;
				reportErr = !r || r.sections.length === 0;
			})
			.catch(() => {
				if (my !== seq) return;
				report = null;
				reportErr = true;
			})
			.finally(() => {
				if (my === seq) reportBusy = false;
			});
	}

	// ── 표시 포맷 · 원값(원)은 조/억 사람 단위, 밴드/멀티플은 범위 물결 ──
	const nf = (v: number, d = 0) => v.toLocaleString('en-US', { maximumFractionDigits: d });
	function won(v: number | null | undefined): string {
		if (v == null || v === 0) return '-';
		const a = Math.abs(v);
		if (a >= 1e12) return nf(v / 1e12, 2) + (lang === 'en' ? 'T KRW' : '조원');
		if (a >= 1e8) return nf(Math.round(v / 1e8)) + (lang === 'en' ? '00M KRW' : '억원');
		return nf(Math.round(v)) + (lang === 'en' ? ' KRW' : '원');
	}
	const price = (v: number | null | undefined): string => (v == null ? '-' : nf(Math.round(v)) + (lang === 'en' ? ' KRW' : '원'));
	function range(t: [number, number] | null | undefined, f: (n: number) => string): string {
		if (!t) return '-';
		return t[0] === t[1] ? f(t[0]) : `${f(t[0])} ~ ${f(t[1])}`;
	}

	const summary = $derived(report?.summary ?? null);
	// 항등식 자기검증 통과율 · 원문 관계식(공모가×주식수=총액, 매각제한+유통=총발행 등) 기계 검증.
	const idsPass = $derived.by(() => {
		const ids = summary?.identities ?? {};
		const vals = Object.values(ids);
		return { pass: vals.filter(Boolean).length, total: vals.length };
	});
	// implied PER vs 비교배수 좌표는 *동일 기준(PER 모형)* 일 때만(단정 아님). EV/EBITDA 등 타 모형의
	// 비교배수와 implied PER 를 겹쳐 톤을 입히면 이종 기준 오도(에이치엘지노믹스 실측 케이스).
	const perModel = $derived((summary?.model ?? '').toUpperCase().includes('PER'));
	const perTone = $derived.by(() => {
		if (!perModel || !summary?.impliedPer || summary.peerPer == null) return '';
		return Math.max(...summary.impliedPer) < summary.peerPer ? 'low' : 'high';
	});

	function onKey(e: KeyboardEvent): void {
		if (e.key === 'Escape') {
			e.preventDefault();
			onClose();
			return;
		}
		if (!filings.length || !sel) return;
		const i = filings.findIndex((f) => f.rceptNo === sel?.rceptNo);
		if (e.key === 'ArrowDown') {
			e.preventDefault();
			const next = filings[Math.min(i + 1, filings.length - 1)];
			if (next) pickIssuer(next);
		} else if (e.key === 'ArrowUp') {
			e.preventDefault();
			const prev = filings[Math.max(i - 1, 0)];
			if (prev) pickIssuer(prev);
		}
	}
</script>

<div class="scrimWrap" role="presentation" onclick={onClose}>
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="scrModal ipoModal"
		role="dialog"
		aria-modal="true"
		aria-label={lang === 'en' ? 'IPO offerings' : 'IPO 공모 발굴'}
		onclick={(e) => e.stopPropagation()}
		onkeydown={onKey}
		tabindex="-1"
	>
		<div class="scrHead">
			<span class="scrTitle">{lang === 'en' ? 'IPO OFFERINGS' : 'IPO 공모'}</span>
			<span class="ipoSub">{lang === 'en' ? 'pre-listing issuers · live from DART registration statements (equity) · last 3 months' : '상장 전 발행사 · 증권신고서(지분증권) 라이브 · 최근 3개월'}</span>
			<button class="scrClose" onclick={onClose} aria-label="close"><X size={14} /></button>
		</div>

		<div class="ipoBody">
			<div class="ipoList" role="listbox" aria-label={lang === 'en' ? 'issuers' : '발행사 목록'}>
				{#if listBusy}
					<div class="ipoState"><span class="ipoSpin">◴</span>{lang === 'en' ? 'Loading…' : '발굴 중…'}</div>
				{:else if !filings.length}
					<div class="ipoState">{lang === 'en' ? 'No filings in window (or live source not deployed).' : '최근 3개월 신규 공모 없음 (또는 라이브 소스 미배선).'}</div>
				{:else}
					{#each filings as f (f.rceptNo)}
						<!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
						<div class={'ipoRow' + (sel?.rceptNo === f.rceptNo ? ' sel' : '')} onclick={() => pickIssuer(f)}>
							<span class="ipoCorp"><b>{f.corpName}</b></span>
							<span class="ipoDate mono">{f.rceptDate}</span>
							<span class="ipoTags">
								{#if f.isSpac}<i class="tag tSpac">{lang === 'en' ? 'SPAC' : '스팩'}</i>{/if}
								{#if f.confirmationRceptNo}<i class="tag tConf">{lang === 'en' ? 'priced' : '확정가'}</i>{/if}
								{#if f.corrected}<i class="tag tCorr">{lang === 'en' ? 'amended' : '정정'}</i>{/if}
							</span>
						</div>
					{/each}
				{/if}
			</div>

			<div class="ipoDetail">
				{#if !sel}
					<div class="ipoState">{lang === 'en' ? 'Select an issuer.' : '발행사를 선택하세요.'}</div>
				{:else}
					<div class="ipoDetHead">
						<b class="ipoDetName">{sel.corpName}</b>
						<span class="ipoDetMeta">{sel.reportNm} · {sel.rceptDate}</span>
						<a class="ipoExt" href={sel.url} target="_blank" rel="noopener">{lang === 'en' ? 'DART source ↗' : 'DART 원문 ↗'}</a>
					</div>

					{#if !isLocal}
						<!-- 공개 floor · 메타 + 링크아웃. 리포트는 로컬 상위집합에서 원문 라이브 파싱(무거운 compute). -->
						<div class="ipoPublicNote">
							<p>
								{lang === 'en'
									? 'The full 6-category offering report (valuation vs peers, free-float and lock-up waterfall, self-verified identities) is generated by parsing the filing text live on the local terminal.'
									: '6카테고리 공모분석 리포트(비교기업 대비 밸류에이션 좌표·유통물량/보호예수·항등식 자기검증)는 로컬 터미널이 신고서 원문을 라이브 파싱해 생성합니다.'}
							</p>
							<code>pip install dartlab && dartlab serve</code>
							{#if sel.confirmationRceptNo}
								<p class="ipoConfNote">
									{lang === 'en' ? 'Final offering price disclosed: ' : '확정공모가 공시됨: '}
									<a href={'https://dart.fss.or.kr/dsaf001/main.do?rcpNo=' + sel.confirmationRceptNo} target="_blank" rel="noopener">{lang === 'en' ? 'pricing filing ↗' : '발행조건확정 원문 ↗'}</a>
								</p>
							{/if}
						</div>
					{:else if reportBusy}
						<div class="ipoState"><span class="ipoSpin">◴</span>{lang === 'en' ? 'Parsing filing text live… (a few seconds)' : '신고서 원문 라이브 파싱 중… (수초 소요)'}</div>
					{:else if reportErr || !report}
						<div class="ipoState ipoErr">
							{lang === 'en' ? 'Could not build the report (fetch/parse failed). Use the DART source link above.' : '리포트 생성 실패(원문 fetch/파싱 실패). 위 DART 원문 링크로 확인하세요.'}
						</div>
					{:else}
						{#if summary}
							<div class="ipoKpis">
								{#if summary.confirmedPrice}
									<div class="kpi kpiHot">
										<span class="kLbl">{lang === 'en' ? 'final price' : '확정공모가'}</span>
										<span class="kVal">{price(summary.confirmedPrice)}</span>
										{#if summary.bandLocation}<span class="kSub">{summary.bandLocation}{lang === 'en' ? '' : ' 확정'}</span>{/if}
									</div>
								{:else if summary.priceBand}
									<div class="kpi">
										<span class="kLbl">{lang === 'en' ? 'price band' : '희망공모가'}</span>
										<span class="kVal">{range(summary.priceBand, (n) => nf(n))}{lang === 'en' ? ' KRW' : '원'}</span>
									</div>
								{/if}
								{#if summary.marketCap}
									<div class="kpi">
										<span class="kLbl">{lang === 'en' ? 'implied mkt cap' : '예상 시가총액'}</span>
										<span class="kVal">{range(summary.marketCap, won)}</span>
									</div>
								{/if}
								{#if summary.subscription}
									<div class="kpi">
										<span class="kLbl">{lang === 'en' ? 'subscription' : '청약기일'}</span>
										<span class="kVal">{summary.subscription}</span>
									</div>
								{/if}
								{#if summary.freeFloatPct != null}
									<div class="kpi">
										<span class="kLbl">{lang === 'en' ? 'free float at listing' : '상장직후 유통가능'}</span>
										<span class="kVal">{nf(summary.freeFloatPct, 1)}%</span>
									</div>
								{/if}
								{#if summary.impliedPer}
									<div class={'kpi' + (perTone === 'low' ? ' kUp' : perTone === 'high' ? ' kDn' : '')}>
										<span class="kLbl">implied PER</span>
										<span class="kVal">{range(summary.impliedPer, (n) => nf(n, 1))}{lang === 'en' ? 'x' : '배'}</span>
										{#if summary.peerPer != null && perModel}
											<span class="kSub">{lang === 'en' ? `peer ${nf(summary.peerPer, 1)}x` : `비교기업 ${nf(summary.peerPer, 1)}배 좌표`}</span>
										{:else if summary.peerPer != null}
											<span class="kSub">{lang === 'en' ? `peer ${nf(summary.peerPer, 1)}x (${summary.model}, not comparable)` : `비교배수 ${nf(summary.peerPer, 1)}배 (${summary.model} 기준 · 직접 비교 아님)`}</span>
										{/if}
									</div>
								{/if}
								{#if summary.isLoss}
									<div class="kpi kDn"><span class="kLbl">{lang === 'en' ? 'risk' : '리스크'}</span><span class="kVal">{lang === 'en' ? 'loss-making' : '최근 연간 적자'}</span></div>
								{/if}
								{#if idsPass.total}
									<div class={'kpi ' + (idsPass.pass === idsPass.total ? 'kUp' : 'kDn')}>
										<span class="kLbl">{lang === 'en' ? 'identity checks' : '항등식 검증'}</span>
										<span class="kVal">{idsPass.pass}/{idsPass.total}</span>
										<span class="kSub">{lang === 'en' ? 'self-verified vs source' : '원문 관계식 자기검증'}</span>
									</div>
								{/if}
							</div>
						{/if}

						<div class="ipoSections">
							{#each report.sections as sec (sec.title)}
								<section class="ipoSec">
									<h4>
										{sec.title}
										{#if sec.badge}<span class={'secBadge ' + (sec.badge.startsWith('✓') ? 'ok' : 'no')}>{sec.badge}</span>{/if}
									</h4>
									<dl>
										{#each sec.rows as [label, value] (label)}
											<dt>{label}</dt>
											<dd>{value}</dd>
										{/each}
									</dl>
								</section>
							{/each}
						</div>
						<p class="ipoFoot">
							{lang === 'en'
								? 'All figures extracted from the filing itself and self-verified with in-document identities (badges). Implied multiples and discounts are coordinates vs the issuer-chosen peer set, not an over/under-valuation verdict.'
								: '모든 수치는 접수번호 원문에서 직접 추출, 원문 자체 관계식으로 자기검증(배지). implied 멀티플·할인율은 발행사 선택 비교군 기준 좌표이며 고/저평가 단정이 아닙니다.'}
						</p>
					{/if}
				{/if}
			</div>
		</div>

		<div class="ipoFootBar">
			<span><b class="tAmber">↑↓</b> {lang === 'en' ? 'issuer' : '발행사 이동'}</span>
			<span><b class="tAmber">Esc</b> {lang === 'en' ? 'close' : '닫기'}</span>
			{#if filings.length}<span class="ipoCount">{filings.length}{lang === 'en' ? ' issuers' : '개 발행사'}</span>{/if}
		</div>
	</div>
</div>

<style>
	.ipoModal { width: min(1060px, 96vw); max-height: 88vh; display: flex; flex-direction: column; }
	.ipoSub { font-size: 10px; color: #c2cad6; font-style: italic; }
	.scrClose { margin-left: auto; }
	.ipoBody { flex: 1 1 auto; min-height: 0; display: grid; grid-template-columns: 250px 1fr; border-top: 1px solid var(--dl-line, #1b2130); }
	.ipoList { overflow-y: auto; border-right: 1px solid var(--dl-line, #1b2130); }
	.ipoRow { display: flex; flex-wrap: wrap; align-items: center; gap: 3px 8px; padding: 7px 10px; border-left: 2px solid transparent; border-bottom: 1px solid var(--dl-line, #1b2130); cursor: pointer; }
	.ipoRow.sel { border-left-color: var(--amber, #e3b341); background: rgba(var(--amber-rgb, 227, 179, 65), 0.1); }
	.ipoCorp { font-size: 11.5px; color: var(--dl-ink, #c8cfdb); }
	.ipoDate { font-size: 10px; color: #8b93a0; font-variant-numeric: tabular-nums; }
	.ipoTags { display: inline-flex; gap: 4px; }
	.tag { font-style: normal; font-size: 8.5px; font-weight: 700; border-radius: 3px; padding: 1px 5px; }
	.tSpac { color: #d2a8ff; background: rgba(210, 168, 255, 0.12); }
	.tConf { color: #56d364; background: rgba(86, 211, 100, 0.12); }
	.tCorr { color: #d29922; background: rgba(210, 153, 34, 0.12); }
	.ipoDetail { overflow-y: auto; padding: 10px 14px; min-width: 0; }
	.ipoDetHead { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; padding-bottom: 8px; border-bottom: 1px solid var(--dl-line, #1b2130); }
	.ipoDetName { font-size: 13px; color: var(--dl-ink, #c8cfdb); }
	.ipoDetMeta { font-size: 10.5px; color: #8b93a0; }
	.ipoExt { margin-left: auto; font-size: 10px; color: var(--amber, #e3b341); text-decoration: none; white-space: nowrap; }
	.ipoExt:hover { text-decoration: underline; }
	.ipoState { padding: 26px 14px; font-size: 12px; color: #c2cad6; text-align: center; }
	.ipoErr { color: var(--dn, #f85149); }
	.ipoSpin { display: inline-block; margin-right: 6px; animation: ipospin 0.9s linear infinite; }
	@keyframes ipospin { to { transform: rotate(360deg); } }
	.ipoPublicNote { padding: 16px 4px; font-size: 11.5px; color: #aab2bf; line-height: 1.6; }
	.ipoPublicNote code { display: inline-block; margin-top: 8px; font-size: 10.5px; padding: 3px 8px; border: 1px solid var(--dl-line, #2a3142); border-radius: 4px; color: var(--dl-ink, #c8cfdb); background: rgba(255, 255, 255, 0.04); }
	.ipoConfNote { margin-top: 10px; }
	.ipoConfNote a { color: var(--amber, #e3b341); }
	.ipoKpis { display: flex; flex-wrap: wrap; gap: 8px; padding: 10px 0; }
	.kpi { min-width: 118px; padding: 6px 10px; border: 1px solid var(--dl-line, #2a3142); border-radius: 4px; display: flex; flex-direction: column; gap: 2px; }
	.kLbl { font-size: 8.5px; text-transform: uppercase; letter-spacing: 0.04em; color: #8b93a0; }
	.kVal { font-size: 13px; font-weight: 700; color: var(--dl-ink, #c8cfdb); font-variant-numeric: tabular-nums; }
	.kSub { font-size: 9px; color: #8b93a0; }
	.kpiHot { border-color: var(--amber, #e3b341); }
	.kpiHot .kVal { color: var(--amber, #e3b341); }
	.kUp .kVal { color: var(--up, #56d364); }
	.kDn .kVal { color: var(--dn, #f85149); }
	.ipoSections { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 10px; padding-bottom: 8px; }
	.ipoSec { border: 1px solid var(--dl-line, #1b2130); border-radius: 4px; padding: 8px 10px; }
	.ipoSec h4 { margin: 0 0 6px; font-size: 10.5px; letter-spacing: 0.03em; color: #aab2bf; display: flex; align-items: center; gap: 8px; }
	.secBadge { font-size: 8.5px; font-weight: 700; border-radius: 3px; padding: 1px 5px; }
	.secBadge.ok { color: #56d364; background: rgba(86, 211, 100, 0.12); }
	.secBadge.no { color: #d29922; background: rgba(210, 153, 34, 0.12); }
	.ipoSec dl { margin: 0; display: grid; grid-template-columns: minmax(84px, auto) 1fr; gap: 3px 10px; font-size: 11px; }
	.ipoSec dt { color: #8b93a0; }
	.ipoSec dd { margin: 0; color: var(--dl-ink, #c8cfdb); overflow-wrap: anywhere; }
	.ipoFoot { font-size: 9.5px; color: #8b93a0; line-height: 1.5; margin: 2px 0 4px; }
	.ipoFootBar { display: flex; gap: 14px; align-items: center; padding: 6px 14px; border-top: 1px solid var(--dl-line, #1b2130); font-size: 10px; color: #c2cad6; }
	.ipoFootBar .tAmber { color: var(--amber, #e3b341); }
	.ipoCount { margin-left: auto; font-variant-numeric: tabular-nums; }
	@media (max-width: 720px) {
		.ipoBody { grid-template-columns: 1fr; grid-template-rows: minmax(90px, 168px) 1fr; }
		.ipoList { border-right: 0; border-bottom: 1px solid var(--dl-line, #1b2130); }
	}
</style>
