// 레슨 레지스트리. YAML 원본을 그대로 읽어 목록과 본문을 낸다.
//
// 로딩 전략. `import.meta.glob(..., { query: '?raw' })` 로 YAML **원본 문자열**을 번들에 싣고
// 브라우저가 런타임에 파싱한다. 파생 산출물(구운 JSON·TS)이 없으므로 SSOT 가 그대로 배송된다.
// blog(`lib/blog/posts.ts`)와 Skill OS(`lib/skills/catalog.ts`)가 이미 쓰는 패턴과 같다.
//
// 규모 가드. 레슨은 편당 2~3KB 라 62 편이어도 raw 약 190KB(gzip 약 45KB)다. 이 정도는 eager 로
// 실어도 허브 첫 로드에 문제가 없고, 대신 색인과 본문이 **한 진실**을 공유한다. 다만 corpus 가
// 커지면 이 전제가 깨진다. `tests/audit/lessonSchema.py` 가 총 바이트 임계를 강제하고, 넘으면
// 그때 색인(경량 메타)과 본문(지연 청크)을 분리하라고 실패로 알려 준다. 미리 나누지 않는다.
import { parse } from 'yaml';

import type { Lesson, LessonLevel, LessonSummary, LessonTrack } from './types';

const rawLessons = import.meta.glob('./content/**/*.yaml', {
	eager: true,
	query: '?raw',
	import: 'default'
}) as Record<string, string>;

/** 트랙 정의 SSOT. 폴더 이름과 1:1. 새 트랙은 여기 한 줄 + 폴더 하나. */
export const TRACKS: LessonTrack[] = [
	{ id: 'foundations', title: '시작', blurb: '회사 하나를 잡는 것에서 시작합니다.', order: 1 },
	{ id: 'financials', title: '회사 재무', blurb: '재무제표를 꺼내고 계정을 직접 굴립니다.', order: 2 },
	{ id: 'engines', title: '판독 엔진', blurb: '22축 분석 · 신용등급 · 서사.', order: 3 },
	{ id: 'market', title: '시장 횡단', blurb: '한 회사가 아니라 상장사 전체를 한 표로.', order: 4 },
	// 도감은 축을 YAML 에 베끼지 않는다. 엔진 카탈로그(axis·label·description·example)를 런타임에 읽는다.
	// 축이 늘거나 이름이 바뀌면 도감이 저절로 따라간다. 사본이 없으니 어긋날 자리도 없다.
	{ id: 'catalog', title: '엔진 도감', blurb: '엔진이 무엇을 할 수 있는지 카탈로그로 전수 훑기.', order: 5 }
];

export const LEVELS: LessonLevel[] = ['기초', '중급', '심화'];

function parseLesson(raw: string, path: string): Lesson {
	const doc = parse(raw) as Lesson;
	if (!doc?.meta?.id) throw new Error(`레슨 스키마 위반(meta.id 없음): ${path}`);
	return doc;
}

const lessons: Lesson[] = Object.entries(rawLessons)
	.map(([path, raw]) => parseLesson(raw, path))
	.sort((a, b) => {
		const ta = TRACKS.findIndex((t) => t.id === a.meta.track);
		const tb = TRACKS.findIndex((t) => t.id === b.meta.track);
		return ta !== tb ? ta - tb : a.meta.order - b.meta.order;
	});

const byId = new Map(lessons.map((l) => [l.meta.id, l]));

/** 허브 그리드용 경량 목록(본문 셀 없음). */
export function listLessons(): LessonSummary[] {
	return lessons.map((l) => ({ ...l.meta, sectionCount: l.sections.length }));
}

export function getLesson(id: string): Lesson | undefined {
	return byId.get(id);
}

export function lessonsOfTrack(trackId: string): LessonSummary[] {
	return listLessons().filter((l) => l.track === trackId);
}

/** 총 레슨 수. 허브 헤드라인·테스트가 쓴다. */
export function lessonCount(): number {
	return lessons.length;
}

// 브라우저에서 도는 중임을 매 레슨 말미에 밝힌다. 무엇이 되고 무엇이 안 되는지 먼저 알려 주는 것이
// 예의고, 경계를 가르치는 셀(expectError)의 맥락이 된다.
const BROWSER_NOTE = `---

**브라우저에서 도는 중입니다.** 공시 · 재무 데이터는 HuggingFace 에서 바로 받아 브라우저 안에서
계산합니다. 설치한 파이썬이 없어도 되고, 결과가 서버로 나가지도 않습니다. 반대로 실시간 시세 ·
수급 · 뉴스처럼 바깥으로 나가야 하는 수집은 브라우저 보안 정책에 막혀 로컬 설치본에서만 됩니다.`;

/** `meta.company` 가 있으면 넣는 공유 부트스트랩. import 한 줄이면 워커가 알아서 설치한다. */
function setupCode(company: string): string {
	return `# dartlab 은 import 하면 노트북이 알아서 설치한다 (최초 1회 약 20초).
import dartlab
c = dartlab.Company("${company}")   # 데스크톱과 동일. 데이터는 첫 접근 시 자동 다운로드`;
}

export interface LessonCell {
	id: string;
	type: 'code' | 'markdown';
	content: string;
	/** `local` 셀은 브라우저에서 읽기 전용으로 렌더한다. */
	runtime: 'pyodide' | 'local';
}

/**
 * 레슨을 열었을 때 저장되는 노트북 id. 레슨 id 에서 **결정적**으로 나온다.
 *
 * 예전에는 레슨을 열 때마다 `crypto.randomUUID()` 로 사본을 만들었다. 같은 레슨을 세 번 열면
 * IndexedDB 에 사본이 세 개 쌓였고, 사용자가 어제 하던 진도로 돌아갈 방법도 없었다. 안정 id 를
 * 쓰면 다시 열기가 곧 이어하기가 되고, 저장 개수가 레슨 수를 넘지 않는다.
 */
export function lessonNotebookId(lessonId: string): string {
	return `lesson:${lessonId}`;
}

/** `lesson:` 접두 노트북인가 (허브가 내 노트북 목록에서 걸러 낼 때 쓴다). */
export function isLessonNotebook(notebookId: string): boolean {
	return notebookId.startsWith('lesson:');
}

/**
 * 레슨(SSOT) 을 노트북 셀로 투영한다.
 *
 * 셀 id 는 레슨 id 와 섹션 id 로 **결정적**으로 만든다. 그래야 레슨 원본을 나중에 고쳐도
 * 사용자가 그 셀에 남긴 편집(진도 오버레이)이 계속 붙는다. 인덱스 기반이면 섹션을 하나 끼워
 * 넣는 순간 사용자의 편집이 엉뚱한 셀로 옮겨 간다.
 */
export function lessonToCells(lesson: Lesson): LessonCell[] {
	const cells: LessonCell[] = [];
	const push = (id: string, type: LessonCell['type'], content: string, runtime: LessonCell['runtime'] = 'pyodide') =>
		cells.push({ id: `${lesson.meta.id}::${id}`, type, content, runtime });

	push('intro', 'markdown', `# ${lesson.meta.title}\n\n${lesson.intro.body.trim()}\n\n${BROWSER_NOTE}`);
	if (lesson.meta.company) push('setup', 'code', setupCode(lesson.meta.company));

	for (const section of lesson.sections) {
		const heading = section.title ? `## ${section.title}\n\n` : '';
		const body = section.body?.trim() ?? '';
		if (heading || body) push(`${section.id}:md`, 'markdown', `${heading}${body}`.trim());
		if (section.code) push(section.id, 'code', section.code.trim(), section.runtime ?? 'pyodide');
	}
	return cells;
}
