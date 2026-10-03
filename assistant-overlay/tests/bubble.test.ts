import { describe, test, expect, vi } from "vitest";
import { BubbleController } from "../src/ui/bubble";

describe("BubbleController", () => {
  test("bubble auto-hides after 4s", async () => {
    vi.useFakeTimers();
    const el = document.createElement("div");
    const b = new BubbleController(el);
    b.showFinal("Halo ne~");
    expect(b.isVisible()).toBe(true);
    vi.advanceTimersByTime(4000);
    expect(b.isVisible()).toBe(false);
    vi.useRealTimers();
  });

  test("showPartial keeps visible", () => {
    const el = document.createElement("div");
    const b = new BubbleController(el);
    b.showPartial("Ha");
    expect(b.isVisible()).toBe(true);
    expect(el.textContent).toContain("Ha");
  });

  test("appendToken appends", () => {
    const el = document.createElement("div");
    const b = new BubbleController(el);
    b.showFinal("Halo");
    b.appendToken(" ne~");
    expect(el.textContent).toContain("Halo");
    expect(el.textContent).toContain("ne~");
  });
});
