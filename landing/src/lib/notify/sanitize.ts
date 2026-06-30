// 알림 sink 정화 · SW 렌더 직전 방어심층(authoritative 정화는 발행 러너 .github/scripts/notify/sanitize.py).
// 알림 body 는 OS 알림센터 + 화면에 렌더되는 sink. LLM wrap_external 부적용, 전용 정화.
// 설계: mainPlan/watcher-notify-platform/02-hub-d1-receiving.md 6절.

// C0/C1 제어 + zero-width + RTL/LTR override·embedding·isolate(양방향 스푸핑) + BOM.
// U+0009 ~ U+000D (tab·LF·VT·FF·CR) 는 보존 · 아래 정규식이 단일 공백으로 정규화(단어 붙음 방지).
// 소스 순수 ASCII 유지 위해 이스케이프 문자열로 구성(보이지 않는 문자 리터럴 금지).
const STRIP_RE = new RegExp(
	'[\\u0000-\\u0008\\u000E-\\u001F\\u007F-\\u009F\\u200B-\\u200F\\u202A-\\u202E\\u2060-\\u2064\\u2066-\\u2069\\uFEFF]',
	'g'
);

/** 제어·zero-width·양방향 제어문자 strip + 공백 정규화 + 길이 cap. textContent 렌더 전제. */
export function sanitizeNotificationText(text: unknown, maxLen = 120): string {
	const s = String(text ?? '')
		.replace(STRIP_RE, '')
		.replace(/\s+/g, ' ')
		.trim();
	return s.length > maxLen ? s.slice(0, maxLen - 1) + '…' : s;
}

/**
 * 클릭 목적지 = 항상 dartlab 자기 라우트(same-origin)만. 외부 originallink 직링크 차단(피싱).
 * payload.url 은 app-path(base 없음) -> base 접두 후 same-origin 검증. 불일치/파싱실패 -> base 루트.
 */
export function safeSelfRoute(rawUrl: unknown, base: string, origin: string): string {
	const root = base.replace(/\/$/, '') + '/';
	if (!rawUrl) return root; // 빈/널 -> 홈(BASE 루트)
	try {
		const dest = new URL(base.replace(/\/$/, '') + String(rawUrl), origin);
		if (dest.origin !== origin) return root;
		return dest.pathname + dest.search;
	} catch {
		return root;
	}
}
