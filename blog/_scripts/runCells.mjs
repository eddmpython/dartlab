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
 *   node blog/_scripts/runCells.mjs --wheel dist/dartlab-0.10.8-...whl --probe "..."   # 미배포 wheel 심어 검증
 *
 * 전제: landing dev 서버가 5173 에 떠 있어야 한다 (cd landing && npm run dev).
 * 편당 약 90 초. 첫 셀이 pyodide + wheel 다운로드를 그 편 전 셀에 상각한다. CI-fast 부적합,
 * dartlab-stories 편을 발행하기 전 로컬에서 돌리는 게이트다.
 */
import { existsSync, readdirSync } from 'node:fs';
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

function slugOf(folder) {
	return folder.replace(/^\d+-/, '');
}

function allPosts() {
	return readdirSync(STORIES, { withFileTypes: true })
		.filter((d) => d.isDirectory())
		.map((d) => d.name)
		.sort();
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

async function runPost(page, folder) {
	const url = `${BASE}/blog/${slugOf(folder)}`;
	await page.goto(url, { waitUntil: 'networkidle', timeout: 60_000 });

	const cells = await page.locator('.rc-bar').count();
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

/**
 * 아직 HF 에 올리지 않은 로컬 wheel 을 브라우저 커널에 먼저 심는다.
 *
 * 브라우저는 HF 의 wheel 로 돈다. 그래서 src 를 고쳐도 재배포 전에는 확인할 길이 없다.
 * 여기서는 `uv build` 산출물을 CORS 허용 정적 서버로 띄우고, micropip 이 그것을 먼저
 * 설치하게 만든다. 앱 워커는 `import dartlab` 을 보면 HF wheel 을 깔지만, 이미 같은
 * 이름이 설치돼 있으면 그대로 둔다. 즉 수정본이 이긴다.
 */
async function serveWheel(wheelPath) {
	const { createServer } = await import('node:http');
	const { readFileSync, statSync } = await import('node:fs');
	const { basename } = await import('node:path');

	const name = basename(wheelPath);
	const bytes = readFileSync(wheelPath);
	statSync(wheelPath);

	const server = createServer((req, res) => {
		res.setHeader('Access-Control-Allow-Origin', '*');
		if (req.url === `/${name}`) {
			res.writeHead(200, { 'Content-Type': 'application/zip', 'Content-Length': bytes.length });
			res.end(bytes);
		} else {
			res.writeHead(404).end();
		}
	});
	await new Promise((ok) => server.listen(8899, ok));
	return { url: `http://localhost:8899/${name}`, close: () => server.close() };
}

async function installWheel(page, url) {
	return page.evaluate(async (wheelUrl) => {
		const mod = await import('/src/lib/notebook/stores/executionStore.ts');
		const src = [
			'import micropip',
			`await micropip.install(${JSON.stringify(wheelUrl)})`,
			'import dartlab',
			'print("wheel", dartlab.__version__)',
		].join('\n');
		const out = await mod.runSnippet(src);
		return { type: out?.type ?? 'none', data: (out?.data ?? '').slice(0, 800) };
	}, url);
}

/** 앱과 같은 커널로 임의 코드를 돌린다. 미측정 능력을 실측할 때 쓴다. */
async function probe(page, code) {
	const anyPost = allPosts().find((f) => f !== 'PIPELINE.md');
	await page.goto(`${BASE}/blog/${slugOf(anyPost)}`, { waitUntil: 'networkidle', timeout: 60_000 });
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
	const page = await ctx.newPage();
	page.setDefaultTimeout(NEXT_CELL_MS);

	const wheelPath = arg('--wheel');
	let wheelServer;
	const probeCode = arg('--probe');
	if (probeCode) {
		if (wheelPath) {
			wheelServer = await serveWheel(wheelPath);
			const anyPost = allPosts()[0];
			await page.goto(`${BASE}/blog/${slugOf(anyPost)}`, { waitUntil: 'networkidle', timeout: 60_000 });
			page.setDefaultTimeout(FIRST_CELL_MS);
			const installed = await installWheel(page, wheelServer.url);
			console.log(`[wheel] ${installed.type} :: ${installed.data.trim().split('\n').slice(-2).join(' | ')}`);
			if (installed.type === 'error') {
				wheelServer.close();
				await browser.close();
				process.exit(1);
			}
			const r = await page.evaluate(async (src) => {
				const mod = await import('/src/lib/notebook/stores/executionStore.ts');
				const out = await mod.runSnippet(src);
				return { type: out?.type ?? 'none', data: (out?.data ?? '').slice(0, 4000) };
			}, probeCode);
			console.log(`[${r.type}]`);
			console.log(r.data);
			wheelServer.close();
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
		await page.goto(`${BASE}/blog/${slugOf(folder)}`, { waitUntil: 'networkidle', timeout: 60_000 });
		const idx = Number(onlyCell) - 1;
		const r = await runOneCell(page, idx, FIRST_CELL_MS);
		console.log(`[${r.status}] ${folder} 셀 ${onlyCell} 만 눌렀다`);
		console.log(r.text.slice(0, 600));
		await browser.close();
		process.exit(r.status === 'ok' ? 0 : 1);
	}

	const one = arg('--post');
	const folders = one ? [one] : allPosts();

	let bad = 0;
	for (const folder of folders) {
		const rep = await runPost(page, folder);
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
