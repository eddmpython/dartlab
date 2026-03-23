import { render } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";

import MessageBubble from "./MessageBubble.svelte";

describe("MessageBubble streaming draft rendering", () => {
	it("renders plain text drafts inline without the structured draft box", () => {
		const { container } = render(MessageBubble, {
			message: {
				role: "assistant",
				text: "이 문장은 아직 작성 중입니다",
				loading: true,
			},
		});

		expect(container.querySelector(".message-live-inline")).toBeInTheDocument();
		expect(container.querySelector(".message-live-tail")).not.toBeInTheDocument();
	});

	it("keeps code drafts in the structured draft box", () => {
		const { container } = render(MessageBubble, {
			message: {
				role: "assistant",
				text: "```js\nconst revenue = 10",
				loading: true,
			},
		});

		expect(container.querySelector(".message-live-tail.message-draft-code")).toBeInTheDocument();
		expect(container.querySelector(".message-live-inline")).not.toBeInTheDocument();
	});
});
