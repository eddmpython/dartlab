// 첫 화면 자료는 빌드할 때 서버에서 골라 HTML 에 넣는다. 화면 코드가 글 목록 모듈을 직접 import 하면
// 전체 목록이 첫 화면 자바스크립트에 다시 실린다. 다음 쪽은 PostFeed 가 blog/list/<n>.json 으로 받는다.
import { getFeedPage, getFeedPageCount, getStoryIndex, getStoryStrip } from '$lib/blog/posts';

export const prerender = true;

export function load() {
	return {
		feed: getFeedPage(1),
		feedPages: getFeedPageCount(),
		strip: getStoryStrip(20),
		storyIndex: getStoryIndex()
	};
}
