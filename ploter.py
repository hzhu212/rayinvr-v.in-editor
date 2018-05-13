from collections import OrderedDict
import matplotlib.pyplot as plt
import numpy as np
import os

from definitions import ROOT_DIR
from util import get_file_logger, Delegator
from model import Model, NodeIndex


class BasePloter(object):
    """Base class for making interactive plot based on a model object"""

    # Each type of nodes has a unique marker in plot. depth nodes: circle;
    # top velocity: downward-triangle; bottom velocity: upward-triangle
    MARKERS = OrderedDict([('depth', 'o'), ('v_top', 'v'), ('v_bottom', '^')])

    def __init__(self, window=None):
        # window is a proxy for `MainWindow`, which provides many attributs and methods.
        # See `MainWindowProxy` class for more information.
        self.wd = window
        self.canvas = self.wd.canvas
        self.ax = self.wd.ax
        self.model = None
        self.lines = []
        self.texts = []
        self.selected = set()
        self.select_mark = None
        self.ctrl_mode = False
        self.line_style = dict(
            linestyle='--', color='k', markersize=4, picker=5, linewidth=1,
            markeredgewidth=1, markerfacecolor='None')
        self.logger = get_file_logger(
            name = type(self).__name__,
            file = os.path.join(ROOT_DIR, 'log', 'ploter.log'),
            level = 'debug')
        self.init_select()
        self.bind_event()

    def init_select(self):
        """Create select-mask: a mask layer for highlighting selected nodes.
        select-mask is unvisible until some node(s) is selected"""
        self.select_mark, = self.ax.plot(
            [], [], 'rs', zorder=100, ms=6, markeredgewidth=1, markerfacecolor='k',
            visible=False)

    def bind_event(self):
        """Bind button events and key events"""
        self.canvas.mpl_connect('pick_event', self.on_pick)
        self.canvas.mpl_connect('button_press_event', self.on_button_press)

    def draw_select(self):
        """Show select-mask when some node(s) is selected"""
        self.logger.debug('selected nodes: ' + ', '.join(map(str, sorted(list(self.selected)))))
        if not self.selected:
            xs, ys = [], []
        else:
            node_indexes = sorted(list(self.selected))
            nodes = [self.model.get_node(ni) for ni in node_indexes]
            # Echo message for selected nodes
            echo_msg = '\n'.join(['[ i, j]: ( x, z, flag)', '-'*28]) + '\n' + \
                '\n'.join(['[%2d,%2d]: (%6.3f,%6.3f,%2d)' %(ni.ilayer, ni.inode, nd[0], nd[1], nd[2]) \
                for ni, nd in zip(node_indexes, nodes)])
            # If there are 2 nodes selected, show there distance in addition
            if len(nodes) == 2:
                nd1, nd2 = nodes[0], nodes[1]
                dx, dy = nd2[0] - nd1[0], nd2[1] - nd1[1]
                d = (dx**2 + dy**2)**0.5
                echo_msg += '\n\n' + '\n'.join([
                    'distance_x = %6.3f',
                    'distance_y = %6.3f',
                    'distance   = %6.3f']) %(dx, dy, d)
            self.wd.echo.set(echo_msg)
            xs, ys, _ = zip(*nodes)
        self.select_mark.set_data(xs, ys)
        self.select_mark.set_visible(True)

    def draw(self):
        """Update the plot after data changed or plot changed"""
        self.canvas.draw_idle()

    def move_left(self, step_large=False):
        """Move every selected node left a bit"""
        delta_x = -self.wd.dx_lg if step_large else -self.wd.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_right(self, step_large=False):
        """Move every selected node right a bit"""
        delta_x = self.wd.dx_lg if step_large else self.wd.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_up(self, step_large=False):
        """Move every selected node up a bit"""
        delta_x = 0
        delta_y = -self.wd.dy_lg if step_large else -self.wd.dy_sm
        self.move(delta_x, delta_y)

    def move_down(self, step_large=False):
        """Move every selected node down a bit"""
        delta_x = 0
        delta_y = self.wd.dy_lg if step_large else self.wd.dy_sm
        self.move(delta_x, delta_y)

    def move(self, delta_x, delta_y):
        """Move every selected node along the vector <delta_x, delta_y>"""
        for node_idx in self.selected:
            try:
                new_x, new_y = self.model.move_node(node_idx, delta_x, delta_y)
            except Exception as e:
                self.wd.show_warning('Warning',
                    'Failed to move nodes, the following error occured:\n\n%s'
                    %(', '.join(map(str, e.args))))
                continue
            self.update_node(node_idx, new_x, new_y)
        # if the first node of any layer was moved, then redraw the text
        # label binding to the node
        if 0 in [node_idx.inode for node_idx in self.selected]:
            self.draw_texts()
        self.draw_select()
        self.draw()

    def update_node(self, node_idx, new_x, new_y):
        """Update coordinates of nodes after they are modified"""
        line = self.get_line_by_tpl_idx((node_idx.ilayer, node_idx.ipart))
        xs, ys = line.get_data()
        xs[node_idx.inode] = new_x
        ys[node_idx.inode] = new_y
        line.set_data(xs, ys)

    def select_next(self, accumulate=False):
        """Select the next node of every currently selected node,
        following the order of left to right, top to bottom.
        if no node is selected currently, then select the first node of the model
        if accumulate=True, current selection won't be cleared"""
        if not self.selected:
            ilayer, ipart = self.get_tpl_idx_by_line(self.lines[0])
            self.selected.add(NodeIndex(ilayer, ipart, 0))
            self.draw_select()
            self.draw()
            return
        new_selected = set()
        for node_idx in self.selected:
            next_node = node_idx.next(self.model)
            if next_node is None:
                continue
            new_selected.add(next_node)
        if not accumulate:
            self.selected.clear()
        self.selected.update(new_selected)
        self.draw_select()
        self.draw()

    def select_previous(self, accumulate=False):
        """Select the previous node of every currently selected node,
        following the order of left to right, top to bottom.
        if no node is selected currently, then select the first node of the model
        if accumulate=True, current selection won't be cleared"""
        if not self.selected:
            ilayer, ipart = self.get_tpl_idx_by_line(self.lines[0])
            self.selected.add(NodeIndex(ilayer, ipart, 0))
            self.draw_select()
            self.draw()
            return
        new_selected = set()
        for node_idx in self.selected:
            prev_node = node_idx.previous(self.model)
            if prev_node is None:
                continue
            new_selected.add(prev_node)
        if not accumulate:
            self.selected.clear()
        self.selected.update(new_selected)
        self.draw_select()
        self.draw()

    def insert_nodes(self):
        """Insert nodes to the right of every selected node"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.wd.show_warning('Warning'
                'Can not insert nodes\nPlease Make sure that every 2 selected '
                'nodes are not in the same layer')
            return
        for node_idx in self.selected:
            try:
                x, y, vary = self.model.insert_node(node_idx)
            except Exception as e:
                self.wd.show_warning('Warning',
                    'Failed to inserte nodes, the following error occured:\n\n%s'
                    %(', '.join(map(str, e.args))))
                continue
            line = self.lines[node_idx.ilayer]
            xs, ys = line.get_data()
            xs = np.insert(xs, node_idx.inode+1, x)
            ys = np.insert(ys, node_idx.inode+1, y)
            line.set_data(xs, ys)
        # self.selected.clear()
        self.draw_select()
        self.draw()

    def delete_nodes(self):
        """Delete all the selected nodes"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.wd.show_warning('Warning',
                'Can not delete nodes\nPlease Make sure that every 2 selected '
                'nodes are not in the same layer')
            return
        for node_idx in self.selected:
            try:
                is_layer_empty = self.model.delete_node(node_idx)
            except Exception as e:
                self.wd.show_warning('Warning',
                    'Failed to delete nodes, the following error occured:\n\n%s'
                    %(', '.join(map(str, e.args))))
                continue
            if is_layer_empty:
                line = self.lines.pop(node_idx.ilayer)
                self.ax.lines.remove(line)
                self.draw_texts()
                continue
            line = self.lines[node_idx.ilayer]
            xs, ys = line.get_data()
            xs = np.delete(xs, node_idx.inode)
            ys = np.delete(ys, node_idx.inode)
            line.set_data(xs, ys)
        self.selected.clear()
        self.draw_select()
        self.draw()

    def on_button_press(self, event):
        """Callback funtion for button press event"""
        if not self.model:
            return
        self.logger.debug('Button pressed: %s' %event.button)
        if event.inaxes is None:
            self.logger.debug('But cursor not in axes.')
            return

    def get_tpl_idx_by_line(self, line):
        """Get the index of corresponding TripleLine object for the selected
        line"""
        ilayer = self.lines.index(line)
        ipart = list(self.MARKERS.values()).index(line.get_marker())
        return (ilayer, ipart)

    def get_line_by_tpl_idx(self, tpl_idx):
        """Get the line2d object for giving TripleLine index"""
        ilayer, ipart = tpl_idx
        return self.lines[ilayer]

    def on_pick(self, event):
        """Callback funtion for mouse pick event"""
        # only allow left button to pick
        self.logger.debug('Pick event occured')
        if event.mouseevent.button != 1:
            return
        # clear previously selected nodes on each pick
        if not self.ctrl_mode:
            self.selected.clear()
        ilayer, ipart = self.get_tpl_idx_by_line(event.artist)
        # find the closest node as the node to select
        x = event.mouseevent.xdata
        y = event.mouseevent.ydata
        self.logger.debug('Cursor picked at (%f, %f), selected layer %d' %(x, y, ilayer))
        xs, ys = event.artist.get_data()
        distances = np.hypot(x - xs[event.ind], y - ys[event.ind])
        idx_min = distances.argmin()
        min_dist = distances[idx_min]

        # select the whole line, if even the closest node is still too
        # far(the distance is larger than pick_tolerence)
        new_selected = set()
        if min_dist > self.wd.pick:
            new_selected = set([NodeIndex(ilayer,ipart,inode) for inode in
                range(len(event.artist.get_xdata()))])
        else:
            inode = event.ind[idx_min]
            new_selected.add(NodeIndex(ilayer,ipart,inode))

        # if in ctrl-mode, allow multiple selection and anti-selection
        if self.ctrl_mode and self.selected.issuperset(new_selected):
            self.selected.difference_update(new_selected)
        else:
            self.selected.update(new_selected)
        self.draw_select()
        self.draw()

    def on_key_press(self, event):
        """Hot key definitions"""
        # Don not listen key event before opening model
        if self.model is None:
            return

        key = event.keysym
        if not (len(key) == 1 and key.isalpha()):
            key = key.lower()
        self.logger.debug('key pressed: %s' %key)

        # enter ctrl_mode
        if key == 'control_l':
            self.ctrl_mode = True
            return

        if key == 'up':
            self.move_up(self.ctrl_mode)
            return
        if key == 'down':
            self.move_down(self.ctrl_mode)
            return
        if key == 'left':
            self.move_left(self.ctrl_mode)
            return
        if key == 'right':
            self.move_right(self.ctrl_mode)
            return
        if key == 'escape':
            self.selected.clear()
            self.draw_select()
            self.draw()
            return
        if key in ('n', 'N'):
            accumulate = key.isupper() or self.ctrl_mode
            self.select_next(accumulate)
            return
        if key in ('p', 'P'):
            accumulate = key.isupper() or self.ctrl_mode
            self.select_previous(accumulate)
            return
        if not self.ctrl_mode and key == 'i':
            self.insert_nodes()
            return
        if not self.ctrl_mode and key in ('d', 'backspace', 'delete'):
            self.delete_nodes()
            return

    def on_key_release(self, event):
        """Key Releasing event"""
        # Don not listen key event before opening model
        if self.model is None:
            return

        key = event.keysym
        if not (len(key) == 1 and key.isalpha()):
            key = key.lower()
        self.logger.debug('key released: %s' %key)

        # exit ctrl_mode
        if key == 'control_l':
            self.ctrl_mode = False
            return


class ModelPloter(BasePloter):
    """Class to plot model profile"""
    def __init__(self, window):
        super().__init__(window)
        self.line_style.update(marker=self.MARKERS['depth'])

    def open(self):
        self.ax.cla()
        self.lines.clear()
        self.selected.clear()
        self.set_axes()
        self.load_model()

        self.plot_model()
        self.init_select()
        self.draw()

    def set_axes(self):
        self.ax.invert_yaxis()
        self.ax.set_xlabel('X (km)')
        self.ax.set_ylabel('Depth (km)')

    def load_model(self):
        """Load model from v.in file"""
        try:
            self.model = Model.load(self.wd.vin_path)
        except Exception as e:
            self.logger.exception(e)
            self.wd.show_error(
                'Error', 'The following error occured while loading model:\n"%s"\n\n'
                %(', '.join(map(str, e.args))))

    def plot_model(self):
        """Plot the model"""
        if not self.model:
            return
        for layer in self.model:
            line, = self.ax.plot(layer.depth[0], layer.depth[1], **self.line_style)
            self.lines.append(line)
        self.draw_texts()

    def draw_texts(self):
        """Make a label for every line in the figure"""
        self.ax.texts.clear()
        self.texts.clear()
        for i, line in enumerate(self.lines):
            # texts will be in the middle of layer
            # x, y = (line.get_xdata()[0], line.get_ydata()[0])
            x, y = (0, line.get_ydata()[0])
            y += self.model.get_thickness(i) / 2
            t = self.ax.text(
                x, y, 'Ly%s' %(i+1), fontsize=8, rotation=0, ha='right',
                va='center', bbox=dict(
                    boxstyle="square", ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8),
                    alpha=0.7),
                )
            self.texts.append(t)

    def is_modified(self):
        """Check if the model has been modified"""
        if not self.model:
            return False
        return self.model != Model.load(self.wd.vin_path)

    def save(self, path=None):
        """Save model back into current v.in file"""
        p = path or self.wd.vin_path
        self.model.dump(p)

    def insert_layer(self):
        """Insert a new layer under selected node(s).
        If selected nodes are in different layers, show warning message and
        quit inserting"""
        if not self.selected:
            return
        ilayers = list(set([node_idx.ilayer for node_idx in self.selected]))
        if len(ilayers) > 1:
            self.wd.show_warning('Warning',
                'Failed to insert new layer.\nMake sure that all the selected '
                'nodes are in the same layer, then editor will insert a layer below.')
            return
        ilayer = ilayers[0]
        self.model.insert_layer(ilayer)
        new_layer = self.model[ilayer+1]
        line, = self.ax.plot(new_layer.depth[0], new_layer.depth[1], **self.line_style)
        self.lines.insert(ilayer+1, line)
        self.selected.clear()
        self.draw_texts()
        self.draw_select()
        self.draw()

    def delete_layers(self):
        """Delete all the selected layers"""
        if not self.selected:
            return
        ilayers = list(set([node_idx[0] for node_idx in self.selected]))
        try:
            for i in reversed(ilayers):
                self.model.delete_layer(i)
                line = self.lines.pop(i)
                self.ax.lines.remove(line)
        except Exception as e:
            self.wd.show_error('Error',
                'Failed to delete layers, the following error occured:\n%s'
                %(', '.join(map(str, e.args))))
        self.selected.clear()
        self.draw_texts()
        self.draw_select()
        self.draw()

    def on_key_press(self, event):
        """customed hot keys"""
        key = event.keysym
        if not (len(key) == 1 and key.isalpha()):
            key = key.lower()
        super().on_key_press(event)

        if self.ctrl_mode and key == 'i':
            self.insert_layer()
            return
        if self.ctrl_mode and key == 'd':
            self.delete_layers()
            return


# ------------------------------------------------------------ #
# velocity plot
# ------------------------------------------------------------ #
class VContourPlotDelegator(Delegator):
    """Delegator for plotting velocity contours"""

    def __init__(self, delegate, allowed_attrs=None):
        super().__init__(delegate, allowed_attrs)
        self.init_plot()

    def init_plot(self):
        self.ax = self.fig.add_subplot(111)
        self.ax.tick_params(axis='both', which='major', labelsize=9)
        self.ax.tick_params(axis='both', which='minor', labelsize=8)
        self.ax.invert_yaxis()
        self.ax.set_xlabel('X (km)')
        self.ax.set_ylabel('Depth (km)')

    def plot_vmodel(self):
        """Plot velocity nodes"""
        for layer in self.model_proc.model:
            self.ax.plot(layer.depth[0], layer.depth[1], 'k.:')
        vp_data = self.model_proc.get_vp_data()
        for top_data, bot_data in vp_data:
            x_v_top, y_v_top = tuple(top_data)
            x_v_bot, y_v_bot = tuple(bot_data)
            self.ax.plot(x_v_top, y_v_top, color='k', marker=11, markerfacecolor='white', linestyle='None')
            self.ax.plot(x_v_bot, y_v_bot, color='k', marker=10, markerfacecolor='white', linestyle='None')

    def plot_velocity_contour(self):
        xx, yy, vp, vs = self.model_proc.get_v_contour()
        p = self.ax.pcolormesh(xx, yy, vp, cmap='jet')
        # p = self.ax.imshow(
        #     np.flip(vp, axis=0), cmap='jet', aspect='auto',
        #     extent=self.model_proc.model.xlim+self.model_proc.model.ylim)
        # self.ax.invert_yaxis()
        cbar = self.fig.colorbar(p, shrink=0.8, fraction=0.1, pad=0.03)
        cbar.ax.set_ylabel('velocity (km/s)')
        cbar.ax.invert_yaxis()
        self.plot_vmodel()


class VSectionPlotDelegator(Delegator):
    """Delegator for plotting velocity sections"""

    TITLES = ('Vp', 'Vs', 'Poisson')
    X_LABELS = ('Vp (km/s)', 'Vs (km/s)', 'Poisson')
    Y_LABEL = 'mbsf'

    def __init__(self, delegate, allowed_attrs=None):
        super().__init__(delegate, allowed_attrs)
        self.init_plot()

    def init_plot(self):
        self.axs[0].set_ylabel(self.Y_LABEL)
        self.axs[0].invert_yaxis()
        self.axs[2].set_xlim(left=0.35, right=0.5)
        for i, ax in enumerate(self.axs):
            ax.grid(linestyle='--')
            ax.tick_params(axis='both', which='major', labelsize=9)
            ax.tick_params(axis='both', which='minor', labelsize=8)
            ax.set_xlabel(self.X_LABELS[i])
            ax.xaxis.tick_top()
            ax.xaxis.set_label_position('top')
        self.curves = [None] * 3

    def plot_sections(self, section_x):
        y, vp, vs, pois = self.model_proc.get_section_data(section_x)
        y = y * 1e3
        if vs.size > 0:
            self.plot_vs_section(y, vs)
            self.plot_pois_section(y, pois)
        self.plot_vp_section(y, vp)

    def plot_vp_section(self, depth, val):
        if self.curves[0] is None:
            self.curves[0], = self.axs[0].plot(val, depth, 'r-', linewidth=1)
        else:
            self.curves[0].set_data(val, depth)
        self.axs[0].set_ylim(top=0, bottom=1.05*depth[-1])

    def plot_vs_section(self, depth, val):
        if self.curves[1] is None:
            self.curves[1], = self.axs[1].plot(val, depth, 'g-', linewidth=1)
        else:
            self.curves[1].set_data(val, depth)
        self.axs[1].relim()
        self.axs[1].autoscale_view(scalex=True, scaley=False)

    def plot_pois_section(self, depth, val):
        if self.curves[2] is None:
            self.curves[2], = self.axs[2].plot(val, depth, 'b-', linewidth=1)
        else:
            self.curves[2].set_data(val, depth)
        # self.axs[2].relim()
        # self.axs[2].autoscale_view(scalex=True, scaley=False)

    def flatten_by_layer(self, idx):
        y = self.curves[0].get_ydata()
        if y[2*idx] == 0:
            return
        y_new = y - y[2*idx]
        # Reset depth data
        for curve in self.curves:
            if curve is None:
                continue
            curve.set_ydata(y_new)
        # Reset depth limit
        self.axs[0].set_ylim(top=0, bottom=1.05*y_new[-1])
        self.fig.canvas.draw()
