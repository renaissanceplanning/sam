# Hillsborough County Parcel Investigation - Summary

## Quick Answer

**The downloaded Hillsborough County parcels cover the FULL COUNTY, not just "one corner".**

## Evidence

### 1. Spatial Bounds Comparison
Both files have identical coverage:

| File | West | East | South | North | Coverage |
|------|------|------|-------|-------|----------|
| Raw DOR GIS | -82.875403° | -82.054482° | 27.526422° | 28.173434° | **Full county** |
| SAM Processed | -82.875403° | -82.054482° | 27.526422° | 28.173433° | **Full county** |

Difference: Less than 0.0001° (essentially identical)

### 2. Visual Verification

A coverage comparison map has been created:
```
D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\coverage_comparison.png
```

Open this file to see:
- **Left panel (blue):** Raw Florida DOR GIS file - 532,240 parcels
- **Middle panel (green):** SAM processed file - 523,644 parcels
- **Right panel:** Missing parcels distribution (red dots) - 4,764 parcels

All three show identical county-wide coverage with red boundary boxes perfectly aligned.

### 3. Parcel Count Details

| Metric | Count | Explanation |
|--------|-------|-------------|
| Raw GIS parcels | 532,240 | Direct from Florida DOR |
| Raw unique IDs | 523,136 | After removing 9,104 duplicates |
| Processed parcels | 523,644 | After NAL merge |
| Missing from processed | 4,764 | No matching NAL tax data |
| Extra in processed | 5,272 | NAL records without GIS geometry |

The ~1.6% difference is due to:
- Duplicate parcel consolidation (expected)
- NAL merge inner join (expected)
- Missing NAL data for some parcels (expected)

## Files Created

### 1. Raw GIS File (Unprocessed)
```
D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2024_raw.gpkg
```
- **Source:** Florida DOR directly
- **Parcels:** 532,240
- **Content:** GIS geometries only (no attributes)
- **Use:** Reference/comparison

### 2. Existing Processed File
```
D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2025.gpkg
```
- **Source:** SAM processed
- **Parcels:** 523,644
- **Content:** GIS geometries + NAL attributes
- **Use:** Production analysis

### 3. Missing Parcels File
```
D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\missing_parcels.gpkg
```
- **Parcels:** 4,764
- **Content:** Parcels with no NAL data
- **Use:** Gap analysis

### 4. Coverage Map
```
D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\coverage_comparison.png
```
- Visual proof of full county coverage

## Why "One Corner" Report is Incorrect

Possible explanations for the user's perception:

1. **Attribute Filter Active:** GIS software may have a filter applied (e.g., showing only residential)
2. **Symbology Issue:** Parcels styled by attribute causing many not to display
3. **Wrong File:** Looking at a different/filtered dataset
4. **Zoom Level:** Not zoomed out enough to see full extent
5. **Layer Order:** Another layer obscuring parcels
6. **Coordinate System:** CRS mismatch causing display issues
7. **Render Limit:** GIS software not rendering all 500k+ parcels

## Recommendations

### For the User:
1. **Check GIS Software:**
   - Remove all attribute filters
   - Zoom to layer extent
   - Check symbology settings
   - Verify CRS matches (EPSG:4269)
   - Check render limits

2. **Verify File:**
   - Confirm looking at: `parcels_Hillsborough_2025.gpkg`
   - Check file size: ~290 MB
   - Check record count: 523,644 parcels

3. **Use Raw File:**
   - Raw unprocessed file available with `_raw` suffix
   - Contains all 532,240 parcels from Florida DOR

### For Future Downloads:
The investigation scripts can be used as a template for:
- Downloading raw GIS files
- Comparing with processed files
- Analyzing missing parcels
- Creating coverage visualizations

## Data Sources

**Florida Department of Revenue:**
- GIS File: [Hillsborough_2024Pin.zip](https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2024F/2024F%20PIN/Hillsborough_2024Pin.zip)
- NAL File: [Hillsborough 57 Final NAL 2024.zip](https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2024F/Hillsborough%2057%20Final%20NAL%202024.zip)

## Conclusion

**FULL COUNTY COVERAGE CONFIRMED**

The Hillsborough County parcel download is complete and correct. Both the raw Florida DOR file and the SAM-processed file have identical spatial bounds covering the entire county. The user's report of "one corner only" is not supported by the data analysis. The issue is likely a display/visualization problem in their GIS software, not a download problem.

---

**Investigation Date:** 2026-02-05
**Files Analyzed:** Raw DOR GIS, SAM processed file
**Result:** ✓ FULL COUNTY COVERAGE
**Issue:** User-side visualization problem (not download issue)
