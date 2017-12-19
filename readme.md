# rayinvr-v.in-editor

[中文文档](https://github.com/hzhu212/rayinvr-v.in-editor/blob/master/readme_zh.md)

## Introduction

A simple but useful editor developed with Python3(tkinter+matplotlib) used for editing "strata-velocity model input file (v.in)".

If you aren't interested in the functions of the editor, the code itself is a good example for how to create interactive plot with `matplotlib`.

`v.in` is a kind of ascii file used by the program "rayinvr" developed by Zelt and Smith (1992).

Search the paper "Zelt C A and Smith R B, 1992. Seismic traveltime inversion for 2-D crustal velocity structure. Geophysical Journal International, 108(1): 16-34" for more details.

Download links for the **rayinvr** program:

- [Download gzip-compressed rayinvr package (0.3 Mb)](http://terra.rice.edu/department/faculty/zelt/rayinvr.tar.gz)
- [Download uncompressed rayinvr package (1.6 Mb)](http://terra.rice.edu/department/faculty/zelt/rayinvr.tar)

![Screenshot of rayinvr](http://os09d5k4j.bkt.clouddn.com/image/171214/6bHH4fhhJG.png?imageslim)

A sample `v.in` file looks like this:

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

It represents a strata model with 3 layers. Every layer consists of 3 parts: layer depth, velocity on layer top and velocity on layer bottom. Every part contains 3 lines usually, but can fold to next 3 lines when it's length is large than 10. The integer at the beginning of each part tells which layer it belongs to.

When working with a strata model, we usually adjust numbers in the `v.in` file by hand, which is annoying, non-intuitive and easy to get wrong. That's why **rayinvr v.in editor** comes into being.

## How to use

```sh
git clone https://github.com/hzhu212/rayinvr-v.in-editor.git vin-editor
cd vin-editor
pip install -r requirements.txt
py -3 start.py
```

A `virtualenv` version (recommend):

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

Next time, you can just type these:

```sh
cd vin-editor
./venv/Scripts/activate
python start.py
```

## Screenshots

![mark](http://os09d5k4j.bkt.clouddn.com/image/171220/EFBHF1c7Im.png?imageslim)

![mark](http://os09d5k4j.bkt.clouddn.com/image/171220/5c1Ef9B82h.png?imageslim)

![mark](http://os09d5k4j.bkt.clouddn.com/image/171220/akL5DJ4g76.png?imageslim)

![mark](http://os09d5k4j.bkt.clouddn.com/image/171220/hhiGELFBCa.png?imageslim)

![mark](http://os09d5k4j.bkt.clouddn.com/image/171220/J8iFH91ELJ.png?imageslim)
