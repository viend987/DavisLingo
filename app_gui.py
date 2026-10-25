import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import threading
import time

class MainGui(ctk.CTk):
    def __init__(self, config_manager, slang_engine, ai_service, ocr_service, macro_controller, hud_overlay, rebind_hotkeys_callback=None):
        super().__init__()

        self.config = config_manager
        self.slang = slang_engine
        self.ai = ai_service
        self.ocr = ocr_service
        self.macro = macro_controller
        self.hud = hud_overlay
        self.rebind_hotkeys = rebind_hotkeys_callback

        # Hotkey Interactive Recorder State
        self._recording_key_name = None
        self._recording_hook = None
        self._recording_original_val = None
        self._recording_pressed_mods = set()
        self.hk_entries = {}
        self.hk_entry_widgets = {}
        self.hk_change_btns = {}

        # Window Setup - Sleek and Compact
        self.title("DavisLingo - Roleplay Assistant")
        self.geometry("860x640")
        self.minsize(800, 580)

        # Apply dark theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Color Palette: Cyber Obsidian / Tokyo Night
        self.c_bg = "#090d16"
        self.c_card = "#121826"
        self.c_card_border = "#1f293d"
        self.c_blue = "#38bdf8"
        self.c_green = "#4ade80"
        self.c_amber = "#fbbf24"
        self.c_text = "#f1f5f9"
        self.c_dim = "#94a3b8"

        self.configure(fg_color=self.c_bg)

        # Wire up macro callbacks
        self.macro.log = self.log_message
        self.macro.hud = self.hud

        # Auto-Updater Service
        from updater_service import UpdaterService
        self.updater = UpdaterService(log_callback=self.log_message)
        self._pending_update_info = None

        self._build_layout()
        self.log_message("[SYSTEM] DavisLingo - Roleplay Assistant initialized.")
        self.log_message("[SYSTEM] Publisher: ViendLab | Developer: Viend | Made by JGVRP Player.")

        # Silent check for updates 2.5s after startup
        self.after(2500, self._silent_check_update)

    def _build_layout(self):
        # 1. TOP HEADER BAR (Modern High-Tech Obsidian)
        header_frame = ctk.CTkFrame(self, fg_color=self.c_card, corner_radius=10, border_width=1, border_color=self.c_card_border)
        header_frame.pack(fill="x", padx=12, pady=(10, 6))

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", padx=14, pady=10)

        title_lbl = ctk.CTkLabel(
            title_box,
            text="DAVISLINGO",
            font=ctk.CTkFont(family="Consolas", size=20, weight="bold"),
            text_color=self.c_blue
        )
        title_lbl.pack(anchor="w")

        sub_lbl = ctk.CTkLabel(
            title_box,
            text="GTA V ROLEPLAY ASSISTANT  •  VIENDLAB",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.c_dim
        )
        sub_lbl.pack(anchor="w", pady=(1, 0))

        badges_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        badges_box.pack(side="right", padx=14, pady=10)

        lic_badge = ctk.CTkLabel(
            badges_box,
            text="VIENDLAB",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_green,
            fg_color="#064e3b",
            corner_radius=6,
            padx=10,
            pady=4
        )
        lic_badge.pack(side="right", padx=(6, 0))

        engine_badge = ctk.CTkLabel(
            badges_box,
            text="LPU ACCELERATED",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_blue,
            fg_color="#0c4a6e",
            corner_radius=6,
            padx=10,
            pady=4
        )
        engine_badge.pack(side="right")

        # 2. MAIN TABVIEW (Sleek, organized, no brackets)
        self.tabview = ctk.CTkTabview(
            self,
            fg_color=self.c_card,
            segmented_button_selected_color="#0284c7",
            segmented_button_selected_hover_color="#0369a1",
            segmented_button_unselected_color="#1e293b",
            segmented_button_unselected_hover_color="#334155",
            corner_radius=10
        )
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        tab_rp = self.tabview.add("Roleplay & HUD")
        tab_keys = self.tabview.add("Custom Keybinds")
        tab_sys = self.tabview.add("System & Logs")

        self._build_tab_roleplay(tab_rp)
        self._build_tab_shortcuts(tab_keys)
        self._build_tab_system(tab_sys)

        # 3. BOTTOM WATERMARK / FOOTER
        watermark_frame = ctk.CTkFrame(self, fg_color="transparent")
        watermark_frame.pack(fill="x", padx=14, pady=(0, 6))

        ctk.CTkLabel(
            watermark_frame,
            text="DavisLingo • Developed by Viend (ViendLab) • Made by JGVRP Player",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#64748b"
        ).pack(side="left")

        ctk.CTkLabel(
            watermark_frame,
            text="ROLEPLAY ASSISTANT",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#475569"
        ).pack(side="right")

    # ==================== TAB 1: ROLEPLAY & HUD ====================
    def _build_tab_roleplay(self, parent):
        col_frame = ctk.CTkFrame(parent, fg_color="transparent")
        col_frame.pack(fill="both", expand=True, padx=8, pady=6)

        left_col = ctk.CTkFrame(col_frame, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 6))

        right_col = ctk.CTkFrame(col_frame, fg_color="transparent")
        right_col.pack(side="right", fill="both", expand=True, padx=(6, 0))

        # --- Profile Box ---
        p_card = ctk.CTkFrame(left_col, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        p_card.pack(fill="x", pady=(0, 8))

        ctk.CTkLabel(
            p_card,
            text="ROLEPLAY PERSONA & STYLE",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_amber
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Style Selection
        s_box = ctk.CTkFrame(p_card, fg_color="transparent")
        s_box.pack(fill="x", padx=12, pady=4)
        ctk.CTkLabel(s_box, text="Persona / Faction:", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=self.c_text).pack(side="left")
        
        cur_style = self.config.get("current_style", "LSFD / Fire & Medic")
        if cur_style not in self.slang.styles:
            cur_style = self.slang.styles[0]
            self.config.set("current_style", cur_style)

        self.style_var = ctk.StringVar(value=cur_style)
        self.style_menu = ctk.CTkOptionMenu(
            s_box,
            values=self.slang.styles,
            variable=self.style_var,
            command=self._on_style_changed,
            fg_color="#1e293b",
            button_color="#334155",
            button_hover_color="#475569",
            width=210
        )
        self.style_menu.pack(side="right")

        # Tone Selection
        t_box = ctk.CTkFrame(p_card, fg_color="transparent")
        t_box.pack(fill="x", padx=12, pady=(4, 10))
        ctk.CTkLabel(t_box, text="Emotion / Tone:", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color=self.c_text).pack(side="left")
        self.tone_var = ctk.StringVar(value=self.config.get("emotion_tone", "Neutral"))
        self.tone_menu = ctk.CTkOptionMenu(
            t_box,
            values=self.slang.tones,
            variable=self.tone_var,
            command=self._on_tone_changed,
            fg_color="#1e293b",
            button_color="#334155",
            button_hover_color="#475569",
            width=210
        )
        self.tone_menu.pack(side="right")

        # --- Scan Area Box ---
        scan_card = ctk.CTkFrame(left_col, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        scan_card.pack(fill="x")

        ctk.CTkLabel(
            scan_card,
            text="SCREEN SCAN REGION",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_blue
        ).pack(anchor="w", padx=12, pady=(10, 4))

        bbox = self.config.get("bbox", {"left": 265, "top": 233, "width": 645, "height": 73})
        self.bbox_lbl = ctk.CTkLabel(
            scan_card,
            text=f"Coordinates: X={bbox['left']}, Y={bbox['top']} | Width={bbox['width']}, Height={bbox['height']}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=self.c_dim
        )
        self.bbox_lbl.pack(anchor="w", padx=12, pady=2)

        s_btn_box = ctk.CTkFrame(scan_card, fg_color="transparent")
        s_btn_box.pack(fill="x", padx=12, pady=(8, 10))

        set_btn = ctk.CTkButton(
            s_btn_box,
            text="⛶ Select Scan Area",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=32,
            command=self._open_roi_picker
        )
        set_btn.pack(side="left", padx=(0, 4), expand=True, fill="x")

        test_ocr_btn = ctk.CTkButton(
            s_btn_box,
            text="⚡ Quick Test Scan",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=32,
            command=self._test_ocr_scan
        )
        test_ocr_btn.pack(side="left", padx=(4, 0), expand=True, fill="x")

        # 1-Button Mode: Auto-Paste Top Reply Switch
        self.auto_paste_var = ctk.BooleanVar(value=self.config.get("auto_paste_top_reply", False))
        self.auto_paste_sw = ctk.CTkSwitch(
            scan_card,
            text="Auto-Paste Opsi #1 Langsung ke Game (1-Button Mode)",
            variable=self.auto_paste_var,
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_text,
            progress_color="#059669",
            command=self._on_toggle_auto_paste
        )
        self.auto_paste_sw.pack(anchor="w", padx=12, pady=(0, 10))

        # --- RIGHT COLUMN: HUD Sizing & Opacity Controls ---
        hud_card = ctk.CTkFrame(right_col, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        hud_card.pack(fill="both", expand=True)

        ctk.CTkLabel(
            hud_card,
            text="HUD OVERLAY & DISPLAY CONTROLS",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_green
        ).pack(anchor="w", padx=12, pady=(10, 4))

        # Opacity Slider
        alpha_box = ctk.CTkFrame(hud_card, fg_color="transparent")
        alpha_box.pack(fill="x", padx=12, pady=6)
        cur_alpha = float(self.config.get("osd_alpha", 0.88))
        self.alpha_lbl = ctk.CTkLabel(
            alpha_box,
            text=f"Opacity: {int(cur_alpha * 100)}%",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_text
        )
        self.alpha_lbl.pack(side="left")

        self.alpha_slider = ctk.CTkSlider(
            alpha_box,
            from_=0.25,
            to=1.0,
            command=self._on_alpha_slider_changed,
            width=170
        )
        self.alpha_slider.set(cur_alpha)
        self.alpha_slider.pack(side="right")

        # HUD Size Preset Buttons
        size_lbl = ctk.CTkLabel(
            hud_card,
            text="Ukuran Standar HUD (Atau tarik sudut ⤡ RESIZE pada HUD):",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            text_color=self.c_dim
        )
        size_lbl.pack(anchor="w", padx=12, pady=(10, 4))

        preset_box = ctk.CTkFrame(hud_card, fg_color="transparent")
        preset_box.pack(fill="x", padx=12, pady=2)

        ctk.CTkButton(
            preset_box,
            text="Compact (280x450)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="#1e293b",
            hover_color="#334155",
            height=28,
            command=lambda: self._set_hud_preset(280, 450)
        ).pack(side="left", padx=2, expand=True, fill="x")

        ctk.CTkButton(
            preset_box,
            text="Standard (340x580)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="#1e293b",
            hover_color="#334155",
            height=28,
            command=lambda: self._set_hud_preset(340, 580)
        ).pack(side="left", padx=2, expand=True, fill="x")

        ctk.CTkButton(
            preset_box,
            text="Large (420x700)",
            font=ctk.CTkFont(family="Segoe UI", size=10),
            fg_color="#1e293b",
            hover_color="#334155",
            height=28,
            command=lambda: self._set_hud_preset(420, 700)
        ).pack(side="left", padx=2, expand=True, fill="x")

        # HUD Toggle Button
        h_btn_box = ctk.CTkFrame(hud_card, fg_color="transparent")
        h_btn_box.pack(fill="x", padx=12, pady=(16, 10))

        ctk.CTkButton(
            h_btn_box,
            text="👁 Toggle HUD Overlay Show / Hide",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=34,
            command=self._toggle_hud
        ).pack(fill="x")

    # ==================== TAB 2: CUSTOM SHORTCUTS ====================
    def _build_tab_shortcuts(self, parent):
        scroll_hk = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_hk.pack(fill="both", expand=True, padx=8, pady=4)

        info_lbl = ctk.CTkLabel(
            scroll_hk,
            text="Klik tombol 'Change' lalu tekan tombol keyboard apa saja (atau kombinasi multi-key) untuk auto-input:",
            font=ctk.CTkFont(size=11),
            text_color=self.c_dim
        )
        info_lbl.pack(anchor="w", padx=4, pady=(2, 6))

        hk = self.config.get("hotkeys", {})

        self.hk_entries = {}
        self.hk_entry_widgets = {}
        self.hk_change_btns = {}

        shortcuts_list = [
            ("hotkey_ocr", "1-Button: Scan, Terjemah & Buat Balasan AI:", hk.get("hotkey_ocr", "f4")),
            ("hotkey_clipboard", "Auto-Replace Ketikan (Block Teks -> Keybind -> Ganti ke English RP):", hk.get("hotkey_clipboard", "f5")),
            ("hotkey_toggle_hud", "Sembunyikan / Tampilkan HUD Overlay (Toggle HUD):", hk.get("hotkey_toggle_hud", "f6")),
            ("hotkey_ans1", "Tempel Pilihan Balasan #1 ke Chat Game:", hk.get("hotkey_ans1", "ctrl+1")),
            ("hotkey_ans2", "Tempel Pilihan Balasan #2 ke Chat Game:", hk.get("hotkey_ans2", "ctrl+2")),
            ("hotkey_ans3", "Tempel Pilihan Balasan #3 ke Chat Game:", hk.get("hotkey_ans3", "ctrl+3")),
            ("hotkey_cycle_style", "Ganti Persona / Faksi (Cycle Style):", hk.get("hotkey_cycle_style", "alt+1")),
            ("hotkey_cycle_tone", "Ganti Emosi / Nada (Cycle Tone):", hk.get("hotkey_cycle_tone", "alt+2")),
            ("hotkey_toggle_window", "Buka / Tutup Jendela DavisLingo:", hk.get("hotkey_toggle_window", "insert")),
            ("hotkey_scroll_up", "Scroll Tampilan HUD ke Atas:", hk.get("hotkey_scroll_up", "page up")),
            ("hotkey_scroll_down", "Scroll Tampilan HUD ke Bawah:", hk.get("hotkey_scroll_down", "page down"))
        ]

        for key_name, label_text, default_val in shortcuts_list:
            row = ctk.CTkFrame(scroll_hk, fg_color="#0d121e", corner_radius=6, border_width=1, border_color=self.c_card_border)
            row.pack(fill="x", pady=2, padx=4)

            lbl = ctk.CTkLabel(
                row,
                text=label_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=self.c_text,
                width=370,
                anchor="w"
            )
            lbl.pack(side="left", padx=10, pady=4)

            # Clear / Disable button
            clear_btn = ctk.CTkButton(
                row,
                text="Clear",
                font=ctk.CTkFont(family="Consolas", size=10),
                fg_color="#1e293b",
                hover_color="#334155",
                width=50,
                height=26,
                command=lambda k=key_name: self._clear_shortcut(k)
            )
            clear_btn.pack(side="right", padx=(2, 8), pady=4)

            # Change / Record key button
            change_btn = ctk.CTkButton(
                row,
                text="Change",
                font=ctk.CTkFont(family="Consolas", size=10, weight="bold"),
                fg_color="#2563eb",
                hover_color="#1d4ed8",
                width=72,
                height=26,
                command=lambda k=key_name: self._on_click_change_shortcut(k)
            )
            change_btn.pack(side="right", padx=2, pady=4)
            self.hk_change_btns[key_name] = change_btn

            # Shortcut Entry Display
            entry_var = ctk.StringVar(value=default_val)
            entry = ctk.CTkEntry(
                row,
                textvariable=entry_var,
                font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
                fg_color="#080c14",
                text_color=self.c_amber,
                width=140,
                height=26,
                placeholder_text="None"
            )
            entry.pack(side="right", padx=(4, 6), pady=4)
            self.hk_entries[key_name] = entry_var
            self.hk_entry_widgets[key_name] = entry

        # Apply & Reset Buttons Row
        btn_row = ctk.CTkFrame(scroll_hk, fg_color="transparent")
        btn_row.pack(fill="x", pady=(12, 6), padx=4)

        apply_btn = ctk.CTkButton(
            btn_row,
            text="Simpan Semua Keybind",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            height=34,
            command=self._apply_custom_shortcuts
        )
        apply_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        reset_btn = ctk.CTkButton(
            btn_row,
            text="Reset Default",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            width=130,
            height=34,
            command=self._reset_default_shortcuts
        )
        reset_btn.pack(side="left")

    # ==================== TAB 3: SYSTEM & LOGS ====================
    def _build_tab_system(self, parent):
        top_bar = ctk.CTkFrame(parent, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        top_bar.pack(fill="x", padx=8, pady=(4, 6))

        ctk.CTkLabel(
            top_bar,
            text="Engine: ● ONLINE (ULTRA SPEED - LPU ACCELERATED)",
            font=ctk.CTkFont(family="Consolas", size=11, weight="bold"),
            text_color=self.c_green
        ).pack(side="left", padx=12, pady=8)

        test_btn = ctk.CTkButton(
            top_bar,
            text="⚡ Test Latency Ping",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=140,
            height=30,
            command=self._test_api_connection
        )
        test_btn.pack(side="right", padx=12, pady=8)

        # --- AUTO-UPDATE & VERSION STATUS CARD ---
        update_card = ctk.CTkFrame(parent, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        update_card.pack(fill="x", padx=8, pady=(0, 6))

        up_header = ctk.CTkFrame(update_card, fg_color="transparent")
        up_header.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            up_header,
            text="APPLICATION VERSION & AUTO-UPDATE",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_blue
        ).pack(side="left")

        self.update_status_badge = ctk.CTkLabel(
            up_header,
            text=f"v{self.updater.current_version} (LATEST)",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.c_green,
            fg_color="#064e3b",
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.update_status_badge.pack(side="right")

        # Row 1: Status Info (Left) & Action Buttons (Right) - Buttons always have reserved space on right
        up_action_row = ctk.CTkFrame(update_card, fg_color="transparent")
        up_action_row.pack(fill="x", padx=12, pady=(4, 4))

        up_btn_box = ctk.CTkFrame(up_action_row, fg_color="transparent")
        up_btn_box.pack(side="right", padx=(8, 0))

        self.check_update_btn = ctk.CTkButton(
            up_btn_box,
            text="↻ Check for Updates",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=140,
            height=30,
            command=self._manual_check_update
        )
        self.check_update_btn.pack(side="left", padx=(0, 6))

        self.install_update_btn = ctk.CTkButton(
            up_btn_box,
            text="↓ Install Update Now",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            width=150,
            height=30,
            command=self._start_update_process
        )
        # Not packed initially, packed into up_btn_box when update is detected!

        self.update_info_lbl = ctk.CTkLabel(
            up_action_row,
            text=f"Versi Aktif: v{self.updater.current_version} | Status: Sistem termutakhir.",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=self.c_text,
            anchor="w"
        )
        self.update_info_lbl.pack(side="left", fill="x", expand=True)

        # Row 2: Dedicated Full-Width Changelog Display Box (Spans full width, will NEVER collide with buttons!)
        cl_header_row = ctk.CTkFrame(update_card, fg_color="transparent")
        cl_header_row.pack(fill="x", padx=12, pady=(2, 0))
        ctk.CTkLabel(
            cl_header_row,
            text="Release Notes / Changelog:",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color="#94a3b8"
        ).pack(side="left")

        self.update_changelog_box = ctk.CTkTextbox(
            update_card,
            height=58,
            fg_color="#080c14",
            text_color=self.c_dim,
            font=ctk.CTkFont(family="Segoe UI", size=10),
            border_width=1,
            border_color="#1a2234",
            corner_radius=6,
            wrap="word",
            activate_scrollbars=True
        )
        self.update_changelog_box.pack(fill="x", padx=12, pady=(2, 10))
        self._set_update_changelog("Siap digunakan untuk GTA V Roleplay FiveM.")

        # --- GROQ API KEY CONFIGURATION CARD (ANTI-COPY PROTECTED) ---
        self.MASKED_KEY_DUMMY = "*" * 38
        key_card = ctk.CTkFrame(parent, fg_color="#0d121e", corner_radius=8, border_width=1, border_color=self.c_card_border)
        key_card.pack(fill="x", padx=8, pady=(0, 6))

        card_header = ctk.CTkFrame(key_card, fg_color="transparent")
        card_header.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            card_header,
            text="GROQ CLOUD API KEY - PRIVATE & SECURED",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_amber
        ).pack(side="left")

        self.groq_key_status = ctk.CTkLabel(
            card_header,
            text="ACTIVE & PROTECTED",
            font=ctk.CTkFont(family="Segoe UI", size=9, weight="bold"),
            text_color=self.c_green,
            fg_color="#064e3b",
            corner_radius=4,
            padx=8,
            pady=2
        )
        self.groq_key_status.pack(side="right")

        ctrl_row = ctk.CTkFrame(key_card, fg_color="transparent")
        ctrl_row.pack(fill="x", padx=12, pady=(2, 10))

        ctk.CTkLabel(
            ctrl_row,
            text="API Key:",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color=self.c_text
        ).pack(side="left", padx=(0, 8))

        self.groq_key_var = ctk.StringVar()
        self.groq_key_entry = ctk.CTkEntry(
            ctrl_row,
            textvariable=self.groq_key_var,
            show="*",
            font=ctk.CTkFont(family="Consolas", size=11),
            fg_color="#080c14",
            text_color=self.c_green,
            placeholder_text="Paste API Key Baru...",
            height=30
        )
        self.groq_key_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

        # --- HARDENED ANTI-COPY PROTECTION ---
        def _block_copy_action(event):
            return "break"

        inner_e = self.groq_key_entry._entry
        for evt in ("<<Copy>>", "<Control-c>", "<Control-C>", "<Control-Insert>",
                    "<<Cut>>", "<Control-x>", "<Control-X>", "<Shift-Delete>"):
            inner_e.bind(evt, _block_copy_action)
            self.groq_key_entry.bind(evt, _block_copy_action)

        inner_e.bind("<Button-3>", lambda e: "break")
        self.groq_key_entry.bind("<Button-3>", lambda e: "break")

        # Buttons: Paste, Clear, Save, Cancel
        paste_btn = ctk.CTkButton(
            ctrl_row,
            text="Paste",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            width=65,
            height=30,
            command=self._paste_groq_key
        )
        paste_btn.pack(side="left", padx=(0, 4))

        clear_btn = ctk.CTkButton(
            ctrl_row,
            text="Clear",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#334155",
            hover_color="#475569",
            width=60,
            height=30,
            command=self._clear_groq_key
        )
        clear_btn.pack(side="left", padx=(0, 4))

        save_btn = ctk.CTkButton(
            ctrl_row,
            text="Save Key",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            fg_color="#059669",
            hover_color="#047857",
            width=75,
            height=30,
            command=self._save_groq_key
        )
        save_btn.pack(side="left", padx=(0, 4))

        cancel_btn = ctk.CTkButton(
            ctrl_row,
            text="Cancel",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            fg_color="#475569",
            hover_color="#64748b",
            width=65,
            height=30,
            command=self._cancel_groq_key
        )
        cancel_btn.pack(side="left")

        # Initialize masked key status
        self._init_groq_key_display()

        # --- LOG CONSOLE HEADER WITH CLEAR BUTTON ---
        log_header = ctk.CTkFrame(parent, fg_color="transparent")
        log_header.pack(fill="x", padx=8, pady=(4, 2))

        ctk.CTkLabel(
            log_header,
            text="ACTIVITY & SYSTEM CONSOLE LOGS",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            text_color=self.c_dim
        ).pack(side="left", padx=2)

        clear_log_btn = ctk.CTkButton(
            log_header,
            text="🗑 Clear Console Logs",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color="#1e293b",
            hover_color="#dc2626",
            text_color="#f87171",
            border_width=1,
            border_color="#475569",
            width=135,
            height=26,
            command=self.clear_logs
        )
        clear_log_btn.pack(side="right", padx=2)

        # Log Text Box
        self.log_text = ctk.CTkTextbox(
            parent,
            font=ctk.CTkFont(family="Consolas", size=10),
            fg_color="#070a10",
            text_color=self.c_text,
            wrap="word",
            activate_scrollbars=True
        )
        self.log_text.pack(fill="both", expand=True, padx=8, pady=(0, 6))

    # ==================== EVENT HANDLERS ====================
    def clear_logs(self):
        self.log_text.delete("1.0", "end")
        self.log_message("[SYSTEM] Log konsol berhasil dibersihkan.")

    def log_message(self, message):
        def _append():
            timestamp = time.strftime("%H:%M:%S")
            self.log_text.insert("end", f"[{timestamp}] {message}\n")
            self.log_text.see("end")
        self.after(0, _append)

    # ==================== AUTO-UPDATER HANDLERS ====================
    def _silent_check_update(self):
        def _bg():
            has_update, info = self.updater.check_for_updates()
            if has_update:
                self.after(0, lambda: self._apply_update_detected(info, is_silent=True))
        threading.Thread(target=_bg, daemon=True).start()

    def _set_update_changelog(self, text, is_highlight=False):
        if hasattr(self, "update_changelog_box") and self.update_changelog_box:
            self.update_changelog_box.configure(state="normal")
            self.update_changelog_box.delete("1.0", "end")
            self.update_changelog_box.insert("1.0", str(text).strip())
            color = self.c_text if is_highlight else self.c_dim
            self.update_changelog_box.configure(text_color=color)
            self.update_changelog_box.configure(state="disabled")

    def _manual_check_update(self):
        self.check_update_btn.configure(state="disabled", text="Memeriksa...")
        self.update_info_lbl.configure(text="Menghubungi server update untuk cek rilis terbaru...")
        self._set_update_changelog("Memeriksa pembaruan rilis...", is_highlight=False)

        def _bg():
            has_update, info = self.updater.check_for_updates()
            def _ui():
                self.check_update_btn.configure(state="normal", text="↻ Check for Updates")
                if has_update:
                    self._apply_update_detected(info, is_silent=False)
                else:
                    self.update_status_badge.configure(
                        text=f"v{self.updater.current_version} (LATEST)",
                        fg_color="#064e3b",
                        text_color=self.c_green
                    )
                    self.update_info_lbl.configure(
                        text=f"Versi Aktif: v{self.updater.current_version} | Status: Aplikasi Anda sudah paling baru!",
                        text_color=self.c_green
                    )
                    self._set_update_changelog("Tidak ada pembaruan baru saat ini. Anda menggunakan versi terbaru.", is_highlight=False)
                    self.log_message(f"[UPDATER] DavisLingo v{self.updater.current_version} sudah menggunakan versi terbaru.")
            self.after(0, _ui)
        threading.Thread(target=_bg, daemon=True).start()

    def _apply_update_detected(self, info, is_silent=False):
        self._pending_update_info = info
        lat_v = info.get("latest_version", "")
        changelog = info.get("changelog", "Pembaruan sistem.")
        rel_date = info.get("release_date", "-")

        self.update_status_badge.configure(
            text=f"UPDATE TERSEDIA: v{lat_v}",
            fg_color="#854d0e",
            text_color="#fde047"
        )
        self.update_info_lbl.configure(
            text=f"Versi Baru: v{lat_v} (Rilis: {rel_date}) - Siap diunduh!",
            text_color="#fde047"
        )
        self._set_update_changelog(changelog, is_highlight=True)

        if not self.install_update_btn.winfo_ismapped():
            self.install_update_btn.pack(side="left")

        self.log_message(f"[UPDATER] Versi baru v{lat_v} tersedia! Changelog: {changelog}")
        if self.hud:
            self.hud.show_status_message(f"UPDATE v{lat_v} TERSEDIA (Tab System)")

    def _start_update_process(self):
        if not getattr(self, "_pending_update_info", None):
            self._manual_check_update()
            return

        import os, sys, tempfile
        info = self._pending_update_info
        lat_v = info.get("latest_version", "Baru")
        dl_url = info.get("download_url", "")

        prog_win = ctk.CTkToplevel(self)
        prog_win.title("DavisLingo Auto-Updater")
        prog_win.geometry("460x230")
        prog_win.resizable(False, False)
        prog_win.attributes("-topmost", True)
        prog_win.configure(fg_color="#090d16")

        try:
            x = self.winfo_x() + (self.winfo_width() - 460) // 2
            y = self.winfo_y() + (self.winfo_height() - 230) // 2
            prog_win.geometry(f"+{max(0, x)}+{max(0, y)}")
        except Exception:
            pass

        title_lbl = ctk.CTkLabel(
            prog_win,
            text=f"MEMPERBARUI KE VERSI {lat_v}",
            font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
            text_color="#38bdf8"
        )
        title_lbl.pack(pady=(16, 6))

        desc_lbl = ctk.CTkLabel(
            prog_win,
            text="Mengunduh paket instalasi dari server Google Drive...",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        desc_lbl.pack(pady=(0, 10))

        prog_bar = ctk.CTkProgressBar(prog_win, width=390, height=14, corner_radius=6, progress_color="#00d4ff")
        prog_bar.set(0.0)
        prog_bar.pack(pady=4)

        stat_lbl = ctk.CTkLabel(
            prog_win,
            text="Menghubungkan ke server...",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#f1f5f9"
        )
        stat_lbl.pack(pady=(4, 12))

        cancel_btn = ctk.CTkButton(
            prog_win,
            text="Batal",
            fg_color="#334155",
            hover_color="#475569",
            width=80,
            command=prog_win.destroy
        )
        cancel_btn.pack()

        def _download_thread():
            temp_zip = os.path.join(tempfile.gettempdir(), f"davislingo_update_{lat_v}.zip")

            def _on_progress(pct, dl_mb, tot_mb):
                def _ui_update():
                    prog_bar.set(pct / 100.0)
                    if tot_mb > 0:
                        stat_lbl.configure(text=f"{dl_mb:.1f} MB / {tot_mb:.1f} MB ({int(pct)}%)")
                    else:
                        stat_lbl.configure(text=f"{dl_mb:.1f} MB diunduh...")
                self.after(0, _ui_update)

            try:
                self.log_message(f"[UPDATER] Memulai unduhan versi {lat_v}...")
                self.updater.download_update_package(dl_url, temp_zip, progress_callback=_on_progress)
                self.log_message("[UPDATER] Unduhan selesai 100%. Mempersiapkan instalasi...")

                def _finish_ui():
                    prog_bar.set(1.0)
                    prog_bar.configure(progress_color="#4ade80")
                    desc_lbl.configure(text="Pembaruan berhasil diunduh!", text_color="#4ade80")
                    stat_lbl.configure(text="Memulai restart aplikasi dalam 2 detik...")
                    cancel_btn.configure(state="disabled")

                    def _trigger_swap():
                        self.log_message("[UPDATER] Menjalankan installer dan merestart aplikasi...")
                        self.updater.launch_updater_and_restart(temp_zip)
                        self.destroy()
                        sys.exit(0)

                    self.after(1500, _trigger_swap)

                self.after(0, _finish_ui)

            except Exception as e:
                self.log_message(f"[UPDATER ERROR] Gagal mengunduh pembaruan: {e}")
                def _err_ui():
                    desc_lbl.configure(text=f"Gagal mengunduh update: {e}", text_color="#f87171")
                    stat_lbl.configure(text="Silakan coba lagi beberapa saat lagi.")
                    prog_bar.configure(progress_color="#ef4444")
                self.after(0, _err_ui)

        threading.Thread(target=_download_thread, daemon=True).start()

    # ==================== GROQ API KEY HANDLERS (ANTI-COPY PROTECTED) ====================
    def _init_groq_key_display(self):
        cur_key = self.config.get("groq_api_key", "").strip()
        if cur_key:
            self.groq_key_var.set(self.MASKED_KEY_DUMMY)
            self.groq_key_entry.configure(text_color=self.c_green)
            self.groq_key_status.configure(text="ACTIVE & PROTECTED", fg_color="#064e3b", text_color=self.c_green)
        else:
            self.groq_key_var.set("")
            self.groq_key_entry.configure(text_color=self.c_text)
            self.groq_key_status.configure(text="KEY EMPTY", fg_color="#7f1d1d", text_color="#fca5a5")

    def _paste_groq_key(self):
        try:
            clip_text = self.clipboard_get().strip()
        except Exception:
            clip_text = ""

        if not clip_text:
            self.log_message("[API KEY] Clipboard kosong! Salin API key Groq Anda terlebih dahulu.")
            messagebox.showwarning("Clipboard Kosong", "Clipboard Anda kosong. Silakan salin (Copy) API key terlebih dahulu.")
            return

        self.groq_key_var.set(clip_text)
        self.groq_key_entry.configure(text_color=self.c_amber)
        self.groq_key_status.configure(text="⚡ READY TO SAVE", fg_color="#854d0e", text_color="#fef08a")
        self.log_message("[API KEY] Key baru di-paste dari clipboard. Klik 'Save' untuk menyimpan.")

    def _clear_groq_key(self):
        self.groq_key_var.set("")
        self.groq_key_entry.configure(text_color=self.c_text)
        self.groq_key_status.configure(text="◌ CLEARED / WAITING", fg_color="#1e293b", text_color="#94a3b8")
        self.log_message("[API KEY] Field dikosongkan. Siap menerima input/paste API key baru.")

    def _save_groq_key(self):
        entered_val = self.groq_key_var.get().strip()
        if not entered_val:
            messagebox.showwarning("Warning", "API Key tidak boleh kosong!")
            return

        if entered_val == self.MASKED_KEY_DUMMY:
            self.log_message("[API KEY] Tidak ada perubahan pada Groq API key.")
            return

        # Save new key to config.json
        self.config.set("groq_api_key", entered_val)
        self.log_message("[API KEY] Groq Cloud API Key berhasil diperbarui dan disimpan aman!")

        # Re-mask the field immediately so the actual key is never sitting in the widget
        self.groq_key_var.set(self.MASKED_KEY_DUMMY)
        self.groq_key_entry.configure(text_color=self.c_green)
        self.groq_key_status.configure(text="ACTIVE & PROTECTED", fg_color="#064e3b", text_color=self.c_green)

        try:
            import winsound
            winsound.Beep(1400, 70)
        except Exception:
            pass

        messagebox.showinfo("Success", "Groq Cloud API Key berhasil diperbarui dan diproteksi!")

    def _cancel_groq_key(self):
        self._init_groq_key_display()
        self.log_message("[API KEY] Perubahan dibatalkan. Mengembalikan status API key aktif.")

    def _on_style_changed(self, new_style):
        self.config.set("current_style", new_style)
        tone = self.config.get("emotion_tone", "Neutral")
        if self.hud:
            self.hud.update_profile(new_style, tone=tone)
        self.log_message(f"[STYLE] Switched to: {new_style}")

    def _on_slang_slider_changed(self, val):
        pass

    def _on_tone_changed(self, new_tone):
        self.config.set("emotion_tone", new_tone)
        style = self.config.get("current_style", "LSFD / Fire & Medic")
        if self.hud:
            self.hud.update_profile(style, tone=new_tone)
        self.log_message(f"[TONE] Set emotion/tone to: {new_tone}")

    def _on_alpha_slider_changed(self, val):
        alpha_val = float(val)
        self.alpha_lbl.configure(text=f"Opacity: {int(alpha_val * 100)}%")
        if self.hud:
            self.hud.set_opacity(alpha_val)

    def _set_hud_preset(self, w, h):
        if self.hud:
            self.hud.width = w
            self.hud.height = h
            self.hud.window.geometry(f"{w}x{h}")
            self.hud._save_geometry()
            self.log_message(f"[HUD RESIZE] Applied preset: {w}x{h}")

    # ==================== INTERACTIVE SHORTCUT RECORDER ====================
    def _stop_recording_hook(self):
        import keyboard
        if self._recording_hook is not None:
            try:
                keyboard.unhook(self._recording_hook)
            except Exception:
                pass
            self._recording_hook = None

    def _on_click_change_shortcut(self, key_name):
        # If currently recording this specific key, treat click as Cancel
        if self._recording_key_name == key_name:
            self._cancel_recording_shortcut()
            return

        # If recording another key, cancel that first
        if self._recording_key_name is not None:
            self._cancel_recording_shortcut()

        self._start_recording_shortcut(key_name)

    def _start_recording_shortcut(self, key_name):
        import keyboard
        self._recording_key_name = key_name
        self._recording_original_val = self.hk_entries[key_name].get().strip()
        self._recording_pressed_mods.clear()

        # 1. Clear the shortcut field immediately upon clicking 'Change'
        self.hk_entries[key_name].set("")

        # 2. Update entry border and placeholder
        entry_widget = self.hk_entry_widgets.get(key_name)
        if entry_widget:
            entry_widget.configure(placeholder_text="[ TEKAN TOMBOL... ]", border_color="#38bdf8", border_width=2)
            entry_widget.focus_set()

        # 3. Change button text to Cancel with reddish alert styling
        change_btn = self.hk_change_btns.get(key_name)
        if change_btn:
            change_btn.configure(text="Cancel", fg_color="#dc2626", hover_color="#b91c1c")

        # 4. Temporarily unhook active global hotkeys so they do not fire macros during recording
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass

        # 5. Attach hook
        self._recording_hook = keyboard.hook(self._on_record_key_event)
        self.log_message(f"[SHORTCUT] Recording mode active for '{key_name}'. Tekan tombol atau kombinasi (Esc untuk batal)...")

    def _on_record_key_event(self, event):
        if not self._recording_key_name:
            return

        raw_name = (event.name or "").strip().lower()
        if not raw_name:
            return

        MODIFIERS = {
            'left ctrl': 'ctrl', 'right ctrl': 'ctrl', 'ctrl': 'ctrl', 'control': 'ctrl',
            'left alt': 'alt', 'right alt': 'alt', 'alt': 'alt', 'alt gr': 'alt',
            'left shift': 'shift', 'right shift': 'shift', 'shift': 'shift',
            'left windows': 'windows', 'right windows': 'windows', 'windows': 'windows'
        }

        norm_mod = MODIFIERS.get(raw_name)

        if event.event_type == 'down':
            if norm_mod:
                self._recording_pressed_mods.add(norm_mod)
                # Live preview of modifiers held down
                ordered = [m for m in ['ctrl', 'alt', 'shift', 'windows'] if m in self._recording_pressed_mods]
                preview_text = " + ".join([m.upper() for m in ordered]) + " + ..."
                self.after(0, lambda p=preview_text: self._update_recording_display(p))
            else:
                # Trigger key pressed!
                # If ESC pressed alone without modifiers -> cancel recording
                if raw_name in ('esc', 'escape') and not self._recording_pressed_mods:
                    self.after(0, self._cancel_recording_shortcut)
                    return

                # Build final combo
                ordered = [m for m in ['ctrl', 'alt', 'shift', 'windows'] if m in self._recording_pressed_mods]
                clean_key = raw_name
                if clean_key == 'prior': clean_key = 'page up'
                elif clean_key == 'next': clean_key = 'page down'

                if clean_key not in ordered:
                    final_combo = "+".join(ordered + [clean_key])
                else:
                    final_combo = "+".join(ordered)

                self.after(0, lambda c=final_combo: self._finish_recording_shortcut(c))

        elif event.event_type == 'up':
            if norm_mod and norm_mod in self._recording_pressed_mods:
                self._recording_pressed_mods.discard(norm_mod)
                if self._recording_pressed_mods:
                    ordered = [m for m in ['ctrl', 'alt', 'shift', 'windows'] if m in self._recording_pressed_mods]
                    preview_text = " + ".join([m.upper() for m in ordered]) + " + ..."
                    self.after(0, lambda p=preview_text: self._update_recording_display(p))
                else:
                    self.after(0, lambda: self._update_recording_display(""))

    def _update_recording_display(self, text):
        if self._recording_key_name and self._recording_key_name in self.hk_entries:
            self.hk_entries[self._recording_key_name].set(text)

    def _finish_recording_shortcut(self, combo):
        key_name = self._recording_key_name
        if not key_name:
            return

        self._stop_recording_hook()

        clean_combo = combo.strip().lower()
        self.hk_entries[key_name].set(clean_combo)

        change_btn = self.hk_change_btns.get(key_name)
        if change_btn:
            change_btn.configure(text="Change", fg_color="#2563eb", hover_color="#1d4ed8")

        entry_widget = self.hk_entry_widgets.get(key_name)
        if entry_widget:
            entry_widget.configure(placeholder_text="[None / Empty]", border_color=self.c_card_border, border_width=1)

        self._recording_key_name = None
        self._recording_pressed_mods.clear()

        # Auto-save immediately to config
        new_hk = self.config.get("hotkeys", {})
        new_hk[key_name] = clean_combo
        self.config.set("hotkeys", new_hk)

        # Re-register all global hotkeys
        if self.rebind_hotkeys:
            self.rebind_hotkeys()
        if self.hud:
            self.hud.update_shortcut_hints()

        self.log_message(f"[SHORTCUT] Recorded '{key_name}': {clean_combo.upper()} (Auto-Saved & Registered)")
        try:
            import winsound
            winsound.Beep(1200, 60)
        except Exception:
            pass

    def _cancel_recording_shortcut(self):
        key_name = self._recording_key_name
        if not key_name:
            return

        self._stop_recording_hook()

        if self._recording_original_val is not None:
            self.hk_entries[key_name].set(self._recording_original_val)

        change_btn = self.hk_change_btns.get(key_name)
        if change_btn:
            change_btn.configure(text="Change", fg_color="#2563eb", hover_color="#1d4ed8")

        entry_widget = self.hk_entry_widgets.get(key_name)
        if entry_widget:
            entry_widget.configure(placeholder_text="[None / Empty]", border_color=self.c_card_border, border_width=1)

        self._recording_key_name = None
        self._recording_pressed_mods.clear()

        # Re-register previous hotkeys
        if self.rebind_hotkeys:
            self.rebind_hotkeys()

        self.log_message("[SHORTCUT] Recording cancelled. Restored previous shortcut.")

    def _clear_shortcut(self, key_name):
        if self._recording_key_name == key_name:
            self._cancel_recording_shortcut()

        self.hk_entries[key_name].set("")

        # Auto-save empty string (disabled hotkey)
        new_hk = self.config.get("hotkeys", {})
        new_hk[key_name] = ""
        self.config.set("hotkeys", new_hk)

        if self.rebind_hotkeys:
            self.rebind_hotkeys()
        if self.hud:
            self.hud.update_shortcut_hints()

        self.log_message(f"[SHORTCUT] Cleared shortcut for '{key_name}' (Disabled).")

    def _apply_custom_shortcuts(self):
        new_hk = {}
        for key_name, var in self.hk_entries.items():
            val = var.get().strip().lower()
            new_hk[key_name] = val

        self.config.set("hotkeys", new_hk)
        if self.rebind_hotkeys:
            self.rebind_hotkeys()
        if self.hud:
            self.hud.update_shortcut_hints()
        self.log_message("[SHORTCUTS] All custom keybindings applied successfully!")
        messagebox.showinfo("Success", "Custom shortcuts updated and registered successfully!")

    def _reset_default_shortcuts(self):
        defaults = {
            "hotkey_ocr": "f4",
            "hotkey_clipboard": "f5",
            "hotkey_toggle_hud": "f6",
            "hotkey_ans1": "ctrl+1",
            "hotkey_ans2": "ctrl+2",
            "hotkey_ans3": "ctrl+3",
            "hotkey_cycle_style": "alt+1",
            "hotkey_cycle_tone": "alt+2",
            "hotkey_toggle_window": "insert",
            "hotkey_scroll_up": "page up",
            "hotkey_scroll_down": "page down"
        }
        for k, v in defaults.items():
            if k in self.hk_entries:
                self.hk_entries[k].set(v)
        self._apply_custom_shortcuts()

    def destroy(self):
        self._stop_recording_hook()
        super().destroy()

    def _open_roi_picker(self):
        from roi_picker import RoiPicker
        self.log_message("[SCAN AREA] Click and drag rectangle over FiveM chat box...")
        RoiPicker(self, self._on_bbox_selected)

    def _on_bbox_selected(self, bbox):
        self.config.set("bbox", bbox)
        self.bbox_lbl.configure(
            text=f"X={bbox['left']}, Y={bbox['top']} | W={bbox['width']}, H={bbox['height']}"
        )
        self.log_message(f"[SCAN AREA] New BBox updated: {bbox}")

    def _on_toggle_auto_paste(self):
        val = self.auto_paste_var.get()
        self.config.set("auto_paste_top_reply", val)
        if val:
            self.log_message("[1-BUTTON MODE] Diaktifkan: Scan game akan langsung meng-auto-paste balasan Opsi #1 ke chat FiveM!")
        else:
            self.log_message("[1-BUTTON MODE] Dinonaktifkan: Pemain memilih opsi balasan secara manual (Ctrl+1, 2, 3).")

    def _test_ocr_scan(self):
        if getattr(self, "_is_scanning", False):
            self.log_message("[OCR SCAN] Scan sebelumnya masih diproses...")
            return

        def _worker():
            self._is_scanning = True
            try:
                self.log_message("[OCR SCAN] Triggered scan on screen BBox...")
                if self.hud:
                    self.hud.prepare_for_new_scan()

                bbox = self.config.get("bbox")
                scanned_text = self.ocr.capture_and_read(bbox)
                self.log_message(f"[OCR SCAN] Extracted text: '{scanned_text}'")
                if not scanned_text:
                    self.log_message("[OCR SCAN] No readable text found in scan area.")
                    if self.hud:
                        self.hud.update_ocr_result("", "Area kosong atau teks tidak terbaca.")
                    return

                if self.hud:
                    self.hud.show_status_message("GENERATING AI REPLIES...")

                try:
                    reply_data = self.ai.translate_and_reply_incoming(scanned_text)
                except Exception as ai_err:
                    self.log_message(f"[AI ERROR] Gagal request AI ({ai_err}), menggunakan respons RP fallback aman.")
                    reply_data = self.ai.get_safe_fallback_replies(scanned_text)

                trans_id = reply_data.get("terjemahan_ocr", "")
                opts_id = reply_data.get("opsi_id", [])
                opts_en = reply_data.get("opsi_en", [])

                self.macro.set_active_options(opts_en)
                if self.hud:
                    self.hud.update_ocr_result(scanned_text, trans_id, opts_id, opts_en)
                self.log_message(f"[AI TRANSLATE] {trans_id}")
                for idx, en_opt in enumerate(opts_en):
                    self.log_message(f"   Option #{idx+1}: {en_opt}")

                # 1-Button Mode: If enabled, automatically paste Option #1 into FiveM
                if self.config.get("auto_paste_top_reply", False) and opts_en:
                    self.log_message("[1-BUTTON MODE] Auto-pasting Opsi #1 ke chat FiveM...")
                    time.sleep(0.12)
                    self.macro.handle_reply_selection(0)

            except Exception as e:
                self.log_message(f"[OCR SCAN ERROR] {e}")
                if self.hud:
                    self.hud.show_status_message(f"SCAN ERROR: {e}")
            finally:
                self._is_scanning = False

        threading.Thread(target=_worker, daemon=True).start()

    def toggle_hud_visibility(self):
        if self.hud:
            self.hud.toggle_visibility()

    def _toggle_hud(self):
        self.toggle_hud_visibility()

    def _test_api_connection(self):
        def _worker():
            self.log_message("[API TEST] Sending test ping to AI Engine...")
            t0 = time.time()
            try:
                res = self.ai.translate_outgoing("Halo kawan, apa kabar?", style="LSFD / Fire & Medic")
                dt = time.time() - t0
                self.log_message(f"[API TEST] SUCCESS ({dt:.2f}s latency): '{res}'")
            except Exception as e:
                self.log_message(f"[API TEST] ERROR: {e}")
        threading.Thread(target=_worker, daemon=True).start()

    def cycle_style(self):
        styles = self.slang.styles
        cur = self.config.get("current_style", "LSFD / Fire & Medic")
        try:
            next_idx = (styles.index(cur) + 1) % len(styles)
        except ValueError:
            next_idx = 0
        new_style = styles[next_idx]
        self.style_var.set(new_style)
        self._on_style_changed(new_style)
        if self.hud:
            self.hud.show_status_message(f"STYLE: {new_style.upper()}")

    def cycle_slang(self):
        pass

    def cycle_tone(self):
        tones = self.slang.tones
        cur = self.config.get("emotion_tone", "Neutral")
        try:
            next_idx = (tones.index(cur) + 1) % len(tones)
        except ValueError:
            next_idx = 0
        new_tone = tones[next_idx]
        self.tone_var.set(new_tone)
        self._on_tone_changed(new_tone)
        if self.hud:
            self.hud.show_status_message(f"TONE: {new_tone.upper()}")

    def toggle_window_visibility(self):
        if self.state() == "normal":
            self.withdraw()
        else:
            self.deiconify()
            self.lift()
