/**
 * Room 협업 세션 상태 관리 — SSE fan-out + POST-back.
 *
 * dartlab share 터널 모드에서 활성화되며,
 * 멤버 관리, 채팅, AI 분석 브로드캐스트, 네비게이션 동기화를 담당한다.
 */
import {
	roomState,
	roomJoin,
	roomLeave,
	roomHeartbeat,
	roomStream,
	roomAsk,
	roomNavigate,
	roomChat,
	roomReact,
} from "$lib/api/room.js";

const HEARTBEAT_INTERVAL = 15_000;
const SSE_RECONNECT_DELAY = 2_000;
const SSE_MAX_RETRIES = 5;
const REACTION_TTL = 3_000;
const NAME_STORAGE_KEY = "dartlab-room-name";

export function createRoomStore(ui) {
	// ── 상태 ──
	let roomAvailable = $state(false);
	let joined = $state(false);
	let memberId = $state(null);
	let roomId = $state(null);
	let members = $state([]);
	let chatMessages = $state([]);
	let analyzing = $state(false);
	let analysisStream = $state(null);
	let navState = $state(null);
	let unreadCount = $state(0);
	let reactions = $state([]);
	let isRoomView = $state(false); // 사용자가 Room 탭을 보고 있는지

	// ── 내부 ──
	let _sse = null;
	let _heartbeatTimer = null;
	let _sseRetries = 0;
	let _navFromRemote = false; // 에코 루프 방지

	// ── 메서드 ──

	async function checkRoom() {
		try {
			const state = await roomState();
			roomAvailable = state !== null;
			if (state) {
				roomId = state.roomId || null;
				members = state.members || [];
			}
		} catch {
			roomAvailable = false;
		}
	}

	async function join(name) {
		try {
			const res = await roomJoin(name);
			memberId = res.memberId || res.member_id;
			roomId = res.roomId || res.room_id;
			joined = true;
			// 초기 상태 반영
			if (res.state) {
				members = res.state.members || [];
				chatMessages = (res.state.chatHistory || []).map(_normChat);
				if (res.state.navState) navState = res.state.navState;
			}
			// localStorage에 이름 저장
			try { localStorage.setItem(NAME_STORAGE_KEY, name); } catch {}
			// SSE + heartbeat 시작
			_startSSE();
			_startHeartbeat();
		} catch (err) {
			ui?.showToast?.(`룸 참여 실패: ${err.message}`, "error");
			throw err;
		}
	}

	async function leave() {
		_stopSSE();
		_stopHeartbeat();
		if (memberId) {
			try { await roomLeave(memberId); } catch {}
		}
		joined = false;
		memberId = null;
		members = [];
		chatMessages = [];
		analysisStream = null;
		analyzing = false;
		navState = null;
		unreadCount = 0;
	}

	async function sendChat(text) {
		if (!memberId || !text.trim()) return;
		try {
			await roomChat(memberId, text.trim());
		} catch (err) {
			ui?.showToast?.(`메시지 전송 실패: ${err.message}`, "error");
		}
	}

	async function sendReaction(emoji, targetEvent) {
		if (!memberId) return;
		try {
			await roomReact(memberId, emoji, targetEvent);
		} catch {}
	}

	async function navigate(nav) {
		if (!memberId || _navFromRemote) return;
		try {
			await roomNavigate(memberId, nav);
		} catch {}
	}

	async function askAI(question, company) {
		if (!memberId) return;
		try {
			await roomAsk(memberId, question, company);
		} catch (err) {
			ui?.showToast?.(`분석 요청 실패: ${err.message}`, "error");
		}
	}

	function getSavedName() {
		try { return localStorage.getItem(NAME_STORAGE_KEY) || ""; } catch { return ""; }
	}

	function markRoomViewed() {
		isRoomView = true;
		unreadCount = 0;
	}

	function markRoomHidden() {
		isRoomView = false;
	}

	// ── SSE ──

	function _startSSE() {
		if (_sse) _sse.close();
		_sseRetries = 0;
		_connectSSE();
	}

	function _connectSSE() {
		if (!memberId) return;
		_sse = roomStream(memberId);
		_sse.onmessage = (e) => {
			_sseRetries = 0;
			try {
				const msg = JSON.parse(e.data);
				_handleSSE(msg);
			} catch {}
		};
		_sse.onerror = () => {
			_sse?.close();
			_sse = null;
			if (_sseRetries < SSE_MAX_RETRIES && joined) {
				_sseRetries++;
				setTimeout(_connectSSE, SSE_RECONNECT_DELAY);
			}
		};
	}

	function _stopSSE() {
		if (_sse) { _sse.close(); _sse = null; }
	}

	function _handleSSE(msg) {
		const { event, data } = msg;
		if (!event) return;

		switch (event) {
			case "member_join":
				members = [...members.filter(m => m.memberId !== data.memberId), data];
				if (data.memberId !== memberId) {
					ui?.showToast?.(`${data.name}님이 참여했습니다`, "success", 3000);
				}
				break;
			case "member_leave":
				members = members.filter(m => m.memberId !== data.memberId);
				ui?.showToast?.(`${data.name}님이 퇴장했습니다`, "info", 3000);
				break;
			case "chat":
				chatMessages = [...chatMessages, _normChat(data)];
				if (!isRoomView && data.memberId !== memberId) {
					unreadCount++;
				}
				break;
			case "react": {
				const rid = Date.now() + Math.random();
				const r = { ...data, _id: rid };
				reactions = [...reactions, r];
				setTimeout(() => {
					reactions = reactions.filter(x => x._id !== rid);
				}, REACTION_TTL);
				break;
			}
			case "navigate":
				_navFromRemote = true;
				navState = { ...data, _ts: Date.now() };
				// 다음 틱에서 플래그 해제
				setTimeout(() => { _navFromRemote = false; }, 50);
				break;
			case "ask_start":
				analyzing = true;
				analysisStream = {
					question: data.question,
					company: data.company,
					memberName: data.memberName,
					chunks: "",
					meta: null,
					snapshot: null,
					contexts: [],
					done: false,
				};
				break;
			case "meta":
				if (analysisStream) analysisStream = { ...analysisStream, meta: data };
				break;
			case "snapshot":
				if (analysisStream) analysisStream = { ...analysisStream, snapshot: data };
				break;
			case "context":
				if (analysisStream) {
					analysisStream = {
						...analysisStream,
						contexts: [...analysisStream.contexts, data],
					};
				}
				break;
			case "chunk":
				if (analysisStream) {
					analysisStream = {
						...analysisStream,
						chunks: analysisStream.chunks + (data.text || ""),
					};
				}
				break;
			case "done":
				analyzing = false;
				if (analysisStream) {
					analysisStream = { ...analysisStream, done: true, responseMeta: data };
				}
				break;
			case "error":
				analyzing = false;
				ui?.showToast?.(data.error || "분석 중 오류 발생", "error");
				break;
		}
	}

	// ── Heartbeat ──

	function _startHeartbeat() {
		_stopHeartbeat();
		_heartbeatTimer = setInterval(async () => {
			if (!memberId) return;
			try { await roomHeartbeat(memberId); } catch {}
		}, HEARTBEAT_INTERVAL);
	}

	function _stopHeartbeat() {
		if (_heartbeatTimer) { clearInterval(_heartbeatTimer); _heartbeatTimer = null; }
	}

	// ── 채팅 메시지 정규화 ──

	function _normChat(data) {
		return {
			memberId: data.memberId || data.member_id,
			name: data.name,
			text: data.text,
			timestamp: data.timestamp || Date.now() / 1000,
		};
	}

	// ── 반환 ──

	return {
		// 상태
		get roomAvailable() { return roomAvailable; },
		get joined() { return joined; },
		get memberId() { return memberId; },
		get roomId() { return roomId; },
		get members() { return members; },
		get chatMessages() { return chatMessages; },
		get analyzing() { return analyzing; },
		get analysisStream() { return analysisStream; },
		get navState() { return navState; },
		get unreadCount() { return unreadCount; },
		get reactions() { return reactions; },
		get isNavFromRemote() { return _navFromRemote; },

		// 메서드
		checkRoom,
		join,
		leave,
		sendChat,
		sendReaction,
		navigate,
		askAI,
		getSavedName,
		markRoomViewed,
		markRoomHidden,
	};
}
