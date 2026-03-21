import { render } from "@testing-library/svelte";
import { describe, expect, it } from "vitest";
import Skeleton from "./Skeleton.svelte";

describe("Skeleton", () => {
	it("renders with animate-pulse", () => {
		const { container } = render(Skeleton);
		const el = container.querySelector("div");
		expect(el).toBeInTheDocument();
		expect(el.className).toContain("animate-pulse");
		expect(el).toHaveAttribute("aria-hidden", "true");
	});

	it("accepts custom class", () => {
		const { container } = render(Skeleton, { props: { class: "h-4 w-32" } });
		const el = container.querySelector("div");
		expect(el.className).toContain("h-4");
		expect(el.className).toContain("w-32");
	});
});
