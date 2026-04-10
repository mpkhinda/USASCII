import os
import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import xy
from rasterio.windows import Window
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
from scipy import stats
from tqdm import tqdm

# NLCD class and ASCII dictionaries
nlcd_classes = {
    11: "Open Water", 
    12: "Perennial Ice/Snow",
    21: "Developed, Open Space", 
    22: "Developed, Low Intensity",
    23: "Developed, Medium Intensity", 
    24: "Developed, High Intensity",
    31: "Barren Land (Rock/Sand/Clay)",
    41: "Deciduous Forest", 
    42: "Evergreen Forest", 
    43: "Mixed Forest",
    52: "Shrub/Scrub", 
    71: "Grassland/Herbaceous",
    81: "Pasture/Hay", 
    82: "Cultivated Crops",
    90: "Woody Wetlands", 
    95: "Emergent Herbaceous Wetlands",
}

ascii_map = {
    "Open Water": "~", 
    "Perennial Ice/Snow": "*",
    "Developed, Open Space": ".", 
    "Developed, Low Intensity": "▫",
    "Developed, Medium Intensity": "◻", 
    "Developed, High Intensity": "⊡",
    "Barren Land (Rock/Sand/Clay)": " ",
    "Deciduous Forest": "+", 
    "Evergreen Forest": "^", 
    "Mixed Forest": "×",
    "Shrub/Scrub": "·", 
    "Grassland/Herbaceous": ",",
    "Pasture/Hay": "-", 
    "Cultivated Crops": "=",
    "Woody Wetlands": "w", 
    "Emergent Herbaceous Wetlands": "v",
}

# Mode downsampling
def downsample_mode(src, factor):
    H, W = src.height, src.width
    H2, W2 = H // factor, W // factor
    out = np.zeros((H2, W2), dtype=src.dtypes[0])
    for i in tqdm(range(H2), desc="  rows", leave=False):
        block = src.read(1, window=Window(0, i * factor, W2 * factor, factor))
        block = block.reshape(factor, W2, factor).swapaxes(0, 1)
        flat = block.reshape(W2, -1)
        for j in range(W2):
            out[i, j] = np.bincount(flat[j]).argmax()
    new_transform = src.transform * src.transform.scale(factor, factor)
    return out, new_transform

# Create centroids for each pixel
def raster_to_centroids(path, factor):
    with rasterio.open(path) as src:
        arr, transform = downsample_mode(src, factor)
        crs = src.crs
    rows, cols = np.where(np.isin(arr, list(nlcd_classes.keys())))
    xs, ys = xy(transform, rows, cols)
    codes = [nlcd_classes[arr[r, c]] for r, c in zip(rows, cols)]
    return gpd.GeoDataFrame(
        {"LandCover": codes},
        geometry=[Point(x, y) for x, y in zip(xs, ys)],
        crs=crs,
    )

# Clip to lower 48 without water bodies
def load_lower48(shp="data/us_boundary/cb_2024_us_state_20m.shp", crs=None):
    states = gpd.read_file(shp)
    lower48 = states[~states["STUSPS"].isin(["AK", "HI", "PR"])].dissolve()
    if crs is not None:
        lower48 = lower48.to_crs(crs)
    return lower48

def clip_to_lower48(gdf, lower48):
    return gpd.sjoin(gdf, lower48[["geometry"]], predicate="within").drop(columns="index_right")

# Plot maps
def plot_ascii(gdf, year, out_path):
    fig, ax = plt.subplots(figsize=(8, 12), dpi=300)
    ax.set_xlim(gdf.geometry.x.min(), gdf.geometry.x.max())
    ax.set_ylim(gdf.geometry.y.min(), gdf.geometry.y.max())
    for code, group in gdf.groupby("LandCover"):
        char = ascii_map.get(code, " ")
        for _, row in group.iterrows():
            ax.text(row.geometry.x, row.geometry.y, char,
                    fontsize=4, fontfamily="monospace", ha="center", va="center")
    ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title(str(year), fontsize=4, fontfamily="monospace", loc="left")
    plt.savefig(out_path, bbox_inches="tight"); plt.close()


def run_pipeline(raster_dir, out_dir, native_res=30, target_res=30000):
    factor = target_res // native_res
    os.makedirs(out_dir, exist_ok=True)
    lower48 = None
    for fname in sorted(os.listdir(raster_dir)):
        if not fname.endswith(".tif"):
            continue
        year = "".join(c for c in fname if c.isdigit())[:4]
        gdf = raster_to_centroids(os.path.join(raster_dir, fname), factor)
        if lower48 is None:
            lower48 = load_lower48(crs=gdf.crs)
        gdf = clip_to_lower48(gdf, lower48)
        plot_ascii(gdf, year, os.path.join(out_dir, f"nlcd_{year}.png"))
        print(f"done {year}: {len(gdf)} pts")


if __name__ == "__main__":
    run_pipeline("./data/nlcd_rasters", "./data/nlcd_out")