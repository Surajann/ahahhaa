import { describe, test, expect, vi } from "vitest";
import { WSClient } from "../src/ws/client";

describe("WSClient", () => {
  test("WSClient reconnects 3x on drop", async () => {
    vi.useFakeTimers();
    const client = new WSClient("ws://127.0.0.1:8765/ws", { maxRetries: 3 });
    let retries = 0;
    client.on("reconnect", () => retries++);
    client.handleClose(new CloseEvent("close", { code: 1006 } as any));
    await vi.advanceTimersByTimeAsync(7000);
    expect(retries).toBe(3);
    vi.useRealTimers();
  });

  test("WSClient emits state on message", () => {
    const client = new WSClient("ws://127.0.0.1:8765/ws", {} as any);
    const spy = vi.fn();
    client.on("state", spy);
    client.handleMessage({ data: JSON.stringify({ type: "state", state: "LISTENING" }) } as unknown as MessageEvent);
    expect(spy).toHaveBeenCalledWith("LISTENING");
  });
});
