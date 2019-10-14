import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

from definitions import ROOT_DIR
from globals_ import session, history
from model import ModelProcessor
from ploter import VContourPlotDelegator, VSectionPlotDelegator
from util import get_file_logger, parse_pois_str


class VelocityFrame(ttk.Frame):
    """Velocity frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'velocity_window.log'),
            level = 'debug')
        self.model_proc = None
        self.has_vcf_init = False
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
        self.model_proc = ModelProcessor(model)
        pois_str = session.get('pois')
        if pois_str:
            pois_obj = parse_pois_str(pois_str)
            self.model_proc.bind_pois(pois_obj)
        self.vsf.bind_model(self.model_proc)

    def tab_changed(self, event):
        if event.widget.index(event.widget.select()) == 1 \
                and (not self.has_vcf_init):
            self.vcf.bind_model(self.model_proc)
            self.has_vcf_init = True

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
                pois_obj = parse_pois_str(pois_str)
                self.model_proc.bind_pois(pois_obj)
            else:
                self.model_proc.unbind_pois()
            self.vsf.start_plot()

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
                    pois_obj = parse_pois_str(pois_str)
                except ValueError as e:
                    messagebox.showerror('Error', '\n'.join([str(x) for x in e.args]), parent=self.master)
                    return
            session.set('pois', pois_str)
            history.merge_session(session)

        self.master.settings_work(flag_pois=flag_pois)


class VelocityContourFrame(ttk.Frame):
    """Velocity contour frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = self.master.logger
        self.init_variables()
        self.create_widgets()

    def init_variables(self):
        self.fig = plt.figure(tight_layout=True)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.ploter = VContourPlotDelegator(delegate=self, allowed_attrs=(
            'model_proc', 'fig'))

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
        side_area = ttk.Frame(self)
        side_area.rowconfigure(2, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, rowspan=2, padx=(0, 15), pady=(0, 15), sticky='nswe')

    def bind_model(self, model_proc):
        """`model_proc` is a `ModelProcessor` object, which contains attribute `model`
        and some methods to process model"""
        self.model_proc = model_proc
        self.ploter.plot_velocity_contour()
        self.fig.canvas.draw()


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
        self.section_x_str = tk.StringVar()
        self.ploter = VSectionPlotDelegator(delegate=self, allowed_attrs=(
            'model_proc', 'fig', 'axs'))

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
        side_area.grid(row=0, column=1, rowspan=2, padx=(0, 15), pady=15, sticky='nswe')

        # Choose whether the model contains water layer
        temp = ttk.Frame(side_area)
        temp.columnconfigure(0, weight=1)
        temp.grid(column=0, sticky='nswe')
        ttk.Label(temp, text='Has water layer?').grid(column=0, sticky='nsw')
        ttk.Radiobutton(temp, text='Yes', value=True, variable=self.has_water_layer, command=self.apply_mbsf)\
            .grid(column=0, sticky='nsw')
        ttk.Radiobutton(temp, text='No', value=False, variable=self.has_water_layer, command=self.apply_mbsf)\
            .grid(column=0, sticky='nsw')

        # Set section position
        temp = ttk.Frame(side_area)
        temp.columnconfigure(0, weight=1)
        temp.grid(column=0, pady=(10, 0), sticky='nswe')
        ttk.Label(temp, text='Section position').grid(column=0, sticky='nsw')
        ent = ttk.Entry(temp, width=10, textvariable=self.section_x_str)
        ent.grid(column=0, sticky='nsw')
        ent.bind('<Return>', self.section_x_changed)

        # Set poission ratio
        ttk.Button(side_area, text='Set pois', command=self.master.goto_settings)\
            .grid(column=0, pady=(15, 0), sticky='nswe')

    def bind_model(self, model_proc):
        self.model_proc = model_proc
        self.section_x_str.set(str(sum(self.model_proc.model.xlim)/2.0))
        self.start_plot()
        self.fig.canvas.draw()

    def start_plot(self):
        section_x = float(self.section_x_str.get())
        self.ploter.plot_sections(section_x)
        self.apply_mbsf()

    def section_x_changed(self, event=None):
        xlim = self.model_proc.model.xlim
        try:
            section_x = float(self.section_x_str.get())
        except Exception:
            messagebox.showerror(
                'Error', 'Invalid section position \n%r' %(self.section_x_str.get()),
                parent=self.master)
            return
        section_x = min(max(section_x, xlim[0]), xlim[1])
        self.section_x_str.set(str(section_x))
        self.ploter.plot_sections(section_x)
        self.apply_mbsf()

    def apply_mbsf(self):
        """Use meters-below-sea-floor(mbsf) as y axis, rather than depth."""
        idx = 1 if self.has_water_layer.get() else 0
        self.ploter.flatten_by_layer(idx)

