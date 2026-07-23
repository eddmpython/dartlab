// pyproc 최신 npm 버전 해소. pyprocPinBump.yml 의 resolve 잡.
// pyproc 0.x는 patch도 공개 계약을 깨뜨릴 수 있으므로 파일 경로로 게이트를 생략하지 않는다.
// GITHUB_OUTPUT 에 newer/current/latest/bump/tier2 emit(로컬 실행 시 stdout).
import { readFileSync, appendFileSync } from 'node:fs';

const PKG = 'landing/package.json';

function out(k, v) {
	const f = process.env.GITHUB_OUTPUT;
	if (f) appendFileSync(f, `${k}=${v}\n`);
	console.log(`${k}=${v}`);
}

const semver = (t) => t.replace(/^v/, '').split('.').map(Number);
const isGreater = (candidate, current) => {
	for (let i = 0; i < 3; i += 1) {
		if (candidate[i] > current[i]) return true;
		if (candidate[i] < current[i]) return false;
	}
	return false;
};

// 현재 핀(npm 버전) + npm 최신
const m = readFileSync(PKG, 'utf8').match(/"pyproc":\s*"(\d+\.\d+\.\d+)"/);
const current = m ? m[1] : '';
const reg = await (await fetch('https://registry.npmjs.org/pyproc/latest')).json();
const latest = reg.version || '';

const newer = !!latest && (!current || isGreater(semver(latest), semver(current)));
out('newer', String(newer));
out('current', current);
out('latest', latest);
if (!newer) process.exit(0);

const a = semver(latest),
	b = semver(current || '0.0.0');
out('bump', a[0] !== b[0] ? 'major' : a[1] !== b[1] ? 'minor' : 'patch');

// 모든 0.x 후보는 실 Chromium과 사람 리뷰를 강제한다. 1.0 이후 완화는 별도 근거와 함께 한다.
out('tier2', 'true');
