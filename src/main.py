"""Application entry point: python -m src.main."""

if __package__:
    from .launcher import launch
else:
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.launcher import launch


def main():
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
