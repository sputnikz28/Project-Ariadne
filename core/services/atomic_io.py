"""Atomic JSON persistence — write-to-temp-then-replace, so a failure
mid-write never corrupts the target file. Nothing else in this codebase's
existing save() helpers (artifacts/ark.py, docs/lore/legends/registry.py,
orders/scribes/archivists.py) does this; those write directly and are fine
for narrative/generated data, but the Heroes registry needs to survive
partial writes without corruption.

atomic_write_json() always succeeds and unconditionally overwrites its
target — correct for every caller so far (Heroes/Legends key their
entries by content-derived identity, e.g. dedup_hash/source_prediction_id,
so "overwrite" and "create" are the same safe operation there). It gives
no create-if-absent guarantee: two processes racing to write the same
path with atomic_write_json() would both "succeed", with whichever wins
the final os.replace() silently discarding the other's content. That is
unsafe for a caller assigning a sequential id (e.g. the Academia's
AcademyStudentRegistry, library/academy/students/registry.py) where losing
a candidate id to a race must never mean losing a student's identity.

atomic_create_json() closes that gap: os.O_CREAT | os.O_EXCL is an OS-level
exclusive-create — the OS guarantees at most one of any number of racing
processes/threads opening the same path this way ever succeeds, even
without any additional locking. Callers needing safe id-reservation must
use this, not atomic_write_json(), for the reservation write itself.
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


def atomic_create_json(path, data):
    """Creates path only if it does not already exist. Returns True if
    this call created it; False if it already existed (no write
    happened — the existing content is left completely untouched, never
    inspected or compared). See module docstring: this is the safe
    primitive for id-reservation, unlike atomic_write_json().
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        return False
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise
    return True


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default
