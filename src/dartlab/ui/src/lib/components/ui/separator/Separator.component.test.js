import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Separator from "./Separator.svelte";

describe("Separator", () => {
	it("renders horizontal separator by default", () => {
		render(Separator);
		const sep = screen.getByRole("separator");
		expect(sep).toBeInTheDocument();
		expect(sep).toHaveAttribute("aria-orientation", "horizontal");
		expect(sep.className).toContain("h-px");
		expect(sep.className).toContain("w-full");
	});

	it("renders vertical separator", () => {
		render(Separator, { props: { orientation: "vertical" } });
		const sep = screen.getByRole("separator");
		expect(sep).toHaveAttribute("aria-orientation", "vertical");
		expect(sep.className).toContain("w-px");
		expect(sep.className).toContain("h-full");
	});
});
