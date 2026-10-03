import type { WSClient } from "../ws/client";

export class OverlayController {
  private el: HTMLElement;
  private client: WSClient;
  private idleTimer: ReturnType<typeof setTimeout> | null = null;
  private ignoreCursor = false;

  constructor(el: HTMLElement, client: WSClient) {
    this.el = el;
    this.client = client;
  }

  init(): void {
    this.el.addEventListener("mouseenter", () => this.setIgnoreCursor(false));
    this.client.on("state", (state: unknown) => {
      if (state === "IDLE") {
        this.scheduleIgnore();
      } else {
        this.setIgnoreCursor(false);
        if (this.idleTimer) clearTimeout(this.idleTimer);
      }
    });
    this.scheduleIgnore();
  }

  private scheduleIgnore(): void {
    if (this.idleTimer) clearTimeout(this.idleTimer);
    this.idleTimer = setTimeout(() => this.setIgnoreCursor(true), 5000);
  }

  setIgnoreCursor(ignore: boolean): void {
    this.ignoreCursor = ignore;
    // In Tauri: window.setIgnoreCursorEvents(ignore)
    // Stub for tests
    (this.el as unknown as Record<string, unknown>)._ignoreCursor = ignore;
  }

  isIgnoreCursor(): boolean {
    return this.ignoreCursor;
  }
}
