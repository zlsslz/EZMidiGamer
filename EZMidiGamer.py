#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
EZMidiGamer v1
==========
简单地把任意 MIDI 控制器变成系统鼠标 / 键盘输入，
从而用琴键、弯音轮、旋钮来操作任意游戏。
默认参数针对 MiniLab 3，最初用于 Minecraft Java 版。

Simply turn any MIDI controller into system mouse/keyboard input, 
so you can play any game with keys, wheels and knobs.
Originally built for Minilab3 in Minecraft Java Edition.

-配置修改 / Configuration settings：

    以下配置参数均可在配置区修改。
    The following configuration parameters can be modified in the configuration area.

    两个独立设置 / Two independent settings:

    VIEW_SOURCE — 由哪些物理控件驱动视角 / which physical controls drive the camera
        wheel : 弯音轮(左右) + Mod 轮(上下) / pitch-bend (left/right) + mod (up/down)
        knob  : 两个旋钮(默认 CC74=左右, CC71=上下) / two knobs (CC74 / CC71)
        both  : 转轮与旋钮同时生效，移动量叠加 / wheel and knob active together

    MOVE_MODE — 控件位置如何变成视角移动 / how control position becomes camera motion
        velocity     : 偏离中心量 = 转动速度，推住持续转、松手即停
                    off-center amount = rotation speed; hold to turn, release to stop
        displacement : 转动量 = 位移，转多少偏多少，不转不动
                    amount moved = camera displacement; no input => no motion

    两种方式松手都会停止并在下次操作重新计数。固定频率轮询(POLL_INTERVAL)解决了
    纯事件驱动 MIDI “控件不动、视角就不动”的问题。

    Both modes stop on release and restart on the next input. A fixed-rate poll loop
    (POLL_INTERVAL) fixes the "holding the control still does nothing" limitation.

    默认音符映射(按下=按住, 松开=释放) / Default note mapping:
        60 C4  -> A            61 C#4 -> 鼠标左键 / mouse left
        62 D4  -> W            63 D#4 -> 鼠标右键 / mouse right
        64 E4  -> D            65 F4  -> S
        66 F#4 -> 空格(跳)     67 G4  -> 左 Shift(潜行)
        69 A4  -> Z           
        72 C5  -> Esc          74 D5  -> E
        76 E5  -> F5(切换人称视角 / perspective)

-运行方法 / How to run：
    安装 / Install:  python -m pip install -r requirements.txt
        (python -m pip install mido pygame pynput)
    运行 / Run:      python EZMidiGamer.py
                    python EZMidiGamer.py --source wheel --move velocity
                    python EZMidiGamer.py --source both
                    python EZMidiGamer.py --debug
    退出 / Quit:     Ctrl+C
"""

import argparse
import os
import sys
import time

# Prefer mido's Pygame backend on Windows: it ships pre-built wheels and does
# not require python-rtmidi or a C compiler. Must be set before importing mido.
if sys.platform.startswith("win"):
    os.environ.setdefault("MIDO_BACKEND", "mido.backends.pygame")

import mido
from pynput.mouse import Controller as Mouse, Button as MButton
from pynput.keyboard import Controller as Keyboard, Key as KKey


# ============================ Configuration 配置区 ============================
# Camera input source: 'wheel' | 'knob' | 'both' (override with --source)
VIEW_SOURCE = "both"
# Camera move mode: 'velocity' | 'displacement' (override with --move)
MOVE_MODE = "velocity"

# Main loop poll interval in seconds. Smaller value is smoother, slightly more CPU.
# Common values: 0.02 / 0.05 / 0.2 
POLL_INTERVAL = 0.02

# Run the range calibration on startup (defaults are hard-coded; set True to
# re-detect and print the actual ranges of your device).
CALIBRATE_ON_START = False

# ---- Wheels: centers and dead zones ----
# This device reports signed pitch-bend in -8192..8191 (center 0) and the
# modulation wheel in 0..127 (center 63). Re-run calibration if yours differs.
PITCH_CENTER = 0
MOD_CENTER = 63
PITCH_DEADZONE = 512
MOD_DEADZONE = 8

# ---- Knobs: CC numbers, velocity center and dead zone ----
KNOB_X_CC = 74
KNOB_Y_CC = 71
KNOB_VEL_CENTER = 64     # knob position meaning "zero speed"
KNOB_DEADZONE = 8        # knob velocity dead zone

# ---- Velocity gains: pixels/second per single unit off-center ----
PITCH_VEL = 0.15
MOD_VEL = 10.0
KNOB_X_VEL = 6.0
KNOB_Y_VEL = 6.0

# ---- Displacement gains: pixels per single unit of change ----
PITCH_DISP = 0.003
MOD_DISP = 1.8
KNOB_X_DISP = 12.0
KNOB_Y_DISP = 12.0

# Maximum pixels moved per single tick (guards against sudden flings)
MAX_MOVE = 300

# Direction inversion
PITCH_INVERT = False
MOD_INVERT = True
KNOB_INVERT_X = False
KNOB_INVERT_Y = True

# Note mapping: MIDI note number -> (kind, value)
#   kind 'key'  : a keyboard key (a character, or a pynput Key such as KKey.esc)
#   kind 'mouse': 'left' / 'right' / 'middle' mouse button
# Example: 60: ("key", "a")
NOTE_MAP = {
    60: ("key", "a"),            # C4  -> A
    61: ("mouse", "left"),       # C#4 -> mouse left
    62: ("key", "w"),            # D4  -> W
    63: ("mouse", "right"),      # D#4 -> mouse right
    64: ("key", "d"),            # E4  -> D
    65: ("key", "s"),            # F4  -> S
    66: ("key", KKey.space),     # F#4 -> Space (jump)
    67: ("key", KKey.shift),     # G4  -> Left Shift (sneak)
    69: ("key", 'Z'),            # A4  -> Z
    72: ("key", KKey.esc),       # C5  -> Esc
    74: ("key", "e"),            # D5  -> E
    76: ("key", KKey.f5),        # E5  -> F5 (toggle perspective)
}
# ========================================================================


def parse_args():
    parser = argparse.ArgumentParser(
        description="EZMidiGamer: turn a MIDI controller into mouse/keyboard input")
    parser.add_argument("--port", type=int, default=None,
                        help="MIDI input port index (see the output of --list)")
    parser.add_argument("--list", action="store_true",
                        help="list MIDI input ports and exit")
    parser.add_argument("--no-calibrate", action="store_true",
                        help="force-skip the startup calibration")
    parser.add_argument("--debug", action="store_true",
                        help="print raw MIDI values for troubleshooting")
    parser.add_argument("--source", choices=["wheel", "knob", "both"], default=None,
                        help="camera input source, overrides VIEW_SOURCE")
    parser.add_argument("--move", choices=["velocity", "displacement"], default=None,
                        help="camera move mode, overrides MOVE_MODE")
    return parser.parse_args()


def find_port(wanted):
    """Return the MIDI input port name, preferring a MiniLab device."""
    names = mido.get_input_names()
    if not names:
        print("[!] No MIDI input device found. Make sure the controller is "
              "connected over USB and powered on.")
        return None

    idx = next((i for i, n in enumerate(names) if "minilab" in n.lower()), None)

    if wanted is not None:
        if 0 <= wanted < len(names):
            idx = wanted
        else:
            print(f"[!] Invalid port index {wanted}; there are {len(names)} ports.")
            return None

    print("Available MIDI input ports:")
    for i, name in enumerate(names):
        marker = "  <-- selected" if i == idx else ""
        print(f"  [{i}] {name}{marker}")

    if idx is None:
        idx = 0
        print(f"[?] No MiniLab detected; defaulting to [{idx}] {names[idx]}")
    return names[idx]


def calibrate(port, seconds=10.0):
    """Print the observed ranges of the wheels and knobs to verify defaults."""
    print(f"[#] Calibrating for {seconds:.0f}s: move the pitch/mod wheels and "
          "turn both knobs through their full range...")
    pitches, mods, cc_ranges = [], [], {}
    deadline = time.time() + seconds

    while time.time() < deadline:
        msg = port.poll()
        if msg:
            if msg.type == "pitchwheel":
                pitches.append(msg.pitch)
            elif msg.type == "control_change":
                if msg.control == 1:
                    mods.append(msg.value)
                else:
                    rng = cc_ranges.setdefault(msg.control, [msg.value, msg.value])
                    rng[0] = min(rng[0], msg.value)
                    rng[1] = max(rng[1], msg.value)
        else:
            time.sleep(0.01)

    if pitches:
        print(f"[#] Pitch range {min(pitches)}..{max(pitches)}")
    if mods:
        print(f"[#] Mod range {min(mods)}..{max(mods)}")
    for cc, (lo, hi) in sorted(cc_ranges.items()):
        print(f"[#] CC{cc} range {lo}..{hi}")


class Mapper:
    """Tracks controller state and translates it into mouse/keyboard input."""

    def __init__(self, source, move_mode, debug=False):
        self.source = source
        self.move_mode = move_mode
        self.debug = debug
        self.mouse = Mouse()
        self.keyboard = Keyboard()
        self.held = set()

        # Current values of the continuous controls
        self.pitch = PITCH_CENTER
        self.mod = MOD_CENTER
        self.knob = {}                       # CC number -> value
        # Per-tick accumulated change for displacement mode (reset after tick)
        self.wdisp = {"x": 0.0, "y": 0.0}
        self.kdisp = {"x": 0.0, "y": 0.0}

    # --------------------------- base actions ---------------------------
    def move(self, dx, dy):
        dx = max(-MAX_MOVE, min(MAX_MOVE, dx))
        dy = max(-MAX_MOVE, min(MAX_MOVE, dy))
        if dx or dy:
            self.mouse.move(int(round(dx)), int(round(dy)))

    def note_down(self, note):
        action = NOTE_MAP.get(note)
        if not action or note in self.held:
            return
        kind, value = action
        if kind == "mouse":
            self.mouse.press(getattr(MButton, value))
        else:
            self.keyboard.press(value)
        self.held.add(note)

    def note_up(self, note):
        action = NOTE_MAP.get(note)
        if not action or note not in self.held:
            return
        kind, value = action
        if kind == "mouse":
            self.mouse.release(getattr(MButton, value))
        else:
            self.keyboard.release(value)
        self.held.discard(note)

    # --------------------- per-source tick contributions ---------------------
    def _wheel_contrib(self, dt):
        wx = self.pitch - PITCH_CENTER
        wy = self.mod - MOD_CENTER
        x_inv = -1 if PITCH_INVERT else 1
        y_inv = -1 if MOD_INVERT else 1

        if self.move_mode == "velocity":
            vx = (wx * PITCH_VEL * x_inv) if abs(wx) >= PITCH_DEADZONE else 0.0
            vy = (wy * MOD_VEL * y_inv) if abs(wy) >= MOD_DEADZONE else 0.0
            return vx * dt, vy * dt

        vx = self.wdisp["x"] * PITCH_DISP * x_inv
        vy = self.wdisp["y"] * MOD_DISP * y_inv
        return vx, vy

    def _knob_contrib(self, dt):
        kx = self.knob.get(KNOB_X_CC, KNOB_VEL_CENTER) - KNOB_VEL_CENTER
        ky = self.knob.get(KNOB_Y_CC, KNOB_VEL_CENTER) - KNOB_VEL_CENTER
        x_inv = -1 if KNOB_INVERT_X else 1
        y_inv = -1 if KNOB_INVERT_Y else 1

        if self.move_mode == "velocity":
            vx = (kx * KNOB_X_VEL * x_inv) if abs(kx) >= KNOB_DEADZONE else 0.0
            vy = (ky * KNOB_Y_VEL * y_inv) if abs(ky) >= KNOB_DEADZONE else 0.0
            return vx * dt, vy * dt

        vx = self.kdisp["x"] * KNOB_X_DISP * x_inv
        vy = self.kdisp["y"] * KNOB_Y_DISP * y_inv
        return vx, vy

    # --------------------- MIDI events: update state ---------------------
    def handle(self, msg):
        if self.debug:
            if msg.type == "pitchwheel":
                print(f"[debug] pitchwheel = {msg.pitch}")
            elif msg.type == "control_change":
                print(f"[debug] CC{msg.control} = {msg.value}")
            elif msg.type in ("note_on", "note_off"):
                print(f"[debug] note = {msg.note} velocity = {msg.velocity}")

        if msg.type == "pitchwheel":
            if self.source in ("wheel", "both") and self.move_mode == "displacement":
                self.wdisp["x"] += msg.pitch - self.pitch
            self.pitch = msg.pitch

        elif msg.type == "control_change":
            if msg.control == 1:
                if self.source in ("wheel", "both") and self.move_mode == "displacement":
                    self.wdisp["y"] += msg.value - self.mod
                self.mod = msg.value
            elif self.source in ("knob", "both") and msg.control in (KNOB_X_CC, KNOB_Y_CC):
                last = self.knob.get(msg.control, msg.value)
                if self.move_mode == "displacement":
                    axis = "x" if msg.control == KNOB_X_CC else "y"
                    self.kdisp[axis] += msg.value - last
                self.knob[msg.control] = msg.value

        elif msg.type == "note_on":
            if msg.velocity > 0:
                self.note_down(msg.note)
            else:
                self.note_up(msg.note)
        elif msg.type == "note_off":
            self.note_up(msg.note)

    # --------------------- fixed-rate poll: sum sources ---------------------
    def tick(self, dt):
        vx = vy = 0.0
        if self.source in ("wheel", "both"):
            wx, wy = self._wheel_contrib(dt)
            vx += wx
            vy += wy
        if self.source in ("knob", "both"):
            kx, ky = self._knob_contrib(dt)
            vx += kx
            vy += ky

        # Displacement accumulators restart counting every tick
        self.wdisp = {"x": 0.0, "y": 0.0}
        self.kdisp = {"x": 0.0, "y": 0.0}
        self.move(vx, vy)


def main():
    args = parse_args()
    source = args.source or VIEW_SOURCE
    move_mode = args.move or MOVE_MODE

    if args.list:
        names = mido.get_input_names()
        if not names:
            print("[!] No MIDI device found.  没有找到 MIDI 设备。")
            return 1
        for i, name in enumerate(names):
            print(f"[{i}] {name}")
        return 0

    port_name = find_port(args.port)
    if port_name is None:
        return 1

    print(f"\n[>] Connected: {port_name}  | source: {source}  | mode: {move_mode}\n[>] 连接设备: {port_name}  | 输入: {source}  | 模式: {move_mode}")
    mapper = Mapper(source, move_mode, args.debug)

    try:
        with mido.open_input(port_name) as port:
            if CALIBRATE_ON_START and not args.no_calibrate:
                calibrate(port)
            print("[>] Running. Press Ctrl+C to quit.  运行中。按下 Ctrl+C 退出。\n")
            last = time.time()
            while True:
                # Non-blocking drain of every message received this tick
                for msg in port.iter_pending():
                    mapper.handle(msg)
                now = time.time()
                mapper.tick(now - last)
                last = now
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[#] Quit.  已退出。")
    finally:
        for note in list(mapper.held):
            mapper.note_up(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
