import os
import sys

# The project historically adds the ``core`` package directory to ``sys.path``
# at runtime (see ``run.py`` and the various ``app/routes`` modules), which lets
# modules inside ``core`` import their siblings as top-level modules such as
# ``from database_models import Base``.  Replicate that here so the test suite
# can import those modules regardless of the entry point.
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CORE_DIR = os.path.join(ROOT_DIR, "core")

for path in (ROOT_DIR, CORE_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)
