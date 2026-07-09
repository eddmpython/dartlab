// 레슨 SSOT 스키마. 레슨 한 편 = YAML 파일 한 개.
//
// 왜 YAML 인가. 이 파일을 읽는 소비자가 둘이다. 브라우저(여기 registry.ts)와 파이썬
// (tests/audit/notebookContract.py 계약 게이트, 앞으로의 colab/marimo 투영기). TS 는 파이썬이
// 못 읽고, JSON 은 사람이 못 쓴다. YAML 이 그 교집합이다. 원본 파일을 그대로(raw) 번들에 실어
// 브라우저가 런타임에 파싱하므로, 파생 산출물을 굽지 않는다(SSOT 그대로 배송).
//
// 왜 파일 하나에 레슨 하나인가. 레슨이 수십 편을 넘어가면 한 파일 레지스트리는 병합 충돌과
// 리뷰 소음으로 무너진다. 파일 단위여야 레슨 하나의 diff 가 깨끗하고, 번들러가 편별로 청크를
// 쪼갤 수 있어 허브 첫 로드가 레슨 수와 무관하게 평탄해진다.

/** 커리큘럼 단계. 허브 갤러리가 이 순서로 묶는다. */
export type LessonLevel = '기초' | '중급' | '심화';

/** 셀이 어디서 도는가. 브라우저에서 못 도는 호출을 pyodide 로 태깅해 배포하는 것을 막는다. */
export type LessonRuntime = 'pyodide' | 'local';

/** 레슨 트랙. 폴더 이름과 1:1. */
export interface LessonTrack {
	id: string;
	title: string;
	blurb: string;
	order: number;
}

export interface LessonSection {
	/** 레슨 안에서 유일. 진도 오버레이가 셀을 이 id 로 매칭하므로 바꾸면 사용자 편집이 끊긴다. */
	id: string;
	title?: string;
	/** 코드 셀 위에 붙는 설명 markdown. */
	body?: string;
	/** 실행 셀 파이썬 코드. 없으면 markdown 전용 섹션. */
	code?: string;
	/** 기본 pyodide. `local` 이면 브라우저에서 읽기 전용으로 렌더한다. */
	runtime?: LessonRuntime;
	/** 이 셀은 브라우저에서 예외가 나는 것이 정상이다(경계를 가르치는 셀). */
	expectError?: boolean;
}

export interface LessonMeta {
	/** corpus 유일. 폴더/파일명에서 파생하지 않고 명시한다(파일을 옮겨도 진도가 안 끊긴다). */
	id: string;
	title: string;
	description: string;
	level: LessonLevel;
	track: string;
	/** 트랙 안에서의 순서. */
	order: number;
	tags: string[];
	/** 다른 레슨 id. 사이클 금지(검증기가 위상 정렬로 확인). */
	prerequisites?: string[];
	/** setup 셀에 주입할 종목코드. 없으면 setup 셀을 넣지 않는다. */
	company?: string;
	/** 예상 소요(분). */
	minutes?: number;
}

export interface Lesson {
	meta: LessonMeta;
	intro: { goal: string; body: string };
	sections: LessonSection[];
}

/** 허브 그리드가 쓰는 경량 메타. 레슨 본문(셀) 없이 이것만 eager 로 싣는다. */
export type LessonSummary = LessonMeta & { sectionCount: number };
