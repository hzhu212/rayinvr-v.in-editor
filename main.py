import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import traceback


help_msg = """
------------------------ Mouse Buttons --------------------------
left_click: pick node(s) or layer surface(s).
Ctrl+left_click: enable multiple selection mode.

------------------------ Hot Keys --------------------------
up: move all the selected nodes Up by a distance of "dy_sm".
down: move all the selected nodes Down by a distance of "dy_sm".
left: move all the selected nodes Left by a distance of "dx_sm".
right: move all the selected nodes Right by a distance of "dx_sm".
ctrl+up/down/left/right: move by a larger distance of "dx/y_lg".
c: Clear all the selections.
n: select the Next node(s).
p: select the Previous node(s).
shift/ctrl+n: select the Next node(s) in accumulation mode.
shift/ctrl+p: select the Previous node(s) in accumulation mode.
i: Insert node(s) into the right side of selected node(s).
d: Delete selected node(s).
ctrl+r: Reload current v.in file.
ctrl+s: Save the modified model to current v.in file.
v: open Velocity plot for selected layers. For all layers if no selection.
    Hot keys above is available in v-plot too!
ctrl+i: Insert layer(s) under the layer(s) containing selected node(s).
ctrl+d: Delete layer(s) containing selected node(s).
ctrl+o: Open a new v.in file.
ctrl+shift+s: Save the modified model to another file.

------------------------ Other Hints --------------------------
dx_sm: sm-small, the distance of small step in x direction.
dx_lg: lg-large, the distance of large step in x direction.
dy_sm: the distance of small step in y direction.
dy_lg: the distance of large step in y direction.
pick_size: the pick size of the cursor. If the pick size is smaller,
    it's easer to pick a single node, but harder to pick the whole line.

"""


class MainWindow(tk.Tk):
    """Main window"""
    def __init__(self):
        super().__init__()
        self.logger = self._get_logger()
        self.init_variables()
        self.create_widgets()
        self.plot()
        self.canvas.draw()

    def _get_logger(self):
        logger = logging.getLogger('VinEditor')
        logger.setLevel(logging.DEBUG)
        LOG_FILE_PATH = os.path.join('log', 'main_window.log')
        file_handler = logging.FileHandler(LOG_FILE_PATH, encoding='utf8')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    def init_variables(self):
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

        # toolbar uses pack geometry manager internally, so wrap it with a frame
        # using grid geometry manager.
        toolbar_area = ttk.Frame(self)
        toolbar_area.grid(row=1, column=0, columnspan=2, sticky='nswe')
        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_area)
        toolbar.update()

        # side frame for controlling widgets
        # side_area = ttk.Frame(self, borderwidth=2, relief=tk.GROOVE)
        side_area = ttk.Frame(self)
        side_area.rowconfigure(1, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, padx=(0, 20), sticky='nswe')

        # area for slider bars
        slider_area = self.gen_container(side_area, col_weight={1:1})
        slider_area.grid(row=0, column=0, sticky='nswe')
        sliders_con = self.gen_container(slider_area, row_weight=1, col_weight=1)
        sliders_con.grid(row=0, column=0, sticky='nswe')
        self.create_sliders(sliders_con)
        ttk.Button(slider_area, text='Reset', command=self.reset_sliders)\
            .grid(column=0, pady=(5,0), sticky='n')

        # controlling buttons
        btn_area = self.gen_container(side_area, col_weight={0:1, 1:1})
        btn_area.grid(column=0, pady=(20, 0), sticky='nswe')
        ttk.Button(btn_area, text='Open', command=self.test)\
            .grid(row=0, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Reload', command=self.test)\
            .grid(row=0, column=1, sticky='nswe')
        ttk.Button(btn_area, text='Save', command=self.test)\
            .grid(row=1, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Save As', command=self.test)\
            .grid(row=1, column=1, sticky='nswe')
        ttk.Button(btn_area, text='Help', command=self.show_help)\
            .grid(row=2, column=0, sticky='nswe')
        ttk.Button(btn_area, text='Exit', command=self.exit)\
            .grid(row=2, column=1, sticky='nswe')

    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=filemenu)
        filemenu.add_command(label="Open", command=self.test)
        filemenu.add_command(label="Save", command=self.test)
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

    def plot(self):
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x)
        self.ax.plot(x, y)

    def reset_sliders(self):
        for name, value in zip(self.slider_names, self.slider_init_values):
            self.settings[name].set(value)

    def test(self):
        messagebox.showinfo('Info', 'Just a test')

    def show_help(self):
        new_window = tk.Toplevel()
        new_window.title('v.in editor - help')
        new_window.geometry('650x700+300+30')
        new_window.rowconfigure(0, weight=1)
        new_window.columnconfigure(0, weight=1)
        help_frame = HelpFrame(new_window)
        help_frame.grid(sticky='nswe')

    def show_about(self):
        messagebox.showinfo('About', 'v.in editor by <zhuhe212@163.com>')

    def exit(self):
        self.quit()
        self.destroy()

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)



class HelpFrame(ttk.Frame):
    """Helpi Window"""
    def __init__(self, master):
        super().__init__(master)
        self.create_widgets()

    def create_widgets(self):
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # ttk.Label(self, text='Help: ').grid(row=0, column=0, sticky='nsw')
        text = tk.Text(self, bd=0, font=('Consolas', 11))
        text.grid(row=0, column=0, sticky='nswe')
        text.insert(tk.END, help_msg)


if __name__ == '__main__':
    window = MainWindow()
    window.wm_title('v.in editor')
    window.geometry('1000x600+200+30')
    window.mainloop()
