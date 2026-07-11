// landing/package.json 의 pyproc 핀 SHA 를 주어진 값으로 교체. pyprocPinBump.yml 의 gate/land 잡.
// 사용: node .github/scripts/pyprocApplyPin.mjs <40자 SHA>
// 교체 후 npm install 은 워크플로가 별도로 수행(lock resolved 갱신).
import { readFileSync, writeFileSync } from 'node:fs';

const sha = process.argv[2] || '';
if (!/^[0-9a-f]{40}$/.test(sha)) {
	console.error('사용: node pyprocApplyPin.mjs <40자 SHA>');
	process.exit(2);
}

const PKG = 'landing/package.json';
const before = readFileSync(PKG, 'utf8');
const re = /("pyproc":\s*"git\+https:\/\/github\.com\/eddmpython\/pyproc\.git#)[0-9a-f]{7,40}(")/;
if (!re.test(before)) {
	console.error('pyproc 핀 라인을 못 찾음. landing/package.json 의 pyproc 형식 확인.');
	process.exit(1);
}
const after = before.replace(re, `$1${sha}$2`);
if (after === before) {
	console.log(`이미 핀 = ${sha} (변경 없음)`);
	process.exit(0);
}
writeFileSync(PKG, after);
console.log(`pyproc 핀 -> ${sha}`);
