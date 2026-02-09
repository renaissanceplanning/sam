"""
Compare spatial coverage of raw vs processed Hillsborough parcels.
"""

import geopandas as gpd

raw_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2024_raw.gpkg"
existing_file = r"D:\Renaissance Planning Group\Hillsborough County - 230037_04_ParksAndRec_MasterPlan\tech_group\data\RAW\parcels\parcels_Hillsborough_2025.gpkg"

print("=" * 80)
print("SPATIAL COVERAGE COMPARISON")
print("=" * 80)

# Load both files
print("\nLoading files...")
raw_gdf = gpd.read_file(raw_file)
existing_gdf = gpd.read_file(existing_file)

# Convert raw to same CRS as existing (EPSG:4269)
print(f"Converting raw CRS from {raw_gdf.crs} to {existing_gdf.crs}...")
raw_gdf_transformed = raw_gdf.to_crs(existing_gdf.crs)

# Get bounds in same CRS
raw_bounds = raw_gdf_transformed.total_bounds
existing_bounds = existing_gdf.total_bounds

print("\n" + "=" * 80)
print("BOUNDS COMPARISON (both in EPSG:4269)")
print("=" * 80)

print(f"\nRaw file bounds:")
print(f"  West:  {raw_bounds[0]:.6f}")
print(f"  South: {raw_bounds[1]:.6f}")
print(f"  East:  {raw_bounds[2]:.6f}")
print(f"  North: {raw_bounds[3]:.6f}")

print(f"\nExisting file bounds:")
print(f"  West:  {existing_bounds[0]:.6f}")
print(f"  South: {existing_bounds[1]:.6f}")
print(f"  East:  {existing_bounds[2]:.6f}")
print(f"  North: {existing_bounds[3]:.6f}")

print("\n" + "=" * 80)
print("COVERAGE ANALYSIS")
print("=" * 80)

raw_width = raw_bounds[2] - raw_bounds[0]
raw_height = raw_bounds[3] - raw_bounds[1]
exist_width = existing_bounds[2] - existing_bounds[0]
exist_height = existing_bounds[3] - existing_bounds[1]

print(f"\nRaw coverage: {raw_width:.4f} x {raw_height:.4f} degrees")
print(f"Existing coverage: {exist_width:.4f} x {exist_height:.4f} degrees")

# Check if existing bounds are subset of raw bounds
west_diff = existing_bounds[0] - raw_bounds[0]
south_diff = existing_bounds[1] - raw_bounds[1]
east_diff = raw_bounds[2] - existing_bounds[2]
north_diff = raw_bounds[3] - existing_bounds[3]

print(f"\nBoundary differences (positive = existing is smaller):")
print(f"  Western edge:  {west_diff:+.4f} degrees")
print(f"  Southern edge: {south_diff:+.4f} degrees")
print(f"  Eastern edge:  {east_diff:+.4f} degrees")
print(f"  Northern edge: {north_diff:+.4f} degrees")

# Calculate area coverage percentage
area_coverage = (exist_width * exist_height) / (raw_width * raw_height) * 100
print(f"\nExisting file covers ~{area_coverage:.1f}% of raw area")

# Parcel count comparison
print("\n" + "=" * 80)
print("PARCEL COUNT COMPARISON")
print("=" * 80)
print(f"\nRaw parcels:      {len(raw_gdf):>10,}")
print(f"Existing parcels: {len(existing_gdf):>10,}")
print(f"Missing parcels:  {len(raw_gdf) - len(existing_gdf):>10,}")
print(f"Loss percentage:  {100 * (1 - len(existing_gdf)/len(raw_gdf)):>9.2f}%")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if area_coverage < 95:
    print("\n[ISSUE] The existing file does NOT cover the full county!")
    print(f"It only covers {area_coverage:.1f}% of the raw area.")
    print("\nLikely cause: Processing error or filtering issue in SAM code.")
    print("The merge operation may be dropping parcels or spatial filtering is occurring.")
else:
    print("\n[OK] The existing file appears to cover the full county spatially.")
    print("The missing parcels may be due to:")
    print("  - Parcels without valid NAL data (dropped during merge)")
    print("  - Invalid geometries removed during processing")
    print("  - Duplicate parcels consolidated during dissolve")
