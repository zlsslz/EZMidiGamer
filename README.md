# EZMidiGamer

[https://github.com/zlsslz/EZMidiGamer](https://github.com/zlsslz/EZMidiGamer)

Simply turn any MIDI controller into system mouse/keyboard input, so you can play any game with keys, wheels and knobs.

---

## [中文](#中文) | [English](#english)

# 中文

EZMidiGamer可以简单地把任意 MIDI 控制器变成系统鼠标 / 键盘输入，从而用琴键、弯音轮、旋钮来操作任意游戏。

*请在第一次使用时在 config.py 中自行修改配置内容。*

*若不清楚您的弯音轮或旋钮的范围，详见 “校准”。*

## 功能特性
* **用旋钮和滑轮控制鼠标移动**
  * 3种输入来源选项，2种移动方式选项（速度模式，位移模式），保证了丝滑的游戏体验（详见“鼠标控制”）
* **琴键自定义映射**
  * 随意映射任意按键，包括Esc等特殊键位和鼠标滚轮
* 不更改游戏文件，原理等同于用手柄 / 摇杆操作游戏
* 由 Python 编写，原理简单，可快速修改配置

## 工作原理

```
MIDI 控制器 ──MIDI 消息──> 轮询主循环 ──> 模拟鼠标/键盘 ──> 游戏
```

脚本通过 [mido](https://github.com/mido/mido) 读取 MIDI 消息，每隔 `POLL_INTERVAL`（0.01）秒轮询一次控件状态，
再通过 [pynput](https://github.com/moses-palmer/pynput) 模拟鼠标 / 键盘输入。

## 环境要求

* Python 3.8+
* 任意 MIDI 控制器
* Windows / macOS / Linux

> Windows 默认使用 mido 的 Pygame 后端，有预编译包，无需 C 编译器。

## 安装

```
git clone https://github.com/zlsslz/EZMidiGamer.git
cd EZMidiGamer
python -m pip install -r requirements.txt
python EZMidiGamer.py --list      # 确认能识别控制器
```

## 使用

```
python EZMidiGamer.py
```

可用终端附加参数（临时覆盖config文件）：

```
--list           # 列出电脑上所有可用的 MIDI 输入端口并退出
--port <编号>    # 强制指定 MIDI 端口索引（配合 --list 查看），例如：--port 1
--debug          # 开启调试模式
--no-calibrate   # 强制跳过启动时的 MIDI 设备校准流程
--source <模式>  # 覆盖输入源配置：可选 wheel (弯音轮)、knob (旋钮)、both (两者同时)
--move <模式>    # 覆盖移动模式配置：可选 velocity (速度模式)、displacement (位移模式)
```

`Ctrl+C` 或 C6 退出。进游戏前先把窗口焦点切到游戏。

## 配置
  您可在 `config.py` 任意修改配置。请在调整后重启程序。
  除了下面的介绍，还有很多可配置项。`config.py`中的注释解释了每个参数的作用。

  ### 设备选择

  在配置区设置 `MIDI_DEVICE_NAME` 指定设备名称关键字，
  程序会优先连接名称包含该字符串的 MIDI 设备（不区分大小写）；
  若未找到或留空，则自动选择（默认第一个端口）。

  ```python
  MIDI_DEVICE_NAME = "MiniLab"   # 例
  ```

  ### 按键映射
  以下是默认`NOTE_MAP` ，可自由修改：
  ```python
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
  ```
  “退出程序” 的按键映射需要单独修改 `QUIT_NOTE`。

  ### 鼠标控制
  * *输入来源（`VIEW_SOURCE`）*
    * `wheel`：弯音轮控制左右，Mod 轮控制上下
    * `knob`：两个旋钮分别控制左右 / 上下（默认 CC74 / CC71）
    * `both`：转轮与旋钮同时生效，移动量叠加
  * *移动方式（`MOVE_MODE`）*
    * `velocity`（速度）：控件偏离中心的量 = 转动速度，推住持续转、松手即停
    * `displacement`（位移）：控件转动量 = 视角位移，转多少偏多少、不转不动

## 校准

若视角只往一个方向转或范围不对，把 `CALIBRATE_ON_START` 改为 `True` 运行，
按提示把用于操控的弯音轮、Mod 轮推到底、旋钮转到底，根据打印范围修正中心值与 CC 号。

## 常见问题

* **在桌面环境下有效，但在游戏中无效**：请禁用游戏的 “原始输入” 功能，并在窗口模式下进行测试。
* **弯音轮旋转错误**：详见“校准”
* **鼠标移动过快 / 过慢**：在配置区中调整相应的 `*_VEL` 或 `*_DISP` 增益。
* **因 MIDI 设备范围过窄导致无法触发动作**：
  点击 MIDI 设备上的 OCT+ 或 OCT- 按钮，确保 MIDI 设备内包括 C4~C6，或者自行更改配置脚本。
* **macOS**：在 “辅助功能与输入监视” 下允许终端 / Python。
* **Linux**：Wayland 可能会阻止模拟输入；请使用 X11。

## 免责声明

* 本工具仅在操作系统层面重映射输入，不含自动瞄准、宏或任何作弊逻辑。
* 是否可在多人服务器使用由该服务器规则决定，
* 若因为使用本项目内容导致被服务器处罚 / 封禁等，使用者自行承担责任。
* 本项目仅供娱乐 / 学习。
* 本项目测试范围有限，可能会出现大量问题。*默认参数针对 MiniLab 3，最初用于 Minecraft Java 版。
* 本项目部分内容由人工智能辅助创建。

---

# English

EZMidiGamer simply turns any MIDI controller into system mouse/keyboard input, so you can play any game with keys, wheels and knobs.

*Please modify the configuration in `config.py` yourself during the first use.*

*If you are not sure about the range of your pitch bend wheel or knob, see "Calibration".*

## Features

* **Knobs and wheels control mouse movement**
  * 3 input source options and 2 move mode options (velocity, displacement), ensuring a smooth gaming experience (see "Mouse control" for details)
* **Custom note mapping**
  * Freely map any key, including special keys like Esc and the mouse scroll wheel
* Does not modify game files; equivalent to using a gamepad/joystick
* Written in Python with a simple design; configurations can be adjusted quickly

## How it works

```
MIDI controller ──MIDI messages──> poll loop ──> simulated mouse/keyboard ──> game
```

The script reads MIDI messages via [mido](https://github.com/mido/mido) and polls the 
control state every `POLL_INTERVAL` (0.01) seconds, then simulates mouse/keyboard input 
via [pynput](https://github.com/moses-palmer/pynput).

## Requirements

* Python 3.8+
* Any MIDI controller
* Windows / macOS / Linux

> On Windows mido's Pygame backend is used (pre-built wheels, no C compiler needed).

## Install

```
git clone https://github.com/zlsslz/EZMidiGamer.git
cd EZMidiGamer
python -m pip install -r requirements.txt
python EZMidiGamer.py --list      # confirm the controller is detected
```

## Usage

```
python EZMidiGamer.py
```

Available command-line arguments (temporarily override the config file):

```
--list           # list all available MIDI input ports and exit
--port <index>   # force a MIDI port index (see --list), e.g. --port 1
--debug          # enable debug mode
--no-calibrate   # force-skip the startup MIDI device calibration
--source <mode>  # override input source: wheel, knob, both
--move <mode>    # override move mode: velocity, displacement
```

Press `Ctrl+C` or C6 to quit. Focus the game window before playing.

## Configuration

You can modify any configuration in `config.py`. 
Please restart the program after changes. 
Besides the items introduced below, there are many more configurable options; 
the comments in `config.py` explain each parameter.

### Device selection

Set `MIDI_DEVICE_NAME` in the configuration area to specify a device name keyword: 
the program will prefer the first MIDI port whose name contains that string (case-insensitive). 
If no port matches (or it is left empty), it falls back to automatic selection (the first port).

```python
MIDI_DEVICE_NAME = "MiniLab"   # e.g.
```

### Note mapping

The default `NOTE_MAP` is shown below; feel free to modify it:

```python
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
```

The quit note must be set separately via `QUIT_NOTE`.

### Mouse control

* *Input source (`VIEW_SOURCE`)*
  * `wheel`: pitch-bend wheel for left/right, mod wheel for up/down
  * `knob`: two knobs for left/right and up/down (default CC74 / CC71)
  * `both`: wheel and knob active at once; their motion is added
* *Move mode (`MOVE_MODE`)*
  * `velocity`: off-center amount = rotation speed; hold to keep turning, release to stop
  * `displacement`: amount you move the control = camera displacement; no input => no motion

## Calibration

If the camera only turns one way or the ranges look wrong, set `CALIBRATE_ON_START` to `True` and run it; 
follow the prompts to push the pitch bend and mod wheels to the ends and turn the knobs through their full range, 
then fix the center values and CC numbers from the printed ranges.

## Common problems

* **Effective in desktop environment but ineffective in games**: 
  Disable the "Raw Input" function in the game and test in windowed mode.
* **Pitch bend wheel rotation error**: See "Calibration".
* **Mouse movement too fast / too slow**: 
  Adjust the corresponding `*_VEL` or `*_DISP` gains in the configuration area.
* **Failure to trigger actions due to the narrow range of MIDI devices**: 
  Click the OCT+ or OCT- button on the MIDI device to ensure that 
  C4~C6 are included in the device range, or modify the configuration script yourself.
* **macOS**: Allow Terminal / Python under "Accessibility & Input Monitoring".
* **Linux**: Wayland may block simulated input; use X11.

## Disclaimer

* This tool only remaps input at the OS level and contains no aim assist, macros or cheating logic.
* Whether it is allowed on multiplayer servers is governed by those servers' rules.
* If the user is punished / banned by the server due to the use of this project, 
  the user shall bear the responsibility on their own.
* This project is for entertainment / learning purposes only.
* The testing scope of this project is limited; a large number of issues may arise. 
  Defaults are tuned for the MiniLab 3; originally built for Minecraft Java Edition.
* Part of this project was created with AI assistance.

## License

[GNU General Public License v3.0](LICENSE)
