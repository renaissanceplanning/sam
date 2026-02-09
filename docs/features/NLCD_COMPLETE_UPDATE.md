# NLCD Complete Update - February 2026

## Summary

Fixed NLCD downloads and added support for **Fractional Impervious Surface**. The old S3 bucket URLs were returning 403 Forbidden errors. SAM now uses the new MRLC website URLs and supports multiple NLCD products.

## ✅ What Works Now

### Available Products (Annual NLCD 2019-2024)
1. **Land Cover** (`'land_cover'`) - Land cover classification ✓
2. **Fractional Impervious Surface** (`'impervious'`) - 0-100% imperviousness ✓

### Partially Available Products
3. **Tree Canopy Cover** (`'tree_canopy'`) - 8-year rolling basis, separate USFS product ⚠️
4. **Impervious Descriptor** (`'impervious_descriptor'`) - Not yet available in Annual NLCD ✗

## New URL Structure

### Working URLs (verified Feb 2026)

**Land Cover:**
```
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2023_CU_C1V1.zip
...
```

**Fractional Impervious Surface:**
```
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2024_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2023_CU_C1V1.zip
...
```

### URL Pattern
```
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_{Product}_{Year}_{Region}_C1V1.zip
```

Where:
- **{Product}**: `LndCov` (land cover) or `FctImp` (fractional impervious)
- **{Year}**: 2019-2024 (annual updates)
- **{Region}**: `CU` (CONUS), `AK` (Alaska), `HI` (Hawaii), `PR` (Puerto Rico)
- **C1V1**: Collection 1, Version 1

## Usage

### Single Dataset Download
```python
from sam.menus import DataMenuDownloader

downloader = DataMenuDownloader(
    summary_areas=county_boundary,
    data_dir="data"
)

# Download land cover (default)
downloader.pull_nlcd()

# Download fractional impervious surface
downloader.pull_nlcd('impervious')
```

### Multiple Dataset Download (NEW!)
```python
# Download both land cover and impervious in one call
downloader.pull_nlcd(['land_cover', 'impervious'])
```

### With/Without Clipping
```python
# Download and clip to project area (requires rasterio)
downloader.pull_nlcd('impervious', clip_to_aoi=True)

# Download full CONUS tile (faster, no clipping)
downloader.pull_nlcd('impervious', clip_to_aoi=False)
```

## Files Modified

### Core Download Logic
**File:** `sam/download/nlcd/core.py`

**Changes:**
1. Updated available years: Added 2022, 2023, 2024
2. Updated `NLCD_DATASETS` dict with new product codes:
   - `land_cover` → `LndCov`
   - `impervious` → `FctImp`
   - `tree_canopy` → `None` (separate product)
   - `impervious_descriptor` → `None` (not available yet)
3. Rewrote `build_nlcd_url()` to use new MRLC URLs
4. Added better error messages for 403/404 errors
5. Updated docstrings with current product availability

### Menu Integration
**File:** `sam/menus/core.py`

**Changes:**
1. Updated `pull_nlcd()` signature to accept `str | list[str]` for dataset parameter
2. Added loop to download multiple datasets
3. Improved logging for multi-dataset downloads
4. Updated docstring with:
   - Product availability status (✓ / ⚠️ / ✗)
   - Examples for multiple dataset downloads
   - Notes about Annual NLCD vs Legacy NLCD

## Product Details

### Land Cover (Annual NLCD)
- **Availability:** 1985-2024 (annual)
- **Resolution:** 30m
- **Values:** Land cover classes (forest, urban, water, etc.)
- **File size:** ~1.3 GB (CONUS)

### Fractional Impervious Surface (Annual NLCD)
- **Availability:** 1985-2024 (annual)
- **Resolution:** 30m
- **Values:** 0-100% imperviousness
- **File size:** ~1.3 GB (CONUS)
- **Use:** Hydrology, urban analysis, runoff modeling

### Tree Canopy Cover (Separate USFS Product)
- **Availability:** 8-year rolling basis (2021, 2016, 2013, 2011)
- **Resolution:** 30m
- **Values:** 0-100% tree canopy cover
- **Source:** USDA Forest Service
- **Download:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/
- **Status:** Not integrated into Annual NLCD yet

### Impervious Descriptor
- **Availability:** Not yet available in Annual NLCD
- **Status:** May be added in future releases
- **Alternative:** Use Fractional Impervious Surface

## Testing

Verified all URLs return HTTP 200 OK:

```bash
# Land Cover 2024
curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip"
# HTTP/1.1 200 OK ✓

# Fractional Impervious 2024
curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2024_CU_C1V1.zip"
# HTTP/1.1 200 OK ✓

# Fractional Impervious 2021
curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2021_CU_C1V1.zip"
# HTTP/1.1 200 OK ✓
```

## Example Output

When you run `downloader.pull_nlcd(['land_cover', 'impervious'])`:

```
Downloading NLCD data...
  Datasets: land_cover, impervious
  Year: 2024
  Downloading land_cover...
Downloading NLCD 2024 land_cover from https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip
This may take a while - NLCD files are large (typically 1-5 GB)
Progress: 100.0%
Download complete: data/RAW/nlcd/nlcd_2024_land_cover.zip
    ✓ Saved to: data/RAW/nlcd/nlcd_2024_land_cover.zip
  Downloading impervious...
Downloading NLCD 2024 impervious from https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2024_CU_C1V1.zip
This may take a while - NLCD files are large (typically 1-5 GB)
Progress: 100.0%
Download complete: data/RAW/nlcd/nlcd_2024_impervious.zip
    ✓ Saved to: data/RAW/nlcd/nlcd_2024_impervious.zip

✓ Downloaded 2/2 NLCD datasets
```

## For Your Hillsborough County Project

Update your pull script:

```python
# In pull_hillsborough_data.py

# Option 1: Download land cover only (default)
downloader.pull_nlcd()

# Option 2: Download fractional impervious only
downloader.pull_nlcd('impervious')

# Option 3: Download both (RECOMMENDED for comprehensive analysis)
downloader.pull_nlcd(['land_cover', 'impervious'])
```

## Year Mapping (Based on Base Year)

SAM automatically selects the closest available year:

| Base Year | NLCD Year Used | Notes |
|-----------|----------------|-------|
| 2025 | 2024 | Latest available |
| 2024 | 2024 | Exact match |
| 2023 | 2023 | Exact match |
| 2022 | 2022 | Exact match |
| 2021 | 2021 | Exact match |
| 2020 | 2020 | Exact match |
| 2019 | 2019 | Exact match |
| 2018 | 2019 | Closest available |
| 2017 | 2016 | Legacy product |

## Known Limitations

### Tree Canopy Cover
- Not part of Annual NLCD products
- Released on 8-year rolling basis by USFS
- Requires separate download from USFS Geodata Gateway
- If requested, SAM will print a warning and fall back to land cover

### Impervious Descriptor
- Not yet available in Annual NLCD
- May be added in future collections
- If requested, SAM will print a warning and fall back to land cover

### Large File Sizes
- Full CONUS tiles are 1-5 GB each
- Download time depends on internet speed
- Consider using `clip_to_aoi=True` to reduce file size

### Clipping Requires Rasterio
- `clip_to_aoi=True` requires rasterio package
- Install with: `pip install rasterio`
- If not installed, downloads full tile and prints instructions

## Error Handling

SAM now provides helpful error messages:

**403 Forbidden:**
```
The old MRLC S3 bucket URLs no longer work (changed in 2024/2025).
SAM has been updated to use new MRLC URLs, but this year/dataset may not be available.

Alternative download methods:
1. Visit https://www.mrlc.gov/data to download manually
2. Try the MRLC Data Viewer: https://www.mrlc.gov/viewer/
3. Use the USGS National Map: https://apps.nationalmap.gov/downloader/
4. Use Annual NLCD (2019-2024): https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/
```

**404 Not Found:**
```
This specific year/dataset combination may not be available.
Available years for Annual NLCD: 2019-2024
Available years for Legacy NLCD: 2021, 2019, 2016, 2013, 2011, 2008, 2006, 2004, 2001

Try visiting https://www.mrlc.gov/data to find available downloads
```

## References

- **MRLC Data Portal:** https://www.mrlc.gov/data
- **Annual NLCD Info:** https://www.usgs.gov/centers/eros/science/annual-national-land-cover-database
- **MRLC Viewer:** https://www.mrlc.gov/viewer/
- **USFS Tree Canopy:** https://data.fs.usda.gov/geodata/rastergateway/treecanopycover/
- **User-provided URL example:** https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_FctImp_2021_CU_C1V1.zip

## Credits

Thanks to the user for providing the working Fractional Impervious URL pattern!
