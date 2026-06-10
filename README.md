# 不一样的五子棋

这是一个支持"打子"规则的五子棋项目，包含桌面 UI 和终端模式。

## 目录结构

```
gomoku-re/
├── main.py              # 唯一启动脚本，根据参数选择 GUI 或 CLI
├── README.md
├── LICENSE
├── gomoku/              # 内部包
│   ├── __init__.py       # 模块导出
│   ├── board.py          # 棋盘数据结构、坐标系统、连线检测（带空位缓存）
│   ├── game.py           # 游戏状态、规则（落子/回收/替换）、悔棋、序列化
│   ├── ai.py             # AI 三挡难度（简单/中等/困难），含五子周期模拟
│   ├── cli.py            # 命令行交互（支持 undo/save/load/quit）
│   └── ui.py             # Tkinter 桌面图形界面（含坐标标注）
└── tests/               # 单元测试（pytest）
    ├── test_board.py
    ├── test_game.py
    └── test_ai.py
```

## 规则

- 先让自己连成 5 棋子的一方，不直接获胜。
- 连线后回收这条 5 棋的棋子，并用自己的一颗棋子替换对方的一颗棋子。
- 如果替换后再次出现 5 棋连线，则继续重复该过程。
- 否则轮到对方落子。
- 先把棋子下完的一方判输。

## 玩法

- 运行 `python main.py`：默认启动桌面 UI（如果系统支持 `tkinter`）。
- 运行 `python main.py cli`：强制进入命令行模式。
- 支持人机对战，AI 有简单、中等、困难三种难度。
- 支持 AI vs AI 观战模式。
- 坐标格式支持 `A1` 或 `1 1`。
- 命令行中支持 `undo` / `save` / `load` / `quit` 命令。

## 运行环境

- Python 3.8+
- 若需要桌面界面，请确保系统已安装并启用 `tkinter`。

## 示例

```bash
python main.py
python main.py cli
```

## 测试

```bash
pytest
```

## 开发说明

- `board.py` — 棋盘数据结构、连线检测算法，带空位缓存和棋子计数缓存
- `game.py` — 游戏状态与规则管理，含悔棋历史栈和 JSON 序列化
- `ai.py` — AI 评估函数与选子策略，三挡难度逐级递进，hard 含两轮筛选
- `cli.py` — 命令行交互界面，支持 undo/save/load/quit
- `ui.py` — 桌面图形界面样式与布局，含棋盘坐标标注
- `main.py` — 启动方式选择

所有源文件均使用 UTF-8 编码。
