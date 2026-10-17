#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-3.0-or-later
"""
EZMidiGamer v1
https://github.com/zlsslz/EZMidiGamer
==========
简单地把任意 MIDI 控制器变成系统鼠标 / 键盘输入，
从而用琴键、弯音轮、旋钮来操作任意游戏。
默认参数针对 MiniLab 3，最初用于 Minecraft Java 版。

Simply turn any MIDI controller into system mouse/keyboard input, 
so you can play any game with keys, wheels and knobs.
Originally built for Minilab3 in Minecraft Java Edition.

-How to run / 运行方法:
    Install / 安装:  python -m pip install -r requirements.txt
        (python -m pip install mido pygame pynput)
    Run / 运行:      python EZMidiGamer.py
                    python EZMidiGamer.py --source wheel --move velocity
                    python EZMidiGamer.py --source both
                    python EZMidiGamer.py --debug
    Quit / 退出:     Ctrl+C

-Important: Please modify the configurationin in 'config.py' yourself during first use. 
    If you are not sure about the range of your pitch bend wheel or knob, 
    set 'CALIBRATE_ON_START = True' and run for calibration.
    Please ensure 'config.py' is located in the same folder as this main program.

-注意：请在第一次使用时在 “config.py” 自行修改配置内容。 
    若不清楚您的弯音轮或旋钮的范围，请设置：“CALIBRATE_ON_START = True”，然后运行以校准。
    请确保 “config.py” 与主程序在同一文件夹内。
"""

import argparse
import os
import sys
import time

# Prefer mido's Pygame backend on Windows: it ships pre-built wheels and does
# not require python-rtmidi or a C compiler. Must be set before importing mido.
if sys.platform.startswith("win"):
    os.environ.setdefault("MIDO_BACKEND", "mido.backends.pygame")

#导入config
from config import *

import mido
from pynput.mouse import Controller as Mouse, Button as MButton
from pynput.keyboard import Controller as Keyboard, Key as KKey

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
    """Return the MIDI input port name, preferring the configured device name."""
    names = mido.get_input_names()
    if not names:
        print("[EZMG] Error: No MIDI input device found. Make sure the controller is "
              "connected over USB and powered on.\n[EZMG] 错误: 没有找到MIDI设备。请确保您的设备已连接。")
        return None

    idx = None

    # --port
    if wanted is not None:
        if 0 <= wanted < len(names):
            idx = wanted
        else:
            print(f"[EZMG] Error: Invalid port index {wanted}; there are {len(names)} ports. \n[EZMG] 错误: 无效的设备名称。")
            return None
    else:
        # 匹配关键字
        if MIDI_DEVICE_NAME:
            idx = next((i for i, n in enumerate(names)
                        if MIDI_DEVICE_NAME.lower() in n.lower()), None)
            if idx is not None:
                print(f"[EZMG] Matched configured device name '{MIDI_DEVICE_NAME}': "
                      f"{names[idx]}\n"
                      f"[EZMG] 已按配置的设备名称 '{MIDI_DEVICE_NAME}' 匹配：{names[idx]}")
        # minilab自动匹配（old version）
#        if idx is None:
#            idx = next((i for i, n in enumerate(names) if "minilab" in n.lower()), None)
#            if idx is not None and MIDI_DEVICE_NAME:
#                print(f"[?] Device name '{MIDI_DEVICE_NAME}' not found; falling back to "
#                      f"match: {names[idx]}\n"
#                      f"[?] 未找到 '{MIDI_DEVICE_NAME}'，回退到匹配：{names[idx]}")

    if idx is None and MIDI_DEVICE_NAME:
        print(f"[EZMG] Error: Device name is not found  错误：未找到设备  '{MIDI_DEVICE_NAME}'")
    
    if idx is None:
        idx = 0
        print(f"[EZMG] Defaulting to:  已自动设置: [{idx+1}] {names[idx]}")

    print("[EZMG] Available MIDI input ports:  可用MIDI端口：")
    for i, name in enumerate(names):
        marker = "  <-- selected 当前选择" if i == idx else ""
        print(f"  [{i+1}] {name}{marker}")
    
    return names[idx]

def calibrate(port, seconds=10.0):   #校准
    """Print the observed ranges of the wheels and knobs to verify defaults."""
    print(f"[EZMG] Calibrating for {seconds:.0f}s: move the pitch/mod wheels fully and "
          "turn both knobs through their full range...\n"
          f"[EZMG] 校准中，时长 {seconds:.0f} 秒：移动用于操控的弯音轮、Mod 轮和旋钮，使其达到最大范围……")
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
            time.sleep(0.01)  # 空转保护

    if pitches:
        print(f"[EZMG] Pitch range {min(pitches)}..{max(pitches)}")
    if mods:
        print(f"[EZMG] Mod range {min(mods)}..{max(mods)}")
    for cc, (lo, hi) in sorted(cc_ranges.items()):
        print(f"[EZMG] Activated CC{cc} , range {lo}..{hi}")


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

    def note_down(self, note):  # 按下音符，只有mouse和key需要self.held.add(note)
        action = NOTE_MAP.get(note)
        if not action or note in self.held:
            return
        kind, value = action
        if kind == "mouse":
            self.mouse.press(getattr(MButton, value))
            self.held.add(note)  
        elif kind == "key":
            self.keyboard.press(value)
            self.held.add(note)
        elif kind == "scroll":
            if value == "up":
                self.mouse.scroll(0, SCROLL_AMOUNT)   # 向上
            elif value == "down":
                self.mouse.scroll(0, -SCROLL_AMOUNT)  # 向下

    def note_up(self, note):
        action = NOTE_MAP.get(note)
        if not action or note not in self.held:
            return
        kind, value = action
        if kind == "mouse":
            self.mouse.release(getattr(MButton, value))
        if kind == "key":
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

        #超过最大位移就清零
        if self.move_mode == "displacement":
            if abs(self.wdisp["x"]) > PITCH_DISP_MAX_STEP:
                self.wdisp["x"] = 0
            if abs(self.wdisp["y"]) > MOD_DISP_MAX_STEP:
                self.wdisp["y"] = 0
            if abs(self.kdisp["x"]) > KNOB_DISP_MAX_STEP:
                self.kdisp["x"] = 0
            if abs(self.kdisp["y"]) > KNOB_DISP_MAX_STEP:
                self.kdisp["y"] = 0

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
    print("[EZMG] 欢迎使用EZMidiGamer。 Welcome to use EZMidiGamer. \n[EZMG] https://github.com/zlsslz/EZMidiGamer")
    args = parse_args()
    source = args.source or VIEW_SOURCE
    move_mode = args.move or MOVE_MODE

    if args.list:
        names = mido.get_input_names()
        if not names:
            print("[EZMG] Error: No MIDI device found.  错误：没有找到 MIDI 设备。")
            return 1
        for i, name in enumerate(names):
            print(f"[{i}] {name}")
        return 0

    port_name = find_port(args.port)
    if port_name is None:
        return 1

    print(f"\n[EZMG] Connected 连接设备: {port_name}  | source 输入: {source}  | mode 模式: {move_mode}")
    mapper = Mapper(source, move_mode, args.debug)

    try:
        with mido.open_input(port_name) as port:
            if CALIBRATE_ON_START and not args.no_calibrate:
                calibrate(port)
            print(f"[EZMG] Running. Press Ctrl+C or {QUIT_NOTE} to quit.  运行中。按下 Ctrl+C 或 {QUIT_NOTE} 退出。\n")
            last = time.time()
            while True:
                # Non-blocking drain of every message received this tick
                for msg in port.iter_pending():
                    if msg.type == "note_on" and msg.velocity > 0 and msg.note == QUIT_NOTE:
                        raise KeyboardInterrupt
                    mapper.handle(msg)
                now = time.time()
                mapper.tick(now - last)
                last = now
                time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("\n[EZMG] Quit.  已退出。")
    finally:
        for note in list(mapper.held):
            mapper.note_up(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
