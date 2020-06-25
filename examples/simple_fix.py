# A global variable `fig` refering to `matplotlib.figure.Figure` object will be passed into this script
# 代表当前图像的`matplotlib.figure.Figure`对象通过上下文环境传入次脚本，名称为fig
ax = fig.axes[0]    # 主坐标系对象
cax = fig.axes[1]   # 颜色条坐标系对象
cbar = cax.colorbar # 颜色条对象

# 颜色条标注全部保留两位小数
cbar.set_ticklabels([f'{x:.2f}' for x in cbar.get_ticks()])

# 添加圆圈以标出 OBS 位置
ax.scatter([9.45, 11.37, 12.75], [2.13, 2.12, 2.14], marker='o', c='white', edgecolors='black')
ax.text(9.45, 2.13, 'OBS1', c='red', ha='center', va='bottom')

# 设置坐标轴显示范围
ax.set_xbound([7.1, 15.8])
ax.set_ybound([2.0, 2.9])

# 设置图片尺寸
fig.set_size_inches(10, 6, forward=True)

# 设置坐标轴标题和字体
ax.set_xlabel('距离 (km)', fontname='Microsoft Yahei', fontsize=13)
ax.set_ylabel('深度 (km)', fontname='Microsoft Yahei', fontsize=13)
cax.set_ylabel('波速 (km/s)', fontname='Microsoft Yahei', fontsize=13)
# cax.set_ylabel('泊松比', fontname='Microsoft Yahei', fontsize=13)

# 设置坐标轴标线
ax.tick_params(axis='both', which='major', direction='in', labelsize=12)
ax.tick_params(axis='both', which='minor', direction='in', labelsize=10)

# # equivalent to `caxis` function in MATLAB
# cbar.mappable.set_clim([1.48, 2.31])
