"""example script to fine tune velocity contour"""

# A global variable `fig` refering to `matplotlib.figure.Figure` object will be passed into this script

ax = fig.axes[0]
cax = fig.axes[1]
cbar = cax.colorbar

fig.set_size_inches(10, 6, forward=True)

ax.set_xlabel('距离 (km)', fontname='Microsoft Yahei', fontsize=13)
ax.set_ylabel('深度 (km)', fontname='Microsoft Yahei', fontsize=13)
cax.set_ylabel('波速 (km/s)', fontname='Microsoft Yahei', fontsize=13)

ax.tick_params(axis='both', which='major', direction='in', labelsize=12)
ax.tick_params(axis='both', which='minor', direction='in', labelsize=10)

# # equivalent to `caxis` function in MATLAB
# cbar.mappable.set_clim([1.48, 2.31])
