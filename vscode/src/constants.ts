/** Extension-wide constants. */

export const EXT_ID = "dartlab";
export const OUTPUT_CHANNEL_NAME = "DartLab";

export const STORAGE_KEY_CONVERSATIONS = "dartlab.conversations";

export const CMD = {
  open: `${EXT_ID}.open`,
  settings: `${EXT_ID}.settings`,
  restart: `${EXT_ID}.restart`,
  showLogs: `${EXT_ID}.showLogs`,
  newConversation: `${EXT_ID}.newConversation`,
  focus: `${EXT_ID}.focus`,
} as const;

export const SIDEBAR_VIEW_ID = `${EXT_ID}.sidebar`;
