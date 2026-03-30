import * as vscode from "vscode";
import { STORAGE_KEY_CONVERSATIONS } from "../constants";

interface StoredConversation {
  id: string;
  title: string;
  messages: unknown[];
  createdAt: number;
  updatedAt: number;
}

interface StoredState {
  conversations: StoredConversation[];
  activeConversationId: string | null;
}

/** TreeView provider for conversation history in the sidebar. */
export class HistoryTreeProvider
  implements vscode.TreeDataProvider<HistoryItem>
{
  private _onDidChangeTreeData = new vscode.EventEmitter<void>();
  readonly onDidChangeTreeData = this._onDidChangeTreeData.event;

  constructor(private readonly globalState: vscode.Memento) {}

  refresh(): void {
    this._onDidChangeTreeData.fire();
  }

  private getStoredState(): StoredState {
    return (
      (this.globalState.get(STORAGE_KEY_CONVERSATIONS) as StoredState) ?? {
        conversations: [],
        activeConversationId: null,
      }
    );
  }

  getTreeItem(element: HistoryItem): vscode.TreeItem {
    return element;
  }

  getChildren(): HistoryItem[] {
    const state = this.getStoredState();
    if (state.conversations.length === 0) {
      return [];
    }

    // Group by time
    const now = Date.now();
    const day = 86400000;
    const groups: Record<string, StoredConversation[]> = {};
    const groupOrder = ["Today", "Yesterday", "This Week", "Older"];

    for (const conv of state.conversations) {
      const diff = now - conv.updatedAt;
      let group: string;
      if (diff < day) group = "Today";
      else if (diff < day * 2) group = "Yesterday";
      else if (diff < day * 7) group = "This Week";
      else group = "Older";
      if (!groups[group]) groups[group] = [];
      groups[group].push(conv);
    }

    const items: HistoryItem[] = [];
    for (const group of groupOrder) {
      const convs = groups[group];
      if (!convs?.length) continue;
      // Group separator
      items.push(new HistoryItem(group, "", "group"));
      for (const conv of convs) {
        const msgCount = conv.messages.length;
        const desc = `${msgCount} messages`;
        const item = new HistoryItem(conv.title, desc, "conversation");
        item.conversationId = conv.id;
        item.command = {
          command: "dartlab.openConversation",
          title: "Open",
          arguments: [conv.id],
        };
        item.contextValue = "conversation";
        items.push(item);
      }
    }

    return items;
  }
}

export class HistoryItem extends vscode.TreeItem {
  conversationId?: string;

  constructor(
    label: string,
    description: string,
    kind: "group" | "conversation",
  ) {
    super(
      label,
      kind === "group"
        ? vscode.TreeItemCollapsibleState.None
        : vscode.TreeItemCollapsibleState.None,
    );
    this.description = description;

    if (kind === "group") {
      this.iconPath = undefined;
      this.contextValue = "group";
      // Make it look like a section header
      this.description = "";
    } else {
      this.iconPath = new vscode.ThemeIcon("comment-discussion");
      this.tooltip = label;
    }
  }
}
