/**
 * browser-as-server 라이브 데이터 코어. 블로그(dartlab 이야기)와 노트북 마크다운셀이 공유한다.
 *
 * 세 가지 순수 조각으로 나뉜다. 통합(richMarkdown 확장의 hydration 이든 컴포넌트든)은 이걸 부른다.
 *   1. resolveEndpoint. 저자가 쓴 @[data](...) 대상이 공개 계약(엔진 축) 안인지 검증. 계약 밖이면 null.
 *      공개 계약 = 엔진명뿐이라, 임의 URL(새 verb·경로 이탈)은 브라우저에서 부를 수 없게 막는다.
 *   2. fetchLive. 검증된 엔드포인트를 executionStore.serveApi 로 부른다(SW 왕복 없이 같은 앱에서 직접).
 *   3. renderLiveTable. 응답을 안전한 HTML(모든 셀 이스케이프)로. 정적 호스트라 이 이스케이프가 신뢰경계다.
 *
 * serveApi(무거운 노트북 엔진 체인)는 fetchLive 안에서 동적 import 한다. 순수 조각(검증·렌더)은
 * 그 체인 없이 테스트·재사용되고, 블로그 페이지는 라이브 데이터를 실제 부를 때만 엔진을 당긴다.
 */

// 공개 계약 = 엔진명뿐. @[data] 가 부를 수 있는 엔드포인트를 browserApi.py 라우트와 1:1 로 제한한다.
// 종목코드는 국내 6자리 + 해외 티커를 포괄해 4~10 영숫자. 세그먼트는 슬래시·물음표·공백 불가.
const CODE = '[0-9A-Za-z]{4,10}';
const SEG = '[^/?#\\s]+';
const CONTRACT: RegExp[] = [
	new RegExp(`^company/${CODE}/panel/${SEG}$`),
	new RegExp(`^company/${CODE}/select/${SEG}$`),
	new RegExp(`^company/${CODE}/analysis/${SEG}/${SEG}$`),
	new RegExp(`^company/${CODE}/credit/${SEG}$`),
	new RegExp(`^company/${CODE}/story/${SEG}$`),
	new RegExp(`^company/${CODE}/industry$`),
	new RegExp(`^company/${CODE}/trace/${SEG}$`),
	new RegExp(`^scan/${SEG}$`),
];
// 계약 라우트가 받는 쿼리 키만 허용(browserApi.py 시그니처). 그 외 키는 계약 밖이라 거부.
const ALLOWED_QUERY = new Set(['fields', 'freq', 'scope']);

/**
 * 저자 스펙(예 "company/005930/panel/IS" 또는 "/pyapi/scan/growth?...")을 검증해 정규 /pyapi 경로로.
 * 계약 밖이면 null(호출 안 함).
 */
export function resolveEndpoint(spec: string): string | null {
	const raw = String(spec || '')
		.trim()
		.replace(/^\/+/, '')
		.replace(/^pyapi\//, '');
	const [path, query = ''] = raw.split('?');
	if (!CONTRACT.some((re) => re.test(path))) return null;
	if (query) {
		for (const part of query.split('&')) {
			if (!part) continue;
			const key = part.split('=')[0];
			if (!ALLOWED_QUERY.has(key)) return null;
		}
	}
	return '/pyapi/' + path + (query ? '?' + query : '');
}

export interface LiveResult {
	ok: boolean;
	status: number;
	tier: string;
	data?: unknown;
	error?: string;
}

/** 검증된 엔드포인트를 브라우저 안 dartlab 으로. serveApi 는 SW 없이 같은 앱에서 워커로 직행. */
export async function fetchLive(spec: string): Promise<LiveResult> {
	const endpoint = resolveEndpoint(spec);
	if (!endpoint) {
		return { ok: false, status: 400, tier: 'browser', error: `계약 밖 엔드포인트: ${spec}` };
	}
	try {
		const { serveApi } = await import('$lib/notebook/stores/executionStore');
		const res = await serveApi({ method: 'GET', path: endpoint });
		const tier = res.headers['x-dartlab-tier'] || 'browser';
		let data: unknown;
		try {
			data = JSON.parse(res.body);
		} catch {
			data = { repr: res.body };
		}
		if (res.status !== 200) {
			const detail = (data as { detail?: string })?.detail;
			return { ok: false, status: res.status, tier, error: detail || `HTTP ${res.status}` };
		}
		return { ok: true, status: 200, tier, data };
	} catch (e) {
		return { ok: false, status: 503, tier: 'browser', error: String(e).slice(0, 300) };
	}
}

function esc(v: unknown): string {
	return String(v ?? '').replace(
		/[&<>"]/g,
		(c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' })[c] as string
	);
}

interface TableShape {
	columns: string[];
	shape: [number, number];
	rows: Record<string, unknown>[];
	truncated?: boolean;
}

function isTable(d: unknown): d is TableShape {
	return !!d && Array.isArray((d as TableShape).columns) && Array.isArray((d as TableShape).rows);
}

/**
 * 라이브 응답을 안전한 HTML 로. 모든 셀·헤더는 이스케이프한다. 표(columns/rows)·story(section/text)·
 * dict 를 각각 그린다. tier 는 배지(browser/local)로. 렌더 결과는 이스케이프 완료라 innerHTML 안전.
 */
export function renderLiveTable(result: LiveResult, opts: { max?: number; caption?: string } = {}): string {
	const badge = `<span class="ld-tier ld-tier-${esc(result.tier)}">${esc(result.tier)}</span>`;
	if (!result.ok) {
		return `<div class="ld-box ld-err">${badge}<span class="ld-errmsg">${esc(result.error || '오류')}</span></div>`;
	}
	const d = result.data;
	const cap = opts.caption ? `<figcaption class="ld-cap">${esc(opts.caption)}</figcaption>` : '';
	if (isTable(d)) {
		const max = opts.max ?? 20;
		const shown = d.rows.slice(0, max);
		const head = d.columns.map((c) => `<th>${esc(c)}</th>`).join('');
		const body = shown
			.map((row) => '<tr>' + d.columns.map((c) => `<td>${esc(row[c])}</td>`).join('') + '</tr>')
			.join('');
		const more =
			d.rows.length > shown.length || d.truncated
				? `<div class="ld-more">${d.shape[0]}행 중 ${shown.length}행 표시</div>`
				: '';
		return `<figure class="ld-box ld-table">${cap}<div class="ld-head">${badge}</div><div class="ld-scroll"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>${more}</figure>`;
	}
	// story {section, text}
	const story = d as { section?: string; text?: string };
	if (story && typeof story.text === 'string') {
		return `<figure class="ld-box ld-story">${cap}<div class="ld-head">${badge}</div><div class="ld-text">${esc(story.text)}</div></figure>`;
	}
	// dict 또는 스칼라 repr
	if (d && typeof d === 'object') {
		const rows = Object.entries(d as Record<string, unknown>)
			.slice(0, 40)
			.map(([k, v]) => `<tr><th>${esc(k)}</th><td>${esc(typeof v === 'object' ? JSON.stringify(v) : v)}</td></tr>`)
			.join('');
		return `<figure class="ld-box ld-dict">${cap}<div class="ld-head">${badge}</div><div class="ld-scroll"><table><tbody>${rows}</tbody></table></div></figure>`;
	}
	return `<figure class="ld-box">${cap}<div class="ld-head">${badge}</div><div class="ld-text">${esc(String(d))}</div></figure>`;
}

/**
 * 렌더된 마크다운 안의 라이브 데이터 placeholder(div.ld-mount[data-spec])를 실제 표로 채운다.
 * richMarkdown 이 낸 placeholder 를 블로그(+page.svelte)와 노트북 마크다운셀($effect)이 이걸로 hydrate.
 * 멱등하다(한 번 채운 mount 는 data-ld-done 표기로 재실행 안 함). 각 mount 는 독립 fetch(병렬).
 */
export function hydrateLiveData(root: ParentNode | null | undefined): void {
	if (!root || typeof document === 'undefined') return;
	const mounts = root.querySelectorAll<HTMLElement>('.ld-mount[data-spec]:not([data-ld-done])');
	mounts.forEach((el) => {
		el.setAttribute('data-ld-done', '1');
		const spec = decodeURI(el.getAttribute('data-spec') || '');
		const caption = el.getAttribute('data-caption') || undefined;
		void fetchLive(spec).then((result) => {
			el.innerHTML = renderLiveTable(result, { caption });
		});
	});
}
