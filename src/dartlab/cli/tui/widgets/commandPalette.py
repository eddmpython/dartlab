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
        self._allCommands: list[tuple[str, str]] = []

    def compose(self) -> ComposeResult:
        """Build palette UI."""
        from dartlab.cli.commands.chat import _COMMANDS, _SKILL_COMMANDS

        for name, _aliases, desc in _COMMANDS:
            self._allCommands.append((name, desc))
        for name, _skillId, desc in _SKILL_COMMANDS:
            self._allCommands.append((name, desc))

        with Vertical(id="palette-container"):
            yield Input(placeholder="Type a command...", id="palette-input")
            optionList = OptionList(id="palette-list")
            for name, desc in self._allCommands:
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
        for name, desc in self._allCommands:
            if not query or query in name.lower() or query in desc.lower():
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
