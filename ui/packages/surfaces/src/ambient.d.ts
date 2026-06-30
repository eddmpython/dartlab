// CSS 사이드이펙트 import 앰비언트 · 번들러(vite)가 처리하지만 svelte-check 타입 해석엔 선언 필요.
// landing 은 SvelteKit/vite client 타입에서 받지만, 독립 패키지 check 는 자체 선언이 필요하다.
declare module '*.css';
