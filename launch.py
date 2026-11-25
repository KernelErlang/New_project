"""Open the Nocturne Codex.

Double-click this file (on systems where .py files open with Python), or run
``python launch.py``. It needs nothing but Python 3.9 or newer.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

if sys.version_info < (3, 9):  # noqa: UP036 - a friendly message on old Pythons
    sys.exit("The Codex needs Python 3.9 or newer.")

from nocturne.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
