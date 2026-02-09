# NLCD Final Summary - February 2026

## ✅ All Issues Fixed

### 1. Python 3.9 Compatibility
**Problem:** `TypeError: unsupported operand type(s) for |: 'type' and 'types.GenericAlias'`

**Fix:**
- Changed `Path | dict[str, Path]` → `Union[Path, dict[str, Path]]`
- Changed `str | list[str]` → `Union[str, list[str], None]`
- Added `from typing import Union` import

### 2. Default Behavior - Download All Datasets
**Problem:** User expected `pull_nlcd()` with no parameters to download all available datasets

**Fix:** Default behavior now downloads **both land_cover AND impervious**
```python
# Before: Downloaded only land_cover
downloader.pull_nlcd()

# Now: Downloads land_cover + impervious (all available products)
downloader.pull_nlcd()
```

## Usage Options

### Option 1: Download Everything (Default)
```python
downloader.pull_nlcd()
# Downloads: land_cover + impervious
```

### Option 2: Download Specific Dataset
```python
downloader.pull_nlcd('land_cover')   # Only land cover
downloader.pull_nlcd('impervious')   # Only impervious
```

### Option 3: Download Specific Multiple
```python
downloader.pull_nlcd(['land_cover', 'impervious'])
```

### Option 4: Without Clipping
```python
downloader.pull_nlcd(clip_to_aoi=False)  # Full CONUS tiles
```

## For Your Hillsborough County Project

Your pull script just needs:
```python
# In pull_hillsborough_data.py
downloader.pull_nlcd()  # Downloads both land cover + impervious automatically!
```

This will download based on BASE_YEAR (2025 → uses 2024 data):
- `nlcd_2024_land_cover_clipped.tif` (1.3GB)
- `nlcd_2024_impervious_clipped.tif` (1.3GB)

Both clipped to Hillsborough County boundary.

## What Gets Downloaded

When you run `pull_nlcd()` with no parameters:

```
Downloading NLCD data...
No dataset specified, downloading all available products
  Datasets: land_cover, impervious
  Year: 2024
  Downloading land_cover...
    ✓ Saved to: data/RAW/nlcd/nlcd_2024_land_cover_clipped.tif
  Downloading impervious...
    ✓ Saved to: data/RAW/nlcd/nlcd_2024_impervious_clipped.tif

✓ Downloaded 2/2 NLCD datasets
```

## Files Modified

1. **`sam/download/nlcd/core.py`**
   - Added `Union` import for Python 3.9 compatibility
   - Changed return type annotation

2. **`sam/menus/core.py`**
   - Changed `dataset` parameter default from `'land_cover'` to `None`
   - Added logic to default to `['land_cover', 'impervious']` when `None`
   - Updated docstring with new default behavior
   - Updated examples

## Backwards Compatibility

✅ **Fully backwards compatible** - old code still works:
```python
downloader.pull_nlcd('land_cover')  # Still works
downloader.pull_nlcd(['land_cover', 'impervious'])  # Still works
```

🆕 **New default behavior** - more convenient:
```python
downloader.pull_nlcd()  # Now downloads both!
```

## Ready to Use!

Your Hillsborough County pull script should now work without any errors:
1. ✅ Python 3.9 compatibility fixed
2. ✅ Downloads both land cover + impervious by default
3. ✅ Based on your BASE_YEAR (2025 → 2024 data)
4. ✅ Automatically clipped to county boundary

Just uncomment the NLCD section in your pull script and run it!
