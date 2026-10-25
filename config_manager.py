import json
import os
import sys
import copy

DEFAULT_CONFIG = {
    "ai_provider": "groq",
    "groq_api_key": "",
    "groq_model": "qwen/qwen3.8-27b",
    "current_style": "LSFD / Fire & Medic",
    "emotion_tone": "Neutral",
    "auto_paste_top_reply": False,
    "bbox": {
        "left": 265,
        "top": 233,
        "width": 645,
        "height": 73
    },
    "osd_bbox": {
        "left": 1091,
        "top": 122,
        "width": 340,
        "height": 580
    },
    "osd_enabled": True,
    "osd_duration": 15,
    "osd_alpha": 0.88,
    "sound_feedback": True,
    "hotkeys": {
        "hotkey_ocr": "f4",
        "hotkey_clipboard": "f5",
        "hotkey_ans1": "ctrl+1",
        "hotkey_ans2": "ctrl+2",
        "hotkey_ans3": "ctrl+3",
        "hotkey_cycle_style": "alt+1",
        "hotkey_cycle_tone": "alt+2",
        "hotkey_toggle_window": "insert",
        "hotkey_scroll_up": "page up",
        "hotkey_scroll_down": "page down"
    }
}

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_config_path():
    return os.path.join(get_base_dir(), "config.json")

def deep_merge(base, override):
    """
    Recursively merge override dictionary into base dictionary.
    Keys present in base but missing in override are preserved.
    Keys present in override overwrite base.
    """
    result = copy.deepcopy(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = copy.deepcopy(v)
    return result

class ConfigManager:
    def __init__(self):
        self.config_path = get_config_path()
        self.data = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                
                # Deep merge to preserve all user config while automatically adopting new keys
                self.data = deep_merge(DEFAULT_CONFIG, loaded)

                # If loaded configuration was missing any new keys from DEFAULT_CONFIG, save back
                if self.data != loaded:
                    self.save()
                return
            except Exception:
                pass
        self.data = copy.deepcopy(DEFAULT_CONFIG)
        self.save()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
        except Exception:
            pass

    def get(self, key, default=None):
        return self.data.get(key, default)

    def set(self, key, value, auto_save=True):
        self.data[key] = value
        if auto_save:
            self.save()
