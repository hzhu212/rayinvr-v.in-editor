import logging
import numpy as np
import os
from scipy.interpolate import griddata
import tkinter as tk

from definitions import ROOT_DIR


LOG_LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


def get_file_logger(name, file, level=logging.INFO):
    if isinstance(level, str) :
        level = LOG_LEVELS.get(level.lower(), logging.INFO)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    file_handler = logging.FileHandler(file, encoding='utf8')
    # file_handler.setLevel(level)
    formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


class ScrollText(tk.Frame):
    """Custom tkinter widget: ScrollText"""
    def __init__(self, master, **kw):
        super().__init__(master)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.text = tk.Text(self, **kw)
        self.text.grid(row=0, column=0, sticky='nswe')
        y_scroll = tk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        y_scroll.grid(row=0, column=1, sticky='ns')
        self.text.config(yscrollcommand=y_scroll.set)

    def get(self):
        return self.text.get('1.0', tk.END)

    def set(self, string):
        self.text.config(state=tk.NORMAL)
        self.text.delete('1.0', tk.END)
        self.text.insert(tk.END, string)
        self.text.config(state=tk.DISABLED)


class Delegator(object):
    """Delegator Base Class"""
    def __init__(self, delegate=None):
        self.delegate = delegate
        # Cache is used to only remove added attributes when changing the delegate.
        self.__cache = set()

    def __getattr__(self, name):
        attr = getattr(self.delegate, name)
        setattr(self, name, attr)
        self.__cache.add(name)
        return attr

    def resetcache(self):
        """Removes added attributes while leaving original attributes."""
        for key in self.__cache:
            try:
                delattr(self, key)
            except AttributeError:
                pass
        self.__cache.clear()

    def setdelegate(self, delegate):
        """Reset attributes and change delegate."""
        self.resetcache()
        self.delegate = delegate


class ModelVelocityInterpDelegator(Delegator):
    """Interpolate Model Velocity for Contouring"""
    def __init__(self, delegate):
        super().__init__(delegate)
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'util.log'),
            level = 'debug')

    def fill_velocity(self):
        """fill velocity for all nodes, includeing depth nodes, velocity nodes
        and derived nodes"""
        x_acc, y_acc, v_acc = [], [], []
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bottom = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bottom = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bottom = ly_cur.v_top.x, ly_cur.v_bottom.x
            v_top, v_bottom = ly_cur.v_top.y, ly_cur.v_bottom.y

            x_all = sorted(list(set(np.hstack([x_top, x_bottom, x_v_top, x_v_bottom]))))
            y_top_all = np.interp(x_all, x_top, y_top)
            y_bottom_all = np.interp(x_all, x_bottom, y_bottom)
            v_top_all = np.interp(x_all, x_v_top, v_top)
            v_bottom_all = np.interp(x_all, x_v_bottom, v_bottom)

            x_acc.extend([x_all, x_all])
            y_acc.extend([y_top_all, y_bottom_all-0.0001])
            v_acc.extend([v_top_all, v_bottom_all])

        x, y, v = np.hstack(x_acc), np.hstack(y_acc), np.hstack(v_acc)
        return x, y, v

    def get_grid_data(self, nxgrid=200, nygrid=1000):
        """gridding irregularly spaced velocity data"""
        x, y, v = self.fill_velocity()
        xlim, ylim = self.model.xlim, self.model.ylim
        xi = np.linspace(xlim[0], xlim[1], nxgrid)
        yi = np.linspace(ylim[0], ylim[1], nygrid)
        xi, yi = np.meshgrid(xi, yi)
        vi = griddata((x, y), v, (xi, yi), method='linear')
        return xi, yi, vi
