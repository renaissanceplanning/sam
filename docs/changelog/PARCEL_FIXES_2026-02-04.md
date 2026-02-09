# Florida DOR Parcel Download Fixes - 2026-02-04

## Summary

Fixed critical issues with Florida Department of Revenue (FDOR) parcel downloads due to URL structure changes and mismatched data release schedules.

---

## Issues Fixed

### 1. **URL Structure Changes for 2024+**

**Problem**: FDOR changed the Map Data folder structure starting in 2024.

**Old Structure** (pre-2024):
```
Map Data/2023F/Hillsborough_2023Pin.zip
```

**New Structure** (2024+):
```
Map Data/2024F/2024F PIN/Hillsborough_2024Pin.zip
Map Data/2025F/2025F PIN/Hillsborough_2025Pin.zip
```

**Fix**: Updated `build_url()` to detect year and use appropriate structure:
```python
if try_year >= 2024:
    # 2024+ uses new URL structure with PIN subfolder
    test_gis_url = f"{gis_base_url}/{try_year}F/{try_year}F%20PIN/{gis_file_name.format(county_name=county_name,year=try_year)}"
else:
    test_gis_url = f"{gis_base_url}/{try_year}F/{gis_file_name.format(county_name=county_name,year=try_year)}"
```

---

### 2. **Mismatched GIS and NAL Release Years**

**Problem**: FDOR sometimes releases GIS (shapefile) and NAL (tax roll) data for different years.

Example:
- GIS data available for 2024
- NAL data NOT available for 2024
- NAL data AVAILABLE for 2025

The old code would find GIS 2024, fail to find NAL 2024, and give up.

**Fix**: Try adjacent years for NAL when GIS year's NAL doesn't exist:

```python
# Try same year first, then try adjacent years
nal_years_to_try = [try_year, try_year + 1, try_year - 1]

for nal_year in nal_years_to_try:
    # Try Final first
    test_nal_url_f = f"{base_nal_url}/{nal_year}F/..."
    if works:
        use this
        break

    # Try Provisional
    test_nal_url_p = f"{base_nal_url}/{nal_year}P/..."
    if works:
        use this
        break
```

This allows pairing:
- **GIS 2024** with **NAL 2025** ✓
- **GIS 2023** with **NAL 2024** ✓
- Any reasonable combination

---

### 3. **Year Fallback Logic**

**Problem**: Code was trying to download 2025 data (current year - 1) but 2025 GIS might not exist yet.

**Fix**: Added smart fallback through multiple years:

```python
years_to_try = [year, year - 1, year - 2, 2024, 2023]
years_to_try = sorted(set(years_to_try), reverse=True)  # Remove duplicates
```

For each year:
1. Check if GIS exists
2. Check if NAL exists (same year, +1 year, -1 year)
3. If both found → SUCCESS
4. If either missing → try next year

---

## URL Patterns (as of 2026-02-04)

### GIS (Shapefiles)

**2024+**:
```
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2025F/2025F%20PIN/Hillsborough_2025Pin.zip
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2024F/2024F%20PIN/Hillsborough_2024Pin.zip
```

**Pre-2024**:
```
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Map%20Data/2023F/Hillsborough_2023Pin.zip
```

### NAL (Tax Roll CSV)

**Final**:
```
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025F/Hillsborough%2057%20Final%20NAL%202025.zip
```

**Provisional**:
```
https://floridarevenue.com/property/dataportal/Documents/PTO%20Data%20Portal/Tax%20Roll%20Data%20Files/NAL/2025P/Hillsborough%2057%20Final%20NAL%202025.zip
```

Note: Provisional (`P`) used when Final (`F`) not yet available.

---

## Example: Hardee County (2025)

**Request**: Download 2025 parcels for Hardee County

**Execution**:
1. Try GIS 2025F → ✓ Found at `Map Data/2025F/2025F PIN/Hardee_2025Pin.zip`
2. Try NAL 2025F → ✓ Found at `NAL/2025F/Hardee 35 Final NAL 2025.zip`
3. Success! Use GIS 2025 + NAL 2025

**Example: Hardee County (2024 scenario)**

If GIS 2024 exists but NAL 2024 doesn't:
1. Try GIS 2024F → ✓ Found at `Map Data/2024F/2024F PIN/Hardee_2024Pin.zip`
2. Try NAL 2024F → ✗ Not found
3. Try NAL 2024P → ✗ Not found
4. Try NAL 2025F → ✓ Found!
5. Success! Use GIS 2024 + NAL 2025

---

## Future-Proofing Notes

### Likely Changes Next Year

The FDOR portal structure may change again. Common patterns:

1. **Year subfolder changes**: `2026F/`, `2026/`, etc.
2. **PIN subfolder naming**: `2026F PIN/`, `PIN/`, etc.
3. **File naming conventions**: Case sensitivity, underscores vs spaces

### What Makes Our Code Resilient

✅ **Multi-year fallback**: Tries current year, previous years, and known stable years
✅ **Adjacent year matching**: Pairs GIS and NAL from different years if needed
✅ **URL testing**: Validates each URL before attempting download
✅ **Clear error messages**: Shows what was tried and where to find manual downloads

### If It Breaks Next Year

1. Check the FDOR portal structure: https://floridarevenue.com/property/dataportal/Pages/Downloads.aspx
2. Update URL patterns in `parcel_data_portal.py`:
   - Lines 11-14: Base URLs
   - Lines 323-330: Year-based URL construction
3. Test with single county first
4. Update this documentation

---

## Files Modified

- **`sam/download/fl_parcels/parcel_data_portal.py`**
  - `build_url()` function (lines 305-358)
  - Added multi-year fallback logic
  - Added adjacent year NAL matching
  - Updated 2024+ URL structure

---

## Testing

Test with various scenarios:

```python
from sam.download.fl_parcels.parcel_data_portal import build_url

# Should find 2025F for both
gis, nal = build_url("Hillsborough", 2025)

# Should fall back to 2024 or 2025
gis, nal = build_url("Hardee", 2025)

# Should work with older years
gis, nal = build_url("Miami-Dade", 2023)
```

---

## Known Limitations

1. **County name variations**: Miami-Dade vs Dade, St. vs Saint - handled by `format_florida_counties()`
2. **County number mapping**: Hardcoded sequential numbers - may need updating if FDOR changes numbering
3. **Portal changes**: If FDOR completely restructures their portal, code will need updates

---

*Last Updated: 2026-02-04*
*Next Review: When FDOR releases 2026 data (likely late 2026/early 2027)*
