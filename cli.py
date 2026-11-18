#!/usr/bin/env python3
"""Atajo para usar el corrector sin instalar nada: python cli.py "texto".

El comando real vive en corrector_ca/cli.py (también instalable como `corrector-ca`).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from corrector_ca.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
