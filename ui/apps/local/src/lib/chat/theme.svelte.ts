// 로컬 챗 테마. dark 기본, light 토글. tokens.css 가 :root[data-theme='light'] 로 surface·ink·line 을 재매핑한다.
// 옛 React ThemeProvider(shadcn dark-mode) 를 runes 로 옮긴 것. 셸 전용 UI 상태다.
const KEY = 'dartlab-local-theme';

function initial(): 'dark' | 'light' {
	if (typeof localStorage === 'undefined') return 'dark';
	return localStorage.getItem(KEY) === 'light' ? 'light' : 'dark';
}

class ThemeStore {
	value = $state<'dark' | 'light'>('dark');

	constructor() {
		this.value = initial();
	}

	/** 클라이언트 mount 이후 1회 호출. 저장된 테마를 documentElement 에 반영한다. */
	apply(): void {
		if (typeof document === 'undefined') return;
		const root = document.documentElement;
		if (this.value === 'light') root.setAttribute('data-theme', 'light');
		else root.removeAttribute('data-theme');
	}

	toggle(): void {
		this.value = this.value === 'dark' ? 'light' : 'dark';
		if (typeof localStorage !== 'undefined') localStorage.setItem(KEY, this.value);
		this.apply();
	}
}

export const theme = new ThemeStore();
