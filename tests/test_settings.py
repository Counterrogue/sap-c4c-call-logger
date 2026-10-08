import json
from settings import DEFAULT_SETTINGS, load_settings, save_settings, reset_settings

def test_custom_settings_save_load_and_reset(tmp_path):
    path = tmp_path / "settings.json"
    assert load_settings(path) == DEFAULT_SETTINGS
    custom = {
        **DEFAULT_SETTINGS,
        "type_of_contact": "Video Call",
        "reason_for_conversation": "Without opportunity reference",
        "reason_for_contact": "Follow-up",
        "product_level_3": "Different category",
        "organizer": "Example Organizer",
        "sales_territory": "Example Territory",
    }
    saved = save_settings(custom, path)
    assert saved == custom
    assert load_settings(path) == custom
    assert json.loads(path.read_text()) == custom
    assert reset_settings(path) == DEFAULT_SETTINGS
    assert not path.exists()
    assert load_settings(path) == DEFAULT_SETTINGS

def test_invalid_local_settings_revert_to_defaults(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{not-json")
    assert load_settings(path) == DEFAULT_SETTINGS
