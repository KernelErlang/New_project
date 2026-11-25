"""Allow ``python -m nocturne``."""

import sys

from .cli import main

sys.exit(main())
