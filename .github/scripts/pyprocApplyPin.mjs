// landing/package.json과 runtime-manifest.json의 pyproc 버전을 함께 교체.
// pyprocPinBump.yml 의 gate/landing/propose 잡이 같은 정본을 쓴다.
// 사용: node .github/scripts/pyprocApplyPin.mjs <x.y.z>
// 교체 후 npm install 은 워크플로가 별도 수행(lock 갱신).
import { readFileSync, writeFileSync } from 'node:fs';

const ver = process.argv[2] || '';
if (!/^\d+\.\d+\.\d+$/.test(ver)) {
	console.error('사용: node pyprocApplyPin.mjs <x.y.z>');
	process.exit(2);
}

const PKG = 'landing/package.json';
const MANIFEST = 'landing/runtime-manifest.json';
const before = readFileSync(PKG, 'utf8');
const re = /("pyproc":\s*")\d+\.\d+\.\d+(")/;
if (!re.test(before)) {
	console.error('pyproc npm 핀 라인을 못 찾음. landing/package.json 의 pyproc 형식 확인.');
	process.exit(1);
}
const after = before.replace(re, `$1${ver}$2`);
const manifest = JSON.parse(readFileSync(MANIFEST, 'utf8'));
const manifestChanged = manifest.pyproc !== ver;
manifest.pyproc = ver;
if (after === before && !manifestChanged) {
	console.log(`이미 ${ver} (변경 없음)`);
	process.exit(0);
}
if (after !== before) writeFileSync(PKG, after);
if (manifestChanged) writeFileSync(MANIFEST, JSON.stringify(manifest, null, 2) + '\n');
console.log(`pyproc -> ${ver}`);
