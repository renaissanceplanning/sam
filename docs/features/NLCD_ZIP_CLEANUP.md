# NLCD Automatic Zip Cleanup - Added

## What Changed

The NLCD downloader now **automatically deletes zip files** after successful clipping to save disk space.

## Behavior

### When `clip_to_aoi=True` (default):
1. Downloads zip file (~1-4 GB)
2. Extracts and clips raster to your boundary
3. Saves clipped GeoTIFF
4. **Deletes original zip file** ← NEW!
5. Prints confirmation: "Deleted original zip file: {name} (saved ~X.X GB)"

### When `clip_to_aoi=False`:
- Downloads zip file
- **Keeps zip file** (no clipping performed)
- You must manually extract and process

## Disk Space Savings

For your Hillsborough County project with all 3 NLCD products:

**Before (kept zips):**
- Land Cover zip: 1.3 GB
- Impervious zip: 1.3 GB
- Tree Canopy zip: 3.6 GB
- Clipped TIFs: ~2-3 GB
- **Total: ~9 GB**

**After (deletes zips automatically):**
- Land Cover clipped: ~800 MB
- Impervious clipped: ~800 MB
- Tree Canopy clipped: ~1.2 GB
- **Total: ~3 GB**

**Space saved: ~6 GB** 💾

## Error Handling

If zip deletion fails for any reason:
- Prints a warning message
- Continues normally (doesn't crash)
- You still get your clipped raster
- Zip file remains (you can manually delete it)

## Example Output

```
Downloading NLCD 2024 land_cover from https://...
This may take a while - NLCD files are large (typically 1-5 GB)
Progress: 100.0%
Download complete: data/RAW/nlcd/nlcd_2024_land_cover.zip

Clipping raster to area of interest...
Clipped raster saved to: data/RAW/nlcd/nlcd_2024_land_cover_clipped.tif
Deleted original zip file: nlcd_2024_land_cover.zip (saved ~1.3 GB)  ← NEW!
    ✓ Saved to: data/RAW/nlcd/nlcd_2024_land_cover_clipped.tif
```

## Files Modified

**`sam/download/nlcd/core.py`**
- Added `output_path.unlink()` after successful clipping
- Added try/except to handle deletion errors gracefully
- Prints confirmation with file size saved

**`sam/menus/core.py`**
- Updated docstring: "deletes zips" vs "keeps zips"

## For Your Project

Since your pull script uses default settings:
```python
downloader.pull_nlcd()  # Uses clip_to_aoi=True by default
```

You'll automatically get:
- ✅ All 3 products clipped to Hillsborough County
- ✅ Zip files deleted after clipping
- ✅ ~6 GB disk space saved
- ✅ Only keeps the clipped TIFs you actually need

## If You Want to Keep Zips

If you ever need to keep the original zip files:
```python
downloader.pull_nlcd(clip_to_aoi=False)  # Keeps zips, no clipping
```

Then manually extract and clip later if needed.
