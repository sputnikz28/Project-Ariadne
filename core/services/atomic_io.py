"""Atomic JSON persistence — write-to-temp-then-replace, so a failure
mid-write never corrupts the target file. Nothing else in this codebase's
existing save() helpers (artifacts/ark.py, docs/lore/legends/registry.py,
orders/scribes/archivists.py) does this; those write directly and are fine
for narrative/generated data, but the Heroes registry needs to survive
partial writes without corruption.
"""

import json
import os
import tempfile
from pathlib import Path


def atomic_write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default
