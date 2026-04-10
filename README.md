# USASCII 

🇺🇸 🗺️ -> 🔢  
An ASCII visualization of U.S. land cover maps over time.

[gif of output will go here]

### Setup

Requires [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/download).

```bash
conda env create -f environment.yml
conda activate nlcd
```

### Data

**Land Cover Data -** Download annual NLCD CONUS GeoTIFFs from [MRLC](https://www.mrlc.gov/data) (Projects = Annual NLCD, Products = Land Cover) and place them in `data/nlcd_rasters/`. Files are several GB each and not tracked in this repo.

**US Boundary -** Download a US boundary shapefile for clipping from the [Census TIGER site](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) (labeled 'States 1:20,000,000 (national)') and place in `data/us_boundary/`.

### Usage

```bash
python USASCII_Script.py
```

Outputs one PNG and one GeoPackage per year to `data/nlcd_out/`.

### How it works

1. Reads each annual NLCD raster
2. Downsamples 30m → 30km via nearest-neighbor
3. Extracts centroids for each downsampled pixel
4. Clips to CONUS boundary
5. Plots each land cover class as an ASCII character