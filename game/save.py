"""JSON save/load for a single slot."""

from __future__ import annotations

import json
from pathlib import Path

from .character import Character

SAVE_DIR = Path(__file__).resolve().parent.parent / "saves"
SAVE_PATH = SAVE_DIR / "slot1.json"


def save(pc: Character) -> Path:
    SAVE_DIR.mkdir(exist_ok=True)
    SAVE_PATH.write_text(json.dumps(pc.to_dict(), indent=2, ensure_ascii=False))
    return SAVE_PATH


def has_save() -> bool:
    return SAVE_PATH.exists()


def load() -> Character:
    data = json.loads(SAVE_PATH.read_text())
    return Character.from_dict(data)
