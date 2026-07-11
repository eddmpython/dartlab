// pyproc 최신 태그 -> SHA 해소 + tier2(격리 필요 경로) 분류. pyprocPinBump.yml 의 resolve 잡.
// GITHUB_OUTPUT 에 newer/bump/tier2/sha/tag 를 emit(로컬 실행 시 stdout 로도).
// vision 정책: float 금지·SHA 핀. 그래서 자동 반영 = 최신 태그를 SHA 로 고정해 게이트 통과 후 범프.
import { readFileSync, appendFileSync } from 'node:fs';

const REPO = 'eddmpython/pyproc';
const PKG = 'landing/package.json';
// SAB(fork)·JSPI(subprocess) 표면 = crossOriginIsolated 필요(Tier-2). 여기 변경이면 브라우저 게이트+사람 리뷰.
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
const cmp = (a, b) => {
	for (let i = 0; i < 3; i++) if ((a[i] || 0) !== (b[i] || 0)) return (a[i] || 0) - (b[i] || 0);
	return 0;
};

const pkg = readFileSync(PKG, 'utf8');
const m = pkg.match(/pyproc[^#]*#([0-9a-f]{7,40})/);
const currentSha = m ? m[1] : '';

const tags = (await gh(`/repos/${REPO}/tags?per_page=100`)).filter((t) => /^v\d+\.\d+\.\d+$/.test(t.name));
if (!tags.length) {
	out('newer', 'false');
	process.exit(0);
}
tags.sort((a, b) => cmp(semver(b.name), semver(a.name))); // API 배열순 불신 -> semver 정렬
const latest = tags[0];
const latestSha = latest.commit.sha;

const newer = !currentSha || !latestSha.startsWith(currentSha);
out('newer', String(newer));
out('tag', latest.name);
out('sha', latestSha);
if (!newer) process.exit(0);

const curTag = tags.find((t) => currentSha && t.commit.sha.startsWith(currentSha));
let bump = 'unknown';
if (curTag) {
	const a = semver(latest.name),
		b = semver(curTag.name);
	bump = a[0] !== b[0] ? 'major' : a[1] !== b[1] ? 'minor' : 'patch';
}
out('bump', bump);

let tier2 = true; // 분류 불가 시 err-open(안전 우선)
if (currentSha) {
	try {
		const diff = await gh(`/repos/${REPO}/compare/${currentSha}...${latestSha}`);
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
