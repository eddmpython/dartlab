// 동기화 실측 · HF tree API 의 lastCommit 시각으로 "마지막 실제 push" 를 행마다 확인.
// 선언된 갱신 주기("매일 동기화")가 아니라 측정값을 보여주는 출처 모달의 정공 ·
// allFilings·panel·macro 등 cron 파이프라인의 생존 여부가 화면에서 그대로 검증된다.
// prices-snapshot 4/24·dashboards 4/22 동결 사고(빌드는 되는데 발행이 죽은 채 아무도 모름)의 재발 감시.
const API_ROOT = 'https://huggingface.co/api/datasets/eddmpython/dartlab-data';

const cache = new Map<string, Promise<string | null>>(); // 세션 캐시 · 모달 재오픈 시 재조회 없음

interface TreeEntry {
	path: string;
	lastCommit?: { date?: string };
}

/** 마지막 실제 push 시각(ISO). file 지정 = paths-info 단건(대형 dir 의 tree 1000개 페이지 한계 회피 ·
 * allFilings 일별 1000+ 파일 실측), dir 만 = tree 1페이지 내 최신. 실패 = null(정직 '·').
 * paths-info 는 form-urlencoded POST = CORS preflight 없는 simple request. */
export function fetchLastSync(dir: string, file?: string): Promise<string | null> {
	const key = `${dir}|${file ?? ''}`;
	const hit = cache.get(key);
	if (hit) return hit;
	const p = (async (): Promise<string | null> => {
		try {
			if (file) {
				const resp = await fetch(`${API_ROOT}/paths-info/main`, {
					method: 'POST',
					headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
					body: `paths=${encodeURIComponent(`${dir}/${file}`)}&expand=true`
				});
				if (!resp.ok) return null;
				const entries = (await resp.json()) as TreeEntry[];
				return entries[0]?.lastCommit?.date ?? null;
			}
			const resp = await fetch(`${API_ROOT}/tree/main/${encodeURI(dir)}?expand=true`);
			if (!resp.ok) return null;
			const entries = (await resp.json()) as TreeEntry[];
			const dates = entries.map((e) => e.lastCommit?.date).filter((d): d is string => !!d).sort();
			return dates.at(-1) ?? null;
		} catch {
			return null;
		}
	})();
	cache.set(key, p);
	return p;
}

// ── 마지막 점검(파이프라인 liveness) · HF push 시각(데이터 변경)과 별개. 분기 데이터(finance·report)는
//    매일 체크하지만 변경 없으면 push 0 → push 시각만 보면 stale 처럼 보인다. 담당 워크플로의 마지막
//    실행으로 "점검은 살아있나(변경이 없을 뿐)" vs "파이프라인 사망" 을 구분한다.
//    ⚠ 예약(schedule)만 세면 수동 dispatch 가 빠져 "점검 < 변경" 역전이 난다(데이터는 방금 수동 회복
//    됐는데 마지막 *예약* 은 어제). 그래서 trigger 무관 *최신 실행 1건*을 워크플로별로 조회하고,
//    시작(run_started_at)이 아니라 *완료(updated_at)* 시각을 쓴다 · push 는 실행 도중 일어나므로
//    완료 ≥ push → 점검 ≥ 변경 항상 성립. GitHub Actions 공개 REST(공개repo·CORS·무인증), 워크플로별
//    1회 조회(파일명별 캐시·distinct 4개라 호출 ≤4). 실패 = null('·' 정직). */
const checkCache = new Map<string, Promise<{ at: string; conclusion: string | null } | null>>();

/** 담당 워크플로의 마지막 실행(예약+수동) 완료 시각(ISO) + 결과. 미존재/실패 = null. */
export function fetchLastCheck(workflowFile: string): Promise<{ at: string; conclusion: string | null } | null> {
	const cached = checkCache.get(workflowFile);
	if (cached) return cached;
	const p = (async (): Promise<{ at: string; conclusion: string | null } | null> => {
		try {
			const resp = await fetch(
				`https://api.github.com/repos/eddmpython/dartlab/actions/workflows/${workflowFile}/runs?per_page=1`,
				{ headers: { Accept: 'application/vnd.github+json' } }
			);
			if (!resp.ok) return null;
			const data = (await resp.json()) as { workflow_runs?: Array<{ updated_at?: string; run_started_at?: string; created_at?: string; conclusion?: string | null }> };
			const run = (data.workflow_runs ?? [])[0];
			if (!run) return null;
			const at = run.updated_at || run.run_started_at || run.created_at || '';
			return at ? { at, conclusion: run.conclusion ?? null } : null;
		} catch {
			return null; /* 네트워크/rate-limit 실패 = '·' 정직 폴백 */
		}
	})();
	checkCache.set(workflowFile, p);
	return p;
}

/** ISO → { rel:'3시간 전', abs:'06-12 23:14' } (KST 로컬). 셀에서 상대=1줄·절대=다음 줄로 쌓아 렌더. */
export function fmtSyncParts(iso: string, lang: 'kr' | 'en'): { rel: string; abs: string } {
	const t = new Date(iso);
	if (Number.isNaN(t.getTime())) return { rel: '·', abs: '' };
	const mins = Math.max(0, Math.round((Date.now() - t.getTime()) / 60000));
	const rel =
		mins < 60
			? lang === 'en'
				? `${mins}m ago`
				: `${mins}분 전`
			: mins < 60 * 48
				? lang === 'en'
					? `${Math.round(mins / 60)}h ago`
					: `${Math.round(mins / 60)}시간 전`
				: lang === 'en'
					? `${Math.round(mins / 1440)}d ago`
					: `${Math.round(mins / 1440)}일 전`;
	const pad = (n: number) => String(n).padStart(2, '0');
	return { rel, abs: `${pad(t.getMonth() + 1)}-${pad(t.getDate())} ${pad(t.getHours())}:${pad(t.getMinutes())}` };
}

/** ISO → '3시간 전 (06-12 23:14)' 한 줄 병기 (parts 합성). */
export function fmtSync(iso: string, lang: 'kr' | 'en'): string {
	const { rel, abs } = fmtSyncParts(iso, lang);
	return abs ? `${rel} (${abs})` : rel;
}

/** 신선도 톤 · 기대 주기(expectDays) 대비: ≤2× 정상, ≤4× 주의, 초과 = 지연(적색). */
export function syncTone(iso: string, expectDays: number): 'tUp' | 'tWarn' | 'tDn' {
	const t = new Date(iso).getTime();
	if (Number.isNaN(t)) return 'tWarn';
	const ageDays = (Date.now() - t) / 86400000;
	if (ageDays <= expectDays * 2) return 'tUp';
	if (ageDays <= expectDays * 4) return 'tWarn';
	return 'tDn';
}
