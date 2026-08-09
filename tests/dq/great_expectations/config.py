from pathlib import Path
import os

GE_DIR = Path(__file__).resolve().parent
GX_ROOT = str((GE_DIR / "gx").resolve())
RULES_CONFIG_PATH = str((GE_DIR / "rules_config.json").resolve())
PLUGINS_DIR = str((GE_DIR / "gx" / "plugins").resolve())

