# EZMidiGamer

**[中文](#中文) | [English](#english)**

简单地把任意 MIDI 控制器变成系统鼠标 / 键盘输入，
从而用琴键、弯音轮、旋钮来操作任意游戏。
默认参数针对 MiniLab 3，最初用于 Minecraft Java 版。

Simply turn any MIDI controller into system mouse/keyboard input, 
so you can play any game with keys, wheels and knobs.
Originally built for Minilab3 in Minecraft Java Edition.


请在第一次使用时在python文件中自行修改配置内容。
若不清楚您的弯音轮或旋钮的范围，详见 “校准”。

Please modify the configuration content in the file yourself during the first use.
If you are not sure about the range of your bend tone wheel or knob, 
please refer to "Calibration" for details.

---

<a name="中文"></a>
## 中文

### 功能特性

- **视角输入来源（VIEW_SOURCE）**
  - `wheel`：弯音轮控制左右，Mod 轮控制上下
  - `knob`：两个旋钮分别控制左右 / 上下
  - `both`：转轮与旋钮同时生效，移动量叠加
- **视角移动方式（MOVE_MODE）**
  - `velocity`（速度）：控件偏离中心的量 = 转动速度
  - `displacement`（位移）：控件转动量 = 视角位移
- 琴键自定义映射：移动、跳跃、潜行、背包、切换人称、鼠标左右键等
- 固定频率轮询
- 不更改游戏文件
- 由 Python 编写，原理简单，可快速修改配置

### 工作原理

```
MIDI 控制器 ──MIDI 消息──> 轮询主循环 ──> 模拟鼠标/键盘 ──> 游戏
```

脚本通过 [mido](https://github.com/mido/mido) 读取 MIDI 消息，每隔
`POLL_INTERVAL` 秒轮询一次控件状态，再通过
[pynput](https://github.com/moses-palmer/pynput) 模拟鼠标 / 键盘输入。

### 环境要求

- Python 3.8+
- 任意 MIDI 控制器
- Windows / macOS / Linux

> Windows 默认使用 mido 的 Pygame 后端，有预编译包，无需 C 编译器。

### 安装

```bash
git clone https://github.com/zlsslz/EZMidiGamer.git
cd EZMidiGamer
python -m pip install -r requirements.txt
python EZMidiGamer.py --list      # 确认能识别控制器
```

### 使用

```bash
python EZMidiGamer.py                                   # 默认配置
python EZMidiGamer.py --source wheel --move velocity    # 转轮 + 速度
python EZMidiGamer.py --source knob  --move displacement
python EZMidiGamer.py --source both                     # 转轮与旋钮同时生效
```

`Ctrl+C` 退出。进游戏前先把窗口焦点切到游戏。

### 默认按键映射

| MIDI 音符 | 音高 | 动作 |
|---|---|---|
| 60 | C4 | A |
| 61 | C#4 | 鼠标左键 |
| 62 | D4 | W |
| 63 | D#4 | 鼠标右键 |
| 64 | E4 | D |
| 65 | F4 | S |
| 66 | F#4 | 空格（跳）|
| 67 | G4 | 左 Shift（潜行）|
| 72 | C5 | Esc |
| 74 | D5 | E（背包）|
| 76 | E5 | F5（切换人称）|

修改脚本顶部 `NOTE_MAP` 即可自定义。

### 校准

若视角只往一个方向转或范围不对，把 `CALIBRATE_ON_START` 改为 `True` 运行，
按提示把弯音轮、Mod 轮推到底、旋钮转到底，根据打印范围修正中心值与 CC 号。
实时查看原始值：`python EZMidiGamer.py --debug`。

### 常见问题

- **在桌面环境下有效，但在游戏中无效**：请禁用游戏的“原始输入”功能，并在窗口模式下进行测试。
- **弯音轮旋转错误**：将 CALIBRATE_ON_START 更改为 'True' ，
  运行校准以修正中心值。随后可以根据获得的数据自行写进配置区。
- **鼠标移动过快/过慢**：在配置区中调整相应的`*_VEL`或`*_DISP`增益。
- **因MIDI设备范围过窄导致无法触发动作**：
  点击MIDI设备上的 OCT+ 或 OCT- 按钮，确保MIDI设备内包括C4~C6，或者自行更改配置脚本。
- **macOS**：在“辅助功能与输入监视”下允许终端/Python。
- **Linux**：Wayland可能会阻止模拟输入；请使用X11。

### 免责声明

本工具仅在操作系统层面重映射输入，不含自动瞄准、宏或任何作弊逻辑。
是否可在多人服务器使用由该服务器规则决定，
若因为使用本项目内容导致被服务器处罚/封禁等，使用者自行承担责任。
本项目仅供娱乐 / 学习。
本项目测试范围有限，可能会出现大量问题。
本项目部分内容由人工智能辅助创建。

### 开源协议

[GNU General Public License v3.0](LICENSE)

---

<a name="english"></a>
## English

### Features

- **Camera input source (VIEW_SOURCE)**
  - `wheel`: pitch-bend wheel for left/right, mod wheel for up/down
  - `knob`: two knobs for left/right and up/down (default CC74 / CC71)
  - `both`: wheel and knob active at once; their motion is added
- **Camera move mode (MOVE_MODE)**
  - `velocity`: off-center amount = rotation speed; hold to keep turning, release to stop
  - `displacement`: amount you move the control = camera displacement; no input => no motion
- Custom note mapping: movement, jump, sneak, inventory, perspective toggle, mouse buttons
- Fixed-rate polling
- Does not modify game files; equivalent to using a gamepad/joystick
- Written in Python with simple principle, allowing for quick modification of configurations

### How it works

```
MIDI controller ──MIDI messages──> poll loop ──> simulated mouse/keyboard ──> game
```

[mido](https://github.com/mido/mido) reads MIDI messages; the loop polls control
state every `POLL_INTERVAL` seconds and
[pynput](https://github.com/moses-palmer/pynput) simulates mouse/keyboard input.

### Requirements

- Python 3.8+
- Any MIDI controller (defaults for MiniLab 3)
- Windows / macOS / Linux

> On Windows mido's Pygame backend is used (pre-built wheels, no C compiler needed).

### Install

```bash
git clone https://github.com/zlsslz/EZMidiGamer.git
cd EZMidiGamer
python -m pip install -r requirements.txt
python EZMidiGamer.py --list
```

### Usage

```bash
python EZMidiGamer.py
python EZMidiGamer.py --source wheel --move velocity
python EZMidiGamer.py --source knob  --move displacement
python EZMidiGamer.py --source both
```

Press `Ctrl+C` to quit. Focus the game window before playing.

### Default note mapping

| MIDI note | Note | Action |
|---|---|---|
| 60 | C4 | A |
| 61 | C#4 | mouse left |
| 62 | D4 | W |
| 63 | D#4 | mouse right |
| 64 | E4 | D |
| 65 | F4 | S |
| 66 | F#4 | Space (jump) |
| 67 | G4 | Left Shift (sneak) |
| 72 | C5 | Esc |
| 74 | D5 | E (inventory) |
| 76 | E5 | F5 (perspective) |

Edit `NOTE_MAP` at the top of the script to customize.

### Calibration

If the camera only turns one way or ranges look wrong, set `CALIBRATE_ON_START`
to `True`, move every control through its full range when prompted, then fix the
centers/CC numbers from the printed ranges. For live values:
`python EZMidiGamer.py --debug`.

### Common problems

- **Effective in desktop environment but ineffective in games**: 
  Please disable the "Raw Input" function in games and test in windowed mode.
- **Bend tone wheel rotation error**: Change CALIBRATE_ON_START to 'True', 
  run calibration to correct the center value. Subsequently, 
  you can manually enter the obtained data into the configuration area.
- **Mouse movement too fast/too slow**: 
  Adjust the corresponding `*_VEL` or `*_DISP` gains in the configuration area.
- **Failure to trigger actions due to the narrow range of MIDI devices**:
 Click the OCT+ or OCT- button on the MIDI device
 to ensure that C4~C6 is included in the MIDI device, 
 or modify the configuration script yourself.
- **macOS**: Enable Terminal/Python under "Accessibility & Input Monitoring".
- **Linux**: Wayland may prevent simulated input; please use X11.

### Disclaimer

This tool only remaps input at the OS level and contains no aim assist, 
macros or cheating logic. 
Whether it is allowed on multiplayer servers is governed by those servers' rules; 
If the user is punished/blocked by the server due to the use of the this project, 
the user shall bear the responsibility on their own.
The testing scope of this project is limited, a large number of issues may arise.
AI assisted in this project.

### License

[GNU General Public License v3.0](LICENSE)
