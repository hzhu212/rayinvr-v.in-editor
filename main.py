import logging
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import traceback


class MainWindow(tk.Tk):
    """Main window"""
    def __init__(self):
        super().__init__()
        self.logger = self._get_logger()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.fig = plt.figure()
        self.ax = self.fig.add_subplot(111)
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

    def create_widgets(self):
        # make root window resizable
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

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
        toolbar_area = ttk.Frame(plot_area)
        toolbar_area.grid(row=1, column=0, sticky='nswe')
        toolbar = NavigationToolbar2TkAgg(self.canvas, toolbar_area)
        toolbar.update()

        # side frame for controlling widgets
        # side_area = ttk.Frame(self, borderwidth=2, relief=tk.GROOVE)
        side_area = ttk.Frame(self)
        side_area.rowconfigure(0, weight=1)
        side_area.columnconfigure(0, weight=1)
        side_area.grid(row=0, column=1, sticky='nswe')

        ttk.Button(side_area, text='Test', command=self.test).grid()

    def plot(self):
        x = np.linspace(0, 2*np.pi, 100)
        y = np.sin(x)
        self.ax.plot(x, y)

    def test(self):
        raise ValueError('hhh')

    def close(self):
        self.quit()
        self.destroy()

    def report_callback_exception(self, exc, val, tb):
        self.logger.exception(val)
        err_msg = traceback.format_exception(exc, val, tb)
        err_msg = ''.join(err_msg)
        messagebox.showerror('Internal Error', err_msg)



if __name__ == '__main__':
    window = MainWindow()
    window.wm_title('v.in editor')
    window.geometry('800x600+200+30')
    window.mainloop()
