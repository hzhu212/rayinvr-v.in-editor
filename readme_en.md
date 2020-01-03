# rayinvr-v.in-editor

[中文文档](https://github.com/hzhu212/rayinvr-v.in-editor/blob/master/readme.md)

## Introduction

A simple but useful editor developed with Python3(tkinter+matplotlib) used for editing "strata-velocity model input file (v.in)".

If you aren't interested in the functions of the editor, the code itself is a good example for how to create interactive plot with `matplotlib`.

`v.in` is a kind of ascii file used by the program [Rayinvr](http://terra.rice.edu/department/faculty/zelt/rayinvr.html) developed by Zelt and Smith (1992).

Search the paper "Zelt C A and Smith R B, 1992. Seismic traveltime inversion for 2-D crustal velocity structure. Geophysical Journal International, 108(1): 16-34" for more details.

A simple `v.in` file looks like this:

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

It represents a strata model with 3 layers. Every layer consists of 3 parts: layer depth, velocity on layer top and velocity on layer bottom. Every part contains 3 lines usually, but can fold to next 3 lines when it's length is large than 10. The integer at the beginning of each part tells which layer it belongs to.

To modify a strata model, Rayinvr users have to edit `v.in` file by hand, which is annoying, non-intuitive and easy to make mistakes. That's the reason why `rayinvr v.in editor` comes into being.

## Install and Use

```sh
# download the project from github
git clone https://github.com/hzhu212/rayinvr-v.in-editor.git vin-editor
cd vin-editor

# install dependent packages globally (may cost several minutes)
pip install -r requirements.txt

# launch vin-editor
python main.py

# or double click vin-editor.bat (Windows) / vin-editor.sh (Linux)
```

## Screenshots

Main window:

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173729.png)

Edit strata model:

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173857.png)

Section plot of wave(P/S) velocity:

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103173931.png)

Contour plot of wave(P/S) velocity:

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103174006.png)

Contour plot supports post-processing (through Python script):

![Alt text](https://raw.githubusercontent.com/hzhu212/image-store/master/blog/20200103174046.png)
