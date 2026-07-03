// IPO 공모(증권신고서 지분증권) 계약. 발굴 목록은 공개·로컬 공통배선(라이브 워커 read-through, 베이크 0),
// 단건 6카테고리 리포트는 로컬 /api 런타임 파싱(무거운 본문 파싱 = 로컬 상위집합). 상장 전 발행사(corp_cls=E)는
// allFilings HF bake(상장사 Y/K 한정)에 없어 라이브 경로가 유일한 퍼블릭 데이터원이다.
// 판별 정본 = src/dartlab/providers/dart/securitiesRegistration.classifyIpo (3조건: 지분증권 subtype +
// corp_cls=E + 빈 stock_code). 어댑터 TS 미러는 그 정본을 가리키는 소비 필터일 뿐 정의를 소유하지 않는다.

/** 발행사 1곳의 발굴 항목. 최신 FULL 신고서(초판·기재정정) + 확정공모가 doc 유무. */
export interface IpoFiling {
	corpName: string;
	/** DART corp_code. 발행사 그룹핑 키(상장 전이라 stock_code 없음). */
	corpCode: string;
	/** 최신 FULL 증권신고서(지분증권) 접수번호. 리포트 파싱 대상. */
	rceptNo: string;
	rceptDate: string; // YYYY-MM-DD
	reportNm: string;
	isSpac: boolean;
	/** 기재정정 이력 여부(최신 FULL 이 정정본). */
	corrected: boolean;
	/** [발행조건확정] doc 접수번호. 확정공모가 공시됨(리포트에 병합). 미공시는 null. */
	confirmationRceptNo: string | null;
	confirmationDate: string | null; // YYYY-MM-DD
	/** DART 원문(사용자 표시용 링크아웃). */
	url: string;
}

/** 리포트 KPI 스트립용 typed 핵심값. 서버(renderIpoReport summary)와 1:1. 미산출 null. */
export interface IpoReportSummary {
	/** 발행사 적용 평가모형(예 'PER' | 'EV/EBITDA'). peerPer 는 이 모형 기준 배수라
	 *  PER 모형이 아닐 때 impliedPer 와 좌표 비교 금지(이종 기준 오도 차단). */
	model: string | null;
	priceBand: [number, number] | null;
	confirmedPrice: number | null;
	/** '밴드 상단' | '밴드 하단' | '밴드 내'. 확정가 없으면 null. */
	bandLocation: string | null;
	offerTotal: number | null; // 원
	marketCap: [number, number] | null; // 예상 시가총액(원)
	subscription: string | null; // 청약기일 원문
	freeFloatPct: number | null; // 상장 직후 유통가능비율 %
	impliedPer: [number, number] | null;
	peerPer: number | null; // 발행사 적용 비교기업 PER
	isLoss: boolean;
	/** 항등식 자기검증(원문 관계식). valuationChain·financialsBalance·floatBalance·offeringRawQtyOk. */
	identities: Record<string, boolean>;
}

export interface IpoReportSection {
	title: string;
	/** '✓ 검증' | '✗ 미검증' | null. 원문 항등식 자기검증 배지. */
	badge: string | null;
	rows: [string, string][]; // (라벨, 값)
}

export interface IpoReport {
	title: string;
	/** 본문 fetch 실패 시 null(sections 빈 배열 + markdown 에 사유). */
	summary: IpoReportSummary | null;
	sections: IpoReportSection[];
	markdown: string;
}

export interface IpoPort {
	/** 최근(85일 · DART list 3개월 제한 여유) IPO 발굴. 공개·로컬 공통배선(라이브 워커). 미배선/실패 = []. */
	recent(): Promise<IpoFiling[]>;
	/**
	 * 단건 6카테고리 공모분석 리포트. 로컬 서버(/api/dart/ipo/report) 런타임 파싱(수초).
	 * 공개 어댑터는 notWiredYet(로컬 상위집합 전용). surface 는 env.kind==='local' 로 진입을 게이트한다.
	 */
	report(input: { rceptNo: string; corpName?: string; confirmationRceptNo?: string | null }): Promise<IpoReport | null>;
}
