export class Live2DModelManager {
  private canvas: HTMLCanvasElement;
  private basePath: string;
  private model: unknown = null;
  private fallbackRoot: HTMLElement | null = null;

  constructor(canvas: HTMLCanvasElement, basePath: string) {
    this.canvas = canvas;
    this.basePath = basePath;
  }

  async load(modelPath: string): Promise<void> {
    try {
      // In production: Pixi + pixi-live2d-display
      // For now stub — simulate load success
      void modelPath;
      this.model = { path: modelPath };
      this.canvas.dataset.loaded = "true";
    } catch {
      this.useFallback();
    }
  }

  dispose(): void {
    this.model = null;
    this.canvas.dataset.loaded = "false";
  }

  async setAvatar(path: string): Promise<void> {
    this.dispose();
    // cross-fade 300ms placeholder
    await new Promise((r) => setTimeout(r, 10));
    await this.load(path);
  }

  pauseRAF(): void {
    this.canvas.dataset.paused = "true";
  }

  resumeRAF(): void {
    this.canvas.dataset.paused = "false";
  }

  private useFallback(): void {
    // Inject 2-3 PNG fallback
    if (!this.fallbackRoot) {
      this.fallbackRoot = document.createElement("div");
      this.fallbackRoot.dataset.fallback = "true";
      this.canvas.parentElement?.appendChild(this.fallbackRoot);
    }
  }

  getModel(): unknown {
    return this.model;
  }
}
