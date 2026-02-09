# NLCD XML Metadata Preservation

## What Changed

The NLCD downloader now **preserves and renames XML metadata files** to match the clipped raster filename.

## Why This Matters

XML files in NLCD zips contain valuable information:
- **Metadata**: FGDC/ISO metadata (data source, processing history, lineage)
- **Symbology**: Color ramps and classification schemes for display
- **Projection**: Coordinate system details
- **Attribute definitions**: What each raster value means

Without these files, GIS software loses:
- Proper color styling (defaults to grayscale)
- Metadata documentation
- Value definitions

## What Happens Now

### Before (without XML):
```
data/RAW/nlcd/
└── nlcd_2024_land_cover_clipped.tif
```
**Problem:** Opens in GIS with generic grayscale, no metadata

### After (with XML):
```
data/RAW/nlcd/
├── nlcd_2024_land_cover_clipped.tif
└── nlcd_2024_land_cover_clipped.tif.xml  ← Preserved and renamed!
```
**Result:** Opens in GIS with proper NLCD color scheme and full metadata

## How It Works

1. Downloads zip file (e.g., `Annual_NLCD_LndCov_2024_CU_C1V1.zip`)
2. Extracts to temporary directory
3. Finds raster file (`.tif` or `.img`)
4. **Finds XML files** (`.xml` extensions)
5. Clips raster to your boundary
6. Saves as `nlcd_2024_land_cover_clipped.tif`
7. **Copies XML and renames** to `nlcd_2024_land_cover_clipped.tif.xml`
8. Deletes temp directory and original zip

## Expected Console Output

```
Downloading NLCD 2024 land_cover...
Progress: 100.0%
Download complete: nlcd_2024_land_cover.zip

Clipping raster to area of interest...
Clipped raster saved to: nlcd_2024_land_cover_clipped.tif
  Copied metadata: nlcd_2024_land_cover_clipped.tif.xml  ← NEW!
Deleted original zip file: nlcd_2024_land_cover.zip (saved ~1.3 GB)
```

## Benefits for Your Project

### 1. Proper Symbology in ArcGIS/QGIS
- Land Cover: Opens with standard NLCD colors (green=forest, red=urban, etc.)
- Impervious: Opens with percentage gradient (0-100%)
- Tree Canopy: Opens with canopy percentage colors

### 2. Complete Metadata
- Data source information
- Processing date
- Spatial resolution
- Coordinate system details
- Citation information

### 3. Value Definitions
XML contains lookup tables like:
```xml
<attr>
  <attrlabl>Value</attrlabl>
  <attrdef>NLCD Land Cover Class</attrdef>
  <attrdomv>
    <edom>
      <edomv>11</edomv>
      <edomvd>Open Water</edomvd>
    </edom>
    <edom>
      <edomv>21</edomv>
      <edomvd>Developed, Open Space</edomvd>
    </edom>
    ...
  </attrdomv>
</attr>
```

## Files Modified

**`sam/download/nlcd/core.py`**
- Added logic to find XML files in zip
- Added copying and renaming of XML files after clipping
- Updated docstring to mention XML preservation

## Example: Opening in ArcGIS

**Without XML:**
```
File → Add Data → nlcd_2024_land_cover_clipped.tif
Result: Grayscale raster, no metadata
```

**With XML:**
```
File → Add Data → nlcd_2024_land_cover_clipped.tif
Result: Full NLCD colors, complete metadata in properties!
ArcGIS automatically reads the .tif.xml file
```

## Example: Opening in QGIS

**Without XML:**
```
Displays with single-band grayscale
No metadata in layer properties
```

**With XML:**
```
Reads symbology from XML
Shows metadata in "Information" tab
Applies standard NLCD color scheme
```

## For All Three NLCD Products

Your Hillsborough County downloads will now include XML for:

1. **Land Cover**
   - `nlcd_2024_land_cover_clipped.tif`
   - `nlcd_2024_land_cover_clipped.tif.xml` ← Colors for 20+ land cover classes

2. **Fractional Impervious**
   - `nlcd_2024_impervious_clipped.tif`
   - `nlcd_2024_impervious_clipped.tif.xml` ← 0-100% symbology

3. **Tree Canopy**
   - `nlcd_2023_tree_canopy_clipped.tif`
   - `nlcd_2023_tree_canopy_clipped.tif.xml` ← Canopy percentage colors

## Error Handling

If XML copy fails:
- Prints warning message
- Continues with raster (still usable)
- Doesn't crash the download

```
Warning: Could not copy nlcd_2024_land_cover.tif.xml: [error message]
```

## Technical Details

### XML File Naming Convention
GIS software expects: `{raster_name}.xml`
- Raster: `nlcd_2024_land_cover_clipped.tif`
- XML: `nlcd_2024_land_cover_clipped.tif.xml`

### What Gets Preserved
All `.xml` files in the zip, typically:
- Main metadata XML (FGDC/ISO standard)
- Auxiliary XML (symbology/rendering)

### Copy Method
Uses `shutil.copy2()` which preserves:
- File timestamps
- Metadata attributes
- File permissions

## Summary

✅ **XML metadata files are now preserved**
✅ **Automatically renamed to match clipped file**
✅ **Proper symbology in GIS software**
✅ **Complete metadata accessible**
✅ **No extra work required from you**

Your NLCD rasters will now open with proper colors and full documentation! 🎨
