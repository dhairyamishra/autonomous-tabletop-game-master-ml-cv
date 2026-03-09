"""Configure sys.path so all internal packages are importable.

This must be imported before any game_schema / rules_core / battle_core imports.
Adds package src directories directly to sys.path so modules are importable
as flat names (e.g. `from enums import Player` or `from game_state import GameState`).

For cleaner imports across the project, we also create `game_schema`, `rules_core`,
and `battle_core` as namespace aliases pointing to the hyphenated package src dirs.
"""
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

_GAME_SCHEMA_SRC = ROOT / "packages" / "game-schema" / "src"
_RULES_CORE_SRC  = ROOT / "packages" / "rules-core"  / "src"
_BATTLE_CORE_SRC = ROOT / "packages" / "battle-core" / "src"
_MODULES_DIR     = ROOT / "modules"

for p in [_GAME_SCHEMA_SRC, _RULES_CORE_SRC, _BATTLE_CORE_SRC, ROOT]:
    s = str(p)
    if s not in sys.path:
        sys.path.insert(0, s)


def _make_package_alias(name: str, src_path: Path) -> None:
    """Register a top-level package alias that maps to a src directory."""
    if name in sys.modules:
        return
    pkg = types.ModuleType(name)
    pkg.__path__ = [str(src_path)]
    pkg.__package__ = name
    sys.modules[name] = pkg


_make_package_alias("game_schema", _GAME_SCHEMA_SRC)
_make_package_alias("rules_core",  _RULES_CORE_SRC)
_make_package_alias("battle_core", _BATTLE_CORE_SRC)
