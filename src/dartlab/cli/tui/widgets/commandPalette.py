"""Command palette -- modal slash command selection."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList
from textual.widgets.option_list import Option


class CommandPalette(ModalScreen[str | None]):
    """Modal command palette with fuzzy filter."""

    BINDINGS = [
        ("escape", "dismiss(None)", "Close"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._regularCmds: list[tuple[str, str, str]] = []
        self._skillCmds: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        """Build palette UI."""
        from dartlab.cli.commands.chat import _COMMANDS, _SKILL_COMMANDS

        for name, aliases, desc in _COMMANDS:
            aliasStr = f"  ({', '.join(aliases)})" if aliases else ""
            self._regularCmds.append((name, aliasStr, desc))
        for name, _skillId, desc in _SKILL_COMMANDS:
            self._skillCmds.append((name, desc))

        with Vertical(id="palette-container"):
            yield Input(placeholder="Type a command...", id="palette-input")
            optionList = OptionList(id="palette-list")
            for name, aliasStr, desc in self._regularCmds:
                optionList.add_option(Option(f"{name}{aliasStr}  [dim]{desc}[/]", id=name))
            optionList.add_option(None)  # separator
            for name, desc in self._skillCmds:
                optionList.add_option(Option(f"{name}  [dim]{desc}[/]", id=name))
            yield optionList

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#palette-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Filter commands as user types."""
        query = event.value.lower().strip()
        optionList = self.query_one("#palette-list", OptionList)
        optionList.clear_options()

        regularMatches = []
        for name, aliasStr, desc in self._regularCmds:
            if not query or query in name.lower() or query in aliasStr.lower() or query in desc.lower():
                regularMatches.append((name, aliasStr, desc))

        skillMatches = []
        for name, desc in self._skillCmds:
            if not query or query in name.lower() or query in desc.lower():
                skillMatches.append((name, desc))

        for name, aliasStr, desc in regularMatches:
            optionList.add_option(Option(f"{name}{aliasStr}  [dim]{desc}[/]", id=name))

        if regularMatches and skillMatches:
            optionList.add_option(None)  # separator

        for name, desc in skillMatches:
            optionList.add_option(Option(f"{name}  [dim]{desc}[/]", id=name))

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Select a command."""
        self.dismiss(event.option.id)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Submit first matching command on Enter."""
        optionList = self.query_one("#palette-list", OptionList)
        if optionList.option_count > 0:
            first = optionList.get_option_at_index(0)
            self.dismiss(first.id)
        else:
            self.dismiss(None)
