import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import traceback

from definitions import ROOT_DIR
from ploter import VmodelPloter
from util import ScrollText

help_msg = """## Mouse Buttons

- left_click: pick node or layer.
- ctrl+left_click: pick nodes in accumulation mode.

## Hot Keys

- up: move nodes up by distance of "dy_sm".
- down: move nodes down by distance of "dy_sm".
- left: move nodes left by distance of "dx_sm".
- right: move nodes right by distance of "dx_sm".
- ctrl+up/down/left/right: move nodes by larger distance of "dx_lg"/"dy_lg".
- esc: clear all the selections.
- n: select the Next node(s).
- p: select the Previous node(s).
- shift/ctrl+n: select the Next node(s) in accumulation mode.
- shift/ctrl+p: select the Previous node(s) in accumulation mode.
- i: Insert node(s) into the right side of selected node(s).
- d/backspace/delete: Delete selected node(s).
- ctrl+r: Reload current v.in file.
- ctrl+s: Save the modified model to current v.in file.
- v: open Velocity plot for selected layers. For all layers if no selection.
      Hot keys above is available in v-plot too.
- ctrl+i: Insert layer(s) under the layer(s) containing selected node(s).
- ctrl+d: Delete layer(s) containing selected node(s).
- ctrl+o: Open a new v.in file.
- ctrl+shift+s: Save the modified model as ....

## Variables

- dx_sm: the small step length when moving node(s) in x axis.
- dx_lg: the large step length when moving node(s) in x axis.
- dy_sm: the small step length when moving node(s) in y axis.
- dy_lg: the large step length when moving node(s) in y axis.
- pick: the pick size of cursor. A smaller pick size makes it easer to pick a
      single node, but harder to pick the whole line.
"""


class MainWindow(tk.Tk):
    """Main window"""
    def __init__(self):
        super().__init__()
        self.logger = self._get_logger()
        self.init_variables()
        self.create_widgets()
        self.bind_events()
        self.canvas.draw()

    def _get_logger(self):
        logger = logging.getLogger('VinEditor')
        logger.setLevel(logging.DEBUG)
        LOG_FILE_PATH = os.path.join(ROOT_DIR, 'log', 'main_window.log')
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def init_variables(self):
        self.vin_path = None
        self.canvas = None
        self.ploter = None
        self.fig = plt.figure(tight_layout=True)
        self.fig.patch.set_facecolor('#F0F0F0')
        # self.fig.subplots_adjust(top=0.96, bottom=0.075, left=0.1, right=0.97)
        self.ax = self.fig.add_subplot(111)
        self.ax.tick_params(axis='both', which='major', labelsize=9)
        self.ax.tick_params(axis='both', which='minor', labelsize=8)
        self.settings = {}
        self.slider_names = ['dx_sm', 'dx_lg', 'dy_sm', 'dy_lg', 'pick']
        self.slider_init_values = [0.01, 0.1, 0.001, 0.01, 0.15]
        for name, value in zip(self.slider_names, self.slider_init_values):
            self.settings[name] = tk.DoubleVar()
            self.settings[name].set(value)
        self.ctrl_mode = None
        self.shotcuts = {
            'o': self.open,
            'r': self.reload,
            's': self.save,
            'S': self.save_as,
            'w': self.exit,
            'F1': self.show_help,
        }

    def create_widgets(self):
        # bind window closing event
        self.protocol("WM_DELETE_WINDOW", self.exit)

        # make root window resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        self.create_menu()

        # frame for plotting
        plot_area = ttk.Frame(self)
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)
        plot_area.grid(row=0, column=0, sticky='nswe')

        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        self.canvas._tkcanvas.grid(sticky='nswe')
        self.ploter = VmodelPloter(MainWindowProxy(self))

        # toolbar uses pack geometry manager internally, so wrap it with a frame
        # using grid geometry manager.
        toolbar_area = ttk.Frame(self)
        toolbar_area.grid(row=1, column=0, columnspan=2, sticky='nswe')
        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_area)
        toolbar.update()

        # side frame for controlling widgets
        # side_area = ttk.Frame(self, borderwidth=2, relief=tk.GROOVE)
        side_area = ttk.Frame(self)
        side_area.rowconfigure(2, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, padx=(0, 15), sticky='nswe')

        # area for slider bars
        slider_area = self.gen_container(side_area, col_weight={1:1})
        slider_area.grid(column=0, sticky='nswe')
        sliders_con = self.gen_container(slider_area, row_weight=1, col_weight=1)
        sliders_con.grid(row=0, column=0, sticky='nswe')
        self.create_sliders(sliders_con)
        ttk.Button(slider_area, text='Reset', command=self.reset_sliders)\
            .grid(column=0, pady=(5,0), sticky='n')

        # controlling buttons
        btn_area = self.gen_container(side_area, col_weight={0:1, 1:1})
        btn_area.grid(column=0, pady=(10, 0), sticky='nswe')
        ttk.Button(btn_area, text='Open', command=self.open)\
            .grid(row=0, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Reload', command=self.reload)\
            .grid(row=0, column=1, sticky='nswe')
        ttk.Button(btn_area, text='Save', command=self.save)\
            .grid(row=1, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Save As', command=self.save_as)\
            .grid(row=1, column=1, sticky='nswe')
        ttk.Button(btn_area, text='Help', command=self.show_help)\
            .grid(row=2, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Exit', command=self.exit)\
            .grid(row=2, column=1, sticky='nswe')

        # echo message
        msg_area = self.gen_container(side_area, row_weight={1:1}, col_weight=1)
        msg_area.grid(column=0, pady=(10, 0), sticky='nswe')
        ttk.Label(msg_area, text='Selected nodes: ')\
            .grid(row=0, column=0, sticky='nsw')
        self.echo = ScrollText(msg_area, width=30, bd=0, font=('Consolas', 8), state=tk.DISABLED)
        self.echo.grid(row=1, column=0, sticky='nswe')

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.open)
        filemenu.add_command(label="Save", command=self.save)
        filemenu.add_command(label="Save As", command=self.save_as)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.exit)

        editmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=editmenu)
        editmenu.add_command(label="Undo", command=self.test)
        editmenu.add_command(label="Redo", command=self.test)

        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=helpmenu)
        helpmenu.add_command(label="Help", command=self.show_help)
        helpmenu.add_command(label="About", command=self.show_about)


    @staticmethod
    def gen_container(parent, row_weight=None, col_weight=None):
        container = ttk.Frame(parent)
        if row_weight:
            if not isinstance(row_weight, dict):
                row_weight = {0: 1}
            for k, v in row_weight.items():
                container.rowconfigure(k, weight=v)
        if col_weight:
            if not isinstance(col_weight, dict):
                col_weight = {0: 1}
            for k, v in col_weight.items():
                container.columnconfigure(k, weight=v)
        return container

    def create_sliders(self, parent):
        """create sliders in the top-right corner"""
        slider_style = dict(length=120, sliderlength=10, bd=1, sliderrelief=tk.FLAT)

        def create_slider(parent, idx, name, **kw_scale):
            ttk.Label(parent, text=name+': ').grid(row=idx, column=0, pady=(0,3), sticky='sw')
            tk.Scale(parent, orient=tk.HORIZONTAL, variable=self.settings[name], **kw_scale, **slider_style)\
                .grid(row=idx, column=1, sticky='nswe')

        create_slider(parent, idx=0, name='dx_sm', from_=0, to=0.1, resolution=0.01)
        create_slider(parent, idx=1, name='dx_lg', from_=0, to=1, resolution=0.05)
        create_slider(parent, idx=2, name='dy_sm', from_=0, to=0.01, resolution=0.001)
        create_slider(parent, idx=3, name='dy_lg', from_=0, to=0.1, resolution=0.005)
        create_slider(parent, idx=4, name='pick', from_=0, to=3, resolution=0.05)

    def bind_events(self):
        self.bind('<KeyPress>', self.on_key_press)
        self.bind('<KeyRelease>', self.on_key_release)

    def on_key_press(self, event):
        """Hot key definitions"""
        key = event.keysym
        self.logger.debug('key pressed: %s' %key)
        # entering ctrl_mode
        if key == 'Control_L':
            self.ctrl_mode = True
        else:
            if self.ctrl_mode:
                fun = self.shotcuts.get(key)
                if fun is not None:
                    fun()
                    self.ctrl_mode = False
                    return
        # Pass key events to ploter
        self.ploter.on_key_press(event)

    def on_key_release(self, event):
        """Key Releasing event"""
        key = event.keysym
        self.logger.debug('key released: %s' %key)
        # exit ctrl_mode
        if key == 'control_l':
            self.ctrl_mode = False
        # Pass key events to ploter
        self.ploter.on_key_release(event)

    def sub_title(self, text=None):
        if not text:
            return
        self.title(self.title() + ' - ' + text)

    def reset_sliders(self):
        for name, value in zip(self.slider_names, self.slider_init_values):
            self.settings[name].set(value)

    def test(self):
        messagebox.showinfo('Info', 'Not yet implemented')

    def show_help(self):
        HelpFrame(tk.Toplevel())

    def show_about(self):
        AboutFrame(tk.Toplevel())
        # messagebox.showinfo('About', 'v.in editor by <zhuhe212@163.com>')

    def show_info(self, *args, **kw):
        messagebox.showinfo(*args, **kw)

    def show_warning(self, *args, **kw):
        messagebox.showwarning(*args, **kw)

    def show_error(self, *args, **kw):
        messagebox.showerror(*args, **kw)

    def open(self):
        """Open v.in file"""
        if self.ploter.is_modified():
            okay = messagebox.askokcancel(
                'Warning', 'Do you want to open a new v.in file?\n'
                'Current modification will be lost!')
            if not okay:
                return
        p = filedialog.askopenfilename(
            defaultextension='.in',
            filetypes=[('rayinvr input file', '.in'), ('any type', '.*')],
            initialdir=os.path.join(ROOT_DIR, 'vins'),
            parent=self,
            title='Open v.in')
        p = p.strip()
        if not p:
            return
        self.vin_path = os.path.normpath(p)
        self.sub_title(self.vin_path)
        self.ploter.open()

    def reload(self):
        """Dialog when reloading current v.in file"""
        if not self.vin_path:
            return
        if self.ploter.is_modified():
            okay = messagebox.askokcancel(
                'Warning', 'Do you want to reload current v.in file?\n'
                'This will clear current modifications.')
            if not okay:
                return
        self.ploter.open()

    def save(self):
        """Dialog when saving modified model back into current v.in file"""
        if self.ploter.is_modified():
            okay = messagebox.askokcancel(
                'Info', 'Do you want to save model back into the current v.in file?')
            if not okay:
                return
        self.ploter.save()

    def save_as(self):
        """Dialog when saveing current model as ..."""
        p = filedialog.asksaveasfilename(
            title = 'Save As',
            filetypes = [('rayinvr input file', '*.in'), ('any type', '*.*')],
            initialfile = 'v.in')
        p = p.strip()
        if not p:
            return
        self.ploter.save(p)

    def exit(self):
        if self.ploter.is_modified():
            okay = messagebox.askokcancel(
                'Warning', 'Do you want to exit?\nCurrent modifications will be lost!')
            if not okay:
                return
        self.quit()
        self.destroy()

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)


class HelpFrame(ttk.Frame):
    """Help Window"""
    def __init__(self, window):
        super().__init__(window)
        window.title('v.in editor - Help')
        window.geometry('650x700+300+30')
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid(sticky='nswe')
        text = tk.Text(self, bd=0, font=('Consolas', 11))
        text.grid(row=0, column=0, sticky='nswe')
        text.insert(tk.END, help_msg)

class AboutFrame(ttk.Frame):
    """About Window"""
    def __init__(self, window):
        super().__init__(window)
        window.title('v.in editor - About')
        window.geometry('300x100+500+200')
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        self.create_widgets()

    def create_widgets(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid(sticky='nswe')
        ttk.Label(self, text='v.in editor by <zhuhe212@163.com>')\
            .grid(row=0, column=0, sticky='nswe')


class MainWindowProxy(object):
    """Proxying MainWindow Class"""
    def __init__(self, window):
        self.window = window
        self.tk_variables = ('dx_sm', 'dx_lg', 'dy_sm', 'dy_lg', 'pick')
        self.allowed_attrs = ('fig', 'ax', 'canvas', 'vin_path', 'echo')

    def __getattr__(self, attr):
        if attr in self.tk_variables:
            return self.window.settings[attr].get()
        if attr in self.allowed_attrs:
            return getattr(self.window, attr)
        raise AttributeError('Attribute "%s" is not allowed by "MainWindowProxy"' %attr)

    def bind(self, *args, **kw):
        return self.window.bind(*args, **kw)

    def show_info(self, *args, **kw):
        return self.window.show_info(*args, **kw)

    def show_warning(self, *args, **kw):
        return self.window.show_warning(*args, **kw)

    def show_error(self, *args, **kw):
        return self.window.show_error(*args, **kw)



if __name__ == '__main__':
    window = MainWindow()
    window.wm_title('v.in editor')
    window.geometry('1000x600+200+30')
    window.mainloop()
