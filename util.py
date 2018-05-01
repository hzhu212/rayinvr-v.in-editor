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

    # How fine is the grid data for velocity contouring
    NGRIDX = 1000
    NGRIDY = 1000

    def __init__(self, delegate):
        super().__init__(delegate)
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'util.log'),
            level = 'debug')

    @staticmethod
    def get_perspective_transform(points_orig, points_dest):
        """Get perspective transform matrix"""
        A = []
        for p, p_prime in zip(points_orig, points_dest):
            A.append([p[0], p[1], 1, 0, 0, 0, -p_prime[0]*p[0], -p_prime[0]*p[1]])
            A.append([0, 0, 0, p[0], p[1], 1, -p_prime[1]*p[0], -p_prime[1]*p[1]])
        A = np.array(A)
        b = np.array(points_dest).flatten()
        r = np.linalg.solve(A, b)
        res = np.append(r, 1).reshape((3, 3))
        return res

    @staticmethod
    def apply_perspective_transform(ptm, points):
        """Apply perspective transform for points"""
        n_points = len(points)
        points = np.hstack([points, np.ones((n_points, 1))])
        res = ptm.dot(points.T).T
        res = (res / res[:,-1:])[:,:2]
        return res


    @staticmethod
    def interp_block(xs, ys, vs, xx, yy):
        """velocity interpolating inside a block in rayinvr model"""
        x1, x2, x3, x4 = tuple(xs)
        y1, y2, y3, y4 = tuple(ys)
        v1, v2, v3, v4 = tuple(vs)
        assert x1 == x3 and x2 == x4, 'block should be a trapezoidal in vertical'
        y_top = np.interp(xx, [x1, x2], [y1, y2])
        v_top = np.interp(xx, [x1, x2], [v1, v2])
        y_bot = np.interp(xx, [x3, x4], [y3, y4])
        v_bot = np.interp(xx, [x3, x4], [v3, v4])
        vv = (v_bot - v_top) * (yy - y_top) / (y_bot - y_top) + v_top
        return vv


    def get_grid_data(self):
        """interpolate velocity block by block"""
        xlim, ylim = self.model.xlim, self.model.ylim
        x = np.linspace(xlim[0], xlim[1], self.NGRIDX)
        y = np.linspace(ylim[0], ylim[1], self.NGRIDY)
        xx, yy = np.meshgrid(x, y)
        vv = np.full(xx.shape, np.nan)

        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            v_top, v_bot = ly_cur.v_top.y, ly_cur.v_bot.y

            x_all = sorted(list(set(np.hstack([x_top, x_bot, x_v_top, x_v_bot]))))
            y_top_all = np.interp(x_all, x_top, y_top)
            y_bot_all = np.interp(x_all, x_bot, y_bot)
            v_top_all = np.interp(x_all, x_v_top, v_top)
            v_bot_all = np.interp(x_all, x_v_bot, v_bot)

            layer_mask = (np.interp(xx, x_top, y_top) <= yy) & (yy < np.interp(xx, x_bot, y_bot))
            for iblk in range(len(x_all)-1):
                x1, x2 = x_all[iblk], x_all[iblk+1]
                block_mask = layer_mask & (x1 <= xx) & (xx <= x2)
                xs = [x1, x2, x1, x2]
                ys = [y_top_all[iblk], y_top_all[iblk+1], y_bot_all[iblk], y_bot_all[iblk+1]]
                vs = [v_top_all[iblk], v_top_all[iblk+1], v_bot_all[iblk], v_bot_all[iblk+1]]
                xx_blk, yy_blk = xx[block_mask], yy[block_mask]
                vv_blk = self.interp_block(xs, ys, vs, xx_blk, yy_blk)
                vv[block_mask] = vv_blk

        return xx, yy, vv


    def fill_velocity(self):
        """fill velocity for all nodes, includeing depth nodes, velocity nodes
        and derived nodes"""
        x_acc, y_acc, v_acc = [], [], []
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            v_top, v_bot = ly_cur.v_top.y, ly_cur.v_bot.y

            x_all = sorted(list(set(np.hstack([x_top, x_bot, x_v_top, x_v_bot]))))
            y_top_all = np.interp(x_all, x_top, y_top)
            y_bot_all = np.interp(x_all, x_bot, y_bot)
            v_top_all = np.interp(x_all, x_v_top, v_top)
            v_bot_all = np.interp(x_all, x_v_bot, v_bot)

            x_acc.extend([x_all, x_all])
            y_acc.extend([y_top_all, y_bot_all-0.0001])
            v_acc.extend([v_top_all, v_bot_all])

        x, y, v = np.hstack(x_acc), np.hstack(y_acc), np.hstack(v_acc)
        return x, y, v

    def get_grid_data2(self):
        """gridding irregularly spaced velocity data"""
        x, y, v = self.fill_velocity()
        xlim, ylim = self.model.xlim, self.model.ylim
        xx = np.linspace(xlim[0], xlim[1], self.NGRIDX)
        yy = np.linspace(ylim[0], ylim[1], self.NGRIDY)
        xx, yy = np.meshgrid(xx, yy)
        vv = griddata((x, y), v, (xx, yy), method='linear')
        return xx, yy, vv
