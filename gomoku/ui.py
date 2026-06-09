try:
    import tkinter as tk
    import tkinter.font as tkfont
    from tkinter import messagebox
except ImportError:
    tk = None
    tkfont = None
    messagebox = None

from game import Game, PLAYER_NAMES, STARTING_STONES, BOARD_SIZE

if tk is not None:
    class GameUI:
        def __init__(self):
            self.root = tk.Tk()
            self.root.title('不一样的五子棋')
            self.bg_color = '#e2e8f0'
            self.card_bg = '#f1f5f9'
            self.surface_bg = '#f1f5f9'
            self.panel_bg = '#e2e8f0'
            self.board_bg = '#d6d9e6'
            self.accent = '#3b82f6'
            self.accent_soft = '#93c5fd'
            self.text_main = '#0f172a'
            self.text_secondary = '#475569'
            self.game = Game()
            self.waiting_replacement = False
            self.mode_var = tk.StringVar(value='pvp')
            self.side_var = tk.StringVar(value='1')
            self.level_var = tk.StringVar(value='medium')
            self.status_var = tk.StringVar()
            self.starting_stones_var = tk.IntVar(value=STARTING_STONES)
            self.board_size_var = tk.IntVar(value=BOARD_SIZE)
            self.cell_font_size = 12
            self.fullscreen = False
            self.buttons = []
            font_families = set(tkfont.families()) if tkfont is not None else set()
            preferred_fonts = ['Microsoft YaHei UI', 'Microsoft YaHei', 'SimHei', 'Segoe UI Variable', 'Segoe UI', 'Arial']
            self.ui_font = next((name for name in preferred_fonts if name in font_families), 'Arial')
            self.title_font = tkfont.Font(family=self.ui_font, size=28, weight='bold')
            self.header_font = tkfont.Font(family=self.ui_font, size=16, weight='bold')
            self.label_font = tkfont.Font(family=self.ui_font, size=12)
            self.button_font = tkfont.Font(family=self.ui_font, size=11, weight='bold')
            self.status_font = tkfont.Font(family=self.ui_font, size=12)
            self.root.configure(bg=self.bg_color)
            self.root.option_add('*Font', self.label_font)
            self.build_start_screen()

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
            for text, value in [('双人', 'pvp'), ('人机', 'pve')]:
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
            tk.Label(section, text='初始设置', font=self.label_font, bg=self.card_bg, fg=self.text_main).pack(anchor='w')
            fields = tk.Frame(section, bg=self.card_bg)
            fields.pack(anchor='w', pady=(8, 0))
            tk.Label(fields, text='棋子数：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=0, column=0, sticky='w', padx=6, pady=6)
            tk.Spinbox(fields, from_=5, to=500, textvariable=self.starting_stones_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=0, column=1, sticky='w', padx=6, pady=6)
            tk.Label(fields, text='棋盘大小：', font=self.label_font, bg=self.card_bg, fg=self.text_secondary).grid(row=1, column=0, sticky='w', padx=6, pady=6)
            tk.Spinbox(fields, from_=5, to=99, textvariable=self.board_size_var, width=8, font=self.label_font, bd=0, relief='flat', bg=self.surface_bg, fg=self.text_main, insertbackground=self.text_main).grid(row=1, column=1, sticky='w', padx=6, pady=6)

            tk.Button(card, text='▶ START', command=self.start_game, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=22, pady=14, bd=0).pack(pady=(18, 0), fill='x')
            tk.Button(card, text='退出游戏', command=self.root.destroy, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=22, pady=14, bd=0).pack(pady=(10, 0), fill='x')

        def start_game(self):
            size = int(self.board_size_var.get())
            starting = int(self.starting_stones_var.get())
            self.game = Game(size=size, starting_stones=starting)
            if self.mode_var.get() == 'pve':
                human_side = int(self.side_var.get())
                ai_side = 3 - human_side
                self.game.player_types = {human_side: 'human', ai_side: 'ai'}
                self.game.ai_levels[ai_side] = self.level_var.get()
            else:
                self.game.player_types = {1: 'human', 2: 'human'}
                self.game.ai_levels = {1: None, 2: None}

            self.waiting_replacement = False
            self.build_game_ui()
            self.update_ui()

            if self.game.player_types[self.game.current] == 'ai':
                self.root.after(300, self.ai_take_turn)

        def build_game_ui(self):
            for widget in self.root.winfo_children():
                widget.destroy()

            header_frame = tk.Frame(self.root, bg=self.bg_color, pady=16, padx=18)
            header_frame.pack(fill='x')
            self.current_label = tk.Label(header_frame, font=self.header_font, bg=self.bg_color, fg=self.text_main)
            self.current_label.pack(side='left')
            self.supply_label = tk.Label(header_frame, font=self.label_font, bg=self.bg_color, fg=self.text_secondary)
            self.supply_label.pack(side='left', padx=24)

            self.status_label = tk.Label(self.root, textvariable=self.status_var, font=self.status_font, bg=self.surface_bg, fg=self.text_main, wraplength=760, justify='left', bd=0, relief='flat', padx=18, pady=14)
            self.status_label.pack(fill='x', pady=(0, 10), padx=16)

            board_frame = tk.Frame(self.root, bg=self.panel_bg, bd=0, highlightthickness=1, highlightbackground='#cbd5e1')
            board_frame.pack(fill='both', expand=True, padx=16, pady=8)

            self.canvas = tk.Canvas(board_frame, bg=self.board_bg, highlightthickness=0)
            self.canvas.pack(fill='both', expand=True)
            self.canvas.bind('<Button-1>', self.on_canvas_click)
            self.canvas.bind('<Configure>', lambda e: self.draw_board())
            self.cell_size = 24

            footer = tk.Frame(self.root, bg=self.bg_color, pady=14)
            footer.pack(fill='x')
            tk.Button(footer, text='⛶ 全屏', command=self.toggle_fullscreen, font=self.button_font, bg=self.accent, fg='white', activebackground='#5b21b6', activeforeground='white', relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='↻ 重新开始', command=self.build_start_screen, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)
            tk.Button(footer, text='← 主菜单', command=self.build_start_screen, font=self.button_font, bg=self.surface_bg, fg=self.text_main, activebackground=self.panel_bg, activeforeground=self.text_main, relief='flat', padx=20, pady=12).pack(side='left', padx=10)

        def draw_board(self):
            if not hasattr(self, 'canvas'):
                return
            w = self.canvas.winfo_width()
            h = self.canvas.winfo_height()
            cols = self.game.size
            rows = self.game.size
            if cols == 0 or rows == 0:
                return
            cell_w = max(6, w // cols)
            cell_h = max(6, h // rows)
            self.cell_size = min(cell_w, cell_h)
            self.canvas.delete('all')

            board_w = self.cell_size * cols
            board_h = self.cell_size * rows
            self.board_offset_x = max(0, (w - board_w) // 2)
            self.board_offset_y = max(0, (h - board_h) // 2)

            self.canvas.create_rectangle(self.board_offset_x, self.board_offset_y, self.board_offset_x + board_w, self.board_offset_y + board_h, fill=self.board_bg, outline=self.accent_soft, width=2)
            for i in range(1, cols):
                x = self.board_offset_x + i * self.cell_size
                self.canvas.create_line(x, self.board_offset_y + 2, x, self.board_offset_y + board_h - 2, fill='#94a3b8')
            for j in range(1, rows):
                y = self.board_offset_y + j * self.cell_size
                self.canvas.create_line(self.board_offset_x + 2, y, self.board_offset_x + board_w - 2, y, fill='#94a3b8')

            radius = int(self.cell_size * 0.42)
            highlight_radius = int(radius * 0.4)
            for y in range(rows):
                for x in range(cols):
                    cell = self.game.board.get(x, y)
                    cx = self.board_offset_x + x * self.cell_size + self.cell_size // 2
                    cy = self.board_offset_y + y * self.cell_size + self.cell_size // 2
                    if cell == 1:
                        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#1f2937', outline='#64748b', width=1)
                        self.canvas.create_oval(cx - highlight_radius, cy - highlight_radius, cx - highlight_radius + highlight_radius, cy - highlight_radius + highlight_radius, fill='#475569', outline='')
                    elif cell == 2:
                        self.canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill='#f8fafc', outline='#cbd5e1', width=1)
                        self.canvas.create_oval(cx - highlight_radius, cy - highlight_radius, cx - highlight_radius + highlight_radius, cy - highlight_radius + highlight_radius, fill='#ffffff', outline='')

            if self.waiting_replacement and self.game.player_types[self.game.current] == 'human':
                for y in range(rows):
                    for x in range(cols):
                        if self.game.board.get(x, y) == 3 - self.game.current:
                            x1 = self.board_offset_x + x * self.cell_size
                            y1 = self.board_offset_y + y * self.cell_size
                            self.canvas.create_rectangle(x1 + 2, y1 + 2, x1 + self.cell_size - 2, y1 + self.cell_size - 2, outline='#22c55e', width=3)

            self.canvas.config(scrollregion=(0, 0, w, h))

        def toggle_fullscreen(self):
            self.fullscreen = not self.fullscreen
            self.root.attributes('-fullscreen', self.fullscreen)

        def update_ui(self):
            self.draw_board()
            self.current_label.config(text=f'当前: {PLAYER_NAMES[self.game.current]}')
            self.supply_label.config(text=f'黑棋: {self.game.supply[1]}  白棋: {self.game.supply[2]}')
            if not self.waiting_replacement:
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 请落子。')

        def on_canvas_click(self, event):
            if self.game.player_types[self.game.current] == 'ai':
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
                if self.game.board.is_empty(x, y):
                    self.perform_placement(x, y)
                    self.update_ui()

        def on_cell_click(self, x, y):
            if self.game.player_types[self.game.current] == 'ai':
                return
            if self.waiting_replacement:
                if self.game.board.get(x, y) == 3 - self.game.current:
                    self.perform_replacement(x, y)
            else:
                if self.game.board.is_empty(x, y):
                    self.perform_placement(x, y)

        def perform_placement(self, x, y):
            self.game.place_stone(x, y)
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 放置 {chr(ord("A") + x)}{y + 1}。')
            line = self.game.line_after_placement(x, y)
            if line:
                self.game.recover_line(line)
                if self.game.replacement_is_available():
                    self.waiting_replacement = True
                    self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 连成五子，请选择替换对方棋子。')
                    self.update_ui()
                    return
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 连成五子，但没有可替换的对方棋子。')

            self.conclude_turn()

        def perform_replacement(self, x, y):
            self.game.apply_replacement(x, y)
            self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 替换了 {chr(ord("A") + x)}{y + 1}。')
            self.waiting_replacement = False
            line = self.game.line_after_placement(x, y)
            if line:
                self.game.recover_line(line)
                if self.game.replacement_is_available():
                    self.waiting_replacement = True
                    self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 再次连成五子，请继续替换。')
                    self.update_ui()
                    return
                self.status_var.set(f'{PLAYER_NAMES[self.game.current]} 替换后连成五子，但无法继续替换，回合结束。')
                self.conclude_turn()
                return

            self.conclude_turn()

        def conclude_turn(self):
            self.update_ui()
            if self.game.has_lost(self.game.current):
                messagebox.showinfo('游戏结束', f'{PLAYER_NAMES[self.game.current]} 棋子用完，{PLAYER_NAMES[self.game.opponent()]} 胜利！')
                return
            self.game.current = self.game.opponent()
            self.waiting_replacement = False
            self.update_ui()
            if self.game.player_types[self.game.current] == 'ai':
                self.root.after(300, self.ai_take_turn)

        def ai_take_turn(self):
            if self.waiting_replacement:
                replacement = self.game.select_ai_replacement(self.game.current)
                if replacement:
                    x, y = replacement
                    self.perform_replacement(x, y)
                    return
                self.waiting_replacement = False
                self.conclude_turn()
                return

            move = self.game.select_ai_move(self.game.current)
            if move is None:
                messagebox.showinfo('游戏结束', f'{PLAYER_NAMES[self.game.current]} 无法落子，{PLAYER_NAMES[self.game.opponent()]} 胜利！')
                return
            x, y = move
            self.perform_placement(x, y)

        def run(self):
            self.root.mainloop()
else:
    GameUI = None
