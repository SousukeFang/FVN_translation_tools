"""Run the repository's Agent translation CLI from a skill checkout."""

import sys
from pathlib import Path

repository = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(repository / "src"))

from fvn_translator.cli import main  # noqa: E402

if __name__ == "__main__":
    main()
