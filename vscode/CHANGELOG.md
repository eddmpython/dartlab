# Changelog

## [0.1.8] - 2026-04-03

### Added

- Provider setup flow: selecting a provider triggers connection immediately
  - API key providers: opens signup page + InputBox for key entry
  - OAuth providers (ChatGPT): opens browser for PKCE login, callback handled automatically
  - Ollama: connects directly without credentials
- Provider dropdown always visible in header (shows "프로바이더 선택" when none set)
- Connection success message after provider setup
- Error messages stripped of CLI references (`dartlab.setup(...)`) in UI context

### Changed

- Welcome screen redesigned as provider setup cards (replaces old 3-button layout)
- Chat input always enabled regardless of server state
- Auto-install uses `;` separator on Windows PowerShell (was `&&`)

### Fixed

- Provider errors were silently swallowed (`except Exception: pass`) — now reported to user

## [0.1.0] - 2026-04-01

### Added

- AI chat panel with streaming responses and tool execution visualization
- Multiple AI provider support (Gemini, Groq, Cerebras, OpenAI, Ollama, and more)
- Claude Code-style message rendering (collapsible tools, code blocks, snapshot cards)
- Slash commands: `/new`, `/clear`, `/model`, `/provider`, `/help`, `/resume`
- Module selection for targeted analysis (financials, valuation, governance, etc.)
- Watchlist for frequently analyzed companies
- Session management (search, rename, group, delete)
- Input history navigation with arrow keys
- MCP auto-registration for Claude Code and GitHub Copilot
- Auto-detect Python environment with fallback chain
- Health check and auto-restart with exponential backoff
- Table rendering with number formatting, zebra striping, and CSV download
- Copy and regenerate buttons on messages
- Token usage estimation
- Console proxy for webview error debugging
