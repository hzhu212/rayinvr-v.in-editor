# -*- coding: utf-8 -*-

import functools
import logging
import tkinter as tk
import tkinter.messagebox
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button

from ploter import VmodelPloter


# public dialogs

help_msg = """
鼠标操作：
左键: 点击节点选中一个节点，点击曲线选中整个层
Ctrl+左键: 多选和取消多选
中键: 取消所有选中状态
--------------------------------------------------
快捷键：
up: 将所有选中的节点上移 1 个 step_y_sm 的距离
down: 将所有选中的节点下移 1 个 step_y_sm 的距离
ctrl+up: 将所有选中的节点上移 1 个 step_y_lg 的距离
ctrl+down: 将所有选中的节点下移 1 个 step_y_lg 的距离
c: 取消所有选中状态
n: 选中当前节点的下一个节点
p: 选中当前节点的前一个节点
shift+n: 选中当前节点的下一个节点，累积模式，已选中的不清除
shift+p: 选中当前节点的前一个节点，累积模式，已选中的不清除
i: 在选中的节点右侧插入新节点
delete/d: 删除选中的节点
ctrl+o: open，打开新的 v.in 文件
ctrl+r: reload，重新打开关联的 v.in 文件，以清除当前更改
ctrl+s: 将当前模型回写到关联的 v.in 文件中
ctrl+shift+s: 将当前模型另存为 v.in 文件
--------------------------------------------------
参数说明：
step_x_sm: small，按 left/right 键时节点沿 x 轴运动的小段距离
step_x_lg: large，按 ctrl+left/right 键时节点沿 x 轴运动的较大距离
step_y_sm: 按 up/down 键时节点沿 y 轴运动的小段距离
step_y_lg: 按 ctrl+up/down 键时节点沿 y 轴运动的较大距离
pick_size: 鼠标点选操作的笔尖大小，笔尖越小越不容易选中节点，越容易选中整条曲线
"""

def select_vin_dialog():
    """选择 v.in 文件对话框"""
    path_vin = tk.filedialog.askopenfilename(
        # doc in http://effbot.org/tkinterbook/tkinter-file-dialogs.htm
        title = 'Choose v.in file',
        filetypes = [('model input file', '*.in'), ('any type', '*.*')],
        initialfile = 'v.in'
        )
    # if not path_vin.strip():
    #     tk.messagebox.showerror('错误', '您似乎没有成功地选取 v.in 文件')
    #     return
    return path_vin


class VmodelEditor(tk.Frame):
    """vin-editor 图形界面
    tkinter document: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/index.html"""
    def __init__(self, master=None):
        super(VmodelEditor, self).__init__(master)
        self.master.title('v.in 编辑器')
        self.master.geometry('500x300+100+100')
        self.pack()
        self.createWidgets()

    def createWidgets(self):
        self.path_vin_input = tk.Entry(self, width=60, font=('Consolas', 10))
        self.path_vin_input.pack(ipady=3, pady=20)
        self.select_button = tk.Button(self, text='Select v.in', command=self.select_vin)
        self.select_button.pack(pady=20)
        self.load_button = tk.Button(self, text='Load', command=self.open_model)
        self.load_button.pack(pady=20)

    def select_vin(self):
        path_vin = select_vin_dialog()
        if path_vin is None:
            return
        self.path_vin_input.delete(0, tk.END)
        self.path_vin_input.insert(0, path_vin)

    def open_model(self):
        """打开模型，该操作将会创建一个新的模型窗口
        如果不想创建新的模型窗口，请在当前模型窗口内按 ctrl+o 快捷键"""
        path_vin = self.path_vin_input.get()
        if not path_vin.strip():
            tk.messagebox.showerror('错误', '请输入 v.in 文件路径或选择一个 v.in 文件')
            return
        plot_window = PloterWindow()
        plot_window.bind_ploter(path_vin)
        plot_window.show()


class PloterWindow(object):
    """绘图对象所在的窗口对象，用于处理绘图之外的事件，比如弹出对话框、提示帮助信息、设置绘图超参数等"""
    def __init__(self):
        super(PloterWindow, self).__init__()
        # 采用 gridspec 进行布局
        # 左侧区域包含单个绘图 axes
        self.fig = plt.figure(figsize=(10,6))
        self.fig.subplots_adjust(top=0.95, bottom=0.05)
        self.plot_grid = gridspec.GridSpec(1, 1)
        self.plot_grid.update(left=0.05, right=0.70)
        self.plot_ax = plt.subplot(self.plot_grid[0, 0])
        # 右侧区域包含一群控件 axes
        self.widget_grid = gridspec.GridSpec(15, 12)
        self.widget_grid.update(left=0.75, right=0.95, hspace=0.5, wspace=0.3)
        # 将 ploter 对象绑定到左侧的绘图区
        self.ploter = None
        self.slider_vals = None
        self.dont_show_save_dialog = False
        self.init_keymap()
        self.init_widgets()

    def bind_ploter(self, path_vin):
        """绑定 plotter 对象"""
        self.ploter = VmodelPloter(path_vin=path_vin, window=self)

    def show(self):
        self.ploter.plot()

    def init_keymap(self):
        """禁用一些冲突的快捷键"""
        try:
            plt.rcParams['keymap.home'].remove('home')
            plt.rcParams['keymap.back'].remove('left')
            plt.rcParams['keymap.back'].remove('c')
            plt.rcParams['keymap.forward'].remove('right')
            plt.rcParams['keymap.pan'].remove('p')
            plt.rcParams['keymap.save'].remove('ctrl+s')
        except ValueError as e:
            pass

    def init_widgets(self):
        ax1 = plt.subplot(self.widget_grid[0, 2:])
        ax2 = plt.subplot(self.widget_grid[1, 2:])
        ax3 = plt.subplot(self.widget_grid[2, 2:])
        ax4 = plt.subplot(self.widget_grid[3, 2:])
        ax5 = plt.subplot(self.widget_grid[4, 2:])
        ax6 = plt.subplot(self.widget_grid[5, :])
        ax10 = plt.subplot(self.widget_grid[-4, :6])
        ax11 = plt.subplot(self.widget_grid[-4, 6:])
        ax12 = plt.subplot(self.widget_grid[-3, :6])
        ax13 = plt.subplot(self.widget_grid[-3, 6:])
        ax_2 = plt.subplot(self.widget_grid[-1, :6])
        ax_1 = plt.subplot(self.widget_grid[-1, 6:])

        self.slider1 = Slider(ax1, 'step_x_sm', 0, 0.05, 0.01, '%.2f')
        self.slider2 = Slider(ax2, 'step_x_lg', 0, 0.5, 0.05, '%.2f')
        self.slider3 = Slider(ax3, 'step_y_sm', 0, 0.005, 0.001, '%.3f')
        self.slider4 = Slider(ax4, 'step_y_lg', 0, 0.05, 0.005, '%.3f')
        self.slider5 = Slider(ax5, 'pick_size', 0, 2, 0.15, '%.2f')
        self.sliders = (self.slider1, self.slider2, self.slider3, self.slider4, self.slider5)
        self.slider_intervals = (0.01, 0.05, 0.001, 0.005, 0.05)
        self.slider_vals = [sld.val for sld in self.sliders]
        self.reset_btn = Button(ax6, 'Reset')
        self.open_btn = Button(ax10, 'Open')
        self.reload_btn = Button(ax11, 'Reload')
        self.save_btn = Button(ax12, 'Save')
        self.saveas_btn = Button(ax13, 'Save As')
        self.help_btn = Button(ax_2, 'Help')
        self.exit_btn = Button(ax_1, 'Exit')

        # 绑定回调事件
        for i,sld in enumerate(self.sliders):
            sld.on_changed(self.handle_slider_changed(i))
        self.reset_btn.on_clicked(self.handle_reset_btn)
        self.open_btn.on_clicked(self.handle_open_btn)
        self.reload_btn.on_clicked(self.handle_reload_btn)
        self.save_btn.on_clicked(self.handle_save_btn)
        self.saveas_btn.on_clicked(self.handle_saveas_btn)
        self.help_btn.on_clicked(self.handle_help_btn)
        self.exit_btn.on_clicked(self.handle_exit_btn)
        self._close_by_exit_btn = False
        self.fig.canvas.mpl_connect('close_event', self.handle_close)

    # event handlers

    def handle_exit_btn(self, event):
        if self.ploter.is_modified() and not self.close_window_dialog():
            return
        self._close_by_exit_btn = True
        plt.close(self.fig)

    def handle_close(self, event):
        """直接关闭窗口时弹出警告，告诉用途通过 Exit 按钮退出程序"""
        if self._close_by_exit_btn:
            return
        self.show_warning('请勿直接关闭窗口！\n可能会导致工作状态丢失，请总是使用 Exit 按钮退出程序！')
        if self.ploter.is_modified():
            import datetime as dt
            import os
            quick_save_name = 'quick_save_%s_v.in' %(dt.datetime.now().strftime('%Y%m%d%H%M%S'))
            full_path = os.path.join(os.path.split(self.ploter.path_vin)[0], quick_save_name)
            self.ploter.save_as(full_path)
            self.show_warning('检测到您有未保存的更改，系统已帮您保存到同目录下的 %s 文件中' %quick_save_name)

    def handle_slider_changed(self, idx):
        """滑动条拖动回调，为 4 个滑动条分别返回一个回调函数"""
        return functools.partial(self.slider_changed, i=idx)

    def handle_reset_btn(self, event):
        self.reset_sliders()

    def handle_help_btn(self, event):
        self.show_help()

    def handle_open_btn(self, event):
        self.open_vin()

    def handle_reload_btn(self, event):
        self.reload_vin()

    def handle_save_btn(self, event):
        self.save_back()

    def handle_saveas_btn(self, event):
        self.save_as()

    def slider_changed(self, val, i):
        """第 i 个 slider 发生改变"""
        bigint = 10000
        sld = self.sliders[i]
        itv = self.slider_intervals[i]
        val_int = int(val * bigint)
        itv_int = int(itv * bigint)
        logging.debug('%dth slider with interval %f changed to %f' %(i,itv,val))
        if val_int % itv_int < 1e-8:
            self.slider_vals[i] = val_int / bigint
            return
        carry = 1 if val_int % itv_int >= itv_int/2 else 0
        sld.set_val((val_int // itv_int + carry) * (itv_int/bigint))

    def reset_sliders(self):
        """重置滑动条"""
        for sld in self.sliders:
            sld.reset()
        self.slider_vals = [sld.val for sld in self.sliders]

    def open_vin(self):
        """打开新的 v.in"""
        if self.ploter.is_modified():
            if not self.open_dialog():
                return
        new_path_vin = select_vin_dialog()
        if not new_path_vin: return
        self.ploter.set_path_vin(new_path_vin)
        self.ploter.reload()

    def reload_vin(self):
        """重新载入当前 v.in"""
        if self.ploter.is_modified() and not self.open_dialog():
            return
        self.ploter.reload()

    def save_back(self):
        """将修改后的模型保存回关联的 v.in 文件中"""
        if self.ploter.is_modified() and self.save_dialog():
            self.ploter.save_back()
            return

    def save_as(self):
        """将模型另存为"""
        save_path = self.save_as_dialog()
        if not save_path:
            return
        self.ploter.save_as(save_path)

    def show_help(self):
        tk.messagebox.askokcancel('Help', help_msg)

    def show_warning(self, msg):
        tk.messagebox.showwarning('警告', msg)

    def show_error(self, msg):
        tk.messagebox.showerror('错误', msg)

    def close_window_dialog(self):
        """关闭窗口时弹出提示框"""
        return tk.messagebox.askokcancel('提示', '您确定要关闭窗口吗？\n您对当前模型的所有未保存更改将丢失')

    def open_dialog(self):
        """打开新的 v.in 文件时弹出提示框"""
        return tk.messagebox.askokcancel('提示', '您确定要打开新的 v.in 文件吗？\n您对当前模型的所有未保存更改将丢失')

    def reload_dialog(self):
        """重新载入 v.in 文件时弹出提示框"""
        return tk.messagebox.askokcancel('提示', '您确定要重新载入当前 v.in 文件吗？\n这将重置所有未保存的修改')

    def save_dialog(self):
        """将模型回写到 v.in 文件时弹出提示框"""
        if self.dont_show_save_dialog:
            return True
        res = tk.messagebox.askyesnocancel('提示', '您确定要将当前修改回写到 v.in 文件吗？\n这将覆盖当前的 v.in 文件\n点击“取消”将不再显示此对话框')
        if res is None:
            self.dont_show_save_dialog = True
            return False
        return res

    def save_as_dialog(self):
        """将模型另存为文件时弹出文件选择框"""
        save_path = tk.filedialog.asksaveasfilename(
            title = '另存为',
            filetypes = [('model input file', '*.in'), ('any type', '*.*')],
            initialfile = 'v.in'
            )
        if not save_path.strip():
            # tk.messagebox.showerror('错误', '您似乎没有成功选择保存路径')
            return
        return save_path
