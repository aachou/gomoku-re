try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox
except ImportError:
    tk = None
    tkfont = None
    messagebox = None

import json
import os
import time
import traceback

from .game import Game, PLAYER_NAMES, STARTING_STONES, SAVE_FILE, save_config, load_config, save_stats, load_stats, compute_game_stats
from .board import BOARD_SIZE
from .ai import select_ai_move, select_ai_replacement

THEMES = {
    '默认': {
        'bg_color': '#e2e8f0', 'card_bg': '#f1f5f9', 'surface_bg': '#f1f5f9',
        'panel_bg': '#e2e8f0', 'board_bg': '#d6d9e6', 'accent': '#3b82f6',
        'accent_soft': '#93c5fd', 'text_main': '#0f172a', 'text_secondary': '#475569',
    },
    '森林': {
        'bg_color': '#d4e6c3', 'card_bg': '#e8f5e1', 'surface_bg': '#e8f5e1',
        'panel_bg': '#d4e6c3', 'board_bg': '#c8dbb5', 'accent': '#2d7d46',
        'accent_soft': '#81c784', 'text_main': '#1a3d2b', 'text_secondary': '#3e6b4e',
    },
    '暖阳': {
        'bg_color': '#fce4c8', 'card_bg': '#fff3e0', 'surface_bg': '#fff3e0',
        'panel_bg': '#fce4c8', 'board_bg': '#f5dcc3', 'accent': '#d4783b',
        'accent_soft': '#f0b27a', 'text_main': '#3e2723', 'text_secondary': '#6d4c41',
    },
}

if tk is not None:
    class GameUI:
        def __init__(self):
            self.root = tk.Tk()
            self.root.withdraw()
            self.root.title('不一样的五子棋')
            config = load_config()
            self._theme_name = config.get('theme', '默认')
            self._apply_theme()
            self.game = Game()
            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self.mode_var = tk.StringVar(value='pvp')
            self.side_var = tk.StringVar(value='1')
            self.level_var = tk.StringVar(value='medium')
            self.theme_var = tk.StringVar(value=self._theme_name)
            self.status_var = tk.StringVar()
            self.starting_stones_var = tk.IntVar(value=STARTING_STONES)
            self.board_size_var = tk.IntVar(value=BOARD_SIZE)
            self.ai_delay_var = tk.IntVar(value=300)
            self.board_offset_x = 0
            self.board_offset_y = 0
            self.fullscreen = True
            self._windowed_geometry = '1200x800'
            self._paused = False
            self._timer_job = None
            self._hotkeys_shown = False
            self._stones_dirty = False
            self._highlight_color = '#ef4444'
            self._in_game = False
            self._highlight_cells = []
            self._ai_job = None
            self._ghost_stone_id = None
            self.replay_mode = False
            self.replay_index = 0
            self._live_state = None
            self.replay_timer_job = None
            self._start_canvas = None
            self.buttons = []
            self.level_var.set(config.get('ai_level', 'medium'))
            self.board_size_var.set(config.get('board_size', 15))
            self.starting_stones_var.set(config.get('starting_stones', 30))
            self.ai_delay_var.set(config.get('ai_delay_ms', 300))
            self.root.geometry('1200x800')
            self.root.minsize(900, 640)
            self._center_window()
            self.root.attributes('-fullscreen', True)
            font_families = set(tkfont.families()) if tkfont is not None else set()
            preferred_fonts = ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Segoe UI Variable', 'Segoe UI', 'Arial']
            self.ui_font = next((name for name in preferred_fonts if name in font_families), 'Arial')
            self.title_font = tkfont.Font(family=self.ui_font, size=28, weight='bold')
            self.header_font = tkfont.Font(family=self.ui_font, size=16, weight='bold')
            self.label_font = tkfont.Font(family=self.ui_font, size=12)
            self.button_font = tkfont.Font(family=self.ui_font, size=11, weight='bold')
            self.status_font = tkfont.Font(family=self.ui_font, size=12)
            self.small_font = tkfont.Font(family=self.ui_font, size=10)
            self.root.configure(bg=self.bg_color)
            self.root.option_add('*Font', self.label_font)
            self.root.bind('<Control-z>', lambda e: self.perform_undo())
            self.root.bind('<F11>', lambda e: self.toggle_fullscreen())
            self.root.bind('<Escape>', self._on_escape)
            self.root.bind('<Control-s>', self._save_game)
            self.root.bind('<Control-S>', self._save_game)
            self.root.bind('<Control-l>', self._load_game)
            self.root.bind('<Control-L>', self._load_game)
            self.root.bind('<Key-slash>', lambda e: self._toggle_hotkeys())
            self.root.bind('<Key-question>', lambda e: self._toggle_hotkeys())
            self.root.protocol('WM_DELETE_WINDOW', self._on_close)
            if hasattr(self.root, 'report_callback_exception'):
                self.root.report_callback_exception = self._on_tk_error
            self.build_start_screen()
            self.root.deiconify()

        def _apply_theme(self, theme_name=None):
            if theme_name:
                self._theme_name = theme_name
            colors = THEMES.get(self._theme_name, THEMES['默认'])
            self.bg_color = colors['bg_color']
            self.card_bg = colors['card_bg']
            self.surface_bg = colors['surface_bg']
            self.panel_bg = colors['panel_bg']
            self.board_bg = colors['board_bg']
            self.accent = colors['accent']
            self.accent_soft = colors['accent_soft']
            self.text_main = colors['text_main']
            self.text_secondary = colors['text_secondary']

        def _preview_theme(self):
            self._apply_theme(self.theme_var.get())
            self.root.configure(bg=self.bg_color)
            self.build_start_screen()

        def _toggle_hotkeys(self):
            self._hotkeys_shown = not self._hotkeys_shown
            if self._hotkeys_shown:
                self._show_hotkeys()
            else:
                self._hide_hotkeys()

        def _show_hotkeys(self):
            self._hide_hotkeys()
            self._hotkey_frame = tk.Frame(self.root, bg=self.card_bg, bd=1, relief='solid', highlightbackground=self.accent, highlightthickness=2)
            self._hotkey_frame.place(relx=0.5, rely=0.5, anchor='center')
            tk.Label(self._hotkey_frame, text='快捷键', font=self.header_font, bg=self.card_bg, fg=self.text_main).pack(pady=(10, 4), padx=20)
            shortcuts = [
                ('Ctrl+Z', '悔棋'),
                ('Ctrl+S', '保存'),
                ('Ctrl+L', '载入'),
                ('F11', '切换全屏'),
                ('Esc', '返回主菜单'),
                ('?', '隐藏提示'),
            ]
            for key, desc in shortcuts:
                row = tk.Frame(self._hotkey_frame, bg=self.card_bg)
                row.pack(fill='x', padx=16, pady=2)
                tk.Label(row, text=key, font=self.small_font, bg=self.card_bg, fg=self.accent, width=10, anchor='w').pack(side='left')
                tk.Label(row, text=desc, font=self.small_font, bg=self.card_bg, fg=self.text_secondary, anchor='w').pack(side='left', padx=8)
            tk.Button(self._hotkey_frame, text='关闭', command=self._hide_hotkeys, font=self.button_font, bg=self.accent, fg='white', relief='flat', padx=16, pady=6, bd=0).pack(pady=(8, 10))

        def _hide_hotkeys(self):
            if hasattr(self, '_hotkey_frame') and self._hotkey_frame:
                self._hotkey_frame.destroy()
                self._hotkey_frame = None
            self._hotkeys_shown = False

        def _start_screen_wheel(self, event):
            if self._start_canvas:
                try:
                    self._start_canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
                except tk.TclError:
                    self._start_canvas = None

        def _on_escape(self, event=None):
            if not self._in_game:
                return
            if self.game_over:
                self.build_start_screen()
                return
            if messagebox.askyesno('确认', '返回主菜单？游戏将自动保存，下次可继续。'):
                self._save_game()
                self.build_start_screen()

        def _restart_game(self):
            if not self._in_game:
                return
            if self.game_over:
                self.start_game()
                return
            if messagebox.askyesno('确认', '重新开始当前对局？游戏将自动保存，下次可继续。'):
                self._save_game()
                self.start_game()

        def _confirm_back_to_menu(self):
            if self.game_over:
                self.build_start_screen()
                return
            if messagebox.askyesno('确认', '返回主菜单？游戏将自动保存，下次可继续。'):
                self._save_game()
                self.build_start_screen()

        def _on_close(self):
            if self._in_game:
                try:
                    with open(SAVE_FILE, 'w') as f:
                        json.dump(self.game.serialize(), f)
                except Exception:
                    pass
            self.root.destroy()

        def _on_tk_error(self, exc, val, tb):
            if self._in_game:
                self._save_game()
            traceback.print_exception(exc, val, tb)

        def _save_game(self, event=None):
            if not self._in_game:
                return
            try:
                with open(SAVE_FILE, 'w') as f:
                    json.dump(self.game.serialize(), f)
                self.status_var.set('游戏已保存。')
            except Exception:
                self.status_var.set('保存失败！')

        def _load_game(self, event=None):
            if not os.path.exists(SAVE_FILE):
                self.status_var.set('未找到存档。')
                return
            self._cancel_ai()
            try:
                with open(SAVE_FILE) as f:
                    data = json.load(f)
                self.game = Game.deserialize(data)
                self.waiting_replacement = False
                self.game_over = False
                self.last_move = None
                self._highlight_color = '#ef4444'
                self._stones_dirty = True
                self._highlight_cells = []
                self._in_game = True
                self.replay_mode = False
                self.replay_index = 0
                self._live_state = None
                self._cancel_replay_timer()
                self.build_game_ui()
                self.update_ui()
                self._refresh_log(full=True)
                self.status_var.set('游戏已载入。')
                if self.game.player_types[self.game.current] == 'ai':
                    self._schedule_ai(300)
            except Exception:
                self.status_var.set('载入失败！')

        def _persist_game_stats(self, winner):
            cur = compute_game_stats(self.game, winner)
            stats = load_stats()
            stats['total_games'] += 1
            stats['wins'][1] += cur['wins'][1]
            stats['wins'][2] += cur['wins'][2]
            stats['draws'] += cur['draws']
            stats['moves'][1] += cur['moves'][1]
            stats['moves'][2] += cur['moves'][2]
            stats['recoveries'][1] += cur['recoveries'][1]
            stats['recoveries'][2] += cur['recoveries'][2]
            stats['total_time'][1] += cur['total_time'][1]
            stats['total_time'][2] += cur['total_time'][2]
            save_stats(stats)

        def _show_game_stats(self, winner):
            self._persist_game_stats(winner)
            moves = len(self.game.move_log)
            b_moves = sum(1 for m in self.game.move_log if m['player'] == 1)
            w_moves = sum(1 for m in self.game.move_log if m['player'] == 2)
            b_rec = sum(m.get('recovered', 0) for m in self.game.move_log if m['player'] == 1)
            w_rec = sum(m.get('recovered', 0) for m in self.game.move_log if m['player'] == 2)
            b_time = self._format_time(self.game.timers[1])
            w_time = self._format_time(self.game.timers[2])
            msg = (
                f'总步数：{moves}\n'
                f'黑棋落子：{b_moves}，回收：{b_rec}，用时：{b_time}\n'
                f'白棋落子：{w_moves}，回收：{w_rec}，用时：{w_time}'
            )
            if winner:
                messagebox.showinfo('对局统计', f'{PLAYER_NAMES[winner]} 胜利！\n\n{msg}')
            else:
                messagebox.showinfo('对局统计', f'平局！\n\n{msg}')

        def _show_stats_dialog(self):
            stats = load_stats()
            if stats['total_games'] == 0:
                messagebox.showinfo('对局统计', '暂无对局记录。')
                return
            b_win_pct = stats['wins'][1] / stats['total_games'] * 100
            w_win_pct = stats['wins'][2] / stats['total_games'] * 100
            draw_pct = stats['draws'] / stats['total_games'] * 100
            b_avg_time = stats['total_time'][1] / max(stats['moves'][1], 1)
            w_avg_time = stats['total_time'][2] / max(stats['moves'][2], 1)
            msg = (
                f'总局数：{stats["total_games"]}\n\n'
                f'胜率\n'
                f'  黑棋：{stats["wins"][1]} 胜 ({b_win_pct:.1f}%)\n'
                f'  白棋：{stats["wins"][2]} 胜 ({w_win_pct:.1f}%)\n'
                f'  平局：{stats["draws"]} ({draw_pct:.1f}%)\n\n'
                f'落子\n'
                f'  黑棋：{stats["moves"][1]} 手\n'
                f'  白棋：{stats["moves"][2]} 手\n\n'
                f'回收\n'
                f'  黑棋：{stats["recoveries"][1]} 次\n'
                f'  白棋：{stats["recoveries"][2]} 次\n\n'
                f'平均每步用时\n'
                f'  黑棋：{self._format_time(b_avg_time)}\n'
                f'  白棋：{self._format_time(w_avg_time)}'
            )
            messagebox.showinfo('累计对局统计', msg)

        def build_start_screen(self):
            self._start_canvas = None
            self.root.bind_all('<MouseWheel>', self._start_screen_wheel)
            for widget in self.root.winfo_children():
                widget.destroy()
            self._in_game = False
            self._highlight_cells = []

            container = tk.Frame(self.root, bg=self.bg_color)
            container.pack(fill='both', expand=True)

            canvas = tk.Canvas(container, bg=self.bg_color, highlightthickness=0)
            scrollbar = tk.Scrollbar(container, orient='vertical', command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side='left', fill='both', expand=True)
            scrollbar.pack(side='right', fill='y')

            card = tk.Frame(canvas, bg=self.card_bg, bd=0, highlightbackground='#1e293b', highlightthickness=1, padx=20, pady=20)
            card.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
            card_win = canvas.create_window((10, 10), window=card, anchor='nw')
            canvas.bind('<Configure>', lambda e: canvas.itemconfig(card_win, width=e.width - 20))
            self._start_canvas = canvas
            self.root.bind_all('<MouseWheel>', self._start_screen_wheel)

            accent_bar = tk.Frame(card, bg=self.accent, height=4)
            accent_bar.pack(fill='x', side='top', pady=(0, 10))
            tk.Label(card, text='不一样的五子棋', font=self.title_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            tk.Label(card, text='未来风格对战 · AI 支持 · 自定义棋盘与棋子', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).pack(anchor='w', pady=(4, 12))

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 6))
            tk.Label(section, text='对战模式', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            opt_frame = tk.Frame(section, bg=self.card_bg)
            opt_frame.pack(anchor='w', pady=(4, 4))
            for text, value in [('双人', 'pvp'), ('人机', 'pve'), ('AI vs AI', 'pvai')]:
                tk.Radiobutton(opt_frame, text=text, variable=self.mode_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=12, pady=8, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=6)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 6))
            tk.Label(section, text='执棋方', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            side_frame = tk.Frame(section, bg=self.card_bg)
            side_frame.pack(anchor='w', pady=(4, 4))
            for text, value in [('黑棋', '1'), ('白棋', '2')]:
                tk.Radiobutton(side_frame, text=text, variable=self.side_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=12, pady=8, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=6)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 6))
            tk.Label(section, text='AI 难度', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            level_frame = tk.Frame(section, bg=self.card_bg)
            level_frame.pack(anchor='w', pady=(4, 4))
            for text, value in [('简单', 'simple'), ('中等', 'medium'), ('困难', 'hard')]:
                tk.Radiobutton(level_frame, text=text, variable=self.level_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=12, pady=8, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=6)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 6))
            tk.Label(section, text='主题', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            theme_frame = tk.Frame(section, bg=self.card_bg)
            theme_frame.pack(anchor='w', pady=(4, 4))
            for name in list(THEMES.keys()):
                tk.Radiobutton(theme_frame, text=name, variable=self.theme_var, value=name, command=self._preview_theme, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=12, pady=8, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=6)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 6))
            tk.Label(section, text='初始设置', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            fields = tk.Frame(section, bg=self.card_bg)
            fields.pack(anchor='w', pady=(4, 0))
            tk.Label(fields, text='棋子数：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=0, sticky='w', padx=4, pady=4)
            tk.Spinbox(fields, from_=5, to=500, textvariable=self.starting_stones_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=0, column=1, sticky='w', padx=4, pady=4)
            tk.Label(fields, text='棋盘大小：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=1, column=0, sticky='w', padx=4, pady=4)
            tk.Spinbox(fields, from_=5, to=99, textvariable=self.board_size_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=1, column=1, sticky='w', padx=4, pady=4)

            tk.Button(card, text='▶ START', command=self.start_game, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=22, pady=10, bd=0).pack(pady=(12, 0), fill='x')
            if os.path.exists(SAVE_FILE):
                tk.Button(card, text='▶ 继续上次游戏', command=self._load_game, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=22, pady=10, bd=0).pack(pady=(6, 0), fill='x')
            tk.Button(card, text='⛶ 全屏', command=self.toggle_fullscreen, font=self.button_font, bg=self.accent_soft, fg=self.text_main, activebackground='#93c5fd', activeforeground=self.text_main, relief='flat', padx=22, pady=10, bd=0).pack(pady=(6, 0), fill='x')
            tk.Button(card, text='📊 对局统计', command=self._show_stats_dialog, font=self.button_font, bg=self.panel_bg, fg=self.text_main, activebackground=self.surface_bg, activeforeground=self.text_main, relief='flat', padx=22, pady=10, bd=0).pack(pady=(6, 0), fill='x')
            tk.Button(card, text='退出游戏', command=self._on_close, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=22, pady=10, bd=0).pack(pady=(6, 0), fill='x')

        def start_game(self):
            size = int(self.board_size_var.get())
            starting = int(self.starting_stones_var.get())
            self.game = Game(size=size, starting_stones=starting)
            mode = self.mode_var.get()
            if mode == 'pve':
                human_side = int(self.side_var.get())
                ai_side = 3 - human_side
                self.game.player_types = {human_side: 'human', ai_side: 'ai'}
                self.game.ai_levels[ai_side] = self.level_var.get()
            elif mode == 'pvai':
                self.game.player_types = {1: 'ai', 2: 'ai'}
                self.game.ai_levels = {1: self.level_var.get(), 2: self.level_var.get()}
            else:
                self.game.player_types = {1: 'human', 2: 'human'}
                self.game.ai_levels = {1: None, 2: None}

            try:
                os.remove(SAVE_FILE)
            except Exception:
                pass
            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self._highlight_cells = []
            self._paused = False
            self._in_game = True
            self._cancel_ai()
            self.game._replay_snapshots.clear()
            self.game.save_replay_snapshot()
            self.replay_mode = False
            self.replay_index = 0
            self._live_state = None
            self._cancel_replay_timer()
            new_theme = self.theme_var.get()
            if new_theme != self._theme_name:
                self._apply_theme(new_theme)
                self.root.configure(bg=self.bg_color)
            save_config(
                ai_level=self.level_var.get(),
                board_size=size,
                starting_stones=starting,
                ai_delay_ms=self.ai_delay_var.get(),
                theme=self._theme_name,
            )
            self.build_game_ui()
            self.update_ui()

            if self.game.player_types[self.game.current] == 'ai':
                self._schedule_ai(300)

        def build_game_ui(self):
            self._start_canvas = None
            self.root.bind_all('<MouseWheel>', '')
            for widget in self.root.winfo_children():
                widget.destroy()

            top_frame = tk.Frame(self.root, bg=self.bg_color, pady=12, padx=18)
            top_frame.pack(fill='x')

            self.current_label = tk.Label(top_frame, font=self.header_font, bg=self.bg_color, fg=self.text_main)
            self.current_label.pack(side='left')
            self.supply_label = tk.Label(top_frame, font=self.label_font, bg=self.bg_color, fg=self.text_secondary)
            self.supply_label.pack(side='left', padx=24)
            self.timer_label = tk.Label(top_frame, font=self.label_font, bg=self.bg_color, fg=self.text_secondary)
            self.timer_label.pack(side='right', padx=10)

            center_frame = tk.Frame(self.root, bg=self.bg_color)
            center_frame.pack(fill='both', expand=True, padx=16)

            board_container = tk.Frame(center_frame, bg=self.panel_bg, bd=0, highlightthickness=1, highlightbackground='#cbd5e1')
            board_container.pack(side='left', fill='both', expand=True)

            self.canvas = tk.Canvas(board_container, bg=self.board_bg, highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.canvas.bind('<Button-1>', self.on_canvas_click)
            self.canvas.bind('<Configure>', lambda e: self.draw_board())
            self.canvas.bind('<Motion>', self._on_canvas_motion)
            self.canvas.bind('<Leave>', lambda e: self._remove_ghost_stone())
            self.cell_size = 24

            side_panel = tk.Frame(center_frame, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground='#cbd5e1', width=220)
            side_panel.pack(side='right', fill='y', padx=(8, 0))
            side_panel.pack_propagate(False)
            self.side_panel = side_panel

            tk.Label(side_panel, text='步数历史', font=self.header_font, bg=self.card_bg, fg=self.text_main).pack(pady=(10, 4))

            log_frame = tk.Frame(side_panel, bg=self.card_bg)
            log_frame.pack(fill='both', expand=True, padx=8, pady=4)
            self.log_listbox = tk.Listbox(log_frame, font=self.small_font, bg=self.surface_bg, fg=self.text_main, bd=0, highlightthickness=0, selectbackground=self.accent_soft)
            log_scroll = tk.Scrollbar(log_frame, orient='vertical', command=self.log_listbox.yview)
            self.log_listbox.configure(yscrollcommand=log_scroll.set)
            log_scroll.pack(side='right', fill='y')
            self.log_listbox.pack(fill='both', expand=True)

            ctrl_frame = tk.Frame(side_panel, bg=self.card_bg)
            ctrl_frame.pack(fill='x', padx=8, pady=8)
            tk.Label(ctrl_frame, text='AI 速度', font=self.small_font, bg=self.card_bg, fg=self.text_secondary).pack(anchor='w')
            speed_scale = tk.Scale(ctrl_frame, from_=50, to=2000, orient='horizontal', variable=self.ai_delay_var, font=self.small_font, bg=self.surface_bg, fg=self.text_main, bd=0, highlightthickness=0, showvalue=False)
            speed_scale.pack(fill='x')
            self.speed_label = tk.Label(ctrl_frame, text='', font=self.small_font, bg=self.card_bg, fg=self.text_secondary)
            self.speed_label.pack()
            self._update_speed_label()

            self.pause_btn = tk.Button(ctrl_frame, text='⏸ 暂停', command=self.toggle_pause, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', bd=0)
            self.pause_btn.pack(fill='x', pady=(6, 0))

            self.status_label = tk.Label(self.root, textvariable=self.status_var, font=self.status_font, bg=self.surface_bg, fg=self.text_main, wraplength=760, justify='left', bd=0, relief='flat', padx=18, pady=14)
            self.status_label.pack(fill='x', pady=(0, 10), padx=16)

            footer = tk.Frame(self.root, bg=self.bg_color, pady=14)
            footer.pack(fill='x')
            tk.Button(footer, text='↶ 悔棋', command=self.perform_undo, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='⛶ 全屏', command=self.toggle_fullscreen, font=self.button_font, bg=self.accent_soft, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='↻ 重新开始', command=self._restart_game, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='⟳ 回放', command=self._enter_replay_mode, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='📊 统计', command=self._show_stats_dialog, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='← 主菜单', command=self._confirm_back_to_menu, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)

        def _update_speed_label(self):
            val = self.ai_delay_var.get()
            self.speed_label.config(text=f'{"慢" if val > 1000 else "中" if val > 300 else "快"} ({val}ms)')

        def _cancel_ai(self):
            if self._ai_job:
                self.root.after_cancel(self._ai_job)
                self._ai_job = None

        def _schedule_ai(self, delay):
            self._cancel_ai()
            self._ai_job = self.root.after(delay, self._ai_take_turn_wrapper)

        def _ai_take_turn_wrapper(self):
            self._ai_job = None
            self.ai_take_turn()

        def toggle_pause(self):
            self._paused = not self._paused
            self.pause_btn.config(text='▶ 继续' if self._paused else '⏸ 暂停')
            if not self._paused:
                if self.game.player_types[self.game.current] == 'ai' and not self.waiting_replacement and not self.game_over:
                    self._schedule_ai(100)

        def _layout_changed(self, w, h):
            cols = self.game.size
            rows = self.game.size
            raw_cell = max(6, min(w // cols, h // rows))
            fs_est = max(8, raw_cell // 2)
            off_est = raw_cell // 2 + 4
            margin_est = off_est + fs_est + 4
            available_w = max(1, w - 2 * margin_est)
            available_h = max(1, h - 2 * margin_est)
            cell_w = max(6, available_w // cols)
            cell_h = max(6, available_h // rows)
            new_cell_size = min(cell_w, cell_h)
            board_w = new_cell_size * cols
            board_h = new_cell_size * rows
            fs = max(8, new_cell_size // 2)
            off = new_cell_size // 2 + 4
            label_margin = off + fs + 4
            new_ox = max(label_margin, (w - board_w) // 2)
            new_oy = max(label_margin, (h - board_h) // 2)
            if (new_cell_size != self.cell_size or new_ox != self.board_offset_x or new_oy != self.board_offset_y):
                self.cell_size = new_cell_size
                self.board_offset_x = new_ox
                self.board_offset_y = new_oy
                return True
            return False

        def _draw_grid(self):
            cols = self.game.size
            rows = self.game.size
            board_w = self.cell_size * cols
            board_h = self.cell_size * rows
            fs = max(8, self.cell_size // 2)
            off = self.cell_size // 2 + 4
            self.canvas.create_rectangle(self.board_offset_x, self.board_offset_y, self.board_offset_x + board_w, self.board_offset_y + board_h, fill=self.board_bg, outline=self.accent_soft, width=2, tags='grid')
            for i in range(1, cols):
                x = self.board_offset_x + i * self.cell_size
                self.canvas.create_line(x, self.board_offset_y + 2, x, self.board_offset_y + board_h - 2, fill='#94a3b8', tags='grid')
            for j in range(1, rows):
                y = self.board_offset_y + j * self.cell_size
                self.canvas.create_line(self.board_offset_x + 2, y, self.board_offset_x + board_w - 2, y, fill='#94a3b8', tags='grid')
            for i in range(cols):
                x = self.board_offset_x + i * self.cell_size + self.cell_size // 2
                self.canvas.create_text(x, self.board_offset_y - off, text=chr(ord('A') + i), font=(self.ui_font, fs), fill='#475569', tags='grid')
            for j in range(rows):
                y = self.board_offset_y + j * self.cell_size + self.cell_size // 2
                self.canvas.create_text(self.board_offset_x - off, y, text=str(j + 1), font=(self.ui_font, fs), fill='#475569', tags='grid')
            self._draw_star_points()

        def _draw_star_points(self):
            if self.game.size < 15:
                return
            points = [(3,3),(3,7),(3,11),(7,3),(7,7),(7,11),(11,3),(11,7),(11,11)]
            r = max(3, self.cell_size // 6)
            for sx, sy in points:
                if sx >= self.game.size or sy >= self.game.size:
                    continue
                cx = self.board_offset_x + sx * self.cell_size + self.cell_size // 2
                cy = self.board_offset_y + sy * self.cell_size + self.cell_size // 2
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill='#475569', outline='', tags='grid')

        def _draw_stones(self):
            radius = int(self.cell_size * 0.42)
            highlight_radius = int(radius * 0.4)
            for y in range(self.game.size):
                for x in range(self.game.size):
                    cell = self.game.board.get(x, y)
                    if cell == 0:
                        continue
                    cx = self.board_offset_x + x * self.cell_size + self.cell_size // 2
                    cy = self.board_offset_y + y * self.cell_size + self.cell_size // 2
                    if cell == 1:
                        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#1f2937', outline='#64748b', width=1, tags='stone')
                        self.canvas.create_oval(cx - radius, cy - radius, cx - radius + 2 * highlight_radius, cy - radius + 2 * highlight_radius, fill='#475569', outline='', tags='stone')
                    elif cell == 2:
                        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#f8fafc', outline='#cbd5e1', width=1, tags='stone')
                        self.canvas.create_oval(cx - radius, cy - radius, cx - radius + 2 * highlight_radius, cy - radius + 2 * highlight_radius, fill='#ffffff', outline='', tags='stone')
            if self.last_move is not None:
                lx, ly = self.last_move
                cx = self.board_offset_x + lx * self.cell_size + self.cell_size // 2
                cy = self.board_offset_y + ly * self.cell_size + self.cell_size // 2
                self.canvas.create_oval(cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2, outline=self._highlight_color, width=2, tags='stone')

        def _draw_highlights(self):
            if self.waiting_replacement and self.game.player_types[self.game.current] == 'human':
                for x, y in self._highlight_cells:
                    x1 = self.board_offset_x + x * self.cell_size
                    y1 = self.board_offset_y + y * self.cell_size
                    self.canvas.create_rectangle(x1 + 2, y1 + 2, x1 + self.cell_size - 2, y1 + self.cell_size - 2, outline='#22c55e', width=3, tags='highlight')

        def draw_board(self):
            if not hasattr(self, 'canvas'):
                return
            self._remove_ghost_stone()
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 1 or h <= 1:
                return
            if self._layout_changed(w, h):
                self.canvas.delete('all')
                self._draw_grid()
                self._draw_stones()
            elif self._stones_dirty:
                self.canvas.delete('stone')
                self._draw_stones()
            self.canvas.delete('highlight')
            self._draw_highlights()
            self._stones_dirty = False

        def _reset_highlight(self):
            self._highlight_color = '#ef4444'
            if self.last_move is not None and hasattr(self, 'canvas'):
                self.canvas.delete('stone')
                self._draw_stones()

        def _center_window(self):
            self.root.update_idletasks()
            geo = self.root.geometry()
            import re
            m = re.match(r'(\d+)x(\d+)', geo)
            if m:
                w, h = int(m.group(1)), int(m.group(2))
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                x = max(0, (sw - w) // 2)
                y = max(0, (sh - h) // 2)
                self.root.geometry(f'+{x}+{y}')

        def toggle_fullscreen(self):
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self._windowed_geometry = self.root.geometry()
                self.root.attributes('-fullscreen', True)
            else:
                self.root.attributes('-fullscreen', False)
                self.root.geometry(self._windowed_geometry)
                self._center_window()

        def _format_time(self, seconds):
            m = int(seconds // 60)
            s = int(seconds % 60)
            return f'{m:02d}:{s:02d}'

        def _update_timer_display(self):
            t1 = self._format_time(self.game.timers[1])
            t2 = self._format_time(self.game.timers[2])
            self.timer_label.config(text=f'黑 {t1}  白 {t2}')

        def update_ui(self):
            self.draw_board()
            self.current_label.config(text=f'当前: {PLAYER_NAMES[self.game.current]}')
            self.supply_label.config(text=f'黑棋: {self.game.supply[1]}  白棋: {self.game.supply[2]}')
            self._update_timer_display()
            if not self.waiting_replacement:
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 请落子。')

        def _format_log_entry(self, entry):
            p = PLAYER_NAMES[entry['player']]
            pos = f'{chr(ord("A") + entry["x"])}{entry["y"] + 1}'
            if entry['action'] == 'place':
                text = f'{p} 落子 {pos}'
                if entry['recovered']:
                    text += f' 回收{entry["recovered"]}'
            else:
                text = f'{p} 替换 {pos}'
            return text

        def _refresh_log(self, full=False):
            if full:
                self.log_listbox.delete(0, 'end')
                for entry in self.game.move_log:
                    self.log_listbox.insert('end', self._format_log_entry(entry))
            else:
                self.log_listbox.insert('end', self._format_log_entry(self.game.move_log[-1]))
            self.log_listbox.see('end')

        def on_canvas_click(self, event):
            if self.game_over or self.replay_mode or self.game.player_types[self.game.current] == 'ai':
                return
            x = (event.x - getattr(self, 'board_offset_x', 0)) // self.cell_size
            y = (event.y - getattr(self, 'board_offset_y', 0)) // self.cell_size
            if x < 0 or y < 0 or x >= self.game.size or y >= self.game.size:
                return
            if self.waiting_replacement:
                if self.game.board.get(x, y) == 3 - self.game.current:
                    self.perform_replacement(x, y)
                    self.update_ui()
            else:
                if self.game.board.is_empty(x, y) and self.game.supply[self.game.current] > 0:
                    self.perform_placement(x, y)
                    self.update_ui()

        def _on_canvas_motion(self, event):
            if self.game_over or self.replay_mode:
                self._remove_ghost_stone()
                return
            if self.game.player_types[self.game.current] == 'ai' or self.waiting_replacement:
                self._remove_ghost_stone()
                return
            x = (event.x - self.board_offset_x) // self.cell_size
            y = (event.y - self.board_offset_y) // self.cell_size
            if x < 0 or y < 0 or x >= self.game.size or y >= self.game.size:
                self._remove_ghost_stone()
                return
            if self.game.board.get(x, y) != 0:
                self._remove_ghost_stone()
                return
            cx = self.board_offset_x + x * self.cell_size + self.cell_size // 2
            cy = self.board_offset_y + y * self.cell_size + self.cell_size // 2
            radius = int(self.cell_size * 0.42)
            color = '#1f2937' if self.game.current == 1 else '#f8fafc'
            self._remove_ghost_stone()
            self._ghost_stone_id = self.canvas.create_oval(
                cx - radius, cy - radius, cx + radius, cy + radius,
                fill=color, outline='', stipple='gray25', tags='ghost'
            )

        def _remove_ghost_stone(self):
            if self._ghost_stone_id:
                try:
                    self.canvas.delete(self._ghost_stone_id)
                except Exception:
                    pass
                self._ghost_stone_id = None

        def _cancel_replay_timer(self):
            if self.replay_timer_job:
                self.root.after_cancel(self.replay_timer_job)
                self.replay_timer_job = None

        def _enter_replay_mode(self):
            if len(self.game._replay_snapshots) < 2:
                self.status_var.set('当前没有可供回放的历史记录。')
                return
            self._live_state = self.game.serialize()
            self.replay_mode = True
            self.replay_index = 0
            self._remove_ghost_stone()
            self._build_replay_controls()
            self._update_replay_display()

        def _exit_replay_mode(self):
            self._cancel_replay_timer()
            self.replay_mode = False
            if self._live_state:
                self.game = Game.deserialize(self._live_state)
                self._live_state = None
            self.replay_index = 0
            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self._stones_dirty = True
            self._highlight_cells = []
            if hasattr(self, 'replay_ctrl_frame') and self.replay_ctrl_frame:
                self.replay_ctrl_frame.destroy()
                self.replay_ctrl_frame = None
            self.log_listbox.pack(fill='both', expand=True)
            self.update_ui()
            self._refresh_log(full=True)
            self.status_var.set('已退出回放模式。')
            if self.game.player_types[self.game.current] == 'ai':
                self._schedule_ai(300)

        def _build_replay_controls(self):
            if hasattr(self, 'replay_ctrl_frame') and self.replay_ctrl_frame:
                self.replay_ctrl_frame.destroy()
            self.log_listbox.pack_forget()
            self.replay_ctrl_frame = tk.Frame(self.side_panel, bg=self.card_bg)
            self.replay_ctrl_frame.pack(fill='both', expand=True, padx=8, pady=4)
            tk.Label(self.replay_ctrl_frame, text='回放模式', font=self.header_font, bg=self.card_bg, fg=self.accent).pack(pady=(4, 8))
            self.replay_progress_label = tk.Label(self.replay_ctrl_frame, font=self.label_font, bg=self.card_bg, fg=self.text_main)
            self.replay_progress_label.pack(pady=4)
            btn_frame = tk.Frame(self.replay_ctrl_frame, bg=self.card_bg)
            btn_frame.pack(pady=8)
            tk.Button(btn_frame, text='⏮', command=self._replay_prev, font=self.button_font, bg=self.accent, fg='white', relief='flat', padx=12, pady=8, bd=0, width=3).pack(side='left', padx=4)
            self.replay_play_btn = tk.Button(btn_frame, text='▶ 播放', command=self._replay_toggle_play, font=self.button_font, bg=self.accent_soft, fg=self.text_main, relief='flat', padx=12, pady=8, bd=0)
            self.replay_play_btn.pack(side='left', padx=4)
            tk.Button(btn_frame, text='⏭', command=self._replay_next, font=self.button_font, bg=self.accent, fg='white', relief='flat', padx=12, pady=8, bd=0, width=3).pack(side='left', padx=4)
            tk.Button(self.replay_ctrl_frame, text='❌ 退出回放', command=self._exit_replay_mode, font=self.button_font, bg=self.surface_bg, fg=self.text_main, relief='flat', padx=16, pady=8, bd=0).pack(pady=(8, 4))

        def _update_replay_display(self):
            total = len(self.game._replay_snapshots) - 1
            self.replay_progress_label.config(text=f'第 {self.replay_index} / {total} 手')
            self.game.restore_replay_snapshot(self.game._replay_snapshots[self.replay_index])
            self.last_move = None
            self._stones_dirty = True
            self.draw_board()
            self.current_label.config(text=f'当前: {PLAYER_NAMES[self.game.current]}')
            self.supply_label.config(text=f'黑棋: {self.game.supply[1]}  白棋: {self.game.supply[2]}')
            self._update_timer_display()
            self._refresh_log(full=True)
            self.status_var.set(f'回放 - 第 {self.replay_index} / {total} 手')

        def _replay_prev(self):
            self._cancel_replay_timer()
            if self.replay_index > 0:
                self.replay_index -= 1
                self._update_replay_display()

        def _replay_next(self):
            self._cancel_replay_timer()
            if self.replay_index < len(self.game._replay_snapshots) - 1:
                self.replay_index += 1
                self._update_replay_display()
            else:
                self.replay_play_btn.config(text='▶ 播放')

        def _replay_toggle_play(self):
            if self.replay_timer_job:
                self._cancel_replay_timer()
                self.replay_play_btn.config(text='▶ 播放')
                return
            if self.replay_index >= len(self.game._replay_snapshots) - 1:
                self.replay_index = 0
                self._update_replay_display()
            self.replay_play_btn.config(text='⏸ 暂停')
            self._replay_auto_step()

        def _replay_auto_step(self):
            if not self.replay_mode:
                return
            if self.replay_index < len(self.game._replay_snapshots) - 1:
                self.replay_index += 1
                self._update_replay_display()
                self.replay_timer_job = self.root.after(800, self._replay_auto_step)
            else:
                self.replay_play_btn.config(text='▶ 播放')
                self.replay_timer_job = None

        def perform_undo(self):
            self._cancel_ai()
            if not self.game.undo():
                return
            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self._highlight_color = '#ef4444'
            self._stones_dirty = True
            self._highlight_cells = []
            self.update_ui()
            self._refresh_log(full=True)
            self.status_var.set('已悔棋。')
            if self.game.player_types[self.game.current] == 'ai':
                self._schedule_ai(300)

        def perform_placement(self, x, y):
            self.game.save_snapshot()
            self.game.start_turn_timer()
            result = self.game.do_placement(x, y)
            if result is None:
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 没有棋子可下！')
                return
            self._after_placement(x, y, result, is_replacement=False)

        def perform_replacement(self, x, y):
            result = self.game.do_replacement(x, y)
            if result is None:
                return
            self.waiting_replacement = False
            self._after_placement(x, y, result, is_replacement=True)

        def _after_placement(self, x, y, result, is_replacement):
            self.last_move = (x, y)
            self._stones_dirty = True
            self._highlight_color = '#ffdd00'
            action = '替换' if is_replacement else '放置'
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} {action} {chr(ord("A") + x)}{y + 1}。')
            self._refresh_log()
            self.root.after(200, self._reset_highlight)
            if result.result == 'recovered':
                if result.can_replace:
                    self.waiting_replacement = True
                    self._highlight_cells = list(self.game.board._player_cells[3 - self.game.current])
                    msg = '再次连成五子，请继续替换' if is_replacement else '连成五子，请选择替换对方棋子'
                    self.status_var.set(f'{PLAYER_NAMES[self.game.current]} {msg}。')
                    self.update_ui()
                    return
                prefix = '替换后' if is_replacement else ''
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} {prefix}连成五子，但没有可替换的对方棋子。')
            self.conclude_turn()

        def conclude_turn(self):
            self.game.stop_turn_timer()
            self.update_ui()
            if self.game.has_lost(self.game.current):
                self.game.save_replay_snapshot()
                self.game_over = True
                winner = self.game.opponent()
                messagebox.showinfo('游戏结束', f'{PLAYER_NAMES[self.game.current]} 棋子用完，{PLAYER_NAMES[winner]} 胜利！')
                self._show_game_stats(winner)
                try:
                    os.remove(SAVE_FILE)
                except Exception:
                    pass
                return
            if self.game.is_draw():
                self.game.save_replay_snapshot()
                self.game_over = True
                messagebox.showinfo('游戏结束', '棋盘已满，平局！')
                self._show_game_stats(None)
                try:
                    os.remove(SAVE_FILE)
                except Exception:
                    pass
                return
            self.game.current = self.game.opponent()
            self.game.save_replay_snapshot()
            self.waiting_replacement = False
            self.update_ui()
            if self.game.player_types[self.game.current] == 'ai':
                delay = self.ai_delay_var.get()
                self._schedule_ai(delay)

        def ai_take_turn(self):
            if self._paused or self.game_over:
                return
            self.game.save_snapshot()
            level = self.game.ai_levels.get(self.game.current, 'medium')
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} AI({level}) 思考中…')
            if self.waiting_replacement:
                replacement = select_ai_replacement(self.game.board, self.game.current, self.game.ai_levels[self.game.current])
                if replacement:
                    x, y = replacement
                    self.perform_replacement(x, y)
                    if self.waiting_replacement:
                        delay = self.ai_delay_var.get()
                        self._schedule_ai(delay)
                    return
                self.waiting_replacement = False
                self.conclude_turn()
                return

            move = select_ai_move(self.game.board, self.game.current, self.game.ai_levels[self.game.current])
            if move is None:
                messagebox.showinfo('游戏结束', f'{PLAYER_NAMES[self.game.current]} 无法落子，{PLAYER_NAMES[self.game.opponent()]} 胜利！')
                return
            x, y = move
            self.perform_placement(x, y)
            if self.waiting_replacement:
                delay = self.ai_delay_var.get()
                self._schedule_ai(delay)

        def run(self):
            self.root.mainloop()
else:
    GameUI = None
