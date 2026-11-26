// UI 런타임 데이터층 배선 가드. 데이터 워크벤치 SSOT 의 기계 강제.
//
// 대상: ui/packages/runtime/src/adapters/**/sources/*.ts (source 레이어).
// 파서: TypeScript 컴파일러 API (ts.createSourceFile → AST walk) — 정규식이 못 거르는
//       문자열·주석 속 fetch/Map false positive 를 의미 기반 검출로 제거(06 §2 정공법).
//
// 가드 규칙(06 §2):
//   1. source 안 raw `fetch(` 호출 금지 — 코어/게이트(data/fetch.request) 경유.
//   2. source 안 데이터 오리진 URL 문자열 직접 구성 금지 — origins 레지스트리 경유.
//      (huggingface·workers.dev·hf-proxy 토큰 + http(s):// 리터럴. 단 공시 표시용 dart.fss.or.kr
//       링크는 데이터 오리진이 아니므로 allowlist — 보수적 false positive 차단.)
//   3. source 안 모듈 레벨 `new Map(` 캐시 신설 금지 — 코어 캐시 사용.
//      (보수적: 모듈 스코프 + 변수명이 Cache 로 끝나는 할당만. 함수 내 transform Map·상수 lookup
//       table 은 정당하므로 미검출.)
//   4. source 안 `createDataCore(` 호출 금지 — 코어는 어댑터(createXRuntime)가 만들어 주입.
//      EXCEPT financeSource.ts 의 loadFinanceRows 경로(landing 주입 콜백, 시그니처 불변 제약) 1건 allowlist.
//   5. 전역: createDataCore / new RuntimeCache / new RequestDedup 인스턴스화 ≥1
//      (죽은 작업대 재발 방지 — data/fetch/request.ts + 어댑터 스캔, 0 이면 fail).
//   6. source 안 hfRange 저수준 로더(readParquetRows·readParquetWholeFile) 직접 import 금지 —
//      코어(core.requestParquet*) 경유. 파서 가드 사각(직접 read = 캐시·dedup 우회) 차단. type import 는 허용.
//
// baseline 부채원장(uiDataWiring.baseline.json): 착수 시점 잔존 위반을 기록 → 이후 *신규 위반만* fail
//   (회귀가드 철학, operation.testing 동일). 이관 완료 source 부터 baseline 에서 사라지며 0 으로 수렴.
//
// 실행: node tests/audit/checkUiDataWiring.mjs            (스캔 + baseline 대조, 신규 위반 시 exit 1)
//       node tests/audit/checkUiDataWiring.mjs --write-baseline   (현 위반을 baseline 으로 기록)
//
// exit 0 = 신규 위반 0(통과). exit 1 = 신규 위반(회귀). exit 2 = 전역 인스턴스화 위반 또는 도구 오류.

import ts from 'typescript';
import { readFileSync, writeFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join, relative } from 'node:path';
import { globSync } from 'node:fs';

const SELF_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = join(SELF_DIR, '..', '..'); // tests/audit → repo root
const RUNTIME_SRC = join(REPO_ROOT, 'ui', 'packages', 'runtime', 'src');
const SOURCES_GLOB = join(RUNTIME_SRC, 'adapters', '**', 'sources', '*.ts');
const BASELINE_PATH = join(SELF_DIR, 'uiDataWiring.baseline.json');

// 데이터 오리진 호스트 토큰 — 항상 위반(레지스트리 경유 강제).
const ORIGIN_TOKENS = ['huggingface', 'workers.dev', 'hf-proxy'];
// 공시 표시용 링크(데이터 fetch 가 아닌 사용자 표시 URL) — http(s) 리터럴 검사에서 제외.
const DISPLAY_URL_ALLOW = ['dart.fss.or.kr'];

// rule 4 allowlist — 비움. 옛 8 source 의 무인자-레거시 폴백 core 8 copy 는 data/fetch.moduleFallbackCore()
//   헬퍼 1개로 통합(createDataCore 호출이 source 밖으로 모임) → source 안 createDataCore 직접 호출 0건.
//   향후 source 가 직접 createDataCore 를 부를 정당한 사유가 생기면 여기 등록(기본 = 어댑터 주입 또는 헬퍼).
const CREATE_CORE_ALLOW = [];

// rule 6 — source 안에서 직접 import 금지인 저수준 데이터 로더(코어 data/fetch.request 경유 강제).
//   파서 가드의 사각: createDataCore 우회하고 hfRange 의 parquet read 를 직접 부르면 캐시·dedup 이 안 걸린다.
const RAW_LOADERS = ['readParquetRows', 'readParquetWholeFile'];

/** posix 상대경로(baseline 비교 안정 — OS 무관). */
const relPosix = (abs) => relative(REPO_ROOT, abs).split('\\').join('/');

/** 단일 source 파일 위반 수집. */
function scanSourceFile(absPath) {
	const text = readFileSync(absPath, 'utf-8');
	const sf = ts.createSourceFile(absPath, text, ts.ScriptTarget.Latest, /*setParentNodes*/ true, ts.ScriptKind.TS);
	const rel = relPosix(absPath);
	const fileName = absPath.split(/[\\/]/).pop();
	const violations = [];
	const add = (rule, node, detail) => {
		const { line } = sf.getLineAndCharacterOfPosition(node.getStart(sf));
		violations.push({ file: rel, line: line + 1, rule, detail });
	};

	// 모듈(최상위) 스코프 여부 — node 의 조상에 함수/메서드/화살표가 없으면 모듈 레벨.
	const isModuleScope = (node) => {
		for (let p = node.parent; p; p = p.parent) {
			if (
				ts.isFunctionDeclaration(p) ||
				ts.isFunctionExpression(p) ||
				ts.isArrowFunction(p) ||
				ts.isMethodDeclaration(p) ||
				ts.isConstructorDeclaration(p) ||
				ts.isGetAccessorDeclaration(p) ||
				ts.isSetAccessorDeclaration(p)
			) {
				return false;
			}
		}
		return true;
	};

	const visit = (node) => {
		// rule 1·4 — CallExpression(fetch / createDataCore)
		if (ts.isCallExpression(node) && ts.isIdentifier(node.expression)) {
			const callee = node.expression.text;
			if (callee === 'fetch') {
				add(1, node, 'raw fetch() — data/fetch.request 경유');
			} else if (callee === 'createDataCore') {
				// allowlist: financeSource.ts 의 financeRowsCore() 내부 호출.
				const enclosing = enclosingFnName(node);
				const allowed = CREATE_CORE_ALLOW.some((a) => a.file === fileName && a.fn === enclosing);
				if (!allowed) add(4, node, 'createDataCore() — 어댑터(createXRuntime)가 주입');
			}
		}
		// rule 3 — 모듈 레벨 `const xCache = new Map(...)`
		if (
			ts.isNewExpression(node) &&
			ts.isIdentifier(node.expression) &&
			node.expression.text === 'Map' &&
			isModuleScope(node)
		) {
			const name = declaredVarName(node);
			if (name && /Cache$/.test(name)) {
				add(3, node, `module-level new Map cache: ${name} — 코어 캐시 사용`);
			}
		}
		// rule 6 — hfRange 저수준 parquet 로더 직접 import(코어 우회) 금지
		if (
			ts.isImportDeclaration(node) &&
			ts.isStringLiteral(node.moduleSpecifier) &&
			/\/hfRange$/.test(node.moduleSpecifier.text) &&
			node.importClause?.namedBindings &&
			ts.isNamedImports(node.importClause.namedBindings)
		) {
			for (const spec of node.importClause.namedBindings.elements) {
				// 값 import 만(type import·`import type {…}` 은 제외 — FetchLike 등 타입은 허용).
				if (!node.importClause.isTypeOnly && !spec.isTypeOnly && RAW_LOADERS.includes(spec.name.text)) {
					add(6, node, `'${spec.name.text}' 직접 import(hfRange) — core.requestParquet* 경유`);
				}
			}
		}
		// rule 2 — 데이터 오리진 URL 문자열 리터럴
		if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
			checkUrlLiteral(node.text, node);
		}
		if (ts.isTemplateExpression(node)) {
			// 템플릿 리터럴: head + 각 span 의 literal 부분만 검사(표현식부 무시).
			checkUrlLiteral(node.head.text, node);
			for (const span of node.templateSpans) checkUrlLiteral(span.literal.text, node);
		}
		ts.forEachChild(node, visit);
	};

	const checkUrlLiteral = (value, node) => {
		const lower = value.toLowerCase();
		for (const tok of ORIGIN_TOKENS) {
			if (lower.includes(tok)) {
				add(2, node, `오리진 URL 토큰 '${tok}' — origins 레지스트리 경유`);
				return;
			}
		}
		const m = lower.match(/https?:\/\/([^\s/"'`]+)/);
		if (m) {
			const host = m[1];
			if (!DISPLAY_URL_ALLOW.some((h) => host.includes(h))) {
				add(2, node, `직접 URL 리터럴 'http(s)://${host}…' — origins 레지스트리 경유`);
			}
		}
	};

	// new/call 을 감싸는 변수 선언자 이름.
	function declaredVarName(node) {
		for (let p = node.parent; p; p = p.parent) {
			if (ts.isVariableDeclaration(p) && ts.isIdentifier(p.name)) return p.name.text;
			if (ts.isPropertyAssignment(p) || ts.isBinaryExpression(p)) break;
		}
		return null;
	}
	// node 를 감싸는 가장 가까운 명명 함수/화살표 변수 이름(rule 4 allowlist 판정).
	function enclosingFnName(node) {
		for (let p = node.parent; p; p = p.parent) {
			if (ts.isFunctionDeclaration(p) && p.name) return p.name.text;
			if ((ts.isArrowFunction(p) || ts.isFunctionExpression(p)) && p.parent && ts.isVariableDeclaration(p.parent) && ts.isIdentifier(p.parent.name)) {
				return p.parent.name.text;
			}
		}
		return null;
	}

	visit(sf);
	return violations;
}

/** rule 5 전역 — createDataCore / new RuntimeCache / new RequestDedup 인스턴스화 ≥1. */
function checkGlobalInstantiation() {
	const scanFiles = [
		join(RUNTIME_SRC, 'data', 'fetch', 'request.ts'),
		...globSync(join(RUNTIME_SRC, 'adapters', '**', '*.ts'))
	];
	const found = { createDataCore: false, RuntimeCache: false, RequestDedup: false };
	for (const f of scanFiles) {
		if (!existsSync(f)) continue;
		const text = readFileSync(f, 'utf-8');
		const sf = ts.createSourceFile(f, text, ts.ScriptTarget.Latest, false, ts.ScriptKind.TS);
		const visit = (node) => {
			if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 'createDataCore') {
				found.createDataCore = true;
			}
			if (ts.isNewExpression(node) && ts.isIdentifier(node.expression)) {
				if (node.expression.text === 'RuntimeCache') found.RuntimeCache = true;
				if (node.expression.text === 'RequestDedup') found.RequestDedup = true;
			}
			ts.forEachChild(node, visit);
		};
		visit(sf);
	}
	const missing = Object.entries(found)
		.filter(([, v]) => !v)
		.map(([k]) => k);
	return missing;
}

function loadBaseline() {
	if (!existsSync(BASELINE_PATH)) return null;
	return JSON.parse(readFileSync(BASELINE_PATH, 'utf-8'));
}

/** 위반 → 안정 키(파일·규칙·detail). line 은 키에서 제외 — 위아래 줄 이동에 강건. */
const vKey = (v) => `${v.file} ${v.rule} ${v.detail}`;

function main() {
	const writeMode = process.argv.includes('--write-baseline');

	const missing = checkGlobalInstantiation();
	if (missing.length) {
		console.error(`[checkUiDataWiring] FAIL (rule 5) — 죽은 작업대: 인스턴스화 0건 → ${missing.join(', ')}`);
		console.error('  createDataCore / new RuntimeCache / new RequestDedup 중 하나라도 코드베이스에 없으면 데이터 코어가 실배선 안 된 것.');
		return 2;
	}

	const files = globSync(SOURCES_GLOB).sort();
	if (files.length === 0) {
		console.error(`[checkUiDataWiring] FAIL — source 파일 0건 (경로 오류?): ${SOURCES_GLOB}`);
		return 2;
	}
	const all = [];
	for (const f of files) all.push(...scanSourceFile(f));
	all.sort((a, b) => a.file.localeCompare(b.file) || a.rule - b.rule || a.line - b.line);

	if (writeMode) {
		const payload = {
			_comment:
				'데이터 워크벤치 SSOT 가드(checkUiDataWiring.mjs) 부채원장. 착수 시점 잔존 위반. 신규 위반만 fail. ' +
				'이관 완료 source 는 여기서 사라지며 0 으로 수렴(증가 0 강제). 갱신: node tests/audit/checkUiDataWiring.mjs --write-baseline.',
			generatedAt: new Date().toISOString().slice(0, 10),
			ruleLegend: {
				1: 'raw fetch() in source',
				2: 'direct origin URL literal in source',
				3: 'module-level new Map cache in source',
				4: 'createDataCore() in source (financeSource.loadFinanceRows allowlisted)',
				5: 'global: createDataCore/RuntimeCache/RequestDedup must instantiate >=1',
				6: 'direct hfRange loader import (readParquetRows/WholeFile) in source'
			},
			violations: all.map(({ file, rule, detail }) => ({ file, rule, detail }))
		};
		writeFileSync(BASELINE_PATH, JSON.stringify(payload, null, '\t') + '\n', 'utf-8');
		console.log(`[checkUiDataWiring] baseline 기록: ${relPosix(BASELINE_PATH)} (${all.length} 위반, ${files.length} source 파일)`);
		return 0;
	}

	const baseline = loadBaseline();
	if (!baseline) {
		console.error(`[checkUiDataWiring] FAIL — baseline 부재: ${relPosix(BASELINE_PATH)}`);
		console.error('  먼저 `node tests/audit/checkUiDataWiring.mjs --write-baseline` 로 부채원장을 생성하세요.');
		return 2;
	}

	const baseSet = new Map();
	for (const b of baseline.violations) baseSet.set(vKey(b), (baseSet.get(vKey(b)) ?? 0) + 1);

	const curSet = new Map();
	for (const v of all) curSet.set(vKey(v), v);

	// 신규 위반: 현재 키가 baseline 에 없는 것 (또는 같은 키 개수가 baseline 초과 — 여기선 detail 에 변수명/host 포함이라 키 단위 충분).
	const newViolations = all.filter((v) => !baseSet.has(vKey(v)));
	// 해소된 baseline: baseline 에 있으나 현재 없는 것(부채 ratchet 가시화).
	const resolved = [...baseSet.keys()].filter((k) => !curSet.has(k));

	console.log(`[checkUiDataWiring] source 파일 ${files.length}개, 현재 위반 ${all.length}건, baseline ${baseline.violations.length}건.`);
	if (resolved.length) {
		console.log(`[checkUiDataWiring] 해소된 baseline ${resolved.length}건 (부채 ratchet — baseline 갱신 권장):`);
		for (const k of resolved) console.log(`    - ${k.split(' ').join(' · ')}`);
	}

	if (newViolations.length) {
		console.error(`[checkUiDataWiring] FAIL — 신규 위반 ${newViolations.length}건(회귀):`);
		for (const v of newViolations) {
			console.error(`    ${v.file}:${v.line}  [rule ${v.rule}]  ${v.detail}`);
		}
		console.error('  source 는 fetch·URL·캐시 Map 을 직접 갖지 않는다 — data/fetch.request + origins 레지스트리 경유(operation.ui 데이터층).');
		return 1;
	}

	console.log('[checkUiDataWiring] PASS — 신규 위반 0건.');
	return 0;
}

process.exit(main());
