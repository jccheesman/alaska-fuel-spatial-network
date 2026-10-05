#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""plot_mask_construction.py — how the river-ice mask is built, on real geometry.

Six panels over one 90 km window, every layer read from the file the pipeline
actually consumes rather than redrawn schematically:

    1  inputs      NHDFlowline (30 Brown rivers) + NHDArea polygons + reach points
    2  buffers     2 km around each reach point, 500 m around each flowline
    3  union       which of the two criteria kept each polygon (or both)
    4  river mask  polygons UNION 200 m flowline buffer = arcpy env.mask
    5  p_ice       the interpolated field inside that mask
    6  provenance  1 = polygon median, 2 = IDW, 3 = NN fallback

Panels 5-6 read the arcpy outputs directly, so this doubles as a check that
the mask and the raster agree.

Inputs live under friction_preprocessing/data/ and the friction raster tree —
see friction_preprocessing/README.md. Defaults assume the documented layout;
override with the flags if yours differs.

Usage:
    python plot_mask_construction.py
    python plot_mask_construction.py --month 1 --lon -159.5 --lat 61.58   # Aniak
    python plot_mask_construction.py --half-km 60 --out figs/mask.png

Palette validated with the dataviz validator (all-pairs, #fcfcfb surface).
"""

import argparse
import numpy as np, matplotlib, pyproj, warnings
matplotlib.use('Agg'); warnings.filterwarnings('ignore')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, BoundaryNorm
import geopandas as gpd, rasterio
from rasterio.windows import from_bounds
from shapely.ops import unary_union

ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--data', default='source_scripts/friction_surface/friction_preprocessing/data',
                help='holds waterFilledMedians2000_2023.geojson, brown_river_flowlines/, brown_river_polygons/')
ap.add_argument('--rasters', default='inputs/friction_rasters/river_ice',
                help='river_ice_MM.tif; provenance_MM.tif is looked for in ./provenance under this')
ap.add_argument('--month', type=int, default=10, help='default 10 — freeze-up, so p_ice still varies')
ap.add_argument('--lon', type=float, default=-149.10)
ap.add_argument('--lat', type=float, default=64.56)
ap.add_argument('--half-km', type=float, default=45.0)
ap.add_argument('--out', default='outputs/analysis/river_ice_mask_construction.png')
args=ap.parse_args()
import os
D=args.data; R=args.rasters; MM=f'{args.month:02d}'
SURF="#fcfcfb"; INK="#0b0b0b"; INK2="#52514e"; MUTED="#898781"; HAIR="#e1e0d9"
LAND="#f2f1ec"
C_FL="#2a78d6"; C_PT="#0d366b"; C_POLY="#86b6ef"; C_BUF="#eda100"; C_MASK="#4a3aa7"
P1,P2,P3="#1baf7a","#2a78d6","#eb6834"
plt.rcParams.update({"font.family":["DejaVu Sans"],"figure.facecolor":SURF,
                     "axes.facecolor":SURF,"savefig.facecolor":SURF})
ICE=LinearSegmentedColormap.from_list('ice',["#cde2fb","#9ec5f4","#5598e7","#256abf","#0d366b"])

fwd=pyproj.Transformer.from_crs('EPSG:4326','EPSG:3338',always_xy=True)
CX,CY=fwd.transform(args.lon,args.lat); H=args.half_km*1000
BOX=(CX-H,CY-H,CX+H,CY+H)

pts=gpd.read_file(os.path.join(D,'waterFilledMedians2000_2023.geojson'))
jan=pts[pts['month']==args.month].drop_duplicates('ReachID').copy()
jan['p_ice']=(1-jan['areaPropMedWater']).clip(0,1)
fl=gpd.read_file(os.path.join(D,'brown_river_flowlines','brown_river_flowlines.shp')).to_crs(3338)
poly=gpd.read_file(os.path.join(D,'brown_river_polygons','brown_river_polygons.shp')).to_crs(3338)
jl=jan.cx[BOX[0]:BOX[2],BOX[1]:BOX[3]]; fll=fl.cx[BOX[0]:BOX[2],BOX[1]:BOX[3]]
pll=poly.cx[BOX[0]:BOX[2],BOX[1]:BOX[3]]

def rd(path,box):
    s=rasterio.open(path)
    w=from_bounds(*box,transform=s.transform)
    a=s.read(1,window=w,boundless=True,fill_value=s.nodata if s.nodata is not None else 0)
    return a,[box[0],box[2],box[1],box[3]]
ice,ext_i=rd(os.path.join(R,f'river_ice_{MM}.tif'),BOX)
prov,ext_p=rd(os.path.join(R,'provenance',f'provenance_{MM}.tif'),BOX)
ice=np.where(ice==-9999,np.nan,ice)
prov=np.where(prov==0,np.nan,prov)

fig=plt.figure(figsize=(15.2,10.9),dpi=165)
gs=fig.add_gridspec(2,3,hspace=0.15,wspace=0.06,left=0.028,right=0.988,top=0.795,bottom=0.055)
def base(ax,title,sub):
    ax.add_patch(Rectangle((BOX[0],BOX[1]),BOX[2]-BOX[0],BOX[3]-BOX[1],fc=LAND,ec='none',zorder=0))
    ax.set_xlim(BOX[0],BOX[2]); ax.set_ylim(BOX[1],BOX[3])
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_color(HAIR); s.set_linewidth(1.1)
    ax.set_title(title,fontsize=13,color=INK,fontweight='bold',loc='left',pad=17)
    ax.text(0,1.012,sub,transform=ax.transAxes,fontsize=9.6,color=INK2,va='bottom')

# 1 inputs
ax=fig.add_subplot(gs[0,0]); base(ax,'1 · Inputs','NHD flowlines + NHDArea polygons + Brown reach points')
pll.plot(ax=ax,fc=C_POLY,ec='none',alpha=.75,zorder=1)
fll.plot(ax=ax,color=C_FL,lw=1.0,zorder=2)
ax.scatter(jl.geometry.x,jl.geometry.y,s=46,c=jl['p_ice'],cmap=ICE,vmin=0,vmax=1,
           ec=INK,lw=.7,zorder=4)
# 2 buffers
ax=fig.add_subplot(gs[0,1]); base(ax,'2 · Buffers','2 km around each reach point · 500 m around each flowline')
from matplotlib.collections import PatchCollection
from matplotlib.patches import Circle
ax.add_collection(PatchCollection([Circle((p.x,p.y),2000) for p in jl.geometry],
                  facecolor='none',edgecolor=C_BUF,lw=1.1,linestyle=(0,(4,2)),zorder=3))
gpd.GeoSeries([unary_union(fll.geometry.buffer(500).values)],crs=3338).plot(ax=ax,fc=C_BUF,ec='none',alpha=.30,zorder=2)
pll.plot(ax=ax,fc='none',ec=C_POLY,lw=1.0,zorder=1)
fll.plot(ax=ax,color=C_FL,lw=.7,zorder=4)
ax.scatter(jl.geometry.x,jl.geometry.y,s=13,c=C_PT,zorder=5)
# 3 union
ax=fig.add_subplot(gs[0,2]); base(ax,'3 · Union — which criterion kept each polygon','reach-point buffer, flowline buffer, or both')
pbuf=unary_union(jl.geometry.buffer(2000).values); fbuf=unary_union(fll.geometry.buffer(500).values)
CA,CB,CC="#eda100","#1baf7a","#4a3aa7"
cnt={'a':0,'b':0,'both':0}
for g in pll.geometry:
    ha,hb=g.intersects(pbuf),g.intersects(fbuf)
    k='both' if (ha and hb) else ('a' if ha else 'b'); cnt[k]+=1
    gpd.GeoSeries([g],crs=3338).plot(ax=ax,fc={'a':CA,'b':CB,'both':CC}[k],ec='none',alpha=.85,zorder=2)
fll.plot(ax=ax,color=C_FL,lw=.7,alpha=.5,zorder=3)
lg3=ax.legend(handles=[Patch(fc=CA,label=f'reach-point buffer only ({cnt["a"]})'),
                       Patch(fc=CB,label=f'flowline buffer only ({cnt["b"]})'),
                       Patch(fc=CC,label=f'both ({cnt["both"]})')],
              loc='lower left',fontsize=9.2,frameon=True,facecolor=SURF,edgecolor=HAIR,
              borderpad=.6,labelspacing=.5)
lg3.get_frame().set_linewidth(.8)
for t in lg3.get_texts(): t.set_color(INK)
# 4 mask
ax=fig.add_subplot(gs[1,0]); base(ax,'4 · River mask','polygons ∪ 200 m flowline buffer — arcpy env.mask')
gpd.GeoSeries([unary_union(list(pll.geometry)+list(fll.geometry.buffer(200)))],crs=3338).plot(
    ax=ax,fc=C_MASK,ec='none',alpha=.92,zorder=2)
# 5 interpolated
ax=fig.add_subplot(gs[1,1]); base(ax,'5 · Interpolated p_ice — October (freeze-up)','zonal median → IDW (power 2, 12 pts, 50 km) → NN fill')
im=ax.imshow(ice,extent=ext_i,origin='upper',cmap=ICE,vmin=0,vmax=1,interpolation='nearest',zorder=2)
cax=ax.inset_axes([0.04,0.06,0.34,0.032])
cb=fig.colorbar(im,cax=cax,orientation='horizontal'); cb.outline.set_edgecolor(HAIR)
cb.set_ticks([0,1]); cb.ax.set_xticklabels(['open','frozen'],fontsize=8.6,color=INK2)
cb.ax.tick_params(length=0)
# 6 provenance
ax=fig.add_subplot(gs[1,2]); base(ax,'6 · Provenance','which stage produced each cell')
ax.imshow(prov,extent=ext_p,origin='upper',cmap=ListedColormap([P1,P2,P3]),
          norm=BoundaryNorm([.5,1.5,2.5,3.5],3),interpolation='nearest',zorder=2)
lg=ax.legend(handles=[Patch(fc=P1,label='1 · polygon median'),Patch(fc=P2,label='2 · IDW'),
                      Patch(fc=P3,label='3 · NN fallback')],loc='lower left',fontsize=9.4,
             frameon=True,facecolor=SURF,edgecolor=HAIR,borderpad=.6,labelspacing=.5)
lg.get_frame().set_linewidth(.8)
for t in lg.get_texts(): t.set_color(INK)

fig.text(0.028,0.962,'How the river-ice mask is built, and what gets interpolated inside it',
         fontsize=19,color=INK,fontweight='bold')
fig.text(0.028,0.918,
 'Real geometry, 90 km square at the Tanana–Nenana confluence (64.56N 149.10W). Every layer is the file the pipeline actually reads: '
 f'{len(fll)} NHD flowlines, {len(pll)} NHDArea polygons, {len(jl)} Brown reach points.\n'
 'Point colour is October p_ice = clamp(1 − areaPropMedWater, 0, 1) — freeze-up, so values still vary. '
 f'Panels 5–6 are the arcpy outputs river_ice_{MM}.tif and provenance_{MM}.tif, read directly.',
 fontsize=10.6,color=INK2,va='top',linespacing=1.55)
h=[Line2D([],[],marker='o',ls='',ms=8,mfc="#5598e7",mec=INK,mew=.7,label='Brown reach point (colour = p_ice)'),
   Line2D([],[],color=C_FL,lw=2.2,label='NHDFlowline, 30 Brown rivers'),
   Patch(fc=C_POLY,label='NHDArea polygon (ftype 460 / 364)'),
   Patch(fc=C_BUF,alpha=.45,label='join buffer'),
   Patch(fc=C_MASK,alpha=.9,label='river mask')]
lg=fig.legend(handles=h,loc='upper left',bbox_to_anchor=(0.028,0.878),ncol=5,fontsize=9.8,
              frameon=True,facecolor=SURF,edgecolor=HAIR,borderpad=.7,labelspacing=.55)
lg.get_frame().set_linewidth(.8)
for t in lg.get_texts(): t.set_color(INK)
fig.text(0.028,0.014,'build_brown_polygon_mask.py (geopandas) → river_ice_full_pipeline.py (arcpy) · '
         'waterFilledMedians2000_2023.geojson, Brown et al. 2026 · NHD_H_Alaska_State_Shape',
         fontsize=8.8,color=MUTED)
os.makedirs(os.path.dirname(args.out) or '.',exist_ok=True)
fig.savefig(args.out,dpi=165,bbox_inches='tight',facecolor=SURF)
print(f'wrote {args.out} — {len(fll)} flowlines, {len(pll)} polygons, {len(jl)} reach points')
