# -*- coding: utf-8 -*-
"""
EZMidiGamer 配置文件 / Configuration file
https://github.com/zlsslz/EZMidiGamer

这是 EZMidiGamer 的配置文件。修改此文件即可调整配置。请在调整后重启程序。
-注意：请在第一次使用时在此处自行修改配置内容：
    若不清楚您的弯音轮或旋钮的范围，请设置：“CALIBRATE_ON_START = True”，然后运行以校准：
    移动用于操控的弯音轮、Mod 轮和旋钮，使其达到最大范围，根据打印范围修正中心值与 CC 号。
    请确保 “config.py” 与主程序在同一文件夹内。

This is the configuration file of EZMidiGamer.
Edit this file to modify configurations. Please save and reload after modify.
-Important: Please modify the configurationin in 'config.py' yourself during first use. 
    If you are not sure about the range of your pitch bend wheel or knob, 
    set 'CALIBRATE_ON_START = True' and run for calibration:
    move the pitch/mod wheels fully and turn both knobs through their full range, 
    then fix the centers/CC numbers from the printed ranges. 
    Please ensure 'config.py' is located in the same folder as this main program.
"""
CONFIG_VERSION = 1

from pynput.keyboard import Key as KKey
print('[EZMG] You have run a configuration file. To use EZMidiGamer, please run "EZMidiGamer.py".'
    '\n[EZMG] 您直接运行了配置文件。如需使用 EZMidiGamer，请运行主程序 “EZMidiGamer.py”。')

# ---------------- CONFIG AREA  配置区 ----------------


# Camera input source 输入方式 : (override with --source)
# 'wheel' ：pitch-bend for left&right, mod for up&down  / 弯音轮控制左右，Mod 轮控制上下
# 'knob' ：two knobs for left&right and up&down / 两个旋钮分别控制左右 / 上下
# 'both' ：wheel and knob active at once; their motion is added / 同时生效，移动量叠加
VIEW_SOURCE = "both"

# Camera move mode 移动模式 :  (override with --move)
#'velocity' : off-center amount = mouse speed / 控件偏离中心的量=鼠标速度
#'displacement' : amount you move the control = mouse displacement / 控件转动量=鼠标位移
MOVE_MODE = "displacement"

# Main loop poll interval in seconds  主循环间隔
# Common values: 0.01 / 0.02 / 0.05  
POLL_INTERVAL = 0.01

# Run the range calibration on startup 开始时校准，设置为 True 以在运行校准
# set True to re-detect and print the actual ranges. 
CALIBRATE_ON_START = False

# ---- MIDI device selection  MIDI设备选择 ----  
# Optional device name keyword: if set, program will select the first port whose
# name contains this string (case-insensitive); or falls back to automatic.
# 程序会先搜索包含改名称（不分大小写）的第一个端口，无果后自动选择
MIDI_DEVICE_NAME = "123"

# ---- Wheels: centers and dead zones  滑轮中心和死区 ---- 
PITCH_CENTER = 0
MOD_CENTER = 63
PITCH_DEADZONE = 512
MOD_DEADZONE = 16

# ---- Knobs: CC numbers, center and dead zone  旋钮：CC号，中心和死区----  
KNOB_X_CC = 74
KNOB_Y_CC = 71
KNOB_VEL_CENTER = 64     # knob position meaning "zero speed"
KNOB_DEADZONE = 8        # knob velocity dead zone

# ---- Velocity gains: pixels/second / 速度模式灵敏度：单元每秒  ----
PITCH_VEL = 0.15
MOD_VEL = 10.0
KNOB_X_VEL = 6.0
KNOB_Y_VEL = 6.0

# ---- Displacement gains: pixels / 位移模式灵敏度：单元----
PITCH_DISP = 0.1
MOD_DISP = 8
KNOB_X_DISP = 12.0
KNOB_Y_DISP = 12.0

# ---- Displacement per-tick limits / 位移模式每tick累积上限 ----
# 若在某个tick下移动超过该值，不产生效果
PITCH_DISP_MAX_STEP = 2048
MOD_DISP_MAX_STEP   = 16
KNOB_DISP_MAX_STEP  = 20

# Maximum pixels moved per single tick / 每tick最大移动像素
# Guards against sudden flings
MAX_MOVE = 300

# Decide how much distance(notch) to move when the wheel scrolled
# Not related to switch items in the games like Minecraft
# 设定每次滚轮操作移动距离，与某些游戏的切换物品功能（如MC）无关
SCROLL_AMOUNT = 5

# Direction inversion / 方向反向
PITCH_INVERT = False
MOD_INVERT = True
KNOB_INVERT_X = False
KNOB_INVERT_Y = True

# Note mapping: MIDI note number -> (kind, value)
# 按键映射：MIDI按键编号 -> （按键种类，按键名称）
#   kind 'key'  : a keyboard key (a character, or a pynput Key such as KKey.esc)
#   kind 'mouse': 'left' / 'right' / 'middle' mouse button
#   kind 'scroll': 'up' / 'down' to scroll
# Example 示例 : 60: ("key", "a")
# C3=48, C4=60, C5=72, C6=84
NOTE_MAP = {
    60: ("key", "a"),            # C4  -> A
    61: ("mouse", "left"),       # C#4 -> mouse left
    62: ("key", "w"),            # D4  -> W
    63: ("mouse", "right"),      # D#4 -> mouse right
    64: ("key", "d"),            # E4  -> D
    65: ("key", "s"),            # F4  -> S
    66: ("key", KKey.space),     # F#4 -> Space
    67: ("key", KKey.shift),     # G4  -> Shift
    69: ("key", 'z'),            # A4  -> Z
    72: ("key", KKey.esc),       # C5  -> Esc
    73: ("scroll", "up"),        # C#5 -> Scroll Up
    74: ("key", "e"),            # D5  -> E
    75: ("scroll", "down"),      # D#5 -> Scroll Down
    76: ("key", KKey.f5),        # E5  -> F5
}

# Press which key to quit this program  按下此键退出程序 
QUIT_NOTE = 84  # Default: 84(C6)