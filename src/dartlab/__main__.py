"""Allow `python -m dartlab` to invoke the CLI."""

from dartlab.cli.main import main

raise SystemExit(main())
