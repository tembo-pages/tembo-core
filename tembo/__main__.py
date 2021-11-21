"""
Entrypoint module.

Used when using `python -m tembo` to invoke the CLI.
"""

import sys

from tembo.cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
