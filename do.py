# pixel_watch_hotkeys.py
# pip install mss keyboard pyautogui
# Windows/macOS/Linux. Ctrl+C to exit.

import os, json, time, threading
from typing import Tuple, Dict, Any
import mss
import keyboard
import pyautogui
import time

# ====== SETTINGS ======
SET_DIR = r"C:\ba\setting"
SET_FILE = os.path.join(SET_DIR, "settings.json")

BLACK_TOL = 20             # channel must be <= this to count as "black"
CONSEC_MATCHES = 2         # consecutive confirms before firing (for stability)
LOG_EVERY_SEC = 60
MONITOR_DELAY = 1.0        # seconds between checks

COOLDOWN_COMBINED_S = 3.0  # cooldown for the combined trigger
# ======================

# --- Global monitoring state ---
monitoring_enabled = True

# --- Tail sequence: esc → 3 → home → enter → (3 → enter) x2 ---
def _tail_sequence():
    keyboard.send("esc")
    time.sleep(0.050)
    keyboard.send("3")         # use "num 3" if you want Numpad3 instead
    time.sleep(0.050)
    keyboard.send("home")
    time.sleep(0.050)
    keyboard.send("enter")
    time.sleep(0.080)
    for _ in range(2):         # repeat 3 -> enter two times
        keyboard.send("3")
        time.sleep(0.080)
        keyboard.send("enter")
        time.sleep(0.080)

# --- Actions (run when BOTH rule1 & rule2 pixels are black) ---
def do_actions():
    # Rule1 sequence: 300ms -> "2" -> 100ms -> "2" -> 300ms -> Numpad0 -> tail
    time.sleep(0.300); keyboard.send("2")
    time.sleep(0.100); keyboard.send("2")
    time.sleep(0.300); keyboard.send("num 0")
    _tail_sequence()
    # Rule2 sequence: 300ms -> Numpad0 -> 100ms -> Numpad0 -> 300ms -> tail
    time.sleep(0.300); keyboard.send("num 0")
    time.sleep(0.100); keyboard.send("num 0")
    time.sleep(0.300); _tail_sequence()

state: Dict[str, Any] = {
    "coord": None,         # (x, y) for rule 1
    "coord2": None,        # (x, y) for rule 2
    "last_trigger_combined": 0.0,
    "streak_combined": 0,
}

def ensure_dir():
    os.makedirs(SET_DIR, exist_ok=True)

def load_settings():
    if not os.path.isfile(SET_FILE):
        return
    try:
        with open(SET_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data.get("coord"), list) and len(data["coord"]) == 2:
            state["coord"] = tuple(map(int, data["coord"]))
        if isinstance(data.get("coord2"), list) and len(data["coord2"]) == 2:
            state["coord2"] = tuple(map(int, data["coord2"]))
    except Exception as e:
        print(f"[Load] Failed: {e!r}")

def save_settings():
    ensure_dir()
    try:
        data = {
            "coord":  list(state["coord"])  if state["coord"]  else None,
            "coord2": list(state["coord2"]) if state["coord2"] else None,
        }
        with open(SET_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[Saved] {SET_FILE} -> {data}")
    except Exception as e:
        print(f"[Save] Failed: {e!r}")

def get_mouse_xy() -> Tuple[int, int]:
    x, y = pyautogui.position()
    return int(x), int(y)

def read_pixel_rgb(sct: mss.mss, x: int, y: int) -> Tuple[int, int, int]:
    bbox = {"top": y, "left": x, "width": 1, "height": 1}
    shot = sct.grab(bbox)
    r, g, b = shot.rgb[0], shot.rgb[1], shot.rgb[2]
    return (r, g, b)

def is_black(rgb: Tuple[int,int,int], tol: int = BLACK_TOL) -> bool:
    r, g, b = rgb
    return (r <= tol) and (g <= tol) and (b <= tol)

# ---- Hotkeys ----
def hotkey_set_coord_rule1():
    x, y = get_mouse_xy()
    state["coord"] = (x, y)
    print(f"[Set R1] Coord = {state['coord']}")
    save_settings()

def hotkey_set_coord_rule2():
    x, y = get_mouse_xy()
    state["coord2"] = (x, y)
    print(f"[Set R2] Coord = {state['coord2']}")
    save_settings()

def toggle_monitoring():
    global monitoring_enabled
    monitoring_enabled = not monitoring_enabled
    print(f"[Toggle] Monitoring {'ENABLED' if monitoring_enabled else 'PAUSED'}")

def register_hotkeys():
    keyboard.add_hotkey("shift+v", hotkey_set_coord_rule1, suppress=False)  # set coord for rule1
    keyboard.add_hotkey("shift+n", hotkey_set_coord_rule2, suppress=False)  # set coord for rule2
    keyboard.add_hotkey("shift+p", toggle_monitoring,   suppress=False)     # start/pause
    print("[Hotkeys] R1: Shift+V=coord | R2: Shift+N=coord | Shift+P=start/pause")

# ---- Monitor ----
def monitor_loop():
    last_log = 0.0
    print("[Monitor] Started")
    time.sleep(0.3)
    with mss.mss() as sct:
        while True:
            t0 = time.time()

            if not monitoring_enabled:
                time.sleep(0.2)
                continue

            if not (state["coord"] and state["coord2"]):
                if t0 - last_log >= 3:
                    last_log = t0
                    print("[Warn] Set R1 coord (Shift+V) and R2 coord (Shift+N).")
                time.sleep(0.25)
                continue

            try:
                (x1, y1) = state["coord"]
                (x2, y2) = state["coord2"]

                obs1 = read_pixel_rgb(sct, x1, y1)
                obs2 = read_pixel_rgb(sct, x2, y2)

                # Combined condition: BOTH are black
                if is_black(obs1) and is_black(obs2):
                    state["streak_combined"] += 1
                    if state["streak_combined"] >= CONSEC_MATCHES:
                        now = time.time()
                        if now - state["last_trigger_combined"] >= COOLDOWN_COMBINED_S:
                            threading.Thread(target=do_actions, daemon=True).start()
                            state["last_trigger_combined"] = now
                            state["streak_combined"] = 0
                else:
                    state["streak_combined"] = 0

                if t0 - last_log >= LOG_EVERY_SEC:
                    last_log = t0
                    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] alive; "
                          f"R1={state['coord']} R2={state['coord2']} tol={BLACK_TOL}")

            except Exception as e:
                print(f"[Monitor] Error: {e!r}. Recovering…")
                time.sleep(0.5)

            time.sleep(MONITOR_DELAY)

if __name__ == "__main__":
    ensure_dir()
    load_settings()
    print("[Init] Settings:", {
        "coord": state["coord"],
        "coord2": state["coord2"],
        "black_tol": BLACK_TOL
    })
    register_hotkeys()
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n[Exit] Bye")
