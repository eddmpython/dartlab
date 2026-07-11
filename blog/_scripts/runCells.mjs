/**
 * 브라우저 실행셀 발행 게이트.
 *
 * "dartlab 이야기" 는 본문 python 코드펜스가 곧 브라우저 실행셀이다. 이 하네스는 실제
 * chromium 에서 글을 열고 실행 막대를 위에서 아래로 눌러, 셀마다 출력이 실제로 났는지 본다.
 * 커널은 앱과 같은 pyodide 워커다. auditBlog.py 가 문자(계약·SEO)를 보는 발행 게이트라면,
 * 이것은 코드가 브라우저에서 실제로 도는지 보는 짝이다.
 *
 * 손 검수로는 못 잡는 실패가 있다. 워커가 마지막 식을 조용히 삼켜도 예외가 안 나고 출력만
 * 사라진다. 그래서 세 결과를 가른다.
 *   ok     출력이 났다
 *   empty  실행은 끝났는데 출력이 없다 (조용히 삼킨 경우. 가장 위험하다)
 *   error  파이썬 예외
 *
 * 사용:
 *   node blog/_scripts/runCells.mjs --post 01-what-is-dartlab
 *   node blog/_scripts/runCells.mjs                       # 발행분 전수
 *   node blog/_scripts/runCells.mjs --probe "import dartlab; dartlab.Company('005930').panel('IS').shape"
 *   node blog/_scripts/runCells.mjs --post 02-... --cell 5    # 그 셀만 첫 클릭 (선행 실행 회귀)
 *   node blog/_scripts/runCells.mjs --wheel dist/dartlab-0.10.8-...whl --post 06-...   # 미배포 wheel 매핑 검증
 *
 * 전제: landing dev 서버가 5173 에 떠 있어야 한다 (cd landing && npm run dev).
 * 편당 약 90 초. 첫 셀이 pyodide + wheel 다운로드를 그 편 전 셀에 상각한다. CI-fast 부적합,
 * dartlab-stories 편을 발행하기 전 로컬에서 돌리는 게이트다.
 */
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, resolve } from 'node:path';

const HERE = dirname(fileURLToPath(import.meta.url));
const REPO = resolve(HERE, '..', '..');

// playwright 는 이 하네스의 유일한 무거운 의존이다. main install 을 부풀리지 않으려고 별도로
// 넣지 않고, repo 에 이미 설치된 것을 빌려 쓴다. 한 곳이 사라져도 다음을 시도한다.
function resolveChromium() {
	const candidates = [
		resolve(REPO, 'ui', 'web', 'node_modules', 'playwright', 'index.mjs'),
		resolve(REPO, 'sns', 'video', 'toolkit', 'playwright', 'node_modules', 'playwright', 'index.mjs'),
		resolve(REPO, 'node_modules', 'playwright', 'index.mjs'),
	];
	const found = candidates.find(existsSync);
	if (!found) {
		throw new Error(
			`playwright 를 찾지 못했다. 다음 중 하나에 설치돼 있어야 한다:\n  ${candidates.join('\n  ')}`
		);
	}
	return import(pathToFileURL(found).href);
}
const { chromium } = await resolveChromium();

const STORIES = resolve(REPO, 'blog', '03-dartlab-stories');
const BASE = process.env.HARNESS_BASE ?? 'http://localhost:5173';

/** 첫 셀은 pyodide + wheel 을 내려받는다. 그 다음부터는 커널이 살아 있다. */
const FIRST_CELL_MS = 240_000;
const NEXT_CELL_MS = 90_000;
const PAGE_LOAD_MS = 120_000;

function slugOf(folder) {
	return folder.replace(/^\d+-/, '');
}

function allPosts() {
	return readdirSync(STORIES, { withFileTypes: true })
		.filter((d) => d.isDirectory())
		.map((d) => d.name)
		.sort();
}

function resolveStoryFolder(folder) {
	const direct = resolve(STORIES, folder);
	if (existsSync(direct)) return folder;
	return allPosts().find((f) => slugOf(f) === slugOf(folder)) ?? folder;
}

function expectedCodeCells(folder) {
	const resolved = resolveStoryFolder(folder);
	const indexPath = resolve(STORIES, resolved, 'index.md');
	if (!existsSync(indexPath)) return 0;
	const raw = readFileSync(indexPath, 'utf8');
	return (raw.match(/```python\b/g) ?? []).length;
}

async function openPost(page, folder) {
	const url = `${BASE}/blog/${slugOf(folder)}`;
	// Dev 서버는 폰트, 후원 버튼, 댓글 위젯 같은 외부 요청이 남아 networkidle 이 닫히지 않을 수 있다.
	// 실행셀 가드는 DOM 과 본문이 뜬 뒤 버튼을 누르는 것이 목적이므로 본문 존재를 진입 조건으로 삼는다.
	await page.goto(url, { waitUntil: 'domcontentloaded', timeout: PAGE_LOAD_MS });
	await page.waitForSelector('article, main', { timeout: PAGE_LOAD_MS });
	return url;
}

/** 셀 하나를 누르고 결과가 확정될 때까지 기다린다. */
async function runOneCell(page, index, budgetMs) {
	const bar = page.locator('.rc-bar').nth(index);
	const runBtn = bar.locator('button.rc-run');
	await runBtn.click();

	// 버튼이 다시 살아나면 실행이 끝난 것이다.
	await runBtn.waitFor({ state: 'attached' });
	await page.waitForFunction(
		(i) => {
			const btn = document.querySelectorAll('.rc-bar')[i]?.querySelector('button.rc-run');
			return btn && !btn.disabled;
		},
		index,
		{ timeout: budgetMs }
	);

	// rc-out 은 output 이 있을 때만 붙는다. OutputPanel 은 data 가 비면 스스로 사라진다.
	// 인덱스로 찾으면 안 된다. 출력 없는 셀이 하나라도 있으면 그 뒤가 통째로 밀린다.
	// 같은 컴포넌트가 rc-bar 와 rc-out 을 한 부모 아래 낳으므로 그 부모로 범위를 좁힌다.
	const out = bar.locator('xpath=..').locator('.rc-out');
	const hasOut = (await out.count()) > 0;
	if (!hasOut) return { status: 'empty', text: '' };

	const panel = out.locator('.output-panel');
	if ((await panel.count()) === 0) return { status: 'empty', text: '' };

	const isError = (await panel.getAttribute('class'))?.includes('error');
	const text = ((await panel.innerText()) ?? '').trim();
	return { status: isError ? 'error' : 'ok', text };
}

async function runPost(page, folder, afterOpen = null) {
	await openPost(page, folder);
	if (afterOpen) await afterOpen();
	const expected = expectedCodeCells(folder);
	if (expected > 0) {
		try {
			await page.waitForSelector('.rc-bar', { timeout: FIRST_CELL_MS });
		} catch {
			return {
				folder,
				cells: 0,
				results: [
					{
						status: 'error',
						text: `본문 python 코드 ${expected}개지만 실행 막대가 뜨지 않았다`,
						index: 0,
						elapsedSec: +(FIRST_CELL_MS / 1000).toFixed(1),
					},
				],
			};
		}
	}

	const cells = await page.locator('.rc-bar').count();
	if (expected > 0 && cells < expected) {
		return {
			folder,
			cells,
			results: [
				{
					status: 'error',
					text: `본문 python 코드 ${expected}개지만 실행 막대는 ${cells}개다`,
					index: 0,
					elapsedSec: 0,
				},
			],
		};
	}
	if (cells === 0) {
		return { folder, cells: 0, results: [], note: '실행 막대가 하나도 없다' };
	}

	const results = [];
	for (let i = 0; i < cells; i++) {
		const budget = i === 0 ? FIRST_CELL_MS : NEXT_CELL_MS;
		const t0 = Date.now();
		let r;
		try {
			r = await runOneCell(page, i, budget);
		} catch (err) {
			r = { status: 'error', text: `하네스 타임아웃 또는 실패: ${err.message.split('\n')[0]}` };
		}
		results.push({ ...r, index: i, elapsedSec: +((Date.now() - t0) / 1000).toFixed(1) });
	}
	return { folder, cells, results };
}

/** 앱과 같은 커널로 임의 코드를 돌린다. 미측정 능력을 실측할 때 쓴다. */
async function probe(page, code) {
	const anyPost = allPosts().find((f) => f !== 'PIPELINE.md');
	await openPost(page, anyPost);
	page.setDefaultTimeout(FIRST_CELL_MS);
	return page.evaluate(async (src) => {
		const mod = await import('/src/lib/notebook/stores/executionStore.ts');
		const out = await mod.runSnippet(src);
		return { type: out?.type ?? 'none', data: (out?.data ?? '').slice(0, 4000) };
	}, code);
}

async function main() {
	const argv = process.argv.slice(2);
	const arg = (name) => {
		const i = argv.indexOf(name);
		return i >= 0 ? argv[i + 1] : undefined;
	};

	const browser = await chromium.launch();
	const ctx = await browser.newContext();
	const wheelPath = arg('--wheel');
	if (wheelPath) {
		const localWheel = resolve(REPO, wheelPath);
		if (!existsSync(localWheel)) throw new Error(`wheel 파일 없음: ${localWheel}`);
		await ctx.route('**/pyodide/dartlab-*.whl', async (route) => {
			await route.fulfill({ path: localWheel, contentType: 'application/zip' });
		});
		console.log(`[wheel-route] ${localWheel}`);
	}
	const page = await ctx.newPage();
	page.setDefaultTimeout(NEXT_CELL_MS);

	async function ensureWheelOnCurrentPage() {
		// --wheel 은 브라우저 컨텍스트 route 로 HF wheel 요청을 로컬 wheel 파일에 매핑한다.
		// 버튼과 probe 가 같은 worker 자동 설치 경로를 타게 하려면 별도 수동 설치를 하지 않는다.
	}
	const probeCode = arg('--probe');
	if (probeCode) {
		if (wheelPath) {
			await openPost(page, allPosts()[0]);
			await ensureWheelOnCurrentPage();
			const r = await page.evaluate(async (src) => {
				const mod = await import('/src/lib/notebook/stores/executionStore.ts');
				const out = await mod.runSnippet(src);
				return { type: out?.type ?? 'none', data: (out?.data ?? '').slice(0, 4000) };
			}, probeCode);
			console.log(`[${r.type}]`);
			console.log(r.data);
			await browser.close();
			process.exit(r.type === 'error' ? 1 : 0);
		}
		const r = await probe(page, probeCode);
		console.log(`[${r.type}]`);
		console.log(r.data);
		await browser.close();
		process.exit(r.type === 'error' ? 1 : 0);
	}

	// 독자는 글 중간부터 누른다. --cell N 은 그 한 셀만 첫 클릭으로 눌러 선행 실행이 붙는지 본다.
	const onlyCell = arg('--cell');
	if (onlyCell) {
		const folder = arg('--post') ?? allPosts()[0];
		await openPost(page, folder);
		await ensureWheelOnCurrentPage();
		const idx = Number(onlyCell) - 1;
		const r = await runOneCell(page, idx, FIRST_CELL_MS);
		console.log(`[${r.status}] ${folder} 셀 ${onlyCell} 만 눌렀다`);
		console.log(r.text.slice(0, 4000));
		await browser.close();
		process.exit(r.status === 'ok' ? 0 : 1);
	}

	const one = arg('--post');
	const folders = one ? [one] : allPosts();

	let bad = 0;
	for (const folder of folders) {
		const rep = await runPost(page, folder, ensureWheelOnCurrentPage);
		console.log(`\n=== ${rep.folder} . 셀 ${rep.cells} ===`);
		if (rep.note) console.log(`  ${rep.note}`);
		for (const r of rep.results) {
			const mark = r.status === 'ok' ? 'ok   ' : r.status === 'empty' ? 'EMPTY' : 'ERROR';
			if (r.status !== 'ok') bad++;
			const head = r.text.split('\n')[0].slice(0, 90);
			console.log(`  [${mark}] 셀 ${r.index + 1} (${r.elapsedSec}s) ${head}`);
		}
	}

	await browser.close();
	console.log(`\n결과: 문제 ${bad} 건`);
	process.exit(bad > 0 ? 1 : 0);
}

main().catch((err) => {
	console.error(err);
	process.exit(1);
});
