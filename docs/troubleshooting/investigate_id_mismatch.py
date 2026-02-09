"""
Investigate why existing file has more unique IDs than raw file.
"""

import geopandas as gpd
import pandas as pd

raw_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2024_raw.gpkg"
existing_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2025.gpkg"

print("=" * 80)
print("INVESTIGATING PARCEL ID MISMATCH")
print("=" * 80)

# Load both files
print("\nLoading files...")
raw_gdf = gpd.read_file(raw_file)
existing_gdf = gpd.read_file(existing_file)

# Get parcel IDs
raw_ids = set(raw_gdf['PARCELNO'].astype(str).unique())
existing_ids = set(existing_gdf['PARCELNO'].astype(str).unique())

print(f"\nRaw file:")
print(f"  Total parcels: {len(raw_gdf):,}")
print(f"  Unique IDs: {len(raw_ids):,}")
print(f"  Duplicates: {len(raw_gdf) - len(raw_ids):,}")

print(f"\nExisting file:")
print(f"  Total parcels: {len(existing_gdf):,}")
print(f"  Unique IDs: {len(existing_ids):,}")
print(f"  Duplicates: {len(existing_gdf) - len(existing_ids):,}")

# Find IDs that are in raw but not in existing
missing_from_existing = raw_ids - existing_ids
print(f"\nIDs in raw but NOT in existing: {len(missing_from_existing):,}")

# Find IDs that are in existing but not in raw
extra_in_existing = existing_ids - raw_ids
print(f"IDs in existing but NOT in raw: {len(extra_in_existing):,}")

# Net difference
net_difference = len(extra_in_existing) - len(missing_from_existing)
print(f"\nNet difference: {net_difference:+,} IDs")

if len(extra_in_existing) > 0:
    print("\n" + "=" * 80)
    print("EXTRA IDs IN EXISTING FILE (not in raw)")
    print("=" * 80)
    print("\nThese parcels are in the existing file but NOT in the raw GIS file!")
    print("They likely came from the NAL file.")

    print(f"\nFirst 20 extra IDs:")
    for i, pid in enumerate(list(extra_in_existing)[:20]):
        print(f"  {i+1}. {pid}")

    # Get sample records
    sample_extra = existing_gdf[existing_gdf['PARCELNO'].astype(str).isin(list(extra_in_existing)[:5])]
    print(f"\nSample records from extra parcels:")
    print(sample_extra[['PARCELNO', 'DOR_UC', 'OWN_NAME', 'LND_VAL']].to_string())

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

print(f"""
The existing file has {len(extra_in_existing):,} parcel IDs that are NOT in the raw GIS file.
This suggests the merge process is bringing in parcels from the NAL file
that don't have geometries in the GIS file.

This is unusual because the merge should be an INNER join (GIS + NAL),
which would only keep parcels present in BOTH files.

The SAM code uses: pd.merge(gis_gdf, nal_df, how='inner')

If there are more IDs in the result than in the GIS, one of these is happening:
1. The NAL file has duplicate parcel IDs that create multiple records
2. The merge is actually a different join type
3. There's post-processing that adds parcels
""")

print("\nRECOMMENDATION:")
print("The user reports 'only one corner' was downloaded, but the spatial analysis")
print("shows FULL COUNTY coverage. This may be a visualization issue or they are")
print("looking at a different file.")
print("\nThe raw GIS file from Florida DOR has complete county coverage.")
print("The processed file also has complete coverage with similar bounds.")
