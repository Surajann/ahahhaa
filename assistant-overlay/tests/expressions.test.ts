import { describe, test, expect } from "vitest";
import { ExpressionController } from "../src/live2d/expressions";

function mockModel() {
  let current = "idle";
  return {
    setExpression: (name: string) => { current = name; },
    getExpression: () => current,
    _current: () => current
  };
}

describe("ExpressionController", () => {
  test("expression switches with happy", () => {
    const m = mockModel();
    const ctrl = new ExpressionController(m as any);
    ctrl.setExpression("happy");
    expect(ctrl.current()).toBe("happy");
  });

  test("setByState maps LISTENING to thinking", () => {
    const m = mockModel();
    const ctrl = new ExpressionController(m as any);
    ctrl.setByState("LISTENING");
    expect(ctrl.current()).toBe("thinking");
  });

  test("setBySentiment happy maps to happy", () => {
    const m = mockModel();
    const ctrl = new ExpressionController(m as any);
    ctrl.setBySentiment("happy");
    expect(ctrl.current()).toBe("happy");
  });
});
