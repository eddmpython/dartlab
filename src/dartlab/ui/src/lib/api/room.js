/**
 * Room 협업 세션 API 클라이언트 — 서버 /api/room/* 엔드포인트 1:1 래핑.
 */
import { BASE } from "./http.js";

/** 현재 룸 상태 조회. 룸이 없으면 null 반환. */
export async function roomState() {
	const res = await fetch(`${BASE}/api/room/state`);
	if (res.status === 404) return null;
	if (!res.ok) throw new Error(`room/state 실패: ${res.status}`);
	return res.json();
}

/** 룸 참여. { memberId, roomId, state } 반환. */
export async function roomJoin(name) {
	const res = await fetch(`${BASE}/api/room/join`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ name }),
	});
	if (!res.ok) throw new Error(`room/join 실패: ${res.status}`);
	return res.json();
}

/** 룸 퇴장. */
export async function roomLeave(memberId) {
	const res = await fetch(`${BASE}/api/room/leave`, {
		method: "POST",
		headers: _memberHeaders(memberId),
	});
	if (!res.ok) throw new Error(`room/leave 실패: ${res.status}`);
	return res.json();
}

/** 프레즌스 heartbeat (15초 간격). */
export async function roomHeartbeat(memberId) {
	const res = await fetch(`${BASE}/api/room/heartbeat`, {
		method: "POST",
		headers: _memberHeaders(memberId),
	});
	if (!res.ok) throw new Error(`room/heartbeat 실패: ${res.status}`);
	return res.json();
}

/** SSE 브로드캐스트 스트림. EventSource 반환. */
export function roomStream(memberId) {
	return new EventSource(`${BASE}/api/room/stream?member=${encodeURIComponent(memberId)}`);
}

/** AI 질문 → 전체 브로드캐스트. */
export async function roomAsk(memberId, question, company) {
	const body = { question };
	if (company) body.company = company;
	const res = await fetch(`${BASE}/api/room/ask`, {
		method: "POST",
		headers: { "Content-Type": "application/json", "x-room-member": memberId },
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error(`room/ask 실패: ${res.status}`);
	return res.json();
}

/** 네비게이션 동기화. */
export async function roomNavigate(memberId, nav) {
	const res = await fetch(`${BASE}/api/room/navigate`, {
		method: "POST",
		headers: { "Content-Type": "application/json", "x-room-member": memberId },
		body: JSON.stringify(nav),
	});
	if (!res.ok) throw new Error(`room/navigate 실패: ${res.status}`);
	return res.json();
}

/** 채팅 메시지 전송. */
export async function roomChat(memberId, text) {
	const res = await fetch(`${BASE}/api/room/chat`, {
		method: "POST",
		headers: { "Content-Type": "application/json", "x-room-member": memberId },
		body: JSON.stringify({ text }),
	});
	if (!res.ok) throw new Error(`room/chat 실패: ${res.status}`);
	return res.json();
}

/** 이모지 반응. */
export async function roomReact(memberId, emoji, targetEvent) {
	const body = { emoji };
	if (targetEvent) body.targetEvent = targetEvent;
	const res = await fetch(`${BASE}/api/room/react`, {
		method: "POST",
		headers: { "Content-Type": "application/json", "x-room-member": memberId },
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error(`room/react 실패: ${res.status}`);
	return res.json();
}

// ── 내부 헬퍼 ──

function _memberHeaders(memberId) {
	return { "Content-Type": "application/json", "x-room-member": memberId };
}
