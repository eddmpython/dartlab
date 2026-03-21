import { render, screen } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Progress from "./Progress.svelte";

describe("Progress", () => {
	it("renders progressbar role with correct ARIA attributes", () => {
		render(Progress, { props: { value: 50, max: 100 } });
		const bar = screen.getByRole("progressbar");
		expect(bar).toBeInTheDocument();
		expect(bar).toHaveAttribute("aria-valuenow", "50");
		expect(bar).toHaveAttribute("aria-valuemin", "0");
		expect(bar).toHaveAttribute("aria-valuemax", "100");
	});

	it("clamps percentage to 0-100", () => {
		render(Progress, { props: { value: 150, max: 100 } });
		const bar = screen.getByRole("progressbar");
		const inner = bar.querySelector("div");
		expect(inner.style.width).toBe("100%");
	});

	it("renders indeterminate without aria-valuenow", () => {
		render(Progress, { props: { indeterminate: true } });
		const bar = screen.getByRole("progressbar");
		expect(bar).not.toHaveAttribute("aria-valuenow");
	});
});
