# -*- coding: utf-8 -*-
import time, threading
from threading import Lock
import keyboard
import win32gui, win32con, win32api

paused = False
pause_lock = Lock()
def toggle_pause():
    global paused
    with pause_lock:
        paused = not paused
        print(f"[MASTER] {'PAUSED' if paused else 'RESUMED'}")
keyboard.add_hotkey('-', toggle_pause, suppress=False)
def is_paused():
    with pause_lock:
        return paused

target_s = None
target_h = None
def _lock(tag):
    hwnd = win32gui.GetForegroundWindow()
    if hwnd and win32gui.IsWindow(hwnd):
        print(f"[Locked {tag}] {win32gui.GetWindowText(hwnd)} ({hwnd})")
        return hwnd
    return None
def set_target_s():
    global target_s
    target_s = _lock('S')
def set_target_h():
    global target_h
    target_h = _lock('H')
def _is_valid(hwnd):
    return bool(hwnd) and win32gui.IsWindow(hwnd)
def _fg_is_target_h():
    return _is_valid(target_h) and win32gui.GetForegroundWindow() == target_h

def _lparam(vk, is_down, extended=False):
    sc = win32api.MapVirtualKey(vk, 0)
    lp = 1 | (sc << 16)
    if extended: lp |= 0x01000000
    if not is_down: lp |= 0xC0000000
    return lp
def post_vk_to(hwnd, vk, is_down, extended=False):
    if not _is_valid(hwnd): return False
    msg = win32con.WM_KEYDOWN if is_down else win32con.WM_KEYUP
    win32api.PostMessage(hwnd, msg, vk, _lparam(vk, is_down, extended))
    return True
def tap_vk_to(hwnd, vk, extended=False, sleep=0.03):
    if not _is_valid(hwnd): return False
    post_vk_to(hwnd, vk, True, extended)
    time.sleep(sleep)
    post_vk_to(hwnd, vk, False, extended)
    return True

VK = {
    'UP': win32con.VK_UP,
    'DOWN': win32con.VK_DOWN,
    'LEFT': win32con.VK_LEFT,
    'RIGHT': win32con.VK_RIGHT,
    'SPACE': win32con.VK_SPACE,
    'DECIMAL': win32con.VK_DECIMAL,
    'NUMPAD0': win32con.VK_NUMPAD0,
    'NUMPAD3': win32con.VK_NUMPAD3,
    'A': ord('A'),
    '1': ord('1'),
    '2': ord('2'),
    '3': ord('3'),
    '9': ord('9'),
    ',': 0xBC
}

injecting = set()
inj_lock = Lock()
def _inj_add(name):
    with inj_lock: injecting.add(name)
def _inj_del(name):
    with inj_lock: injecting.discard(name)
def is_injected(name):
    with inj_lock: return name in injecting
def reinject_local(name, event_type):
    if not name or is_injected(name): return
    _inj_add(name)
    try:
        if event_type == 'down': keyboard.press(name)
        else: keyboard.release(name)
    finally:
        time.sleep(0.005)
        _inj_del(name)

ARROW_VK = {'up':VK['UP'],'down':VK['DOWN'],'left':VK['LEFT'],'right':VK['RIGHT']}
def _send_arrow_to_both(vk, is_down):
    sent_any = False
    if post_vk_to(target_h, vk, is_down, extended=True): sent_any = True
    if post_vk_to(target_s, vk, is_down, extended=True): sent_any = True
    return sent_any
def make_arrow_press(name):
    vk = ARROW_VK[name]
    def h(e):
        if is_paused(): reinject_local(name,'down'); return
        if getattr(e,"is_keypad",False):
            if not post_vk_to(target_s, vk, True, extended=True):
                reinject_local(name,'down')
        else:
            if not _send_arrow_to_both(vk, True):
                reinject_local(name,'down')
    return h
def make_arrow_release(name):
    vk = ARROW_VK[name]
    def h(e):
        if is_paused(): reinject_local(name,'up'); return
        if getattr(e,"is_keypad",False):
            if not post_vk_to(target_s, vk, False, extended=True):
                reinject_local(name,'up')
        else:
            if not _send_arrow_to_both(vk, False):
                reinject_local(name,'up')
    return h
for n in ARROW_VK:
    keyboard.on_press_key(n, make_arrow_press(n), suppress=True)
    keyboard.on_release_key(n, make_arrow_release(n), suppress=True)

NUMPAD_SC_TO_VK = {
    82: win32con.VK_NUMPAD0,
    79: win32con.VK_NUMPAD1,
    81: win32con.VK_NUMPAD3,
    71: win32con.VK_NUMPAD7,
    73: win32con.VK_NUMPAD9,
    76: None,
    78: None,
    83: None
}
NUMPAD_SC_TO_NAME = {
    82:'num 0',79:'num 1',81:'num 3',71:'num 7',73:'num 9',76:'num 5',78:'num add',83:'num del'
}
def make_np_press(sc):
    def h(e):
        if is_paused(): reinject_local(NUMPAD_SC_TO_NAME.get(sc,''),'down'); return
        if sc == 76:
            if not post_vk_to(target_s, VK['DOWN'], True, extended=True):
                reinject_local('down','down')
        elif sc == 83:
            if not post_vk_to(target_s, VK['2'], True, extended=False):
                reinject_local('2','down')
        elif sc == 78:
            if not post_vk_to(target_s, VK['DECIMAL'], True, extended=False):
                reinject_local('num del','down')
        elif sc in (82,79,81,71,73):
            if not post_vk_to(target_s, NUMPAD_SC_TO_VK[sc], True, extended=False):
                reinject_local(NUMPAD_SC_TO_NAME.get(sc,''),'down')
    return h
def make_np_release(sc):
    def h(e):
        if is_paused(): reinject_local(NUMPAD_SC_TO_NAME.get(sc,''),'up'); return
        if sc == 76:
            if not post_vk_to(target_s, VK['DOWN'], False, extended=True):
                reinject_local('down','up')
        elif sc == 83:
            if not post_vk_to(target_s, VK['2'], False, extended=False):
                reinject_local('2','up')
        elif sc == 78:
            if not post_vk_to(target_s, VK['DECIMAL'], False, extended=False):
                reinject_local('num del','up')
        elif sc in (82,79,81,71,73):
            if not post_vk_to(target_s, NUMPAD_SC_TO_VK[sc], False, extended=False):
                reinject_local(NUMPAD_SC_TO_NAME.get(sc,''),'up')
    return h
for sc in [76,83,78,82,79,81,71,73]:
    keyboard.on_press_key(sc, make_np_press(sc), suppress=True)
    keyboard.on_release_key(sc, make_np_release(sc), suppress=True)

pressed_h = {'w':False,'a':False,'s':False,'d':False}
def run_q_to_h():
    if not _is_valid(target_h): return
    tap_vk_to(target_h, VK['9'])
    tap_vk_to(target_h, VK[','])
def run_e_to_h():
    if not _is_valid(target_h): return
    tap_vk_to(target_h, VK['2'])
    tap_vk_to(target_h, VK['1'])
    tap_vk_to(target_h, VK['SPACE'])
    tap_vk_to(target_h, VK['3'])
def space_once_to_h():
    if not _is_valid(target_h): return
    tap_vk_to(target_h, VK['3'])

def on_w_down(_):
    if is_paused(): reinject_local('w','down'); return
    if not _is_valid(target_h): reinject_local('w','down'); return
    if not pressed_h['w']:
        pressed_h['w'] = True
        post_vk_to(target_h, VK['UP'], True, extended=True)
    if not _fg_is_target_h(): reinject_local('w','down')
def on_w_up(_):
    if is_paused(): reinject_local('w','up'); return
    if not _is_valid(target_h): reinject_local('w','up'); return
    if pressed_h['w']:
        pressed_h['w'] = False
        post_vk_to(target_h, VK['UP'], False, extended=True)
    if not _fg_is_target_h(): reinject_local('w','up')

def on_a_down(_):
    if is_paused(): reinject_local('a','down'); return
    if not _is_valid(target_h): reinject_local('a','down'); return
    if not pressed_h['a']:
        pressed_h['a'] = True
        post_vk_to(target_h, VK['LEFT'], True, extended=True)
    if not _fg_is_target_h(): reinject_local('a','down')
def on_a_up(_):
    if is_paused(): reinject_local('a','up'); return
    if not _is_valid(target_h): reinject_local('a','up'); return
    if pressed_h['a']:
        pressed_h['a'] = False
        post_vk_to(target_h, VK['LEFT'], False, extended=True)
    if not _fg_is_target_h(): reinject_local('a','up')

def on_s_down(_):
    if keyboard.is_pressed('shift'):
        set_target_s(); return
    if is_paused(): reinject_local('s','down'); return
    if not _is_valid(target_h): reinject_local('s','down'); return
    if not pressed_h['s']:
        pressed_h['s'] = True
        post_vk_to(target_h, VK['DOWN'], True, extended=True)
    if not _fg_is_target_h(): reinject_local('s','down')
def on_s_up(_):
    if keyboard.is_pressed('shift'):
        return
    if is_paused(): reinject_local('s','up'); return
    if not _is_valid(target_h): reinject_local('s','up'); return
    if pressed_h['s']:
        pressed_h['s'] = False
        post_vk_to(target_h, VK['DOWN'], False, extended=True)
    if not _fg_is_target_h(): reinject_local('s','up')

def on_d_down(_):
    if is_paused(): reinject_local('d','down'); return
    if not _is_valid(target_h): reinject_local('d','down'); return
    if not pressed_h['d']:
        pressed_h['d'] = True
        post_vk_to(target_h, VK['RIGHT'], True, extended=True)
    if not _fg_is_target_h(): reinject_local('d','down')
def on_d_up(_):
    if is_paused(): reinject_local('d','up'); return
    if not _is_valid(target_h): reinject_local('d','up'); return
    if pressed_h['d']:
        pressed_h['d'] = False
        post_vk_to(target_h, VK['RIGHT'], False, extended=True)
    if not _fg_is_target_h(): reinject_local('d','up')

def on_q_down(_):
    if is_paused(): reinject_local('q','down'); return
    threading.Thread(target=run_q_to_h, daemon=True).start()
def on_q_up(_):
    if is_paused(): reinject_local('q','up'); return

def on_e_down(_):
    if is_paused(): reinject_local('e','down'); return
    threading.Thread(target=run_e_to_h, daemon=True).start()
def on_e_up(_):
    if is_paused(): reinject_local('e','up'); return

def on_space_down(_):
    if is_paused(): reinject_local('space','down'); return
    threading.Thread(target=space_once_to_h, daemon=True).start()
def on_space_up(_):
    if is_paused(): reinject_local('space','up'); return

def on_x_down(_):
    if is_paused(): reinject_local('x','down'); return
    if _is_valid(target_h): post_vk_to(target_h, VK['A'], True, extended=False)
    if _is_valid(target_s): post_vk_to(target_s, VK['A'], True, extended=False)
def on_x_up(_):
    if is_paused(): reinject_local('x','up'); return
    if _is_valid(target_h): post_vk_to(target_h, VK['A'], False, extended=False)
    if _is_valid(target_s): post_vk_to(target_s, VK['A'], False, extended=False)

keyboard.on_press_key('w', on_w_down, suppress=True)
keyboard.on_release_key('w', on_w_up, suppress=True)
keyboard.on_press_key('a', on_a_down, suppress=True)
keyboard.on_release_key('a', on_a_up, suppress=True)
keyboard.on_press_key('s', on_s_down, suppress=True)
keyboard.on_release_key('s', on_s_up, suppress=True)
keyboard.on_press_key('d', on_d_down, suppress=True)
keyboard.on_release_key('d', on_d_up, suppress=True)
keyboard.on_press_key('q', on_q_down, suppress=True)
keyboard.on_release_key('q', on_q_up, suppress=True)
keyboard.on_press_key('e', on_e_down, suppress=True)
keyboard.on_release_key('e', on_e_up, suppress=True)
keyboard.on_press_key('space', on_space_down, suppress=True)
keyboard.on_release_key('space', on_space_up, suppress=True)
keyboard.on_press_key('x', on_x_down, suppress=True)
keyboard.on_release_key('x', on_x_up, suppress=True)

keyboard.add_hotkey('shift+s', set_target_s, suppress=False)
keyboard.add_hotkey('shift+h', set_target_h, suppress=False)

for n in ARROW_VK:
    keyboard.on_press_key(n, make_arrow_press(n), suppress=True)
    keyboard.on_release_key(n, make_arrow_release(n), suppress=True)
for sc in [76,83,78,82,79,81,71,73]:
    keyboard.on_press_key(sc, make_np_press(sc), suppress=True)
    keyboard.on_release_key(sc, make_np_release(sc), suppress=True)

print("Routing active. '-' toggles pause. Shift+S/H to lock targets.")
try:
    keyboard.wait()
finally:
    keyboard.unhook_all_hotkeys()
