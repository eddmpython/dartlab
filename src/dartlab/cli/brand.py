"""Terminal color palette -- single source of truth for CLI/TUI theming.

Web landing uses landing/src/lib/brand.ts separately (red-based).
Terminal uses cyan/teal palette for clean readability on dark backgrounds.
"""

# Primary brand (cyan/teal)
CLR = "#22d3ee"  # cyan-400
CLR_DIM = "#0891b2"  # cyan-600

# Functional
CLR_ACCENT = "#67e8f9"  # cyan-300 (light cyan)
CLR_MUTED = "#6b7280"  # gray-500
CLR_SUCCESS = "#34d399"  # emerald-400
CLR_WARN = "#fbbf24"  # amber-400
CLR_DANGER = "#f87171"  # red-400
