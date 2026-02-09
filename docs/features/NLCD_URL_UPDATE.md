# NLCD Download URL Update - February 2026

## Problem
The NLCD download was failing with **403 Forbidden** errors because the old S3 bucket URLs no longer work:
- Old URL: `https://s3-us-west-2.amazonaws.com/mrlc/nlcd_2021_land_cover_l48_20230630.zip`
- Result: **403 Forbidden**

## Solution
Updated SAM to use the new MRLC website URLs:
- New URL pattern: `https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_{year}_CU_C1V1.zip`
- Result: **200 OK** ✓

## What Changed

### File Modified
**`sam/download/nlcd/core.py`** - `build_nlcd_url()` function

### New URL Structure

**Annual NLCD Products (2019-2024):**
```
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2023_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2022_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2021_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2020_CU_C1V1.zip
https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2019_CU_C1V1.zip
```

**Format Breakdown:**
- `Annual_NLCD_LndCov` = Product name (Annual National Land Cover Database Land Cover)
- `{year}` = Data year (2019-2024 available)
- `CU` = Region code (CU = Continental US / CONUS)
- `C1V1` = Collection 1, Version 1

### Region Codes
- `CU` = CONUS (Continental US)
- `AK` = Alaska
- `HI` = Hawaii
- `PR` = Puerto Rico

### Available Years
**Annual NLCD (2019-2024):**
- Full annual coverage starting 2019
- Updated yearly with latest land cover data
- Currently: 2019, 2020, 2021, 2022, 2023, 2024

**Legacy NLCD (pre-2019):**
- Older products: 2016, 2013, 2011, 2008, 2006, 2004, 2001
- These may require manual download
- URLs not yet updated for legacy products

## Limitations

### Dataset Support
The new Annual NLCD URLs currently support:
- ✅ **Land Cover** - Working for 2019-2024
- ❌ **Impervious Surface** - Not yet available via Annual NLCD
- ❌ **Tree Canopy** - Not yet available via Annual NLCD
- ❌ **Impervious Descriptor** - Not yet available via Annual NLCD

If you request a non-land-cover dataset, SAM will:
1. Print a warning message
2. Fall back to land cover data
3. Continue the download

### Legacy Years (2016 and earlier)
For years before 2019, SAM will:
1. Print a warning that it's a legacy product
2. Return a placeholder URL
3. Provide instructions for manual download from https://www.mrlc.gov/data

## Usage

No code changes needed! Just use SAM as normal:

```python
downloader = DataMenuDownloader(
    summary_areas=county_boundary,
    data_dir="data"
)

# This now works with the new URLs!
downloader.pull_nlcd()
```

### Year Mapping
SAM automatically maps requested years to closest available:
- Request 2025 → Downloads 2024 (closest available)
- Request 2023 → Downloads 2023 (exact match)
- Request 2020 → Downloads 2020 (exact match)
- Request 2018 → Downloads 2019 (closest available)
- Request 2016 → Legacy product (manual download may be required)

## Testing

Verified URLs return **200 OK**:
```bash
curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2024_CU_C1V1.zip"
# HTTP/1.1 200 OK
# Content-Length: 1441615256  (1.34 GB)

curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2021_CU_C1V1.zip"
# HTTP/1.1 200 OK

curl -I "https://www.mrlc.gov/downloads/sciweb1/shared/mrlc/data-bundles/Annual_NLCD_LndCov_2019_CU_C1V1.zip"
# HTTP/1.1 200 OK
```

## Error Messages Improved

Updated error handling provides better guidance:

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

## Next Steps

### For Your Project
The NLCD download should now work in your Hillsborough County pull script:

```python
# In pull_hillsborough_data.py
downloader.pull_nlcd()  # Will now download Annual NLCD 2024
```

### Future Improvements
1. Add support for other Annual NLCD products (impervious, tree canopy) when available
2. Update legacy product URLs if MRLC provides new access methods
3. Add direct ScienceBase integration as alternative download source
4. Consider caching downloaded files to avoid repeated large downloads

## References
- MRLC Data Portal: https://www.mrlc.gov/data
- Annual NLCD Info: https://www.usgs.gov/centers/eros/science/annual-national-land-cover-database
- MRLC Viewer: https://www.mrlc.gov/viewer/
- ScienceBase Catalog: https://www.sciencebase.gov/catalog/item/655ceb8ad34ee4b6e05cc51a
