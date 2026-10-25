import tkinter as tk
import ctypes

# Ensure Per-Monitor DPI Awareness so screen geometry accurately reflects true hardware pixels
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class RoiPicker:
    def __init__(self, parent_root, on_bbox_selected):
        self.parent = parent_root
        self.callback = on_bbox_selected
        
        # Query true virtual screen across all monitors to prevent DPI scaling cutoff
        user32 = ctypes.windll.user32
        try:
            vsx = user32.GetSystemMetrics(76) # SM_XVIRTUALSCREEN
            vsy = user32.GetSystemMetrics(77) # SM_YVIRTUALSCREEN
            vsw = user32.GetSystemMetrics(78) # SM_CXVIRTUALSCREEN
            vsh = user32.GetSystemMetrics(79) # SM_CYVIRTUALSCREEN
            if vsw <= 0 or vsh <= 0:
                vsx, vsy = 0, 0
                vsw = user32.GetSystemMetrics(0)
                vsh = user32.GetSystemMetrics(1)
        except Exception:
            vsx, vsy = 0, 0
            vsw = self.parent.winfo_screenwidth()
            vsh = self.parent.winfo_screenheight()

        self.vsx = vsx
        self.vsy = vsy
        self.vsw = vsw
        self.vsh = vsh

        self.top = tk.Toplevel(self.parent)
        self.top.overrideredirect(True)
        self.top.geometry(f"{vsw}x{vsh}+{vsx}+{vsy}")
        self.top.attributes("-alpha", 0.38)
        self.top.attributes("-topmost", True)
        self.top.config(cursor="cross")

        # Win32 API SetWindowPos to guarantee HWND covers the entire virtual desktop
        try:
            self.top.update_idletasks()
            hwnd = self.top.winfo_id()
            user32.SetWindowPos(hwnd, -1, vsx, vsy, vsw, vsh, 0x0040) # SWP_SHOWWINDOW
        except Exception:
            pass

        # Canvas across full virtual screen
        self.canvas = tk.Canvas(self.top, cursor="cross", bg="#0a0e17", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.start_canvas_x = None
        self.start_canvas_y = None
        self.start_screen_x = None
        self.start_screen_y = None
        self.rect = None
        self.dim_text = None

        # Bindings for mouse selection
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # Right-click cancels immediately
        self.canvas.bind("<ButtonPress-3>", lambda e: self.cancel())
        self.top.bind("<ButtonPress-3>", lambda e: self.cancel())

        # Bind Escape key to both window and canvas
        self.top.bind("<Escape>", lambda e: self.cancel())
        self.canvas.bind("<Escape>", lambda e: self.cancel())
        self.top.bind_all("<Escape>", lambda e: self.cancel())

        # Global hook for Escape key so it works even if focus is lost
        self._esc_hook = None
        try:
            import keyboard
            self._esc_hook = keyboard.on_press_key("esc", lambda e: self.parent.after(0, self.cancel))
        except Exception:
            pass

        # Grab focus so keyboard events (ESC) are captured 100% of the time!
        self.top.after(50, self._force_focus)

        # Top Control Banner (Cancel button + instructions)
        bar_w = 480
        bar_h = 44
        bar_x = self.vsx + (self.vsw - bar_w) // 2
        bar_y = max(20, self.vsy + 20)

        self.banner = tk.Frame(self.top, bg="#111827", highlightbackground="#00d4ff", highlightthickness=1)
        self.banner.place(x=bar_x, y=bar_y, width=bar_w, height=bar_h)
        self.banner.lift()

        info_lbl = tk.Label(
            self.banner,
            text="DRAG BOX OVER CHAT AREA",
            font=("Consolas", 10, "bold"),
            fg="#00d4ff",
            bg="#111827"
        )
        info_lbl.pack(side=tk.LEFT, padx=12, pady=8)

        cancel_btn = tk.Button(
            self.banner,
            text="[CANCEL (ESC)]",
            font=("Consolas", 9, "bold"),
            fg="#f87171",
            bg="#1f2937",
            activebackground="#374151",
            activeforeground="#ef4444",
            relief=tk.FLAT,
            padx=10,
            command=self.cancel
        )
        cancel_btn.pack(side=tk.RIGHT, padx=10, pady=6)
        cancel_btn.lift()

    def _force_focus(self):
        try:
            self.top.lift()
            self.top.focus_force()
            self.canvas.focus_set()
        except Exception:
            pass

    def cancel(self):
        if hasattr(self, '_esc_hook') and self._esc_hook is not None:
            try:
                import keyboard
                keyboard.unhook(self._esc_hook)
            except Exception:
                pass
            self._esc_hook = None
        try:
            self.top.destroy()
        except Exception:
            pass

    def _on_press(self, event):
        self.start_canvas_x = event.x
        self.start_canvas_y = event.y
        self.start_screen_x = self.vsx + event.x
        self.start_screen_y = self.vsy + event.y

        if self.rect:
            self.canvas.delete(self.rect)
        if self.dim_text:
            self.canvas.delete(self.dim_text)

        # Clear fill so underlying FiveM chat text is 100% visible while selecting!
        self.rect = self.canvas.create_rectangle(
            self.start_canvas_x, self.start_canvas_y, self.start_canvas_x, self.start_canvas_y,
            outline="#00ff9d",
            width=2
        )
        self.dim_text = self.canvas.create_text(
            self.start_canvas_x, self.start_canvas_y + 15,
            text="0 x 0 px",
            fill="#00ff9d",
            font=("Consolas", 9, "bold"),
            anchor="nw"
        )

    def _on_drag(self, event):
        cur_cx, cur_cy = event.x, event.y
        self.canvas.coords(self.rect, self.start_canvas_x, self.start_canvas_y, cur_cx, cur_cy)
        
        # Live dimension badge
        w = abs(cur_cx - self.start_canvas_x)
        h = abs(cur_cy - self.start_canvas_y)
        tx = min(self.vsw - 90, max(cur_cx, self.start_canvas_x) + 4)
        ty = min(self.vsh - 25, max(cur_cy, self.start_canvas_y) + 4)
        if self.dim_text:
            self.canvas.coords(self.dim_text, tx, ty)
            self.canvas.itemconfig(self.dim_text, text=f"{w}x{h} px")

    def _on_release(self, event):
        end_screen_x = self.vsx + event.x
        end_screen_y = self.vsy + event.y

        left = min(self.start_screen_x, end_screen_x)
        top = min(self.start_screen_y, end_screen_y)
        width = abs(end_screen_x - self.start_screen_x)
        height = abs(end_screen_y - self.start_screen_y)

        self.cancel()
        if width > 15 and height > 15:
            bbox = {
                "left": int(left),
                "top": int(top),
                "width": int(width),
                "height": int(height)
            }
            if self.callback:
                self.callback(bbox)
