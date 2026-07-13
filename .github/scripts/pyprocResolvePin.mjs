// pyproc 최신 npm 버전 해소 + tier2(격리 필요 경로) 분류. pyprocPinBump.yml 의 resolve 잡.
// npm 레지스트리가 "무엇이 최신"을, github compare 가 "무엇이 바뀌었나(tier2)"를 준다.
// GITHUB_OUTPUT 에 newer/current/latest/bump/tier2 emit(로컬 실행 시 stdout).
import { readFileSync, appendFileSync } from 'node:fs';

const REPO = 'eddmpython/pyproc';
const PKG = 'landing/package.json';
// SAB(fork)·JSPI(subprocess) 표면 = crossOriginIsolated 필요(Tier-2). 여기 변경이면 브라우저 게이트(GATE-B)+사람 리뷰.
const TIER2_PREFIX = ['src/processOs/'];
const TIER2_FILE = ['src/capabilities/syscallBridge.js'];
// 격리 불필요(Tier-1)로 알려진 안전셋. 이 밖 src/ 변경은 err-open 으로 tier2 취급.
const SAFE = [
	'src/runtime/',
	'src/capabilities/asgiServer.js',
	'src/capabilities/reactive.js',
	'src/capabilities/terminal.js'
];

function out(k, v) {
	const f = process.env.GITHUB_OUTPUT;
	if (f) appendFileSync(f, `${k}=${v}\n`);
	console.log(`${k}=${v}`);
}

async function gh(path) {
	const headers = { Accept: 'application/vnd.github+json', 'User-Agent': 'dartlab-pyproc-pin' };
	if (process.env.GH_TOKEN) headers.Authorization = `Bearer ${process.env.GH_TOKEN}`;
	const r = await fetch(`https://api.github.com${path}`, { headers });
	if (!r.ok) throw new Error(`GitHub API ${path} -> ${r.status}`);
	return r.json();
}

const semver = (t) => t.replace(/^v/, '').split('.').map(Number);

// 현재 핀(npm 버전) + npm 최신
const m = readFileSync(PKG, 'utf8').match(/"pyproc":\s*"(\d+\.\d+\.\d+)"/);
const current = m ? m[1] : '';
const reg = await (await fetch('https://registry.npmjs.org/pyproc/latest')).json();
const latest = reg.version || '';

const newer = !!latest && current !== latest;
out('newer', String(newer));
out('current', current);
out('latest', latest);
if (!newer) process.exit(0);

const a = semver(latest),
	b = semver(current || '0.0.0');
out('bump', a[0] !== b[0] ? 'major' : a[1] !== b[1] ? 'minor' : 'patch');

let tier2 = true; // 분류 불가 시 err-open(안전 우선)
if (current) {
	try {
		const diff = await gh(`/repos/${REPO}/compare/v${current}...v${latest}`);
		const files = (diff.files || []).map((f) => f.filename);
		const hitsTier2 =
			files.some((f) => TIER2_PREFIX.some((p) => f.startsWith(p))) || files.some((f) => TIER2_FILE.includes(f));
		const unknownSrc = files.some((f) => f.startsWith('src/') && !SAFE.some((s) => f.startsWith(s)));
		tier2 = hitsTier2 || unknownSrc;
	} catch {
		tier2 = true;
	}
}
out('tier2', String(tier2));
