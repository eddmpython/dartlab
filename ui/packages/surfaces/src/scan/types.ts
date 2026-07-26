/**
 * Scan Studio (`/scan`) · 공유 타입 정의.
 *
 * MetricKey/MetricGroup 은 metrics.ts 에서 catalog 에서 자동 도출 (SSOT 한 곳).
 * 본 파일은 그것에 의존 안 하는 generic 타입만 둔다 (순환 import 방지).
 */

export type Op = '>' | '>=' | '<' | '<=' | '==' | '!=' | 'between' | 'contains' | 'in' | 'exists';

/** 단일 필터 조건. between 일 때는 value2 도 사용. */
export interface FilterCond {
	metric: string;
	op: Op;
	value?: number | string | string[];
	value2?: number | string;
	/** true 면 조건 결과 반전 (NOT). 기본 false. */
	negate?: boolean;
}

/** 정렬 키 + 방향. */
export interface SortKey {
	key: string;
	dir: 'asc' | 'desc';
}

/** 메트릭 데이터 소스 · 런타임 projection 단위. */
export type MetricSource =
	| 'ecosystem'
	| 'valuation'
	| 'prices'
	| 'changes'
	| 'productIndex'
	| 'finance5y'
	| 'priceTrend'
	| 'report';

/** 표 셀에 직접 그리는 짧은 시계열. */
export interface SeriesMetric {
	labels: string[];
	values: Array<number | null>;
	unit: string;
	source: string;
}

/** 메트릭 정의 · UI 헤더 툴팁 + 포맷터 + 그리드 정렬 보조.
 *
 * 구체 MetricGroup union 은 metrics.ts 에서 정의. 여기는 string 으로 약하게.
 */
export interface MetricDef {
	key: string;
	/** 컬럼 헤더 표기 (한국어) */
	label: string;
	/** 그룹 · 컬럼 그룹 toggle 단위 */
	group: string;
	/** 'number' = 정렬·필터 가능, 'text' = 검색만, 'enum' = 칩 선택, 'series' = sparkline */
	type: 'number' | 'text' | 'enum' | 'series';
	/** 단위 (% · 원 · 배 · 명 · 점 등). type=number 한정 */
	unit?: string;
	/** 한국어 설명 (컬럼 헤더 hover 툴팁 + 정의 + 좋은 방향) */
	definition: string;
	/** enum 값들 (type=enum 한정) */
	values?: readonly string[];
	/** true = 큰 값일수록 좋음, false = 작을수록 좋음, undefined = 중립 */
	higherBetter?: boolean;
	/** 데이터 소스 · DuckDB SQL projection 단위 */
	source: MetricSource;
	/** parquet source 인 경우 SQL projection snippet (column alias = key) */
	sql?: string;
	/** 포맷 변환 (raw 값 → 표시 문자열). 미지정 시 toString. */
	format?: (v: unknown) => string;
	/** 분포 패널 스케일 · 시총·매출은 'log' 권장. 기본 'linear'. */
	distribution?: 'linear' | 'log';
}

/** 통합 노드 · ecosystem + parquet maps 를 join 한 결과. */
export interface ScanNode {
	id: string;
	label: string;
	industry: string;
	industryName?: string;
	color?: string;
	[key: string]: unknown;
}

/** URL 쿼리 직렬화 페이로드 (v2).
 *
 * 키 추가는 **optional 만** 허용한다. 야생의 옛 공유 링크(sitemap 등재 /scan)가 계속
 * 해석되어야 하므로 기존 키의 이름·의미는 불변이다.
 */
export interface ScanPayload {
	v: 2;
	i: string[];
	c: FilterCond[];
	s: SortKey[];
	cols: string[];
	p?: string;
	sel?: string;
	/** 조회 시장 범위 (KR/US/ALL). 없으면 KR. 옛 페이로드 호환. */
	m?: 'KR' | 'US' | 'ALL';
}

/** Workspace · 사용자 저장 컬럼셋 (PR-E 에서 활용). */
export interface SavedColumnSet {
	id: string;
	name: string;
	cols: string[];
	conds: FilterCond[];
	sort: SortKey[];
	createdAt: number;
}
