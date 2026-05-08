"""
HandBrake Config - Outil de calibration frein a main DIY
Lit l axe analogique depuis un Arduino Nano via port serie (115200 baud)
Sortie vers vJoy device 2 (axe Y) pour application en jeu
"""

import json
import threading
import time
import os
import serial
import serial.tools.list_ports
import customtkinter as ctk
from tkinter import messagebox

try:
    import pyvjoy
    VJOY_AVAILABLE = True
except Exception:
    VJOY_AVAILABLE = False

VJOY_DEVICE_ID = 2
VJOY_AXIS      = "wAxisY"

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")
DEFAULT_CONFIG = {
    "raw_min":       0,
    "raw_max":       1023,
    "deadzone_low":  0.03,
    "deadzone_high": 0.02,
    "curve":         "linear",
    "curve_expo":    2.0,
    "smooth_n":      8,
    "com_port":      "",
    "baud_rate":     115200,
    "vjoy_enabled":  True,
    "vjoy_device":   VJOY_DEVICE_ID,
    "vjoy_axis":     VJOY_AXIS,
}

# ── Traitement de l axe ────────────────────────────────────────────────────────
def apply_calibration(raw: int, raw_min: int, raw_max: int) -> float:
    span = raw_max - raw_min
    if span == 0:
        return 0.0
    return max(0.0, min(1.0, (raw - raw_min) / span))

def apply_deadzone(val: float, dz_low: float, dz_high: float) -> float:
    if val <= dz_low:
        return 0.0
    if val >= (1.0 - dz_high):
        return 1.0
    active = 1.0 - dz_low - dz_high
    return (val - dz_low) / active

def apply_curve(val: float, curve: str, expo: float) -> float:
    if curve == "expo":
        return val ** expo
    if curve == "scurve":
        return val * val * (3 - 2 * val)
    return val

def process_axis(raw: int, cfg: dict) -> float:
    val = apply_calibration(raw, cfg["raw_min"], cfg["raw_max"])
    val = apply_deadzone(val, cfg["deadzone_low"], cfg["deadzone_high"])
    val = apply_curve(val, cfg["curve"], cfg["curve_expo"])
    return val

# ── Application ────────────────────────────────────────────────────────────────
class HandbrakeApp(ctk.CTk):

    ACCENT  = "#E63946"
    ACCENT2 = "#457B9D"
    BG      = "#1A1A2E"
    BG2     = "#16213E"
    BG3     = "#0F3460"
    TEXT    = "#E0E0E0"

    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.cfg = self._load_config()
        self._raw_value    = 0
        self._output_value = 0.0
        self._calibrating  = False
        self._cal_min      = 1023
        self._cal_max      = 0
        self._running      = True
        self._vjoy         = None
        self._vjoy_error   = ""
        self._serial: serial.Serial | None = None
        self._smooth_buf: list[int] = []
        self._init_vjoy()

        self.title("HandBrake Config")
        self.geometry("520x860")
        self.resizable(False, False)
        self.configure(fg_color=self.BG)

        self._build_ui()
        self._refresh_ui_from_config()

        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── vJoy ──────────────────────────────────────────────────────────────────
    def _init_vjoy(self):
        if not VJOY_AVAILABLE:
            self._vjoy_error = "pyvjoy non installe"
            return
        if not self.cfg.get("vjoy_enabled", True):
            return

        sdk    = pyvjoy._sdk
        dev_id = self.cfg["vjoy_device"]

        if not sdk.vJoyEnabled():
            self._vjoy_error = "Driver vJoy non actif"
            return

        stat = sdk.GetVJDStatus(dev_id)
        if stat == pyvjoy.VJD_STAT_BUSY:
            sdk.RelinquishVJD(dev_id)
            time.sleep(0.1)
            stat = sdk.GetVJDStatus(dev_id)

        if stat == pyvjoy.VJD_STAT_MISS:
            self._vjoy_error = f"Device {dev_id} non configure dans vJoy"
            return

        try:
            self._vjoy = pyvjoy.VJoyDevice(dev_id)
            self._vjoy_error = ""
        except Exception as e:
            self._vjoy = None
            self._vjoy_error = str(e)

    def _send_vjoy(self, value_0_1: float):
        if self._vjoy is None:
            return
        raw_vjoy = int(1 + value_0_1 * 32766)
        try:
            setattr(self._vjoy.data, self.cfg["vjoy_axis"], raw_vjoy)
            self._vjoy.update()
        except Exception:
            pass

    # ── Serial ────────────────────────────────────────────────────────────────
    def _list_ports(self):
        return [p.device for p in serial.tools.list_ports.comports()]

    def _connect_serial(self):
        port = self._port_var.get()
        if not port:
            messagebox.showerror("Erreur", "Selectionne un port COM")
            return
        try:
            if self._serial and self._serial.is_open:
                self._serial.close()
            self._serial = serial.Serial(port, self.cfg["baud_rate"], timeout=0.1)
            self.cfg["com_port"] = port
            self._lbl_serial_status.configure(
                text=f"Connecte : {port}", text_color="#4CAF50"
            )
            self._btn_connect.configure(text="Deconnecter", fg_color=self.ACCENT)
        except serial.SerialException as e:
            self._lbl_serial_status.configure(
                text=f"Erreur : {e}", text_color=self.ACCENT
            )

    def _disconnect_serial(self):
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self._lbl_serial_status.configure(
            text="Deconnecte", text_color="#888888"
        )
        self._btn_connect.configure(text="Connecter", fg_color=self.BG3)

    def _toggle_serial(self):
        if self._serial and self._serial.is_open:
            self._disconnect_serial()
        else:
            self._connect_serial()

    def _refresh_ports(self):
        ports = self._list_ports()
        self._port_combo.configure(values=ports if ports else [""])
        if ports:
            self._port_var.set(ports[0])

    # ── Config ────────────────────────────────────────────────────────────────
    def _load_config(self) -> dict:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except Exception:
                pass
        return dict(DEFAULT_CONFIG)

    def _save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.cfg, f, indent=2)
        messagebox.showinfo("Sauvegarde", "Configuration sauvegardee !")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        title_frame = ctk.CTkFrame(self, fg_color=self.BG3, corner_radius=0)
        title_frame.pack(fill="x")
        ctk.CTkLabel(
            title_frame, text="HANDBRAKE CONFIG",
            font=ctk.CTkFont("Courier New", 22, "bold"),
            text_color=self.ACCENT
        ).pack(pady=14)
        ctk.CTkLabel(
            title_frame, text="Frein a main DIY - Arduino Nano",
            font=ctk.CTkFont(size=11), text_color="#888888"
        ).pack(pady=(0, 4))

        if not VJOY_AVAILABLE:
            vjoy_text, vjoy_color = "vJoy : non disponible (pyvjoy manquant)", "#E63946"
        elif self._vjoy is not None:
            vjoy_text  = f"vJoy device {self.cfg['vjoy_device']} - axe {self.cfg['vjoy_axis']}  [ACTIF]"
            vjoy_color = "#4CAF50"
        else:
            vjoy_text  = f"vJoy : erreur - {self._vjoy_error}"
            vjoy_color = "#F4A261"

        ctk.CTkLabel(
            title_frame, text=vjoy_text,
            font=ctk.CTkFont("Courier New", 10),
            text_color=vjoy_color
        ).pack(pady=(0, 10))

        self._build_section("CONNEXION SERIE",      self._build_serial)
        self._build_section("APERCU EN TEMPS REEL", self._build_preview)
        self._build_section("FILTRAGE",             self._build_smooth)
        self._build_section("CALIBRATION",          self._build_calibration)
        self._build_section("ZONE MORTE",          self._build_deadzone)
        self._build_section("COURBE DE REPONSE",   self._build_curve)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=12)
        ctk.CTkButton(
            btn_frame, text="Sauvegarder",
            fg_color=self.ACCENT, hover_color="#C1121F",
            font=ctk.CTkFont("Courier New", 13, "bold"),
            command=self._save_config, height=40
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))
        ctk.CTkButton(
            btn_frame, text="Reinitialiser",
            fg_color=self.BG3, hover_color="#1A3A6A",
            font=ctk.CTkFont("Courier New", 13),
            command=self._reset_config, height=40
        ).pack(side="right", expand=True, fill="x", padx=(6, 0))

    def _build_section(self, title: str, builder_fn):
        frame = ctk.CTkFrame(self, fg_color=self.BG2, corner_radius=8)
        frame.pack(fill="x", padx=12, pady=6)
        ctk.CTkLabel(
            frame, text=title,
            font=ctk.CTkFont("Courier New", 12, "bold"),
            text_color=self.ACCENT2
        ).pack(anchor="w", padx=12, pady=(10, 4))
        builder_fn(frame)

    def _build_serial(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=4)

        self._port_var = ctk.StringVar(value=self.cfg.get("com_port", ""))
        ports = self._list_ports()
        self._port_combo = ctk.CTkComboBox(
            row, values=ports if ports else [""],
            variable=self._port_var,
            font=ctk.CTkFont("Courier New", 11), width=120
        )
        self._port_combo.pack(side="left")

        ctk.CTkButton(
            row, text="Rafraichir", width=90,
            font=ctk.CTkFont(size=11), fg_color=self.BG3,
            command=self._refresh_ports
        ).pack(side="left", padx=(8, 0))

        self._btn_connect = ctk.CTkButton(
            row, text="Connecter", width=100,
            fg_color=self.BG3, hover_color="#1A3A6A",
            font=ctk.CTkFont("Courier New", 12, "bold"),
            command=self._toggle_serial
        )
        self._btn_connect.pack(side="left", padx=(8, 0))

        self._lbl_serial_status = ctk.CTkLabel(
            inner, text="Deconnecte",
            font=ctk.CTkFont("Courier New", 10), text_color="#888888"
        )
        self._lbl_serial_status.pack(anchor="w", pady=(6, 0))

    def _build_preview(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        ctk.CTkLabel(inner, text="Brut (raw):", font=ctk.CTkFont(size=11),
                     text_color="#888").grid(row=0, column=0, sticky="w", pady=2)
        self._bar_raw = ctk.CTkProgressBar(inner, height=18, corner_radius=4,
                                            progress_color="#555")
        self._bar_raw.grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=2)
        self._lbl_raw = ctk.CTkLabel(inner, text="---", width=80,
                                      font=ctk.CTkFont("Courier New", 11))
        self._lbl_raw.grid(row=0, column=2, padx=(8, 0))

        ctk.CTkLabel(inner, text="Sortie:", font=ctk.CTkFont(size=11),
                     text_color="#888").grid(row=1, column=0, sticky="w", pady=2)
        self._bar_out = ctk.CTkProgressBar(inner, height=18, corner_radius=4,
                                            progress_color=self.ACCENT)
        self._bar_out.grid(row=1, column=1, sticky="ew", padx=(8, 0), pady=2)
        self._lbl_out = ctk.CTkLabel(inner, text="---", width=80,
                                      font=ctk.CTkFont("Courier New", 11))
        self._lbl_out.grid(row=1, column=2, padx=(8, 0))

        inner.grid_columnconfigure(1, weight=1)

    def _build_calibration(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x", pady=4)
        ctk.CTkLabel(row, text="Min raw:", width=70,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self._entry_min = ctk.CTkEntry(row, width=90,
                                        font=ctk.CTkFont("Courier New", 11))
        self._entry_min.pack(side="left", padx=(4, 16))
        ctk.CTkLabel(row, text="Max raw:", width=70,
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self._entry_max = ctk.CTkEntry(row, width=90,
                                        font=ctk.CTkFont("Courier New", 11))
        self._entry_max.pack(side="left", padx=4)
        ctk.CTkButton(row, text="Appliquer", width=90,
                       font=ctk.CTkFont(size=11),
                       command=self._apply_manual_cal).pack(side="left", padx=(12, 0))

        cal_row = ctk.CTkFrame(inner, fg_color="transparent")
        cal_row.pack(fill="x", pady=4)
        self._btn_cal = ctk.CTkButton(
            cal_row, text="Demarrer calibration auto",
            fg_color=self.BG3, hover_color="#1A3A6A",
            font=ctk.CTkFont("Courier New", 12),
            command=self._toggle_calibration, height=36
        )
        self._btn_cal.pack(side="left", fill="x", expand=True)
        self._lbl_cal = ctk.CTkLabel(
            cal_row, text="Tire / relache le frein pour detecter min/max",
            font=ctk.CTkFont(size=10), text_color="#666", wraplength=200
        )
        self._lbl_cal.pack(side="left", padx=(10, 0))

    def _build_smooth(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        self._smooth_var = ctk.IntVar(value=self.cfg.get("smooth_n", 8))
        self._lbl_smooth = ctk.CTkLabel(
            inner,
            text=f"Moyenne glissante : {self.cfg.get('smooth_n', 8)} samples  (1 = brut, 32 = très lissé)",
            font=ctk.CTkFont(size=11)
        )
        self._lbl_smooth.pack(anchor="w", pady=(4, 0))
        ctk.CTkSlider(
            inner, from_=1, to=32, number_of_steps=31,
            variable=self._smooth_var,
            command=self._on_smooth_change
        ).pack(fill="x", pady=(2, 6))

    def _build_deadzone(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        self._dz_low_var = ctk.DoubleVar(value=self.cfg["deadzone_low"] * 100)
        self._lbl_dz_low = ctk.CTkLabel(inner,
            text=f"Bas (relache) : {self.cfg['deadzone_low']*100:.1f}%",
            font=ctk.CTkFont(size=11))
        self._lbl_dz_low.pack(anchor="w", pady=(4, 0))
        ctk.CTkSlider(inner, from_=0, to=20, variable=self._dz_low_var,
                       command=self._on_dz_low).pack(fill="x", pady=(2, 6))

        self._dz_high_var = ctk.DoubleVar(value=self.cfg["deadzone_high"] * 100)
        self._lbl_dz_high = ctk.CTkLabel(inner,
            text=f"Haut (enfonce) : {self.cfg['deadzone_high']*100:.1f}%",
            font=ctk.CTkFont(size=11))
        self._lbl_dz_high.pack(anchor="w", pady=(4, 0))
        ctk.CTkSlider(inner, from_=0, to=20, variable=self._dz_high_var,
                       command=self._on_dz_high).pack(fill="x", pady=(2, 6))

    def _build_curve(self, parent):
        inner = ctk.CTkFrame(parent, fg_color="transparent")
        inner.pack(fill="x", padx=12, pady=(0, 12))

        self._curve_var = ctk.StringVar(value=self.cfg["curve"])
        curves = [("Lineaire", "linear"), ("Exponentielle", "expo"), ("S-Curve", "scurve")]
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(fill="x")
        for label, value in curves:
            ctk.CTkRadioButton(
                row, text=label, variable=self._curve_var, value=value,
                font=ctk.CTkFont(size=11),
                command=self._on_curve_change
            ).pack(side="left", padx=12, pady=6)

        self._expo_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._expo_frame.pack(fill="x")
        ctk.CTkLabel(self._expo_frame, text="Exposant :",
                     font=ctk.CTkFont(size=11)).pack(side="left")
        self._expo_var = ctk.DoubleVar(value=self.cfg["curve_expo"])
        self._lbl_expo = ctk.CTkLabel(self._expo_frame,
            text=f"{self.cfg['curve_expo']:.1f}",
            font=ctk.CTkFont("Courier New", 11), width=35)
        self._lbl_expo.pack(side="right")
        ctk.CTkSlider(self._expo_frame, from_=1.0, to=4.0,
                       variable=self._expo_var,
                       command=self._on_expo_change).pack(
                           side="left", fill="x", expand=True, padx=(8, 4))

    # ── Callbacks ─────────────────────────────────────────────────────────────
    def _refresh_ui_from_config(self):
        self._entry_min.delete(0, "end")
        self._entry_min.insert(0, str(self.cfg["raw_min"]))
        self._entry_max.delete(0, "end")
        self._entry_max.insert(0, str(self.cfg["raw_max"]))
        self._smooth_var.set(self.cfg.get("smooth_n", 8))
        self._lbl_smooth.configure(
            text=f"Moyenne glissante : {self.cfg.get('smooth_n', 8)} samples  (1 = brut, 32 = très lissé)"
        )
        self._dz_low_var.set(self.cfg["deadzone_low"] * 100)
        self._dz_high_var.set(self.cfg["deadzone_high"] * 100)
        self._curve_var.set(self.cfg["curve"])
        self._expo_var.set(self.cfg["curve_expo"])
        self._on_curve_change()
        if self.cfg.get("com_port"):
            self._port_var.set(self.cfg["com_port"])

    def _apply_manual_cal(self):
        try:
            vmin = int(self._entry_min.get())
            vmax = int(self._entry_max.get())
            assert 0 <= vmin < vmax <= 1023
            self.cfg["raw_min"] = vmin
            self.cfg["raw_max"] = vmax
        except Exception:
            messagebox.showerror("Erreur", "Valeurs invalides (0-1023, min < max)")

    def _toggle_calibration(self):
        if not self._calibrating:
            self._calibrating = True
            self._cal_min = 1023
            self._cal_max = 0
            self._btn_cal.configure(
                text="Arreter calibration",
                fg_color=self.ACCENT, hover_color="#C1121F"
            )
        else:
            self._calibrating = False
            self._btn_cal.configure(
                text="Demarrer calibration auto",
                fg_color=self.BG3, hover_color="#1A3A6A"
            )
            if self._cal_max > self._cal_min:
                self.cfg["raw_min"] = self._cal_min
                self.cfg["raw_max"] = self._cal_max
                self._entry_min.delete(0, "end")
                self._entry_min.insert(0, str(self._cal_min))
                self._entry_max.delete(0, "end")
                self._entry_max.insert(0, str(self._cal_max))
                self._lbl_cal.configure(
                    text=f"Calibre : {self._cal_min} -> {self._cal_max}",
                    text_color="#4CAF50"
                )

    def _on_smooth_change(self, val):
        n = max(1, round(float(val)))
        self.cfg["smooth_n"] = n
        self._smooth_buf.clear()
        self._lbl_smooth.configure(
            text=f"Moyenne glissante : {n} samples  (1 = brut, 32 = très lissé)"
        )

    def _on_dz_low(self, val):
        self.cfg["deadzone_low"] = float(val) / 100
        self._lbl_dz_low.configure(text=f"Bas (relache) : {float(val):.1f}%")

    def _on_dz_high(self, val):
        self.cfg["deadzone_high"] = float(val) / 100
        self._lbl_dz_high.configure(text=f"Haut (enfonce) : {float(val):.1f}%")

    def _on_curve_change(self):
        self.cfg["curve"] = self._curve_var.get()
        if self.cfg["curve"] == "expo":
            self._expo_frame.pack(fill="x")
        else:
            self._expo_frame.pack_forget()

    def _on_expo_change(self, val):
        self.cfg["curve_expo"] = float(val)
        self._lbl_expo.configure(text=f"{float(val):.1f}")

    def _reset_config(self):
        if messagebox.askyesno("Reinitialiser", "Remettre tous les parametres par defaut ?"):
            self.cfg = dict(DEFAULT_CONFIG)
            self._refresh_ui_from_config()

    # ── Boucle de lecture serie ───────────────────────────────────────────────
    def _smooth(self, raw: int) -> int:
        n = max(1, int(self.cfg.get("smooth_n", 8)))
        self._smooth_buf.append(raw)
        if len(self._smooth_buf) > n:
            self._smooth_buf.pop(0)
        return round(sum(self._smooth_buf) / len(self._smooth_buf))

    def _read_loop(self):
        while self._running:
            if self._serial and self._serial.is_open:
                try:
                    line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                    if line:
                        raw = int(line)
                        smoothed = self._smooth(raw)
                        self._raw_value = smoothed
                        if self._calibrating:
                            self._cal_min = min(self._cal_min, smoothed)
                            self._cal_max = max(self._cal_max, smoothed)
                        self._output_value = process_axis(smoothed, self.cfg)
                        self._send_vjoy(self._output_value)
                        self.after(0, self._update_preview)
                except (ValueError, serial.SerialException):
                    pass
                time.sleep(0.01)  # ~100 Hz max, évite d'inonder l'UI
            else:
                time.sleep(0.04)

    def _update_preview(self):
        raw  = self._raw_value
        out  = self._output_value
        span = self.cfg["raw_max"] - self.cfg["raw_min"]
        raw_pct = (raw - self.cfg["raw_min"]) / span if span else 0
        raw_pct = max(0.0, min(1.0, raw_pct))

        self._bar_raw.set(raw_pct)
        self._bar_out.set(out)
        self._lbl_raw.configure(text=f"{raw_pct*100:5.1f}%  ({raw})")
        self._lbl_out.configure(text=f"{out*100:5.1f}%")

        if out > 0.8:
            color = self.ACCENT
        elif out > 0.4:
            color = "#F4A261"
        else:
            color = "#2A9D8F"
        self._bar_out.configure(progress_color=color)

    def _on_close(self):
        self._running = False
        if self._serial and self._serial.is_open:
            self._serial.close()
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = HandbrakeApp()
    app.mainloop()
