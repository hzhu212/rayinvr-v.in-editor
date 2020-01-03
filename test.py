import matplotlib.pyplot as plt
import numpy as np

from model import TripleLine, Layer, EndLayer, Model, ModelManager, NodeIndex
from ploter import ModelPloter
from util import SessionManager, HistoryManager, parse_pois_str


def test_triple_line():
    s = '''
    12    0.000   1.000   1.500   2.500   3.000
     0    2.550   2.560   2.570   2.570   2.590
             0       0       0       1       0
    '''

    t = TripleLine.loads(s)
    print(t)
    print(t._data)
    print(t.dumps(5))
    t.insert_node(3, (2.51,1,0))
    print(t.dumps())

def test_layer():
    s = '''
    2    0.000   0.940   1.450   2.440   2.660   6.140   7.270   7.700   8.350   9.570
    1    2.550   2.560   2.570   2.570   2.590   2.580   2.540   2.350   2.180   2.130
             0       0       0       0       0       0       0       0       0       0
    2   10.940  11.910  12.330  16.060  17.930  18.960  20.470  21.210  23.000
    0    2.110   2.120   2.130   2.250   2.400   2.490   2.480   2.440   2.410
             0       0       0       0       0       0       0       0       0
    2    0.000  23.000
    0    1.500   1.500
             0       0
    2    0.000  23.000
    0    1.506   1.506
             0       0
    '''

    ly = Layer.loads(s)
    print(ly)
    print(ly._data)
    print(ly.dumps(2))

def test_end_layer():
    s = '''
    6  300.000
    0   40.000
    '''
    ely = EndLayer.loads(s)
    print(ely)
    print(ely.dumps())

def test_model():
    path_vin = 'examples/v1.in'
    model = Model.load(path_vin)
    print(model)
    print(model.dumps())
    print(model.get_node(NodeIndex(0,0,5)))

def test_ploter():
    path_vin = 'v.in'
    ploter = ModelPloter(path_vin)
    ploter.plot()


def test_velosity_interp():
    s = '''
    1    0.000  23.000
    0    0.000   0.000
             0       0
    1    0.000  23.000
    0    1.480   1.480
             0       0
    1    0.000  23.000
    0    1.480   1.480
             0       0
    2    0.000   0.940   1.450   2.440   2.660   6.140   7.270   7.700   8.350   9.570
    1    2.550   2.560   2.570   2.570   2.590   2.580   2.540   2.350   2.180   2.130
             0       0       0       0       0       0       0       0       0       0
    2   10.940  11.910  12.330  16.060  17.930  18.960  20.470  21.210  23.000
    0    2.110   2.120   2.130   2.250   2.400   2.490   2.480   2.440   2.410
             0       0       0       0       0       0       0       0       0
    2    0.000  23.000
    0    1.500   1.500
             0       0
    2    0.000  23.000
    0    1.520   1.520
             0       0
    3    0.000   0.940   1.450   2.440   2.660   6.140   7.270   7.700   8.350   9.000
    1    2.620   2.630   2.640   2.640   2.660   2.650   2.610   2.420   2.255   2.225
             0       0       0       0       0       0       0       0       0       0
    3   10.000  11.000  12.000  13.000  14.000  15.000  16.060  17.930  18.960  20.470
    1    2.188   2.185   2.200   2.230   2.290   2.300   2.322   2.462   2.547   2.537
             0       0       0       0       0       0       0       0       0       0
    3   21.210  23.000
    0    2.497   2.467
             0       0
    3    0.000   9.000   9.500  10.000  10.500  11.000  11.500  12.000  12.500  13.000
    1    1.842   1.842   1.842   1.805   1.771   1.857   1.788   1.779   1.841   1.905
             0       0       0       0       0       0       0       0       0       1
    3   13.500  14.000  14.500  15.000  15.500  23.000
    0    1.938   1.880   1.851   1.839   1.793   1.842
             0       0       0       0       0       0
    3    0.000  23.000
    0    2.100   2.100
             0       0
    4    0.000  23.000
    0    2.620   2.620
    '''
    # 3    0.000  23.000
    # 0    2.620   2.620

    model = Model.loads(s)
    mp = ModelManager(model)
    xx, yy, vv = mp.get_v_contour()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    fig.set_tight_layout(True)
    ax.invert_yaxis()
    ax.set_xlabel('X (km)')
    ax.set_ylabel('Depth (km)')

    p = ax.imshow(np.flip(vv, axis=0), cmap='jet', aspect='auto', extent=model.xlim+model.ylim)
    ax.invert_yaxis()
    cbar = plt.colorbar(p, shrink=0.8, fraction=0.1, pad=0.03)
    cbar.ax.set_ylabel('velocity (km/s)')
    cbar.ax.invert_yaxis()

    for layer in model:
        ax.plot(layer.depth[0], layer.depth[1], 'k.:', linewidth=1)
    plt.show()


def test_session_manager():
    sm = SessionManager(autosave=True)
    print(sm.load())
    sm['file'] = 'test/中文/v.in'
    print(sm)
    print(sm.load())
    sm.update({'pois': '1,2,3,'})
    print(sm.load())

def test_history_manager():
    hm = HistoryManager(autosave=True)
    sm = SessionManager(autosave=False)
    sm['file'] = 'test1_v.in'
    hm.merge_session(sm)
    print(hm.load())
    sm['pois'] = '1,2,3,4,5,'
    hm.merge_session(sm)
    print(hm.load())
    sm.update({'file': 'test2_v.in', 'pois': 'test pois'})
    hm.merge_session(sm)
    print(hm.load())

def test_parse_pois_str():
    pois_str = '''
        pois=0.4999,0.4852,0.4770,0.4620,0.4700,
        poisl=2,2,2,2,3,3,
        poisb=2,3,5,6,2,4,
        poisbl=0.485,0.487,0.476,0.458,0.462,0.489,'''
    print(parse_pois_str(pois_str))

if __name__ == '__main__':
    test_triple_line()
    # test_layer()
    # test_end_layer()
    # test_model()
    # test_ploter()
    # test_velosity_interp()
    # test_session_manager()
    # test_history_manager()
    # test_parse_pois_str()
