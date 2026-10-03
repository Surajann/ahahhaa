export type WSHandlers = {
  maxRetries?: number;
};

export class WSClient {
  private url: string;
  private maxRetries: number;
  private retries = 0;
  private ws: WebSocket | null = null;
  private handlers: Map<string, Set<Function>> = new Map();
  private opts: WSHandlers;

  constructor(url: string, opts: WSHandlers) {
    this.url = url;
    this.opts = opts;
    this.maxRetries = opts.maxRetries ?? 3;
  }

  on(event: string, cb: Function): void {
    if (!this.handlers.has(event)) this.handlers.set(event, new Set());
    this.handlers.get(event)!.add(cb);
  }

  off(event: string, cb: Function): void {
    this.handlers.get(event)?.delete(cb);
  }

  private emit(event: string, ...args: unknown[]): void {
    for (const cb of this.handlers.get(event) ?? []) {
      try {
        (cb as (...a: unknown[]) => void)(...args);
      } catch {
        /* ignore */
      }
    }
  }

  connect(): void {
    try {
      this.ws = new WebSocket(this.url);
      this.ws.onmessage = (e) => this.handleMessage(e);
      this.ws.onclose = (e) => this.handleClose(e as unknown as CloseEvent);
      this.ws.onerror = () => {};
    } catch {
      this.scheduleReconnect();
    }
  }

  send(data: unknown): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  handleMessage(event: MessageEvent): void {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "state" && msg.state) {
        this.emit("state", msg.state);
      } else if (msg.type) {
        this.emit(msg.type, msg);
      }
      this.emit("message", msg);
    } catch {
      /* ignore malformed */
    }
  }

  handleClose(event: CloseEvent): void {
    void event;
    this.scheduleReconnect();
  }

  private scheduleReconnect(): void {
    if (this.retries >= this.maxRetries) return;
    const delays = [1000, 2000, 4000];
    const delay = delays[Math.min(this.retries, delays.length - 1)];
    this.retries++;
    this.emit("reconnect", this.retries);
    setTimeout(() => {
      if (this.retries <= this.maxRetries) {
        this.connect();
      }
    }, delay);
  }

  handleOpen(): void {
    this.retries = 0;
  }
}
