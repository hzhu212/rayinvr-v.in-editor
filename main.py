import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import os
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
import traceback

from definitions import ROOT_DIR
from globals_ import session, history
from ploter import ModelPloter
from util import ScrollText, get_file_logger
from velocity import VelocityFrame


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


class MainFrame(ttk.Frame):
    """Main frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'main_window.log'),
            level = 'debug')
        self.init_variables()
        self.create_widgets()
        self.bind_events()
        self.canvas.draw()

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
        # Set master window properties
        self.master.wm_title('v.in editor')
        self.master.geometry('1000x600+200+30')
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.master.protocol("WM_DELETE_WINDOW", self.exit)

        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        # Create menu
        self.create_menu()

        # Frame for plotting
        plot_area = ttk.Frame(self)
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)
        plot_area.grid(row=0, column=0, sticky='nswe')

        # Create matplotlib canvas for plotting
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        self.canvas._tkcanvas.grid(sticky='nswe')
        self.ploter = ModelPloter(MainFrameProxy(self))
        # toolbar uses pack geometry manager internally, so wrap it with a frame
        # using grid geometry manager.
        toolbar_area = ttk.Frame(self)
        toolbar_area.grid(row=1, column=0, sticky='nswe')
        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_area)
        toolbar.update()

        # Side frame for controlling widgets
        side_area = ttk.Frame(self)
        side_area.rowconfigure(2, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, rowspan=2, padx=(0, 15), pady=(0, 15), sticky='nswe')

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
        ttk.Button(btn_area, text='Show Velocity', command=self.show_velocity)\
            .grid(row=2, column=0, columnspan=2, sticky='nswe')

        # echo message
        msg_area = self.gen_container(side_area, row_weight={1:1}, col_weight=1)
        msg_area.grid(column=0, pady=(10, 0), sticky='nswe')
        ttk.Label(msg_area, text='Selected nodes: ')\
            .grid(row=0, column=0, sticky='nsw')
        self.echo = ScrollText(msg_area, width=30, bd=0, font=('Consolas', 8), state=tk.DISABLED)
        self.echo.grid(row=1, column=0, sticky='nswe')

    def create_menu(self):
        menubar = tk.Menu(self)
        self.master.config(menu=menubar)

        self.filemenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='File', menu=self.filemenu)
        self.filemenu.add_command(label='Open', command=self.open)
        self.recentmenu = self.create_recent_opens_menu()
        self.filemenu.add_command(label='Save', command=self.save)
        self.filemenu.add_command(label='Save As', command=self.save_as)
        self.filemenu.add_separator()
        self.filemenu.add_command(label='Exit', command=self.exit)

        editmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Edit', menu=editmenu)
        editmenu.add_command(label='Undo', command=self.not_implement)
        editmenu.add_command(label='Redo', command=self.not_implement)

        helpmenu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label='Help', menu=helpmenu)
        helpmenu.add_command(label='Help', command=self.show_help)
        helpmenu.add_command(label='About', command=self.show_about)

    def create_recent_opens_menu(self):
        def clear_recent_opens():
            history.clear()
            self.update_recent_opens_menu()

        recentmenu = tk.Menu(self.filemenu, tearoff=0)
        self.filemenu.add_cascade(label='Open Recent', menu=recentmenu)
        recentmenu.add_command(label='Clear Items', command=clear_recent_opens)
        recentmenu.add_separator()
        for file_path in history.get('recent_opens')[:10]:
            def closure(file_path):
                recentmenu.add_command(
                    label=file_path, command=lambda: self.open(file_path))
            closure(file_path)
        return recentmenu

    def update_recent_opens_menu(self):
        self.recentmenu.delete(2, tk.END)
        for file_path in history.get('recent_opens')[1:10]:
            def closure(file_path):
                self.recentmenu.add_command(
                    label=file_path, command=lambda: self.open(file_path))
            closure(file_path)

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
        self.master.bind('<KeyPress>', self.on_key_press)
        self.master.bind('<KeyRelease>', self.on_key_release)

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

    def set_title(self, text=None):
        if not text:
            return
        self.master.title(self.master.title() + ' - ' + text)

    def reset_sliders(self):
        for name, value in zip(self.slider_names, self.slider_init_values):
            self.settings[name].set(value)

    def not_implement(self):
        messagebox.showinfo('Info', 'Not yet implemented')

    def show_velocity(self):
        if self.ploter.model is None:
            return
        vf = VelocityFrame(tk.Toplevel())
        vf.grid(sticky='nswe')
        vf.bind_model(self.ploter.model.copy())

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

    def open(self, file_path=None):
        """Open v.in file"""
        if file_path is None:
            if self.ploter.is_modified():
                okay = messagebox.askokcancel(
                    'Warning', 'Do you want to open a new v.in file?\n'
                    'Current modification will be lost!')
                if not okay:
                    return
            initialdir = os.path.join(ROOT_DIR, 'vins')
            recent_opens = history.get('recent_opens')
            if recent_opens:
                initialdir = os.path.dirname(recent_opens[0])
            file_path = filedialog.askopenfilename(
                defaultextension='.in',
                filetypes=[('rayinvr input file', '.in'), ('any type', '.*')],
                initialdir=initialdir,
                parent=self,
                title='Open v.in')
            file_path = file_path.strip()
            if not file_path:
                return
        self.vin_path = os.path.normpath(file_path)
        self.logger.debug('Opening file %r' %self.vin_path)
        self.set_title(self.vin_path)
        self.ploter.open()
        # Handle session and history
        if self.vin_path in history.get('recent_opens'):
            session.update(history.get_session_data(self.vin_path))
        else:
            session.clear()
            session.set('file', self.vin_path)
        history.merge_session(session)
        self.update_recent_opens_menu()

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
        self.master.quit()
        self.master.destroy()

    def report_callback_exception(self, etype, evalue, tb):
        self.logger.exception(evalue)
        err_msg = traceback.format_exception(etype, evalue, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)


class HelpFrame(ttk.Frame):
    """Help Window"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        self.master.title('v.in editor - Help')
        self.master.geometry('660x700+300+30')
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid(padx=20, pady=10, sticky='nswe')
        text = tk.Text(self, bd=0, bg='#F0F0F0', font=('Consolas', 11))
        text.grid(row=0, column=0, sticky='nswe')
        text.insert(tk.END, help_msg)
        text.config(state=tk.DISABLED)

class AboutFrame(ttk.Frame):
    """About Window"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.create_widgets()

    def create_widgets(self):
        self.master.title('v.in editor - About')
        self.master.geometry('320x100+500+200')
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.grid(padx=20, pady=10, sticky='nswe')
        text = tk.Text(self, bd=0, bg='#F0F0F0', font=('Consolas', 11))
        text.grid(row=0, column=0, sticky='nswe')
        text.insert(tk.END, 'v.in editor by <zhuhe212@163.com>')
        text.config(state=tk.DISABLED)


class MainFrameProxy(object):
    """Proxying MainFrame Class"""
    def __init__(self, window):
        self.window = window
        self.tk_variables = ('dx_sm', 'dx_lg', 'dy_sm', 'dy_lg', 'pick')
        self.allowed_attrs = ('fig', 'ax', 'canvas', 'vin_path', 'echo')

    def __getattr__(self, name):
        if name in self.tk_variables:
            return self.window.settings[name].get()
        if name in self.allowed_attrs:
            return getattr(self.window, name)
        raise AttributeError('Attribute "%s" is not allowed by %s' %(name, type(self).__name__))

    def bind(self, *args, **kw):
        return self.window.bind(*args, **kw)

    def show_info(self, *args, **kw):
        return self.window.show_info(*args, **kw)

    def show_warning(self, *args, **kw):
        return self.window.show_warning(*args, **kw)

    def show_error(self, *args, **kw):
        return self.window.show_error(*args, **kw)



if __name__ == '__main__':
    root = tk.Tk()
    mf = MainFrame(root)
    mf.grid(row=0, column=0, sticky='nswe')
    root.report_callback_exception = mf.report_callback_exception
    root.mainloop()
