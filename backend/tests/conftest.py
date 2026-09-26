import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Isolate runtime data BEFORE any app import (config reads these at import time)
os.environ.setdefault("RCV_DATA_DIR", tempfile.mkdtemp(prefix="rcv_test_data_"))
os.environ.setdefault("RCV_CACHE_DIR", tempfile.mkdtemp(prefix="rcv_test_cache_"))