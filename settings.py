"""Local, non-secret settings for C4C demo. Never committed to GitHub."""
import json
from pathlib import Path
from core import DEFAULT_ACTIVITY_FIELDS, validate_activity_defaults

SETTINGS_FILE = Path(__file__).resolve().parent / ".local_activity_defaults.json"
DEFAULT_SETTINGS = {
    **DEFAULT_ACTIVITY_FIELDS,
    "organizer": "Demo Organizer",
    "sales_territory": "Demo Territory",
}

def normalize_settings(raw):
    if not isinstance(raw, dict):
        raise ValueError("Settings must be an object")
    fields = validate_activity_defaults({
        key: raw[key] for key in DEFAULT_ACTIVITY_FIELDS if key in raw
    })
    organizer = str(raw.get("organizer", DEFAULT_SETTINGS["organizer"])).strip()
    sales_territory = str(raw.get("sales_territory", DEFAULT_SETTINGS["sales_territory"])).strip()
    if not sales_territory:
        raise ValueError("Sales Territory is required")
    return {**fields, "organizer": organizer, "sales_territory": sales_territory}

def load_settings(path=None):
    path = Path(path) if path else SETTINGS_FILE
    try:
        return normalize_settings(json.loads(path.read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError):
        return DEFAULT_SETTINGS.copy()

def save_settings(settings, path=None):
    path = Path(path) if path else SETTINGS_FILE
    normalized = normalize_settings(settings)
    # Temp file + replace prevents partially written settings.
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(normalized, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)
    return normalized

def reset_settings(path=None):
    path = Path(path) if path else SETTINGS_FILE
    path.unlink(missing_ok=True)
    return DEFAULT_SETTINGS.copy()
