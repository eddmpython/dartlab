/** Extension-wide constants. */

export const EXT_ID = "dartlab";
export const OUTPUT_CHANNEL_NAME = "DartLab Server";

export const DEFAULT_PORT = 8400;
export const PORT_SCAN_MAX = 8420;
export const HEALTH_CHECK_INTERVAL_MS = 500;
export const HEALTH_CHECK_TIMEOUT_MS = 30_000;
export const PERIODIC_HEALTH_MS = 60_000;
export const MAX_RESTART_ATTEMPTS = 3;
export const RESTART_BACKOFF_MS = 2_000;

export const STORAGE_KEY_PORT = "dartlab.lastPort";
export const STORAGE_KEY_CONVERSATIONS = "dartlab.conversations";

export const CMD = {
  open: `${EXT_ID}.open`,
  settings: `${EXT_ID}.settings`,
  restart: `${EXT_ID}.restart`,
  showLogs: `${EXT_ID}.showLogs`,
} as const;

export const SIDEBAR_VIEW_ID = `${EXT_ID}.sidebar`;
export const PANEL_VIEW_TYPE = "dartlab.chat";
