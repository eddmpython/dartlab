/**
 * ViewerBlock → ChartSpec 변환 함수.
 * 프론트엔드에서 finance 블록 데이터를 직접 ChartSpec으로 변환한다.
 */
import { COLORS, AREA_LABELS, GRADE_MAP } from './colors.js';

/**
 * finance ViewerBlock → combo ChartSpec.
 * block.data = { columns: [...], rows: [...] }
 * block.meta = { periods: [...], unit: "백만원", scale: "백만" }
 */
export function financeBlockToChartSpec(block) {
  if (!block?.data?.rows || !block?.data?.columns) return null;

  const { rows, columns } = block.data;
  const meta = block.meta || {};
  const periodCols = columns.filter((c) => /^\d{4}/.test(c));
  if (periodCols.length < 2) return null;

  // 첫 컬럼이 항목명
  const itemCol = columns[0];
  const series = [];
  const chartTypes = ['bar', 'line', 'line'];

  // 상위 3개 항목만 차트 시리즈로
  const topRows = rows.slice(0, 3);
  topRows.forEach((row, i) => {
    const name = row[itemCol] || `항목${i}`;
    const data = periodCols.map((p) => {
      const v = row[p];
      return v != null ? Number(v) : 0;
    });
    if (data.some((v) => v !== 0)) {
      series.push({
        name,
        data,
        color: COLORS[i % COLORS.length],
        type: chartTypes[i] || 'line',
      });
    }
  });

  if (series.length === 0) return null;

  return {
    chartType: 'combo',
    title: meta.title || '재무 추이',
    series,
    categories: periodCols,
    options: { unit: meta.unit || '백만원' },
  };
}

/**
 * insights grades → radar ChartSpec.
 */
export function insightToRadarSpec(insights, corpName = '') {
  if (!insights) return null;

  const areaNames = Object.keys(AREA_LABELS);
  const categories = areaNames.map((n) => AREA_LABELS[n]);
  const data = areaNames.map((n) => {
    const grade = insights[n]?.grade || insights[n] || 'F';
    return GRADE_MAP[grade] ?? 0;
  });

  return {
    chartType: 'radar',
    title: corpName ? `${corpName} 투자 인사이트` : '투자 인사이트',
    series: [{ name: corpName || '등급', data, color: COLORS[0] }],
    categories,
    options: { maxValue: 5 },
  };
}
