import tkinter as tk
import time

class HudOverlay:
    def __init__(self, root, config_manager):
        self.root = root
        self.config = config_manager

        self.window = tk.Toplevel(self.root)
        self.window.title("DAVISLINGO_HUD")
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        
        # Color palette: Tokyo Night / Dark Obsidian
        self.bg_color = "#090c14"
        self.card_bg = "#111622"
        self.card_border = "#1e2638"
        self.accent_blue = "#38bdf8"
        self.accent_green = "#4ade80"
        self.accent_amber = "#fbbf24"
        self.text_main = "#f1f5f9"
        self.text_dim = "#94a3b8"

        self.window.configure(bg=self.bg_color)

        # Alpha transparency
        alpha = float(self.config.get("osd_alpha", 0.88))
        self.window.attributes("-alpha", alpha)

        # Positioning & Sizing
        osd_bbox = self.config.get("osd_bbox", {"left": 1091, "top": 122, "width": 340, "height": 580})
        self.pos_x = int(osd_bbox.get("left", 1091))
        self.pos_y = int(osd_bbox.get("top", 122))
        self.width = max(260, int(osd_bbox.get("width", 340)))
        self.height = max(260, int(osd_bbox.get("height", 580)))
        self.window.geometry(f"{self.width}x{self.height}+{self.pos_x}+{self.pos_y}")

        self._build_ui()

        # If OSD disabled in config, hide
        self.is_visible = bool(self.config.get("osd_enabled", True))
        if not self.is_visible:
            self.window.withdraw()

    def _build_ui(self):
        # Outer Container with subtle border
        self.outer_frame = tk.Frame(
            self.window,
            bg=self.bg_color,
            highlightbackground=self.card_border,
            highlightthickness=1
        )
        self.outer_frame.pack(fill=tk.BOTH, expand=True)

        # 1. TOP HEADER (Drag-to-Move Area)
        self.header_frame = tk.Frame(self.outer_frame, bg=self.card_bg, padx=8, pady=5, cursor="fleur")
        self.header_frame.pack(fill=tk.X, side=tk.TOP)

        # Title Label
        title_lbl = tk.Label(
            self.header_frame,
            text="DAVISLINGO HUD",
            font=("Consolas", 10, "bold"),
            fg=self.accent_blue,
            bg=self.card_bg
        )
        title_lbl.pack(side=tk.LEFT)

        # Status Dot
        self.status_dot = tk.Label(
            self.header_frame,
            text="● ACTIVE",
            font=("Segoe UI", 8, "bold"),
            fg=self.accent_green,
            bg=self.card_bg
        )
        self.status_dot.pack(side=tk.RIGHT)

        # Bind dragging to header and title
        self._drag_start_x = 0
        self._drag_start_y = 0
        for w in (self.header_frame, title_lbl, self.status_dot):
            w.bind("<ButtonPress-1>", self._start_drag)
            w.bind("<B1-Motion>", self._on_drag)

        # 2. STATUS & PROFILE BADGE
        profile_frame = tk.Frame(self.outer_frame, bg=self.bg_color, padx=8, pady=4)
        profile_frame.pack(fill=tk.X, side=tk.TOP)

        self.profile_badge = tk.Label(
            profile_frame,
            text="LSFD / FIRE & MEDIC • NEUTRAL",
            font=("Consolas", 8, "bold"),
            fg=self.accent_amber,
            bg=self.card_bg,
            padx=8,
            pady=3
        )
        self.profile_badge.pack(fill=tk.X)

        self.toast_lbl = tk.Label(
            profile_frame,
            text="READY (Scroll: Wheel / PgUp-PgDn)",
            font=("Segoe UI", 8),
            fg=self.accent_green,
            bg=self.bg_color,
            wraplength=300,
            justify=tk.LEFT,
            anchor="w"
        )
        self.toast_lbl.pack(fill=tk.X, pady=(2, 0))

        # 3. BOTTOM FOOTER (Resize Handle & Info)
        self.footer_frame = tk.Frame(self.outer_frame, bg=self.card_bg, padx=6, pady=3)
        self.footer_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.footer_hint = tk.Label(
            self.footer_frame,
            text="ViendLab • JGVRP Assistant",
            font=("Segoe UI", 7),
            fg=self.text_dim,
            bg=self.card_bg
        )
        self.footer_hint.pack(side=tk.LEFT)

        # Resize Grip Handle
        self.grip = tk.Label(
            self.footer_frame,
            text="⤡ RESIZE",
            font=("Consolas", 8, "bold"),
            fg=self.accent_blue,
            bg=self.card_bg,
            cursor="size_nw_se",
            padx=4
        )
        self.grip.pack(side=tk.RIGHT)

        # 4. SCROLLABLE MIDDLE CONTAINER (Canvas + Frame)
        canvas_container = tk.Frame(self.outer_frame, bg=self.bg_color)
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=6, pady=4)

        self.canvas = tk.Canvas(
            canvas_container,
            bg=self.bg_color,
            highlightthickness=0,
            borderwidth=0
        )
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.scrollable_frame,
            anchor="nw"
        )

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width)
        )

        # 5. EIGHT-DIRECTIONAL FREEFORM RESIZE BORDERS (N, S, W, E, NW, NE, SW, SE)
        self._init_8way_borders()

        # Bind mouse wheel scrolling across canvas and children
        self._bind_mousewheel(self.window)

        # --- BUILD CARDS INSIDE SCROLLABLE FRAME ---
        # Card A: Incoming OCR Scan Result
        self.scan_card = tk.Frame(
            self.scrollable_frame,
            bg=self.card_bg,
            highlightbackground=self.card_border,
            highlightthickness=1,
            padx=8,
            pady=6
        )
        self.scan_card.pack(fill=tk.X, pady=(0, 6))

        self.ocr_header = tk.Label(
            self.scan_card,
            text="DETECTED INCOMING CHAT",
            font=("Consolas", 8, "bold"),
            fg=self.text_dim,
            bg=self.card_bg,
            anchor="w"
        )
        self.ocr_header.pack(fill=tk.X)

        self.ocr_src_lbl = tk.Label(
            self.scan_card,
            text="Raw: (Menunggu pemindaian teks...)",
            font=("Segoe UI", 8, "italic"),
            fg=self.text_dim,
            bg=self.card_bg,
            wraplength=300,
            justify=tk.LEFT,
            anchor="w"
        )
        self.ocr_src_lbl.pack(fill=tk.X, pady=(2, 2))

        self.ocr_trans_lbl = tk.Label(
            self.scan_card,
            text="Arti: -",
            font=("Segoe UI", 9, "bold"),
            fg=self.text_main,
            bg=self.card_bg,
            wraplength=300,
            justify=tk.LEFT,
            anchor="w"
        )
        self.ocr_trans_lbl.pack(fill=tk.X, pady=(1, 0))

        # Card B: AI Smart Reply Section Header
        self.reply_header = tk.Label(
            self.scrollable_frame,
            text="AI SMART REPLIES",
            font=("Consolas", 8, "bold"),
            fg=self.accent_blue,
            bg=self.bg_color,
            anchor="w"
        )
        self.reply_header.pack(fill=tk.X, pady=(2, 4))

        # Reply Cards (Options 1, 2, 3)
        self.reply_frames = []
        self.reply_en_labels = []
        self.reply_id_labels = []
        self.reply_badge_labels = []

        for i in range(3):
            card = tk.Frame(
                self.scrollable_frame,
                bg=self.card_bg,
                highlightbackground=self.card_border,
                highlightthickness=1,
                padx=8,
                pady=6
            )
            card.pack(fill=tk.X, pady=3)

            top_row = tk.Frame(card, bg=self.card_bg)
            top_row.pack(fill=tk.X)

            badge_lbl = tk.Label(
                top_row,
                text=f"REPLY #{i+1}",
                font=("Consolas", 8, "bold"),
                fg=self.accent_amber,
                bg="#1f2638",
                padx=6,
                pady=2
            )
            badge_lbl.pack(side=tk.LEFT, padx=(0, 6))

            en_lbl = tk.Label(
                card,
                text="Waiting for scan...",
                font=("Segoe UI", 9, "bold"),
                fg=self.accent_green,
                bg=self.card_bg,
                wraplength=280,
                justify=tk.LEFT,
                anchor="w"
            )
            en_lbl.pack(fill=tk.X, pady=(3, 1))

            id_lbl = tk.Label(
                card,
                text="ID: -",
                font=("Segoe UI", 8),
                fg=self.text_dim,
                bg=self.card_bg,
                wraplength=280,
                justify=tk.LEFT,
                anchor="w"
            )
            id_lbl.pack(fill=tk.X)

            self.reply_frames.append(card)
            self.reply_en_labels.append(en_lbl)
            self.reply_id_labels.append(id_lbl)
            self.reply_badge_labels.append(badge_lbl)

        # Initial shortcut hints update
        self.update_shortcut_hints()

    # --- MOUSE WHEEL & HOTKEY SCROLLING ---
    def _bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel, add="+")
        for child in widget.winfo_children():
            self._bind_mousewheel(child)

    def _on_mousewheel(self, event):
        if self.canvas:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def scroll_up(self):
        def _scroll():
            self.canvas.yview_scroll(-3, "units")
        self.root.after(0, _scroll)

    def scroll_down(self):
        def _scroll():
            self.canvas.yview_scroll(3, "units")
        self.root.after(0, _scroll)

    # --- DRAG TO MOVE ---
    def _start_drag(self, event):
        self._drag_start_x = event.x_root - self.window.winfo_x()
        self._drag_start_y = event.y_root - self.window.winfo_y()

    def _on_drag(self, event):
        new_x = event.x_root - self._drag_start_x
        new_y = event.y_root - self._drag_start_y
        self.pos_x = new_x
        self.pos_y = new_y
        self.window.geometry(f"+{new_x}+{new_y}")
        self._save_geometry()

    # --- 8-DIRECTIONAL FREEFORM BORDER & CORNER RESIZE ---
    def _init_8way_borders(self):
        B_THICK = 6
        C_SIZE = 12

        # 4 Edges
        self.b_top = tk.Frame(self.window, bg=self.card_border, cursor="size_ns")
        self.b_bottom = tk.Frame(self.window, bg=self.card_border, cursor="size_ns")
        self.b_left = tk.Frame(self.window, bg=self.card_border, cursor="size_we")
        self.b_right = tk.Frame(self.window, bg=self.card_border, cursor="size_we")

        # 4 Corners
        self.c_nw = tk.Frame(self.window, bg=self.card_border, cursor="size_nw_se")
        self.c_ne = tk.Frame(self.window, bg=self.card_border, cursor="size_ne_sw")
        self.c_sw = tk.Frame(self.window, bg=self.card_border, cursor="size_ne_sw")
        self.c_se = tk.Frame(self.window, bg=self.card_border, cursor="size_nw_se")

        # Relative Placements
        self.b_top.place(x=C_SIZE, y=0, relwidth=1.0, width=-(C_SIZE*2), height=B_THICK)
        self.b_bottom.place(x=C_SIZE, rely=1.0, y=-B_THICK, relwidth=1.0, width=-(C_SIZE*2), height=B_THICK)
        self.b_left.place(x=0, y=C_SIZE, width=B_THICK, relheight=1.0, height=-(C_SIZE*2))
        self.b_right.place(relx=1.0, x=-B_THICK, y=C_SIZE, width=B_THICK, relheight=1.0, height=-(C_SIZE*2))

        self.c_nw.place(x=0, y=0, width=C_SIZE, height=C_SIZE)
        self.c_ne.place(relx=1.0, x=-C_SIZE, y=0, width=C_SIZE, height=C_SIZE)
        self.c_sw.place(x=0, rely=1.0, y=-C_SIZE, width=C_SIZE, height=C_SIZE)
        self.c_se.place(relx=1.0, x=-C_SIZE, rely=1.0, y=-C_SIZE, width=C_SIZE, height=C_SIZE)

        # Bind all edges, corners, and grip to 8-way resize
        borders = [
            (self.b_top, "n"),
            (self.b_bottom, "s"),
            (self.b_left, "w"),
            (self.b_right, "e"),
            (self.c_nw, "nw"),
            (self.c_ne, "ne"),
            (self.c_sw, "sw"),
            (self.c_se, "se"),
            (self.grip, "se")
        ]

        for widget, direction in borders:
            widget.bind("<ButtonPress-1>", lambda e, d=direction: self._start_8way_resize(e, d))
            widget.bind("<B1-Motion>", self._on_8way_resize)
            widget.bind("<ButtonRelease-1>", self._end_8way_resize)

    def _start_8way_resize(self, event, direction):
        self._resize_dir = direction
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_win_x = self.window.winfo_x()
        self._resize_start_win_y = self.window.winfo_y()
        self._resize_start_w = self.window.winfo_width()
        self._resize_start_h = self.window.winfo_height()

    def _on_8way_resize(self, event):
        dx = event.x_root - self._resize_start_x
        dy = event.y_root - self._resize_start_y
        d = self._resize_dir

        w = self._resize_start_w
        h = self._resize_start_h
        x = self._resize_start_win_x
        y = self._resize_start_win_y

        MIN_W = 240
        MIN_H = 220

        if "e" in d:
            w = max(MIN_W, w + dx)
        if "w" in d:
            new_w = max(MIN_W, w - dx)
            x = x + (w - new_w)
            w = new_w
        if "s" in d:
            h = max(MIN_H, h + dy)
        if "n" in d:
            new_h = max(MIN_H, h - dy)
            y = y + (h - new_h)
            h = new_h

        self.window.geometry(f"{w}x{h}+{x}+{y}")
        self.width = w
        self.height = h
        self.pos_x = x
        self.pos_y = y

        # Adapt wrap length dynamically
        wrap_val = max(180, w - 45)
        for lbl in self.reply_en_labels + self.reply_id_labels + [self.ocr_src_lbl, self.ocr_trans_lbl, self.toast_lbl]:
            lbl.config(wraplength=wrap_val)

    def _end_8way_resize(self, event):
        self._save_geometry()

    def _save_geometry(self):
        osd_bbox = self.config.get("osd_bbox", {})
        osd_bbox["left"] = self.window.winfo_x()
        osd_bbox["top"] = self.window.winfo_y()
        osd_bbox["width"] = self.window.winfo_width()
        osd_bbox["height"] = self.window.winfo_height()
        self.config.set("osd_bbox", osd_bbox)

    # --- OPACITY ---
    def set_opacity(self, alpha_val):
        val = max(0.20, min(1.0, float(alpha_val)))
        self.window.attributes("-alpha", val)
        self.config.set("osd_alpha", round(val, 2))

    # --- SHORTCUT HINTS ---
    def update_shortcut_hints(self):
        def _update():
            hk = self.config.get("hotkeys", {})
            k_ocr = hk.get("hotkey_ocr", "f4").upper()
            k_f5 = hk.get("hotkey_clipboard", "f5").upper()
            k_hud = hk.get("hotkey_toggle_hud", "f6").upper()
            k_ans1 = hk.get("hotkey_ans1", "ctrl+1").upper()
            k_ans2 = hk.get("hotkey_ans2", "ctrl+2").upper()
            k_ans3 = hk.get("hotkey_ans3", "ctrl+3").upper()

            self.ocr_header.config(text=f"DETECTED CHAT • SCAN KEY: {k_ocr}")
            self.reply_header.config(text=f"AI REPLIES • {k_ans1} | {k_ans2} | {k_ans3}")

            keys = [k_ans1, k_ans2, k_ans3]
            for idx, badge in enumerate(self.reply_badge_labels):
                if idx < len(keys):
                    badge.config(text=f"OPTION {idx+1} • {keys[idx]}")

            self.toast_lbl.config(text=f"READY ({k_ocr}: Scan | {k_f5}: Replace | {k_hud}: Hide HUD)")
            self.footer_hint.config(text=f"HUD: {k_hud} | Scroll: {hk.get('hotkey_scroll_up','PgUp').upper()}/{hk.get('hotkey_scroll_down','PgDn').upper()}")
        self.root.after(0, _update)

    def update_profile(self, style, *args, **kwargs):
        def _update():
            tone = kwargs.get("tone")
            if not tone and args:
                if len(args) >= 2:
                    tone = args[1]
                elif len(args) == 1:
                    tone = args[0]
            if not tone:
                tone = self.config.get("emotion_tone", "Neutral")

            self.profile_badge.config(
                text=f"{str(style).upper()} • {str(tone).upper()}"
            )
        self.root.after(0, _update)

    def show_status_message(self, message, is_active=True):
        def _update():
            self.toast_lbl.config(text=message)
            if is_active:
                self.status_dot.config(text="● ACTIVE", fg=self.accent_green)
            else:
                self.status_dot.config(text="● STANDBY", fg=self.text_dim)
        self.root.after(0, _update)

    def prepare_for_new_scan(self):
        def _clear():
            self.status_dot.config(text="● SCANNING", fg=self.accent_amber)
            self.toast_lbl.config(text="MEMPROSES TEKS BARU...")
            for i in range(3):
                self.reply_en_labels[i].config(text="Membuat balasan baru...")
                self.reply_id_labels[i].config(text="Menyesuaikan konteks...")
                self.reply_frames[i].config(highlightbackground=self.card_border)
        self.root.after(0, _clear)

    def update_ocr_result(self, raw_ocr, translated_id, options_id=None, options_en=None):
        def _update():
            clean_src = raw_ocr.strip() if raw_ocr else "(Empty scan)"
            self.ocr_src_lbl.config(text=f"Raw: \"{clean_src}\"")
            
            clean_trans = translated_id.strip() if translated_id else "-"
            self.ocr_trans_lbl.config(text=f"Arti: {clean_trans}")

            opts_en = options_en or []
            opts_id = options_id or []

            for i in range(3):
                if i < len(opts_en) and opts_en[i].strip():
                    en_text = opts_en[i].strip()
                    id_text = opts_id[i].strip() if i < len(opts_id) else ""
                    self.reply_en_labels[i].config(text=en_text)
                    self.reply_id_labels[i].config(text=f"ID: {id_text}")
                    self.reply_frames[i].config(highlightbackground=self.accent_blue)
                else:
                    self.reply_en_labels[i].config(text="-")
                    self.reply_id_labels[i].config(text="ID: -")
                    self.reply_frames[i].config(highlightbackground=self.card_border)

            self.status_dot.config(text="● READY", fg=self.accent_blue)
            hk = self.config.get("hotkeys", {})
            self.toast_lbl.config(text=f"READY (Paste: {hk.get('hotkey_ans1','Ctrl+1').upper()}..)")

            # Auto-reset canvas scroll to top so player sees top reply first
            self.canvas.yview_moveto(0.0)
            self._bind_mousewheel(self.scrollable_frame)
        self.root.after(0, _update)

    def _force_bring_to_front(self):
        try:
            import ctypes
            user32 = ctypes.windll.user32
            hwnd = user32.GetParent(self.window.winfo_id()) or self.window.winfo_id()
            # HWND_TOPMOST = -1, SWP_NOMOVE = 0x0002, SWP_NOSIZE = 0x0001, SWP_SHOWWINDOW = 0x0040, SWP_NOACTIVATE = 0x0010
            user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040 | 0x0010)
        except Exception:
            pass

    def toggle_visibility(self):
        # Debounce to prevent rapid double-clicks or key repeats from desyncing toggle
        now = time.time()
        if now - getattr(self, "_last_toggle_time", 0) < 0.2:
            return
        self._last_toggle_time = now

        def _toggle():
            if not self.window or not self.window.winfo_exists():
                return

            current_state = self.window.state()
            is_shown = (current_state != "withdrawn") and getattr(self, "is_visible", True)

            if is_shown:
                self.is_visible = False
                self.window.withdraw()
                self.config.set("osd_enabled", False)
                if hasattr(self.root, "log_message"):
                    self.root.log_message("[HUD] Overlay disembunyikan.")
            else:
                self.is_visible = True
                self.window.deiconify()
                self.window.overrideredirect(True)
                self.window.attributes("-topmost", True)
                self.window.lift()
                self._force_bring_to_front()
                self.config.set("osd_enabled", True)
                if hasattr(self.root, "log_message"):
                    self.root.log_message("[HUD] Overlay ditampilkan.")

        self.root.after(0, _toggle)

    def set_visible(self, visible):
        self.is_visible = bool(visible)
        def _set():
            if not self.window or not self.window.winfo_exists():
                return
            if self.is_visible:
                self.window.deiconify()
                self.window.overrideredirect(True)
                self.window.attributes("-topmost", True)
                self.window.lift()
                self._force_bring_to_front()
            else:
                self.window.withdraw()
            self.config.set("osd_enabled", self.is_visible)
        self.root.after(0, _set)
