"""Rebuild disposable SQLite state from authoritative units.jsonl."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fvn_translator.storage import StateDatabase, UnitRepository, Workspace  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    workspace = Workspace(args.workspace)
    database = StateDatabase(workspace.state / "state.sqlite3")
    try:
        units = UnitRepository(workspace.intermediate / "units.jsonl", database).load()
        print(f"Rebuilt state for {len(units)} units")
    finally:
        database.close()


if __name__ == "__main__":
    main()
