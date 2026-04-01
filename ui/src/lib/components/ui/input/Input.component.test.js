import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Input from "./Input.svelte";

describe("Input", () => {
	it("renders text input by default", () => {
		render(Input, { props: { placeholder: "검색..." } });
		const input = screen.getByPlaceholderText("검색...");
		expect(input).toBeInTheDocument();
		expect(input).toHaveAttribute("type", "text");
	});

	it("applies ghost variant", () => {
		render(Input, { props: { variant: "ghost", placeholder: "Ghost" } });
		const input = screen.getByPlaceholderText("Ghost");
		expect(input.className).toContain("bg-transparent");
	});

	it("applies size sm", () => {
		render(Input, { props: { size: "sm", placeholder: "Small" } });
		const input = screen.getByPlaceholderText("Small");
		expect(input.className).toContain("h-8");
	});

	it("passes disabled", () => {
		render(Input, { props: { disabled: true, placeholder: "No" } });
		const input = screen.getByPlaceholderText("No");
		expect(input).toBeDisabled();
	});
});
