import { describe, test, expect, vi } from "vitest";
import { LipSync } from "../src/live2d/lipsync";

function mockModel() {
  const params: Record<string, number> = { ParamMouthOpenY: 0 };
  return {
    params,
    setParam: (name: string, v: number) => { params[name] = v; },
    getParam: (name: string) => params[name] ?? 0
  };
}

describe("LipSync", () => {
  test("lipsync lerps ParamMouthOpenY with 0.35", () => {
    const m = mockModel();
    const sync = new LipSync(m as any);
    sync.pushViseme(1.0, 100);
    sync.tick(16);
    expect(m.params.ParamMouthOpenY).toBeCloseTo(0.35, 1);
  });

  test("lipsync rms fallback when viseme missing", () => {
    const m = mockModel();
    const sync = new LipSync(m as any);
    sync.pushAudioRMS(new Uint8Array([0, 128, 255, 128]));
    expect(sync.currentMouthOpen()).toBeGreaterThan(0);
  });

  test("lipsync rms silence gives ~0", () => {
    const m = mockModel();
    const sync = new LipSync(m as any);
    sync.pushAudioRMS(new Uint8Array([128, 128, 128]));
    expect(sync.currentMouthOpen()).toBeCloseTo(0, 1);
  });
});
