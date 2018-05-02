import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import os
import tkinter as tk
from tkinter import ttk
import traceback

from definitions import ROOT_DIR
from ploter import VPloter
from util import get_file_logger


class VelocityFrame(ttk.Frame):
    """Velocity frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'velocity_window.log'),
            level = 'debug')
        self.model = None
        self.create_widgets()

    def create_widgets(self):
        # Set master window properties
        self.master.title('v.in editor - Velocity Plot')
        self.master.geometry('1000x600+220+50')
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Make frame resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # Create a Notebook widget to contain several panels
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky='nswe')
        self.vcf = VelocityContourFrame(self)
        notebook.add(self.vcf, text=' Velocity Contour ', sticky='nswe')

    def bind_model(self, model):
        self.model = model
        self.vcf.bind_model(self.model)


class VelocityContourFrame(ttk.Frame):
    """Velocity contour frame"""
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.logger = self.master.logger
        self.init_variables()
        self.create_widgets()
        self.canvas.draw()

    def init_variables(self):
        self.fig = plt.figure(tight_layout=True)
        self.fig.patch.set_facecolor('#F0F0F0')
        self.ax = self.fig.add_subplot(111)
        self.ax.tick_params(axis='both', which='major', labelsize=9)
        self.ax.tick_params(axis='both', which='minor', labelsize=8)

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
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_area)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nswe')
        self.canvas._tkcanvas.grid(sticky='nswe')
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

    def bind_model(self, model):
        self.ploter = VPloter(self, model)
        self.ploter.plot_velocity_contour()
