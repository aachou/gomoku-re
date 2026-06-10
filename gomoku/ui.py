try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox
except ImportError:
    tk = None
    tkfont = None
    messagebox = None

import time

from .game import Game, PLAYER_NAMES, STARTING_STONES, save_config, load_config
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
            self._windowed_geometry = None
            self._paused = False
            self._timer_job = None
            self._hotkeys_shown = False
            self.buttons = []
            self.level_var.set(config.get('ai_level', 'medium'))
            self.board_size_var.set(config.get('board_size', 15))
            self.starting_stones_var.set(config.get('starting_stones', 30))
            self.ai_delay_var.set(config.get('ai_delay_ms', 300))
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
            self.root.bind('<Escape>', lambda e: self.build_start_screen())
            self.root.bind('<Key-slash>', lambda e: self._toggle_hotkeys())
            self.root.bind('<Key-question>', lambda e: self._toggle_hotkeys())
            self.build_start_screen()

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

        def build_start_screen(self):
            for widget in self.root.winfo_children():
                widget.destroy()

            container = tk.Frame(self.root, bg=self.bg_color, padx=20, pady=20)
            container.pack(fill='both', expand=True)

            card = tk.Frame(container, bg=self.card_bg, bd=0, highlightbackground='#1e293b', highlightthickness=1, padx=26, pady=26)
            card.pack(padx=20, pady=24, fill='x', expand=True)

            accent_bar = tk.Frame(card, bg=self.accent, height=4)
            accent_bar.pack(fill='x', side='top', pady=(0, 16))
            tk.Label(card, text='不一样的五子棋', font=self.title_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            tk.Label(card, text='未来风格对战 · AI 支持 · 自定义棋盘与棋子', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).pack(anchor='w', pady=(6, 20))

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 12))
            tk.Label(section, text='对战模式', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            opt_frame = tk.Frame(section, bg=self.card_bg)
            opt_frame.pack(anchor='w', pady=(8, 8))
            for text, value in [('双人', 'pvp'), ('人机', 'pve'), ('AI vs AI', 'pvai')]:
                tk.Radiobutton(opt_frame, text=text, variable=self.mode_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=16, pady=12, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=8)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 12))
            tk.Label(section, text='执棋方', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            side_frame = tk.Frame(section, bg=self.card_bg)
            side_frame.pack(anchor='w', pady=(8, 8))
            for text, value in [('黑棋', '1'), ('白棋', '2')]:
                tk.Radiobutton(side_frame, text=text, variable=self.side_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=16, pady=12, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=8)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 12))
            tk.Label(section, text='AI 难度', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            level_frame = tk.Frame(section, bg=self.card_bg)
            level_frame.pack(anchor='w', pady=(8, 8))
            for text, value in [('简单', 'simple'), ('中等', 'medium'), ('困难', 'hard')]:
                tk.Radiobutton(level_frame, text=text, variable=self.level_var, value=value, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=16, pady=12, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=8)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 12))
            tk.Label(section, text='主题', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            theme_frame = tk.Frame(section, bg=self.card_bg)
            theme_frame.pack(anchor='w', pady=(8, 8))
            for name in list(THEMES.keys()):
                tk.Radiobutton(theme_frame, text=name, variable=self.theme_var, value=name, bg=self.surface_bg, fg=self.text_main, selectcolor=self.accent, activebackground=self.panel_bg, activeforeground=self.text_main, font=self.label_font, indicatoron=0, padx=16, pady=12, bd=0, relief='flat', highlightthickness=0).pack(side='left', padx=8)

            section = tk.Frame(card, bg=self.card_bg)
            section.pack(fill='x', pady=(0, 12))
            tk.Label(section, text='初始设置', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            fields = tk.Frame(section, bg=self.card_bg)
            fields.pack(anchor='w', pady=(8, 0))
            tk.Label(fields, text='棋子数：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=0, sticky='w', padx=6, pady=6)
            tk.Spinbox(fields, from_=5, to=500, textvariable=self.starting_stones_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=0, column=1, sticky='w', padx=6, pady=6)
            tk.Label(fields, text='棋盘大小：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=1, column=0, sticky='w', padx=6, pady=6)
            tk.Spinbox(fields, from_=5, to=99, textvariable=self.board_size_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=1, column=1, sticky='w', padx=6, pady=6)

            tk.Button(card, text='▶ START', command=self.start_game, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=22, pady=14, bd=0).pack(pady=(18, 0), fill='x')
            tk.Button(card, text='⛶ 全屏', command=self.toggle_fullscreen, font=self.button_font, bg=self.accent_soft, fg=self.text_main, activebackground='#93c5fd', activeforeground=self.text_main, relief='flat', padx=22, pady=14, bd=0).pack(pady=(10, 0), fill='x')
            tk.Button(card, text='退出游戏', command=self.root.destroy, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=22, pady=14, bd=0).pack(pady=(10, 0), fill='x')

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

            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self._paused = False
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
                self.root.after(300, self.ai_take_turn)

        def build_game_ui(self):
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
            self.cell_size = 24

            side_panel = tk.Frame(center_frame, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground='#cbd5e1', width=220)
            side_panel.pack(side='right', fill='y', padx=(8, 0))
            side_panel.pack_propagate(False)

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
            tk.Button(footer, text='↻ 重新开始', command=self.build_start_screen, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='← 主菜单', command=self.build_start_screen, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)

        def _update_speed_label(self):
            val = self.ai_delay_var.get()
            self.speed_label.config(text=f'{"慢" if val > 1000 else "中" if val > 300 else "快"} ({val}ms)')

        def toggle_pause(self):
            self._paused = not self._paused
            self.pause_btn.config(text='▶ 继续' if self._paused else '⏸ 暂停')
            if not self._paused:
                if self.game.player_types[self.game.current] == 'ai' and not self.waiting_replacement and not self.game_over:
                    self.root.after(100, self.ai_take_turn)

        def _layout_changed(self, w, h):
            cols = self.game.size
            rows = self.game.size
            cell_w = max(6, w // cols)
            cell_h = max(6, h // rows)
            new_cell_size = min(cell_w, cell_h)
            board_w = new_cell_size * cols
            board_h = new_cell_size * rows
            margin = self.cell_size
            new_ox = max(margin, (w - board_w) // 2)
            new_oy = max(margin, (h - board_h) // 2)
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
                self.canvas.create_oval(cx - radius - 2, cy - radius - 2, cx + radius + 2, cy + radius + 2, outline='#ef4444', width=2, tags='stone')

        def _draw_highlights(self):
            if self.waiting_replacement and self.game.player_types[self.game.current] == 'human':
                opponent = 3 - self.game.current
                for x, y in self.game.board._player_cells[opponent]:
                    x1 = self.board_offset_x + x * self.cell_size
                    y1 = self.board_offset_y + y * self.cell_size
                    self.canvas.create_rectangle(x1 + 2, y1 + 2, x1 + self.cell_size - 2, y1 + self.cell_size - 2, outline='#22c55e', width=3, tags='highlight')

        def draw_board(self):
            if not hasattr(self, 'canvas'):
                return
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            if w <= 1 or h <= 1:
                return
            if self._layout_changed(w, h):
                self.canvas.delete('all')
                self._draw_grid()
            self.canvas.delete('stone', 'highlight')
            self._draw_stones()
            self._draw_highlights()

        def toggle_fullscreen(self):
            self.fullscreen = not self.fullscreen
            if self.fullscreen:
                self._windowed_geometry = self.root.geometry()
                self.root.attributes('-fullscreen', True)
            else:
                self.root.attributes('-fullscreen', False)
                if self._windowed_geometry:
                    self.root.geometry(self._windowed_geometry)

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

        def _refresh_log(self):
            self.log_listbox.delete(0, 'end')
            for entry in self.game.move_log:
                p = PLAYER_NAMES[entry['player']]
                pos = f'{chr(ord("A") + entry["x"])}{entry["y"] + 1}'
                if entry['action'] == 'place':
                    text = f'{p} 落子 {pos}'
                    if entry['recovered']:
                        text += f' 回收{entry["recovered"]}'
                else:
                    text = f'{p} 替换 {pos}'
                self.log_listbox.insert('end', text)
            self.log_listbox.see('end')

        def on_canvas_click(self, event):
            if self.game_over or self.game.player_types[self.game.current] == 'ai':
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

        def perform_undo(self):
            if not self.game.undo():
                return
            self.waiting_replacement = False
            self.game_over = False
            self.last_move = None
            self.update_ui()
            self._refresh_log()
            self.status_var.set('已悔棋。')
            if self.game.player_types[self.game.current] == 'ai':
                self.root.after(300, self.ai_take_turn)

        def perform_placement(self, x, y):
            self.game.start_turn_timer()
            result = self.game.do_placement(x, y)
            if result is None:
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 没有棋子可下！')
                return
            self.last_move = (x, y)
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 放置 {chr(ord("A") + x)}{y + 1}。')
            self._refresh_log()
            if result.result == 'recovered':
                if result.can_replace:
                    self.waiting_replacement = True
                    self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 连成五子，请选择替换对方棋子。')
                    self.update_ui()
                    return
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 连成五子，但没有可替换的对方棋子。')
            self.conclude_turn()

        def perform_replacement(self, x, y):
            result = self.game.do_replacement(x, y)
            if result is None:
                return
            self.last_move = (x, y)
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 替换了 {chr(ord("A") + x)}{y + 1}。')
            self.waiting_replacement = False
            self._refresh_log()
            if result.result == 'recovered':
                if result.can_replace:
                    self.waiting_replacement = True
                    self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 再次连成五子，请继续替换。')
                    self.update_ui()
                    return
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 替换后连成五子，但无法继续替换，回合结束。')
            self.conclude_turn()

        def conclude_turn(self):
            self.game.stop_turn_timer()
            self.update_ui()
            if self.game.has_lost(self.game.current):
                self.game_over = True
                messagebox.showinfo('游戏结束', f'{PLAYER_NAMES[self.game.current]} 棋子用完，{PLAYER_NAMES[self.game.opponent()]} 胜利！')
                return
            if self.game.is_draw():
                self.game_over = True
                messagebox.showinfo('游戏结束', '棋盘已满，平局！')
                return
            self.game.current = self.game.opponent()
            self.waiting_replacement = False
            self.update_ui()
            if self.game.player_types[self.game.current] == 'ai':
                delay = self.ai_delay_var.get()
                self.root.after(delay, self.ai_take_turn)

        def ai_take_turn(self):
            if self._paused or self.game_over:
                return
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} AI思考中…')
            if self.waiting_replacement:
                replacement = select_ai_replacement(self.game.board, self.game.current, self.game.ai_levels[self.game.current])
                if replacement:
                    x, y = replacement
                    self.perform_replacement(x, y)
                    if self.waiting_replacement:
                        delay = self.ai_delay_var.get()
                        self.root.after(delay, self.ai_take_turn)
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
                self.root.after(delay, self.ai_take_turn)

        def run(self):
            self.root.mainloop()
else:
    GameUI = None
