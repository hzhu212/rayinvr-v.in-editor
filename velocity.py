import os
import runpy
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import numpy as np

from globals_ import session, history
from model import ModelManager
from ploter import VContourPlotDelegator, VSectionPlotDelegator
import util


cur_dir = os.path.dirname(os.path.abspath(__file__))


class VelocityFrame(ttk.Frame):
    """Velocity frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = util.get_file_logger(
            name = type(self).__name__,
            file = os.path.join(cur_dir, 'log', 'velocity_window.log'),
            level = 'debug')
        self.model_manager = None
        self.last_tab_id = None
        self.create_widgets()

    def create_widgets(self):
        # Set master window properties
        self.master.title('v.in editor - Velocity Plotting')
        self.master.geometry('1000x600+220+50')
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Create a Notebook widget to contain several panels
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky='nswe')
        self.vsf = VelocitySectionFrame(self)
        self.vcf = VelocityContourFrame(self)
        self.st = SettingsFrame(self)
        self.notebook.add(self.vsf, text=' Sections ', sticky='nswe')
        self.notebook.add(self.vcf, text=' Contours ', sticky='nswe')
        self.notebook.add(self.st, text=' Settings ', sticky='nswe')
        self.notebook.bind('<<NotebookTabChanged>>', self.tab_changed)

    def bind_model(self, model):
        self.model_manager = ModelManager(model)
        pois_str = session.get('pois')
        if pois_str:
            pois_obj = util.parse_pois_str(pois_str)
            self.model_manager.bind_pois(pois_obj)
        self.vsf.bind_model(self.model_manager)
        self.vcf.bind_model(self.model_manager)

    def tab_changed(self, event):
        if event.widget.index(event.widget.select()) == 1:
            pass

    def goto_settings(self):
        self.last_tab_id = self.notebook.select()
        self.notebook.select(2)

    def settings_work(self, flag_pois=False):
        """A flag will be set as True when related settings is changed"""
        if self.last_tab_id is not None:
            self.notebook.select(self.last_tab_id)
            self.last_tab_id = None
        if flag_pois:
            pois_str = session.get('pois')
            if pois_str is not '':
                pois_obj = util.parse_pois_str(pois_str)
                self.model_manager.bind_pois(pois_obj)
                self.vsf.pois_set()
                self.vcf.pois_set()
            else:
                self.model_manager.unbind_pois()
                self.vsf.pois_unset()
                self.vcf.pois_unset()


class SettingsFrame(ttk.Frame):
    """Some settings like poission ratio etc."""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = self.master.logger
        self.create_widgets()

    def create_widgets(self):
        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        main_area = ttk.Frame(self)
        main_area.rowconfigure(0, weight=1)
        main_area.columnconfigure(0, weight=1)
        main_area.grid(padx=20, pady=20, sticky='nswe')

        # Frame for setting poission ratio
        pois_area = ttk.Frame(main_area)
        pois_area.grid(column=0, sticky='nswe')
        ttk.Label(pois_area, text='Set poission ratio (copy from r.in): ')\
            .grid(column=0, sticky='nsw')
        text = tk.Text(pois_area, height=5, font=('Consolas', 11))
        text.grid(column=0, pady=(5, 0), sticky='nswe')
        text.insert(tk.END, session.get('pois'))
        self.pois_text = text

        # Controlling buttons
        btn_area = ttk.Frame(main_area)
        btn_area.grid(column=0, sticky='nswe')
        ttk.Button(btn_area, text='OK', command=self.handle_ok).grid(sticky='nse')

    def handle_ok(self):
        flag_pois = False
        pois_str = self.pois_text.get('1.0', tk.END).strip()
        if pois_str != session.get('pois'):
            flag_pois = True
            if pois_str is not '':
                try:
                    pois_obj = util.parse_pois_str(pois_str)
                except ValueError as e:
                    messagebox.showerror('Error', '\n'.join([str(x) for x in e.args]), parent=self.master)
                    return
            session.set('pois', pois_str)
            history.merge_session(session)

        self.master.settings_work(flag_pois=flag_pois)


class VelocityContourFrame(ttk.Frame):
    """Velocity contour frame"""
    NXGRID, NYGRID = 500, 500

    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = self.master.logger
        self.init_variables()
        self.create_widgets()

    def init_variables(self):
        self.fig = plt.figure(tight_layout=True)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.plot_type_tkvar = tk.IntVar(value=0)
        self.ignore_sea_water_tkvar = tk.BooleanVar(value=True)
        self.xmin_tkvar = tk.DoubleVar()
        self.xmax_tkvar = tk.DoubleVar()
        self.ymin_tkvar = tk.DoubleVar()
        self.ymax_tkvar = tk.DoubleVar()
        self.xstep_tkvar = tk.DoubleVar()
        self.ystep_tkvar = tk.DoubleVar()
        self.script_path_tkvar = tk.StringVar()
        self.ploter = VContourPlotDelegator(delegate=self, allowed_attrs=(
            'model_manager', 'fig'))

    def create_widgets(self):
        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Frame for plotting
        plot_area = ttk.Frame(self)
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)
        plot_area.grid(row=0, column=0, sticky='nswe')

        # Create matplotlib canvas for plotting
        canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        canvas._tkcanvas.grid(sticky='nswe')
        # toolbar uses pack geometry manager internally, so wrap it with a frame
        # using grid geometry manager.
        toolbar_area = ttk.Frame(self)
        toolbar_area.grid(row=1, column=0, sticky='nswe')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_area)
        toolbar.update()

        # Side frame for controlling widgets
        side_area = ttk.LabelFrame(self, text='Options')
        # side_area.rowconfigure(0, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, rowspan=2, padx=(0, 15), pady=(0, 15), sticky='nswe')

        # Choose Vp, Vs or Pois Ratio
        tmp = ttk.Frame(side_area)
        tmp.grid(column=0, sticky='nswe', pady=0)
        ttk.Label(tmp, text='Plot Type: ').grid(row=0, column=0, columnspan=3, sticky='nswe')
        self.plot_type_radios = [
            ttk.Radiobutton(tmp, text='Vp', value=0, variable=self.plot_type_tkvar),
            ttk.Radiobutton(tmp, text='Vs', value=1, variable=self.plot_type_tkvar),
            ttk.Radiobutton(tmp, text='Pois', value=2, variable=self.plot_type_tkvar),
            ]
        self.plot_type_radios[0].grid(row=1, column=0, sticky='nsw')
        self.plot_type_radios[1].grid(row=1, column=1, sticky='nsw')
        self.plot_type_radios[2].grid(row=1, column=2, sticky='nsw')

        # whether to ignore sea water
        tmp = ttk.Frame(side_area)
        tmp.grid(column=0, sticky='nswe', pady=(10, 0))
        ttk.Label(tmp, text='Ignore Sea Water?').grid(row=0, column=0, columnspan=2, sticky='nswe')
        ttk.Radiobutton(tmp, text='Yes', value=True, variable=self.ignore_sea_water_tkvar).grid(row=1, column=0, sticky='nsw')
        ttk.Radiobutton(tmp, text='No', value=False, variable=self.ignore_sea_water_tkvar).grid(row=1, column=1, sticky='nsw')

        # plot params
        tmp = ttk.Frame(side_area)
        tmp.columnconfigure(1, weight=1)
        tmp.grid(column=0, sticky='nswe', pady=(10, 0))
        ttk.Label(tmp, text='Plot Parameters: ').grid(column=0, sticky='nswe')
        # set xlim and ylim
        util.create_label_entry(tmp, 'xmin: ', self.xmin_tkvar, self.xmin_changed, label_width=6)
        util.create_label_entry(tmp, 'xmax: ', self.xmax_tkvar, self.xmax_changed, label_width=6)
        util.create_label_entry(tmp, 'ymin: ', self.ymin_tkvar, self.ymin_changed, label_width=6)
        util.create_label_entry(tmp, 'ymax: ', self.ymax_tkvar, self.ymax_changed, label_width=6)
        # set xstep and ystep for meshing
        util.create_label_entry(tmp, 'xstep: ', self.xstep_tkvar, self.xstep_changed, label_width=6)
        util.create_label_entry(tmp, 'ystep: ', self.ystep_tkvar, self.ystep_changed, label_width=6)
        # use current viewport to set parameters
        ttk.Button(tmp, text='Use Viewport', command=self.use_viewport).grid(column=0, pady=5, sticky='nw')

        # plot button
        ttk.Button(side_area, text='Plot', command=self.update_plot).grid(column=0, pady=(10, 0), sticky='nw')

        # load script to fix figure
        ttk.Separator(side_area, orient=tk.HORIZONTAL).grid(column=0, pady=(20, 0), sticky='ew')
        tmp = ttk.Frame(side_area)
        tmp.columnconfigure(0, weight=1)
        tmp.grid(column=0, sticky='swe', pady=(5, 0))
        ttk.Label(tmp, text='Fix figure using scirpt: ').grid(row=0, column=0, columnspan=2, pady=(0, 5), sticky='nsw')
        ttk.Entry(tmp, textvariable=self.script_path_tkvar).grid(row=1, column=0, sticky='nswe')
        ttk.Button(tmp, text='...', width=3, command=self.select_script).grid(row=1, column=1, sticky='nse')
        # fix button
        ttk.Button(tmp, text='Fix', command=self.fix_plot).grid(column=0, pady=(10, 0), sticky='nw')


    def bind_model(self, model_manager):
        """`model_manager` is a `ModelManager` object, which contains attribute `model`
        and some methods to process model"""
        self.model_manager = model_manager

        # set default values for plot parameters
        xmin, xmax = self.model_manager.model.xlim
        ymin, ymax = self.model_manager.model.ylim
        xstep, ystep = (xmax - xmin) / self.NXGRID, (ymax - ymin) / self.NYGRID
        self.xmin_tkvar.set(xmin)
        self.xmax_tkvar.set(xmax)
        self.ymin_tkvar.set(ymin)
        self.ymax_tkvar.set(ymax)
        self.xstep_tkvar.set(xstep)
        self.ystep_tkvar.set(ystep)


    def pois_set(self):
        self.plot_type_radios[1].configure(state=tk.NORMAL)
        self.plot_type_radios[2].configure(state=tk.NORMAL)

    def pois_unset(self):
        self.plot_type_radios[1].configure(state=tk.DISABLED)
        self.plot_type_radios[2].configure(state=tk.DISABLED)
        self.plot_type_tkvar.set(0)

    def update_plot(self):
        """update contour plot according to user setting parameters"""
        xmin = self.xmin_tkvar.get()
        xmax = self.xmax_tkvar.get()
        ymin = self.ymin_tkvar.get()
        ymax = self.ymax_tkvar.get()
        xstep = self.xstep_tkvar.get()
        ystep = self.ystep_tkvar.get()
        xlim = (xmin, xmax)
        ylim = (ymin, ymax)
        nxgrid = int(round((xmax - xmin) / xstep))
        nygrid = int(round((ymax - ymin) / ystep))
        ignore_sea_water = self.ignore_sea_water_tkvar.get()
        self.ploter.plot_velocity_contour(self.plot_type_tkvar.get(), xlim, ylim, nxgrid, nygrid, ignore_sea_water)
        self.fig.canvas.draw()

    def use_viewport(self):
        xlim, ylim = self.ploter.get_viewport()
        if not xlim:
            return
        xmin, xmax = xlim
        ymin, ymax = ylim
        xstep, ystep = (xmax - xmin) / self.NXGRID, (ymax - ymin) / self.NYGRID
        self.xmin_tkvar.set(round(xmin, 10))
        self.xmax_tkvar.set(round(xmax, 10))
        self.ymin_tkvar.set(round(ymin, 10))
        self.ymax_tkvar.set(round(ymax, 10))
        self.xstep_tkvar.set(round(xstep, 10))
        self.ystep_tkvar.set(round(ystep, 10))

    def xmin_changed(self, event=None):
        xmin = self.xmin_tkvar.get()
        XMIN, XMAX = self.model_manager.model.xlim
        if xmin < XMIN:
            self.xmin_tkvar.set(str(XMIN))
        elif xmin > XMAX:
            self.xmin_tkvar.set(str(XMAX))

    def xmax_changed(self, event=None):
        xmax = self.xmax_tkvar.get()
        XMIN, XMAX = self.model_manager.model.xlim
        if xmax < XMIN:
            self.xmax_tkvar.set(str(XMIN))
        elif xmax > XMAX:
            self.xmax_tkvar.set(str(XMAX))

    def ymin_changed(self, event=None):
        ymin = self.ymin_tkvar.get()
        YMIN, YMAX = self.model_manager.model.ylim
        if ymin < YMIN:
            self.ymin_tkvar.set(str(YMIN))
        elif ymin > YMAX:
            self.ymin_tkvar.set(str(YMAX))

    def ymax_changed(self, event=None):
        ymax = self.ymax_tkvar.get()
        YMIN, YMAX = self.model_manager.model.ylim
        if ymax < YMIN:
            self.ymax_tkvar.set(str(YMIN))
        elif ymax > YMAX:
            self.ymax_tkvar.set(str(YMAX))

    def xstep_changed(self, event=None):
        xstep = self.xstep_tkvar.get()
        if xstep < 0:
            self.xstep_tkvar.set(-xstep)

    def ystep_changed(self, event=None):
        ystep = self.ystep_tkvar.get()
        if ystep < 0:
            self.ystep_tkvar.set(-ystep)

    def select_script(self):
        """select python script to fix figure"""
        p = filedialog.askopenfilename(
            defaultextension='.py',
            filetypes=[('python script', '.py'), ('any type', '.*')],
            initialdir='.',
            parent=self,
            title='Select Python script to fix current figure')
        p = p.strip()
        if not p:
            return
        self.script_path_tkvar.set(os.path.normpath(p))

    def fix_plot(self):
        script_path = self.script_path_tkvar.get()
        if not os.path.isfile(script_path):
            messagebox.showerror('Error', 'Invalid scirpt path', parent=self.master)
            return
        context = locals()
        context.update(globals())
        context.update(dict(fig=self.ploter.fig))
        runpy.run_path(script_path, init_globals=context)
        self.ploter.fig.canvas.draw()


class VelocitySectionFrame(ttk.Frame):
    """Velocity section frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = self.master.logger
        self.init_variables()
        self.create_widgets()

    def init_variables(self):
        self.fig, self.axs = plt.subplots(1, 3, sharey=True, tight_layout=True)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.has_water_layer = tk.BooleanVar()
        self.section_x_tkvar = tk.DoubleVar()
        self.ymin_tkvar = tk.DoubleVar()
        self.ymax_tkvar = tk.DoubleVar()
        self.ploter = VSectionPlotDelegator(delegate=self, allowed_attrs=(
            'model_manager', 'fig', 'axs'))

    def create_widgets(self):
        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Frame for plotting
        plot_area = ttk.Frame(self)
        plot_area.rowconfigure(0, weight=1)
        plot_area.columnconfigure(0, weight=1)
        plot_area.grid(row=0, column=0, sticky='nswe')

        # Create matplotlib canvas for plotting
        canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        canvas._tkcanvas.grid(sticky='nswe')
        # toolbar uses pack geometry manager internally, so wrap it with a frame
        # using grid geometry manager.
        toolbar_area = ttk.Frame(self)
        toolbar_area.grid(row=1, column=0, sticky='nswe')
        toolbar = NavigationToolbar2Tk(canvas, toolbar_area)
        toolbar.update()

        # Side frame for controlling widgets
        side_area = ttk.LabelFrame(self, text='Options')
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, rowspan=2, padx=(0, 15), sticky='nswe')

        # Choose whether the model contains water layer
        tmp = ttk.Frame(side_area)
        tmp.columnconfigure(0, weight=1)
        tmp.grid(column=0, sticky='nswe')
        ttk.Label(tmp, text='Ignore sea water?').grid(column=0, sticky='nsw')
        ttk.Radiobutton(tmp, text='Yes', value=True, variable=self.has_water_layer).grid(column=0, sticky='nsw')
        ttk.Radiobutton(tmp, text='No', value=False, variable=self.has_water_layer).grid(column=0, sticky='nsw')

        # plot params
        tmp = ttk.Frame(side_area)
        tmp.columnconfigure(0, weight=1)
        tmp.grid(column=0, sticky='nswe', pady=(20, 0))
        ttk.Label(tmp, text='Plot Parameters: ').grid(column=0, sticky='nswe')

        util.create_label_entry(tmp, 'Section At: ', self.section_x_tkvar, self.section_x_changed, label_width=10, entry_width=10)
        util.create_label_entry(tmp, 'ymin: ', self.ymin_tkvar, self.section_x_changed, label_width=10, entry_width=10)
        util.create_label_entry(tmp, 'ymax: ', self.ymax_tkvar, self.section_x_changed, label_width=10, entry_width=10)

        # # Set poission ratio
        # ttk.Button(side_area, text='Set pois', command=self.master.goto_settings).grid(column=0, pady=(15, 0), sticky='nswe')
        # plot button
        ttk.Button(side_area, text='Plot', command=self.update_plot).grid(column=0, pady=(15, 0), sticky='nswe')


    def bind_model(self, model_manager):
        self.model_manager = model_manager
        self.section_x_tkvar.set(sum(self.model_manager.model.xlim)/2.0)
        self.update_plot()
        self.fig.canvas.draw()

    def pois_set(self):
        pass

    def pois_unset(self):
        pass

    def update_plot(self):
        section_x = self.section_x_tkvar.get()
        deduct_layer = 1 if self.has_water_layer.get() else None
        ymin, ymax = self.ymin_tkvar.get(), self.ymax_tkvar.get()
        ylim = [ymin, ymax] if (ymin or ymax) else None
        self.ploter.plot_sections(section_x, deduct_layer=deduct_layer, ylim=ylim)

    def section_x_changed(self, event=None):
        xmin, xmax = self.model_manager.model.xlim
        section_x = self.section_x_tkvar.get()
        section_x = np.clip(section_x, xmin, xmax)
        self.section_x_tkvar.set(section_x)
