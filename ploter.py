import logging
import matplotlib.pyplot as plt
import numpy as np
import os

from util import Vmodel, NodeIndex


class BasePloter(object):
    markers = {'depth': 'o', 'v_top': 'v', 'v_bottom': '^'}
    """Base class for making interactive plot based on a vmodel object"""
    def __init__(self, parent=None, model=None):
        super(BasePloter, self).__init__()
        self.parent = parent
        self.model = model
        self.fig = None
        self.ax = None
        self.lines = []
        self.texts = []
        self.selected = set()
        self.select_mask = None
        self.ctrl_mode = False
        self.line_style = dict(
            linestyle = '--', color='k', markersize=4, picker=5, linewidth=1,
            markeredgewidth=1, markerfacecolor='None',
            )

    def create(self):
        """Create figure and axes objects"""
        if self.fig is None and self.ax is None:
            self.fig, self.ax = plt.subplots()
        self.set_axes()
        self.init_selected()
        self.bind_event()

    def set_axes(self):
        """Set axes. For example title, label, axis direction etc."""
        pass

    def init_selected(self):
        """Create select-mask: a mask layer for highlighting selected nodes.
        select-mask is unvisible until some node(s) is selected"""
        self.select_mask, = self.ax.plot([], [], 'rs', zorder=100, ms=6,
            markeredgewidth=1, markerfacecolor='k', visible=False)

    def bind_event(self):
        """Bind button events and key events"""
        self.fig.canvas.mpl_connect('close_event', self.handle_close)
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)

    def handle_close(self, event):
        """Clear plot status after user closed the plot window to enable
        garbage collection"""
        self.fig = None
        self.ax = None
        self.select_mask = None
        self.ctrl_mode = False
        self.lines.clear()
        self.texts.clear()
        self.selected.clear()

    # some parameters from parent object
    @property
    def dx_sm(self):
        return self.parent.dx_sm
    @property
    def dx_lg(self):
        return self.parent.dx_lg
    @property
    def dy_sm(self):
        return self.parent.dy_sm
    @property
    def dy_lg(self):
        return self.parent.dy_lg
    @property
    def pick_tolerence(self):
        return self.parent.pick_tolerence

    def plot(self):
        """Waiting to be implemented"""
        pass

    def draw_texts(self):
        """Make a label for every line in the figure"""
        pass

    def draw_selected(self):
        """Show select-mask when some node(s) is selected"""
        logging.debug('selected node: ' + ', '.join(map(str, self.selected)))
        if not self.selected:
            xs, ys = [], []
        else:
            nodes = sorted([self.model.get_node(ni) for ni in self.selected])
            xs, ys, _ = zip(*nodes)
        self.select_mask.set_data(xs, ys)
        self.select_mask.set_visible(True)

    def update_plot(self):
        """Update the plot after data changed or plot changed"""
        self.fig.canvas.draw_idle()

    def move_left(self, step_large=False):
        """Move every selected node left a bit"""
        delta_x = -self.dx_lg if step_large else -self.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_right(self, step_large=False):
        """Move every selected node right a bit"""
        delta_x = self.dx_lg if step_large else self.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_up(self, step_large=False):
        """Move every selected node up a bit"""
        delta_x = 0
        delta_y = -self.dy_lg if step_large else -self.dy_sm
        self.move(delta_x, delta_y)

    def move_down(self, step_large=False):
        """Move every selected node down a bit"""
        delta_x = 0
        delta_y = self.dy_lg if step_large else self.dy_sm
        self.move(delta_x, delta_y)

    def move(self, delta_x, delta_y):
        """Move every selected node along the vector <delta_x, delta_y>"""
        for node_idx in self.selected:
            try:
                new_x, new_y = self.model.move_node(node_idx, delta_x, delta_y)
            except Exception as e:
                self.show_warning(
                    'Failed to move nodes, the following error occured:\n\n%s'
                    %(', '.join(map(str, e.args))))
                continue
            self.update_node(node_idx, new_x, new_y)
        # if the first node of any layer was moved, then redraw the text
        # label binding to the node
        if 0 in [node_idx.inode for node_idx in self.selected]:
            self.draw_texts()
        self.draw_selected()
        self.update_plot()

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
            self.draw_selected()
            self.update_plot()
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
        self.draw_selected()
        self.update_plot()

    def select_previous(self, accumulate=False):
        """Select the previous node of every currently selected node,
        following the order of left to right, top to bottom.
        if no node is selected currently, then select the first node of the model
        if accumulate=True, current selection won't be cleared"""
        if not self.selected:
            ilayer, ipart = self.get_tpl_idx_by_line(self.lines[0])
            self.selected.add(NodeIndex(ilayer, ipart, 0))
            self.draw_selected()
            self.update_plot()
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
        self.draw_selected()
        self.update_plot()

    def insert_nodes(self):
        """Insert nodes to the right of every selected node"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.show_warning(
                'Can not insert nodes\nPlease Make sure that every 2 selected '
                'nodes are not in the same layer')
            return
        for node_idx in self.selected:
            try:
                x, y, vary = self.model.insert_node(node_idx)
            except Exception as e:
                self.show_warning(
                    'Failed to inserte nodes, the following error occured:\n\n%s'
                    %(', '.join(map(str, e.args))))
                continue
            line = self.lines[node_idx.ilayer]
            xs, ys = line.get_data()
            xs = np.insert(xs, node_idx.inode+1, x)
            ys = np.insert(ys, node_idx.inode+1, y)
            line.set_data(xs, ys)
        # self.selected.clear()
        self.draw_selected()
        self.update_plot()

    def delete_nodes(self):
        """Delete all the selected nodes"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.show_warning(
                'Can not delete nodes\nPlease Make sure that every 2 selected '
                'nodes are not in the same layer')
            return
        for node_idx in self.selected:
            try:
                is_layer_empty = self.model.delete_node(node_idx)
            except Exception as e:
                self.show_warning(
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
        self.draw_selected()
        self.update_plot()

    def prompt_reload(self):
        """Prompt to reload current v.in file"""
        self.reload()
        pass

    def reload(self):
        """Reload model from current v.in file"""
        pass

    def prompt_save(self):
        """Prompt to save current model"""
        self.save()
        pass

    def save(self):
        """Save current model"""
        pass

    def show_info(self, msg=None):
        self.parent.show_info(msg)

    def show_warning(self, msg=None):
        self.parent.show_warning(msg)

    def show_error(self, msg=None):
        self.parent.show_error(msg)

    def show_help(self, msg=None):
        self.parent.show_help(msg)

    def on_button_press(self, event):
        """Callback funtion for button press event"""
        logging.debug('button pressed: %s' %event.button)
        if event.inaxes is None:
            return

    def get_tpl_idx_by_line(self, line):
        """Get the index of corresponding TripleLine object for the selected
        line"""
        ilayer = self.lines.index(line)
        ipart = list(self.markers.values()).index(line.get_marker())
        return (ilayer, ipart)

    def get_line_by_tpl_idx(self, tpl_idx):
        """Get the line2d object for giving TripleLine index"""
        ilayer, ipart = tpl_idx
        return self.lines[ilayer]

    def on_pick(self, event):
        """Callback funtion for mouse pick event"""
        # only allow left button to pick
        if event.mouseevent.button != 1:
            return
        # clear previously selected nodes on each pick
        if not self.ctrl_mode:
            self.selected.clear()
        ilayer, ipart = self.get_tpl_idx_by_line(event.artist)
        # find the closest node as the node to select
        x = event.mouseevent.xdata
        y = event.mouseevent.ydata
        xs, ys = event.artist.get_data()
        distances = np.hypot(x - xs[event.ind], y - ys[event.ind])
        idx_min = distances.argmin()
        min_dist = distances[idx_min]

        # select the whole line, if even the closest node is still too
        # far(the distance is larger than pick_tolerence)
        new_selected = set()
        if min_dist > self.pick_tolerence:
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
        self.draw_selected()
        self.update_plot()

    def hot_keys(self):
        """Hot keys"""
        return ['control', 'up', 'down', 'ctrl+up', 'ctrl+down', 'left',
            'right', 'ctrl+left', 'ctrl+right', 'c', 'n', 'p', 'N', 'P',
            'ctrl+n', 'ctrl+p', 'i', 'd', 'delete', 'ctrl+s', 'ctrl+r', 'f1',
            ]

    def on_key_press(self, event):
        """Hot key definitions"""
        logging.debug('key pressed: %s' %event.key)
        if event.key not in self.hot_keys():
            return
        if event.key == 'control':
            self.ctrl_mode = True
            return
        if event.key == 'alt':
            self.alt_mode = True
            return
        # ctrl-mode is noly for mouse picking, so clear ctrl-mode here in case
        # it would be blocked by the prompt window and can't clear normally.
        if 'ctrl' in event.key:
            self.ctrl_mode = False
        if event.key in ('up', 'ctrl+up'):
            step_large = ('ctrl' in event.key)
            self.move_up(step_large)
            return
        if event.key in ('down', 'ctrl+down'):
            step_large = ('ctrl' in event.key)
            self.move_down(step_large)
            return
        if event.key in ('left', 'ctrl+left'):
            step_large = ('ctrl' in event.key)
            self.move_left(step_large)
            return
        if event.key in ('right', 'ctrl+right'):
            step_large = ('ctrl' in event.key)
            self.move_right(step_large)
            return
        if event.key == 'c':
            self.selected.clear()
            self.draw_selected()
            self.update_plot()
            return
        if event.key in ('n', 'N', 'ctrl+n'):
            accumulate = event.key.isupper() or 'ctrl' in event.key
            self.select_next(accumulate)
            return
        if event.key in ('p', 'P', 'ctrl+p'):
            accumulate = event.key.isupper() or 'ctrl' in event.key
            self.select_previous(accumulate)
            return
        if event.key == 'i':
            self.insert_nodes()
            return
        if event.key in ('d', 'delete'):
            self.delete_nodes()
            return
        if event.key == 'ctrl+r':
            self.prompt_reload()
            return
        if event.key == 'ctrl+s':
            self.prompt_save()
            return
        if event.key == 'f1':
            self.show_help()
            return

    def on_key_release(self, event):
        """键盘释放回调"""
        if event.key == 'control':
            self.ctrl_mode = False
            return
        if event.key == 'alt':
            self.alt_mode = False
            return


class VmodelPloter(BasePloter):
    """Class to plot model profile"""
    def __init__(self, parent, path_vin):
        super(VmodelPloter, self).__init__(parent=parent)
        self.path_vin = path_vin
        self.ax = self.parent.plot_ax
        self.fig = self.ax.get_figure()
        self.v_ploter = None
        self.line_style.update(marker=self.markers['depth'])
        self.create()
        self.load_model()

    def set_axes(self):
        self.ax.invert_yaxis()
        self.ax.set_title('vmodle for file "%s"' %self.path_vin, fontsize=10)
        self.ax.set_xlabel('x (km)')
        self.ax.set_ylabel('depth (km)')

    def load_model(self):
        """Load model from v.in file"""
        try:
            self.model = Vmodel.load(self.path_vin)
        except Exception as e:
            logging.exception(e)
            self.parent.show_error(
                'The following error occured when loading vmodel:\n\n"%s"\n\n'
                'please checked the format of your v.in file'
                %(', '.join(map(str, e.args))))

    def set_path_vin(self, path_vin):
        """Change v.in file path when opening a new one"""
        self.path_vin = path_vin

    @property
    def cache_path(self):
        """Save current model to cache path before open velocity plot,
        in case velocity plot would need to reload"""
        p = os.path
        name_vin = os.path.split(self.path_vin)[-1]
        return p.join(p.dirname(p.abspath(__file__)), 'cache', name_vin)

    def plot(self):
        """Plot the model"""
        if not self.model:
            return
        for layer in self.model:
            line, = self.ax.plot(layer.depth[0], layer.depth[1], **self.line_style)
            self.lines.append(line)
        self.draw_texts()

    def plot_v(self):
        """open velocity plot"""
        if self.v_ploter is None:
            self.save_cache()
            self.v_ploter = VPloter(parent=self)
        else:
            self.v_ploter.clear()
        self.v_ploter.create()
        self.v_ploter.plot()
        plt.show()

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
        return self.model != Vmodel.load(self.path_vin)

    def prompt_reload(self):
        if self.is_modified() and not self.parent.reload_dialog():
            return
        self.reload()

    def prompt_open(self):
        if self.is_modified() and not self.parent.open_dialog():
            return
        path_vin = self.parent.select_vin_dialog()
        if not path_vin:
            return
        self.open(path_vin)

    def prompt_save(self):
        if self.is_modified() and self.parent.save_dialog():
            self.save()

    def prompt_save_as(self):
        save_path = self.parent.save_as_dialog()
        if not save_path:
            return
        self.save_as(save_path)

    def open(self, path_vin):
        self.set_path_vin(path_vin)
        self.reload()

    def reload(self):
        self.ax.cla()
        self.lines.clear()
        self.selected.clear()
        self.create()
        self.load_model()
        self.plot()
        self.draw_selected()
        self.update_plot()

    def save(self):
        """Save model back into current v.in file"""
        self.model.dump(self.path_vin)

    def save_as(self, save_path):
        """Save model as a new v.in file"""
        self.model.dump(save_path)

    def save_cache(self):
        """Save current model to cache path before open velocity plot,
        in case velocity plot would need to reload"""
        cache_dir = os.path.dirname(self.cache_path)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        self.save_as(self.cache_path)

    def insert_layer(self):
        """Insert a new layer under selected node(s).
        If selected nodes are in different layers, show warning message and
        quit inserting"""
        if not self.selected:
            return
        ilayers = list(set([node_idx.ilayer for node_idx in self.selected]))
        if len(ilayers) > 1:
            self.parent.show_warning(
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
        self.draw_selected()
        self.update_plot()

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
            self.parent.show_error(
                'Failed to delete layers, the following error occured:\n%s'
                %(', '.join(map(str, e.args))))
        self.selected.clear()
        self.draw_texts()
        self.draw_selected()
        self.update_plot()

    def on_button_press(self, event):
        super(VmodelPloter, self).on_button_press(event)
        # clear all the selections when clicking middle button
        logging.debug('button pressed in VmodelPloter: %s' %event.button)
        if event.button == 2:
            self.selected.clear()
            self.draw_selected()
            self.update_plot()
            return

    def hot_keys(self):
        default = super(VmodelPloter, self).hot_keys()
        custom = ['ctrl+i', 'ctrl+d', 'ctrl+o', 'ctrl+S', 'v']
        return default + custom

    def on_key_press(self, event):
        super(VmodelPloter, self).on_key_press(event)
        # customed hot keys
        if event.key == 'ctrl+i':
            self.insert_layer()
            return
        if event.key == 'ctrl+d':
            self.delete_layers()
            return
        if event.key == 'ctrl+o':
            self.prompt_open()
            return
        if event.key == 'ctrl+S':
            self.prompt_save_as()
            return
        if event.key == 'v':
            self.plot_v()
            return


# ------------------------------------------------------------ #
# velocity plot
# ------------------------------------------------------------ #
class VPloter(BasePloter):
    """Velocity ploter"""
    def __init__(self, parent):
        super(VPloter, self).__init__(parent)
        # customed
        self.model = self.parent.model
        self.labels = []

    def clear(self):
        """Clear status to ready for replot"""
        if self.ax is not None:
            self.ax.cla()
        self.lines.clear()
        self.labels.clear()
        self.texts.clear()
        self.selected.clear()

    def set_axes(self):
        self.ax.invert_yaxis()
        self.ax.set_title('velocity plot for file "%s"' %(self.parent.path_vin),
            fontsize=10)
        self.ax.set_xlabel('x (km)')
        self.ax.set_ylabel('velocity (km/s)')

    def plot(self):
        """Get velocity plot.
        If there are(is) selected nodes, then only plot velocity for the
        surfaces that have selected nodes.
        If there is no node selected, then plot velocity for all surfaces."""
        if not self.parent.selected:
            ilayers = range(len(self.model))
        else:
            ilayers = set([node_idx.ilayer for node_idx in self.parent.selected])
            iupper_layers = set([i-1 for i in list(ilayers)]).difference(set([-1]))
            ilayers = list(ilayers.union(iupper_layers))
        for i in ilayers:
            # For every selected surface, we plot 2 velocity line:
            # 1. the velocity on the top of the surface
            # 2. the velocity below the surface
            line_v_top, = self.ax.plot(
                self.model[i].v_top[0], self.model[i].v_top[1],
                marker=self.markers['v_top'], **self.line_style)
            line_v_bottom, = self.ax.plot(
                self.model[i].v_bottom[0], self.model[i].v_bottom[1],
                marker=self.markers['v_bottom'], **self.line_style)
            lines = (line_v_top, line_v_bottom)
            # assign surface index as label for every line
            self.labels.extend([(i,1), (i,2)])
            self.lines.extend(lines)
        self.draw_texts()

    def draw_texts(self):
        """Draw label for each line """
        self.ax.texts.clear()
        self.texts.clear()
        for (ilayer, ipart), line in zip(self.labels, self.lines):
            # x, y = (line.get_xdata()[0], line.get_ydata()[0])
            x, y = (0, line.get_ydata()[0])
            t = self.ax.text(
                x, y, 'Ly%s-%s' %(ilayer+1, 'top' if ipart==1 else 'bot'),
                fontsize=8, rotation=30., ha='right', va='top', bbox=dict(
                    boxstyle="square", ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8),
                    alpha=0.7),
                )
            self.texts.append(t)

    def is_modified(self):
        with open(self.parent.cache_path) as f:
            cached = f.read().rstrip()
        current = self.model.dumps().rstrip()
        return cached != current

    def prompt_save(self):
        return self.parent.prompt_save()

    def prompt_reload(self):
        if self.is_modified() and not self.parent.parent.reload_dialog():
            return
        self.reload()

    def reload(self):
        """Reload model from parent cached v.in file"""
        new_model = self.load_model()
        if new_model is None:
            return
        self.model = new_model
        self.parent.model = new_model
        self.clear()
        self.create()
        self.plot()
        self.draw_selected()
        self.update_plot()

    def load_model(self):
        """Load model from cached v.in file"""
        try:
            return Vmodel.load(self.parent.cache_path)
        except Exception as e:
            self.parent.show_error(
                'The following error occured when loading vmodel:\n\n"%s"\n\n'
                'please checked the format of the cached v.in file:\n"%s"'
                %(', '.join(map(str, e.args))), self.parent.cache_path)
            return None

    def hot_keys(self):
        return ['control', 'up', 'down', 'ctrl+up', 'ctrl+down', 'left',
            'right', 'ctrl+left', 'ctrl+right', 'c', 'n', 'p', 'N', 'P',
            'i', 'd', 'delete', 'ctrl+r', 'ctrl+s', 'f1']

    def get_tpl_idx_by_line(self, line):
        return self.labels[self.lines.index(line)]

    def get_line_by_tpl_idx(self, tpl_idx):
        return self.lines[self.labels.index(tpl_idx)]
