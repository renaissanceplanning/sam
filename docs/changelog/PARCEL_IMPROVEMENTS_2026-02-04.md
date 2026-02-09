# Parcel Download Improvements - 2026-02-04

## Issues Fixed

### 1. **Only Download Specified County (Not Neighbors)**

**Problem**: When providing Hillsborough County boundary, SAM downloaded parcels for 6 counties (Hardee, Pinellas, Pasco, Hillsborough, Polk, Manatee) because the boundary slightly overlapped with neighbors.

**Root Cause**: `extract_fips()` used `.intersects()` which returns ALL counties that touch the boundary, even slightly.

**Fix**: Updated `extract_fips()` to use the county with the **largest overlap area**:

```python
# Find all intersecting counties
intersecting = county_shapes[county_shapes.intersects(dissolved)]

if len(intersecting) == 1:
    # Only one county intersects - use it
    county = intersecting
else:
    # Multiple counties intersect - use the one with largest overlap
    intersecting['overlap_area'] = intersecting.geometry.intersection(dissolved).area
    county = intersecting.nlargest(1, 'overlap_area')
```

**Result**: Now only downloads Hillsborough County when that's the primary area of interest.

---

### 2. **Correct Year in Filename**

**Problem**: Parcels downloaded for 2025 were saved as `parcels_2022.shp` (using base_year instead of actual data year).

**Root Cause**: Filename used `self.years["parcel_year"]` (the requested year) instead of the actual year downloaded. Since `download_fl_parcels()` forces the year to `date.today().year - 1`, the actual data is always from 2025 (in 2026).

**Fix**: Track and use the actual year downloaded:

```python
from datetime import date
actual_year = date.today().year - 1  # What download_fl_parcels actually uses

# Save with correct year
output_file = par_dir / f"parcels_{actual_year}.gpkg"
```

**Result**: Files now correctly named `parcels_2025.gpkg` when 2025 data is downloaded.

---

### 3. **Switch to GeoPackage Format**

**Problem**: Shapefile format has severe limitations:
- ❌ **2GB file size limit** - Hit with 1.9M parcels from 6 counties
- ❌ **Field names truncated to 10 characters** - Lost meaningful column names
- ❌ **Numeric precision issues** - Large values like `$957,016,742` couldn't be stored properly
- ❌ **DBF format warnings** - 100+ warnings during save

**Fix**: Switched from Shapefile (.shp) to GeoPackage (.gpkg) format:

```python
# Old:
output_file = par_dir / f"parcels_{actual_year}.shp"
parcels.to_file(output_file)

# New:
output_file = par_dir / f"parcels_{actual_year}.gpkg"
parcels.to_file(output_file, driver='GPKG')
```

**GeoPackage Advantages**:
- ✅ **No file size limit** - Can handle millions of parcels
- ✅ **Full field names** - No 10-character limit
- ✅ **Better numeric precision** - Handles large values correctly
- ✅ **Single file** - Unlike shapefile's 4-7 files
- ✅ **Modern standard** - SQLite-based, widely supported
- ✅ **Faster** - Better performance for large datasets

**Compatibility**: GeoPackage is supported by:
- QGIS, ArcGIS Pro, ArcGIS Online
- GeoPandas, GDAL, QGIS
- PostGIS, SpatiaLite
- All modern GIS software

**Result**: Clean save with no warnings, all data preserved correctly.

---

## Example Output (Before vs After)

### Before:
```
Downloading 6 counties: Hardee, Pinellas, Pasco, Hillsborough, Polk, Manatee
...
✓ Combined total: 1,928,120 parcels
Saving to: parcels_2022.shp
[100+ warnings about truncated fields, numeric overflow, 2GB limit]
```

### After:
```
Downloading 1 county: Hillsborough
...
✓ Combined total: 523,644 parcels
Saving to: parcels_2025.gpkg
✓ Saved 523,644 parcels to parcels_2025.gpkg
   (Using GeoPackage format - no 2GB limit, full field names preserved)
```

---

## Files Modified

1. **`sam/config/helper_functions.py`**
   - `extract_fips()` - Use largest overlap county instead of all intersecting

2. **`sam/menus/core.py`**
   - `pull_parcels()` - Track actual year downloaded
   - Changed output format from `.shp` to `.gpkg`
   - Added progress messages

---

## Migration Guide

If you have scripts expecting `.shp` files:

```python
# Old code:
parcels = gpd.read_file("parcels_2022.shp")

# New code (works with both formats):
parcels = gpd.read_file("parcels_2025.gpkg")
```

GeoPackage is read the same way - no code changes needed!

---

## Future Improvements

Consider adding an option to specify output format:

```python
downloader.pull_parcels(
    parcel_source="DOR",
    output_format="gpkg"  # or "shp", "geojson", "parquet"
)
```

This would allow users to choose based on their workflow needs.

---

*Last Updated: 2026-02-04*
