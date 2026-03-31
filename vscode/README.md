# DartLab for Visual Studio Code

AI-powered financial analysis for Korean (DART) and US (EDGAR) public companies, directly inside VS Code.

![DartLab](https://raw.githubusercontent.com/eddmpython/dartlab/master/resources/banner.png)

## Features

### AI Chat for Company Analysis

Ask questions about any public company in natural language. DartLab fetches real-time financial data from DART/EDGAR and generates analysis using your preferred AI provider.

- **One stock code, full analysis** -- type a stock code and get financials, governance, valuation, and more
- **Streaming responses** with tool execution visualization
- **Markdown rendering** with syntax highlighting, tables, and code blocks

### Multiple AI Providers

Choose from multiple AI providers, including free-tier options:

- Gemini, Groq, Cerebras (free)
- OpenAI, Ollama (local), and more
- Switch providers anytime from the header dropdown

### Smart Chat Interface

- **Slash commands** -- `/new`, `/clear`, `/model`, `/provider`, `/help`
- **Module selection** -- choose analysis modules (financials, valuation, governance, etc.)
- **Prompt templates** -- pre-built analysis templates for common workflows
- **Watchlist** -- quick-access buttons for frequently analyzed companies
- **Session management** -- search, rename, group, and resume conversations
- **Input history** -- navigate with arrow keys

### MCP Integration

DartLab automatically registers as an MCP server, so you can use DartLab tools from Claude Code, GitHub Copilot, and other MCP-compatible clients.

## Requirements

- **Python 3.12+**
- **dartlab** Python package:
  ```
  pip install dartlab
  ```

The extension automatically detects your Python environment. If auto-detection fails, set the path in `Settings > DartLab > Python Path`.

## Quick Start

1. Install the **dartlab** Python package: `pip install dartlab`
2. Open VS Code and install the **DartLab** extension
3. Click the DartLab icon in the Activity Bar (or press `Ctrl+Shift+D`)
4. Pick an AI provider (free options available)
5. Type a stock code or question and start analyzing

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+D` | Open DartLab Chat |
| `Ctrl+N` | New Conversation (when panel focused) |
| `Up/Down` | Navigate input history |

## Extension Settings

| Setting | Description | Default |
|---------|-------------|---------|
| `dartlab.pythonPath` | Python executable path | Auto-detect |
| `dartlab.autoStart` | Auto-start server on activation | `true` |

## Data Sources

- **DART** -- Korean electronic disclosure system (stable)
- **EDGAR** -- US SEC filings (beta)

All data is fetched on-demand from official sources. No API key required for basic usage.

## Links

- [Documentation](https://eddmpython.github.io/dartlab/)
- [GitHub](https://github.com/eddmpython/dartlab)
- [PyPI](https://pypi.org/project/dartlab/)
- [Report Issues](https://github.com/eddmpython/dartlab/issues)

## License

MIT
