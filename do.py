import time, keyboard, threading, atexit
import win32gui, win32con, win32api

d=0.08; esc_gap=0.10; tab_gap=0.10; hold3=0.3
e1=threading.Event(); e3=threading.Event()
busy=threading.Event()
held=set()
ARROWS=('up','down','left','right')
ARROW_SC=set()
pressed_sc=set()
TARGET=None
suppress_hook=None

VK = {
    'esc':0x1B,'tab':0x09,'enter':0x0D,'home':0x24,
    'up':0x26,'down':0x28,'left':0x25,'right':0x27,
    '0':0x30,'1':0x31,'2':0x32,'3':0x33,'4':0x34,'5':0x35,'6':0x36,'9':0x39,
}
WM_KEYDOWN=0x0100; WM_KEYUP=0x0101

def post_key(hwnd, key):
    vk = VK[key]
    win32api.PostMessage(hwnd, WM_KEYDOWN, vk, 0)
    win32api.PostMessage(hwnd, WM_KEYUP,   vk, 0)

def post_seq(keys, gap):
    if TARGET and win32gui.IsWindow(TARGET):
        for k in keys:
            post_key(TARGET, k); time.sleep(gap)
    else:
        for k in keys:
            keyboard.send(k); time.sleep(gap)

def press_hold(k):
    if k not in held:
        keyboard.press(k); held.add(k)

def release(k):
    if k in held:
        keyboard.release(k); held.discard(k)

def cleanup():
    release('3')
    for k in list(held):
        release(k)
    global suppress_hook
    if suppress_hook:
        keyboard.unhook(suppress_hook); suppress_hook=None
atexit.register(cleanup)

def dbl_esc():
    keyboard.send('esc'); time.sleep(0.08)
    keyboard.send('esc'); time.sleep(0.08)

def w1():
    while True:
        e1.wait()
        while e1.is_set():
            time.sleep(0.01); post_seq(['1'], d)
            if not e1.is_set(): break
            post_seq(['up'], d)
            if not e1.is_set(): break
            post_seq(['enter'], d)

def w3():
    while True:
        e3.wait()
        time.sleep(0.01); post_seq(['esc'], esc_gap)
        if not e3.is_set(): continue
        post_seq(['esc'], esc_gap)
        if not e3.is_set(): continue
        post_seq(['tab'], tab_gap)
        if not e3.is_set(): continue
        post_seq(['tab'], tab_gap)
        if not e3.is_set(): continue
        while e3.is_set():
            keyboard.press('3'); t0=time.time()
            while e3.is_set() and time.time()-t0<hold3: time.sleep(0.01)
            keyboard.release('3')
            if not e3.is_set(): break
            time.sleep(0.02)
        time.sleep(0.10); post_seq(['esc'], 0)
        time.sleep(0.10); post_seq(['esc'], 0)

def stop1():
    if e1.is_set():
        e1.clear(); dbl_esc()

def stop3():
    if e3.is_set():
        e3.clear(); release('3'); dbl_esc(); cleanup()

def tog1():
    if e1.is_set(): stop1()
    else: stop3(); e1.set()

def tog3():
    if e3.is_set(): stop3()
    else: stop1(); e3.set()

def halt_all():
    e1.clear(); e3.clear(); release('3')

def macro9():
    if busy.is_set(): return
    halt_all()
    post_seq(['esc','esc'], d)
    post_seq(['9','home','enter'], d)

def macroDel():
    if busy.is_set(): return
    halt_all()
    time.sleep(0.10)
    post_seq(['esc'], 0)
    time.sleep(0.10)
    post_seq(['esc'], 0)
    time.sleep(0.20)
    post_seq(['tab'], 0.20)
    post_seq(['tab'], 0.20)
    post_seq(['5'], 0.20)
    post_seq(['6'], 0.10)
    time.sleep(0.10)
    time.sleep(0.10)
    post_seq(['esc'], 0)
    time.sleep(0.10)
    post_seq(['esc'], 0)
    time.sleep(0.20)
    post_seq(['5'], 0)
    time.sleep(0.05)
    post_seq(['home'], 0)
    time.sleep(0.10)
    post_seq(['enter'], 0)
    time.sleep(0.10)
    post_seq(['6'], 0)
    time.sleep(0.10)
    post_seq(['enter'], 0)

def macro7():
    if busy.is_set(): return
    halt_all()
    time.sleep(0.20)
    post_seq(['esc'], 0)
    time.sleep(0.10)
    post_seq(['esc'], 0)
    time.sleep(0.05)
    post_seq(['tab'], 0)
    time.sleep(0.15)
    post_seq(['tab'], 0)
    time.sleep(0.10)
    post_seq(['4'], 0)
    time.sleep(0.10)
    post_seq(['enter'], 0)
    time.sleep(0.20)
    post_seq(['esc'], 0)
    time.sleep(0.10)
    post_seq(['esc'], 0)
    tog3()

def macro0():
    global suppress_hook
    if busy.is_set(): return
    busy.set()
    was_running_e3 = e3.is_set()
    if was_running_e3: stop3()
    suppress_hook = keyboard.hook(lambda e: None, suppress=True)
    try:
        halt_all()
        time.sleep(0.03)
        post_seq(['esc'], 0)
        time.sleep(0.03)
        post_seq(['esc'], 0)
        time.sleep(0.05)
        post_seq(['3'], 0)
        time.sleep(0.05)
        post_seq(['home'], 0)
        time.sleep(0.03)
        post_seq(['enter'], 0)
        time.sleep(0.03)
        for _ in range(5): 
            time.sleep(0.03)
            post_seq(['3'], 0)
            time.sleep(0.05)
            post_seq(['enter'], 0)
            time.sleep(0.05)
            post_seq(['0'], 0)
            time.sleep(0.03)
    finally:
        if suppress_hook:
            keyboard.unhook(suppress_hook); suppress_hook=None
        busy.clear()
        if was_running_e3: tog3()

KP = {
    'num1': set(keyboard.key_to_scan_codes('num 1')),
    'num3': set(keyboard.key_to_scan_codes('num 3')),
    'num7': set(keyboard.key_to_scan_codes('num 7')),
    'num9': set(keyboard.key_to_scan_codes('num 9')),
    'numdel': set(keyboard.key_to_scan_codes('num del')),
}

def hook(e):
    if busy.is_set():
        return
    sc=e.scan_code
    n=e.name or ''
    if e.event_type=='down':
        if n in ARROWS:
            ARROW_SC.add(sc)
            if e3.is_set():
                if n in held: release(n)
                else: press_hold(n)
            return
        if sc in pressed_sc: return
        pressed_sc.add(sc)
        if sc in ARROW_SC: return
        if sc in KP['num1']: tog1(); return
        if sc in KP['num3']: tog3(); return
        if sc in KP['num7']: macro7(); return
        if sc in KP['num9']: macro9(); return
        if sc in KP['numdel']: macroDel(); return
    elif e.event_type=='up':
        pressed_sc.discard(sc)

keyboard.hook(hook, suppress=False)
keyboard.add_hotkey('num 0', macro0, suppress=False)
keyboard.add_hotkey('num 2', lambda: keyboard.send('2'), suppress=True)
keyboard.add_hotkey('num 5', lambda: post_seq(['down'], 0), suppress=True)

threading.Thread(target=w1, daemon=True).start()
threading.Thread(target=w3, daemon=True).start()

keyboard.wait()
