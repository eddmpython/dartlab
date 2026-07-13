// landing/package.json 의 pyproc npm 버전을 주어진 값으로 교체. pyprocPinBump.yml 의 gate/land 잡.
// 사용: node .github/scripts/pyprocApplyPin.mjs <x.y.z>
// 교체 후 npm install 은 워크플로가 별도 수행(lock 갱신).
import { readFileSync, writeFileSync } from 'node:fs';

const ver = process.argv[2] || '';
if (!/^\d+\.\d+\.\d+$/.test(ver)) {
	console.error('사용: node pyprocApplyPin.mjs <x.y.z>');
	process.exit(2);
}

const PKG = 'landing/package.json';
const before = readFileSync(PKG, 'utf8');
const re = /("pyproc":\s*")\d+\.\d+\.\d+(")/;
if (!re.test(before)) {
	console.error('pyproc npm 핀 라인을 못 찾음. landing/package.json 의 pyproc 형식 확인.');
	process.exit(1);
}
const after = before.replace(re, `$1${ver}$2`);
if (after === before) {
	console.log(`이미 ${ver} (변경 없음)`);
	process.exit(0);
}
writeFileSync(PKG, after);
console.log(`pyproc -> ${ver}`);
