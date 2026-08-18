"""
文件夹存储占用分析器 —— 主窗口
阶段二：GUI 骨架
阶段三：分析与绘图联动（analyze / draw_chart / fill_list）
阶段四：交互（下钻 / 返回 / 拖拽）
"""

import tkinter as tk
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# 配置中文字体，避免中文乱码（按系统可用字体依次回退）
from matplotlib import font_manager

_CHINESE_FONTS = ["Microsoft YaHei", "SimHei", "SimSun", "Arial Unicode MS"]
_available = {f.name for f in font_manager.fontManager.ttflist}
for _fn in _CHINESE_FONTS:
    if _fn in _available:
        plt.rcParams["font.family"] = _fn
        break
plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号


class FolderAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("文件夹存储占用分析器")
        self.root.geometry("960x740")
        self.root.minsize(820, 620)

        # 外观主题
        self._setup_style()

        # 状态
        self.current_path = None
        self.path_stack = []
        self.current_items = {}
        self.current_mapping = {}
        self._wedge_labels = {}  # wedge id -> label（下钻用）
        self._wedge_size = {}    # wedge id -> 字节数（hover/tooltip 用）
        self._wedge_pct = {}     # wedge id -> 占比（hover/tooltip 用）
        self._hovered_wedge = None
        self._annot = None       # 当前悬浮注释

        self._build_ui()
        self._draw_placeholder_chart()
        self._bind_chart_events()
        self._register_drop()

    # ------------------------------------------------------------------ #
    # 外观主题（问题1：更美观）
    # ------------------------------------------------------------------ #
    def _setup_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        # 主色调
        BG = "#f4f6fb"
        ACCENT = "#3b6fd4"
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground="#222", font=("Microsoft YaHei", 10))
        style.configure("TButton", font=("Microsoft YaHei", 10), padding=4)
        style.map("TButton",
                  background=[("active", ACCENT), ("!disabled", "#e8edf7")],
                  foreground=[("active", "#fff"), ("!disabled", "#222")])
        style.configure("Title.TLabel", font=("Microsoft YaHei", 16, "bold"),
                        foreground=ACCENT, background=BG)
        style.configure("Header.TLabel", font=("Microsoft YaHei", 10, "bold"),
                        foreground="#555", background=BG)
        style.configure("Drop.TLabel",
                        font=("Microsoft YaHei", 10), foreground="#3b6fd4",
                        background="#e8edf7", relief="solid")
        style.configure("TLabelframe", background=BG, foreground="#333",
                        font=("Microsoft YaHei", 10, "bold"))
        style.configure("TLabelframe.Label", background=BG, foreground=ACCENT,
                        font=("Microsoft YaHei", 10, "bold"))
        style.configure("Treeview", font=("Microsoft YaHei", 9), rowheight=22)
        style.configure("Treeview.Heading", font=("Microsoft YaHei", 9, "bold"))
        # 返回按钮高亮样式
        style.map("Back.TButton",
                  background=[("disabled", "#cccccc"), ("active", "#2a55a8"), ("!disabled", ACCENT)],
                  foreground=[("disabled", "#777"), ("!disabled", "#ffffff")])
        self.root.configure(bg=BG)

    # ------------------------------------------------------------------ #
    # 阶段二：界面搭建
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        # 标题栏
        title_frame = ttk.Frame(self.root, padding=(12, 10, 12, 4))
        title_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(title_frame, text="📁 文件夹存储占用分析器", style="Title.TLabel").pack(side=tk.LEFT)
        ttk.Label(title_frame, text="  递归统计 · 扇形图 · 下钻分析",
                  style="Header.TLabel").pack(side=tk.LEFT, padx=8)

        # 顶部输入区
        top_frame = ttk.Frame(self.root, padding=(12, 4, 12, 8))
        top_frame.pack(side=tk.TOP, fill=tk.X)
        ttk.Label(top_frame, text="文件夹路径：", style="Header.TLabel").pack(side=tk.LEFT)
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(top_frame, textvariable=self.path_var, font=("Microsoft YaHei", 10))
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)
        ttk.Button(top_frame, text="📂 浏览...", command=self._on_browse).pack(side=tk.LEFT, padx=3)
        ttk.Button(top_frame, text="🔍 分析", command=self._on_analyze).pack(side=tk.LEFT, padx=3)

        # 拖拽提示条
        drop_frame = ttk.Frame(self.root, padding=(12, 0, 12, 6))
        drop_frame.pack(side=tk.TOP, fill=tk.X)
        self.drop_label = ttk.Label(
            drop_frame, text="可将文件夹拖拽到此处（或本窗口）进行分析",
            style="Drop.TLabel", anchor=tk.CENTER, padding=8
        )
        self.drop_label.pack(fill=tk.X, padx=2, pady=2)

        # 信息栏
        info_frame = ttk.Frame(self.root, padding=(12, 2, 12, 6))
        info_frame.pack(side=tk.TOP, fill=tk.X)
        self.info_path = ttk.Label(info_frame, text="当前路径：-", anchor=tk.W, style="Header.TLabel")
        self.info_path.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.info_size = ttk.Label(info_frame, text="总大小：-", anchor=tk.E, style="Header.TLabel")
        self.info_size.pack(side=tk.LEFT, padx=10)
        self.back_btn = ttk.Button(info_frame, text="↑ 返回上一级", style="Back.TButton",
                                   command=self._on_back, state=tk.DISABLED)
        self.back_btn.pack(side=tk.RIGHT)

        # 主区域：左饼图 + 右明细
        main_frame = ttk.Frame(self.root, padding=(12, 4, 12, 12))
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # 左侧饼图
        chart_frame = ttk.LabelFrame(main_frame, text="占用占比（双击扇区下钻 · 悬停查看详情）", padding=6)
        chart_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.fig = plt.Figure(figsize=(5.2, 4.2), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=chart_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # 右侧明细
        list_frame = ttk.LabelFrame(main_frame, text="明细列表", padding=6)
        list_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        columns = ("name", "size", "ratio")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("name", text="名称")
        self.tree.heading("size", text="大小")
        self.tree.heading("ratio", text="占比")
        self.tree.column("name", width=170)
        self.tree.column("size", width=90)
        self.tree.column("ratio", width=70)
        vsb = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)

    def _draw_placeholder_chart(self):
        """阶段二占位图，提示尚未分析。"""
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        ax.text(0.5, 0.5, "请选择文件夹\n开始分析", ha="center", va="center", fontsize=14)
        ax.set_axis_off()
        self.canvas.draw()

    # ------------------------------------------------------------------ #
    # 阶段三：分析与绘图联动
    # ------------------------------------------------------------------ #
    def analyze(self, path):
        """分析指定文件夹（绝对路径），刷新饼图与明细列表。"""
        import os
        from core.scanner import scan_directory, build_chart_data, human_size

        if not path or not os.path.isdir(path):
            from tkinter import messagebox
            messagebox.showerror("错误", f"路径无效或不是文件夹：\n{path}")
            return

        try:
            items = scan_directory(path)
        except (PermissionError, OSError) as e:
            from tkinter import messagebox
            messagebox.showwarning("访问警告", f"无法访问文件夹：\n{path}\n{e}")
            return

        self.current_path = os.path.abspath(path)
        self.current_items = items
        labels, sizes, mapping = build_chart_data(items)
        self.current_mapping = mapping

        total = sum(items.values())
        self.info_path.config(text=f"当前路径：{self.current_path}")
        self.info_size.config(text=f"总大小：{human_size(total)}（{total} B）")
        self._update_back_button()

        self.draw_chart(labels, sizes)
        self.fill_list(items, total)

    def draw_chart(self, labels, sizes):
        """根据标签与大小绘制饼图（问题2/3：小扇区不显示文字，悬停反馈）。"""
        self.fig.clf()
        ax = self.fig.add_subplot(111)
        self._wedge_labels.clear()
        self._wedge_size.clear()
        self._wedge_pct.clear()
        self._hovered_wedge = None
        if self._annot:
            self._annot = None

        if not sizes:
            ax.text(0.5, 0.5, "该文件夹为空\n或无可统计内容", ha="center", va="center", fontsize=12)
            ax.set_axis_off()
            self.canvas.draw()
            return

        import os
        from core.scanner import human_size
        folder_name = os.path.basename(self.current_path) or self.current_path
        total = sum(sizes)

        # 问题2：占比过小的扇区不显示名称与百分比，避免遮挡
        SMALL_LABEL_RATIO = 0.03
        show_label = [ (s / total) >= SMALL_LABEL_RATIO for s in sizes ]

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=[lb if sh else "" for lb, sh in zip(labels, show_label)],
            autopct=lambda p: f"{p:.1f}%" if p / 100.0 >= SMALL_LABEL_RATIO else "",
            startangle=90,
            textprops={"fontsize": 9},
            wedgeprops={"linewidth": 1, "edgecolor": "white"},
        )
        ax.set_title(f"{folder_name} 占用占比", fontsize=12, fontweight="bold")

        for w, lb, s in zip(wedges, labels, sizes):
            self._wedge_labels[id(w)] = lb
            self._wedge_size[id(w)] = s
            self._wedge_pct[id(w)] = s / total * 100

        # 用于 hover 放大反馈的原始半径
        self._base_radius = 1.0
        self.canvas.draw()

    def fill_list(self, items, total):
        """刷新右侧明细列表。"""
        from core.scanner import human_size
        self.tree.delete(*self.tree.get_children())
        if total == 0:
            return
        for name, size in sorted(items.items(), key=lambda x: -x[1]):
            ratio = size / total * 100
            self.tree.insert("", tk.END, values=(name, human_size(size), f"{ratio:.2f}%"))

    def _update_back_button(self):
        """根据下钻栈更新返回按钮状态。"""
        if self.path_stack:
            self.back_btn.config(state=tk.NORMAL)
        else:
            self.back_btn.config(state=tk.DISABLED)

    # ------------------------------------------------------------------ #
    # 阶段四：交互（下钻 / 返回 / 拖拽）
    # ------------------------------------------------------------------ #
    def _bind_chart_events(self):
        """绑定饼图交互事件：移动（悬停反馈）、单击/双击（下钻）。"""
        self.canvas.mpl_connect("motion_notify_event", self._on_chart_hover)
        self.canvas.mpl_connect("button_press_event", self._on_chart_click)

    def _hit_wedge(self, event):
        """根据鼠标位置返回命中的 wedge 对象（未命中返回 None）。"""
        if event.inaxes is None or event.xdata is None or event.ydata is None:
            return None
        import math

        cx, cy = event.xdata, event.ydata
        # 饼图圆心在 (0,0)，半径 1；点击需在圆内
        if math.hypot(cx, cy) > 1.0:
            return None
        # 数据坐标下的数学角度（从 +x 轴逆时针），与 matplotlib wedge.theta 同定义
        theta = math.degrees(math.atan2(cy, cx)) % 360.0
        ax = event.inaxes
        for w in ax.patches:
            # 用模运算判断 theta 是否落在 [theta1, theta2] 区间，
            # 正确处理跨越 360° 的扇区（如 theta2 = 450）
            span = (w.theta2 - w.theta1) % 360.0
            diff = (theta - w.theta1) % 360.0
            if 0.0 <= diff <= span:
                return w
        return None

    def _on_chart_hover(self, event):
        """悬停某扇区：高亮 + 浮动提示 + 联动右侧列表（问题2/3）。"""
        w = self._hit_wedge(event)
        if w is None:
            if self._hovered_wedge is not None:
                self._hovered_wedge = None
                self._highlight_wedge(None)
                self._show_annot(None)
                self._select_in_tree(None)
                self.canvas.draw_idle()
            return

        if id(w) != id(self._hovered_wedge) if self._hovered_wedge else True:
            self._hovered_wedge = w
            self._highlight_wedge(w)
            self._show_annot(w, event)
            self._select_in_tree(self._wedge_labels.get(id(w)))
            self.canvas.draw_idle()

    def _highlight_wedge(self, w):
        """问题3：悬停扇区放大并提亮，其余恢复原状。"""
        for wedge in self.fig.axes[0].patches:
            if w is None:
                wedge.set_radius(self._base_radius)
                wedge.set_alpha(1.0)
            elif wedge is w:
                wedge.set_radius(self._base_radius * 1.06)
                wedge.set_alpha(1.0)
            else:
                wedge.set_radius(self._base_radius)
                wedge.set_alpha(0.55)

    def _show_annot(self, w, event=None):
        """问题2：悬停时浮动显示该扇区名称/大小/占比（小扇区尤其适用）。"""
        ax = self.fig.axes[0]
        # 清除旧注释
        for txt in list(ax.texts):
            if getattr(txt, "_is_hover_annot", False):
                txt.remove()
        self._annot = None
        if w is None:
            return
        lb = self._wedge_labels.get(id(w))
        sz = self._wedge_size.get(id(w), 0)
        pct = self._wedge_pct.get(id(w), 0.0)
        from core.scanner import human_size
        text = f"{lb}\n{human_size(sz)}  ({pct:.1f}%)"
        # 注释放在扇区中点外侧
        import math
        mid = math.radians((w.theta1 + w.theta2) / 2.0)
        r = self._base_radius + 0.18
        x = r * math.cos(mid)
        y = r * math.sin(mid)
        annot = ax.annotate(
            text, xy=(x, y), ha="center", va="center",
            fontsize=9, bbox=dict(boxstyle="round,pad=0.4", fc="#fff7d6", ec="#d4a017"),
            zorder=10,
        )
        annot._is_hover_annot = True
        self._annot = annot

    def _select_in_tree(self, label):
        """悬停时右侧明细列表高亮对应行。"""
        if label is None:
            self.tree.selection_remove(*self.tree.selection())
            return
        for item in self.tree.get_children():
            if self.tree.item(item, "values")[0] == label:
                self.tree.selection_set(item)
                self.tree.see(item)
                return

    def _on_chart_click(self, event):
        """单击高亮反馈；双击触发下钻（问题3）。"""
        if event.inaxes is None:
            return
        w = self._hit_wedge(event)
        if w is None:
            return
        # 点击反馈：短暂加粗描边
        self._flash_wedge(w)
        if event.dblclick:
            self._drill_down(self._wedge_labels.get(id(w)))

    def _flash_wedge(self, w):
        """点击扇区的瞬时视觉反馈。"""
        orig_lw = w.get_linewidth()
        w.set_linewidth(3.0)
        w.set_edgecolor("#3b6fd4")
        self.canvas.draw_idle()
        self.root.after(180, lambda: (
            w.set_linewidth(orig_lw), w.set_edgecolor("white"), self.canvas.draw_idle()
        ))

    def _drill_down(self, label):
        """下钻到指定扇区对应的子文件夹。"""
        from tkinter import messagebox
        import os
        if label is None or label == "其他":
            return  # "其他" 为合并项，无具体子文件夹
        target = os.path.join(self.current_path, label)
        if not os.path.isdir(target):
            return
        self.path_stack.append(self.current_path)
        self.analyze(target)

    def _on_back(self):
        """返回上一级文件夹。"""
        if not self.path_stack:
            return
        parent = self.path_stack.pop()
        self.analyze(parent)

    def _register_drop(self):
        """注册 Windows 拖拽文件夹到窗口（零依赖 ctypes 方案）。"""
        try:
            import ctypes
            from ctypes import wintypes

            self._drag_query_file = ctypes.windll.shell32.DragQueryFileW
            self._drag_finish = ctypes.windll.shell32.DragFinish
            user32 = ctypes.windll.user32
            GWLP_WNDPROC = -4
            WM_DROPFILES = 0x0233

            # 正确声明 64 位窗口过程相关 API 的类型，避免指针截断
            user32.GetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int]
            user32.GetWindowLongPtrW.restype = ctypes.c_uint64
            user32.SetWindowLongPtrW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_uint64]
            user32.SetWindowLongPtrW.restype = ctypes.c_uint64
            user32.CallWindowProcW.argtypes = [
                ctypes.c_void_p, wintypes.HWND, wintypes.UINT,
                ctypes.c_uint64, ctypes.c_uint64,
            ]
            user32.CallWindowProcW.restype = ctypes.c_int64

            hwnd = self.root.winfo_id()
            ctypes.windll.shell32.DragAcceptFiles(hwnd, True)

            # 保存原始窗口过程（无符号 64 位指针）
            orig = user32.GetWindowLongPtrW(hwnd, GWLP_WNDPROC)
            orig_ptr = ctypes.c_void_p(orig)

            WndProcType = ctypes.WINFUNCTYPE(
                ctypes.c_int64,  # LRESULT (64-bit)
                ctypes.c_int64,  # HWND
                ctypes.c_uint,   # UINT msg
                ctypes.c_uint64, # WPARAM
                ctypes.c_uint64, # LPARAM
            )

            def wnd_proc(hwnd, msg, wparam, lparam):
                if msg == WM_DROPFILES:
                    try:
                        self._on_drop_files(wparam)
                    finally:
                        self._drag_finish(wparam)
                    return 0
                return user32.CallWindowProcW(
                    orig_ptr, hwnd, msg,
                    ctypes.c_uint64(wparam), ctypes.c_uint64(lparam)
                )

            self._wnd_proc_ptr = WndProcType(wnd_proc)
            user32.SetWindowLongPtrW(hwnd, GWLP_WNDPROC, ctypes.c_uint64(ctypes.cast(self._wnd_proc_ptr, ctypes.c_void_p).value))
        except Exception as e:
            # 拖拽不可用时静默失败，界面仍支持浏览/输入
            print(f"[提示] 拖拽功能不可用：{e}")

    def _on_drop_files(self, hdrop):
        """处理拖入的文件/文件夹（DragFinish 由 wnd_proc 统一调用）。"""
        import os
        import ctypes
        from tkinter import messagebox
        buf = ctypes.create_unicode_buffer(1024)
        count = self._drag_query_file(hdrop, 0xFFFFFFFF, None, 0)
        for i in range(count):
            self._drag_query_file(hdrop, i, buf, 1024)
            dropped = buf.value
            if os.path.isdir(dropped):
                self.path_var.set(dropped)
                self.path_stack = []
                self.analyze(dropped)
                return
        messagebox.showinfo("提示", "请拖拽文件夹（而非文件）进行分析。")

    # ------------------------------------------------------------------ #
    # 阶段三回调：浏览 / 分析
    # ------------------------------------------------------------------ #
    def _on_browse(self):
        from tkinter import filedialog
        path = filedialog.askdirectory(title="选择要分析的文件夹")
        if path:
            self.path_var.set(path)
            self.path_stack = []  # 新分析重置下钻栈
            self.analyze(path)

    def _on_analyze(self):
        path = self.path_var.get().strip()
        self.path_stack = []
        self.analyze(path)


def main():
    root = tk.Tk()
    app = FolderAnalyzerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
