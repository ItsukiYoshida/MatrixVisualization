import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib as mpl
import matplotlib.font_manager as fm
import os
import platform
import sys
import traceback
import argparse
import json
import locale
import logging
from datetime import datetime
from functools import partial

# 日本語フォントの設定
def setup_japanese_fonts():
    # プラットフォーム検出
    system = platform.system()
    
    # 利用可能なフォントをリスト化
    font_list = sorted([f.name for f in fm.fontManager.ttflist])
    
    # プラットフォームごとのデフォルトフォント設定
    if system == 'Windows':
        font_candidates = ['MS Gothic', 'Yu Gothic', 'Meiryo', 'Noto Sans CJK JP']
    elif system == 'Darwin':  # macOS
        font_candidates = ['Hiragino Sans', 'Hiragino Kaku Gothic ProN', 'Noto Sans CJK JP']
    else:  # Linux
        font_candidates = ['IPAGothic', 'IPAPGothic', 'VL Gothic', 'Noto Sans CJK JP']
    
    # 利用可能な日本語フォントを検索
    for font in font_candidates:
        if any(font in f for f in font_list):
            plt.rcParams['font.family'] = 'sans-serif'
            plt.rcParams['font.sans-serif'] = [font]
            print(f"日本語フォント '{font}' を設定しました")
            return True
    
    print("適切な日本語フォントが見つかりませんでした。デフォルトフォントを使用します。")
    return False

# 日本語フォント設定を実行
setup_japanese_fonts()

class MatrixVisualization:
    def __init__(self, root):
        self.root = root
        self.root.title("行列演算可視化ツール")
        self.root.geometry("1300x800")
        self.root.minsize(1000, 700)
        
        # アプリケーションのテーマ設定
        self.is_dark_mode = False
        
        # 予約語のリスト
        self.reserved_words = ['+', '-', '*', '^', 'Det', 'Tr', '=']
        
        # 行列辞書 - キーは行列名、値は行列のデータとプロパティ
        self.matrices = {}
        
        # 矢印のリスト
        self.arrows = []
        
        # 色付き要素のリスト
        self.colored_cells = []
        
        # スタイル設定
        self.style = ttk.Style()
        self.setup_style()
        
        # メインフレーム
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ステータスバー
        self.status_var = tk.StringVar()
        self.status_var.set("準備完了")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # メニューバー
        self.create_menu()
        
        # 左右に分割するパネル
        self.panel_paned = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.panel_paned.pack(fill=tk.BOTH, expand=True)
        
        # 左側のスクロール可能なコントロールパネル
        self.create_scrollable_control_panel()
        
        # 右側の可視化パネル
        self.viz_panel = ttk.Frame(self.panel_paned)
        self.panel_paned.add(self.viz_panel, weight=2)
        
        # Matplotlib の図とキャンバス
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.get_tk_widget().bind("<Motion>", self.on_mouse_move)
        
        # ツールチップ用の変数
        self.tooltip = None
        
        # 最後に選択した要素の情報
        self.last_selected_matrix = None
        self.last_selected_cell = None
        
        # 初期可視化
        self.visualize_matrices()
    
    def setup_style(self):
        """スタイルの初期設定"""
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TLabel", background="#f0f0f0")
        self.style.configure("TLabelframe", background="#f0f0f0")
        self.style.configure("TLabelframe.Label", background="#f0f0f0")
        self.style.configure("TButton", background="#e0e0e0", foreground="#000000")
        self.style.configure("TNotebook", background="#f0f0f0")
        self.style.configure("TNotebook.Tab", background="#e0e0e0", foreground="#000000", padding=[10, 2])
        self.style.map("TNotebook.Tab", background=[("selected", "#f0f0f0")], foreground=[("selected", "#000000")])
    
    def toggle_theme(self):
        """ダークモードとライトモードを切り替え"""
        self.is_dark_mode = not self.is_dark_mode
        
        if self.is_dark_mode:
            # ダークモードのスタイル設定
            self.style.configure("TFrame", background="#2d2d2d")
            self.style.configure("TLabel", background="#2d2d2d", foreground="#ffffff")
            self.style.configure("TLabelframe", background="#2d2d2d")
            self.style.configure("TLabelframe.Label", background="#2d2d2d", foreground="#ffffff")
            self.style.configure("TButton", background="#3d3d3d", foreground="#ffffff")
            self.style.configure("TNotebook", background="#2d2d2d")
            self.style.configure("TNotebook.Tab", background="#3d3d3d", foreground="#ffffff", padding=[10, 2])
            self.style.map("TNotebook.Tab", background=[("selected", "#4d4d4d")], foreground=[("selected", "#ffffff")])
            
            # Matplotlibの設定
            self.fig.patch.set_facecolor('#2d2d2d')
            self.ax.set_facecolor('#2d2d2d')
            self.ax.title.set_color('#ffffff')
            
            # コンソールとリストボックスの色設定
            self.console_text.config(bg="#3d3d3d", fg="#ffffff", insertbackground="#ffffff")
            self.console_history.config(bg="#3d3d3d", fg="#ffffff")
            self.matrices_listbox.config(bg="#3d3d3d", fg="#ffffff")
            self.arrows_listbox.config(bg="#3d3d3d", fg="#ffffff")
            self.colored_cells_listbox.config(bg="#3d3d3d", fg="#ffffff")
            
            # ステータスバーの色を変更
            self.status_var.set("ダークモードに切り替えました")
        else:
            # ライトモードのスタイル設定（デフォルト）
            self.style.configure("TFrame", background="#f0f0f0")
            self.style.configure("TLabel", background="#f0f0f0", foreground="#000000")
            self.style.configure("TLabelframe", background="#f0f0f0")
            self.style.configure("TLabelframe.Label", background="#f0f0f0", foreground="#000000")
            self.style.configure("TButton", background="#e0e0e0", foreground="#000000")
            self.style.configure("TNotebook", background="#f0f0f0")
            self.style.configure("TNotebook.Tab", background="#e0e0e0", foreground="#000000", padding=[10, 2])
            self.style.map("TNotebook.Tab", background=[("selected", "#f0f0f0")], foreground=[("selected", "#000000")])
            
            # Matplotlibの設定
            self.fig.patch.set_facecolor('#f0f0f0')
            self.ax.set_facecolor('#ffffff')
            self.ax.title.set_color('#000000')
            
            # コンソールとリストボックスの色設定
            self.console_text.config(bg="#ffffff", fg="#000000", insertbackground="#000000")
            self.console_history.config(bg="#ffffff", fg="#000000")
            self.matrices_listbox.config(bg="#ffffff", fg="#000000")
            self.arrows_listbox.config(bg="#ffffff", fg="#000000")
            self.colored_cells_listbox.config(bg="#ffffff", fg="#000000")
            
            # ステータスバーの色を変更
            self.status_var.set("ライトモードに切り替えました")
        
        # キャンバスを更新
        self.canvas.draw()
        
    def create_menu(self):
        """メニューバーを作成"""
        menu_bar = tk.Menu(self.root)
        
        # ファイルメニュー
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="新規", command=self.reset_all, accelerator="Ctrl+N")
        file_menu.add_separator()
        file_menu.add_command(label="PNG形式で保存", command=lambda: self.save_figure("png"), accelerator="Ctrl+S")
        file_menu.add_command(label="PDF形式で保存", command=lambda: self.save_figure("pdf"), accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit, accelerator="Alt+F4")
        file_menu.add_command(label="データを開く", command=lambda: self.load_matrix_data(filedialog.askopenfilename(filetypes=[("JSON ファイル", "*.json")])), accelerator="Ctrl+O")
        file_menu.add_command(label="データを保存", command=lambda: self.save_matrix_data(filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON ファイル", "*.json")])), accelerator="Ctrl+S")
        file_menu.add_separator()
        menu_bar.add_cascade(label="ファイル", menu=file_menu)
        
        # 編集メニュー
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="行列をクリップボードにコピー", command=self.copy_matrix_to_clipboard, accelerator="Ctrl+C")
        edit_menu.add_separator()
        edit_menu.add_command(label="すべてを選択", command=self.select_all, accelerator="Ctrl+A")
        menu_bar.add_cascade(label="編集", menu=edit_menu)
        
        # 表示メニュー
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="テーマ切替", command=self.toggle_theme)
        view_menu.add_command(label="グリッド表示切替", command=self.toggle_grid)
        view_menu.add_separator()
        view_menu.add_command(label="拡大", command=lambda: self.zoom(1.2), accelerator="Ctrl++")
        view_menu.add_command(label="縮小", command=lambda: self.zoom(0.8), accelerator="Ctrl+-")
        view_menu.add_command(label="ビューをリセット", command=self.reset_view, accelerator="Ctrl+0")
        menu_bar.add_cascade(label="表示", menu=view_menu)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="コマンド一覧", command=self.show_commands_help)
        help_menu.add_command(label="ショートカットキー", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="このアプリについて", command=self.show_about)
        menu_bar.add_cascade(label="ヘルプ", menu=help_menu)
        
        self.root.config(menu=menu_bar)
        
        # ショートカットキーのバインド
        self.root.bind("<Control-n>", lambda e: self.reset_all())
        self.root.bind("<Control-s>", lambda e: self.save_figure("png"))
        self.root.bind("<Control-p>", lambda e: self.save_figure("pdf"))
        self.root.bind("<Control-c>", lambda e: self.copy_matrix_to_clipboard())
        self.root.bind("<Control-a>", lambda e: self.select_all())
        self.root.bind("<Control-plus>", lambda e: self.zoom(1.2))
        self.root.bind("<Control-minus>", lambda e: self.zoom(0.8))
        self.root.bind("<Control-0>", lambda e: self.reset_view())
        self.root.bind("<Control-o>", lambda e: self.load_matrix_data(filedialog.askopenfilename(filetypes=[("JSON ファイル", "*.json")])))
        self.root.bind("<Control-s>", lambda e: self.save_matrix_data(filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON ファイル", "*.json")])))
    
    def create_scrollable_control_panel(self):
        """スクロール可能なコントロールパネルを作成"""
        # スクロール可能なフレームを作成
        control_container = ttk.Frame(self.panel_paned)
        self.panel_paned.add(control_container, weight=1)
        
        # スクロールバー付きキャンバス
        canvas = tk.Canvas(control_container, bg="#f0f0f0")
        scrollbar = ttk.Scrollbar(control_container, orient=tk.VERTICAL, command=canvas.yview)
        
        # スクロール可能なフレーム
        self.control_panel = ttk.Frame(canvas)
        
        # スクロールバーとキャンバスの連携
        self.control_panel.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # キャンバスにフレームを配置
        canvas_frame = canvas.create_window((0, 0), window=self.control_panel, anchor=tk.NW)
        
        # キャンバスの幅をフレームに合わせる
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # スクロールホイールイベントの設定
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", lambda e: canvas.yview_scroll(-1, "units"))  # Linux
        canvas.bind_all("<Button-5>", lambda e: canvas.yview_scroll(1, "units"))  # Linux
        
        # レイアウト
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # スクロールバーとキャンバスの連携
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # タブを作成
        self.create_tabbed_interface()
    
    def create_tabbed_interface(self):
        """タブインターフェースを作成"""
        notebook = ttk.Notebook(self.control_panel)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 各タブのコンテンツフレーム
        matrix_tab = ttk.Frame(notebook)
        arrow_tab = ttk.Frame(notebook)
        cell_tab = ttk.Frame(notebook)
        expr_tab = ttk.Frame(notebook)
        console_tab = ttk.Frame(notebook)
        list_tab = ttk.Frame(notebook)
        
        # タブの追加
        notebook.add(matrix_tab, text="行列定義")
        notebook.add(arrow_tab, text="矢印設定")
        notebook.add(cell_tab, text="要素設定")
        notebook.add(expr_tab, text="行列式")
        notebook.add(console_tab, text="コンソール")
        notebook.add(list_tab, text="定義済みリスト")
        
        # 各タブの内容を設定
        self.create_matrix_tab(matrix_tab)
        self.create_arrow_tab(arrow_tab)
        self.create_cell_tab(cell_tab)
        self.create_expr_tab(expr_tab)
        self.create_console_tab(console_tab)
        self.create_list_tab(list_tab)
    
    def create_matrix_tab(self, parent):
        """行列定義タブの内容を作成"""
        frame = ttk.LabelFrame(parent, text="行列定義")
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        # 行列定義フォーム用のグリッド
        for i in range(6):
            frame.columnconfigure(i, weight=1)
        
        ttk.Label(frame, text="行列名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.matrix_name = ttk.Entry(frame, width=5)
        self.matrix_name.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.matrix_name.insert(0, "A")
        
        ttk.Label(frame, text="行:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.rows = ttk.Spinbox(frame, from_=1, to=10, width=5)
        self.rows.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.rows.set(3)
        
        ttk.Label(frame, text="列:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.cols = ttk.Spinbox(frame, from_=1, to=10, width=5)
        self.cols.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.cols.set(3)
        
        ttk.Label(frame, text="位置 X:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.pos_x = ttk.Spinbox(frame, from_=0, to=20, width=5)
        self.pos_x.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.pos_x.set(0)
        
        ttk.Label(frame, text="位置 Y:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.pos_y = ttk.Spinbox(frame, from_=0, to=20, width=5)
        self.pos_y.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.pos_y.set(0)
        
        add_btn = ttk.Button(frame, text="行列を追加", command=self.add_matrix)
        add_btn.grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.create_tooltip(add_btn, "新しい行列を作成し可視化パネルに追加します")
        
        # ランダム行列生成セクション
        rand_frame = ttk.LabelFrame(parent, text="ランダム行列生成")
        rand_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(rand_frame, text="最小値:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.random_min = ttk.Spinbox(rand_frame, from_=-100, to=100, width=5)
        self.random_min.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.random_min.set(-10)
        
        ttk.Label(rand_frame, text="最大値:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.random_max = ttk.Spinbox(rand_frame, from_=-100, to=100, width=5)
        self.random_max.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.random_max.set(10)
        
        rand_btn = ttk.Button(rand_frame, text="ランダム値で設定", command=self.generate_random_matrix)
        rand_btn.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.create_tooltip(rand_btn, "指定した範囲のランダム値で行列を生成します")
        
        # 特殊行列生成セクション
        special_frame = ttk.LabelFrame(parent, text="特殊行列生成")
        special_frame.pack(fill=tk.X, padx=5, pady=5)
        
        identity_btn = ttk.Button(special_frame, text="単位行列", command=lambda: self.generate_special_matrix("identity"))
        identity_btn.grid(row=0, column=0, padx=5, pady=5)
        self.create_tooltip(identity_btn, "対角成分が1、それ以外が0の単位行列を生成します")
        
        zeros_btn = ttk.Button(special_frame, text="零行列", command=lambda: self.generate_special_matrix("zeros"))
        zeros_btn.grid(row=0, column=1, padx=5, pady=5)
        self.create_tooltip(zeros_btn, "すべての要素が0の行列を生成します")
        
        ones_btn = ttk.Button(special_frame, text="1行列", command=lambda: self.generate_special_matrix("ones"))
        ones_btn.grid(row=0, column=2, padx=5, pady=5)
        self.create_tooltip(ones_btn, "すべての要素が1の行列を生成します")
        
        upper_btn = ttk.Button(special_frame, text="上三角行列", command=lambda: self.generate_special_matrix("upper"))
        upper_btn.grid(row=1, column=0, padx=5, pady=5)
        self.create_tooltip(upper_btn, "対角成分を含む上側のみに値がある行列を生成します")
        
        lower_btn = ttk.Button(special_frame, text="下三角行列", command=lambda: self.generate_special_matrix("lower"))
        lower_btn.grid(row=1, column=1, padx=5, pady=5)
        self.create_tooltip(lower_btn, "対角成分を含む下側のみに値がある行列を生成します")
        
        diag_btn = ttk.Button(special_frame, text="対角行列", command=lambda: self.generate_special_matrix("diagonal"))
        diag_btn.grid(row=1, column=2, padx=5, pady=5)
        self.create_tooltip(diag_btn, "対角成分のみに値がある行列を生成します")
    
    def create_arrow_tab(self, parent):
        """矢印設定タブの内容を作成"""
        arrow_frame = ttk.LabelFrame(parent, text="矢印定義")
        arrow_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(arrow_frame, text="始点行列:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_matrix = ttk.Entry(arrow_frame, width=5)
        self.source_matrix.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.source_matrix.insert(0, "A")
        
        ttk.Label(arrow_frame, text="行:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.source_row = ttk.Spinbox(arrow_frame, from_=0, to=9, width=3)
        self.source_row.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.source_row.set(0)
        
        ttk.Label(arrow_frame, text="列:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.source_col = ttk.Spinbox(arrow_frame, from_=0, to=9, width=3)
        self.source_col.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.source_col.set(0)
        
        ttk.Label(arrow_frame, text="終点行列:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.target_matrix = ttk.Entry(arrow_frame, width=5)
        self.target_matrix.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.target_matrix.insert(0, "B")
        
        ttk.Label(arrow_frame, text="行:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.target_row = ttk.Spinbox(arrow_frame, from_=0, to=9, width=3)
        self.target_row.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.target_row.set(0)
        
        ttk.Label(arrow_frame, text="列:").grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        self.target_col = ttk.Spinbox(arrow_frame, from_=0, to=9, width=3)
        self.target_col.grid(row=1, column=5, padx=5, pady=5, sticky=tk.W)
        self.target_col.set(0)
        
        # 矢印スタイルフレーム
        style_frame = ttk.Frame(arrow_frame)
        style_frame.grid(row=2, column=0, columnspan=6, padx=5, pady=5, sticky=tk.W+tk.E)
        
        ttk.Label(style_frame, text="色:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.arrow_color = ttk.Entry(style_frame, width=10)
        self.arrow_color.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.arrow_color.insert(0, "red")
        
        color_btn = ttk.Button(style_frame, text="色選択", command=lambda: self.choose_color(self.arrow_color))
        color_btn.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(style_frame, text="スタイル:").grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.arrow_style = ttk.Combobox(style_frame, values=["-|>", "->>", "-[", "-|", "<->", "<-|>"], width=5)
        self.arrow_style.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.arrow_style.current(0)
        
        ttk.Label(style_frame, text="太さ:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.arrow_width = ttk.Spinbox(style_frame, from_=0.5, to=5.0, increment=0.5, width=5)
        self.arrow_width.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.arrow_width.set(2.0)
        
        ttk.Label(style_frame, text="ラベル:").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.arrow_label = ttk.Entry(style_frame, width=10)
        self.arrow_label.grid(row=1, column=4, padx=5, pady=5, sticky=tk.W)
        
        add_btn = ttk.Button(arrow_frame, text="矢印を追加", command=self.add_arrow)
        add_btn.grid(row=3, column=0, columnspan=6, padx=5, pady=5, sticky=tk.E+tk.W)
        self.create_tooltip(add_btn, "指定された始点と終点の間に矢印を追加します")
    
    def create_cell_tab(self, parent):
        """要素設定タブの内容を作成"""
        cell_setting_frame = ttk.LabelFrame(parent, text="要素の設定")
        cell_setting_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(cell_setting_frame, text="行列:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.cell_matrix = ttk.Entry(cell_setting_frame, width=5)
        self.cell_matrix.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.cell_matrix.insert(0, "A")
        
        ttk.Label(cell_setting_frame, text="行:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.cell_row = ttk.Spinbox(cell_setting_frame, from_=0, to=9, width=3)
        self.cell_row.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.cell_row.set(0)
        
        ttk.Label(cell_setting_frame, text="列:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.cell_col = ttk.Spinbox(cell_setting_frame, from_=0, to=9, width=3)
        self.cell_col.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.cell_col.set(0)
        
        ttk.Label(cell_setting_frame, text="値:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.cell_value = ttk.Entry(cell_setting_frame, width=8)
        self.cell_value.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.cell_value.insert(0, "0")
        
        ttk.Label(cell_setting_frame, text="色:").grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.cell_color = ttk.Entry(cell_setting_frame, width=10)
        self.cell_color.grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.cell_color.insert(0, "none")
        
        color_btn = ttk.Button(cell_setting_frame, text="色選択", command=lambda: self.choose_color(self.cell_color))
        color_btn.grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        set_btn = ttk.Button(cell_setting_frame, text="設定", command=self.update_cell)
        set_btn.grid(row=2, column=2, columnspan=4, padx=5, pady=5, sticky=tk.E+tk.W)
        self.create_tooltip(set_btn, "指定したセルの値と色を設定します")
        
        # 範囲選択フレーム
        range_frame = ttk.LabelFrame(parent, text="範囲選択")
        range_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(range_frame, text="始点行:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.range_start_row = ttk.Spinbox(range_frame, from_=0, to=9, width=3)
        self.range_start_row.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.range_start_row.set(0)
        
        ttk.Label(range_frame, text="始点列:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.range_start_col = ttk.Spinbox(range_frame, from_=0, to=9, width=3)
        self.range_start_col.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.range_start_col.set(0)
        
        ttk.Label(range_frame, text="終点行:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.range_end_row = ttk.Spinbox(range_frame, from_=0, to=9, width=3)
        self.range_end_row.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.range_end_row.set(0)
        
        ttk.Label(range_frame, text="終点列:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.range_end_col = ttk.Spinbox(range_frame, from_=0, to=9, width=3)
        self.range_end_col.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.range_end_col.set(0)
        
        ttk.Label(range_frame, text="色:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.range_color = ttk.Entry(range_frame, width=10)
        self.range_color.grid(row=2, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.range_color.insert(0, "lightblue")
        
        color_btn = ttk.Button(range_frame, text="色選択", command=lambda: self.choose_color(self.range_color))
        color_btn.grid(row=2, column=3, padx=5, pady=5, sticky=tk.W)
        
        apply_btn = ttk.Button(range_frame, text="範囲に適用", command=self.apply_color_to_range)
        apply_btn.grid(row=3, column=0, columnspan=4, padx=5, pady=5, sticky=tk.E+tk.W)
        self.create_tooltip(apply_btn, "指定した範囲内のすべてのセルに色を適用します")
    
    def create_expr_tab(self, parent):
        """行列式タブの内容を作成"""
        expr_frame = ttk.LabelFrame(parent, text="行列式入力")
        expr_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(expr_frame, text="式:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.expr_entry = ttk.Entry(expr_frame, width=40)
        self.expr_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.expr_entry.insert(0, "A + B = C")
        
        eval_btn = ttk.Button(expr_frame, text="式を評価", command=self.evaluate_expression)
        eval_btn.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=tk.E+tk.W)
        self.create_tooltip(eval_btn, "入力した行列式を評価して可視化します")
        
        # 演算子ボタン群
        op_frame = ttk.LabelFrame(parent, text="演算子")
        op_frame.pack(fill=tk.X, padx=5, pady=5)
        
        operators = ['+', '-', '*', '^', 'Det(', 'Tr(', '=']
        for i, op in enumerate(operators):
            btn = ttk.Button(op_frame, text=op, width=5, 
                         command=partial(self.insert_operator, op))
            btn.grid(row=i//4, column=i%4, padx=5, pady=5)
        
        # テンプレート式
        template_frame = ttk.LabelFrame(parent, text="テンプレート式")
        template_frame.pack(fill=tk.X, padx=5, pady=5)
        
        templates = [
            ("A + B", "行列加算"),
            ("A * B", "行列乗算"),
            ("A^2", "行列べき乗"),
            ("Det(A)", "行列式"),
            ("Tr(A)", "トレース"),
            ("A + B = C", "行列等式")
        ]
        
        for i, (template, desc) in enumerate(templates):
            btn = ttk.Button(template_frame, text=desc, 
                         command=partial(self.load_template, template))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.E+tk.W)
            self.create_tooltip(btn, f"式テンプレート: {template}")
        
        # 式の説明テキスト
        ttk.Label(parent, text="式の例: A + B = C, Det(A), A^2, Tr(B)").pack(padx=5, pady=5, anchor=tk.W)
        ttk.Label(parent, text="演算子優先順位: かっこ > べき乗 > 乗算 > 加減算").pack(padx=5, pady=5, anchor=tk.W)
    
    def create_console_tab(self, parent):
        """コンソールタブの内容を作成"""
        console_frame = ttk.LabelFrame(parent, text="コマンドコンソール")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # 複数行入力用テキストエリア
        self.console_text = tk.Text(console_frame, height=10, width=50, wrap=tk.WORD)
        self.console_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # コマンド実行ボタンと例
        button_frame = ttk.Frame(console_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        execute_btn = ttk.Button(button_frame, text="実行", command=self.execute_console_commands)
        execute_btn.pack(side=tk.LEFT, padx=5)
        self.create_tooltip(execute_btn, "コンソールに入力されたすべてのコマンドを実行します")
        
        clear_btn = ttk.Button(button_frame, text="クリア", command=lambda: self.console_text.delete(1.0, tk.END))
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # サンプルコマンドボタン
        samples_frame = ttk.LabelFrame(parent, text="サンプルコマンド")
        samples_frame.pack(fill=tk.X, padx=5, pady=5)
        
        sample_commands = [
            ("行列定義", "A := [3, 3] @ (0, 0)"),
            ("矢印追加", "A[0][0] -> B[1][1] : red"),
            ("要素の色", "A[0][0] : lightblue"),
            ("複数コマンド", "A := [2, 2] @ (0, 0)\nB := [2, 2] @ (3, 0)\nA[0][0] -> B[0][0] : green")
        ]
        
        for i, (desc, cmd) in enumerate(sample_commands):
            btn = ttk.Button(samples_frame, text=desc, 
                         command=partial(self.load_sample_command, cmd))
            btn.grid(row=i//2, column=i%2, padx=5, pady=5, sticky=tk.E+tk.W)
            self.create_tooltip(btn, f"コマンド例: {cmd}")
        
        # コマンド履歴表示
        history_frame = ttk.LabelFrame(parent, text="コマンド履歴")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.console_history = tk.Text(history_frame, height=8, width=50, wrap=tk.WORD)
        self.console_history.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.console_history.config(state=tk.DISABLED)
        
        clear_history_btn = ttk.Button(history_frame, text="履歴をクリア", 
                                   command=lambda: self.clear_history())
        clear_history_btn.pack(padx=5, pady=5, anchor=tk.E)
    
    def create_list_tab(self, parent):
        """定義済みリストタブの内容を作成"""
        matrices_frame = ttk.LabelFrame(parent, text="定義済み行列")
        matrices_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        matrices_list_frame = ttk.Frame(matrices_frame)
        matrices_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.matrices_listbox = tk.Listbox(matrices_list_frame, height=8)
        matrices_scrollbar = ttk.Scrollbar(matrices_list_frame, orient=tk.VERTICAL, command=self.matrices_listbox.yview)
        self.matrices_listbox.config(yscrollcommand=matrices_scrollbar.set)
        
        self.matrices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        matrices_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.matrices_listbox.bind('<<ListboxSelect>>', self.on_matrix_select)
        
        matrices_buttons_frame = ttk.Frame(matrices_frame)
        matrices_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        delete_matrix_btn = ttk.Button(matrices_buttons_frame, text="削除", command=self.delete_matrix)
        delete_matrix_btn.pack(side=tk.LEFT, padx=5)
        
        edit_matrix_btn = ttk.Button(matrices_buttons_frame, text="編集", command=self.edit_matrix)
        edit_matrix_btn.pack(side=tk.LEFT, padx=5)
        
        duplicate_matrix_btn = ttk.Button(matrices_buttons_frame, text="複製", command=self.duplicate_matrix)
        duplicate_matrix_btn.pack(side=tk.LEFT, padx=5)
        
        # 矢印リスト
        arrows_frame = ttk.LabelFrame(parent, text="定義済み矢印")
        arrows_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        arrows_list_frame = ttk.Frame(arrows_frame)
        arrows_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.arrows_listbox = tk.Listbox(arrows_list_frame, height=6)
        arrows_scrollbar = ttk.Scrollbar(arrows_list_frame, orient=tk.VERTICAL, command=self.arrows_listbox.yview)
        self.arrows_listbox.config(yscrollcommand=arrows_scrollbar.set)
        
        self.arrows_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        arrows_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.arrows_listbox.bind('<<ListboxSelect>>', self.on_arrow_select)
        
        arrows_buttons_frame = ttk.Frame(arrows_frame)
        arrows_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        delete_arrow_btn = ttk.Button(arrows_buttons_frame, text="削除", command=self.delete_arrow)
        delete_arrow_btn.pack(side=tk.LEFT, padx=5)
        
        edit_arrow_btn = ttk.Button(arrows_buttons_frame, text="編集", command=self.edit_arrow)
        edit_arrow_btn.pack(side=tk.LEFT, padx=5)
        
        # 色付き要素リスト
        colored_cells_frame = ttk.LabelFrame(parent, text="色付き要素")
        colored_cells_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        colored_cells_list_frame = ttk.Frame(colored_cells_frame)
        colored_cells_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.colored_cells_listbox = tk.Listbox(colored_cells_list_frame, height=6)
        colored_cells_scrollbar = ttk.Scrollbar(colored_cells_list_frame, orient=tk.VERTICAL, command=self.colored_cells_listbox.yview)
        self.colored_cells_listbox.config(yscrollcommand=colored_cells_scrollbar.set)
        
        self.colored_cells_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        colored_cells_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.colored_cells_listbox.bind('<<ListboxSelect>>', self.on_colored_cell_select)
        
        colored_cells_buttons_frame = ttk.Frame(colored_cells_frame)
        colored_cells_buttons_frame.pack(fill=tk.X, padx=5, pady=5)
        
        delete_cell_btn = ttk.Button(colored_cells_buttons_frame, text="削除", command=self.delete_colored_cell)
        delete_cell_btn.pack(side=tk.LEFT, padx=5)
        
        edit_cell_btn = ttk.Button(colored_cells_buttons_frame, text="編集", command=self.edit_colored_cell)
        edit_cell_btn.pack(side=tk.LEFT, padx=5)
    
    #------------------------
    # ユーティリティ関数
    #------------------------
    
    def create_tooltip(self, widget, text):
        """ウィジェットにツールチップを追加"""
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 25
            
            # ツールチップウィンドウを作成
            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")
            
            label = ttk.Label(self.tooltip, text=text, justify=tk.LEFT,
                          background="#ffffe0", relief=tk.SOLID, borderwidth=1)
            label.pack(padx=3, pady=3)
        
        def leave(event):
            if self.tooltip:
                self.tooltip.destroy()
                self.tooltip = None
        
        widget.bind("<Enter>", enter)
        widget.bind("<Leave>", leave)
    
    def on_mouse_move(self, event):
        """マウス移動時のイベントハンドラ"""
        # キャンバス上の位置を取得
        x, y = event.x, event.y
        
        # データ座標に変換
        data_x, data_y = self.ax.transData.inverted().transform((x, y))
        
        # セルの位置を特定
        cell_x, cell_y = int(data_x), int(-data_y - 1)
        
        # 行列内のセルかどうかを判定
        for name, matrix_data in self.matrices.items():
            pos_x, pos_y = matrix_data['position']
            rows, cols = matrix_data['values'].shape
            
            if (pos_x <= data_x < pos_x + cols and 
                -pos_y - rows <= data_y < -pos_y):
                
                # インデックスを計算
                i = int(-data_y - pos_y - 1)
                j = int(data_x - pos_x)
                
                if 0 <= i < rows and 0 <= j < cols:
                    # セル情報を表示
                    value = matrix_data['values'][i, j]
                    self.status_var.set(f"行列: {name}, 行: {i}, 列: {j}, 値: {value}")
                    
                    # 選択した要素を記録
                    self.last_selected_matrix = name
                    self.last_selected_cell = (i, j)
                    return
        
        # 行列外の場合
        self.status_var.set("準備完了")
        self.last_selected_matrix = None
        self.last_selected_cell = None
    
    def choose_color(self, entry_widget):
        """色選択ダイアログを表示して結果をエントリウィジェットに設定"""
        current_color = entry_widget.get()
        if current_color in mpl.colors.CSS4_COLORS:
            # 名前付きカラーをRGBに変換
            rgb = mpl.colors.to_rgb(current_color)
            initial_color = "#{:02x}{:02x}{:02x}".format(
                int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
        elif mpl.colors.is_color_like(current_color):
            # 既にカラーコードの場合
            initial_color = current_color
        else:
            # デフォルト色
            initial_color = "#ff0000"
        
        color = colorchooser.askcolor(initialcolor=initial_color)
        if color[1]:  # カラーコードが返された場合
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, color[1])
    
    def load_template(self, template):
        """式テンプレートを読み込む"""
        self.expr_entry.delete(0, tk.END)
        self.expr_entry.insert(0, template)
    
    def insert_operator(self, operator):
        """演算子を式エントリに挿入"""
        current_pos = self.expr_entry.index(tk.INSERT)
        self.expr_entry.insert(current_pos, operator)
    
    def load_sample_command(self, command):
        """サンプルコマンドをコンソールに読み込む"""
        self.console_text.delete(1.0, tk.END)
        self.console_text.insert(1.0, command)
    
    def clear_history(self):
        """コマンド履歴をクリア"""
        self.console_history.config(state=tk.NORMAL)
        self.console_history.delete(1.0, tk.END)
        self.console_history.config(state=tk.DISABLED)
    
    def generate_random_matrix(self):
        """ランダム値の行列を生成"""
        try:
            min_val = int(self.random_min.get())
            max_val = int(self.random_max.get())
            rows = int(self.rows.get())
            cols = int(self.cols.get())
            
            matrix_name = self.matrix_name.get().strip()
            pos_x = float(self.pos_x.get())
            pos_y = float(self.pos_y.get())
            
            # ランダム行列を生成
            values = np.random.randint(min_val, max_val + 1, size=(rows, cols))
            
            # 行列を保存
            self.matrices[matrix_name] = {
                'values': values,
                'position': (pos_x, pos_y),
                'rows': rows,
                'cols': cols
            }
            
            # リストボックスを更新
            self.update_matrices_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            self.status_var.set(f"ランダム行列 '{matrix_name}' を生成しました")
            
        except ValueError as e:
            messagebox.showerror("エラー", f"ランダム行列の生成に失敗しました: {str(e)}")
    
    def generate_special_matrix(self, matrix_type):
        """特殊行列を生成"""
        try:
            matrix_name = self.matrix_name.get().strip()
            rows = int(self.rows.get())
            cols = int(self.cols.get())
            pos_x = float(self.pos_x.get())
            pos_y = float(self.pos_y.get())
            
            if matrix_type == "identity":
                if rows != cols:
                    messagebox.showerror("エラー", "単位行列は正方行列である必要があります")
                    return
                values = np.eye(rows, dtype=int)
            
            elif matrix_type == "zeros":
                values = np.zeros((rows, cols), dtype=int)
            
            elif matrix_type == "ones":
                values = np.ones((rows, cols), dtype=int)
            
            elif matrix_type == "upper":
                if rows != cols:
                    messagebox.showerror("エラー", "上三角行列は正方行列である必要があります")
                    return
                values = np.triu(np.ones((rows, cols), dtype=int))
                # 1から順に埋める
                counter = 1
                for i in range(rows):
                    for j in range(i, cols):
                        values[i, j] = counter
                        counter += 1
            
            elif matrix_type == "lower":
                if rows != cols:
                    messagebox.showerror("エラー", "下三角行列は正方行列である必要があります")
                    return
                values = np.tril(np.ones((rows, cols), dtype=int))
                # 1から順に埋める
                counter = 1
                for i in range(rows):
                    for j in range(i + 1):
                        values[i, j] = counter
                        counter += 1
            
            elif matrix_type == "diagonal":
                if rows != cols:
                    messagebox.showerror("エラー", "対角行列は正方行列である必要があります")
                    return
                values = np.zeros((rows, cols), dtype=int)
                # 対角成分を1から順に埋める
                for i in range(rows):
                    values[i, i] = i + 1
            
            # 行列を保存
            self.matrices[matrix_name] = {
                'values': values,
                'position': (pos_x, pos_y),
                'rows': rows,
                'cols': cols
            }
            
            # リストボックスを更新
            self.update_matrices_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            matrix_type_names = {
                "identity": "単位行列",
                "zeros": "零行列",
                "ones": "1行列",
                "upper": "上三角行列",
                "lower": "下三角行列",
                "diagonal": "対角行列"
            }
            
            self.status_var.set(f"{matrix_type_names[matrix_type]} '{matrix_name}' を生成しました")
            
        except ValueError as e:
            messagebox.showerror("エラー", f"特殊行列の生成に失敗しました: {str(e)}")
    
    def apply_color_to_range(self):
        """指定された範囲のセルに色を適用"""
        matrix_name = self.cell_matrix.get().strip()
        
        # 行列が存在するか確認
        if matrix_name not in self.matrices:
            messagebox.showerror("エラー", f"行列 '{matrix_name}' が定義されていません。")
            return
        
        # 範囲の確認
        try:
            start_row = int(self.range_start_row.get())
            start_col = int(self.range_start_col.get())
            end_row = int(self.range_end_row.get())
            end_col = int(self.range_end_col.get())
            
            matrix_rows = self.matrices[matrix_name]['rows']
            matrix_cols = self.matrices[matrix_name]['cols']
            
            # 範囲のバリデーション
            if (start_row < 0 or start_row >= matrix_rows or 
                start_col < 0 or start_col >= matrix_cols or
                end_row < 0 or end_row >= matrix_rows or
                end_col < 0 or end_col >= matrix_cols):
                raise ValueError(f"範囲が行列の境界外です。行: 0-{matrix_rows-1}, 列: 0-{matrix_cols-1}")
            
            # 範囲の整理（始点 <= 終点になるようにする）
            if start_row > end_row:
                start_row, end_row = end_row, start_row
            if start_col > end_col:
                start_col, end_col = end_col, start_col
                
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        # 色の確認
        color = self.range_color.get().strip()
        if color and color.lower() != "none":
            try:
                # 色名の検証
                if not (color in mpl.colors.CSS4_COLORS or mpl.colors.is_color_like(color)):
                    raise ValueError(f"'{color}' は有効な色名またはカラーコードではありません。")
                
                # 範囲内の各セルに色を適用
                for row in range(start_row, end_row + 1):
                    for col in range(start_col, end_col + 1):
                        # 既存の色設定を削除
                        self.colored_cells = [cell for cell in self.colored_cells 
                                          if not (cell['matrix'] == matrix_name and cell['row'] == row and cell['col'] == col)]
                        
                        # 色設定を追加
                        self.colored_cells.append({
                            'matrix': matrix_name,
                            'row': row,
                            'col': col,
                            'color': color
                        })
                
                # 色付き要素リストを更新
                self.update_colored_cells_listbox()
                
                # 可視化を更新
                self.visualize_matrices()
                
                self.status_var.set(f"範囲 ({start_row},{start_col}) から ({end_row},{end_col}) に色 '{color}' を適用しました")
                
            except ValueError as e:
                messagebox.showerror("エラー", str(e))
                return
        elif color.lower() == "none":
            # 範囲内の色設定を削除
            for row in range(start_row, end_row + 1):
                for col in range(start_col, end_col + 1):
                    self.colored_cells = [cell for cell in self.colored_cells 
                                       if not (cell['matrix'] == matrix_name and cell['row'] == row and cell['col'] == col)]
            
            # 色付き要素リストを更新
            self.update_colored_cells_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            self.status_var.set(f"範囲 ({start_row},{start_col}) から ({end_row},{end_col}) の色を削除しました")
    
    def edit_matrix(self):
        """選択された行列を編集"""
        if not self.matrices_listbox.curselection():
            messagebox.showinfo("情報", "編集する行列を選択してください。")
            return
        
        index = self.matrices_listbox.curselection()[0]
        selected_matrix = self.matrices_listbox.get(index).split()[0]
        
        if selected_matrix in self.matrices:
            # 編集ダイアログを表示
            self.show_matrix_editor(selected_matrix)
    
    def duplicate_matrix(self):
        """選択された行列を複製"""
        if not self.matrices_listbox.curselection():
            messagebox.showinfo("情報", "複製する行列を選択してください。")
            return
        
        index = self.matrices_listbox.curselection()[0]
        selected_matrix = self.matrices_listbox.get(index).split()[0]
        
        if selected_matrix in self.matrices:
            # 新しい行列名を生成
            new_name = selected_matrix + "_copy"
            counter = 1
            while new_name in self.matrices:
                counter += 1
                new_name = f"{selected_matrix}_copy{counter}"
            
            # 行列データをコピー
            original_data = self.matrices[selected_matrix]
            self.matrices[new_name] = {
                'values': original_data['values'].copy(),
                'position': (original_data['position'][0] + 1, original_data['position'][1] + 1),  # 少しずらす
                'rows': original_data['rows'],
                'cols': original_data['cols']
            }
            
            # リストを更新
            self.update_matrices_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            self.status_var.set(f"行列 '{selected_matrix}' を '{new_name}' として複製しました")
    
    def show_matrix_editor(self, matrix_name):
        """行列編集ダイアログを表示"""
        if matrix_name not in self.matrices:
            return
        
        # 行列データ
        matrix_data = self.matrices[matrix_name]
        values = matrix_data['values']
        rows, cols = values.shape
        
        # ダイアログを作成
        editor = tk.Toplevel(self.root)
        editor.title(f"行列 '{matrix_name}' の編集")
        editor.geometry("600x400")
        editor.transient(self.root)
        editor.grab_set()
        
        # フレームを作成
        frame = ttk.Frame(editor, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # スクロール可能なキャンバス
        canvas = tk.Canvas(frame, bg="#f0f0f0")
        scrollbar_y = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar_x = ttk.Scrollbar(frame, orient=tk.HORIZONTAL, command=canvas.xview)
        
        # スクロール可能なフレーム
        content_frame = ttk.Frame(canvas)
        
        # スクロールバーとキャンバスの連携
        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # キャンバスにフレームを配置
        canvas_frame = canvas.create_window((0, 0), window=content_frame, anchor=tk.NW)
        
        # キャンバスの幅をフレームに合わせる
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        
        # レイアウト
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # スクロールバーとキャンバスの連携
        canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # エントリウィジェットの配列を作成
        entries = []
        for i in range(rows):
            row_entries = []
            for j in range(cols):
                entry = ttk.Entry(content_frame, width=6)
                entry.grid(row=i+1, column=j+1, padx=2, pady=2)
                entry.insert(0, str(values[i, j]))
                row_entries.append(entry)
            entries.append(row_entries)
        
        # 行と列のラベル
        for i in range(rows):
            ttk.Label(content_frame, text=f"行 {i}").grid(row=i+1, column=0, padx=5, pady=2, sticky=tk.E)
        
        for j in range(cols):
            ttk.Label(content_frame, text=f"列 {j}").grid(row=0, column=j+1, padx=2, pady=5)
        
        # ボタンフレーム
        button_frame = ttk.Frame(editor)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 位置編集フレーム
        pos_frame = ttk.LabelFrame(button_frame, text="行列位置")
        pos_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(pos_frame, text="X:").grid(row=0, column=0, padx=5, pady=5)
        pos_x_entry = ttk.Spinbox(pos_frame, from_=0, to=20, width=5)
        pos_x_entry.grid(row=0, column=1, padx=5, pady=5)
        pos_x_entry.set(str(matrix_data['position'][0]))
        
        ttk.Label(pos_frame, text="Y:").grid(row=0, column=2, padx=5, pady=5)
        pos_y_entry = ttk.Spinbox(pos_frame, from_=0, to=20, width=5)
        pos_y_entry.grid(row=0, column=3, padx=5, pady=5)
        pos_y_entry.set(str(matrix_data['position'][1]))
        
        # 行列名変更フレーム
        name_frame = ttk.LabelFrame(button_frame, text="行列名")
        name_frame.pack(side=tk.LEFT, padx=10)
        
        ttk.Label(name_frame, text="新名前:").grid(row=0, column=0, padx=5, pady=5)
        name_entry = ttk.Entry(name_frame, width=10)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        name_entry.insert(0, matrix_name)
        
        # ボタン配置
        ttk.Button(button_frame, text="保存", 
                command=lambda: self.save_matrix_edits(
                    matrix_name, name_entry.get(), entries, 
                    float(pos_x_entry.get()), float(pos_y_entry.get()), editor)).pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(button_frame, text="キャンセル", 
                command=editor.destroy).pack(side=tk.RIGHT, padx=10)
    
    def save_matrix_edits(self, old_name, new_name, entries, pos_x, pos_y, dialog):
        """行列編集の保存"""
        # 新しい行列名のバリデーション
        if new_name in self.reserved_words:
            messagebox.showerror("エラー", f"'{new_name}' は予約語のため、行列名として使用できません。", parent=dialog)
            return
        
        if not new_name:
            messagebox.showerror("エラー", "行列名を入力してください。", parent=dialog)
            return
        
        # 名前が変更された場合、既存の行列と重複しないか確認
        if new_name != old_name and new_name in self.matrices:
            messagebox.showerror("エラー", f"行列 '{new_name}' は既に存在します。", parent=dialog)
            return
        
        # エントリから値を取得
        rows = len(entries)
        cols = len(entries[0]) if rows > 0 else 0
        
        new_values = np.zeros((rows, cols))
        
        try:
            for i in range(rows):
                for j in range(cols):
                    value = entries[i][j].get()
                    if value:
                        # 数値に変換
                        new_values[i, j] = float(value) if '.' in value else int(value)
        except ValueError:
            messagebox.showerror("エラー", "すべての値は数値である必要があります。", parent=dialog)
            return
        
        # 古い行列のデータを保存
        old_matrix_data = self.matrices[old_name]
        
        # 行列を更新
        if new_name != old_name:
            # 名前が変わった場合は古い行列を削除し、新しい行列を追加
            del self.matrices[old_name]
            
            # 関連する矢印と色付き要素を更新
            for arrow in self.arrows:
                if arrow['source'][0] == old_name:
                    arrow['source'] = (new_name, arrow['source'][1], arrow['source'][2])
                if arrow['target'][0] == old_name:
                    arrow['target'] = (new_name, arrow['target'][1], arrow['target'][2])
            
            for cell in self.colored_cells:
                if cell['matrix'] == old_name:
                    cell['matrix'] = new_name
        
        # 新しい行列データを保存
        self.matrices[new_name] = {
            'values': new_values,
            'position': (pos_x, pos_y),
            'rows': rows,
            'cols': cols
        }
        
        # リストを更新
        self.update_matrices_listbox()
        self.update_arrows_listbox()
        self.update_colored_cells_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
        
        # ダイアログを閉じる
        dialog.destroy()
        
        if new_name != old_name:
            self.status_var.set(f"行列 '{old_name}' を '{new_name}' に変更し、更新しました")
        else:
            self.status_var.set(f"行列 '{new_name}' を更新しました")
    
    def edit_arrow(self):
        """選択された矢印を編集"""
        if not self.arrows_listbox.curselection():
            messagebox.showinfo("情報", "編集する矢印を選択してください。")
            return
        
        index = self.arrows_listbox.curselection()[0]
        
        if 0 <= index < len(self.arrows):
            # 矢印データを取得して編集フォームに設定
            arrow_data = self.arrows[index]
            
            self.source_matrix.delete(0, tk.END)
            self.source_matrix.insert(0, arrow_data['source'][0])
            
            self.source_row.delete(0, tk.END)
            self.source_row.insert(0, str(arrow_data['source'][1]))
            
            self.source_col.delete(0, tk.END)
            self.source_col.insert(0, str(arrow_data['source'][2]))
            
            self.target_matrix.delete(0, tk.END)
            self.target_matrix.insert(0, arrow_data['target'][0])
            
            self.target_row.delete(0, tk.END)
            self.target_row.insert(0, str(arrow_data['target'][1]))
            
            self.target_col.delete(0, tk.END)
            self.target_col.insert(0, str(arrow_data['target'][2]))
            
            self.arrow_color.delete(0, tk.END)
            self.arrow_color.insert(0, arrow_data['color'])
            
            # スタイルと太さの設定（もし存在するなら）
            if 'style' in arrow_data:
                self.arrow_style.set(arrow_data['style'])
            
            if 'width' in arrow_data:
                self.arrow_width.delete(0, tk.END)
                self.arrow_width.insert(0, str(arrow_data['width']))
            
            if 'label' in arrow_data and arrow_data['label']:
                self.arrow_label.delete(0, tk.END)
                self.arrow_label.insert(0, arrow_data['label'])
            
            # 矢印を削除（後で更新される）
            del self.arrows[index]
            self.update_arrows_listbox()
            self.visualize_matrices()
            
            self.status_var.set(f"矢印 {index+1} を編集モードにしました。編集後に「矢印を追加」をクリックしてください。")
    
    def edit_colored_cell(self):
        """選択された色付き要素を編集"""
        if not self.colored_cells_listbox.curselection():
            messagebox.showinfo("情報", "編集する色付き要素を選択してください。")
            return
        
        index = self.colored_cells_listbox.curselection()[0]
        
        if 0 <= index < len(self.colored_cells):
            # 色付き要素データを取得して編集フォームに設定
            cell_data = self.colored_cells[index]
            
            self.cell_matrix.delete(0, tk.END)
            self.cell_matrix.insert(0, cell_data['matrix'])
            
            self.cell_row.delete(0, tk.END)
            self.cell_row.insert(0, str(cell_data['row']))
            
            self.cell_col.delete(0, tk.END)
            self.cell_col.insert(0, str(cell_data['col']))
            
            self.cell_color.delete(0, tk.END)
            self.cell_color.insert(0, cell_data['color'])
            
            # 値も設定
            if cell_data['matrix'] in self.matrices:
                value = self.matrices[cell_data['matrix']]['values'][cell_data['row'], cell_data['col']]
                self.cell_value.delete(0, tk.END)
                self.cell_value.insert(0, str(value))
            
            # 色付き要素を削除（後で更新される）
            del self.colored_cells[index]
            self.update_colored_cells_listbox()
            self.visualize_matrices()
            
            self.status_var.set(f"色付き要素 {index+1} を編集モードにしました。編集後に「設定」をクリックしてください。")
    
    def zoom(self, factor):
        """表示を拡大または縮小"""
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()
        
        # 中心点を計算
        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2
        
        # 新しい範囲を計算
        width = (x_max - x_min) / factor
        height = (y_max - y_min) / factor
        
        self.ax.set_xlim(center_x - width/2, center_x + width/2)
        self.ax.set_ylim(center_y - height/2, center_y + height/2)
        
        # キャンバスを更新
        self.canvas.draw()
        
        zoom_type = "拡大" if factor > 1 else "縮小"
        self.status_var.set(f"表示を{zoom_type}しました")
    
    def reset_view(self):
        """表示範囲をリセット"""
        self.adjust_plot_limits()
        self.canvas.draw()
        self.status_var.set("表示範囲をリセットしました")
    
    def toggle_grid(self):
        """グリッド表示を切り替え"""
        self.ax.grid(not self.ax.xaxis._gridOnMajor)
        self.canvas.draw()
        
        grid_status = "表示" if self.ax.xaxis._gridOnMajor else "非表示"
        self.status_var.set(f"グリッドを{grid_status}にしました")
    
    def copy_matrix_to_clipboard(self):
        """選択された行列をクリップボードにコピー"""
        if not self.matrices_listbox.curselection() and self.last_selected_matrix is None:
            messagebox.showinfo("情報", "コピーする行列を選択してください。")
            return
        
        # リストボックスでの選択を優先
        if self.matrices_listbox.curselection():
            index = self.matrices_listbox.curselection()[0]
            selected_matrix = self.matrices_listbox.get(index).split()[0]
        else:
            selected_matrix = self.last_selected_matrix
        
        if selected_matrix in self.matrices:
            matrix_data = self.matrices[selected_matrix]
            values = matrix_data['values']
            
            # 行列をテキスト形式に変換
            text = f"行列 {selected_matrix}:\n"
            for row in values:
                text += " ".join(str(val) for val in row) + "\n"
            
            # クリップボードにコピー
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            
            self.status_var.set(f"行列 '{selected_matrix}' をクリップボードにコピーしました")
    
    def select_all(self):
        """フォーカスされたウィジェットの全選択"""
        focused = self.root.focus_get()
        if isinstance(focused, tk.Entry):
            focused.select_range(0, tk.END)
        elif isinstance(focused, tk.Text):
            focused.tag_add(tk.SEL, "1.0", tk.END)
    
    def show_commands_help(self):
        """コマンド一覧ヘルプを表示"""
        help_text = """コマンド一覧:

        1. 行列定義:
        A := [3, 3] @ (0, 0)
        （行列名 := [行, 列] @ (位置X, 位置Y)）

        2. 矢印定義:
        A[0][0] -> B[1][1] : red
        （始点行列[行][列] -> 終点行列[行][列] : 色）

        3. 要素の色設定:
        A[0][0] : lightblue
        （行列[行][列] : 色）

        4. 複数のコマンドは改行で区切って実行できます。

        ※ 色は色名（red, blue）またはカラーコード（#FF0000）で指定できます。
        """
        
        help_dialog = tk.Toplevel(self.root)
        help_dialog.title("コマンド一覧")
        help_dialog.geometry("500x400")
        help_dialog.transient(self.root)
        
        text = tk.Text(help_dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, help_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(help_dialog, text="閉じる", command=help_dialog.destroy).pack(pady=10)
    
    def show_shortcuts(self):
        """ショートカットキー一覧を表示"""
        shortcuts_text = """ショートカットキー一覧:

        ファイル操作:
        Ctrl+N: 新規（すべてリセット）
        Ctrl+S: PNG形式で保存
        Ctrl+P: PDF形式で保存
        Alt+F4: 終了

        編集操作:
        Ctrl+C: 選択した行列をクリップボードにコピー
        Ctrl+A: すべて選択

        表示操作:
        Ctrl++: 拡大
        Ctrl+-: 縮小
        Ctrl+0: ビューをリセット

        その他:
        Tab: フィールド間を移動
        Enter: コマンド実行（コンソールフォーカス時）
        """
        
        shortcuts_dialog = tk.Toplevel(self.root)
        shortcuts_dialog.title("ショートカットキー一覧")
        shortcuts_dialog.geometry("500x400")
        shortcuts_dialog.transient(self.root)
        
        text = tk.Text(shortcuts_dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, shortcuts_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(shortcuts_dialog, text="閉じる", command=shortcuts_dialog.destroy).pack(pady=10)
    
    def show_about(self):
        """このアプリについての情報を表示"""
        about_text = """行列演算可視化ツール

        バージョン: 2.0

        このアプリケーションは行列演算を視覚的に表現するためのツールです。
        行列の定義、演算、そして視覚的な表現を簡単に行うことができます。

        主な機能:
        - 行列の作成と編集
        - 矢印による要素間の関係の表示
        - 色を使った要素の強調
        - 行列式の評価と視覚化
        - コマンドラインによる操作

        開発者: 行列視覚化研究チーム
        """
        
        about_dialog = tk.Toplevel(self.root)
        about_dialog.title("このアプリについて")
        about_dialog.geometry("500x400")
        about_dialog.transient(self.root)
        
        text = tk.Text(about_dialog, wrap=tk.WORD)
        text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text.insert(tk.END, about_text)
        text.config(state=tk.DISABLED)
        
        ttk.Button(about_dialog, text="閉じる", command=about_dialog.destroy).pack(pady=10)
    
    #------------------------
    # 元の機能の実装
    #------------------------
    
    def on_matrix_select(self, event):
        """リストボックスで行列を選択したときのイベントハンドラ"""
        if self.matrices_listbox.curselection():
            index = self.matrices_listbox.curselection()[0]
            selected_matrix = self.matrices_listbox.get(index).split()[0]  # 行列名を取得
            
            if selected_matrix in self.matrices:
                matrix_data = self.matrices[selected_matrix]
                
                # 行列定義のフィールドを更新
                self.matrix_name.delete(0, tk.END)
                self.matrix_name.insert(0, selected_matrix)
                
                self.rows.delete(0, tk.END)
                self.rows.insert(0, str(matrix_data['rows']))
                
                self.cols.delete(0, tk.END)
                self.cols.insert(0, str(matrix_data['cols']))
                
                self.pos_x.delete(0, tk.END)
                self.pos_x.insert(0, str(matrix_data['position'][0]))
                
                self.pos_y.delete(0, tk.END)
                self.pos_y.insert(0, str(matrix_data['position'][1]))
                
                self.status_var.set(f"行列 '{selected_matrix}' を選択しました")
                
                # 行列を強調表示（一時的に枠を変更）
                for name, data in self.matrices.items():
                    pos_x, pos_y = data['position']
                    rows, cols = data['values'].shape
                    
                    if name == selected_matrix:
                        # 選択された行列を強調
                        rect = patches.Rectangle((pos_x-0.2, -(pos_y-0.2)-rows-0.2), cols+0.4, rows+0.4, 
                                             linewidth=2, edgecolor='blue', facecolor='none', linestyle='--')
                        self.ax.add_patch(rect)
                
                # キャンバスを更新
                self.canvas.draw()

    def reset_all(self):
        """すべてのデータをリセット"""
        if messagebox.askyesno("確認", "すべての行列、矢印、色付き要素をリセットしますか？"):
            self.matrices = {}
            self.arrows = []
            self.colored_cells = []
            self.matrices_listbox.delete(0, tk.END)
            self.arrows_listbox.delete(0, tk.END)
            self.colored_cells_listbox.delete(0, tk.END)
            self.ax.clear()
            self.ax.set_title('行列演算の可視化', fontsize=16, color='black' if not self.is_dark_mode else 'white')
            self.ax.axis('off')
            self.canvas.draw()
            self.status_var.set("すべてのデータをリセットしました")

    def update_matrices_listbox(self):
        """行列リストを更新"""
        self.matrices_listbox.delete(0, tk.END)
        for name, matrix_data in self.matrices.items():
            shape = f"{matrix_data['rows']}x{matrix_data['cols']}"
            pos = f"位置: ({matrix_data['position'][0]}, {matrix_data['position'][1]})"
            self.matrices_listbox.insert(tk.END, f"{name} ({shape}) - {pos}")

    def update_arrows_listbox(self):
        """矢印リストを更新"""
        self.arrows_listbox.delete(0, tk.END)
        for i, arrow in enumerate(self.arrows):
            source = f"{arrow['source'][0]}[{arrow['source'][1]},{arrow['source'][2]}]"
            target = f"{arrow['target'][0]}[{arrow['target'][1]},{arrow['target'][2]}]"
            style_info = f" {arrow.get('style', '-|>')} {arrow.get('width', 2.0)}"
            self.arrows_listbox.insert(tk.END, f"{i+1}: {source} → {target} ({arrow['color']}{style_info})")

    def update_colored_cells_listbox(self):
        """色付き要素リストを更新"""
        self.colored_cells_listbox.delete(0, tk.END)
        for i, cell in enumerate(self.colored_cells):
            value = "?"
            if cell['matrix'] in self.matrices:
                if 0 <= cell['row'] < self.matrices[cell['matrix']]['rows'] and \
                0 <= cell['col'] < self.matrices[cell['matrix']]['cols']:
                    value = str(self.matrices[cell['matrix']]['values'][cell['row'], cell['col']])
            
            self.colored_cells_listbox.insert(tk.END, 
                f"{i+1}: {cell['matrix']}[{cell['row']},{cell['col']}] = {value} ({cell['color']})")

    def save_matrix_data(self, file_path):
        """行列データをJSONファイルに保存"""
        try:
            # 行列データの変換
            matrices_data = []
            for name, matrix_data in self.matrices.items():
                matrices_data.append({
                    'name': name,
                    'rows': matrix_data['rows'],
                    'cols': matrix_data['cols'],
                    'position': list(matrix_data['position']),
                    'values': matrix_data['values'].tolist()  # NumPy配列をリストに変換
                })
            
            # 矢印データの変換
            arrows_data = []
            for arrow in self.arrows:
                arrow_data = {
                    'source': list(arrow['source']),
                    'target': list(arrow['target']),
                    'color': arrow['color']
                }
                if 'style' in arrow:
                    arrow_data['style'] = arrow['style']
                if 'width' in arrow:
                    arrow_data['width'] = arrow['width']
                if 'label' in arrow:
                    arrow_data['label'] = arrow['label']
                arrows_data.append(arrow_data)
            
            # 色付きセルデータの変換
            colored_cells_data = []
            for cell in self.colored_cells:
                colored_cells_data.append({
                    'matrix': cell['matrix'],
                    'row': cell['row'],
                    'col': cell['col'],
                    'color': cell['color']
                })
            
            # 全データを１つのオブジェクトにまとめる
            data = {
                'matrices': matrices_data,
                'arrows': arrows_data,
                'colored_cells': colored_cells_data
            }
            
            # JSONファイルに保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.status_var.set(f"データを {file_path} に保存しました")
            return True
        
        except Exception as e:
            messagebox.showerror("保存エラー", f"データの保存中にエラーが発生しました: {str(e)}")
            self.status_var.set(f"保存エラー: {str(e)}")
            return False

    def load_matrix_data(self, file_path):
        """行列データをJSONファイルから読み込み"""
        try:
            matrices, arrows, colored_cells = load_matrices_from_file(file_path)
            
            if not matrices:
                self.status_var.set(f"データの読み込みに失敗しました: {file_path}")
                return False
            
            # データをセット
            self.matrices = matrices
            self.arrows = arrows
            self.colored_cells = colored_cells
            
            # リストを更新
            self.update_matrices_listbox()
            self.update_arrows_listbox()
            self.update_colored_cells_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            self.status_var.set(f"データを {file_path} から読み込みました")
            return True
        
        except Exception as e:
            messagebox.showerror("読み込みエラー", f"データの読み込み中にエラーが発生しました: {str(e)}")
            self.status_var.set(f"読み込みエラー: {str(e)}")
            return False

    def add_matrix(self):
        """行列を追加してビジュアライズする"""
        name = self.matrix_name.get().strip()
        
        # 予約語チェック
        if name in self.reserved_words:
            messagebox.showerror("エラー", f"'{name}' は予約語のため、行列名として使用できません。")
            return
        
        # 行列名が空でないか、予約語のサブセットでないか確認
        if not name or any(name == word for word in self.reserved_words):
            messagebox.showerror("エラー", "有効な行列名を入力してください。")
            return
        
        # 行と列の数が有効か確認
        try:
            rows = int(self.rows.get())
            cols = int(self.cols.get())
            if rows <= 0 or cols <= 0:
                raise ValueError("行と列は正の整数である必要があります。")
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        # 位置が有効か確認
        try:
            pos_x = float(self.pos_x.get())
            pos_y = float(self.pos_y.get())
        except ValueError:
            messagebox.showerror("エラー", "位置は数値である必要があります。")
            return
        
        # 行列名が既に存在するか確認し、上書きを確認
        if name in self.matrices:
            if not messagebox.askyesno("確認", f"行列 '{name}' は既に存在します。上書きしますか？"):
                return
        
        # 行列の値をrow majorで1から順に設定
        values = np.zeros((rows, cols), dtype=int)
        counter = 1
        for i in range(rows):
            for j in range(cols):
                values[i, j] = counter
                counter += 1
        
        # 行列を保存
        self.matrices[name] = {
            'values': values,
            'position': (pos_x, pos_y),
            'rows': rows,
            'cols': cols
        }
        
        # リストボックスを更新
        self.update_matrices_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
        
        self.status_var.set(f"行列 '{name}' を追加しました")

    def delete_matrix(self):
        """選択された行列を削除"""
        if not self.matrices_listbox.curselection():
            messagebox.showinfo("情報", "削除する行列を選択してください。")
            return
        
        index = self.matrices_listbox.curselection()[0]
        selected_matrix = self.matrices_listbox.get(index).split()[0]
        
        if messagebox.askyesno("確認", f"行列 '{selected_matrix}' を削除しますか？"):
            # 関連する矢印と色付き要素も削除
            self.arrows = [arrow for arrow in self.arrows 
                        if arrow['source'][0] != selected_matrix and arrow['target'][0] != selected_matrix]
            self.colored_cells = [cell for cell in self.colored_cells if cell['matrix'] != selected_matrix]
            
            # 行列を削除
            if selected_matrix in self.matrices:
                del self.matrices[selected_matrix]
                
            # リストを更新
            self.update_matrices_listbox()
            self.update_arrows_listbox()
            self.update_colored_cells_listbox()
            
            # 可視化を更新
            self.visualize_matrices()
            
            self.status_var.set(f"行列 '{selected_matrix}' を削除しました")

    def visualize_matrices(self):
        """行列と矢印を描画"""
        self.ax.clear()
        
        # 行列を描画
        self.draw_matrices()
        
        # 矢印を描画
        self.draw_arrows()
        
        # 色付き要素を描画
        self.draw_colored_cells()
        
        # グラフの表示範囲を調整
        self.adjust_plot_limits()
        
        # タイトルを設定
        self.ax.set_title('行列演算の可視化', fontsize=16, color='black' if not self.is_dark_mode else 'white')
        
        # キャンバスを更新
        self.canvas.draw()

    def adjust_plot_limits(self):
        """プロットの表示範囲を調整"""
        max_x, min_y = 0, 0
        padding = 2
        
        # 行列の範囲を計算
        for matrix_data in self.matrices.values():
            pos_x, pos_y = matrix_data['position']
            rows, cols = matrix_data['values'].shape
            max_x = max(max_x, pos_x + cols + 0.5)
            min_y = min(min_y, -(pos_y + rows + 0.5))
        
        self.ax.set_xlim(-padding, max_x + padding)
        self.ax.set_ylim(min_y - padding, padding)
        self.ax.set_aspect('equal')
        self.ax.axis('off')

    def evaluate_expression(self):
        """行列式を評価"""
        expr = self.expr_entry.get().strip()
        if not expr:
            messagebox.showerror("エラー", "式を入力してください。")
            return
        
        # 式を解析して可視化
        self.parse_and_visualize_expression(expr)

    def parse_and_visualize_expression(self, expr):
        """式を解析して可視化する"""
        # イコールで分割
        parts = expr.split('=')
        
        # それぞれの部分を個別に解析
        equation_parts = []
        
        for part in parts:
            part = part.strip()
            if not part:
                continue
                
            # 式を分解する
            # まずかっこ付きの演算子（Det, Tr）を処理
            parenthesis_ops = {'Det(': 'Det', 'Tr(': 'Tr'}
            processed_expr = part
            bracket_contents = {}
            bracket_count = 0
            
            for op_start in parenthesis_ops:
                op_name = parenthesis_ops[op_start]
                start_idx = 0
                while True:
                    # 演算子の開始位置を見つける
                    start_pos = processed_expr.find(op_start, start_idx)
                    if start_pos == -1:
                        break
                        
                    # 対応する閉じかっこを見つける
                    bracket_level = 1
                    end_pos = start_pos + len(op_start)
                    while end_pos < len(processed_expr) and bracket_level > 0:
                        if processed_expr[end_pos] == '(':
                            bracket_level += 1
                        elif processed_expr[end_pos] == ')':
                            bracket_level -= 1
                        end_pos += 1
                    
                    if bracket_level > 0:
                        messagebox.showerror("エラー", f"式の括弧が閉じられていません: {expr}")
                        return
                    
                    # 括弧内の内容を保存
                    content = processed_expr[start_pos + len(op_start):end_pos - 1]
                    placeholder = f"__OP{bracket_count}__"
                    bracket_contents[placeholder] = (op_name, content)
                    
                    # 式を更新
                    processed_expr = processed_expr[:start_pos] + placeholder + processed_expr[end_pos:]
                    bracket_count += 1
                    start_idx = start_pos + len(placeholder)
            
            # 残りの演算子を処理
            remaining_ops = ['+', '-', '*', '^']
            operations = []
            terms = []
            current_term = ""
            
            i = 0
            while i < len(processed_expr):
                char = processed_expr[i]
                
                # べき乗の特殊処理
                if char == '^':
                    operations.append(char)
                    if current_term:
                        terms.append(current_term.strip())
                        current_term = ""
                    
                    # 指数を取得
                    i += 1
                    exponent = ""
                    # 負の指数のケース
                    if i < len(processed_expr) and processed_expr[i] == '-':
                        exponent += '-'
                        i += 1
                    
                    # 指数の数値部分
                    while i < len(processed_expr) and (processed_expr[i].isdigit() or processed_expr[i] == '.'):
                        exponent += processed_expr[i]
                        i += 1
                    
                    # 指数が既存の行列名でない場合、自動的に作成
                    if exponent and exponent not in self.matrices:
                        try:
                            exponent_value = float(exponent)
                            # 整数に変換可能なら整数に
                            if exponent_value == int(exponent_value):
                                exponent_value = int(exponent_value)
                            
                            # 1x1の行列として作成
                            self.matrices[exponent] = {
                                'values': np.array([[exponent_value]]),
                                'position': (10, 0),  # 適当な位置
                                'rows': 1,
                                'cols': 1
                            }
                            self.update_matrices_listbox()
                        except ValueError:
                            pass  # 数値でない場合は無視
                    
                    terms.append(exponent.strip())
                    continue
                
                # 通常の演算子
                elif char in remaining_ops:
                    if current_term:
                        terms.append(current_term.strip())
                        current_term = ""
                    operations.append(char)
                else:
                    current_term += char
                
                i += 1
            
            if current_term:
                terms.append(current_term.strip())
            
            # 括弧内容を元に戻す
            for i, term in enumerate(terms):
                if term in bracket_contents:
                    op_name, content = bracket_contents[term]
                    terms[i] = (op_name, content)
            
            # 行列が定義されているか確認し、必要に応じて自動作成
            all_matrices = set()
            for term in terms:
                if isinstance(term, str):
                    if term not in self.matrices and term.strip().isdigit():
                        # 数値の場合、1x1行列として自動作成
                        value = int(term.strip())
                        self.matrices[term] = {
                            'values': np.array([[value]]),
                            'position': (10, 0),  # 適当な位置
                            'rows': 1,
                            'cols': 1
                        }
                        self.update_matrices_listbox()
                    
                    if term in self.matrices:
                        all_matrices.add(term)
                    else:
                        messagebox.showerror("エラー", f"行列 '{term}' が定義されていません。")
                        return
                elif isinstance(term, tuple):
                    op_name, content = term
                    if content in self.matrices:
                        all_matrices.add(content)
                    else:
                        messagebox.showerror("エラー", f"行列 '{content}' が定義されていません。")
                        return
            
            equation_parts.append((terms, operations))
        
        # 可視化
        self.visualize_expression(equation_parts)

    def visualize_expression(self, equation_parts):
        """式の評価結果をビジュアライズ"""
        self.ax.clear()
        
        # 行列を描画
        self.draw_matrices()
        
        # 各部分の式を評価
        for part_idx, (terms, operations) in enumerate(equation_parts):
            # 特殊演算（Det, Tr）を適用
            for i, term in enumerate(terms):
                if isinstance(term, tuple):
                    op_name, matrix_name = term
                    if matrix_name in self.matrices:
                        matrix_data = self.matrices[matrix_name]
                        
                        if op_name == 'Det':
                            # 行列式の視覚化
                            self.visualize_determinant(matrix_name, matrix_data)
                            
                        elif op_name == 'Tr':
                            # トレースの視覚化
                            self.visualize_trace(matrix_name, matrix_data)
            
            # 通常の二項演算を適用
            if len(terms) >= 2 and len(operations) >= 1:
                for i in range(len(operations)):
                    if i+1 < len(terms):
                        left_term = terms[i]
                        right_term = terms[i+1]
                        op = operations[i]
                        
                        # 項が特殊演算の場合は処理をスキップ（既に処理済み）
                        if isinstance(left_term, tuple) or isinstance(right_term, tuple):
                            continue
                        
                        if left_term in self.matrices and right_term in self.matrices:
                            if op == '+' or op == '-':
                                self.visualize_addition_subtraction(left_term, right_term, op)
                            elif op == '*':
                                self.visualize_multiplication(left_term, right_term)
                            elif op == '^':
                                self.visualize_power(left_term, right_term)
        
        # 等号の表示（2つ以上の部分がある場合）
        if len(equation_parts) >= 2:
            # 左辺と右辺の中央位置を計算
            left_matrices = equation_parts[0][0]
            right_matrices = equation_parts[1][0]
            
            left_positions = []
            right_positions = []
            
            for term in left_matrices:
                if isinstance(term, str) and term in self.matrices:
                    pos_x, pos_y = self.matrices[term]['position']
                    rows, cols = self.matrices[term]['values'].shape
                    left_positions.append((pos_x, pos_y, cols, rows))
                elif isinstance(term, tuple) and term[1] in self.matrices:
                    pos_x, pos_y = self.matrices[term[1]]['position']
                    rows, cols = self.matrices[term[1]]['values'].shape
                    left_positions.append((pos_x, pos_y, cols, rows))
            
            for term in right_matrices:
                if isinstance(term, str) and term in self.matrices:
                    pos_x, pos_y = self.matrices[term]['position']
                    rows, cols = self.matrices[term]['values'].shape
                    right_positions.append((pos_x, pos_y, cols, rows))
                elif isinstance(term, tuple) and term[1] in self.matrices:
                    pos_x, pos_y = self.matrices[term[1]]['position']
                    rows, cols = self.matrices[term[1]]['values'].shape
                    right_positions.append((pos_x, pos_y, cols, rows))
            
            if left_positions and right_positions:
                # 左辺の最右端
                left_max_x = max(x + w for x, y, w, h in left_positions)
                # 右辺の最左端
                right_min_x = min(x for x, y, w, h in right_positions)
                
                # 等号の中央位置
                eq_center_x = (left_max_x + right_min_x) / 2
                
                # 左辺と右辺の平均高さ
                avg_y = -sum(y + h/2 for x, y, w, h in left_positions + right_positions) / len(left_positions + right_positions)
                
                # 等号を表示
                self.ax.text(eq_center_x, avg_y, "=", ha='center', va='center', fontsize=16, fontweight='bold')
        
        # 矢印と色付き要素を描画
        self.draw_arrows()
        self.draw_colored_cells()
        
        # グラフの表示範囲を調整
        self.adjust_plot_limits()
        
        # キャンバスを更新
        self.canvas.draw()

    def visualize_determinant(self, matrix_name, matrix_data):
        """行列式の視覚化"""
        values = matrix_data['values']
        pos_x, pos_y = matrix_data['position']
        rows, cols = values.shape
        
        # 行列式は正方行列のみ定義される
        if rows != cols:
            warning_text = f"行列式 Det({matrix_name}) は正方行列でのみ定義されます"
            self.ax.text(pos_x + cols/2, -(pos_y + rows + 1.5), warning_text, 
                        ha='center', va='center', fontsize=14, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))
            return
        
        # 行列全体を強調
        for i in range(rows):
            for j in range(cols):
                x = pos_x + j
                y = pos_y + i
                rect = patches.Rectangle((x, -y-1), 1, 1, linewidth=1, edgecolor='blue', facecolor='lightcyan')
                self.ax.add_patch(rect)
        
        # 行列式の記号を表示
        self.ax.text(pos_x - 0.5, -(pos_y + rows/2), "det", ha='right', va='center', fontsize=14, color='blue')
        
        # 行列式の値を計算して表示
        det_val = round(np.linalg.det(values), 2)
        result_text = f"Det({matrix_name}) = {det_val}"
        self.ax.text(pos_x + cols/2, -(pos_y + rows + 1.5), result_text, 
                    ha='center', va='center', fontsize=14, color='blue',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='blue'))

    def visualize_trace(self, matrix_name, matrix_data):
        """トレースの視覚化"""
        values = matrix_data['values']
        pos_x, pos_y = matrix_data['position']
        rows, cols = values.shape
        
        # 対角成分を強調
        for i in range(min(rows, cols)):
            x = pos_x + i
            y = pos_y + i
            rect = patches.Rectangle((x, -y-1), 1, 1, linewidth=2, edgecolor='red', facecolor='lightyellow')
            self.ax.add_patch(rect)
        
        # トレースの記号を表示
        self.ax.text(pos_x - 0.5, -(pos_y + rows/2), "tr", ha='right', va='center', fontsize=14, color='red')
        
        # トレース値を計算して表示
        trace_val = np.trace(values)
        result_text = f"Tr({matrix_name}) = {trace_val}"
        self.ax.text(pos_x + cols/2, -(pos_y + rows + 1.5), result_text, 
                    ha='center', va='center', fontsize=14, color='red',
                    bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))

    def visualize_addition_subtraction(self, left_name, right_name, operator):
        """行列の加算・減算の視覚化"""
        left_data = self.matrices[left_name]
        right_data = self.matrices[right_name]
        
        left_pos_x, left_pos_y = left_data['position']
        right_pos_x, right_pos_y = right_data['position']
        
        left_rows, left_cols = left_data['values'].shape
        right_rows, right_cols = right_data['values'].shape
        
        # 加減算は同じサイズの行列のみ可能
        if left_rows != right_rows or left_cols != right_cols:
            warning_text = f"{left_name} {operator} {right_name}: 行列のサイズが一致しません"
            mid_x = (left_pos_x + left_cols + right_pos_x) / 2
            mid_y = -(max(left_pos_y, right_pos_y) + max(left_rows, right_rows) + 1.5)
            self.ax.text(mid_x, mid_y, warning_text, 
                        ha='center', va='center', fontsize=14, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))
            return
        
        # 行列間に演算子を表示
        mid_x = (left_pos_x + left_cols + right_pos_x) / 2
        mid_y = -(left_pos_y + left_rows/2 + right_pos_y + right_rows/2) / 2
        
        # 演算子の表示
        self.ax.text(mid_x, mid_y, operator, ha='center', va='center', 
                    color='purple', fontweight='bold', fontsize=16)
        
        # 演算結果を表示（オプション）
        if operator == '+':
            result = left_data['values'] + right_data['values']
            op_name = "加算"
        else:  # operator == '-'
            result = left_data['values'] - right_data['values']
            op_name = "減算"
        
        # 演算結果のテキストを表示
        result_text = f"{left_name} {operator} {right_name} ({op_name})"
        self.ax.text(mid_x, -(max(left_pos_y, right_pos_y) + max(left_rows, right_rows) + 1.5), 
                    result_text, ha='center', va='center', fontsize=14, color='purple')

    def visualize_multiplication(self, left_name, right_name):
        """行列の乗算の視覚化"""
        left_data = self.matrices[left_name]
        right_data = self.matrices[right_name]
        
        left_pos_x, left_pos_y = left_data['position']
        right_pos_x, right_pos_y = right_data['position']
        
        left_rows, left_cols = left_data['values'].shape
        right_rows, right_cols = right_data['values'].shape
        
        # 行列の乗算条件: 1つ目の行列の列数 = 2つ目の行列の行数
        if left_cols != right_rows:
            warning_text = f"{left_name} * {right_name}: 行列乗算の条件を満たしません"
            mid_x = (left_pos_x + left_cols + right_pos_x) / 2
            mid_y = -(max(left_pos_y, right_pos_y) + max(left_rows, right_rows) + 1.5)
            self.ax.text(mid_x, mid_y, warning_text, 
                        ha='center', va='center', fontsize=14, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))
            return
        
        # 行列間に演算子を表示
        mid_x = (left_pos_x + left_cols + right_pos_x) / 2
        mid_y = -(left_pos_y + left_rows/2 + right_pos_y + right_rows/2) / 2
        
        # 演算子の表示
        self.ax.text(mid_x, mid_y, "×", ha='center', va='center', 
                    color='green', fontweight='bold', fontsize=16)
        
        # いくつかの乗算パターンを可視化（最大3×3まで）
        colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'magenta', 'cyan', 'olive']
        color_idx = 0
        
        for i in range(min(3, left_rows)):
            for j in range(min(3, right_cols)):
                if color_idx < len(colors):
                    color = colors[color_idx]
                    color_idx += 1
                else:
                    color = 'black'
                
                # A_ik * B_kj の計算を視覚化
                for k in range(min(3, left_cols)):
                    # 元の行列の要素を強調
                    self.ax.add_patch(patches.Rectangle(
                        (left_pos_x + k, -(left_pos_y + i + 1)), 1, 1, 
                        linewidth=2, edgecolor=color, facecolor='none', alpha=0.7))
                    
                    self.ax.add_patch(patches.Rectangle(
                        (right_pos_x + j, -(right_pos_y + k + 1)), 1, 1, 
                        linewidth=2, edgecolor=color, facecolor='none', alpha=0.7))
        
        # 演算結果のテキストを表示
        result_text = f"{left_name} × {right_name} (行列乗算)"
        self.ax.text(mid_x, -(max(left_pos_y, right_pos_y) + max(left_rows, right_rows) + 1.5), 
                    result_text, ha='center', va='center', fontsize=14, color='green')

    def visualize_power(self, base_name, exponent_name):
        """行列のべき乗の視覚化"""
        base_data = self.matrices[base_name]
        exponent_data = self.matrices[exponent_name]
        
        base_pos_x, base_pos_y = base_data['position']
        base_rows, base_cols = base_data['values'].shape
        
        # べき乗は正方行列でのみ有効
        if base_rows != base_cols:
            warning_text = f"{base_name}^{exponent_name}: べき乗は正方行列でのみ有効です"
            self.ax.text(base_pos_x + base_cols/2, -(base_pos_y + base_rows + 1.5), 
                        warning_text, ha='center', va='center', fontsize=14, color='red',
                        bbox=dict(facecolor='white', alpha=0.7, edgecolor='red'))
            return
        
        # べき指数の表示
        exponent_pos_x, exponent_pos_y = exponent_data['position']
        self.ax.text(base_pos_x + base_cols + 0.2, -(base_pos_y), exponent_name, 
                    ha='left', va='top', fontsize=12, color='blue')
        
        # 元の行列を強調
        for i in range(base_rows):
            for j in range(base_cols):
                x = base_pos_x + j
                y = base_pos_y + i
                rect = patches.Rectangle((x, -y-1), 1, 1, linewidth=1, edgecolor='blue', facecolor='lightblue', alpha=0.3)
                self.ax.add_patch(rect)
        
        # 演算結果のテキストを表示
        result_text = f"{base_name}^{exponent_name} (行列のべき乗)"
        self.ax.text(base_pos_x + base_cols/2, -(base_pos_y + base_rows + 1.5), 
                    result_text, ha='center', va='center', fontsize=14, color='blue')
    
    def add_arrow(self):
        """矢印を追加"""
        source_matrix = self.source_matrix.get().strip()
        target_matrix = self.target_matrix.get().strip()
        
        # 行列が存在するか確認
        if source_matrix not in self.matrices:
            messagebox.showerror("エラー", f"始点行列 '{source_matrix}' が定義されていません。")
            return
        
        if target_matrix not in self.matrices:
            messagebox.showerror("エラー", f"終点行列 '{target_matrix}' が定義されていません。")
            return
        
        # 行と列のインデックスが有効か確認
        try:
            source_row = int(self.source_row.get())
            source_col = int(self.source_col.get())
            target_row = int(self.target_row.get())
            target_col = int(self.target_col.get())
            
            source_rows = self.matrices[source_matrix]['rows']
            source_cols = self.matrices[source_matrix]['cols']
            target_rows = self.matrices[target_matrix]['rows']
            target_cols = self.matrices[target_matrix]['cols']
            
            if source_row < 0 or source_row >= source_rows or source_col < 0 or source_col >= source_cols:
                raise ValueError(f"始点の位置が範囲外です。行: 0-{source_rows-1}, 列: 0-{source_cols-1}")
                
            if target_row < 0 or target_row >= target_rows or target_col < 0 or target_col >= target_cols:
                raise ValueError(f"終点の位置が範囲外です。行: 0-{target_rows-1}, 列: 0-{target_cols-1}")
                
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        # 色が有効か確認
        color = self.arrow_color.get().strip()
        try:
            # 色名の検証
            if color not in mpl.colors.CSS4_COLORS and not mpl.colors.is_color_like(color):
                raise ValueError(f"'{color}' は有効な色名またはカラーコードではありません。")
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        # 拡張プロパティを取得
        style = self.arrow_style.get()
        
        try:
            width = float(self.arrow_width.get())
            if width <= 0:
                raise ValueError("矢印の太さは正の値である必要があります。")
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        label = self.arrow_label.get().strip()
        
        # 矢印を追加
        arrow_data = {
            'source': (source_matrix, source_row, source_col),
            'target': (target_matrix, target_row, target_col),
            'color': color,
            'style': style,
            'width': width
        }
        
        if label:
            arrow_data['label'] = label
        
        self.arrows.append(arrow_data)
        
        # 矢印リストを更新
        self.update_arrows_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
        
        self.status_var.set(f"矢印 {source_matrix}[{source_row}][{source_col}] → {target_matrix}[{target_row}][{target_col}] を追加しました")

    def delete_arrow(self):
        """選択された矢印を削除"""
        if not self.arrows_listbox.curselection():
            messagebox.showinfo("情報", "削除する矢印を選択してください。")
            return
        
        index = self.arrows_listbox.curselection()[0]
        if 0 <= index < len(self.arrows):
            arrow = self.arrows[index]
            source = f"{arrow['source'][0]}[{arrow['source'][1]}][{arrow['source'][2]}]"
            target = f"{arrow['target'][0]}[{arrow['target'][1]}][{arrow['target'][2]}]"
            
            if messagebox.askyesno("確認", f"矢印 {source} → {target} を削除しますか？"):
                del self.arrows[index]
                
                # リストを更新
                self.update_arrows_listbox()
                
                # 可視化を更新
                self.visualize_matrices()
                
                self.status_var.set(f"矢印 {source} → {target} を削除しました")

    def update_cell(self):
        """行列の要素を更新（値と色）"""
        matrix_name = self.cell_matrix.get().strip()
        
        # 行列が存在するか確認
        if matrix_name not in self.matrices:
            messagebox.showerror("エラー", f"行列 '{matrix_name}' が定義されていません。")
            return
        
        # 行と列のインデックスが有効か確認
        try:
            row = int(self.cell_row.get())
            col = int(self.cell_col.get())
            
            matrix_rows = self.matrices[matrix_name]['rows']
            matrix_cols = self.matrices[matrix_name]['cols']
            
            if row < 0 or row >= matrix_rows or col < 0 or col >= matrix_cols:
                raise ValueError(f"要素の位置が範囲外です。行: 0-{matrix_rows-1}, 列: 0-{matrix_cols-1}")
        except ValueError as e:
            messagebox.showerror("エラー", str(e))
            return
        
        # 値を更新
        try:
            value = self.cell_value.get().strip()
            if value:
                # 数値に変換可能か確認
                if '.' in value:
                    value = float(value)
                else:
                    value = int(value)
                self.matrices[matrix_name]['values'][row, col] = value
        except ValueError:
            messagebox.showerror("エラー", "値は数値である必要があります。")
            return
        
        # 色を更新
        color = self.cell_color.get().strip()
        if color and color.lower() != "none":
            try:
                # 色名の検証
                if not (color in mpl.colors.CSS4_COLORS or mpl.colors.is_color_like(color)):
                    raise ValueError(f"'{color}' は有効な色名またはカラーコードではありません。")
                
                # 既存の色設定を削除
                self.colored_cells = [cell for cell in self.colored_cells 
                                if not (cell['matrix'] == matrix_name and cell['row'] == row and cell['col'] == col)]
                
                # 色設定を追加
                self.colored_cells.append({
                    'matrix': matrix_name,
                    'row': row,
                    'col': col,
                    'color': color
                })
                
                # 色付き要素リストを更新
                self.update_colored_cells_listbox()
                
            except ValueError as e:
                messagebox.showerror("エラー", str(e))
                return
        elif color.lower() == "none":
            # 色設定を削除
            self.colored_cells = [cell for cell in self.colored_cells 
                            if not (cell['matrix'] == matrix_name and cell['row'] == row and cell['col'] == col)]
            self.update_colored_cells_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
        
        self.status_var.set(f"要素 {matrix_name}[{row}][{col}] を更新しました")

    def delete_colored_cell(self):
        """選択された色付き要素を削除"""
        if not self.colored_cells_listbox.curselection():
            messagebox.showinfo("情報", "削除する色付き要素を選択してください。")
            return
        
        index = self.colored_cells_listbox.curselection()[0]
        if 0 <= index < len(self.colored_cells):
            cell = self.colored_cells[index]
            cell_desc = f"{cell['matrix']}[{cell['row']}][{cell['col']}]"
            
            if messagebox.askyesno("確認", f"色付き要素 {cell_desc} を削除しますか？"):
                del self.colored_cells[index]
                
                # リストを更新
                self.update_colored_cells_listbox()
                
                # 可視化を更新
                self.visualize_matrices()
                
                self.status_var.set(f"色付き要素 {cell_desc} を削除しました")

    def draw_matrices(self):
        """すべての行列を描画"""
        for name, matrix_data in self.matrices.items():
            values = matrix_data['values']
            pos_x, pos_y = matrix_data['position']
            rows, cols = values.shape
            
            # 行列全体の背景（わずかに大きめに）
            background = patches.Rectangle(
                (pos_x - 0.1, -(pos_y + rows) - 0.1), 
                cols + 0.2, rows + 0.2, 
                linewidth=1.5, 
                edgecolor='gray', 
                facecolor='#f8f8f8' if not self.is_dark_mode else '#2a2a2a',
                alpha=0.7,
                zorder=0
            )
            self.ax.add_patch(background)
            
            # 行列のセルを描画
            for i in range(rows):
                for j in range(cols):
                    x = pos_x + j
                    y = pos_y + i
                    
                    # セルのカラーを決定
                    cell_color = 'white' if not self.is_dark_mode else '#3a3a3a'
                    text_color = 'black' if not self.is_dark_mode else 'white'
                    
                    rect = patches.Rectangle(
                        (x, -y-1), 1, 1, 
                        linewidth=1, 
                        edgecolor='black' if not self.is_dark_mode else '#555555', 
                        facecolor=cell_color,
                        zorder=1
                    )
                    self.ax.add_patch(rect)
                    
                    # 値が整数か浮動小数点数かに基づいてフォーマット
                    val = values[i, j]
                    if isinstance(val, int) or (isinstance(val, float) and val.is_integer()):
                        text = str(int(val))
                    else:
                        text = f"{val:.2f}"
                    
                    self.ax.text(
                        x + 0.5, -y - 0.5, 
                        text, 
                        ha='center', 
                        va='center', 
                        fontsize=12,
                        color=text_color,
                        zorder=2
                    )
            
            # 行列名を左上に表示（影付き）
            text_color = 'black' if not self.is_dark_mode else 'white'
            # 影の効果（オフセット付きで同じテキストを描画）
            if not self.is_dark_mode:
                self.ax.text(
                    pos_x - 0.18, -pos_y + 0.02, 
                    name, 
                    ha='right', 
                    va='center', 
                    fontsize=14, 
                    fontweight='bold',
                    color='lightgray',
                    zorder=3
                )
            
            self.ax.text(
                pos_x - 0.2, -pos_y, 
                name, 
                ha='right', 
                va='center', 
                fontsize=14, 
                fontweight='bold',
                color=text_color,
                zorder=4
            )

    def draw_arrows(self):
        """すべての矢印を描画"""
        for arrow in self.arrows:
            source_name, source_row, source_col = arrow['source']
            target_name, target_row, target_col = arrow['target']
            color = arrow['color']
            
            # 追加のスタイル情報
            style = arrow.get('style', '-|>')
            width = arrow.get('width', 2.0)
            label = arrow.get('label', '')
            
            if source_name in self.matrices and target_name in self.matrices:
                source_pos = self.matrices[source_name]['position']
                target_pos = self.matrices[target_name]['position']
                
                # 矢印の始点と終点を計算
                start_x = source_pos[0] + source_col + 0.5
                start_y = -(source_pos[1] + source_row + 0.5)
                end_x = target_pos[0] + target_col + 0.5
                end_y = -(target_pos[1] + target_row + 0.5)
                
                # 矢印スタイルを設定
                arrow_style = None
                if style == '-|>':
                    arrow_style = '-|>'
                elif style == '->>':
                    arrow_style = '->'
                elif style == '-[':
                    arrow_style = '-['
                elif style == '-|':
                    arrow_style = '-|'
                elif style == '<->':
                    arrow_style = '<->'
                elif style == '<-|>':
                    arrow_style = '<-|>'
                else:
                    arrow_style = '-|>'  # デフォルト
                
                # 矢印を描画
                annotation = self.ax.annotate(
                    '', 
                    xy=(end_x, end_y), 
                    xytext=(start_x, start_y),
                    arrowprops=dict(
                        arrowstyle=arrow_style, 
                        color=color, 
                        lw=width,
                        alpha=0.8,
                        connectionstyle="arc3,rad=.1"  # 少し湾曲させる
                    ),
                    zorder=10
                )
                
                # ラベルがあれば表示
                if label:
                    # 矢印の中点を計算
                    mid_x = (start_x + end_x) / 2
                    mid_y = (start_y + end_y) / 2
                    
                    # 少しオフセットを加える
                    offset_x = (end_y - start_y) * 0.1
                    offset_y = (start_x - end_x) * 0.1
                    
                    # ラベルのテキストを描画
                    self.ax.text(
                        mid_x + offset_x, 
                        mid_y + offset_y, 
                        label,
                        ha='center',
                        va='center',
                        fontsize=10,
                        fontweight='bold',
                        color=color,
                        bbox=dict(facecolor='white' if not self.is_dark_mode else '#2a2a2a', alpha=0.8),
                        zorder=11
                    )

    def draw_colored_cells(self):
        """色付き要素を描画"""
        for cell in self.colored_cells:
            matrix_name = cell['matrix']
            row = cell['row']
            col = cell['col']
            color = cell['color']
            
            if matrix_name in self.matrices:
                matrix_pos = self.matrices[matrix_name]['position']
                
                # セルの位置を計算
                x = matrix_pos[0] + col
                y = matrix_pos[1] + row
                
                # 色の輝度を計算して、適切なテキスト色を選択
                try:
                    rgb = mpl.colors.to_rgb(color)
                    brightness = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
                    text_color = 'black' if brightness > 0.5 else 'white'
                except:
                    text_color = 'black'  # 変換できない場合はデフォルト
                
                # 色付きセルを描画
                rect = patches.Rectangle(
                    (x, -y-1), 1, 1, 
                    linewidth=1, 
                    edgecolor='black', 
                    facecolor=color,
                    alpha=0.8,
                    zorder=5
                )
                self.ax.add_patch(rect)
                
                # セルの値を再描画
                cell_value = self.matrices[matrix_name]['values'][row, col]
                
                # 値が整数か浮動小数点数かに基づいてフォーマット
                if isinstance(cell_value, int) or (isinstance(cell_value, float) and cell_value.is_integer()):
                    value_text = str(int(cell_value))
                else:
                    value_text = f"{cell_value:.2f}"
                
                self.ax.text(
                    x + 0.5, -y - 0.5, 
                    value_text, 
                    ha='center', 
                    va='center', 
                    fontsize=12,
                    color=text_color,
                    fontweight='bold',
                    zorder=6
                )

    def execute_console_commands(self):
        """コンソールテキストエリアのコマンドをすべて実行"""
        commands_text = self.console_text.get(1.0, tk.END).strip()
        if not commands_text:
            return
        
        # 各行をコマンドとして処理
        commands = commands_text.split('\n')
        success_count = 0
        error_count = 0
        
        # コマンド履歴に追加
        self.console_history.config(state=tk.NORMAL)
        self.console_history.insert(tk.END, f"==== コマンド実行開始 ({len(commands)}行) ====\n")
        
        for i, command in enumerate(commands):
            command = command.strip()
            if not command or command.startswith('#'):  # 空行やコメント行はスキップ
                continue
                
            self.console_history.insert(tk.END, f"> {command}\n")
            
            try:
                result = self.parse_and_execute_command(command)
                if result:
                    self.console_history.insert(tk.END, f"  結果: {result}\n")
                success_count += 1
            except ValueError as e:
                self.console_history.insert(tk.END, f"  エラー: {str(e)}\n")
                error_count += 1
        
        self.console_history.insert(tk.END, f"==== 実行完了: 成功 {success_count}, 失敗 {error_count} ====\n\n")
        self.console_history.see(tk.END)
        self.console_history.config(state=tk.DISABLED)
        
        # 可視化を更新
        self.visualize_matrices()
        
        self.status_var.set(f"コマンド実行: 成功 {success_count}, 失敗 {error_count}")

    def parse_and_execute_command(self, command):
        """単一のコマンドを解析して実行"""
        # 行列定義: A := [3, 3] @ (0, 0)
        if ":=" in command and "@" in command:
            parts = command.split(":=")
            matrix_name = parts[0].strip()
            
            # 予約語チェック
            if matrix_name in self.reserved_words:
                raise ValueError(f"'{matrix_name}' は予約語のため、行列名として使用できません。")
            
            # サイズと位置の抽出
            size_pos = parts[1].strip()
            size_part = size_pos.split("@")[0].strip()
            pos_part = size_pos.split("@")[1].strip()
            
            # サイズの解析 [rows, cols]
            size_match = re.search(r'\[(\d+),\s*(\d+)\]', size_part)
            if not size_match:
                raise ValueError("行列サイズの形式が正しくありません。例: [3, 3]")
            
            rows = int(size_match.group(1))
            cols = int(size_match.group(2))
            
            # 位置の解析 (x, y)
            pos_match = re.search(r'\((\d+(?:\.\d+)?),\s*(\d+(?:\.\d+)?)\)', pos_part)
            if not pos_match:
                raise ValueError("位置の形式が正しくありません。例: (0, 0)")
            
            pos_x = float(pos_match.group(1))
            pos_y = float(pos_match.group(2))
            
            # 行列の値を設定
            values = np.zeros((rows, cols), dtype=int)
            counter = 1
            for i in range(rows):
                for j in range(cols):
                    values[i, j] = counter
                    counter += 1
            
            # 行列を追加
            self.matrices[matrix_name] = {
                'values': values,
                'position': (pos_x, pos_y),
                'rows': rows,
                'cols': cols
            }
            
            # リストを更新
            self.update_matrices_listbox()
            
            return f"行列 '{matrix_name}' を作成しました ({rows}x{cols})"
            
        # 矢印定義: A[0][0] -> B[1][1] : red
        elif "->" in command and "[" in command and "]" in command:
            parts = command.split("->")
            source_part = parts[0].strip()
            target_parts = parts[1].strip().split(":")
            target_part = target_parts[0].strip()
            
            # 色の抽出
            color = "red"  # デフォルト
            if len(target_parts) > 1:
                color = target_parts[1].strip()
            
            # 始点の解析 A[i][j]
            source_match = re.search(r'([A-Za-z0-9_]+)\[(\d+)\]\[(\d+)\]', source_part)
            if not source_match:
                raise ValueError("始点の形式が正しくありません。例: A[0][0]")
            
            source_matrix = source_match.group(1)
            source_row = int(source_match.group(2))
            source_col = int(source_match.group(3))
            
            # 終点の解析 B[k][l]
            target_match = re.search(r'([A-Za-z0-9_]+)\[(\d+)\]\[(\d+)\]', target_part)
            if not target_match:
                raise ValueError("終点の形式が正しくありません。例: B[1][1]")
            
            target_matrix = target_match.group(1)
            target_row = int(target_match.group(2))
            target_col = int(target_match.group(3))
            
            # 行列の存在チェック
            if source_matrix not in self.matrices:
                raise ValueError(f"始点行列 '{source_matrix}' が定義されていません。")
            if target_matrix not in self.matrices:
                raise ValueError(f"終点行列 '{target_matrix}' が定義されていません。")
            
            # インデックスの範囲チェック
            source_rows = self.matrices[source_matrix]['rows']
            source_cols = self.matrices[source_matrix]['cols']
            target_rows = self.matrices[target_matrix]['rows']
            target_cols = self.matrices[target_matrix]['cols']
            
            if source_row < 0 or source_row >= source_rows or source_col < 0 or source_col >= source_cols:
                raise ValueError(f"始点の位置が範囲外です。行: 0-{source_rows-1}, 列: 0-{source_cols-1}")
            if target_row < 0 or target_row >= target_rows or target_col < 0 or target_col >= target_cols:
                raise ValueError(f"終点の位置が範囲外です。行: 0-{target_rows-1}, 列: 0-{target_cols-1}")
            
            # 矢印を追加
            arrow_data = {
                'source': (source_matrix, source_row, source_col),
                'target': (target_matrix, target_row, target_col),
                'color': color,
                'style': '-|>',  # デフォルトスタイル
                'width': 2.0     # デフォルト太さ
            }
            
            self.arrows.append(arrow_data)
            
            # リストを更新
            self.update_arrows_listbox()
            
            return f"矢印 {source_matrix}[{source_row}][{source_col}] → {target_matrix}[{target_row}][{target_col}] を追加しました"
            
        # 要素の色設定: A[0][0] : red
        elif ":" in command and "[" in command and "]" in command and "->" not in command:
            parts = command.split(":")
            cell_part = parts[0].strip()
            color = parts[1].strip()
            
            # セルの解析 A[i][j]
            cell_match = re.search(r'([A-Za-z0-9_]+)\[(\d+)\]\[(\d+)\]', cell_part)
            if not cell_match:
                raise ValueError("要素の形式が正しくありません。例: A[0][0]")
            
            matrix_name = cell_match.group(1)
            row = int(cell_match.group(2))
            col = int(cell_match.group(3))
            
            # 行列の存在チェック
            if matrix_name not in self.matrices:
                raise ValueError(f"行列 '{matrix_name}' が定義されていません。")
            
            # インデックスの範囲チェック
            matrix_rows = self.matrices[matrix_name]['rows']
            matrix_cols = self.matrices[matrix_name]['cols']
            
            if row < 0 or row >= matrix_rows or col < 0 or col >= matrix_cols:
                raise ValueError(f"要素の位置が範囲外です。行: 0-{matrix_rows-1}, 列: 0-{matrix_cols-1}")
            
            # 既存の色設定を削除
            self.colored_cells = [cell for cell in self.colored_cells 
                            if not (cell['matrix'] == matrix_name and cell['row'] == row and cell['col'] == col)]
            
            # 色が "none" でない場合、新しい色設定を追加
            if color.lower() != "none":
                self.colored_cells.append({
                    'matrix': matrix_name,
                    'row': row,
                    'col': col,
                    'color': color
                })
                
                # リストを更新
                self.update_colored_cells_listbox()
                
                return f"要素 {matrix_name}[{row}][{col}] の色を '{color}' に設定しました"
            else:
                # リストを更新
                self.update_colored_cells_listbox()
                
                return f"要素 {matrix_name}[{row}][{col}] の色を削除しました"
                
        # 値設定: A[0][0] = 5
        elif "=" in command and "[" in command and "]" in command and "->" not in command:
            parts = command.split("=")
            cell_part = parts[0].strip()
            value_part = parts[1].strip()
            
            # セルの解析 A[i][j]
            cell_match = re.search(r'([A-Za-z0-9_]+)\[(\d+)\]\[(\d+)\]', cell_part)
            if not cell_match:
                raise ValueError("要素の形式が正しくありません。例: A[0][0]")
            
            matrix_name = cell_match.group(1)
            row = int(cell_match.group(2))
            col = int(cell_match.group(3))
            
            # 行列の存在チェック
            if matrix_name not in self.matrices:
                raise ValueError(f"行列 '{matrix_name}' が定義されていません。")
            
            # インデックスの範囲チェック
            matrix_rows = self.matrices[matrix_name]['rows']
            matrix_cols = self.matrices[matrix_name]['cols']
            
            if row < 0 or row >= matrix_rows or col < 0 or col >= matrix_cols:
                raise ValueError(f"要素の位置が範囲外です。行: 0-{matrix_rows-1}, 列: 0-{matrix_cols-1}")
            
            # 値を解析
            try:
                # 数値に変換
                if '.' in value_part:
                    value = float(value_part)
                else:
                    value = int(value_part)
                
                # 値を設定
                self.matrices[matrix_name]['values'][row, col] = value
                
                return f"要素 {matrix_name}[{row}][{col}] の値を '{value}' に設定しました"
                
            except ValueError:
                raise ValueError(f"値 '{value_part}' は有効な数値ではありません。")
                
        else:
            raise ValueError("認識できないコマンド形式です。例: A := [3, 3] @ (0, 0), A[0][0] -> B[1][1] : red, A[0][0] : blue")

    def on_arrow_select(self, event):
        """リストボックスで矢印を選択したときのイベントハンドラ"""
        if self.arrows_listbox.curselection():
            index = self.arrows_listbox.curselection()[0]
            
            if 0 <= index < len(self.arrows):
                arrow_data = self.arrows[index]
                
                # 矢印定義のフィールドを更新
                self.source_matrix.delete(0, tk.END)
                self.source_matrix.insert(0, arrow_data['source'][0])
                
                self.source_row.delete(0, tk.END)
                self.source_row.insert(0, str(arrow_data['source'][1]))
                
                self.source_col.delete(0, tk.END)
                self.source_col.insert(0, str(arrow_data['source'][2]))
                
                self.target_matrix.delete(0, tk.END)
                self.target_matrix.insert(0, arrow_data['target'][0])
                
                self.target_row.delete(0, tk.END)
                self.target_row.insert(0, str(arrow_data['target'][1]))
                
                self.target_col.delete(0, tk.END)
                self.target_col.insert(0, str(arrow_data['target'][2]))
                
                self.arrow_color.delete(0, tk.END)
                self.arrow_color.insert(0, arrow_data['color'])
                
                # 拡張プロパティの更新
                if 'style' in arrow_data:
                    self.arrow_style.set(arrow_data['style'])
                else:
                    self.arrow_style.current(0)
                    
                if 'width' in arrow_data:
                    self.arrow_width.delete(0, tk.END)
                    self.arrow_width.insert(0, str(arrow_data['width']))
                else:
                    self.arrow_width.delete(0, tk.END)
                    self.arrow_width.insert(0, "2.0")
                    
                if 'label' in arrow_data:
                    self.arrow_label.delete(0, tk.END)
                    self.arrow_label.insert(0, arrow_data['label'])
                else:
                    self.arrow_label.delete(0, tk.END)
                
                self.status_var.set(f"矢印 {index+1} を選択しました")
                
                # 矢印を強調表示
                self.visualize_matrices()  # 現在の表示をリセット
                
                # 選択された矢印を強調
                source_name, source_row, source_col = arrow_data['source']
                target_name, target_row, target_col = arrow_data['target']
                
                if source_name in self.matrices and target_name in self.matrices:
                    source_pos = self.matrices[source_name]['position']
                    target_pos = self.matrices[target_name]['position']
                    
                    # セルを強調
                    source_x = source_pos[0] + source_col
                    source_y = source_pos[1] + source_row
                    rect1 = patches.Rectangle((source_x, -source_y-1), 1, 1, 
                                        linewidth=2, edgecolor='blue', facecolor='none')
                    self.ax.add_patch(rect1)
                    
                    target_x = target_pos[0] + target_col
                    target_y = target_pos[1] + target_row
                    rect2 = patches.Rectangle((target_x, -target_y-1), 1, 1, 
                                        linewidth=2, edgecolor='red', facecolor='none')
                    self.ax.add_patch(rect2)
                    
                    # キャンバスを更新
                    self.canvas.draw()

    def on_colored_cell_select(self, event):
        """リストボックスで色付き要素を選択したときのイベントハンドラ"""
        if self.colored_cells_listbox.curselection():
            index = self.colored_cells_listbox.curselection()[0]
            
            if 0 <= index < len(self.colored_cells):
                cell_data = self.colored_cells[index]
                
                # 要素の色設定フィールドを更新
                self.cell_matrix.delete(0, tk.END)
                self.cell_matrix.insert(0, cell_data['matrix'])
                
                self.cell_row.delete(0, tk.END)
                self.cell_row.insert(0, str(cell_data['row']))
                
                self.cell_col.delete(0, tk.END)
                self.cell_col.insert(0, str(cell_data['col']))
                
                self.cell_color.delete(0, tk.END)
                self.cell_color.insert(0, cell_data['color'])
                
                # 値も設定
                if cell_data['matrix'] in self.matrices:
                    value = self.matrices[cell_data['matrix']]['values'][cell_data['row'], cell_data['col']]
                    self.cell_value.delete(0, tk.END)
                    self.cell_value.insert(0, str(value))
                
                # セルの位置も範囲選択に設定
                self.range_start_row.delete(0, tk.END)
                self.range_start_row.insert(0, str(cell_data['row']))
                
                self.range_start_col.delete(0, tk.END)
                self.range_start_col.insert(0, str(cell_data['col']))
                
                self.range_end_row.delete(0, tk.END)
                self.range_end_row.insert(0, str(cell_data['row']))
                
                self.range_end_col.delete(0, tk.END)
                self.range_end_col.insert(0, str(cell_data['col']))
                
                self.range_color.delete(0, tk.END)
                self.range_color.insert(0, cell_data['color'])
                
                self.status_var.set(f"色付き要素 {index+1} を選択しました")
                
                # セルを強調表示
                self.visualize_matrices()  # 現在の表示をリセット
                
                # 選択されたセルを強調
                if cell_data['matrix'] in self.matrices:
                    matrix_pos = self.matrices[cell_data['matrix']]['position']
                    row = cell_data['row']
                    col = cell_data['col']
                    
                    x = matrix_pos[0] + col
                    y = matrix_pos[1] + row
                    
                    rect = patches.Rectangle((x, -y-1), 1, 1, 
                                        linewidth=3, edgecolor='yellow', facecolor='none')
                    self.ax.add_patch(rect)
                    
                    # キャンバスを更新
                    self.canvas.draw()

    def save_figure(self, format):
        """図を保存する"""
        filetypes = {
            'png': ('PNG ファイル', '*.png'),
            'pdf': ('PDF ファイル', '*.pdf'),
            'svg': ('SVG ファイル', '*.svg'),
            'jpg': ('JPEG ファイル', '*.jpg')
        }
        
        if format not in filetypes:
            messagebox.showerror("エラー", f"サポートされていないフォーマット: {format}")
            return
        
        # 保存ダイアログを表示
        filename = filedialog.asksaveasfilename(
            title=f"{format.upper()} として保存",
            filetypes=[(filetypes[format][0], filetypes[format][1])],
            defaultextension=f".{format}"
        )
        
        if not filename:
            return  # ユーザーがキャンセルした場合
        
        try:
            # グラフの境界を調整して保存（余白や切れないように）
            self.fig.tight_layout()
            
            # DPIを設定して高品質で保存
            dpi = 300 if format in ['png', 'jpg'] else 150
            
            # 透過設定
            transparent = format in ['png', 'svg']
            
            # 図を保存
            self.fig.savefig(
                filename, 
                format=format, 
                bbox_inches='tight', 
                dpi=dpi,
                transparent=transparent,
                pad_inches=0.1
            )
            
            # ステータスバーを更新
            self.status_var.set(f"図を {filename} に保存しました")
            
            # 保存成功メッセージを表示
            messagebox.showinfo("保存完了", f"図を {filename} に保存しました。")
            
        except Exception as e:
            # エラーメッセージを表示
            error_msg = str(e)
            messagebox.showerror("保存エラー", f"保存中にエラーが発生しました: {error_msg}")
            self.status_var.set(f"保存エラー: {error_msg}")
            
            # デバッグ用にエラー詳細をコンソールに出力
            import traceback
            traceback.print_exc()

def setup_logging():
    """ログ機能のセットアップ"""
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"matrix_viz_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("MatrixViz")

def load_config(config_file):
    """設定ファイルを読み込む"""
    default_config = {
        "theme": "light",
        "language": "ja",
        "window_size": [1300, 800],
        "default_matrices": [
            {"name": "A", "rows": 3, "cols": 3, "position": [0, 0]},
            {"name": "B", "rows": 3, "cols": 3, "position": [5, 0]}
        ],
        "font_size": 12,
        "auto_save": False
    }
    
    if not os.path.exists(config_file):
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return {**default_config, **config}  # デフォルト設定を上書き
    except Exception as e:
        print(f"設定ファイルの読み込みエラー: {str(e)}")
        return default_config

def save_config(config_file, config):
    """設定ファイルを保存する"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"設定ファイルの保存エラー: {str(e)}")
        return False

def parse_arguments():
    """コマンドライン引数を解析"""
    parser = argparse.ArgumentParser(description='行列演算可視化ツール')
    parser.add_argument('--config', type=str, default='config.json', help='設定ファイルのパス')
    parser.add_argument('--theme', choices=['light', 'dark'], help='テーマ（light/dark）')
    parser.add_argument('--debug', action='store_true', help='デバッグモードで実行')
    parser.add_argument('--file', type=str, help='読み込む行列データファイル')
    parser.add_argument('--fullscreen', action='store_true', help='フルスクリーンで起動')
    return parser.parse_args()

def load_matrices_from_file(file_path):
    """ファイルから行列データを読み込む"""
    matrices = {}
    arrows = []
    colored_cells = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'matrices' in data:
            for matrix_data in data['matrices']:
                name = matrix_data.get('name')
                if name:
                    rows = matrix_data.get('rows', 3)
                    cols = matrix_data.get('cols', 3)
                    pos_x = matrix_data.get('position', [0, 0])[0]
                    pos_y = matrix_data.get('position', [0, 0])[1]
                    
                    # 値の配列が与えられていればそれを使用、なければデフォルト値
                    if 'values' in matrix_data:
                        values = np.array(matrix_data['values'])
                    else:
                        values = np.zeros((rows, cols), dtype=int)
                        counter = 1
                        for i in range(rows):
                            for j in range(cols):
                                values[i, j] = counter
                                counter += 1
                    
                    matrices[name] = {
                        'values': values,
                        'position': (pos_x, pos_y),
                        'rows': rows,
                        'cols': cols
                    }
        
        if 'arrows' in data:
            for arrow_data in data['arrows']:
                source = arrow_data.get('source')
                target = arrow_data.get('target')
                if source and target:
                    arrows.append({
                        'source': tuple(source),
                        'target': tuple(target),
                        'color': arrow_data.get('color', 'red'),
                        'style': arrow_data.get('style', '-|>'),
                        'width': arrow_data.get('width', 2.0),
                        'label': arrow_data.get('label', '')
                    })
        
        if 'colored_cells' in data:
            for cell_data in data['colored_cells']:
                matrix = cell_data.get('matrix')
                row = cell_data.get('row')
                col = cell_data.get('col')
                color = cell_data.get('color')
                if matrix is not None and row is not None and col is not None and color:
                    colored_cells.append({
                        'matrix': matrix,
                        'row': row,
                        'col': col,
                        'color': color
                    })
        
        return matrices, arrows, colored_cells
    
    except Exception as e:
        print(f"ファイルの読み込みエラー: {str(e)}")
        return {}, [], []

def main():
    try:
        # コマンドライン引数の解析
        args = parse_arguments()
        
        # ログの設定
        logger = setup_logging()
        logger.info("行列演算可視化ツールを起動しています...")
        
        # 設定の読み込み
        config_file = args.config
        config = load_config(config_file)
        
        # コマンドライン引数で設定を上書き
        if args.theme:
            config['theme'] = args.theme
        
        # ロケールの設定
        try:
            locale.setlocale(locale.LC_ALL, '')
            logger.info(f"ロケール設定: {locale.getlocale()}")
        except:
            logger.warning("ロケールの設定に失敗しました。デフォルトを使用します。")
        
        # Tkアプリケーションの作成
        root = tk.Tk()
        root.title("行列演算可視化ツール v2.0")
        
        # エラーハンドリングの設定
        def show_error(exc, val, tb):
            error_msg = ''.join(traceback.format_exception(exc, val, tb))
            logger.error(f"未処理の例外:\n{error_msg}")
            messagebox.showerror("エラー", f"予期しないエラーが発生しました:\n{val}")
        
        # 未処理の例外ハンドラを設定
        if not args.debug:  # デバッグモードでなければエラーをキャッチ
            sys.excepthook = show_error
        
        # ウィンドウサイズの設定
        width, height = config['window_size']
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        root.geometry(f"{width}x{height}+{x}+{y}")
        
        # フルスクリーン設定
        if args.fullscreen:
            root.attributes('-fullscreen', True)
        
        # アプリケーションの作成
        app = MatrixVisualization(root)
        
        # テーマの設定
        if config['theme'] == 'dark':
            app.toggle_theme()  # ダークモードに切り替え
        
        # データファイルの読み込み
        if args.file:
            matrices, arrows, colored_cells = load_matrices_from_file(args.file)
            if matrices:
                app.matrices = matrices
                app.arrows = arrows
                app.colored_cells = colored_cells
                app.update_matrices_listbox()
                app.update_arrows_listbox()
                app.update_colored_cells_listbox()
                app.visualize_matrices()
                app.status_var.set(f"データファイル '{args.file}' を読み込みました")
                logger.info(f"データファイル '{args.file}' を読み込みました")
        else:
            # 設定ファイルからデフォルトの行列を作成
            for matrix_def in config['default_matrices']:
                name = matrix_def['name']
                rows = matrix_def['rows']
                cols = matrix_def['cols']
                pos_x, pos_y = matrix_def['position']
                
                values = np.zeros((rows, cols), dtype=int)
                counter = 1
                for i in range(rows):
                    for j in range(cols):
                        values[i, j] = counter
                        counter += 1
                
                app.matrices[name] = {
                    'values': values,
                    'position': (pos_x, pos_y),
                    'rows': rows,
                    'cols': cols
                }
            
            # デフォルトの矢印と色付きセルの例
            if len(app.matrices) >= 2:
                matrix_names = list(app.matrices.keys())
                app.arrows.append({
                    'source': (matrix_names[0], 0, 0),
                    'target': (matrix_names[1], 0, 0),
                    'color': "red",
                    'style': '-|>',
                    'width': 2.0,
                    'label': '例'
                })
                
                app.colored_cells.append({
                    'matrix': matrix_names[0],
                    'row': 1,
                    'col': 1,
                    'color': "lightblue"
                })
            
            # リストと可視化を更新
            app.update_matrices_listbox()
            app.update_arrows_listbox()
            app.update_colored_cells_listbox()
            app.visualize_matrices()
            
            app.status_var.set("デフォルトのデータを読み込みました")
            logger.info("デフォルトのデータを読み込みました")
        
        # アプリケーション終了時の処理
        def on_closing():
            # 設定を保存
            if config.get('auto_save', False):
                save_config(config_file, config)
                logger.info("設定を保存しました")
            
            logger.info("アプリケーションを終了します")
            root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        
        # メインループを開始
        logger.info("メインループを開始します")
        root.mainloop()
    
    except Exception as e:
        if 'logger' in locals():
            logger.error(f"起動エラー: {str(e)}", exc_info=True)
        else:
            print(f"起動エラー: {str(e)}")
            traceback.print_exc()

if __name__ == "__main__":
    main()