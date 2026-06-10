# 不一样的五子棋

这是一个支持"打子"规则的五子棋项目，包含桌面 UI 和终端模式。

## 目录结构

```
gomoku-re/
├── main.py              # 唯一启动脚本，根据参数选择 GUI 或 CLI
├── README.md
├── LICENSE
├── gomoku_config.json   # 用户配置（AI 难度、棋盘大小、速度、主题等）
├── gomoku_save.json     # 存档文件
├── gomoku/              # 内部包
│   ├── __init__.py       # 模块导出
│   ├── board.py          # 棋盘数据结构、连线检测、增量评估缓存、五子威胁缓存
│   ├── game.py           # 游戏状态、规则（落子/回收/替换）、悔棋、序列化、计时器
│   ├── ai.py             # AI 三挡难度（简单/中等/困难），含五子周期模拟
│   ├── cli.py            # 命令行交互（支持 undo/save/load/quit）
│   └── ui.py             # Tkinter 桌面图形界面（悔棋/步数历史/调速/计时器/主题/热键提示/存档读档/确认弹窗/对局统计/重新开始/窗口缩放）
└── tests/               # 单元测试（pytest，65 个）
    ├── test_board.py
    ├── test_game.py
    └── test_ai.py
```

## 规则

- 先让自己连成 5 棋子的一方，不直接获胜。
- 连线后回收这条 5 棋的棋子，并用自己的一颗棋子替换对方的一颗棋子。
- 如果替换后再次出现 5 棋连线，则继续重复该过程，直到无连线或无棋可换。
- 否则轮到对方落子。
- 先把棋子下完的一方判输。

## 玩法

- 运行 `uv run main.py`（或 `python main.py`）：默认启动桌面 UI（如果系统支持 `tkinter`）。
- 运行 `uv run main.py cli`（或 `python main.py cli`）：强制进入命令行模式。
- 支持人机对战，AI 有简单、中等、困难三种难度。
- 支持 AI vs AI 观战模式（可调速/暂停）。
- 坐标格式支持 `A1` 或 `1 1`。
- 桌面 UI 支持：悔棋（Ctrl+Z）、步数历史、双方计时、AI 速度调节、主题切换（默认/森林/暖阳）、热键提示（按 `?` 查看）、落子闪烁动画、存档读档（Ctrl+S/Ctrl+L）、退出确认、对局统计弹窗、重新开始、全屏/窗口切换（默认 1200×800，最小 900×640）。
- 终端 CLI 支持：AI 思考提示（"AI 思考中…"）显示。
- 命令行中支持 `undo` / `save` / `load` / `quit` 命令。

## 运行环境

- Python 3.8+
- 若需要桌面界面，请确保系统已安装并启用 `tkinter`。
- 推荐使用 [uv](https://docs.astral.sh/uv/) 管理项目：`uv run main.py` 自动管理虚拟环境与依赖。

## 示例

```bash
uv run main.py
uv run main.py cli
# 或直接用 python：
python main.py
python main.py cli
```

## 测试

```bash
uv run pytest
# 或直接用 python：
pytest
```

（65 个测试用例）

## 性能

| AI 难度 | 平均每步耗时 |
|---------|-------------|
| 简单    | < 1ms       |
| 中等    | ~2ms        |
| 困难    | ~17ms       |

（15×15 棋盘，约 20 枚棋子时测量）

## 开发说明

- `board.py` — 棋盘数据结构、连线检测算法，带空位/棋子/玩家位置/增量潜力四层缓存 + 五子威胁惰性缓存，`_update_potential_around` 限 5 步
- `game.py` — 游戏状态与规则管理，含悔棋历史栈、JSON 序列化、双方计时、配置持久化，提供 `do_placement`/`do_replacement` 封装落子+日志+回收检测
- `ai.py` — AI 评估函数与选子策略，三挡难度逐级递进，hard 含两轮筛选 + 链模拟（候选从 30 缩至 20）；`select_ai_replacement` 提供 `quick=True` 轻量版用于模拟内部；`_score_all_moves` 遇必成五连时提前返回
- `cli.py` — 命令行交互界面，支持 undo/save/load/quit，含替换循环、AI 思考提示
- `ui.py` — 桌面图形界面，含悔棋、步数历史列表（增量追加）、AI 速度滑块、暂停、计时器、全屏切换（1200×800 默认窗口，最小 900×640）、3 套主题（实时预览）、热键提示（`?`）、落子闪烁动画、增量棋盘渲染、`_draw_highlights` 缓存、`_layout_changed` 两遍法预留坐标标签空间、存档读档（Ctrl+S/L）、退出确认、对局统计弹窗、重新开始
- `main.py` — 启动方式选择

所有源文件均使用 UTF-8 编码。
