import { BASE } from "./http.js";

export async function fetchStatus(provider = null, probe = true) {
	const params = new URLSearchParams();
	if (provider) params.set("provider", provider);
	if (!probe) params.set("probe", "0");
	const qs = params.toString();
	const res = await fetch(`${BASE}/api/status${qs ? `?${qs}` : ""}`);
	if (!res.ok) throw new Error("상태 확인 실패");
	return res.json();
}

export async function fetchAiSuggestions(stockCode) {
	const res = await fetch(`${BASE}/api/suggest?stockCode=${encodeURIComponent(stockCode)}`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "추천 질문 조회 실패");
	}
	return res.json();
}

export async function validateProvider(provider, model = null, apiKey = null) {
	const body = { provider };
	if (model) body.model = model;
	if (apiKey) body.api_key = apiKey;
	const res = await fetch(`${BASE}/api/provider/validate`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error("설정 실패");
	return res.json();
}

export const configure = validateProvider;

export async function fetchAiProfile() {
	const res = await fetch(`${BASE}/api/ai/profile`);
	if (!res.ok) throw new Error("AI profile 조회 실패");
	return res.json();
}

export async function updateAiProfile(patch) {
	const res = await fetch(`${BASE}/api/ai/profile`, {
		method: "PUT",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(patch),
	});
	if (!res.ok) throw new Error("AI profile 저장 실패");
	return res.json();
}

export async function updateAiSecret(provider, apiKey = null, clear = false) {
	const res = await fetch(`${BASE}/api/ai/profile/secrets`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ provider, api_key: apiKey, clear }),
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "AI secret 저장 실패");
	}
	return res.json();
}

export async function validateDartKey(apiKey) {
	const res = await fetch(`${BASE}/api/openapi/dart-key/validate`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ api_key: apiKey }),
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "OpenDART 키 검증 실패");
	}
	return res.json();
}

export async function saveDartKey(apiKey) {
	const res = await fetch(`${BASE}/api/openapi/dart-key`, {
		method: "PUT",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ api_key: apiKey }),
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "OpenDART 키 저장 실패");
	}
	return res.json();
}

export async function deleteDartKey() {
	const res = await fetch(`${BASE}/api/openapi/dart-key`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "OpenDART 키 삭제 실패");
	}
	return res.json();
}

export function subscribeAiProfileEvents({ onProfileChanged, onError } = {}) {
	const es = new EventSource(`${BASE}/api/ai/profile/events`);
	es.addEventListener("profile_changed", (event) => {
		try {
			const payload = JSON.parse(event.data);
			onProfileChanged?.(payload);
		} catch (err) {
			console.warn("profile_changed parse:", err);
		}
	});
	es.onerror = (err) => {
		onError?.(err);
	};
	return {
		close() { es.close(); },
	};
}

export async function fetchModels(provider) {
	const res = await fetch(`${BASE}/api/models/${encodeURIComponent(provider)}`);
	if (!res.ok) return { models: [] };
	return res.json();
}

export function pullOllamaModel(modelName, { onProgress, onDone, onError }) {
	const controller = new AbortController();
	fetch(`${BASE}/api/ollama/pull`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ model: modelName }),
		signal: controller.signal,
	})
	.then(async (res) => {
		if (!res.ok) { onError?.("다운로드 실패"); return; }
		const reader = res.body.getReader();
		const decoder = new TextDecoder();
		let buffer = "";
		while (true) {
			const { done, value } = await reader.read();
			if (done) break;
			buffer += decoder.decode(value, { stream: true });
			const lines = buffer.split("\n");
			buffer = lines.pop() || "";
			for (const line of lines) {
				if (line.startsWith("data:")) {
					try {
						const data = JSON.parse(line.slice(5).trim());
						if (data.total && data.completed !== undefined) {
							onProgress?.({ total: data.total, completed: data.completed, status: data.status });
						} else if (data.status) {
							onProgress?.({ status: data.status });
						}
					} catch (e) { console.warn("SSE parse:", e); }
				}
			}
		}
		onDone?.();
	})
	.catch((err) => {
		if (err.name !== "AbortError") onError?.(err.message);
	});
	return { abort: () => controller.abort() };
}

export async function codexLogout() {
	const res = await fetch(`${BASE}/api/codex/logout`, { method: "POST" });
	if (!res.ok) throw new Error("Codex 로그아웃 실패");
	return res.json();
}

export async function oauthAuthorize() {
	const res = await fetch(`${BASE}/api/oauth/authorize`);
	if (!res.ok) throw new Error("OAuth 로그인 시작 실패");
	return res.json();
}

export async function oauthStatus() {
	const res = await fetch(`${BASE}/api/oauth/status`);
	if (!res.ok) throw new Error("OAuth 상태 확인 실패");
	return res.json();
}

export async function oauthLogout() {
	const res = await fetch(`${BASE}/api/oauth/logout`, { method: "POST" });
	if (!res.ok) throw new Error("OAuth 로그아웃 실패");
	return res.json();
}

export async function geminiOauthAuthorize() {
	const res = await fetch(`${BASE}/api/gemini/oauth/authorize`);
	if (!res.ok) throw new Error("Gemini OAuth 로그인 시작 실패");
	return res.json();
}

export async function geminiOauthStatus() {
	const res = await fetch(`${BASE}/api/gemini/oauth/status`);
	if (!res.ok) throw new Error("Gemini OAuth 상태 확인 실패");
	return res.json();
}

export async function geminiOauthLogout() {
	const res = await fetch(`${BASE}/api/gemini/oauth/logout`, { method: "POST" });
	if (!res.ok) throw new Error("Gemini OAuth 로그아웃 실패");
	return res.json();
}

export async function startChannelConnection(platform, payload = {}) {
	const res = await fetch(`${BASE}/api/channels/${encodeURIComponent(platform)}/start`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload),
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || `${platform} 채널 시작 실패`);
	}
	return res.json();
}

export async function stopChannelConnection(platform) {
	const res = await fetch(`${BASE}/api/channels/${encodeURIComponent(platform)}/stop`, {
		method: "POST",
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || `${platform} 채널 종료 실패`);
	}
	return res.json();
}
