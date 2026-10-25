import sys
import os
import threading
import keyboard
import ctypes
from PIL import Image, ImageTk

# Enable Per-Monitor High-DPI Awareness so Tkinter and overlays match true monitor resolution
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# Fix taskbar icon: Set explicit Windows AppUserModelID before Tkinter inits
try:
    myappid = 'ViendLab.DavisLingo.RoleplayAssistant.v3'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except Exception:
    pass

# Ensure current and executable directory is in sys.path
def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

base_dir = get_base_dir()
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from config_manager import ConfigManager
from slang_engine import SlangEngine
from ai_service import UnifiedAiService
from ocr_service import OcrService
from macro_controller import MacroController
from hud_overlay import HudOverlay
from app_gui import MainGui

def rebind_all_hotkeys(gui, macro, config):
    try:
        keyboard.unhook_all_hotkeys()
    except Exception:
        pass

    hk = config.get("hotkeys", {})

    # Helper function to register with error handling
    def safe_add(key_str, action, name):
        if not key_str:
            return
        clean_key = str(key_str).strip().lower()
        try:
            keyboard.add_hotkey(clean_key, action, suppress=False)
        except Exception as e:
            gui.log_message(f"[HOTKEY ERROR] Could not bind '{clean_key}' for {name}: {e}")

    # 1. OCR Scan
    safe_add(hk.get("hotkey_ocr", "f4"), gui._test_ocr_scan, "OCR Scan")

    # 2. Clipboard Translate & Auto-Paste
    safe_add(hk.get("hotkey_clipboard", "f5"), macro.handle_outgoing_translation, "Auto-Translate")

    # 3. AI Replies (1, 2, 3)
    safe_add(hk.get("hotkey_ans1", "ctrl+1"), lambda: macro.handle_reply_selection(0), "Reply #1")
    safe_add(hk.get("hotkey_ans2", "ctrl+2"), lambda: macro.handle_reply_selection(1), "Reply #2")
    safe_add(hk.get("hotkey_ans3", "ctrl+3"), lambda: macro.handle_reply_selection(2), "Reply #3")

    # 4. Cycle Style, Slang, Tone
    safe_add(hk.get("hotkey_cycle_style", "alt+1"), gui.cycle_style, "Cycle Style")
    safe_add(hk.get("hotkey_cycle_slang", "alt+2"), gui.cycle_slang, "Cycle Slang")
    safe_add(hk.get("hotkey_cycle_tone", "alt+3"), gui.cycle_tone, "Cycle Tone")

    # 5. Toggle Main Window
    safe_add(hk.get("hotkey_toggle_window", "insert"), gui.toggle_window_visibility, "Toggle Window")

    # 6. Scroll HUD Up / Down
    if gui.hud:
        safe_add(hk.get("hotkey_scroll_up", "page up"), gui.hud.scroll_up, "HUD Scroll Up")
        safe_add(hk.get("hotkey_scroll_down", "page down"), gui.hud.scroll_down, "HUD Scroll Down")

def main():
    config = ConfigManager()
    slang = SlangEngine()
    ai = UnifiedAiService(config)
    ocr = OcrService()
    macro = MacroController(ai, slang, config)

    # Initialize MainGui with placeholder rebind callback
    gui = MainGui(config, slang, ai, ocr, macro, None, None)

    # Create HUD Overlay using gui as root
    hud = HudOverlay(gui, config)
    gui.hud = hud
    macro.hud = hud

    # Define rebind callback that captures current instances
    def trigger_rebind():
        rebind_all_hotkeys(gui, macro, config)

    gui.rebind_hotkeys = trigger_rebind

    # Update HUD with initial profile and shortcuts
    hud.update_profile(
        config.get("current_style", "LSFD / Fire & Medic"),
        config.get("emotion_tone", "Neutral")
    )
    hud.update_shortcut_hints()

    # --- COMPREHENSIVE WINDOW & TASKBAR ICON BINDING ---
    candidate_dirs = [
        base_dir,
        os.path.join(base_dir, "_internal"),
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd()
    ]
    icon_ico = None
    icon_png = None

    for d in candidate_dirs:
        p_ico = os.path.join(d, "app.ico")
        p_png = os.path.join(d, "app.png")
        if not icon_ico and os.path.exists(p_ico):
            icon_ico = p_ico
        if not icon_png and os.path.exists(p_png):
            icon_png = p_png

    # 1. Tkinter native iconbitmap (.ico)
    if icon_ico and os.path.exists(icon_ico):
        try:
            gui.iconbitmap(icon_ico)
            gui.wm_iconbitmap(icon_ico)
            hud.window.iconbitmap(icon_ico)
            hud.window.wm_iconbitmap(icon_ico)
        except Exception:
            pass

    # 2. Tkinter iconphoto (PNG 32-bit RGBA)
    if icon_png and os.path.exists(icon_png):
        try:
            icon_img = ImageTk.PhotoImage(file=icon_png)
            gui.iconphoto(True, icon_img)
            hud.window.iconphoto(True, icon_img)
            gui._app_icon_ref = icon_img
        except Exception:
            pass

    # 3. Direct Win32 API WM_SETICON & GCLP_HICON (Force taskbar DWM to use the exact icon)
    if icon_ico and os.path.exists(icon_ico):
        try:
            gui.update_idletasks()
            hwnd_inner = gui.winfo_id()
            hwnd_parent = ctypes.windll.user32.GetParent(hwnd_inner) or hwnd_inner

            IMAGE_ICON = 1
            LR_LOADFROMFILE = 0x00000010
            LR_DEFAULTSIZE = 0x00000040
            user32 = ctypes.windll.user32

            hicon_big = user32.LoadImageW(None, icon_ico, IMAGE_ICON, 0, 0, LR_LOADFROMFILE | LR_DEFAULTSIZE)
            hicon_sm = user32.LoadImageW(None, icon_ico, IMAGE_ICON, 16, 16, LR_LOADFROMFILE)

            WM_SETICON = 0x0080
            ICON_SMALL = 0
            ICON_BIG = 1
            GCLP_HICON = -14
            GCLP_HICONSM = -34

            for h in (hwnd_inner, hwnd_parent):
                if h:
                    user32.SendMessageW(h, WM_SETICON, ICON_BIG, hicon_big)
                    user32.SendMessageW(h, WM_SETICON, ICON_SMALL, hicon_sm or hicon_big)
                    try:
                        ctypes.windll.user32.SetClassLongPtrW(h, GCLP_HICON, hicon_big)
                        ctypes.windll.user32.SetClassLongPtrW(h, GCLP_HICONSM, hicon_sm or hicon_big)
                    except Exception:
                        pass
        except Exception:
            pass

    # Invalidate and refresh Windows Explorer / Taskbar icon cache
    try:
        ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
    except Exception:
        pass

    # Initial Hotkeys Binding
    trigger_rebind()

    def on_closing():
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        gui.destroy()

    gui.protocol("WM_DELETE_WINDOW", on_closing)
    gui.mainloop()

if __name__ == "__main__":
    main()
