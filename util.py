import numpy as np
import re
from tkinter import filedialog

class TripleLine(object):
    """地层模型每 3 行作为一组数据(长度超过10可以折行)
    分别为：节点 x 坐标、节点深度/速度、反演时是否可变
    其中，每一行都用一个 numpy 数组保存"""
    def __init__(self, data=None):
        super(TripleLine, self).__init__()
        self._data = data

    @classmethod
    def loads(cls, triple_string):
        """从字符串中载入数据"""
        if not triple_string.strip():
            return
        triple = cls()
        lines = triple_string.strip().split('\n')
        lines = [line.strip() for line in lines]
        assert len(lines) % 3 == 0, '模型的一组节点数据必须为 3N 行'
        triple_line = [[], [], []]
        for i in range(len(lines)//3):
            triple_line[0].extend(re.split(' +', lines[i*3])[1:])
            triple_line[1].extend(re.split(' +', lines[i*3+1])[1:])
            triple_line[2].extend(re.split(' +', lines[i*3+2]))
        triple_line[0] = list(map(float, triple_line[0]))
        triple_line[1] = list(map(float, triple_line[1]))
        triple_line[2] = list(map(int, triple_line[2]))
        assert len(set(map(len, triple_line))) == 1, '一组节点的三行数据必须等长'
        triple._data = triple_line
        return triple

    def dumps(self, idx=0):
        """将数据输出为字符串"""
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

    def move_node(self, idx, delta_x, delta_y):
        """移动节点，并返回移动后节点的坐标"""
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

    @property
    def z(self):
        return self._data[1]

    @property
    def v(self):
        return self._data[1]

    @property
    def vary(self):
        return self._data[2]

    def insert_node(self, i, new_node=None):
        """在第 i 个节点右侧插入一个新的节点，如果节点超出索引，则认为在最后一个节点右侧插入，不抛出错误
        返回插入后的新节点 3 元组"""
        if i >= len(self):
            i = len(self) - 1
        # 如果新节点的值未指定，则采用两侧节点的线性插值
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
                raise ValueError('新插入节点的 x 坐标必须大于其左侧的节点')
        # 插入新节点
        self.x.insert(i+1, new_node[0])
        self.y.insert(i+1, new_node[1])
        self.vary.insert(i+1, new_node[2])
        return new_node

    def delete_node(self, i):
        """删除第 i 个节点右，如果节点超出索引，则认为在最后一个节点右侧插入，不抛出错误"""
        try:
            for lst in self._data:
                lst.pop(i)
        except IndexError as e:
            raise IndexError('节点索引在横向上超出了模型范围')

class Layer(object):
    """地层模型的一层。
    data 为一个长度为 3 的数组，代表 3 个部分：地层深度、顶部速度、底部速度。
    其中，每个部分均为一个 TripleLine 对象"""
    def __init__(self, data=None):
        super(Layer, self).__init__()
        self._data = data

    @classmethod
    def loads(cls, layer_string):
        """从一层的字符串中加载层对象"""
        layer = cls([])
        lines = layer_string.strip().split('\n')
        assert len(lines) % 3 == 0, '模型的每层均应包含 3N 行'
        last = 0
        for i in range(len(lines)//3):
            line2 = lines[3*i+1]
            if int(line2.lstrip()[:2]) == 0:
                layer._data.append(TripleLine.loads('\n'.join(lines[last*3:(i+1)*3])))
                last = i + 1
        assert len(layer._data) == 3, '模型的每层必须且仅能包含 3 个部分：深度节点、顶速度节点、底速度节点'
        return layer

    def dumps(self, idx=1):
        return ''.join([tl.dumps(idx) for tl in self._data])

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

    @property
    def v_bottom(self):
        return self._data[2]

    def get_tpl(self, node_idx):
        """给出 NodeIndex 对象，返回节点所在的 TripleLine 对象，如果超出索引则返回 None"""
        try:
            return self._data[node_idx[1]]
        except IndexError as e:
            return None


class Vmodel(object):
    """地层模型类
    其 data 属性为一个 Layer 对象的数组"""
    def __init__(self, data=None):
        super(Vmodel, self).__init__()
        self._data = data if data else []

    def loads(self, model_string):
        """从字符串中加载模型"""
        lines = model_string.strip().split('\n')
        assert int(lines[0].lstrip()[:2]) == 1, '模型的起始层编号应为 1'
        assert len(lines)%3 == 2, '请确保模型底部有结束层，结束层包含 2 行，即深度节点的 x 和 z 坐标'
        current_layer = 1
        in_layer = []
        for i in range(len(lines)//3+1):
            line1 = lines[3*i]
            if int(line1.lstrip()[:2]) != current_layer:
                self._data.append(Layer.loads('\n'.join(in_layer)))
                in_layer.clear()
                current_layer += 1
            in_layer.extend(lines[3*i:3*(i+1)])
        self.end_layer = '\n'.join(lines[-2:]) + '\n'

    @classmethod
    def load(cls, path_vin):
        """从 v.in 文件中加载模型"""
        vmodel = cls()
        with open(path_vin, 'r') as f:
            vmodel.loads(f.read())
        return vmodel

    def dumps(self):
        """将模型生成 v.in 格式的字符串"""
        return ''.join([ly.dumps(i+1) for i,ly in enumerate(self._data)]) + self.end_layer

    def dump(self, path_vin):
        """将模型以 v.in 的格式保存到指定文件中"""
        with open(path_vin, 'w') as f:
            f.write(self.dumps())

    def __getitem__(self, slc):
        return self._data[slc]

    def __str__(self):
        return '<class Vmodel with {0} layers: [\n{1}]'.format(
            self.nlayer,
            '\n'.join(map(lambda ly: '  ' + str(ly).replace('\n','\n  '), self._data)))

    def __eq__(self, other):
        return self.dumps() == other.dumps()

    def __len__(self):
        return len(self._data)

    @property
    def nlayer(self):
        return len(self._data)

    def get_layer(self, node_idx):
        """给出 NodeIndex 对象，返回节点所在的层对象，如果超出索引则返回 None"""
        try:
            return self._data[node_idx[0]]
        except IndexError as e:
            return None

    def get_tpl(self, node_idx):
        """给出 NodeIndex 对象，返回节点所在的 TripleLine 对象，如果超出索引则返回 None"""
        try:
            return self._data[node_idx[0]][node_idx[1]]
        except IndexError as e:
            return None

    def get_node(self, node_idx):
        """给出 NodeIndex 对象，返回节点处的值（1*3 tuple），如果超出索引则返回 None"""
        try:
            tpl = self._data[node_idx[0]][node_idx[1]]
            return tuple([l[node_idx[2]] for l in tpl])
        except (IndexError, TypeError) as e:
            return None

    def move_node(self, node_idx, delta_x, delta_y):
        """移动一个节点"""
        layer = self._data[node_idx[0]]
        tpl = layer[node_idx[1]]
        return tpl.move_node(node_idx[2], delta_x, delta_y)

    def insert_node(self, node_idx, new_node=None):
        """在 node_idx 右侧插入一个新的节点，返回插入后的新节点 3 元组"""
        tpl = self.get_tpl(node_idx)
        if tpl is None:
            raise IndexError('节点索引在纵向上超出了模型范围')
        return tpl.insert_node(node_idx[2], new_node)

    def delete_node(self, node_idx):
        """删除 node_idx 指示的节点"""
        tpl = self.get_tpl(node_idx)
        if tpl is None:
            raise IndexError('节点索引在纵向上超出了模型范围')
        tpl.delete_node(node_idx[2])


class NodeIndex(object):
    """模型中某个节点的索引，相当于一个 1*3 的 tuple，用 3 个整数分别制定：
    层索引、所属部分索引、节点索引"""
    def __init__(self, *args):
        """接收 3 个整数参数"""
        super(NodeIndex, self).__init__()
        assert len(args) == 3, 'NodeIndex 接收的参数为一个长度为 3 的 tuple 或 list'
        self._data = tuple(map(int, args))

    def __getitem__(self, slc):
        return self._data[slc]

    def __hash__(self):
        return hash(self._data)

    def __eq__(self, other):
        return self._data == other._data

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
        """返回左边邻居节点的索引对象，如果已到最左侧则返回 None"""
        if self.inode == 0:
            return None
        return NodeIndex(self.ilayer, self.ipart, self.inode-1)

    def right(self):
        """返回右边邻居节点的索引对象"""
        return NodeIndex(self.ilayer, self.ipart, self.inode+1)

    def up(self):
        """返回上方邻居节点的索引对象，如果已到最上方则返回 None"""
        if self.ilayer == 0:
            return None
        return NodeIndex(self.ilayer-1, self.ipart, self.inode)

    def down(self):
        """返回下方邻居节点的索引对象"""
        return NodeIndex(self.ilayer+1, self.ipart, self.inode)

    def begin(self):
        """返回该层的第一个节点"""
        return NodeIndex(self.ilayer, self.ipart, 0)

    def end(self, length):
        """返回该层的最后一个节点，需要传入该层的长度"""
        return NodeIndex(self.ilayer, self.ipart, length-1)
