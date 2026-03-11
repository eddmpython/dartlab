/**
 * DartLab API 클라이언트
 */

const BASE = "";  // 같은 origin (proxy or production)

/** LLM provider 상태 확인 */
export async function fetchStatus() {
	const res = await fetch(`${BASE}/api/status`);
	if (!res.ok) throw new Error("상태 확인 실패");
	return res.json();
}

/** LLM provider 설정 (api_key, base_url 지원) */
export async function configure(provider, model = null, apiKey = null) {
	const body = { provider };
	if (model) body.model = model;
	if (apiKey) body.api_key = apiKey;
	const res = await fetch(`${BASE}/api/configure`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	});
	if (!res.ok) throw new Error("설정 실패");
	return res.json();
}

/** Provider별 모델 목록 조회 */
export async function fetchModels(provider) {
	const res = await fetch(`${BASE}/api/models/${encodeURIComponent(provider)}`);
	if (!res.ok) return { models: [] };
	return res.json();
}

/** Ollama 모델 다운로드 (SSE 진행률) */
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
					} catch {}
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

/** ChatGPT OAuth 인증 시작 */
export async function oauthAuthorize() {
	const res = await fetch(`${BASE}/api/oauth/authorize`);
	if (!res.ok) throw new Error("OAuth 인증 시작 실패");
	return res.json();
}

/** OAuth 인증 완료 여부 폴링 */
export async function oauthStatus() {
	const res = await fetch(`${BASE}/api/oauth/status`);
	if (!res.ok) return { done: false };
	return res.json();
}

/** OAuth 로그아웃 */
export async function oauthLogout() {
	const res = await fetch(`${BASE}/api/oauth/logout`, { method: "POST" });
	if (!res.ok) throw new Error("로그아웃 실패");
	return res.json();
}

/** Excel 내보내기 가능한 모듈 목록 */
export async function fetchExportModules(stockCode) {
	const res = await fetch(`${BASE}/api/export/modules/${encodeURIComponent(stockCode)}`);
	if (!res.ok) throw new Error("모듈 목록 조회 실패");
	return res.json();
}

/** 데이터 소스 트리 (registry 기반 전체 소스) */
export async function fetchExportSources(stockCode) {
	const res = await fetch(`${BASE}/api/export/sources/${encodeURIComponent(stockCode)}`);
	if (!res.ok) throw new Error("소스 목록 조회 실패");
	return res.json();
}

/** 템플릿 목록 (프리셋 + 커스텀) */
export async function fetchTemplates() {
	const res = await fetch(`${BASE}/api/export/templates`);
	if (!res.ok) throw new Error("템플릿 조회 실패");
	return res.json();
}

/** 템플릿 저장 */
export async function saveTemplate(template) {
	const res = await fetch(`${BASE}/api/export/templates`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(template),
	});
	if (!res.ok) throw new Error("템플릿 저장 실패");
	return res.json();
}

/** 템플릿 삭제 */
export async function deleteTemplate(templateId) {
	const res = await fetch(`${BASE}/api/export/templates/${encodeURIComponent(templateId)}`, {
		method: "DELETE",
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "템플릿 삭제 실패");
	}
	return res.json();
}

/** Excel 파일 다운로드 */
export async function downloadExcel(stockCode, modules = null, templateId = null) {
	let url = `${BASE}/api/export/excel/${encodeURIComponent(stockCode)}`;
	const params = new URLSearchParams();
	if (templateId) {
		params.set("template_id", templateId);
	} else if (modules && modules.length > 0) {
		params.set("modules", modules.join(","));
	}
	const qs = params.toString();
	if (qs) url += `?${qs}`;
	const res = await fetch(url);
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "Excel 다운로드 실패");
	}
	const blob = await res.blob();
	const disposition = res.headers.get("content-disposition") || "";
	const match = disposition.match(/filename\*?=(?:UTF-8'')?["']?([^;"'\n]+)/i);
	const filename = match ? decodeURIComponent(match[1]) : `${stockCode}.xlsx`;
	const a = document.createElement("a");
	a.href = URL.createObjectURL(blob);
	a.download = filename;
	a.click();
	URL.revokeObjectURL(a.href);
	return filename;
}

/** 경량 데이터 소스 목록 (빠름 — registry 메타만 확인) */
export async function fetchDataSources(stockCode) {
	const res = await fetch(`${BASE}/api/data/sources/${encodeURIComponent(stockCode)}`);
	if (!res.ok) throw new Error("소스 목록 조회 실패");
	return res.json();
}

/** 데이터 미리보기 */
export async function fetchDataPreview(stockCode, module, maxRows = 50) {
	const params = new URLSearchParams();
	if (maxRows !== 50) params.set("max_rows", String(maxRows));
	const qs = params.toString();
	const url = `${BASE}/api/data/preview/${encodeURIComponent(stockCode)}/${encodeURIComponent(module)}${qs ? "?" + qs : ""}`;
	const res = await fetch(url);
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "미리보기 실패");
	}
	return res.json();
}

/** 종목 검색 */
export async function searchCompany(query) {
	const res = await fetch(`${BASE}/api/search?q=${encodeURIComponent(query)}`);
	if (!res.ok) throw new Error("검색 실패");
	return res.json();
}

/** 기업 정보 */
export async function fetchCompany(code) {
	const res = await fetch(`${BASE}/api/company/${code}`);
	if (!res.ok) throw new Error("기업 정보 조회 실패");
	return res.json();
}

/** LLM 질문 (동기) */
export async function ask(company, question, options = {}) {
	const body = { company, question, stream: false, ...options };
	const res = await fetch(`${BASE}/api/ask`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.detail || "질문 실패");
	}
	return res.json();
}

/**
 * LLM 질문 (SSE 스트리밍)
 * @param {string} company
 * @param {string} question
 * @param {object} options
 * @param {function} onMeta - meta 이벤트 콜백
 * @param {function} onSnapshot - snapshot 이벤트 콜백 (핵심 수치 즉시 표시)
 * @param {function} onContext - context 이벤트 콜백 (모듈별, 여러 번 호출됨)
 * @param {function} onToolCall - tool_call 이벤트 콜백 (도구 호출)
 * @param {function} onToolResult - tool_result 이벤트 콜백 (도구 결과)
 * @param {function} onChunk - chunk 이벤트 콜백
 * @param {function} onDone - done 이벤트 콜백
 * @param {function} onError - error 이벤트 콜백
 */
export function askStream(company, question, options = {}, { onMeta, onSnapshot, onContext, onSystemPrompt, onToolCall, onToolResult, onChunk, onDone, onError }, history = null) {
	const body = { question, stream: true, ...options };
	if (company) body.company = company;
	if (history && history.length > 0) body.history = history;

	const controller = new AbortController();

	fetch(`${BASE}/api/ask`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(body),
		signal: controller.signal,
	})
		.then(async (res) => {
			if (!res.ok) {
				const err = await res.json().catch(() => ({}));
				onError?.(err.detail || "스트리밍 실패");
				return;
			}

			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let buffer = "";
			let doneFired = false;
			let currentEvent = null;

			while (true) {
				const { done, value } = await reader.read();
				if (done) break;

				buffer += decoder.decode(value, { stream: true });
				const lines = buffer.split("\n");
				buffer = lines.pop() || "";

				for (const line of lines) {
					if (line.startsWith("event:")) {
						currentEvent = line.slice(6).trim();
					} else if (line.startsWith("data:") && currentEvent) {
						const data = line.slice(5).trim();
						try {
							const parsed = JSON.parse(data);
							if (currentEvent === "meta") onMeta?.(parsed);
							else if (currentEvent === "snapshot") onSnapshot?.(parsed);
							else if (currentEvent === "context") onContext?.(parsed);
							else if (currentEvent === "system_prompt") onSystemPrompt?.(parsed);
							else if (currentEvent === "tool_call") onToolCall?.(parsed);
							else if (currentEvent === "tool_result") onToolResult?.(parsed);
							else if (currentEvent === "chunk") onChunk?.(parsed.text);
							else if (currentEvent === "error") onError?.(parsed.error, parsed.action, parsed.detail);
							else if (currentEvent === "done") { if (!doneFired) { doneFired = true; onDone?.(); } }
						} catch {
							// skip malformed JSON
						}
						currentEvent = null;
					}
				}
			}

			if (!doneFired) { doneFired = true; onDone?.(); }
		})
		.catch((err) => {
			if (err.name !== "AbortError") {
				onError?.(err.message);
			}
		});

	return { abort: () => controller.abort() };
}
