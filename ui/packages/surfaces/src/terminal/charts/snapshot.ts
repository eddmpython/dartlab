// 차트 스냅샷 PNG · klinecharts getConvertPictureUrl + 하단 출처 띠 합성.
// DOM 의 .chartSrc 캡션은 라이브러리 캔버스에 포함되지 않으므로, 공공누리 출처표시 의무를
// 이미지 산출물에 보존하는 유일 경로가 이 합성이다. 다크 배경·png·오버레이 포함 3인자 전부 명시.
export async function downloadSnapshot(chart: { getConvertPictureUrl?: (o: boolean, t: string, bg: string) => string }, opts: { fileTag: string; srcLine: string }): Promise<void> {
	const url = chart?.getConvertPictureUrl?.(true, 'png', '#0b0e14');
	if (!url) return;
	const img = new Image();
	await new Promise<void>((resolve, reject) => {
		img.onload = () => resolve();
		img.onerror = () => reject(new Error('snapshot image load'));
		img.src = url;
	});
	const pad = 26;
	const cv = document.createElement('canvas');
	cv.width = img.width;
	cv.height = img.height + pad;
	const ctx = cv.getContext('2d');
	if (!ctx) return;
	ctx.fillStyle = '#0b0e14';
	ctx.fillRect(0, 0, cv.width, cv.height);
	ctx.drawImage(img, 0, 0);
	ctx.fillStyle = '#7b828f';
	ctx.font = '11px ui-monospace, monospace';
	ctx.textBaseline = 'middle';
	ctx.fillText(opts.srcLine, 8, img.height + pad / 2);
	const blob: Blob | null = await new Promise((resolve) => cv.toBlob(resolve, 'image/png'));
	if (!blob) return;
	const a = document.createElement('a');
	a.href = URL.createObjectURL(blob);
	a.download = `dartlab_${opts.fileTag}.png`;
	a.click();
	setTimeout(() => URL.revokeObjectURL(a.href), 4000);
}
