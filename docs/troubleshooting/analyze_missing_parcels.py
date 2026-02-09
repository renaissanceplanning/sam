"""
Analyze which parcels are missing from the processed file.
"""

import geopandas as gpd
import pandas as pd

raw_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2024_raw.gpkg"
existing_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2025.gpkg"

print("=" * 80)
print("ANALYZING MISSING PARCELS")
print("=" * 80)

# Load both files
print("\nLoading files...")
raw_gdf = gpd.read_file(raw_file)
existing_gdf = gpd.read_file(existing_file)

print(f"Raw parcels: {len(raw_gdf):,}")
print(f"Existing parcels: {len(existing_gdf):,}")

# Get parcel IDs
raw_ids = set(raw_gdf['PARCELNO'].unique())
existing_ids = set(existing_gdf['PARCELNO'].unique())

print(f"\nUnique parcel IDs in raw: {len(raw_ids):,}")
print(f"Unique parcel IDs in existing: {len(existing_ids):,}")

# Find missing parcels
missing_ids = raw_ids - existing_ids
print(f"\nMissing parcel IDs: {len(missing_ids):,}")

if len(missing_ids) > 0:
    print("\nFirst 20 missing parcel IDs:")
    missing_list = list(missing_ids)[:20]
    for i, pid in enumerate(missing_list):
        print(f"  {i+1}. {pid}")

    # Get the missing parcels from raw file
    missing_parcels = raw_gdf[raw_gdf['PARCELNO'].isin(missing_ids)].copy()

    print(f"\n" + "=" * 80)
    print("SPATIAL DISTRIBUTION OF MISSING PARCELS")
    print("=" * 80)

    # Convert to same CRS for comparison
    missing_parcels_geo = missing_parcels.to_crs("EPSG:4269")

    # Get bounds of missing parcels
    if len(missing_parcels_geo) > 0:
        missing_bounds = missing_parcels_geo.total_bounds
        print(f"\nMissing parcels bounds:")
        print(f"  West:  {missing_bounds[0]:.6f}")
        print(f"  South: {missing_bounds[1]:.6f}")
        print(f"  East:  {missing_bounds[2]:.6f}")
        print(f"  North: {missing_bounds[3]:.6f}")

        # Check if they're evenly distributed or concentrated
        existing_bounds = existing_gdf.total_bounds
        print(f"\nExisting parcels bounds:")
        print(f"  West:  {existing_bounds[0]:.6f}")
        print(f"  South: {existing_bounds[1]:.6f}")
        print(f"  East:  {existing_bounds[2]:.6f}")
        print(f"  North: {existing_bounds[3]:.6f}")

        # Check if missing parcels are within existing bounds
        within_west = missing_bounds[0] >= existing_bounds[0]
        within_south = missing_bounds[1] >= existing_bounds[1]
        within_east = missing_bounds[2] <= existing_bounds[2]
        within_north = missing_bounds[3] <= existing_bounds[3]

        if all([within_west, within_south, within_east, within_north]):
            print("\n[DIAGNOSIS] Missing parcels are distributed WITHIN the existing coverage.")
            print("This suggests they were dropped during the NAL merge process.")
            print("Likely reason: No matching NAL data for these parcel IDs.")
        else:
            print("\n[DIAGNOSIS] Some missing parcels extend BEYOND existing coverage!")
            print("This could indicate a spatial filtering issue.")

    # Save missing parcels for inspection
    output_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\missing_parcels.gpkg"
    missing_parcels_geo.to_file(output_file, driver="GPKG")
    print(f"\nMissing parcels saved to: {output_file}")

else:
    print("\nNo missing parcel IDs - all raw parcels are in the existing file.")

    # Check for duplicate parcels
    raw_dupes = len(raw_gdf) - len(raw_ids)
    existing_dupes = len(existing_gdf) - len(existing_ids)

    print(f"\nDuplicate parcels in raw: {raw_dupes:,}")
    print(f"Duplicate parcels in existing: {existing_dupes:,}")

    if raw_dupes > existing_dupes:
        print("\n[DIAGNOSIS] Duplicates were removed during processing.")
        print("This is expected behavior from the dissolve operation.")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"\nRaw file:      {len(raw_gdf):>10,} parcels ({len(raw_ids):,} unique IDs)")
print(f"Existing file: {len(existing_gdf):>10,} parcels ({len(existing_ids):,} unique IDs)")
print(f"Missing:       {len(missing_ids):>10,} parcel IDs")
print(f"Loss:          {100 * len(missing_ids) / len(raw_ids):>9.2f}%")
