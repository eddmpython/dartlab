"""DartLab CLI package."""


def main(argv=None):
    from .main import main as _main

    return _main(argv)


__all__ = ["main"]
