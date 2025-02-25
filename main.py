import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib as mpl
import matplotlib.font_manager as fm
import os
import platform

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
        self.root.geometry("1200x800")
        
        # 予約語のリスト
        self.reserved_words = ['+', '-', '*', '^', 'Det', 'Tr', '=']
        
        # 行列辞書 - キーは行列名、値は行列のデータとプロパティ
        self.matrices = {}
        
        # 矢印のリスト
        self.arrows = []
        
        # 色付き要素のリスト
        self.colored_cells = []
        
        # メインフレーム
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 左側のコントロールパネル
        control_panel = ttk.Frame(main_frame, width=400)
        control_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        # 右側の可視化パネル
        self.viz_panel = ttk.Frame(main_frame)
        self.viz_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Matplotlib の図とキャンバス
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.viz_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 行列定義セクション
        matrix_frame = ttk.LabelFrame(control_panel, text="行列定義")
        matrix_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(matrix_frame, text="行列名:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.matrix_name = ttk.Entry(matrix_frame, width=5)
        self.matrix_name.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        self.matrix_name.insert(0, "A")
        
        ttk.Label(matrix_frame, text="行:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.rows = ttk.Spinbox(matrix_frame, from_=1, to=10, width=5)
        self.rows.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        self.rows.set(3)
        
        ttk.Label(matrix_frame, text="列:").grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        self.cols = ttk.Spinbox(matrix_frame, from_=1, to=10, width=5)
        self.cols.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.cols.set(3)
        
        ttk.Label(matrix_frame, text="位置 X:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.pos_x = ttk.Spinbox(matrix_frame, from_=0, to=20, width=5)
        self.pos_x.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.pos_x.set(0)
        
        ttk.Label(matrix_frame, text="位置 Y:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.pos_y = ttk.Spinbox(matrix_frame, from_=0, to=20, width=5)
        self.pos_y.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        self.pos_y.set(0)
        
        ttk.Button(matrix_frame, text="行列を追加", command=self.add_matrix).grid(row=1, column=4, columnspan=2, padx=5, pady=5, sticky=tk.W)
        
        # 式入力セクション
        expr_frame = ttk.LabelFrame(control_panel, text="行列式入力")
        expr_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(expr_frame, text="式:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.expr_entry = ttk.Entry(expr_frame, width=40)
        self.expr_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.expr_entry.insert(0, "A + B = C")
        
        ttk.Button(expr_frame, text="式を評価", command=self.evaluate_expression).grid(row=1, column=0, columnspan=2, padx=5, pady=5)
        
        # 矢印定義セクション
        arrow_frame = ttk.LabelFrame(control_panel, text="矢印定義")
        arrow_frame.pack(fill=tk.X, pady=(0, 10))
        
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
        
        ttk.Label(arrow_frame, text="色:").grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.arrow_color = ttk.Entry(arrow_frame, width=10)
        self.arrow_color.grid(row=2, column=1, padx=5, pady=5, sticky=tk.W)
        self.arrow_color.insert(0, "red")
        
        ttk.Button(arrow_frame, text="矢印を追加", command=self.add_arrow).grid(row=2, column=2, columnspan=4, padx=5, pady=5, sticky=tk.W)
        
        # 要素の設定セクション
        cell_setting_frame = ttk.LabelFrame(control_panel, text="要素の設定")
        cell_setting_frame.pack(fill=tk.X, pady=(0, 10))

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
        self.cell_value = ttk.Entry(cell_setting_frame, width=5)
        self.cell_value.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        self.cell_value.insert(0, "0")

        ttk.Label(cell_setting_frame, text="色:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.cell_color = ttk.Entry(cell_setting_frame, width=10)
        self.cell_color.grid(row=1, column=3, columnspan=2, padx=5, pady=5, sticky=tk.W)
        self.cell_color.insert(0, "none")

        ttk.Button(cell_setting_frame, text="設定", command=self.update_cell).grid(row=1, column=5, padx=5, pady=5, sticky=tk.W)
        
        # コマンドコンソール
        console_frame = ttk.LabelFrame(control_panel, text="コマンドコンソール")
        console_frame.pack(fill=tk.X, pady=(0, 10))

        self.console_entry = ttk.Entry(console_frame, width=50)
        self.console_entry.pack(fill=tk.X, padx=5, pady=5)
        self.console_entry.bind('<Return>', self.execute_command)

        ttk.Button(console_frame, text="実行", command=lambda: self.execute_command(None)).pack(fill=tk.X, padx=5, pady=5)

        # コマンド履歴表示
        self.console_history = tk.Text(console_frame, height=5, width=50)
        self.console_history.pack(fill=tk.X, padx=5, pady=5)
        self.console_history.config(state=tk.DISABLED)
        
        # 行列リストビューと削除ボタン
        matrices_frame = ttk.LabelFrame(control_panel, text="定義済み行列")
        matrices_frame.pack(fill=tk.X, pady=(0, 10))
        
        matrices_list_frame = ttk.Frame(matrices_frame)
        matrices_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.matrices_listbox = tk.Listbox(matrices_list_frame)
        self.matrices_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.matrices_listbox.bind('<<ListboxSelect>>', self.on_matrix_select)
        
        matrices_buttons_frame = ttk.Frame(matrices_list_frame)
        matrices_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(matrices_buttons_frame, text="削除", command=self.delete_matrix).pack(fill=tk.X, padx=5, pady=5)
        
        # 矢印リストビューと削除ボタン
        arrows_frame = ttk.LabelFrame(control_panel, text="定義済み矢印")
        arrows_frame.pack(fill=tk.X, pady=(0, 10))
        
        arrows_list_frame = ttk.Frame(arrows_frame)
        arrows_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.arrows_listbox = tk.Listbox(arrows_list_frame)
        self.arrows_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.arrows_listbox.bind('<<ListboxSelect>>', self.on_arrow_select)
        
        arrows_buttons_frame = ttk.Frame(arrows_list_frame)
        arrows_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(arrows_buttons_frame, text="削除", command=self.delete_arrow).pack(fill=tk.X, padx=5, pady=5)
        
        # 色付き要素のリストビューと削除ボタン
        colored_cells_frame = ttk.LabelFrame(control_panel, text="色付き要素")
        colored_cells_frame.pack(fill=tk.X, pady=(0, 10))
        
        colored_cells_list_frame = ttk.Frame(colored_cells_frame)
        colored_cells_list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.colored_cells_listbox = tk.Listbox(colored_cells_list_frame)
        self.colored_cells_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.colored_cells_listbox.bind('<<ListboxSelect>>', self.on_colored_cell_select)
        
        colored_cells_buttons_frame = ttk.Frame(colored_cells_list_frame)
        colored_cells_buttons_frame.pack(side=tk.RIGHT, fill=tk.Y)
        
        ttk.Button(colored_cells_buttons_frame, text="削除", command=self.delete_colored_cell).pack(fill=tk.X, padx=5, pady=5)
        
        # ファイル操作ボタン
        file_frame = ttk.Frame(control_panel)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(file_frame, text="PNG として保存", command=lambda: self.save_figure("png")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        ttk.Button(file_frame, text="PDF として保存", command=lambda: self.save_figure("pdf")).pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5, pady=5)
        
        # リセットボタン
        ttk.Button(control_panel, text="すべてリセット", command=self.reset_all).pack(fill=tk.X, pady=(0, 10))
    
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
                value = self.matrices[cell_data['matrix']]['values'][cell_data['row'], cell_data['col']]
                self.cell_value.delete(0, tk.END)
                self.cell_value.insert(0, str(value))
    
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
    
    def delete_matrix(self):
        """選択された行列を削除"""
        if not self.matrices_listbox.curselection():
            messagebox.showinfo("情報", "削除する行列を選択してください。")
            return
        
        index = self.matrices_listbox.curselection()[0]
        selected_matrix = self.matrices_listbox.get(index).split()[0]
        
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
            self.arrows_listbox.insert(tk.END, f"{i+1}: {source} → {target} ({arrow['color']})")
    
    def update_colored_cells_listbox(self):
        """色付き要素リストを更新"""
        self.colored_cells_listbox.delete(0, tk.END)
        for i, cell in enumerate(self.colored_cells):
            self.colored_cells_listbox.insert(tk.END, 
                f"{i+1}: {cell['matrix']}[{cell['row']},{cell['col']}] ({cell['color']})")
    
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
        
        # 矢印を追加
        self.arrows.append({
            'source': (source_matrix, source_row, source_col),
            'target': (target_matrix, target_row, target_col),
            'color': color
        })
        
        # 矢印リストを更新
        self.update_arrows_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
    
    def delete_arrow(self):
        """選択された矢印を削除"""
        if not self.arrows_listbox.curselection():
            messagebox.showinfo("情報", "削除する矢印を選択してください。")
            return
        
        index = self.arrows_listbox.curselection()[0]
        if 0 <= index < len(self.arrows):
            del self.arrows[index]
            
        # リストを更新
        self.update_arrows_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
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
                value = int(value) if value.isdigit() else float(value)
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
    
    def delete_colored_cell(self):
        """選択された色付き要素を削除"""
        if not self.colored_cells_listbox.curselection():
            messagebox.showinfo("情報", "削除する色付き要素を選択してください。")
            return
        
        index = self.colored_cells_listbox.curselection()[0]
        if 0 <= index < len(self.colored_cells):
            del self.colored_cells[index]
            
        # リストを更新
        self.update_colored_cells_listbox()
        
        # 可視化を更新
        self.visualize_matrices()
    
    def execute_command(self, event):
        """コマンドを実行"""
        command = self.console_entry.get().strip()
        if not command:
            return
        
        # コマンド履歴に追加
        self.console_history.config(state=tk.NORMAL)
        self.console_history.insert(tk.END, f"> {command}\n")
        self.console_history.see(tk.END)
        self.console_history.config(state=tk.DISABLED)
        
        # コマンドをクリア
        self.console_entry.delete(0, tk.END)
        
        # コマンドを解析して実行
        try:
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
                self.arrows.append({
                    'source': (source_matrix, source_row, source_col),
                    'target': (target_matrix, target_row, target_col),
                    'color': color
                })
                
                # リストを更新
                self.update_arrows_listbox()
                
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
                
            else:
                raise ValueError("認識できないコマンド形式です。")
            
            # 可視化を更新
            self.visualize_matrices()
            
        except ValueError as e:
            # エラーメッセージを履歴に追加
            self.console_history.config(state=tk.NORMAL)
            self.console_history.insert(tk.END, f"エラー: {str(e)}\n")
            self.console_history.see(tk.END)
            self.console_history.config(state=tk.DISABLED)
            messagebox.showerror("コマンドエラー", str(e))
    
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
        
        # キャンバスを更新
        self.canvas.draw()
    
    def draw_matrices(self):
        """すべての行列を描画"""
        for name, matrix_data in self.matrices.items():
            values = matrix_data['values']
            pos_x, pos_y = matrix_data['position']
            rows, cols = values.shape
            
            # 行列のセルを描画
            for i in range(rows):
                for j in range(cols):
                    x = pos_x + j
                    y = pos_y + i
                    rect = patches.Rectangle((x, -y-1), 1, 1, linewidth=1, edgecolor='black', facecolor='white')
                    self.ax.add_patch(rect)
                    self.ax.text(x + 0.5, -y - 0.5, str(values[i, j]), 
                                ha='center', va='center', fontsize=12)
            
            # 行列名を左上に表示
            self.ax.text(pos_x - 0.2, -pos_y, name, ha='right', va='center', fontsize=14, fontweight='bold')
    
    def draw_arrows(self):
        """すべての矢印を描画"""
        for arrow in self.arrows:
            source_name, source_row, source_col = arrow['source']
            target_name, target_row, target_col = arrow['target']
            color = arrow['color']
            
            if source_name in self.matrices and target_name in self.matrices:
                source_pos = self.matrices[source_name]['position']
                target_pos = self.matrices[target_name]['position']
                
                # 矢印の始点と終点を計算
                start_x = source_pos[0] + source_col + 0.5
                start_y = -(source_pos[1] + source_row + 0.5)
                end_x = target_pos[0] + target_col + 0.5
                end_y = -(target_pos[1] + target_row + 0.5)
                
                # 矢印を描画
                self.ax.annotate('', 
                                xy=(end_x, end_y), 
                                xytext=(start_x, start_y),
                                arrowprops=dict(arrowstyle='->', color=color, lw=2))
    
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
                
                # 色付きセルを描画
                rect = patches.Rectangle((x, -y-1), 1, 1, linewidth=1, edgecolor='black', facecolor=color)
                self.ax.add_patch(rect)
                
                # セルの値を再描画
                cell_value = self.matrices[matrix_name]['values'][row, col]
                self.ax.text(x + 0.5, -y - 0.5, str(cell_value), 
                            ha='center', va='center', fontsize=12)
    
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
        self.ax.set_title('行列演算の可視化', fontsize=16)
    
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
    
    def save_figure(self, format):
        """図を保存する"""
        filetypes = {'png': 'PNG ファイル (*.png)|*.png', 'pdf': 'PDF ファイル (*.pdf)|*.pdf'}
        default_ext = {'png': '.png', 'pdf': '.pdf'}
        
        filename = filedialog.asksaveasfilename(
            title=f"{format.upper()} として保存",
            filetypes=[(filetypes[format].split('|')[0], filetypes[format].split('|')[1])],
            defaultextension=default_ext[format]
        )
        
        if filename:
            try:
                self.fig.savefig(filename, format=format, bbox_inches='tight', dpi=300)
                messagebox.showinfo("保存完了", f"図を {filename} に保存しました。")
            except Exception as e:
                messagebox.showerror("エラー", f"保存中にエラーが発生しました: {str(e)}")
    
    def reset_all(self):
        """すべてをリセット"""
        self.matrices = {}
        self.arrows = []
        self.colored_cells = []
        self.matrices_listbox.delete(0, tk.END)
        self.arrows_listbox.delete(0, tk.END)
        self.colored_cells_listbox.delete(0, tk.END)
        self.ax.clear()
        self.ax.set_title('行列演算の可視化', fontsize=16)
        self.ax.axis('off')
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = MatrixVisualization(root)
    root.mainloop()

if __name__ == "__main__":
    main()