#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_marine_clip.py — what the marine clip removes, and why only four.

Four panels, all on real geometry:

    1  Stikine delta / Dry Strait   the 225 km2 polygon and its 264 leaked cells
    2  Cross Sound / Chatham        the 141 km2 polygon labelled "Porcupine River"
    3  statewide                    all four, against the 963 kept
    4  the alternatives             leak vs IDW coverage for the three options

The mechanism this exists to show: NHDArea ftype 364 (Lake/Pond) is not always
a lake, and build_brown_polygon_mask admits a polygon WHOLE if any part of it
falls inside the 2 km reach-point or 500 m flowline buffer. A large estuarine
polygon grazing a river mouth therefore brings its entire marine extent into
the river-ice interpolation mask.

drop_marine_polygons() removes any polygon intersecting an NWN segment whose
KEY_ID is not in friction_config.RIVER_SEGMENT_KEY_IDS. On a correctly built
mask panel 1-3 show no dark leaked cells at all.

Usage:
    python plot_marine_clip.py
    python plot_marine_clip.py --out figs/clip.png
"""

import numpy as np, matplotlib, pyproj, warnings, json
matplotlib.use('Agg'); warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
import geopandas as gpd, rasterio
from shapely.ops import unary_union

SURF="#fcfcfb"; INK="#0b0b0b"; INK2="#52514e"; MUTED="#898781"; HAIR="#e1e0d9"
WATER="#dde6f0"; LAND="#f0efec"; AXIS="#c3c2b7"
C_KEEP="#86b6ef"; C_BAD="#d03b3b"; C_FL="#2a78d6"; C_MAR="#898781"; C_LEAK="#7a1f1f"
plt.rcParams.update({"font.family":["DejaVu Sans"],"figure.facecolor":SURF,
                     "axes.facecolor":SURF,"savefig.facecolor":SURF})
OUT='outputs/analysis/river_ice_marine_clip.png'
ref=rasterio.open('/mnt/user-data/uploads/alaska-fuel-spatial-network/outputs/01_friction_build/waterway_mask_150m.tif')
T=ref.transform; D=6
water=np.load('/tmp/water_bg.npy'); H,W=water.shape
EXT=[T.c,T.c+W*D*150,T.f-H*D*150,T.f]
bad=gpd.read_file('/tmp/bad_polys.gpkg'); marine=gpd.read_file('/tmp/marine_nwn.gpkg')
rivn=gpd.read_file('/tmp/river_nwn.gpkg')
poly=gpd.read_file('/tmp/brownpoly/brown_river_polygons/brown_river_polygons.shp').to_crs(3338)
fl=gpd.read_file('/tmp/brown/brown_river_flowlines/brown_river_flowlines.shp').to_crs(3338)
good=poly[~poly.index.isin(poly.sjoin(bad,how='inner',predicate='intersects').index)]
lk=np.load('/tmp/leakcells.npz'); LX=T.c+(lk['cc']+.5)*T.a; LY=T.f+(lk['rr']+.5)*T.e
fwd=pyproj.Transformer.from_crs('EPSG:4326','EPSG:3338',always_xy=True)

fig=plt.figure(figsize=(14.6,10.4),dpi=165)
gs=fig.add_gridspec(2,2,hspace=0.20,wspace=0.09,left=0.03,right=0.985,top=0.775,bottom=0.055)

def panel(cell,bounds,title,sub,labels,legend=False):
    ax=fig.add_subplot(cell)
    x0,y0=fwd.transform(bounds[0],bounds[1]); x1,y1=fwd.transform(bounds[2],bounds[3])
    ax.imshow(np.where(water,0,1).astype(float),extent=EXT,origin='upper',
              cmap=matplotlib.colors.ListedColormap([WATER,LAND]),interpolation='nearest',zorder=0)
    good.plot(ax=ax,fc=C_KEEP,ec='none',alpha=.9,zorder=1)
    marine.plot(ax=ax,color=C_MAR,lw=2.6,alpha=.85,zorder=2)
    rivn.plot(ax=ax,color=C_FL,lw=2.6,alpha=.85,zorder=2)
    bad.plot(ax=ax,fc=C_BAD,ec=C_BAD,lw=.8,alpha=.55,zorder=3)
    fl.plot(ax=ax,color=C_FL,lw=1.0,zorder=4)
    ax.scatter(LX,LY,s=7,c=C_LEAK,marker='s',lw=0,zorder=5)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(HAIR); s.set_linewidth(1.1)
    ax.set_title(title,fontsize=13,color=INK,fontweight='bold',loc='left',pad=17)
    ax.text(0,1.012,sub,transform=ax.transAxes,fontsize=9.6,color=INK2,va='bottom')
    st=dict(fontsize=9.4,color=INK,va='center',zorder=9,
            bbox=dict(boxstyle='round,pad=0.24',fc=SURF,ec=HAIR,lw=.8,alpha=.94))
    for lon,lat,t,dx,dy,ha in labels:
        x,y=fwd.transform(lon,lat)
        ax.annotate(t,(x,y),(x+dx*1000,y+dy*1000),textcoords='data',ha=ha,
                    arrowprops=dict(arrowstyle='-',color=MUTED,lw=.85,shrinkA=0,shrinkB=2),**st)
    return ax

panel(gs[0,0],(-133.4,56.30,-132.0,57.00),
      'Stikine delta / Dry Strait',
      '225.1 km² ftype-364 polygon labelled "Stikine River" — 264 leaked cells',
      [(-132.55,56.62,'Dry Strait',-13,-9,'right'),(-132.25,56.72,'Stikine R. flowline',11,8,'left'),
       (-132.96,56.81,'Petersburg',-11,8,'right'),(-132.42,56.53,'Sumner Strait',9,-11,'left')])
panel(gs[0,1],(-137.0,57.75,-134.8,58.45),
      'Cross Sound / Chatham Strait',
      '141.0 km² polygon labelled "Porcupine River" — 1,100 km from the Porcupine',
      [(-136.07,57.86,'Pelican',-11,-9,'right'),(-136.35,58.19,'Elfin Cove',-11,8,'right'),
       (-135.33,58.11,'Hoonah',11,-8,'left')])

# --- panel C: statewide ---
ax=fig.add_subplot(gs[1,0])
ax.imshow(np.where(water,0,1).astype(float),extent=EXT,origin='upper',
          cmap=matplotlib.colors.ListedColormap([WATER,LAND]),interpolation='nearest',zorder=0)
marine.plot(ax=ax,color=C_MAR,lw=.5,alpha=.4,zorder=1)
good.plot(ax=ax,fc=C_KEEP,ec='none',zorder=2)
fl.plot(ax=ax,color=C_FL,lw=.45,zorder=3)
bad.plot(ax=ax,fc=C_BAD,ec=C_BAD,lw=1.2,zorder=4)
ax.scatter(LX,LY,s=2.5,c=C_LEAK,marker='s',lw=0,zorder=5)
b=fl.total_bounds; ax.set_xlim(b[0]-80_000,b[2]+60_000); ax.set_ylim(b[1]-60_000,b[3]+80_000)
ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_color(HAIR); s.set_linewidth(1.1)
ax.set_title('All four, statewide',fontsize=13,color=INK,fontweight='bold',loc='left',pad=17)
ax.text(0,1.012,'963 polygons kept · 4 dropped, 371.3 km² · every one ftype 364 Lake/Pond',
        transform=ax.transAxes,fontsize=9.6,color=INK2,va='bottom')
for lon,lat,t,dx,dy,ha in [(-132.5,56.6,'Stikine',150,-60,'left'),(-136.0,58.0,'"Porcupine"',-150,60,'right'),
                           (-151.2,60.55,'Kenai',-150,-70,'right'),(-148.9,70.4,'Kuparuk',120,60,'left')]:
    x,y=fwd.transform(lon,lat)
    ax.annotate(t,(x,y),(x+dx*1000,y+dy*1000),textcoords='data',ha=ha,fontsize=9.4,color=INK,
                bbox=dict(boxstyle='round,pad=0.24',fc=SURF,ec=HAIR,lw=.8,alpha=.94),
                arrowprops=dict(arrowstyle='-',color=MUTED,lw=.85,shrinkA=0,shrinkB=2),zorder=9)

# --- panel D: the options ---
ax=fig.add_subplot(gs[1,1])
opts=[('keep all 967\n(pre-fix)',396,89.8),('drop the 4\n(shipped)',2,89.5),('flowlines only\n(rejected)',0,78.7)]
y=np.arange(len(opts))[::-1]
cols=[C_BAD,"#1baf7a","#eda100"]
ax.barh(y,[o[1] for o in opts],height=.5,color=cols,zorder=3)
for yy,(lab,leak,cov),c in zip(y,opts,cols):
    ax.text(leak+9,yy,f'{leak} marine cells leaked',va='center',fontsize=10.4,color=INK)
    ax.text(leak+9,yy-0.28,f'IDW coverage of river cells {cov}%',va='center',fontsize=9.4,color=MUTED)
ax.set_yticks(y); ax.set_yticklabels([o[0] for o in opts],fontsize=10)
ax.set_xlim(0,470); ax.set_xlabel('marine waterway cells inside the river-ice domain',fontsize=9.8,color=MUTED)
ax.tick_params(colors=MUTED,length=0,labelsize=9.8)
for s in ('top','right','left'): ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color(AXIS); ax.grid(axis='x',color=HAIR,lw=.8,zorder=0)
ax.set_title('Why four, and not none or all',fontsize=13,color=INK,fontweight='bold',loc='left',pad=17)
ax.text(0,1.012,'dropping the flowline half instead is clean but costs 9,661 river cells',
        transform=ax.transAxes,fontsize=9.6,color=INK2,va='bottom')

fig.text(0.03,0.963,'The marine clip: four Lake/Pond polygons that reach salt water',
         fontsize=19,color=INK,fontweight='bold')
fig.text(0.03,0.917,
 'NHDArea ftype 364 is not always a lake, and a polygon joins the river-ice mask WHOLE if any part of it falls within the 2 km reach-point or 500 m flowline buffer.\n'
 'Four large estuarine polygons were admitted that way, putting 396 cells of the marine waterway network inside the domain where river ice may gate a barge.',
 fontsize=10.6,color=INK2,va='top',linespacing=1.55)
h=[Patch(fc=C_KEEP,label='NHDArea polygon kept (963)'),
   Patch(fc=C_BAD,alpha=.6,label='polygon dropped by the marine clip (4)'),
   Line2D([],[],color=C_FL,lw=2.4,label='Brown flowline / river waterway'),
   Line2D([],[],color=C_MAR,lw=2.4,alpha=.85,label='marine waterway network'),
   Line2D([],[],marker='s',ls='',ms=7,mfc=C_LEAK,mec='none',label='leaked marine cell (396)')]
lg=fig.legend(handles=h,loc='upper left',bbox_to_anchor=(0.03,0.855),ncol=5,fontsize=9.8,
              frameon=True,facecolor=SURF,edgecolor=HAIR,borderpad=.7,labelspacing=.55)
lg.get_frame().set_linewidth(.8)
for t in lg.get_texts(): t.set_color(INK)
fig.text(0.03,0.013,'drop_marine_polygons() in build_brown_polygon_mask.py — removes any polygon intersecting an NWN segment whose KEY_ID is not in RIVER_SEGMENT_KEY_IDS',
         fontsize=8.8,color=MUTED)
fig.savefig(OUT,dpi=165,bbox_inches='tight',facecolor=SURF)
print(f'wrote {OUT} — {len(bad)} polygons dropped, {len(LX)} leaked cells shown')
