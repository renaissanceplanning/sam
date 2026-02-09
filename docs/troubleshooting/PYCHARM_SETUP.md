# PyCharm Setup for SAM and Dependencies ✓

## Issue Resolved

OSMNetwork and other SAM modules now import correctly in PyCharm.

## What Was Fixed

### 1. ALGI Package Structure
**Problem**: Root `__init__.py` was conflicting with package structure
- Removed: `C:\github\packages\algi\__init__.py` (conflicting file)
- Cleared: `__pycache__` directory
- Reinstalled: `pip install -e .` for algi

### 2. SAM Editable Install
**Problem**: SAM wasn't installed as a proper package
- Before: Direct path import (PyCharm couldn't resolve properly)
- After: Editable install with `pip install -e .`

## Installed Packages (Editable Mode)

All Renaissance Planning packages are now installed in editable mode:

```bash
# Core dependencies
pip install -e C:/github/packages/rputils
pip install -e C:/github/packages/algi
pip install -e C:/github/packages/gary

# Main package
pip install -e C:/github/packages/sam
```

**Editable mode means**:
- Changes to code are immediately available
- No need to reinstall after editing files
- PyCharm can properly resolve imports
- Proper IntelliSense/autocomplete

## Verify Installation

Run this in PyCharm's Python Console:

```python
# Core dependencies
import gary
import algi
import rputils
from algi.dep.BBOX import BBOX
from rputils import isiterable

print("✓ Core dependencies loaded")

# SAM and OSM
from sam.osm import OSMNetwork
from sam.menus import DataMenuDownloader

print("✓ SAM modules loaded")

# Check OSMNetwork methods
print("\nOSMNetwork methods:")
print("  - walk:", hasattr(OSMNetwork, 'walk'))
print("  - bike:", hasattr(OSMNetwork, 'bike'))
print("  - drive:", hasattr(OSMNetwork, 'drive'))
print("  - to_gdf:", hasattr(OSMNetwork, 'to_gdf'))
print("  - to_shp:", hasattr(OSMNetwork, 'to_shp'))
```

Expected output:
```
✓ Core dependencies loaded
✓ SAM modules loaded

OSMNetwork methods:
  - walk: True
  - bike: True
  - drive: True
  - to_gdf: True
  - to_shp: True
```

## PyCharm Configuration

### If Imports Still Don't Work in PyCharm:

1. **Invalidate Caches and Restart**
   - File → Invalidate Caches → Invalidate and Restart
   - This refreshes PyCharm's import index

2. **Verify Python Interpreter**
   - File → Settings → Project → Python Interpreter
   - Should show all installed packages:
     - sam (0.1) - editable install
     - gary (0.1.1a0) - editable install
     - algi (0.1a0) - editable install
     - rputils (0.1.1a0) - editable install
     - osmnx, pandana, etc.

3. **Check Project Structure**
   - File → Settings → Project → Project Structure
   - `C:\github\packages\sam` should be marked as "Sources" or properly detected

4. **Restart PyCharm**
   - Sometimes needed for import changes to fully take effect

## How to Use OSMNetwork

### Basic Usage

```python
from sam.osm import OSMNetwork
import geopandas as gpd

# Load your study area
study_area = gpd.read_file("hillsborough_county.shp")

# Download walk network
walk_net = OSMNetwork.walk(
    geometry=study_area,
    add_travel_time=True,
    crs=2779  # Florida State Plane East (ft)
)

# Save as shapefile
walk_net.to_shp(
    save_dir="data/networks",
    prefix="hillsborough_walk",
    trim=True  # Remove disconnected components
)

# Convert to GeoDataFrame for analysis
walk_gdf = walk_net.to_gdf()
print(f"Walk network: {len(walk_gdf)} edges")
```

### Using DataMenuDownloader

```python
from sam.menus import DataMenuDownloader
import geopandas as gpd

# Load study area
county = gpd.read_file("hillsborough_county.shp")

# Initialize downloader
downloader = DataMenuDownloader(
    summary_areas=county,
    data_dir="data",
    base_year=2025
)

# Download all three networks (walk, bike, drive)
downloader.pull_OSM(
    add_travel_time=True,
    trim=True
)
```

This will create:
- `data/RAW/networks/walk_network_2025.shp`
- `data/RAW/networks/bike_network_2025.shp`
- `data/RAW/networks/drive_network_2025.shp`

## Available Network Types

### Walk Network
- Pedestrian paths
- Sidewalks
- Crosswalks
- Trails
- **Use for**: Park accessibility, walkability analysis

### Bike Network
- Bike lanes
- Bike paths
- Shared roadways
- **Use for**: Bike route planning, connectivity analysis

### Drive Network
- Roads for vehicles
- Streets
- Highways
- **Use for**: Drive time analysis, vehicular access

## OSMNetwork Methods

### Class Methods (Download Networks)

```python
# Download and create network
walk_net = OSMNetwork.walk(geometry, add_travel_time=True, crs=None)
bike_net = OSMNetwork.bike(geometry, add_travel_time=True, crs=None)
drive_net = OSMNetwork.drive(geometry, add_travel_time=True, crs=None)
```

**Parameters:**
- `geometry`: GeoDataFrame or GeoSeries (Polygon/MultiPolygon)
- `add_travel_time`: Add speed and travel time attributes (default: True)
- `crs`: Target CRS for projection (default: inherit from geometry)
- `**kwargs`: Passed to `dl_osm_network()` (e.g., `trim_components=True`)

### Instance Methods (Convert/Export)

```python
# Convert to GeoDataFrame (edges)
gdf = network.to_gdf(trim=False)

# Convert to Pandana network (for accessibility analysis)
pandana_net = network.to_pandana()

# Save as shapefile
network.to_shp(
    save_dir="output",
    prefix="network_name",
    trim=True  # Remove disconnected components
)
```

## Network Attributes

After download with `add_travel_time=True`, edges have:
- `u`, `v`, `key`: Edge identifiers
- `name`: Street name
- `highway`: OSM highway type
- `length`: Edge length (meters)
- `speed_kph`: Estimated speed (km/h)
- `travel_time`: Travel time (seconds)
- `geometry`: LineString geometry

## Common Issues and Solutions

### Issue: "ImportError: cannot import name 'OSMNetwork'"

**Solution 1**: Restart PyCharm
- File → Invalidate Caches → Invalidate and Restart

**Solution 2**: Check Python interpreter
- Settings → Project → Python Interpreter
- Verify `sam` is listed and version is 0.1

**Solution 3**: Reinstall in editable mode
```bash
cd C:/github/packages/sam
pip uninstall -y sam
pip install -e .
```

### Issue: "ModuleNotFoundError: No module named 'osmnx'"

**Solution**: Install missing dependencies
```bash
pip install osmnx pandana networkx
```

### Issue: "cannot import name 'isiterable' from 'rputils'"

**Solution**: Reinstall rputils
```bash
cd C:/github/packages/rputils
pip uninstall -y rputils
pip install -e .
```

### Issue: "ImportError: cannot import name 'BBOX' from 'algi'"

**Solution**: Remove conflicting root `__init__.py`
```bash
rm C:/github/packages/algi/__init__.py
cd C:/github/packages/algi
pip install -e .
```

## Dependencies Overview

### Core RP Packages (Editable)
- **sam**: Main spatial analysis package
- **gary**: Network analysis utilities
- **algi**: GIS utilities (BBOX, raster tools)
- **rputils**: General utilities

### OSM Dependencies
- **osmnx**: Download OSM data
- **pandana**: Network accessibility analysis
- **networkx**: Graph analysis

### GIS Dependencies
- **geopandas**: Geospatial data handling
- **shapely**: Geometric operations
- **rasterio**: Raster data processing
- **fiona**: Vector data I/O

## Package Locations

All editable installs point to:
- `C:\github\packages\sam\` → sam package
- `C:\github\packages\gary\` → gary package
- `C:\github\packages\algi\` → algi package
- `C:\github\packages\rputils\` → rputils package

Code changes in these directories are immediately available without reinstall.

## Testing the Setup

Run this test script to verify everything works:

```python
# test_osm_import.py
import sys

def test_imports():
    """Test all critical imports"""
    try:
        # Core packages
        import gary
        import algi
        import rputils
        from algi.dep.BBOX import BBOX
        print("✓ Core packages imported")

        # SAM modules
        from sam.osm import OSMNetwork
        from sam.menus import DataMenuDownloader
        print("✓ SAM modules imported")

        # Verify OSMNetwork
        methods = ['walk', 'bike', 'drive', 'to_gdf', 'to_shp']
        for method in methods:
            assert hasattr(OSMNetwork, method), f"Missing method: {method}"
        print(f"✓ OSMNetwork has all {len(methods)} methods")

        print("\n✅ All tests passed! Setup is correct.")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
```

Run in terminal:
```bash
python test_osm_import.py
```

Expected output:
```
✓ Core packages imported
✓ SAM modules imported
✓ OSMNetwork has all 5 methods

✅ All tests passed! Setup is correct.
```

## Next Steps

1. **Restart PyCharm** (if not already done)
2. **Test imports** in PyCharm console
3. **Start using OSM** in your Hillsborough County analysis

The OSM functionality is now fully working and ready to use!
