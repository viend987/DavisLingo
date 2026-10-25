import ctypes
from ctypes import wintypes
import time
import threading
import keyboard
try:
    import winsound
except ImportError:
    winsound = None

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalLock.restype = wintypes.LPVOID
kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
kernel32.GlobalUnlock.restype = wintypes.BOOL
user32.GetClipboardData.argtypes = [wintypes.UINT]
user32.GetClipboardData.restype = wintypes.HANDLE
user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
user32.SetClipboardData.restype = wintypes.HANDLE

def set_clipboard_text(text):
    for _ in range(5):
        if user32.OpenClipboard(None):
            try:
                user32.EmptyClipboard()
                data = text.encode('utf-16le') + b'\x00\x00'
                GMEM_MOVEABLE = 0x0002
                h_mem = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
                p_mem = kernel32.GlobalLock(h_mem)
                ctypes.memmove(p_mem, data, len(data))
                kernel32.GlobalUnlock(h_mem)
                CF_UNICODETEXT = 13
                user32.SetClipboardData(CF_UNICODETEXT, h_mem)
                return True
            finally:
                user32.CloseClipboard()
        time.sleep(0.02)
    return False

def get_clipboard_text():
    for _ in range(5):
        if user32.OpenClipboard(None):
            try:
                CF_UNICODETEXT = 13
                h_mem = user32.GetClipboardData(CF_UNICODETEXT)
                if not h_mem:
                    return ""
                p_mem = kernel32.GlobalLock(h_mem)
                text = ctypes.wstring_at(p_mem)
                kernel32.GlobalUnlock(h_mem)
                return text
            finally:
                user32.CloseClipboard()
        time.sleep(0.02)
    return ""

def play_sound(freq=1200, duration=60):
    if winsound:
        def _beep():
            try:
                winsound.Beep(freq, duration)
            except Exception:
                pass
        threading.Thread(target=_beep, daemon=True).start()

class MacroController:
    def __init__(self, ai_service, slang_engine, config_manager, log_callback=None, hud_callback=None):
        self.ai = ai_service
        self.slang = slang_engine
        self.config = config_manager
        self.log = log_callback or print
        self.hud = hud_callback

        self.last_options_en = []
        self.is_busy = False

    def handle_outgoing_translation(self):
        """
        Triggered by F5:
        1. Select all & copy from active game chat (Ctrl+A -> Ctrl+C).
        2. Read copied text.
        3. Translate with selected RP Style, Slang Level & Tone.
        4. Auto-paste (Ctrl+V) translation into game chat.
        """
        if self.is_busy:
            return
        
        def _worker():
            self.is_busy = True
            try:
                style = self.config.get("current_style", "LSFD / Fire & Medic")
                tone = self.config.get("emotion_tone", "Neutral")
                ignore = self.slang.get_ignore_words_str()

                # Step 1: Keystroke simulation Ctrl+A -> Ctrl+C
                keyboard.send("ctrl+a")
                time.sleep(0.04)
                keyboard.send("ctrl+c")
                time.sleep(0.05)

                # Step 2: Read clipboard
                input_text = get_clipboard_text().strip()
                if not input_text:
                    self.log("[F5 OUTGOING] Input empty or no text selected.")
                    play_sound(600, 100)
                    return

                self.log(f"[F5 OUTGOING] Processing: '{input_text}' [{style} | {tone}]")
                if self.hud:
                    self.hud.show_status_message(f"TRANSLATING [{style.upper()}]...")

                # Step 3: Check local slang dictionary first
                quick_res = self.slang.get_quick_translation(input_text, style)
                if quick_res:
                    final_text = quick_res
                    self.log(f"[F5 OUTGOING] Dictionary Match: '{final_text}'")
                else:
                    final_text = self.ai.translate_outgoing(
                        input_text,
                        style=style,
                        tone=tone,
                        ignore_words=ignore
                    )
                    self.log(f"[F5 OUTGOING] AI Translated: '{final_text}'")

                if final_text:
                    # Step 4: Write translation to clipboard & paste
                    set_clipboard_text(final_text)
                    time.sleep(0.03)
                    keyboard.send("ctrl+v")
                    play_sound(1300, 80)
                    if self.hud:
                        self.hud.show_status_message(f"PASTED: {final_text[:30]}...")
            except Exception as e:
                self.log(f"[F5 OUTGOING ERROR] {e}")
                play_sound(400, 200)
            finally:
                self.is_busy = False

        threading.Thread(target=_worker, daemon=True).start()

    def handle_reply_selection(self, option_index):
        """
        Triggered by Ctrl+1, Ctrl+2, Ctrl+3:
        Puts corresponding English response into clipboard and auto-pastes it.
        """
        if option_index < 0 or option_index >= len(self.last_options_en):
            self.log(f"[AI REPLY] Option {option_index + 1} not available.")
            play_sound(500, 100)
            return

        choice_text = self.last_options_en[option_index].strip()
        if not choice_text:
            return

        def _worker():
            self.log(f"[AI REPLY] Pasting Option {option_index + 1}: '{choice_text}'")
            set_clipboard_text(choice_text)
            time.sleep(0.04)
            keyboard.send("ctrl+v")
            play_sound(1500, 70)
            if self.hud:
                self.hud.show_status_message(f"REPLY #{option_index + 1} PASTED")

        threading.Thread(target=_worker, daemon=True).start()

    def set_active_options(self, options_en):
        self.last_options_en = options_en or []
