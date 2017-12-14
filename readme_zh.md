# rayinvr-v.in-editor

[English Document](https://github.com/hzhu212/rayinvr-v.in-editor/blob/master/readme.md)

## 简介

一款简单易用的“地层模型编辑器”，使用 Python3 编写。

用于编辑一种称作 `v.in` 的文本文件，这种文件为 Zelt 和 Smith 于 1992 年开发的地层反演程序 rayinvr 所使用的地层模型格式。

关于 rayinvr 和 v.in 的更多详情可搜索文献“Zelt C A and Smith R B, 1992. Seismic traveltime inversion for 2-D crustal velocity structure. Geophysical Journal International, 108(1): 16-34”

**rayinvr** 软件下载地址：

- [Download gzip-compressed rayinvr package (0.3 Mb)](http://terra.rice.edu/department/faculty/zelt/rayinvr.tar.gz)
- [Download uncompressed rayinvr package (1.6 Mb)](http://terra.rice.edu/department/faculty/zelt/rayinvr.tar)

![rayinvr 运行截图](http://os09d5k4j.bkt.clouddn.com/image/171214/6bHH4fhhJG.png?imageslim)

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
 3    0.00 100.00 200.00 300.00
 0   25.00  25.00  25.00  25.00
         1      1      1      1
 3  300.00
 0    6.40
         1
 3  300.00
 0    6.73
        -1
 4  300.00
 0   40.00
```

上述 v.in 文件描述了一个包含 3 层的地层模型。每一层都由 3 个部分组成：地层深度、地层顶部速度、地层底部速度。每个部分一般包含 3 行，但当该部分的长度超过 10 的时候也可折行，如上例中的第一层的地层深度部分，折行后，该部分的第二行行首的 0 应改为 1。每个部分开头的整数描述了该部分位于哪一层。

当调节地层模型的时候，我们一般需要手动编辑 `v.in` 文件中的数字，这非常的麻烦、不直观，而且容易出错，这就是我为什么要写 **rayinvr v.in editor** 这款小工具。

## 使用方法

```sh
git clone https://github.com/hzhu212/rayinvr-v.in-editor.git vin-editor
cd vin-editor
pip install -r requirements.txt
py -3 start.py
```

推荐使用 `virtualenv`：

```sh
git clone https://github.com/hzhu212/rayinvr-v.in-editor.git vin-editor
cd vin-editor

# install virtualenv
pip install virtualenv

# create a virtual environment and activate it
virtualenv venv
./venv/Scripts/activate

# install required packages into virtual environment, rather than globally
pip install -r requirements.txt

# start the program
python start.py
```

virtualenv 只用配置一次，下次运行直接用以下命令即可：

```sh
cd vin-editor
./venv/Scripts/activate
python start.py
```

## 运行截图

![v.in-editor 运行截图](http://os09d5k4j.bkt.clouddn.com/image/171214/elg4A60BiB.png?imageslim)

![v.in-editor 运行截图](http://os09d5k4j.bkt.clouddn.com/image/171214/D0fjgIH9Gg.png?imageslim)

![v.in-editor 运行截图](http://os09d5k4j.bkt.clouddn.com/image/171214/Dl89gJG26c.png?imageslim)

![v.in-editor 运行截图](http://os09d5k4j.bkt.clouddn.com/image/171214/439AI7dgmG.png?imageslim)
