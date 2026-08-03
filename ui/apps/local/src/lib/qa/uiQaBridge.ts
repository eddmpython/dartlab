import { goto } from '$app/navigation';

type QaCommand = {
	commandId: string;
	action: 'click' | 'fill' | 'key' | 'navigate' | 'scroll' | 'snapshot';
	targetQaId: string | null;
	value: string | null;
	key: string | null;
	path: string | null;
	behavior: ScrollBehavior | null;
	block: ScrollLogicalPosition | null;
};

type QaDiagnostic = {
	code: 'duplicate-qa-id' | 'horizontal-overflow' | 'offscreen-element' | 'console-error';
	severity: 'info' | 'warning' | 'error';
	message: string;
	qaId?: string;
};

const API_ROOT = '/api/ui-qa';
const ALLOWED_KEYS = new Set(['Enter', 'Escape', 'Tab', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space']);
const MAX_TEXT = 500;

function redactSecrets(value: string): string {
	return value
		.replace(/\bBearer\s+[A-Za-z0-9._~-]+/gi, 'Bearer [redacted]')
		.replace(/\bsk-[A-Za-z0-9_-]{8,}\b/g, '[redacted]')
		.replace(/((?:api[_ -]?key|token|password|secret)\s*[:=]\s*)[^\s]+/gi, '$1[redacted]');
}

function compactText(value: string | null | undefined, limit = MAX_TEXT): string | null {
	const compact = value?.replace(/\s+/g, ' ').trim();
	return compact ? redactSecrets(compact).slice(0, limit) : null;
}

function rectOf(rect: DOMRect) {
	return { x: rect.x, y: rect.y, width: rect.width, height: rect.height };
}

function qaElement(qaId: string): HTMLElement | null {
	for (const candidate of document.querySelectorAll<HTMLElement>('[data-qa]')) {
		if (candidate.dataset.qa === qaId) return candidate;
	}
	return null;
}

function elementLabel(element: HTMLElement): string | null {
	const direct = element.getAttribute('aria-label');
	if (direct) return compactText(direct, 300);
	const labelledBy = element.getAttribute('aria-labelledby');
	if (!labelledBy) return null;
	return compactText(
		labelledBy
			.split(/\s+/)
			.map((id) => document.getElementById(id)?.textContent ?? '')
			.join(' '),
		300
	);
}

function collectSnapshot(consoleErrors: string[]) {
	const diagnostics: QaDiagnostic[] = [];
	const counts = new Map<string, number>();
	const elements = Array.from(document.querySelectorAll<HTMLElement>('[data-qa]')).slice(0, 500).map((element) => {
		const qaId = element.dataset.qa ?? '';
		counts.set(qaId, (counts.get(qaId) ?? 0) + 1);
		const rect = element.getBoundingClientRect();
		const style = getComputedStyle(element);
		const rendered = style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity) !== 0;
		const visible = rendered && rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.right > 0 && rect.top < innerHeight && rect.left < innerWidth;
		if (rendered && rect.width > 0 && rect.height > 0 && !visible) {
			diagnostics.push({
				code: 'offscreen-element',
				severity: 'info',
				message: `검수 대상 ${qaId}이 현재 viewport 밖에 있습니다.`,
				qaId
			});
		}

		let checked: boolean | null = null;
		if (element instanceof HTMLInputElement && ['checkbox', 'radio'].includes(element.type)) checked = element.checked;
		let safeValue: string | null = null;
		if (
			element.dataset.qaValue === 'safe' &&
			(element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) &&
			!(element instanceof HTMLInputElement && element.type === 'password')
		) {
			safeValue = redactSecrets(element.value).slice(0, 2000);
		}

		return {
			qaId,
			tag: element.tagName.toLowerCase(),
			role: element.getAttribute('role'),
			label: elementLabel(element),
			text: compactText(element.innerText),
			disabled: 'disabled' in element ? Boolean((element as HTMLButtonElement).disabled) : element.getAttribute('aria-disabled') === 'true',
			visible,
			checked,
			safeValue,
			rect: rectOf(rect),
			style: {
				display: style.display.slice(0, 40),
				position: style.position.slice(0, 40),
				color: style.color.slice(0, 80),
				backgroundColor: style.backgroundColor.slice(0, 80),
				fontSize: style.fontSize.slice(0, 40)
			}
		};
	});

	for (const [qaId, count] of counts) {
		if (count > 1) {
			diagnostics.push({
				code: 'duplicate-qa-id',
				severity: 'error',
				message: `data-qa="${qaId}"가 ${count}번 사용되었습니다.`,
				qaId
			});
		}
	}
	const horizontalOverflow = Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth ?? 0) - innerWidth;
	if (horizontalOverflow > 1) {
		diagnostics.push({
			code: 'horizontal-overflow',
			severity: 'warning',
			message: `문서가 viewport보다 ${Math.round(horizontalOverflow)}px 넓습니다.`
		});
	}
	for (const message of consoleErrors.slice(-20)) {
		diagnostics.push({ code: 'console-error', severity: 'error', message });
	}

	const active = document.activeElement instanceof HTMLElement ? document.activeElement.dataset.qa : undefined;
	return {
		route: location.pathname,
		title: document.title.slice(0, 300),
		viewport: { x: scrollX, y: scrollY, width: innerWidth, height: innerHeight },
		document: {
			x: 0,
			y: 0,
			width: Math.max(document.documentElement.scrollWidth, document.body?.scrollWidth ?? 0),
			height: Math.max(document.documentElement.scrollHeight, document.body?.scrollHeight ?? 0)
		},
		activeQaId: active ?? null,
		elements,
		diagnostics: diagnostics.slice(0, 200),
		capturedAt: new Date().toISOString()
	};
}

function setEditableValue(element: HTMLInputElement | HTMLTextAreaElement, value: string): void {
	const prototype = element instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
	const setter = Object.getOwnPropertyDescriptor(prototype, 'value')?.set;
	if (!setter) throw new Error('입력값 setter를 찾을 수 없습니다.');
	setter.call(element, value);
	element.dispatchEvent(new Event('input', { bubbles: true }));
	element.dispatchEvent(new Event('change', { bubbles: true }));
}

async function executeCommand(command: QaCommand): Promise<Record<string, unknown>> {
	if (command.action === 'snapshot') return { route: location.pathname };
	if (command.action === 'navigate') {
		if (!command.path || !command.path.startsWith('/') || command.path.startsWith('//')) throw new Error('허용되지 않은 이동 경로입니다.');
		const target = new URL(command.path, location.origin);
		if (target.origin !== location.origin || target.search || target.hash) throw new Error('same-origin 경로만 이동할 수 있습니다.');
		await goto(target.pathname);
		return { route: location.pathname };
	}

	const target = command.targetQaId ? qaElement(command.targetQaId) : null;
	if (!target) throw new Error(`data-qa 대상이 없습니다: ${command.targetQaId ?? ''}`);
	if (command.action === 'click') target.click();
	if (command.action === 'fill') {
		if (!(target instanceof HTMLInputElement || target instanceof HTMLTextAreaElement)) throw new Error('fill 대상은 input 또는 textarea여야 합니다.');
		if (target.dataset.qaFill !== 'true') throw new Error('fill이 명시적으로 허용되지 않은 대상입니다.');
		if (target instanceof HTMLInputElement && ['password', 'file', 'hidden'].includes(target.type)) throw new Error('민감하거나 파일 기반 입력은 조작할 수 없습니다.');
		setEditableValue(target, command.value ?? '');
		target.focus();
	}
	if (command.action === 'key') {
		if (!command.key || !ALLOWED_KEYS.has(command.key)) throw new Error('허용되지 않은 키입니다.');
		const key = command.key === 'Space' ? ' ' : command.key;
		target.focus();
		target.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
		target.dispatchEvent(new KeyboardEvent('keyup', { key, bubbles: true, cancelable: true }));
	}
	if (command.action === 'scroll') {
		target.scrollIntoView({ behavior: command.behavior ?? 'auto', block: command.block ?? 'center' });
	}
	await new Promise((resolve) => setTimeout(resolve, 80));
	return {
		route: location.pathname,
		activeQaId: document.activeElement instanceof HTMLElement ? document.activeElement.dataset.qa ?? null : null
	};
}

async function jsonFetch(path: string, init?: RequestInit): Promise<Response> {
	return fetch(`${API_ROOT}${path}`, {
		...init,
		cache: 'no-store',
		headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }
	});
}

/** 로컬 UI가 에이전트 검수 API와 연결되며 반환 함수로 완전히 종료된다. */
export async function startUiQaBridge(): Promise<() => void> {
	let active = true;
	const consoleErrors: string[] = [];
	const config = await jsonFetch('/config').then((response) => (response.ok ? response.json() : null)).catch(() => null);
	if (!config?.enabled || !active) return () => undefined;

	const sessionId = crypto.randomUUID();
	const registered = await jsonFetch('/sessions/register', {
		method: 'POST',
		body: JSON.stringify({
			sessionId,
			clientName: 'dartlab-local-ui',
			capabilities: ['semantic-snapshot', 'click', 'fill', 'key', 'navigate', 'scroll']
		})
	}).catch(() => null);
	if (!registered?.ok) return () => undefined;

	let snapshotTimer: ReturnType<typeof setTimeout> | null = null;
	let heartbeatTimer: ReturnType<typeof setInterval> | null = null;
	const pushSnapshot = async () => {
		if (!active) return;
		await jsonFetch(`/sessions/${sessionId}/snapshot`, {
			method: 'POST',
			body: JSON.stringify(collectSnapshot(consoleErrors))
		}).catch(() => undefined);
	};
	const scheduleSnapshot = () => {
		if (!active || snapshotTimer) return;
		snapshotTimer = setTimeout(() => {
			snapshotTimer = null;
			void pushSnapshot();
		}, 250);
	};
	const observer = new MutationObserver(scheduleSnapshot);
	observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, characterData: true });
	const onResize = () => scheduleSnapshot();
	const onError = (event: ErrorEvent) => {
		consoleErrors.push(compactText(event.message, 500) ?? '알 수 없는 UI 오류');
		if (consoleErrors.length > 20) consoleErrors.shift();
		scheduleSnapshot();
	};
	const onRejection = (event: PromiseRejectionEvent) => {
		const message = event.reason instanceof Error ? event.reason.message : String(event.reason ?? '처리되지 않은 Promise 오류');
		consoleErrors.push(compactText(message, 500) ?? '처리되지 않은 Promise 오류');
		if (consoleErrors.length > 20) consoleErrors.shift();
		scheduleSnapshot();
	};
	addEventListener('resize', onResize);
	addEventListener('error', onError);
	addEventListener('unhandledrejection', onRejection);
	heartbeatTimer = setInterval(() => void pushSnapshot(), 10_000);
	await pushSnapshot();

	void (async () => {
		while (active) {
			try {
				const response = await jsonFetch(`/sessions/${sessionId}/commands/next`);
				if (response.status === 204) {
					await new Promise((resolve) => setTimeout(resolve, 400));
					continue;
				}
				if (!response.ok) throw new Error(`UI 검수 명령 조회 실패: ${response.status}`);
				const command = (await response.json()) as QaCommand;
				try {
					const detail = await executeCommand(command);
					await pushSnapshot();
					await jsonFetch(`/sessions/${sessionId}/commands/${command.commandId}/result`, {
						method: 'POST',
						body: JSON.stringify({ ok: true, detail })
					});
				} catch (reason) {
					const message = reason instanceof Error ? reason.message : String(reason);
					await jsonFetch(`/sessions/${sessionId}/commands/${command.commandId}/result`, {
						method: 'POST',
						body: JSON.stringify({ ok: false, message })
					});
				}
			} catch {
				await new Promise((resolve) => setTimeout(resolve, 1500));
			}
		}
	})();

	return () => {
		active = false;
		observer.disconnect();
		if (snapshotTimer) clearTimeout(snapshotTimer);
		if (heartbeatTimer) clearInterval(heartbeatTimer);
		removeEventListener('resize', onResize);
		removeEventListener('error', onError);
		removeEventListener('unhandledrejection', onRejection);
		void jsonFetch(`/sessions/${sessionId}`, { method: 'DELETE', keepalive: true }).catch(() => undefined);
	};
}
