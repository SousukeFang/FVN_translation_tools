import argparse

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fvn-translator")
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> None:
    build_parser().parse_args()
    from fvn_translator.tui import TranslatorApp

    TranslatorApp().run()
