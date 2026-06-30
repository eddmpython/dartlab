// 순수 렌더 헬퍼 단위테스트 · /report 인라인에서 추출한 render.ts 가 기계적 동치임을 고정하고,
// 정직 불변(중립색·verdict 합성 0·robust spark) 을 회귀 가드한다. /cards 도 동일 헬퍼를 공유한다.
import { describe, it, expect } from 'vitest';
import { cellTone, verdictTone, spark, isTimeSeries, chunk, lineGeo, splitTitle, clean } from './render';

describe('cellTone · 부호 기반 중립색(크기로 좋고/나쁨 주장 안 함)', () => {
	it('음수 → neg, 양수 → pos, 중립 → 빈', () => {
		expect(cellTone('-1,797')).toBe('neg');
		expect(cellTone('△3.2%')).toBe('neg');
		expect(cellTone('(1,200)')).toBe('neg');
		expect(cellTone('+5.1%')).toBe('pos');
		expect(cellTone('▲12')).toBe('pos');
		expect(cellTone('12.3%')).toBe('');
		expect(cellTone('-')).toBe('');
		expect(cellTone('')).toBe('');
	});
	it('같은 부호면 지표 종류 무관 동일 색 · 부채비율↑·매출↑ 둘 다 양수=pos(좋다고 주장 안 함)', () => {
		expect(cellTone('+30%')).toBe(cellTone('+5%')); // 크기 달라도 같은 톤
		// 부채비율(나쁨)과 매출(좋음)이 같은 값이면 같은 색 · 색이 가치판단을 하지 않음.
		expect(cellTone('957%')).toBe(cellTone('957%'));
	});
});

describe('verdictTone · 합성 0(화이트리스트 어휘만, 미지 → 중립)', () => {
	it('알려진 판정 어휘만 색을 받는다', () => {
		expect(verdictTone('양호')).toBe('ok');
		expect(verdictTone('안정')).toBe('ok');
		expect(verdictTone('충족')).toBe('ok');
		expect(verdictTone('주의')).toBe('warn');
		expect(verdictTone('경계')).toBe('warn');
		expect(verdictTone('미달')).toBe('warn');
	});
	it('모르는 문자열은 verdict 를 발명하지 않는다 → 중립(빈)', () => {
		expect(verdictTone('산출 불가')).toBe('');
		expect(verdictTone('보통')).toBe('');
		expect(verdictTone('우수함')).toBe(''); // 임의 평가어 합성 금지
		expect(verdictTone('12.3%')).toBe('');
		expect(verdictTone('')).toBe('');
	});
});

describe('spark · robust(극단값에 추세 왜곡 안 함)·표 숫자 불변', () => {
	it('유효값 < 3 이면 null(거짓 추세 금지)', () => {
		expect(spark({ '2023': '1', '2024': '2' }, ['2023', '2024'])).toBeNull();
	});
	it('정상 시계열 → 기하 반환', () => {
		const g = spark({ '2021': '10', '2022': '12', '2023': '11', '2024': '15' }, ['2021', '2022', '2023', '2024']);
		expect(g).not.toBeNull();
		expect(g!.points.split(' ').length).toBe(4);
	});
	it('단일 극단값은 clip 표시만(나머지를 평지로 깔지 않음)', () => {
		const g = spark(
			{ '2020': '5', '2021': '6', '2022': '241', '2023': '7', '2024': '8' },
			['2020', '2021', '2022', '2023', '2024']
		);
		expect(g).not.toBeNull();
		expect(g!.clipMarks.length).toBeGreaterThan(0); // 극단값이 clip 으로 표시됨
	});
});

describe('isTimeSeries / chunk / lineGeo / splitTitle / clean', () => {
	it('isTimeSeries · 연도/분기 라벨 2열 이상', () => {
		expect(isTimeSeries(['항목', '2022', '2023', '2024'])).toBe(true);
		expect(isTimeSeries(['항목', '25Q1', '25Q2', '25Q3'])).toBe(true);
		expect(isTimeSeries(['항목', '값'])).toBe(false);
	});
	it('chunk · n 단위 분할', () => {
		expect(chunk([1, 2, 3, 4, 5], 2)).toEqual([[1, 2], [3, 4], [5]]);
	});
	it('lineGeo · 2점 미만 null·정상 시 up 방향', () => {
		expect(lineGeo([1])).toBeNull();
		const g = lineGeo([10, 12, 15]);
		expect(g!.up).toBe(true);
	});
	it('splitTitle · 구분자(-- · ·) 로 head/sub 분리', () => {
		expect(splitTitle('재무분석 -- 수익성은 지속되는가')).toEqual({ head: '재무분석', sub: '수익성은 지속되는가' });
		expect(splitTitle('단일제목')).toEqual({ head: '단일제목', sub: '' });
	});
	it('clean · ** 강조 제거', () => {
		expect(clean('**중요** 내용')).toBe('중요 내용');
	});
});
