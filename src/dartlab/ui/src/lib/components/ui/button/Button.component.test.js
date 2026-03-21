import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Button from "./Button.svelte";

describe("Button", () => {
	it("renders with default variant", () => {
		render(Button, { props: { children: snippetOf("Click me") } });
		const btn = screen.getByRole("button");
		expect(btn).toBeInTheDocument();
		expect(btn.className).toContain("from-dl-primary");
	});

	it("applies ghost variant", () => {
		render(Button, { props: { variant: "ghost", children: snippetOf("Ghost") } });
		const btn = screen.getByRole("button");
		expect(btn.className).toContain("hover:bg-white/5");
	});

	it("applies size sm", () => {
		render(Button, { props: { size: "sm", children: snippetOf("Small") } });
		const btn = screen.getByRole("button");
		expect(btn.className).toContain("px-3");
		expect(btn.className).toContain("text-xs");
	});

	it("handles disabled state", () => {
		render(Button, { props: { disabled: true, children: snippetOf("Disabled") } });
		const btn = screen.getByRole("button");
		expect(btn).toBeDisabled();
	});
});

/** Helper: create a simple text snippet for Svelte 5 */
function snippetOf(text) {
	return ($$anchor) => {
		const node = document.createTextNode(text);
		$$anchor.before(node);
	};
}
