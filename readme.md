# rayinvr-v.in-editor

[English Document](https://github.com/hzhu212/rayinvr-v.in-editor/blob/master/readme_en.md)

## 简介

一款简单易用的“地层模型编辑器”，使用 Python3 编写（借助 tkinter、matplotlib 等第三方库）。

如果你对这款编辑器没有兴趣，那么代码本身仍有参考价值，它将教你如何使用 `matplotlib` 创建复杂的交互式绘图，值得参考。

用于编辑一种称作 `v.in` 的文本文件，这种文件为 Zelt 和 Smith 于 1992 年开发的地层反演程序 [Rayinvr](http://terra.rice.edu/department/faculty/zelt/rayinvr.html) 所使用的地层模型格式。

关于 Rayinvr 和 `v.in` 的更多详情可搜索文献“Zelt C A and Smith R B, 1992. Seismic traveltime inversion for 2-D crustal velocity structure. Geophysical Journal International, 108(1): 16-34”

一个简单的 `v.in` 文件示例如下:

```txt
 1    0.00  25.00  50.00  75.00 100.00 125.0  150.00 175.00 200.00 225.00
 1    0.40   0.20  -0.50  -1.50   0.20   0.60   1.50   0.30   1.00   0.70
         0      0      0      0      0      0      0      0      0      0
 1  250.00 275.00 300.00
 0    0.00   0.50   0.50
         0      0      0
 1    0.00 150.00 300.00
 0    4.90   4.90   4.90
         1      1      1
 1    0.00 150.00 300.00
 0    5.40   5.40   5.40
         1      1      1
 2  300.00
 0   10.00
         0
 2  300.00
 0    0.00
         0
 2    0.00 150.00 300.00
 0    5.70   5.70   5.70
         1      1      1
 3  300.00
 0   40.00
```

上述 v.in 文件描述了一个包含 3 层的地层模型。每一层都由 3 个部分组成：地层深度、地层顶部速度、地层底部速度。每个部分一般包含 3 行，但当该部分的长度超过 10 的时候也可折行，如上例中的第一层的地层深度部分，折行后，该部分的第二行行首的 0 应改为 1。每个部分开头的整数描述了该部分位于哪一层。

在调整地层模型时需要手动编辑 `v.in` 文件中的数字，非常的麻烦、不直观，且容易出错。这也就是编写 `rayinvr v.in editor` 这款工具的初衷。

## 下载与安装

```sh
# 下载项目
git clone https://github.com/hzhu212/rayinvr-v.in-editor.git vin-editor
cd vin-editor

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py

# 或双击 vin-editor.bat (Windows) / vin-editor.sh (Linux)
```

## 运行截图

主界面：

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173729.png)

编辑模型：

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173857.png)

波速剖面图：

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173931.png)

波速云图：

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103174006.png)

波速云图支持后期处理（通过 Python 脚本）：

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103174046.png)
