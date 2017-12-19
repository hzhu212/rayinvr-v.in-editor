# -*- coding: utf-8 -*-

import logging
logging.basicConfig(level=logging.INFO)
import matplotlib.pyplot as plt
import numpy as np

from util import Vmodel, NodeIndex

class VmodelPloter(object):
    """绘制可交互的地层模型"""
    def __init__(self, path_vin=None, window=None):
        super(VmodelPloter, self).__init__()
        assert path_vin, '必须指定一个 v.in 文件'
        self.path_vin = path_vin
        # window 指定当前绘图对象所在的窗口对象
        self.window = window
        if self.window is None:
            self.fig, self.ax = plt.subplots()
        else:
            self.ax = self.window.plot_ax
            self.fig = self.ax.get_figure()
        self.model = None
        self.lines = []
        self.texts = []
        self.selected = set()
        self.selected_mask = None
        self.ctrl_mode = False

        # 载入模型和绑定事件
        self.load_model()
        self.bind_event()

    def bind_event(self):
        """绑定鼠标和键盘事件"""
        self.fig.canvas.mpl_connect('pick_event', self.on_pick)
        self.fig.canvas.mpl_connect('button_press_event', self.on_button_press)
        self.fig.canvas.mpl_connect('key_press_event', self.on_key_press)
        self.fig.canvas.mpl_connect('key_release_event', self.on_key_release)

    def set_path_vin(self, path_vin):
        self.path_vin = path_vin

    def load_model(self):
        """从 v.in 文件中载入模型"""
        try:
            self.model = Vmodel.load(self.path_vin)
        except Exception as e:
            logging.exception(e)
            self.window.show_error('载入模型时出现以下错误：\n\n"%s"\n\n请检查模型格式' %(', '.join(map(str,e.args))))
            return

    def init_selected(self):
        """初始化选中点，以实现选中点的高亮显示"""
        self.selected_mask, = self.ax.plot([], [], 'rs', ms=6, markeredgewidth=1,
            markerfacecolor='k', visible=False)

    def plot(self):
        """绘制地层模型"""
        if not self.model:
            return
        self.ax.invert_yaxis()
        self.ax.set_title('vmodle for file "%s"' %self.path_vin, fontsize=10)
        self.ax.set_xlabel('x (km)')
        self.ax.set_ylabel('depth (km)')
        for layer in self.model:
            line, = self.ax.plot(layer.depth[0], layer.depth[1], 'ko--',
                picker=5, linewidth=1, markeredgewidth=1, markerfacecolor='w', markersize=4)
            self.lines.append(line)
        self.init_selected()
        self.draw_line_label()
        self.draw_selected()
        plt.show()

    def reload(self):
        """重新从当前 v.in 文件中载入数据并绘图，方便后台用文本编辑器修改模型后直接生效"""
        self.load_model()
        self.ax.cla()
        self.ax.invert_yaxis()
        self.ax.set_title('vmodle for file "%s"' %self.path_vin, fontsize=10)
        self.ax.set_xlabel('x (km)')
        self.ax.set_ylabel('depth (km)')
        self.lines.clear()
        self.texts.clear()
        self.selected.clear()
        for layer in self.model:
            line, = self.ax.plot(layer.depth[0], layer.depth[1], 'ko--',
                picker=5, linewidth=1, markeredgewidth=1, markerfacecolor='w', markersize=4)
            self.lines.append(line)
        self.init_selected()
        self.draw_line_label()
        self.redraw()

    def redraw(self):
        self.draw_selected()
        self.fig.canvas.draw_idle()

    def save_back(self):
        """将修改后的模型保存回关联的 v.in 文件中"""
        self.model.dump(self.path_vin)

    def save_as(self, save_path):
        """将修改后的模型另存为"""
        self.model.dump(save_path)

    def is_modified(self):
        """判断当前模型相对于源文件是否发生了修改"""
        return self.model != Vmodel.load(self.path_vin)

    def update_node(self, node_idx, new_x, new_y):
        """节点移动后更新绘图"""
        line = self.lines[node_idx[0]]
        xs, ys = line.get_data()
        xs[node_idx[2]] = new_x
        ys[node_idx[2]] = new_y
        line.set_data(xs, ys)

    @property
    def dx_sm(self):
        return self.window.slider_vals[0]
    @property
    def dx_lg(self):
        return self.window.slider_vals[1]
    @property
    def dy_sm(self):
        return self.window.slider_vals[2]
    @property
    def dy_lg(self):
        return self.window.slider_vals[3]
    @property
    def pick_tolerence(self):
        return self.window.slider_vals[4]

    def move_left(self):
        """将所有选中的节点左移"""
        delta_x = -self.dx_lg if self.ctrl_mode else -self.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_right(self):
        """将所有选中的节点右移"""
        delta_x = self.dx_lg if self.ctrl_mode else self.dx_sm
        delta_y = 0
        self.move(delta_x, delta_y)

    def move_up(self):
        """将所有选中的节点上移"""
        delta_x = 0
        delta_y = -self.dy_lg if self.ctrl_mode else -self.dy_sm
        self.move(delta_x, delta_y)

    def move_down(self):
        """将所有选中的节点下移"""
        delta_x = 0
        delta_y = self.dy_lg if self.ctrl_mode else self.dy_sm
        self.move(delta_x, delta_y)

    def move(self, delta_x, delta_y):
        """将所有选中的节点按照向量 <delta_x, delta_y> 移动"""
        for node_idx in self.selected:
            new_x, new_y = self.model.move_node(node_idx, delta_x, delta_y)
            self.update_node(node_idx, new_x, new_y)
        self.redraw()
        logging.debug(self.model[0][0])

    def selecte_next(self, accumulate=False):
        """选中所有已选中节点的下一个节点，方向为从上到下、从左到右
        如果 accumulate=True，则当前已选择的节点不会被清除"""
        if not self.selected:
            self.selected.add(NodeIndex(0,0,0))
            self.redraw()
            return
        new_selected = set()
        for node_idx in self.selected:
            will_select = node_idx.right()
            if not self.model.get_node(will_select):
                will_select = node_idx.begin().down()
                if not self.model.get_node(will_select):
                    will_select = node_idx
            new_selected.add(will_select)
        if not accumulate:
            self.selected.clear()
        self.selected.update(new_selected)
        self.redraw()

    def selecte_previous(self, accumulate=False):
        """选中所有已选中节点的前一个节点，方向为从上到下、从左到右
        如果 accumulate=True，则当前已选择的节点不会被清除"""
        if not self.selected:
            self.selected.add(NodeIndex(0,0,0))
            self.redraw()
            return
        new_selected = set()
        for node_idx in self.selected:
            will_select = node_idx.left()
            if not self.model.get_node(will_select):
                up_begin = node_idx.begin().up()
                if not self.model.get_node(up_begin):
                    will_select = node_idx
                else:
                    will_select = up_begin.end(len(self.model.get_tpl(up_begin)))
            new_selected.add(will_select)
        if not accumulate:
            self.selected.clear()
        self.selected.update(new_selected)
        self.redraw()

    def insert_nodes(self):
        """在所有选中的节点右侧插入一个节点"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.window.show_warning('无法插入节点！\n多节点同时插入或删除时，请确保任意 2 个节点不在同一层内\n'
                '否则节点索引将出现混乱，得到意想不到的结果')
            return
        for node_idx in self.selected:
            try:
                x, y, vary = self.model.insert_node(node_idx)
            except Exception as e:
                self.window.show_error('插入节点失败，发生了以下错误：\n%s' %(','.join(e.args)))
            line = self.lines[node_idx[0]]
            xs, ys = line.get_data()
            xs = np.insert(xs, node_idx[2]+1, x)
            ys = np.insert(ys, node_idx[2]+1, y)
            line.set_data(xs, ys)
        self.selected.clear()
        self.redraw()

    def delete_nodes(self):
        """删除所有选中的节点"""
        ilayers = [node_idx[0] for node_idx in self.selected]
        if len(ilayers) != len(set(ilayers)):
            self.window.show_warning('无法删除节点！\n多节点同时插入或删除时，请确保任意 2 个节点不在同一层内\n'
                '否则节点索引将出现混乱，得到意想不到的结果')
            return
        for node_idx in self.selected:
            try:
                self.model.delete_node(node_idx)
            except Exception as e:
                self.window.show_error('删除节点失败，发生了以下错误：\n%s' %(','.join(e.args)))
            line = self.lines[node_idx[0]]
            xs, ys = line.get_data()
            xs = np.delete(xs, node_idx[2])
            ys = np.delete(ys, node_idx[2])
            line.set_data(xs, ys)
        self.selected.clear()
        self.redraw()

    def insert_layer(self):
        """在选中层的下侧插入一层，其形状与该层相同但向下平移一段距离
        其底速度为当前层的底速度，顶速度为当前层顶底速度的线性插值"""
        if not self.selected:
            return
        ilayers = list(set([node_idx[0] for node_idx in self.selected]))
        if len(ilayers) > 1:
            self.window.show_warning('插入新层失败！\n无法同时插入多个层，请确保只选中一个层，将在该层下方插入新层')
            return
        ilayer = ilayers[0]
        self.model.insert_layer(ilayer)
        new_layer = self.model[ilayer+1]
        line, = self.ax.plot(new_layer.depth[0], new_layer.depth[1], 'ko--',
            picker=5, linewidth=1, markeredgewidth=1, markerfacecolor='w', markersize=4)
        self.lines.insert(ilayer+1, line)
        self.texts.clear()
        self.ax.texts.clear()
        self.selected.clear()
        self.draw_line_label()
        self.redraw()

    def delete_layers(self):
        """删除所有选中的层"""
        if not self.selected:
            return
        ilayers = list(set([node_idx[0] for node_idx in self.selected]))
        try:
            for i in reversed(ilayers):
                self.model.delete_layer(i)
                line = self.lines.pop(i)
                self.ax.lines.remove(line)
        except Exception as e:
            self.window.show_error('删除层失败，发生了以下错误：\n%s' %(','.join(e.args)))
        self.texts.clear()
        self.ax.texts.clear()
        self.selected.clear()
        self.draw_line_label()
        self.redraw()

    def on_button_press(self, event):
        """鼠标点击回调"""
        logging.debug('mouse button clicked: %s' %event.button)
        if event.inaxes is None:
            return
        # 在图像中点击中键清空已选择的节点
        if event.button == 2:
            self.selected.clear()
            self.redraw()
            return

    def on_pick(self, event):
        """鼠标成功点选绘图对象时回调"""

        # pick_event 事件的选取对象是一个 Artist 对象，比如一个 Line2D 对象，而不是线上的一点
        # 选中一条线的同时，event 会通过其 ind 属性来索引选中的线上的那些点
        # 可以一次选中多个点，只要他们与鼠标的距离在指定范围内，也可以只选中线，没选中点

        # 只允许左键点选
        if event.mouseevent.button != 1:
            return
        # 非多选模式下，清空之前选中的点
        if not self.ctrl_mode:
            self.selected.clear()
        # 如果没有选中任何线，清空已选择的节点
        try:
            ilayer = self.lines.index(event.artist)
        # 没必要？！
        except ValueError as e:
            logging.debug('未选中任何曲线')
            self.selected.clear()
            return

        # 挑出所有选中的点中最近的一个作为真正选中的点
        x = event.mouseevent.xdata
        y = event.mouseevent.ydata
        # 计算出距离最近的一个
        xs, ys = event.artist.get_data()
        distances = np.hypot(x - xs[event.ind], y - ys[event.ind])
        idx_min = distances.argmin()
        min_dist = distances[idx_min]

        new_selected = set()
        # 如果距离最近的点也远到超出阈值，则认为选中了整条线，而非某个点
        if min_dist > self.pick_tolerence:
            new_selected = set([NodeIndex(ilayer,0,inode) for inode in
                range(len(event.artist.get_xdata()))])
        else:
            inode = event.ind[idx_min]
            new_selected.add(NodeIndex(ilayer,0,inode))

        # ctrl 模式下，需要进行多选或取消多选操作
        if self.ctrl_mode and self.selected.issuperset(new_selected):
            self.selected.difference_update(new_selected)
        else:
            self.selected.update(new_selected)
        self.redraw()

    def on_key_press(self, event):
        """快捷键说明见 editor.py """
        logging.debug('key pressed: %s' %event.key)
        # if not event.inaxes:
            # return
        if event.key not in ('control', 'up', 'down', 'ctrl+up', 'ctrl+down',
            'left', 'right', 'ctrl+left', 'ctrl+right', 'c', 'n', 'p', 'N', 'P',
            'i', 'd', 'delete', 'ctrl+i', 'ctrl+d', 'ctrl+o', 'ctrl+r', 'ctrl+s',
            'ctrl+S', 'f1'):
            return
        if event.key == 'control':
            self.ctrl_mode = True
            return
        if event.key in ('up', 'ctrl+up'):
            self.move_up()
            return
        if event.key in ('down', 'ctrl+down'):
            self.move_down()
            return
        if event.key in ('left', 'ctrl+left'):
            self.move_left()
            return
        if event.key in ('right', 'ctrl+right'):
            self.move_right()
            return
        if event.key == 'c':
            self.selected.clear()
            self.redraw()
            return
        if event.key == 'n':
            self.selecte_next()
            return
        if event.key == 'N':
            self.selecte_next(accumulate=True)
            return
        if event.key == 'p':
            self.selecte_previous()
            return
        if event.key == 'P':
            self.selecte_previous(accumulate=True)
            return
        if event.key == 'i':
            self.insert_nodes()
            return
        if event.key == 'ctrl+i':
            self.insert_layer()
            return
        if event.key in ('d', 'delete'):
            self.delete_nodes()
            return
        if event.key == 'ctrl+d':
            self.delete_layers()
            return
        if event.key == 'ctrl+o':
            self.ctrl_mode = False
            self.window.open_vin()
            return
        if event.key == 'ctrl+r':
            self.ctrl_mode = False
            self.window.reload_vin()
            return
        if event.key == 'ctrl+s':
            self.window.save_back()
            return
        if event.key == 'ctrl+S':
            self.ctrl_mode = False
            self.window.save_as()
            return
        if event.key == 'f1':
            self.window.show_help()
            return

    def on_key_release(self, event):
        """键盘释放回调"""
        if event.key == 'control':
            self.ctrl_mode = False
            return

    def draw_line_label(self):
        """在每条线的左端添加文字标签"""
        for i, line in enumerate(self.lines):
            x, y = (line.get_xdata()[0], line.get_ydata()[0])
            t = self.ax.text(x, y, 'S%s' %(i+1), fontsize=8, rotation=30., ha='right', va='bottom',
                bbox=dict(boxstyle="square", ec=(1., 0.5, 0.5), fc=(1., 0.8, 0.8), alpha=0.7),
                )
            self.texts.append(t)

    def draw_selected(self):
        """高亮显示选中的点"""
        if not self.selected:
            xs, ys = [], []
        else:
            xs, ys = tuple(zip(*[self.model.get_node(node_idx) for node_idx in self.selected]))[:2]
        self.selected_mask.set_data(xs, ys)
        self.selected_mask.set_visible(True)

