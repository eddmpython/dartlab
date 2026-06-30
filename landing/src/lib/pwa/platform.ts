// PWA 플랫폼 감지 — InstallPrompt·NotifyOptIn 공유(중복 방지). 순수 함수, 브라우저 전용(window/navigator 사용).
// InstallPrompt 에서 순수 추출(동작 불변). 둘 다 여기서 import.

/** 홈화면 설치 PWA(standalone)로 실행 중인가. iOS 웹푸시 권한은 standalone 안에서만 가능. */
export function isStandalone(): boolean {
	return (
		window.matchMedia('(display-mode: standalone)').matches ||
		(navigator as unknown as { standalone?: boolean }).standalone === true
	);
}

/** iOS Safari 탭(설치 안 된 상태)인가. Chrome/Firefox/Edge on iOS 는 제외. */
export function isIosSafari(): boolean {
	const ua = navigator.userAgent;
	return /iphone|ipad|ipod/i.test(ua) && /safari/i.test(ua) && !/crios|fxios|edgios/i.test(ua);
}
