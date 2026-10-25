import json
import os
import sys

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

class SlangEngine:
    def __init__(self):
        self.slang_path = os.path.join(get_base_dir(), "slang_library.json")
        self.styles = [
            "LSFD / Fire & Medic",
            "LSPD / Police & Sheriff",
            "LA Street Gang",
            "Casual Civilian",
            "Cartel & Latino",
            "Mafia Underworld"
        ]
        self.tones = [
            "Neutral",
            "Calm & Assertive",
            "Friendly & Empathetic",
            "Angry & Intimidating",
            "Panic & Urgent"
        ]
        self.ignore_words = [
            "Los Santos", "LSFD", "LSPD", "LSSD", "DFS", "PBH", "ASGH", "OCD",
            "Vagos", "Ballas", "Families", "Bloods", "Crips", "FIB", "BCSO", "SASP"
        ]
        self.library = {}
        self.load()

    def load(self):
        if os.path.exists(self.slang_path):
            try:
                with open(self.slang_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.ignore_words = data.get("ignore_words", self.ignore_words)
                    loaded_styles = data.get("styles", {})
                    if loaded_styles:
                        self.library = loaded_styles
            except Exception as e:
                print(f"[SLANG] Error loading slang library: {e}")

    def get_quick_translation(self, text, style, intensity=None):
        """
        Check if the phrase directly exists in the local slang dictionary.
        Returns matching translation string if found, otherwise None.
        """
        clean_text = text.strip().lower()
        style_dict = self.library.get(style, {})
        entry = style_dict.get(clean_text)
        if entry:
            if isinstance(entry, dict):
                return entry.get("2") or entry.get("1") or entry.get("3") or next(iter(entry.values()), None)
            elif isinstance(entry, str):
                return entry
        return None

    def get_ignore_words_str(self):
        return ", ".join(self.ignore_words)
