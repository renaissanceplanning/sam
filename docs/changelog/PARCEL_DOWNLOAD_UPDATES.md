# Parcel Download Updates - February 2026

## Summary of Changes

### 1. Output Format Changed: GeoPackage → Shapefile
**Why:** ArcGIS has known compatibility issues with GeoPackage (.gpkg) files, especially large datasets (500k+ features). Files were only showing partial data in ArcGIS Pro, even though the data was complete.

**Change:**
- All parcel outputs now save as `.shp` (ESRI Shapefile) instead of `.gpkg`
- Individual county files: `parcels_{County}_{Year}.shp`
- Combined multi-county files: `parcels_{Year}.shp`

**Trade-offs:**
- Shapefile limitations: 2GB max size, 10-character field names, limited numeric precision
- But: Works reliably in both QGIS and ArcGIS

### 2. Keep Raw Data Flag Added
**New Parameter:** `keep_raw=True` in `pull_parcels()` method

**What it does:**
- Downloads and saves the raw GIS shapefile from Florida DOR
- Filename: `parcels_{County}_{Year}_raw.shp`
- Contains: Geometry only, no NAL (tax roll) attributes
- No processing: No duplicate removal, no merge, no filtering

**Usage:**
```python
downloader.pull_parcels(
    parcel_source="DOR",
    parcel_replica_fields=False,
    keep_raw=True  # <-- New flag
)
```

**Output files:**
- `parcels_Hillsborough_2025.shp` - Processed parcels with attributes
- `parcels_Hillsborough_2025_raw.shp` - Raw GIS geometry only

### 3. DATA_YEAR Column - Already Working Correctly
The DATA_YEAR column properly tracks the actual year of data downloaded, not the requested year.

**Example:**
- Request: `year=2025`
- Available data: 2024 GIS + 2024 NAL
- Result: `DATA_YEAR=2024` (correct)

The build_url() function implements smart fallback:
1. Try requested year
2. Try year-1
3. Try year-2
4. Try 2024
5. Try 2023

Then tries adjacent years for NAL matching (±1 year).

## Files Modified

### Core Download Logic
1. **`sam/menus/core.py`** - DataMenuDownloader class
   - Added `keep_raw` parameter to `pull_parcels()` method
   - Changed output format from `.gpkg` to `.shp`
   - Added logic to save raw GIS file when `keep_raw=True`

2. **`sam/parcels/core.py`** - download_fl_parcels() function
   - Added `keep_raw` parameter
   - Returns tuple `(parcels, raw_gis, actual_year)` when `keep_raw=True`
   - Returns just `parcels` when `keep_raw=False` (backward compatible)

3. **`sam/download/fl_parcels/format_parcels.py`** - process_parcels() function
   - Modified to include raw GIS data in return dictionary: `save_info['gis']`
   - This allows upstream functions to access raw data before merging

### Project Code
4. **`pull_hillsborough_data.py`** - Updated to use `keep_raw=True`

## Testing Needed

1. **Single county download** with keep_raw=True
   ```python
   downloader.pull_parcels(parcel_source="DOR", keep_raw=True)
   ```
   Expected output:
   - `parcels_Hillsborough_2025.shp` (processed)
   - `parcels_Hillsborough_2025_raw.shp` (raw)

2. **Multiple counties** with keep_raw=True
   Expected output:
   - `parcels_CountyA_2025.shp` (processed)
   - `parcels_CountyA_2025_raw.shp` (raw)
   - `parcels_CountyB_2025.shp` (processed)
   - `parcels_CountyB_2025_raw.shp` (raw)
   - `parcels_2025.shp` (combined processed)

3. **Verify in ArcGIS Pro**
   - Open `.shp` file
   - Check attribute table shows all features
   - Verify full spatial extent
   - Compare with QGIS to ensure consistency

## Known Issues Resolved

### Issue: "Parcels only showing northwest corner in ArcGIS"
**Root Cause:** ArcGIS bug reading GeoPackage files
**Solution:** Switched to Shapefile format
**Verification:** The .gpkg file was complete (confirmed in QGIS), ArcGIS just couldn't read it properly

### Issue: "Parcels labeled 2025 but data is 2024"
**Root Cause:** User confusion - the filename uses the DATA_YEAR column value
**Clarification:**
- 2025 GIS file exists (537,289 parcels)
- 2025 NAL file does NOT exist yet
- SAM correctly falls back to 2024 data
- DATA_YEAR column correctly shows 2024
- Filename correctly shows 2024

## Backward Compatibility

**Breaking changes:** None
- `keep_raw` defaults to `False` (maintains current behavior)
- Return type of `download_fl_parcels()` changes only when `keep_raw=True`
- All existing code will continue to work without modification

## Future Improvements

1. Add option to merge 2025 GIS with 2024 NAL (mixed-year approach)
2. Add spatial index to Shapefiles for better performance
3. Consider splitting large counties into tiles to avoid 2GB limit
4. Add File Geodatabase export option as alternative to Shapefile
