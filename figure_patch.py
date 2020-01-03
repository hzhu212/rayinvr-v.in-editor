"""patch matplotlib figure, add copy tools"""

import io
from PIL import Image
import win32clipboard

import matplotlib.pyplot as plt
plt.rcParams['toolbar'] = 'toolmanager'
from matplotlib.backend_tools import ToolBase, ToolCopyToClipboardBase
import matplotlib.backends.backend_tkagg
from matplotlib.backend_managers import ToolManager

from util import TextWindow


class ToolCopyData(ToolBase):
    """show plotting data in editor window"""

    default_keymap = 'ctrl+e'
    description = 'show plotting data in editor window'

    def trigger(self, *args, **kwargs):
        ax_list = self.figure.get_axes()
        with io.StringIO() as output:
            for i, ax in enumerate(ax_list, 1):
                if len(ax_list) > 1:
                    banner = '—'*36
                    print(f'{banner} Axes {i} {banner}', file=output)
                for j, line in enumerate(ax.get_lines(), 1):
                    xdata_str = str(line.get_xdata().tolist())
                    ydata_str = str(line.get_ydata().tolist())
                    print(f'X{j} = {xdata_str}', file=output)
                    print(f'Y{j} = {ydata_str}', file=output)
                    try:
                        zdata_str = str(line.get_zdata().tolist())
                        print(f'Z{j} = {zdata_str}', file=output)
                    except:
                        pass
            data_str = output.getvalue()
            TextWindow(data_str, title='show plotting data', editable=False)


class ToolCopyToClipboard(ToolCopyToClipboardBase):
    """copy figure to clipboard when ctrl+c pressed"""

    def trigger(self, *args, **kwargs):
        with io.BytesIO() as buf, io.BytesIO() as output:
            self.figure.savefig(buf)
            im = Image.open(buf)
            im.convert('RGB').save(output, 'BMP')
            data = output.getvalue()[14:]  # The file header off-set of BMP is 14 bytes

            # self.figure.savefig(output, format='svg')
            # data = output.getvalue()

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)  # DIB = device independent bitmap
        # win32clipboard.SetClipboardData(b'image/svg+xml ' + data)  # DIB = device independent bitmap
        win32clipboard.CloseClipboard()
        self.figure.canvas.toolbar.set_message('copy image success')


oldfigure = plt.figure
def myfigure(*args, **kwargs):
    fig = oldfigure(*args, **kwargs)
    fig.canvas.manager.toolmanager.add_tool('Data', ToolCopyData)
    fig.canvas.manager.toolmanager.add_tool('Copy', ToolCopyToClipboard)
    fig.canvas.manager.toolbar.add_tool('Data', 'io')
    return fig


class MyNavigationToolbar2Tk(matplotlib.backends.backend_tkagg.NavigationToolbar2Tk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.canvas.toolmanager = ToolManager(self.canvas.figure)
        self.canvas.toolmanager.add_tool('Data', ToolCopyData)
        self.canvas.toolmanager.add_tool('Copy', ToolCopyToClipboard)



plt.figure = myfigure
matplotlib.backends.backend_tkagg.NavigationToolbar2Tk = MyNavigationToolbar2Tk
