import * as net from "net";
import { DEFAULT_PORT, PORT_SCAN_MAX } from "../constants";

/** Try to bind a TCP socket to check port availability. */
function isPortFree(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.once("error", () => resolve(false));
    srv.once("listening", () => {
      srv.close(() => resolve(true));
    });
    srv.listen(port, "127.0.0.1");
  });
}

/** Find an available port starting from `preferred`. */
export async function findAvailablePort(
  preferred: number = DEFAULT_PORT,
): Promise<number> {
  for (let port = preferred; port <= PORT_SCAN_MAX; port++) {
    if (await isPortFree(port)) {
      return port;
    }
  }
  // Fallback: let OS assign a port
  return new Promise((resolve, reject) => {
    const srv = net.createServer();
    srv.once("error", reject);
    srv.listen(0, "127.0.0.1", () => {
      const addr = srv.address();
      if (addr && typeof addr !== "string") {
        const port = addr.port;
        srv.close(() => resolve(port));
      } else {
        srv.close(() => reject(new Error("Failed to get assigned port")));
      }
    });
  });
}
