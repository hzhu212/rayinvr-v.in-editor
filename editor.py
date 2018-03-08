import functools
import logging
import tkinter as tk
import tkinter.filedialog
import tkinter.messagebox
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.widgets import Slider, Button

from ploter import VmodelPloter


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

def select_vin_dialog():
    """dialog for selecting v.in file"""
    path_vin = tk.filedialog.askopenfilename(
        # doc in http://effbot.org/tkinterbook/tkinter-file-dialogs.htm
        title = 'Choose v.in file',
        filetypes = [('model input file', '*.in'), ('any type', '*.*')],
        initialfile = 'v.in'
        )
    return path_vin


class VmodelEditor(tk.Frame):
    """vin-editor GUI
    tkinter document: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/index.html"""
    def __init__(self, master=None):
        super(VmodelEditor, self).__init__(master)
        self.master.title('v.in editor')
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
        """Open a new v.in file and load it into a new created PloterWindow object"""
        path_vin = self.path_vin_input.get()
        if not path_vin.strip():
            tk.messagebox.showerror(
                'Error', 'Please input full path of a v.in file, or select '
                'a v.in file')
            return
        plot_window = PloterWindow()
        plot_window.bind_ploter(path_vin)
        plot_window.show()


class PloterWindow(object):
    """The container of the ploter object.
    To handle things higher than plotting, such as showing message to user,
    setting plot parameters etc."""
    def __init__(self):
        super(PloterWindow, self).__init__()
        # Use gridspec to deal with layout.
        # The left part contains the axes for plotting model.
        self.fig = plt.figure(figsize=(10,6))
        self.fig.subplots_adjust(top=0.96, bottom=0.075)
        self.plot_grid = gridspec.GridSpec(1, 1)
        self.plot_grid.update(left=0.06, right=0.715)
        self.plot_ax = plt.subplot(self.plot_grid[0, 0])
        # The right part contains some widgets for user interactivity.
        self.widget_grid = gridspec.GridSpec(15, 12)
        self.widget_grid.update(left=0.75, right=0.95, hspace=0.5, wspace=0.3)
        self.ploter = None
        self.slider_vals = None
        self.dont_show_save_dialog = False
        self.init_keymap()
        self.init_widgets()

    def bind_ploter(self, path_vin):
        """bind a ploter object"""
        self.ploter = VmodelPloter(parent=self, path_vin=path_vin)

    def show(self):
        self.ploter.plot()
        plt.show()

    def init_keymap(self):
        """Disable some default hot keys to avoid conflicts
        matplotlib keymap doc: https://matplotlib.org/users/customizing.html#matplotlibrc-sample"""
        try:
            plt.rcParams['keymap.home'].remove('home')
            plt.rcParams['keymap.back'].remove('left')
            plt.rcParams['keymap.back'].remove('c')
            plt.rcParams['keymap.forward'].remove('right')
            plt.rcParams['keymap.pan'].remove('p')
            plt.rcParams['keymap.save'].remove('ctrl+s')
            plt.rcParams['keymap.xscale'].remove('k')
            plt.rcParams['keymap.yscale'].remove('l')
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

        self.slider1 = Slider(ax1, 'dx_sm', 0, 0.1, 0.01, '%.2f')
        self.slider2 = Slider(ax2, 'dx_lg', 0, 1.0, 0.1, '%.2f')
        self.slider3 = Slider(ax3, 'dy_sm', 0, 0.01, 0.001, '%.3f')
        self.slider4 = Slider(ax4, 'dy_lg', 0, 0.1, 0.01, '%.3f')
        self.slider5 = Slider(ax5, 'pick_size', 0, 3, 0.15, '%.2f')
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

        # Bind callback functions
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

    @property
    def dx_sm(self):
        return self.slider_vals[0]
    @property
    def dx_lg(self):
        return self.slider_vals[1]
    @property
    def dy_sm(self):
        return self.slider_vals[2]
    @property
    def dy_lg(self):
        return self.slider_vals[3]
    @property
    def pick_tolerence(self):
        return self.slider_vals[4]

    # event handlers

    def handle_exit_btn(self, event):
        if self.ploter.is_modified() and not self.close_window_dialog():
            return
        self._close_by_exit_btn = True
        plt.close(self.fig)

    def handle_close(self, event):
        """Closing ploter window directly is not recommended. Instead, we
        recommend using Exit Button."""
        if self._close_by_exit_btn:
            return
        self.show_warning(
            'Please don\'t close the window directly, or your work may get lost.'
            '\nPlease always use the EXIT BUTTON for exiting.')
        if self.ploter.is_modified():
            import datetime as dt
            import os
            quick_save_name = 'quick_save_%s_v.in' %(dt.datetime.now().strftime(
                '%Y%m%d%H%M%S'))
            full_path = os.path.join(os.path.split(self.ploter.path_vin)[0],
                quick_save_name)
            self.ploter.save_as(full_path)
            self.show_warning(
                'Unsaved modification was detected.\nHave saved the model to '
                'file: "%s" under the same directory as currently editing '
                'v.in file' %quick_save_name)

    def handle_slider_changed(self, idx):
        """Callback functions for the sliders."""
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
        self.save()

    def handle_saveas_btn(self, event):
        self.save_as()

    def slider_changed(self, val, i):
        """Callback functions for the i-th slider changing."""
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
        """Reset the sliders"""
        for sld in self.sliders:
            sld.reset()
        self.slider_vals = [sld.val for sld in self.sliders]

    def open_vin(self):
        """Open a new v.in file"""
        self.ploter.prompt_open()

    def reload_vin(self):
        """Reload current v.in file"""
        self.ploter.prompt_reload()

    def save(self):
        """Save the modified model back into the current v.in file."""
        self.ploter.prompt_save()

    def save_as(self):
        """Save current model as ..."""
        self.ploter.prompt_save_as()

    def show_help(self, msg=None):
        global help_msg
        msg = msg if msg else help_msg
        # tk.messagebox.askokcancel('Help', msg)
        print(help_msg)
        tk.messagebox.askokcancel('Help', 'Please read help message in console.')

    def show_info(self, msg):
        tk.messagebox.showinfo('Info', msg)

    def show_warning(self, msg):
        tk.messagebox.showwarning('Warning', msg)

    def show_error(self, msg):
        tk.messagebox.showerror('Error', msg)

    def close_window_dialog(self):
        """Dialog when closing window."""
        return tk.messagebox.askokcancel(
            'Info', 'Are you sure to exit?\nThe unsaved modification will be lost!')

    def open_dialog(self):
        """Dialog when opening new v.in file"""
        return tk.messagebox.askokcancel(
            'Info', 'Are you sure to open a new v.in file?\nThe unsaved '
            'modification will be lost!')

    def select_vin_dialog(self):
        """Dialog to select a v.in file"""
        global select_vin_dialog
        return select_vin_dialog()

    def reload_dialog(self):
        """Dialog when reloading current v.in file"""
        return tk.messagebox.askokcancel(
            'Info', 'Are you sure to reload current v.in file?\nThis will '
            'erase all the unsaved modification.')

    def save_dialog(self):
        """Dialog when saving modified model back into current v.in file"""
        if self.dont_show_save_dialog:
            return True
        res = tk.messagebox.askyesnocancel(
            'Info', 'Are you sure to save modified model back into current '
            'v.in file?\nThis will rewrite current v.in file.\nClick "Cancel" '
            'to disable this dialog for current session.')
        if res is None:
            self.dont_show_save_dialog = True
            return False
        return res

    def save_as_dialog(self):
        """Dialog when saveing current model as ..."""
        save_path = tk.filedialog.asksaveasfilename(
            title = 'Save As',
            filetypes = [('model input file', '*.in'), ('any type', '*.*')],
            initialfile = 'v.in'
            )
        if not save_path.strip():
            return None
        return save_path
