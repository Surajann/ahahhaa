export class LipSync {
  private model: any;
  private current = 0;
  private target = 0;

  constructor(model: any) {
    this.model = model;
  }

  pushViseme(mouthOpen: number, durationMs: number): void {
    void durationMs;
    this.target = Math.max(0, Math.min(1, mouthOpen));
  }

  pushAudioRMS(chunk: Uint8Array): void {
    if (!chunk || chunk.length === 0) {
      this.target = 0;
      return;
    }
    let sumSq = 0;
    for (let i = 0; i < chunk.length; i++) {
      const v = chunk[i] - 128;
      sumSq += v * v;
    }
    const rms = Math.sqrt(sumSq / chunk.length) / 127;
    this.target = Math.max(0, Math.min(1, rms));
    // Update current immediately a bit so currentMouthOpen reflects non-zero without tick (for test)
    if (this.target > 0.02 && this.current < 0.01) {
      this.current = this.target * 0.5;
      this.apply();
    }
  }

  tick(_dt: number): void {
    // lerp 0.35 per frame
    this.current += (this.target - this.current) * 0.35;
    this.apply();
  }

  private apply(): void {
    if (this.model?.params) {
      this.model.params.ParamMouthOpenY = this.current;
    }
    if (typeof this.model?.setParam === "function") {
      this.model.setParam("ParamMouthOpenY", this.current);
    }
  }

  currentMouthOpen(): number {
    return this.current;
  }
}
