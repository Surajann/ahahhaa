import { WSClient } from "./ws/client";
import { OverlayController } from "./ui/overlay";

const client = new WSClient("ws://127.0.0.1:8765/ws", { maxRetries: 3 });
const overlay = new OverlayController(document.getElementById("app") as HTMLElement, client);
client.connect();
overlay.init();
console.log("Anime Assistant overlay started");
