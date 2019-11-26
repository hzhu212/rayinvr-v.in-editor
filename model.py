import copy
import numpy as np
import os
import re

from definitions import ROOT_DIR
from util import get_file_logger


logger_tl = get_file_logger('TripleLine', file=os.path.join(ROOT_DIR, 'log', 'model.log'), level='info')
logger_ly = get_file_logger('Layer', file=os.path.join(ROOT_DIR, 'log', 'model.log'), level='info')
logger_vm = get_file_logger('Model', file=os.path.join(ROOT_DIR, 'log', 'model.log'), level='info')


class TripleLine(object):
    """3 lines of the v.in file/model.
    The 3 lines can fold to 6, 9 or 3N lines when the number of nodes exceed
    10*(N-1)."""
    def __init__(self, data=None):
        self._data = data

    @classmethod
    def loads(cls, tstr):
        """Load object from string."""
        if not tstr.strip():
            return
        triple = cls()
        lines = tstr.strip().split('\n')
        lines = [line.strip() for line in lines]
        if len(lines) % 3 != 0:
            raise ValueError('TripleLine can only load strings of 3N lines, but "%s" got.' %tstr)
        triple_line = [[], [], []]
        for i in range(len(lines)//3):
            triple_line[0].extend(re.split(' +', lines[i*3])[1:])
            triple_line[1].extend(re.split(' +', lines[i*3+1])[1:])
            triple_line[2].extend(re.split(' +', lines[i*3+2]))
        triple_line[0] = list(map(float, triple_line[0]))
        triple_line[1] = list(map(float, triple_line[1]))
        triple_line[2] = list(map(int, triple_line[2]))
        if len(set(map(len, triple_line))) != 1:
            raise ValueError('The 3 lines must in the same length, but "%s" got.' %triple_line)
        triple._data = triple_line
        return triple

    def dumps(self, idx=1):
        """Dump current object as string"""
        max_len = 10
        def _dumps(triple_data):
            if len(triple_data[0]) <= max_len:
                return '%2d ' %idx + ''.join(['%8.3f' %x for x in triple_data[0]]) + '\n' \
                    + '%2d ' %0 + ''.join(['%8.3f' %x for x in triple_data[1]]) + '\n' \
                    + '%3s' %'' + ''.join(['%8d' %x for x in triple_data[2]]) + '\n'
            else:
                chunked = list(map(lambda line: line[:max_len], triple_data))
                left = list(map(lambda line: line[max_len:], triple_data))
                return '%2d ' %idx + ''.join(['%8.3f' %x for x in chunked[0]]) + '\n' \
                    + '%2d ' %1 + ''.join(['%8.3f' %x for x in chunked[1]]) + '\n' \
                    + '%3s' %'' + ''.join(['%8d' %x for x in chunked[2]]) + '\n' \
                    + _dumps(left)
        return _dumps(self._data)

    def copy(self):
        """Make a deepcopy of current object."""
        return TripleLine(copy.deepcopy(self._data))

    def move_node(self, idx, delta_x, delta_y):
        """Move a node and return the position of moved node."""
        self._data[0][idx] += delta_x
        self._data[1][idx] += delta_y
        return (self._data[0][idx], self._data[1][idx])

    def __getitem__(self, slc):
        return self._data[slc]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data[0])

    def __str__(self):
        return (
            '<class TripleLine \n'
            '  1: {0}\n'
            '  2: {1}\n'
            '  3: {2}>').format(*map(str, self._data))

    @property
    def x(self):
        return self._data[0]

    @property
    def y(self):
        return self._data[1]

    @y.setter
    def y(self, new_y):
        self._data[1] = new_y

    @property
    def vary(self):
        return self._data[2]

    def insert_node(self, i, new_node=None):
        """Insert a node into the right side of the i-th node, and return
        the value of the newly inserted node(a 1*3 tuple)."""
        if i >= len(self):
            i = len(self) - 1
        # If the value of the node to insert is not specified, determine it
        # through linear interpolation.
        if new_node is None:
            if i == len(self) - 1:
                x = self.x[i] + (self.x[i] - self.x[i-1] if i > 0 else 1)
                y, vary = self.y[i], self.vary[i]
            else:
                x = (self.x[i] + self.x[i+1]) / 2
                y = (self.y[i] + self.y[i+1]) / 2
                vary = self.vary[i]
            new_node = (x, y, vary)
        else:
            if new_node[0] <= self.x[i]:
                raise ValueError(
                    'The x value of the node to insert must larger than that '
                    'of the left neighboring node.')
        # Insert node
        self.x.insert(i+1, new_node[0])
        self.y.insert(i+1, new_node[1])
        self.vary.insert(i+1, new_node[2])
        return new_node

    def delete_node(self, i):
        """Delete the i-th node.
        If the only node was deleted, return True, else, return False."""
        try:
            for lst in self._data:
                lst.pop(i)
        except IndexError as e:
            raise IndexError('Node index out of range in the x direction.')
        if len(self) == 0:
            return True
        return False

class Layer(object):
    """One layer of the v.in file/model.
    Every layer consists of 3 parts:
        1. Depth nodes of the layer;
        2. Velocity nodes on the top of the layer;
        3. Velocity nodes on the bottom of the layer.
    Each part is a TripleLine object."""
    def __init__(self, data=None):
        self._data = data

    @classmethod
    def loads(cls, lstr):
        """Load the Layer object from string"""
        layer = cls([])
        lines = lstr.strip().split('\n')
        if len(lines) % 3 != 0:
            raise ValueError('Layer can only load strings containing 3N lines, but "%s" got.' %lstr)
        last = 0
        for i in range(len(lines)//3):
            line2 = lines[3*i+1]
            if int(line2.lstrip()[:2]) == 0:
                layer._data.append(TripleLine.loads('\n'.join(lines[last*3:(i+1)*3])))
                last = i + 1
        if len(layer._data) != 3:
            raise ValueError('Layer object must consists of THREE parts, but %d got.' %(len(layer._data)))
        layer.fix_depth()
        layer.fix_v_top()
        layer.fix_v_bot()
        return layer

    def copy(self):
        return Layer(copy.deepcopy(self._data))

    def fix_depth(self):
        """Fix the special case of depth nodes. When layer has only 1 depth
        node, it means the depth of the layer is constant. We expand the
        only node to 2 nodes so we can get a horizontal line on the plot."""
        d = self.depth
        if len(d) == 1:
            x, y, vary = (d.x[0], d.y[0], d.vary[0])
            d.x.insert(0, 0)
            d.y.insert(0, y)
            d.vary.insert(0, vary)

    def fix_v_top(self):
        """Fix the special case of top velocity nodes. When layer has only 1
        top velocity node, it means the top velocity of the layer is constant.
        We expand the only node to 2 nodes so we can get a horizontal line on
        the plot.
        If the velocity of the only node is 0, it means there is no velocity
        gradient on the surface between this layer and the upper layer."""
        vt = self.v_top
        if len(vt) == 1:
            x, y, vary = (vt.x[0], vt.y[0], vt.vary[0])
            vt.x.insert(0, 0)
            vt.y.insert(0, y)
            vt.vary.insert(0, vary)

    def fix_v_bot(self):
        """Fix the special case of bottom velocity nodes. When layer has only 1
        bottom velocity node, it means the bottom velocity of the layer is
        constant. We expand the only node to 2 nodes so we can get a horizontal
        line on the plot.
        If the velocity of the only node is 0, it means there is no velocity
        gradient inside this layer."""
        vb = self.v_bot
        if len(vb) == 1:
            x, y, vary = (vb.x[0], vb.y[0], vb.vary[0])
            vb.x.insert(0, 0)
            vb.y.insert(0, y)
            vb.vary.insert(0, vary)

    def recover_depth(self):
        """Recover the fixed depth nodes."""
        d = self.depth
        if len(d) == 2 and abs(d.y[0]-d.y[1]) < 1e-6:
            d.x.pop(0)
            d.y.pop(0)
            d.vary.pop(0)

    def recover_v_top(self):
        """Recover the fixed top velocity nodes."""
        vt = self.v_top
        if len(vt) == 2 and abs(vt.y[0]-vt.y[1]) < 1e-6:
            vt.x.pop(0)
            vt.y.pop(0)
            vt.vary.pop(0)

    def recover_v_bot(self):
        """Recover the fixed bottom velocity nodes."""
        vb = self.v_bot
        if len(vb) == 2 and abs(vb.y[0]-vb.y[1]) < 1e-6:
            vb.x.pop(0)
            vb.y.pop(0)
            vb.vary.pop(0)

    def dumps(self, idx=1, shrink=False):
        cp = self.copy()
        if shrink:
            cp.recover_v_bot()
            cp.recover_v_top()
            cp.recover_depth()
        return ''.join([tl.dumps(idx) for tl in cp._data])

    def __str__(self):
        return (
            '<class Layer \n'
            '  depth: {0}\n'
            '  v_top: {1}\n'
            '  v_bot: {2}>').format(*map(lambda tl:str(tl).replace('\n','\n  '), self._data))

    def __getitem__(self, slc):
        return self._data[slc]

    @property
    def depth(self):
        return self._data[0]

    @property
    def v_top(self):
        return self._data[1]

    @v_top.setter
    def v_top(self, new_v):
        self._data[1] = new_v

    @property
    def v_bot(self):
        return self._data[2]

    @v_bot.setter
    def v_bot(self, new_v):
        self._data[2] = new_v

    def get_tpl(self, node_idx):
        """Get one "part" of this layer(a TripleLine object) according to the
        given NodeIndex object"""
        try:
            return self._data[node_idx.ipart]
        except IndexError as e:
            return None

    def bind_pois(self, pois_obj):
        """Binding poission ratio to layer.
        `pois_obj` is a dict with 2 attributes: 'x' and 'y'. 'x' refers to horizontal
        offset and 'y' refers to poission ratio. An example of pois_obj:
            {'x': [1,2,2,4,4,5], 'y': [0.5,0.5,0.48,0.48,0.49,0.49]}
            means poission ratio between 1-2km is 0.5, and 2-4km is 0.48 and so on."""
        self.pois = pois_obj


class Model(object):
    """The strata model(corresponding to a v.in file).
    Consists of a series of Layer objects."""
    def __init__(self, data=None):
        self._data = data if data else []
        self._end_layer_str = ''

    @classmethod
    def loads(cls, model_string):
        """Load model from string"""
        model = cls()
        lines = model_string.strip().split('\n')
        if int(lines[0].lstrip()[:2]) != 1:
            raise ValueError('The first layer number of a model should be "1".')
        if len(lines)%3 != 2:
            raise ValueError('There should be 2 ending lines at the end of v.in file.')
        model._end_layer_str = '\n'.join(lines[-2:]) + '\n'
        current_layer = 1
        in_layer = []
        for i in range(len(lines)//3+1):
            line1 = lines[3*i]
            if int(line1.lstrip()[:2]) != current_layer:
                model._data.append(Layer.loads('\n'.join(in_layer)))
                in_layer.clear()
                current_layer += 1
            in_layer.extend(lines[3*i:3*(i+1)])
        return model

    @classmethod
    def load(cls, path_vin):
        """Load model from v.in file."""
        with open(path_vin, 'r') as f:
            return cls.loads(f.read())

    def _end_layer(self):
        """Generate the trailing 2 lines at the end of the v.in file"""
        # return '%2i%9.3f\n%2i%9.3f\n' %(self.nlayer+1, 0, 0, 100)
        origin_layer_number = self._end_layer_str.lstrip().split()[0]
        layer_number_len = self._end_layer_str.index(origin_layer_number) + len(origin_layer_number)
        origin_layer_number = self._end_layer_str[:layer_number_len]
        new_layer_number = ('%' + str(layer_number_len) + 'd') % (self.nlayer + 1, )
        return self._end_layer_str.replace(origin_layer_number, new_layer_number)

    def dumps(self):
        """Dump model into a string in the format of v.in."""
        return ''.join([ly.dumps(i+1) for i,ly in enumerate(self._data)]) \
            + self._end_layer()

    def dump(self, path_vin):
        """Dump model into a v.in file."""
        with open(path_vin, 'w') as f:
            f.write(self.dumps())

    def copy(self):
        return Model(copy.deepcopy(self._data))

    def __getitem__(self, slc):
        return self._data[slc]

    def __str__(self):
        return '<class Model with {0} layers: [\n{1}]'.format(
            self.nlayer,
            '\n'.join(map(lambda ly: '  ' + str(ly).replace('\n','\n  '), self._data)))

    def __eq__(self, other):
        return self.dumps() == other.dumps()

    def __len__(self):
        return len(self._data)

    @property
    def nlayer(self):
        return len(self._data)

    @property
    def xlim(self):
        layer1_x = self._data[0].depth.x
        return (layer1_x[0], layer1_x[-1])

    @property
    def ylim(self):
        layer1_y = self._data[0].depth.y
        layer_end_y = self._data[-1].depth.y
        return (min(layer1_y), max(layer_end_y))

    def get_layer(self, node_idx):
        """Get the Layer object according to the given NodeIndex object."""
        try:
            return self._data[node_idx.ilayer]
        except IndexError as e:
            return None

    def get_tpl(self, node_idx):
        """Get the TripleLine object according to the given NodeIndex object."""
        try:
            return self._data[node_idx.ilayer][node_idx.ipart]
        except IndexError as e:
            return None

    def get_node(self, node_idx):
        """Get the value of a node(1*3 tuple) according to the given NodeIndex
        object."""
        try:
            tpl = self._data[node_idx.ilayer][node_idx.ipart]
            return tuple([l[node_idx.inode] for l in tpl])
        except (IndexError, TypeError) as e:
            return None

    def move_node(self, node_idx, delta_x, delta_y):
        """Move a node. The start and end nodes of a TripleLine object are
        forbidden to move."""
        if abs(delta_x) > 1e-6:
            if node_idx.inode == 0:
                raise ValueError('Can not move the LEADING node of a layer')
            if node_idx == node_idx.end(self):
                raise ValueError('Can not move the ENDING node of a layer')
        tpl = self.get_tpl(node_idx)
        return tpl.move_node(node_idx.inode, delta_x, delta_y)

    def insert_node(self, node_idx, new_node=None):
        """Insert a node after the given node specified by the NodeIndex object.
        The end node of a TripleLine object is forbidden to insert after."""
        if node_idx == node_idx.end(self):
            raise ValueError('Can not insert node after the ENDING node of a layer')
        tpl = self.get_tpl(node_idx)
        if tpl is None:
            raise ValueError('Node index out of range in y-direction')
        return tpl.insert_node(node_idx.inode, new_node)

    def delete_node(self, node_idx):
        """Delete the node specified by the given NodeIndex object.
        The start and end nodes of a TripleLine object are forbidden to delete.
        If the only node of the TripleLine object was deleted, return True,
        else, return False."""
        if node_idx.inode == 0:
            raise ValueError('Can not delete LEADING node of a layer')
        if node_idx == node_idx.end(self):
            raise ValueError('Can not delete ENDING node of a layer')
        tpl = self.get_tpl(node_idx)
        if tpl is None:
            raise ValueError('Node index out of range in y-direction')
        # First make a copy of "tpl" to test if it will be deleted to empty.
        tpl_cp = tpl.copy()
        is_empty = tpl_cp.delete_node(node_idx.inode)
        if not is_empty:
            tpl.delete_node(node_idx.inode)
            return
        # TripleLine object of velocity nodes is forbidden to delete to empty.
        if node_idx.ipart != 0:
            raise ValueError('Can not delete all the velocity nodes of a layer')
        # If the TripleLine object of depth nodes is deleted to empty,
        # then delete the whole layer.
        self._data.pop(node_idx.ilayer)
        return is_empty

    def get_thickness(self, ilayer):
        """Get the thickness of a layer. the thickness is the difference
        of depth between the first points of 2 neighboring nodes
        Mainly for inserting layers, drawing text labels for layers etc."""
        if ilayer >= self.nlayer:
            return None
            # raise IndexError('Layer index out of range')
        # if the model only has 1 layer, then return a constant
        if self.nlayer == 1:
            return 0.1
        # if don't have the next layer, then return the thickness of the upper layer
        if ilayer == self.nlayer-1:
            return self.get_thickness(ilayer-1)
        # Normally, return the thickness of current layer
        depth1 = self._data[ilayer].depth.y[0]
        depth2 = self._data[ilayer+1].depth.y[0]
        return depth2 - depth1

    def insert_layer(self, ilayer):
        """Insert a layer under the i-th layer."""
        if ilayer >= self.nlayer:
            raise ValueError('Layer index out of range')
        current_layer = self._data[ilayer]
        new_layer = current_layer.copy()
        # insert to the center of current layer
        delta_y = self.get_thickness(ilayer) / 2
        new_layer.depth.y = [y+delta_y for y in new_layer.depth.y]
        # Set the top velocity of new inserted layer to the average of current
        # top and bottom velocity
        v_top = (current_layer.v_top.y[0] + current_layer.v_bot.y[0]) / 2
        new_layer.v_top.y = [v_top for i in new_layer.v_top.y]
        # Now the top of new layer becomes the bottom of current layer
        current_layer.v_top.y = new_layer.v_top.y.copy()
        self._data.insert(ilayer+1, new_layer)
        logger_vm.debug(new_layer)

    def delete_layer(self, ilayer):
        """Delete the i-th layer."""
        try:
            self._data.pop(ilayer)
        except IndexError as e:
            raise IndexError('Layer index out of range.')


class NodeIndex(object):
    """Class to index any node in a v.in model.
    Like a 1*3 tuple with 3 integer indexs: layer index, part index and
    node index."""
    def __init__(self, *args):
        """Accept 3 integers as parameters."""
        super(NodeIndex, self).__init__()
        if len(args) != 3:
            raise ValueError('NodeIndex accept 3 integers as parameters.')
        self._data = tuple(map(int, args))

    def __getitem__(self, slc):
        return self._data[slc]

    def __hash__(self):
        return hash(self._data)

    def __eq__(self, other):
        return self._data == other._data

    def __lt__(self, other):
        return self._data < other._data

    def __gt__(self, other):
        return self._data > other._data

    def __str__(self):
        return '<class NodeIndex %s>' %str(self._data)

    @property
    def ilayer(self):
        return self._data[0]

    @property
    def ipart(self):
        return self._data[1]

    @property
    def inode(self):
        return self._data[2]

    def left(self):
        """Get the left neighbor. Return None if there is no left neighbor."""
        if self.inode == 0:
            return None
        return NodeIndex(self.ilayer, self.ipart, self.inode-1)

    def right(self):
        """Get the right neighbor. Return None if there is no right neighbor."""
        return NodeIndex(self.ilayer, self.ipart, self.inode+1)

    def up(self):
        """Get the upper neighbor. Return None if there is no upper neighbor."""
        if self.ilayer == 0:
            return None
        return NodeIndex(self.ilayer-1, self.ipart, self.inode)

    def down(self):
        """Get the neighbor below. Return None if there is no neighbor below."""
        return NodeIndex(self.ilayer+1, self.ipart, self.inode)

    def begin(self):
        """Get the starting node index corresponding to the current index."""
        return NodeIndex(self.ilayer, self.ipart, 0)

    def end(self, model):
        """Get the last node index corresponding to the current index."""
        length = len(model.get_tpl(self))
        return NodeIndex(self.ilayer, self.ipart, length-1)

    def next(self, model):
        """Get the next node index according to the given model."""
        if model.get_node(self) is None:
            return None
        next_node = self.right()
        if model.get_node(next_node) is None:
            next_node = NodeIndex(self.ilayer+1, self.ipart, 0)
            if model.get_node(next_node) is None:
                return None
        return next_node

    def previous(self, model):
        """Get the previous node index according to the given model."""
        if self.ilayer == 0 and self._data[2] == 0:
            return None
        prev_node = self.left()
        if prev_node is None:
            prev_node = self.up().end(model)
        if model.get_node(prev_node) is None:
            return None
        return prev_node


class ModelProcessor():
    """Model processor"""
    # How fine is the grid data for velocity contouring
    NGRIDX = 500
    NGRIDY = 1000

    def __init__(self, model):
        self.model = model
        self.has_pois = False

    @staticmethod
    def vp2vs(vp, nu):
        """Calculate Vs from Vp and pois"""
        vs = vp / (2*(1-nu)/(1-2*nu))**0.5
        return vs

    def bind_pois(self, pois_obj):
        """Bind poission ratio to model"""
        self.has_pois = True
        pois = np.array(pois_obj['pois'])
        poisl = np.array(pois_obj.get('poisl', [])) - 1
        poisb = np.array(pois_obj.get('poisb', [])) - 1
        poisbl = np.array(pois_obj.get('poisbl', []))
        pois[pois == 0.5] = 0.49999
        poisbl[poisbl == 0.5] = 0.49999
        if len(pois) < len(self.model):
            tail = np.ones(len(self.model)-len(pois)) * pois[-1]
            pois = np.hstack([pois, tail])
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            x_all = sorted(list(set(np.hstack([x_top, x_bot, x_v_top, x_v_bot]))))

            layer_pois = pois[ily]
            x, y = [], []
            indices = (poisl == ily)
            iblks, pois_bl = poisb[indices], poisbl[indices]
            if iblks.size is 0:
                x, y = [x_all[0], x_all[-1]], [layer_pois]*2
            else:
                if iblks[0] != 0:
                    np.insert(iblks, 0, 0)
                    np.insert(pois_bl, 0, layer_pois)
                if iblks[-1] != len(x_all)-2:
                    np.append(iblks, len(x_all)-2)
                    np.append(pois_bl, layer_pois)
                for iblk, p in zip(iblks, pois_bl):
                    x.extend([x_all[iblk], x_all[iblk+1]])
                    y.extend([p] * 2)
            ly_cur.bind_pois({'x': x, 'y': y})

    def unbind_pois(self):
        self.has_pois = False

    def get_vp_data(self):
        """Get Vp data"""
        data = []
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            y_v_top = np.interp(x_v_top, x_top, y_top)
            y_v_bot = np.interp(x_v_bot, x_bot, y_bot)
            data.append(([x_v_top, y_v_top], [x_v_bot, y_v_bot]))
        return data

    @staticmethod
    def interp_block(x_corner, y_corner, v_corner, xx, yy):
        """velocity interpolating inside a block in rayinvr model"""
        x1, x2, x3, x4 = tuple(x_corner)
        y1, y2, y3, y4 = tuple(y_corner)
        v1, v2, v3, v4 = tuple(v_corner)
        assert x1 == x3 and x2 == x4, 'block should be a trapezoidal in vertical'
        y_top = np.interp(xx, [x1, x2], [y1, y2])
        v_top = np.interp(xx, [x1, x2], [v1, v2])
        y_bot = np.interp(xx, [x3, x4], [y3, y4])
        v_bot = np.interp(xx, [x3, x4], [v3, v4])
        vv = (v_bot - v_top) * (yy - y_top) / (y_bot - y_top) + v_top
        return vv

    def get_v_contour(self):
        """Get velocity grid data by interpolating velocity block by block"""
        xlim, ylim = self.model.xlim, self.model.ylim
        x = np.linspace(xlim[0], xlim[1], self.NGRIDX)
        y = np.linspace(ylim[0], ylim[1], self.NGRIDY)
        xx, yy = np.meshgrid(x, y)
        vp = np.full(xx.shape, np.nan)
        vs = None
        if self.has_pois:
            vs = np.full(xx.shape, np.nan)

        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            v_top, v_bot = ly_cur.v_top.y, ly_cur.v_bot.y
            if self.has_pois:
                x_pois, pois_ly = ly_cur.pois['x'], ly_cur.pois['y']

            x_all = sorted(list(set(np.hstack([x_top, x_bot, x_v_top, x_v_bot]))))
            y_top_all = np.interp(x_all, x_top, y_top)
            y_bot_all = np.interp(x_all, x_bot, y_bot)
            v_top_all = np.interp(x_all, x_v_top, v_top)
            v_bot_all = np.interp(x_all, x_v_bot, v_bot)

            layer_mask = (np.interp(xx, x_top, y_top) <= yy) & (yy < np.interp(xx, x_bot, y_bot))
            for iblk in range(len(x_all)-1):
                x1, x2 = x_all[iblk], x_all[iblk+1]
                block_mask = layer_mask & (x1 <= xx) & (xx <= x2)
                x_cn = [x1, x2, x1, x2]
                y_cn = [y_top_all[iblk], y_top_all[iblk+1], y_bot_all[iblk], y_bot_all[iblk+1]]
                v_cn = [v_top_all[iblk], v_top_all[iblk+1], v_bot_all[iblk], v_bot_all[iblk+1]]
                xx_blk, yy_blk = xx[block_mask], yy[block_mask]
                vp_blk = self.interp_block(x_cn, y_cn, v_cn, xx_blk, yy_blk)
                vp[block_mask] = vp_blk
                # If has pois, calculate vp contour
                if self.has_pois:
                    pois_blk = np.interp((x1+x2)/2.0, x_pois, pois_ly)
                    vs_blk = self.vp2vs(vp_blk, pois_blk)
                    vs[block_mask] = vs_blk

        return xx, yy, vp, vs

    def get_v_section(self, x):
        y = []
        vp = []
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            v_top, v_bot = ly_cur.v_top.y, ly_cur.v_bot.y
            y.extend([np.interp(x, x_top, y_top), np.interp(x, x_bot, y_bot)])
            vp.extend([np.interp(x, x_v_top, v_top), np.interp(x, x_v_bot, v_bot)])
        return np.array(y), np.array(vp)

    def get_section_data(self, x):
        """Get section data, including vp, vs and pois"""
        y, vp, vs, pois = [], [], [], []
        for ily in range(len(self.model)-1):
            ly_cur, ly_next = self.model[ily], self.model[ily+1]
            x_top, x_bot = ly_cur.depth.x, ly_next.depth.x
            y_top, y_bot = ly_cur.depth.y, ly_next.depth.y
            x_v_top, x_v_bot = ly_cur.v_top.x, ly_cur.v_bot.x
            v_top, v_bot = ly_cur.v_top.y, ly_cur.v_bot.y

            y_sec = [np.interp(x, x_top, y_top), np.interp(x, x_bot, y_bot)]
            vp_sec = [np.interp(x, x_v_top, v_top), np.interp(x, x_v_bot, v_bot)]
            y.extend(y_sec)
            vp.extend(vp_sec)
            if self.has_pois:
                x_pois, pois_ly = ly_cur.pois['x'], ly_cur.pois['y']
                pois_sec = [np.interp(x, x_pois, pois_ly)] * 2
                vs_sec = self.vp2vs(np.array(vp_sec), np.array(pois_sec))
                pois.extend(pois_sec)
                vs.extend(vs_sec)
        return np.array(y), np.array(vp), np.array(vs), np.array(pois)
