/**
 * DartLab API 클라이언트
 */
import { BASE, fetchPack } from "./api/http.js";

export {
	codexLogout,
	configure,
	fetchAiProfile,
	fetchAiSuggestions,
	fetchModels,
	fetchStatus,
	oauthAuthorize,
	oauthLogout,
	oauthStatus,
	pullOllamaModel,
	subscribeAiProfileEvents,
	updateAiProfile,
	updateAiSecret,
	validateProvider,
} from "./api/ai.js";

export {
	roomState,
	roomJoin,
	roomLeave,
	roomHeartbeat,
	roomStream,
	roomAsk,
	roomNavigate,
	roomChat,
	roomReact,
} from "./api/room.js";

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

/** 기업 기본 정보 + surface 안내 */
export async function fetchCompany(code) {
	const res = await fetch(`${BASE}/api/company/${code}`);
	if (!res.ok) throw new Error("기업 정보 조회 실패");
	return res.json();
}

/** company index */
export async function fetchCompanyIndex(code) {
	const res = await fetch(`${BASE}/api/company/${code}/index`);
	if (!res.ok) throw new Error("company index 조회 실패");
	return res.json();
}

/** company topic payload — block=null이면 블록 목차, block=N이면 실제 데이터 */
export async function fetchCompanyShow(code, topic, block = null, raw = false) {
	const params = new URLSearchParams();
	if (block !== null) params.set("block", block);
	if (raw) params.set("raw", "true");
	const qs = params.toString() ? `?${params}` : "";
	const res = await fetch(`${BASE}/api/company/${code}/show/${encodeURIComponent(topic)}${qs}`);
	if (!res.ok) throw new Error("company topic 조회 실패");
	return res.json();
}

/** company topic 전체 블록 일괄 조회 — N+1 호출 제거 */
export async function fetchCompanyShowAll(code, topic) {
	const res = await fetch(`${BASE}/api/company/${code}/show/${encodeURIComponent(topic)}/all`);
	if (!res.ok) throw new Error("company topic 일괄 조회 실패");
	return res.json();
}

/** company topic provenance */
export async function fetchCompanyTrace(code, topic) {
	const res = await fetch(`${BASE}/api/company/${code}/trace/${encodeURIComponent(topic)}`);
	if (!res.ok) throw new Error("company trace 조회 실패");
	return res.json();
}

/** company sections 원본 (MessagePack) */
export async function fetchCompanySections(code) {
	return fetchPack(`${BASE}/api/company/${code}/sections`);
}

/** company diff 요약 */
export async function fetchCompanyDiff(code) {
	const res = await fetch(`${BASE}/api/company/${code}/diff`);
	if (!res.ok) throw new Error("diff 조회 실패");
	return res.json();
}

/** 초기 로드 배치 — toc + 첫 topic viewer + diffSummary 1회 왕복 (MessagePack) */
export async function fetchCompanyInit(code) {
	return fetchPack(`${BASE}/api/company/${encodeURIComponent(code)}/init`);
}

/** 뷰어용 목차 — chapter/topic 트리 */
export async function fetchCompanyToc(code) {
	const res = await fetch(`${BASE}/api/company/${code}/toc`);
	if (!res.ok) throw new Error("목차 조회 실패");
	return res.json();
}

/** 뷰어 전용 topic 데이터 — viewerBlocks + textDocument (MessagePack) */
export async function fetchCompanyViewer(code, topic, period = null) {
	const params = period ? `?period=${encodeURIComponent(period)}` : "";
	return fetchPack(`${BASE}/api/company/${code}/viewer/${encodeURIComponent(topic)}${params}`);
}

/** 여러 topic의 viewer 데이터를 한 번에 반환 — chapter 확장 시 N+1 제거 */
export async function fetchCompanyViewerBatch(code, topics) {
	const res = await fetch(`${BASE}/api/company/${encodeURIComponent(code)}/viewer/batch`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ topics }),
	});
	if (!res.ok) throw new Error("batch viewer 조회 실패");
	return res.json();
}

/** diff 요약 — changeRate + added/removed 미리보기 */
export async function fetchCompanyDiffSummary(code, topic) {
	const res = await fetch(`${BASE}/api/company/${code}/diff/${encodeURIComponent(topic)}/summary`);
	if (!res.ok) throw new Error("diff summary 조회 실패");
	return res.json();
}

/** company topic diff (줄 단위) */
export async function fetchCompanyTopicDiff(code, topic, fromPeriod, toPeriod) {
	const params = new URLSearchParams({ from: fromPeriod, to: toPeriod });
	const res = await fetch(`${BASE}/api/company/${code}/diff/${encodeURIComponent(topic)}?${params}`);
	if (!res.ok) throw new Error("topic diff 조회 실패");
	return res.json();
}

/** 뷰어 내 텍스트 검색 — sections 전체에서 substring 검색 */
export async function fetchCompanySearch(code, query) {
	const params = new URLSearchParams({ q: query });
	const res = await fetch(`${BASE}/api/company/${encodeURIComponent(code)}/search?${params}`);
	if (!res.ok) throw new Error("검색 실패");
	return res.json();
}

/** MiniSearch 인덱스용 flat document list (MessagePack) */
export async function fetchSearchIndex(code) {
	return fetchPack(`${BASE}/api/company/${encodeURIComponent(code)}/searchIndex`);
}

/** 7영역 인사이트 등급 + 이상치 분석 */
export async function fetchCompanyInsights(code) {
	const res = await fetch(`${BASE}/api/company/${encodeURIComponent(code)}/insights`);
	if (!res.ok) throw new Error("인사이트 조회 실패");
	return res.json();
}

/** Ego network — 회사 중심 관계 그래프 */
export async function fetchCompanyNetwork(code) {
	const res = await fetch(`${BASE}/api/company/${encodeURIComponent(code)}/network`);
	if (!res.ok) throw new Error("네트워크 조회 실패");
	return res.json();
}

/** topic AI 요약 (SSE 스트리밍) */
export function streamTopicSummary(code, topic, { onContext, onChunk, onDone, onError, provider, model } = {}) {
	const controller = new AbortController();
	const params = new URLSearchParams();
	if (provider) params.set("provider", provider);
	if (model) params.set("model", model);
	const qs = params.toString();
	const url = `${BASE}/api/company/${encodeURIComponent(code)}/summary/${encodeURIComponent(topic)}${qs ? `?${qs}` : ""}`;
	fetch(url, {
		signal: controller.signal,
	})
		.then(async (res) => {
			if (!res.ok) {
				onError?.("요약 생성 실패");
				return;
			}
			const reader = res.body.getReader();
			const decoder = new TextDecoder();
			let buffer = "";
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
						try {
							const parsed = JSON.parse(line.slice(5).trim());
							if (currentEvent === "context") onContext?.(parsed);
							else if (currentEvent === "chunk") onChunk?.(parsed.text);
							else if (currentEvent === "error") onError?.(parsed.error);
							else if (currentEvent === "done") onDone?.();
						} catch (e) { console.warn("SSE parse:", e); }
						currentEvent = null;
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
 * @param {function} onChart - chart 이벤트 콜백 (ChartSpec 배열)
 * @param {function} onChunk - chunk 이벤트 콜백
 * @param {function} onDone - done 이벤트 콜백
 * @param {function} onError - error 이벤트 콜백
 * @param {function} onUiAction - ui_action 이벤트 콜백 (canonical action)
 */
export function askStream(company, question, options = {}, { onMeta, onSnapshot, onContext, onSystemPrompt, onToolCall, onToolResult, onChart, onChunk, onDone, onError, onUiAction }, history = null) {
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
							else if (currentEvent === "chart") onChart?.(parsed);
							else if (currentEvent === "ui_action") onUiAction?.(parsed);
							else if (currentEvent === "error") onError?.(parsed.error, parsed.action, parsed.detail);
							else if (currentEvent === "done") { if (!doneFired) { doneFired = true; onDone?.(parsed); } }
						} catch (e) {
							console.warn("SSE JSON parse:", e);
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
