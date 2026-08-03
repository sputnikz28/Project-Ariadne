"""Builds the scroll (pergaminho) for one historical draw record — a thin
wrapper around orders.librarians.converter.criar_pergaminho() that corrects
one known field. Pure: no I/O (criar_pergaminho() itself does none either;
saving to disk is the caller's job).
"""

from __future__ import annotations

from orders.librarians.converter import criar_pergaminho


def build_scroll(draw_record: dict) -> dict:
    scroll = criar_pergaminho(draw_record)

    # Temporary compatibility layer until criar_pergaminho() adopts the
    # canonical hash algorithm. criar_pergaminho() hashes json.dumps(chave,
    # sort_keys=True); the real convention used by every existing scroll
    # (verified in-session against 058/2026) is
    # sha256(chave_canonica.encode("utf-8")) == identificadores.sha256_chave.
    # Remove this override if/when criar_pergaminho() is updated to match.
    scroll["assinatura"]["sha256"] = draw_record["identificadores"]["sha256_chave"]

    return scroll
