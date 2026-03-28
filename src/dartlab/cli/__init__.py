"""DartLab CLI package."""


def main(argv=None):
    """CLI 진입점."""
    from .main import main as _main

    return _main(argv)


__all__ = ["main"]
