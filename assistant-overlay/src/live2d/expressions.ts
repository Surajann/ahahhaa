export class ExpressionController {
  private model: any;
  private _current: string = "idle";
  private static STATE_MAP: Record<string, string> = {
    IDLE: "idle",
    LISTENING: "thinking",
    THINKING: "thinking",
    SPEAKING: "talking"
  };

  constructor(model: any) {
    this.model = model;
  }

  setExpression(name: string): void {
    this._current = name;
    if (typeof this.model?.setExpression === "function") {
      this.model.setExpression(name);
    }
    // 200ms fade simulated via model param if available
  }

  setByState(state: string): void {
    const expr = ExpressionController.STATE_MAP[state] ?? "idle";
    this.setExpression(expr);
  }

  setBySentiment(tag: string): void {
    const t = (tag || "idle").toLowerCase();
    if (["happy", "thinking", "confused", "idle"].includes(t)) {
      this.setExpression(t);
    } else {
      this.setExpression("idle");
    }
  }

  current(): string {
    return this._current;
  }
}
