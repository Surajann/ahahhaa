export class BubbleController {
  private el: HTMLElement;
  private visible = false;
  private timer: ReturnType<typeof setTimeout> | null = null;

  constructor(el: HTMLElement) {
    this.el = el;
    this.el.style.background = "#1A1A1A";
    (this.el.style as any).opacity = "0.85";
    this.el.style.borderRadius = "16px";
    this.el.style.fontFamily = "JetBrains Mono Nerd Font";
    this.el.style.fontSize = "11px";
    this.el.style.display = "none";
  }

  showPartial(text: string): void {
    this.visible = true;
    this.el.style.display = "block";
    this.el.style.color = "#BFBAA6";
    this.el.textContent = text;
    this.clearTimer();
  }

  showFinal(text: string): void {
    this.visible = true;
    this.el.style.display = "block";
    this.el.style.color = "#DDD9C1";
    this.el.textContent = text;
    this.scheduleHide();
  }

  appendToken(text: string): void {
    this.visible = true;
    this.el.style.display = "block";
    this.el.textContent = (this.el.textContent || "") + text;
    this.scheduleHide();
  }

  showToolResult(text: string): void {
    this.showFinal(text);
  }

  isVisible(): boolean {
    return this.visible;
  }

  private scheduleHide(): void {
    this.clearTimer();
    this.timer = setTimeout(() => {
      this.visible = false;
      this.el.style.display = "none";
    }, 4000);
  }

  private clearTimer(): void {
    if (this.timer) clearTimeout(this.timer);
    this.timer = null;
  }
}
