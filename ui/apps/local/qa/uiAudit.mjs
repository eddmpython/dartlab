/**
 * 로컬 DartLab UI 시각 검수 실행기.
 *
 * 서버가 발행한 검수 계획(/api/ui-qa/audit-plan)을 화면 크기별로 실행한다. 조작은 전부
 * UI 검수 제어면(/api/ui-qa)을 왕복해서 수행한다. 브라우저를 직접 클릭하지 않는 이유는
 * 제어면 자체가 실제로 도는지를 같은 실행으로 증명하기 위해서다. Playwright 는 창을 열고,
 * 화면 크기를 정하고, 사진을 찍는 일만 한다.
 *
 * 실행:
 *   npm install --no-save playwright@1.62.1   (최초 1 회)
 *   node ui/apps/local/qa/uiAudit.mjs --base http://127.0.0.1:5174 --out /tmp/dartlab-ui-audit
 *
 * 산출:
 *   <out>/<viewportId>/<scenarioId>-<stepId>.png  실제 화면 사진
 *   <out>/report.json                             시나리오별 판정과 finding
 * 종료코드: error 심각도 finding 이 하나라도 있으면 1.
 */

import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { chromium } from 'playwright';

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
	args.set(process.argv[i].replace(/^--/, ''), process.argv[i + 1]);
}
const BASE = (args.get('base') ?? 'http://127.0.0.1:5174').replace(/\/$/, '');
const OUT = args.get('out') ?? '/tmp/dartlab-ui-audit';
const ONLY_SCENARIO = args.get('scenario') ?? null;
const ONLY_VIEWPORT = args.get('viewport') ?? null;
const HEADED = args.get('headed') === 'true';
// 설치된 실물 Chrome 을 기본으로 쓴다. 별도 내려받기가 없고 사용자가 보는 렌더링과 같다.
const CHANNEL = args.get('channel') ?? 'chrome';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function api(path, init) {
	const response = await fetch(`${BASE}/api/ui-qa${path}`, {
		...init,
		headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) }
	});
	if (response.status === 204) return null;
	const body = await response.text();
	if (!response.ok) throw new Error(`${path} -> ${response.status} ${body.slice(0, 300)}`);
	return body ? JSON.parse(body) : null;
}

/** 현재 살아 있는 세션 식별자 집합. 이동 전에 찍어 두고 새 세션만 골라내는 데 쓴다. */
async function knownSessionIds() {
	const { sessions } = await api('/sessions');
	return new Set(sessions.map((item) => item.sessionId));
}

/** 방금 연 페이지가 제어면에 등록될 때까지 기다려 세션 식별자를 찾는다.
 *
 * 같은 경로를 다시 열면 이전 세션이 TTL 동안 남아 있다. 경로만 보고 고르면 이미
 * 죽은 세션에 명령을 보내고 영원히 기다리게 된다. 그래서 이동 전 식별자 집합에
 * 없던 새 세션만 받아들인다.
 */
async function waitForSession(route, before, timeoutMs = 15_000) {
	const deadline = Date.now() + timeoutMs;
	while (Date.now() < deadline) {
		const { sessions } = await api('/sessions');
		const fresh = sessions.find((item) => !before.has(item.sessionId) && item.route === route);
		if (fresh) return fresh.sessionId;
		await sleep(250);
	}
	throw new Error(`검수 브리지가 ${route} 에 붙지 않았습니다. dartlab ai --dev 로 켜져 있는지 확인하십시오.`);
}

/** 제어면에 명령을 넣고 브라우저가 끝낼 때까지 기다린다. */
async function runCommand(sessionId, command, timeoutMs = 15_000) {
	const queued = await api(`/sessions/${sessionId}/commands`, {
		method: 'POST',
		body: JSON.stringify(command)
	});
	const deadline = Date.now() + timeoutMs;
	while (Date.now() < deadline) {
		const state = await api(`/sessions/${sessionId}/commands/${queued.commandId}`);
		if (state.status === 'succeeded' || state.status === 'failed') return state;
		await sleep(150);
	}
	throw new Error(`명령이 끝나지 않았습니다: ${command.action} ${command.targetQaId ?? command.path ?? ''}`);
}

/** 화면이 스스로 선언한 로딩 표시가 사라질 때까지 기다린다.
 *
 * 고정 대기는 느린 화면을 놓치고 빠른 화면을 낭비한다. 앱이 data-qa 로 선언한
 * 로딩 요소가 곧 준비 신호이므로 그것이 사라지는 것을 기다린다. 끝내 남아 있으면
 * 그 자체가 결함이다. 사람이 보는 "스피너가 안 없어진다" 와 같은 판정이다.
 */
async function settleLoading(sessionId, timeoutMs = 8_000) {
	const deadline = Date.now() + timeoutMs;
	let last = [];
	while (Date.now() < deadline) {
		const session = await api(`/sessions/${sessionId}`);
		last = (session.snapshot?.elements ?? []).filter(
			(item) => item.visible && /loading|spinner|skeleton/i.test(item.qaId)
		);
		if (!last.length) return { settled: true, stuck: [], snapshot: session.snapshot };
		await sleep(400);
	}
	const session = await api(`/sessions/${sessionId}`);
	return { settled: false, stuck: last.map((item) => item.qaId), snapshot: session.snapshot };
}

/** 실제로 그려진 내용을 브라우저에서 직접 잰다.
 *
 * data-qa 개수를 화면 충실도의 대리지표로 쓰면 안 된다. 터미널 화면은 계기판 전체를
 * data-qa 하나로 감싸고 있어서 완전히 그려져 있는데도 "비어 있다" 로 오판했다.
 * 사람이 보는 것은 칠해진 픽셀과 글자이지 계측 속성이 아니다.
 */
async function pageContent(page) {
	return page.evaluate(() => {
		let boxes = 0;
		for (const node of document.body.querySelectorAll('*')) {
			const rect = node.getBoundingClientRect();
			if (rect.width > 4 && rect.height > 4) boxes += 1;
			if (boxes > 400) break;
		}
		return { textLength: (document.body.innerText || '').trim().length, boxes };
	});
}

/** 스냅숏에서 요소 단언과 브라우저 진단을 finding 으로 옮긴다. */
function evaluateStep(step, snapshot, content) {
	const findings = [];
	const byId = new Map((snapshot?.elements ?? []).map((item) => [item.qaId, item]));

	// 사람이 보면 즉시 아는 두 가지를 기계가 놓치지 않게 한다. qaId 존재만으로 통과시키면
	// 스피너 하나만 도는 빈 화면도 정상으로 보고된다.
	const visible = (snapshot?.elements ?? []).filter((item) => item.visible);
	const stuck = visible.filter((item) => /loading|spinner|skeleton/i.test(item.qaId));
	for (const item of stuck) {
		findings.push({
			severity: 'error',
			code: 'stuck-loading',
			message: `${item.qaId} 로딩 표시가 사라지지 않았습니다. 화면이 준비되지 않았습니다.`,
			qaId: item.qaId
		});
	}
	if (content && (content.textLength < 40 || content.boxes < 8)) {
		findings.push({
			severity: 'error',
			code: 'empty-route',
			message: `그려진 글자 ${content.textLength} 자, 박스 ${content.boxes} 개. 화면이 사실상 비어 있습니다.`
		});
	}

	for (const qaId of step.assertQaIds ?? []) {
		const element = byId.get(qaId);
		if (!element) {
			findings.push({ severity: 'error', code: 'missing-element', message: `${qaId} 가 화면에 없습니다.`, qaId });
		} else if (!element.visible) {
			findings.push({ severity: 'error', code: 'invisible-element', message: `${qaId} 가 보이지 않습니다.`, qaId });
		}
	}
	const anyOf = step.assertAnyQaIds ?? [];
	if (anyOf.length && !anyOf.some((qaId) => byId.get(qaId)?.visible)) {
		findings.push({
			severity: 'error',
			code: 'missing-any-element',
			message: `${anyOf.join(', ')} 중 어느 것도 보이지 않습니다.`
		});
	}
	for (const diagnostic of snapshot?.diagnostics ?? []) {
		if (diagnostic.code === 'offscreen-element') continue;
		findings.push({
			severity: diagnostic.severity,
			code: diagnostic.code,
			message: diagnostic.message.slice(0, 500),
			qaId: diagnostic.qaId ?? null
		});
	}
	return findings;
}

/** 한 턴이 흘러가는 모습을 시간 순서로 연속 촬영한다.
 *
 * 정지 화면 한 장으로는 대화 흐름을 판정할 수 없다. 사고와 도구 호출과 본문이 어떤
 * 순서로 나타나고 완료 순간 무엇이 흔들리는지는 시간축을 봐야 안다.
 */
async function filmstrip(question) {
	const browser = await chromium
		.launch({ headless: !HEADED, channel: CHANNEL === 'bundled' ? undefined : CHANNEL })
		.catch(() => chromium.launch({ headless: !HEADED }));
	const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
	const page = await context.newPage();
	const consoleErrors = [];
	page.on('console', (m) => m.type() === 'error' && consoleErrors.push(m.text().slice(0, 300)));
	page.on('pageerror', (e) => consoleErrors.push(String(e.message).slice(0, 300)));

	const before = await knownSessionIds();
	await page.goto(`${BASE}/chat`, { waitUntil: 'domcontentloaded', timeout: 30_000 });
	const sessionId = await waitForSession('/chat', before);
	await runCommand(sessionId, { action: 'fill', targetQaId: 'chat-input', value: question });
	await runCommand(sessionId, { action: 'click', targetQaId: 'chat-send' });

	const dir = join(OUT, 'filmstrip');
	await mkdir(dir, { recursive: true });
	const frames = [];
	const totalMs = Number(args.get('liveMs') ?? 240_000);
	const everyMs = Number(args.get('frameMs') ?? 15_000);
	const startedAt = Date.now();
	let index = 0;
	while (Date.now() - startedAt < totalMs) {
		await sleep(everyMs);
		index += 1;
		const seconds = Math.round((Date.now() - startedAt) / 1000);
		const file = join(dir, `t${String(seconds).padStart(4, '0')}s.png`);
		await page.screenshot({ path: file, fullPage: false });
		let visible = [];
		let streaming = true;
		try {
			const session = await api(`/sessions/${sessionId}`);
			visible = (session.snapshot?.elements ?? []).filter((e) => e.visible).map((e) => e.qaId);
			streaming = visible.includes('chat-stop');
		} catch {
			// 세션이 갈렸어도 촬영은 계속한다. 사진이 판정의 본체다.
		}
		frames.push({ seconds, file, visible: [...new Set(visible)].sort() });
		console.log(`  t+${seconds}s -> ${file}  보이는요소 ${visible.length}`);
		if (!streaming && index > 1) {
			console.log('  스트리밍 종료 감지. 마지막 한 장 더 찍고 끝낸다.');
			await sleep(2000);
			const last = join(dir, `t${String(seconds + 2).padStart(4, '0')}s-final.png`);
			await page.screenshot({ path: last, fullPage: false });
			frames.push({ seconds: seconds + 2, file: last, visible, final: true });
			break;
		}
	}
	await browser.close();
	const report = { mode: 'filmstrip', question, frames, consoleErrors };
	await writeFile(join(dir, 'filmstrip.json'), JSON.stringify(report, null, 2), 'utf-8');
	console.log(`\n필름스트립 ${frames.length} 장: ${dir}`);
	if (consoleErrors.length) console.log(`콘솔 오류 ${consoleErrors.length} 건: ${consoleErrors.slice(0, 3).join(' | ')}`);
	return 0;
}

async function main() {
	const config = await api('/config');
	if (args.get('live')) {
		if (!config.enabled) throw new Error('UI 검수 제어면이 꺼져 있습니다. dartlab ai --dev 로 실행하십시오.');
		return filmstrip(args.get('live'));
	}
	if (!config.enabled) {
		throw new Error('UI 검수 제어면이 꺼져 있습니다. dartlab ai --dev 로 loopback 실행하십시오.');
	}
	const plan = await api('/audit-plan');
	const viewports = plan.viewports.filter((item) => !ONLY_VIEWPORT || item.viewportId === ONLY_VIEWPORT);
	const browser = await chromium
		.launch({ headless: !HEADED, channel: CHANNEL === 'bundled' ? undefined : CHANNEL })
		.catch(() => chromium.launch({ headless: !HEADED }));
	const report = { base: BASE, startedAt: new Date().toISOString(), runs: [] };

	for (const viewport of viewports) {
		const context = await browser.newContext({
			viewport: { width: viewport.width, height: viewport.height },
			deviceScaleFactor: viewport.deviceScaleFactor ?? 1
		});
		const page = await context.newPage();
		const consoleErrors = [];
		page.on('console', (message) => {
			if (message.type() === 'error') consoleErrors.push(message.text().slice(0, 300));
		});
		page.on('pageerror', (error) => consoleErrors.push(String(error.message).slice(0, 300)));

		const scenarios = plan.scenarios.filter(
			(item) =>
				item.viewportIds.includes(viewport.viewportId) && (!ONLY_SCENARIO || item.scenarioId === ONLY_SCENARIO)
		);
		for (const scenario of scenarios) {
			const run = {
				scenarioId: scenario.scenarioId,
				viewportId: viewport.viewportId,
				route: scenario.route,
				result: 'passed',
				findings: [],
				shots: []
			};
			try {
				// 검수 브리지가 명령을 long-poll 하므로 networkidle 은 영원히 오지 않는다.
				// 실제 준비 신호는 브리지가 제어면에 등록되는 순간이다.
				const before = await knownSessionIds();
				await page.goto(`${BASE}${scenario.route}`, { waitUntil: 'domcontentloaded', timeout: 30_000 });
				const sessionId = await waitForSession(scenario.route, before);

				for (const step of scenario.steps) {
					const command = {
						action: step.action,
						targetQaId: step.targetQaId ?? null,
						value: step.value ?? null,
						key: step.key ?? null,
						path: step.path ?? null,
						behavior: step.behavior ?? null,
						block: step.block ?? null
					};
					const state = await runCommand(sessionId, command);
					if (!state.ok) {
						run.findings.push({
							severity: 'error',
							code: 'command-failed',
							message: `${step.stepId}: ${state.message ?? '명령 실패'}`,
							qaId: step.targetQaId ?? null
						});
					}
					const settled = await settleLoading(sessionId);
					const content = await pageContent(page).catch(() => null);
					run.findings.push(...evaluateStep(step, settled.snapshot, content));

					if (step.screenshotLabel) {
						const file = join(OUT, viewport.viewportId, `${step.screenshotLabel}.png`);
						await mkdir(dirname(file), { recursive: true });
						await page.screenshot({ path: file, fullPage: false });
						run.shots.push(file);
					}
				}
			} catch (reason) {
				run.result = 'blocked';
				run.findings.push({
					severity: 'error',
					code: 'scenario-blocked',
					message: String(reason instanceof Error ? reason.message : reason).slice(0, 500)
				});
			}

			for (const message of consoleErrors.splice(0)) {
				run.findings.push({ severity: 'error', code: 'console-error', message });
			}
			if (run.result !== 'blocked') {
				run.result = run.findings.some((item) => item.severity === 'error') ? 'failed' : 'passed';
			}
			report.runs.push(run);
			console.log(
				`[${run.result}] ${viewport.viewportId}/${scenario.scenarioId} findings=${run.findings.length} shots=${run.shots.length}`
			);
			for (const finding of run.findings) {
				console.log(`    ${finding.severity} ${finding.code}: ${finding.message}`);
			}
		}
		await context.close();
	}

	await browser.close();
	report.finishedAt = new Date().toISOString();
	report.errorCount = report.runs.reduce(
		(total, run) => total + run.findings.filter((item) => item.severity === 'error').length,
		0
	);
	await mkdir(OUT, { recursive: true });
	await writeFile(join(OUT, 'report.json'), JSON.stringify(report, null, 2), 'utf-8');
	console.log(`\n리포트: ${join(OUT, 'report.json')}  오류 ${report.errorCount} 건`);
	process.exit(report.errorCount > 0 ? 1 : 0);
}

main().catch((reason) => {
	console.error(`검수 실행 실패: ${reason instanceof Error ? reason.message : reason}`);
	process.exit(2);
});
