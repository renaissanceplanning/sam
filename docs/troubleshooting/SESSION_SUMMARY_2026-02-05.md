# SAM OSM Troubleshooting Session - Feb 5, 2026

## Summary

Fixed OSM download functionality in SAM by:
1. Installing missing dependencies (gary, algi, rputils)
2. Fixing OSMnx 2.x API compatibility
3. Resolving PyCharm conda environment issues
4. Cleaning up repository documentation

## Issues Resolved

### 1. Missing Dependencies (gary, algi, rputils)

**Problem**: OSM module couldn't import because dependencies weren't installed.

**Solution**: Installed all three Renaissance Planning packages:
```bash
pip install -e C:/github/packages/rputils
pip install -e C:/github/packages/algi
pip install -e C:/github/packages/gary
pip install -e C:/github/packages/sam
```

**Dependencies installed**:
- gary (0.1.1a0) - network utilities
- algi (0.1a0) - GIS utilities (BBOX class)
- rputils (0.1.1a0) - general utilities (isiterable)
- Plus: pandana, osmnx, urbanaccess, osmnet, geopy, rasterio, fiona, etc.

### 2. ALGI Import Conflict

**Problem**:
```
ImportError: cannot import name 'isiterable' from 'rputils' (unknown location)
```

**Root Cause**: Conflicting `__init__.py` in algi root directory

**Solution**:
- Removed `C:/github/packages/algi/__init__.py`
- Cleared `__pycache__`
- Reinstalled: `pip install -e C:/github/packages/algi`

### 3. OSMnx API Compatibility

**Problem**:
```
graph_from_polygon() got an unexpected keyword argument 'clean_periphery'
```

**Root Cause**: OSMnx 2.x removed the `clean_periphery` parameter

**Solution**: Removed deprecated parameter from `sam/download/osm/core.py` line 186

**File**: `sam/download/osm/core.py`

**Changed**:
```python
# Before
cg = ox.graph_from_polygon(
    c,
    network_type=net_type,
    simplify=True,
    retain_all=True,
    truncate_by_edge=True,
    clean_periphery=False,  # ❌ Removed
    custom_filter=osm_query,
)

# After
cg = ox.graph_from_polygon(
    c,
    network_type=net_type,
    simplify=True,
    retain_all=True,
    truncate_by_edge=True,  # ✅ Works with osmnx 2.x
    custom_filter=osm_query,
)
```

### 4. PyCharm Conda Environment Issue

**Problem**: `HAS_OSM = False` in PyCharm but `True` in command line

**Root Cause**:
- Command line used system Python: `C:\Python313\python.exe`
- PyCharm used conda environment: `C:\Users\CharlesRudder\miniconda3\envs\renplan\python.exe`
- Packages were only installed in system Python

**Solution**: Install packages to conda environment
```bash
conda activate renplan
cd C:/github/packages/rputils && pip install -e .
cd C:/github/packages/algi && pip install -e .
cd C:/github/packages/gary && pip install -e .
cd C:/github/packages/sam && pip install -e .
```

**Documentation**: See `CONDA_ENV_FIX.md` for complete guide

### 5. Improved Error Messages

**Enhanced**: `sam/menus/core.py` lines 29-34 and 493

**Added logging** for OSM import failures:
```python
try:
    from sam.osm import OSMNetwork
    HAS_OSM = True
except ImportError as e:
    logger.warning(f"OSM import failed: {e}")
    OSMNetwork = None
    HAS_OSM = False
except Exception as e:
    logger.warning(f"Unexpected error importing OSM: {e}")
    OSMNetwork = None
    HAS_OSM = False
```

**Added debug logging** in `pull_OSM()`:
```python
logger.debug(f"pull_OSM called - HAS_OSM={HAS_OSM}, OSMNetwork={OSMNetwork}")
```

## Testing & Verification

### Test Results

Successfully tested OSM download with small Tampa area:

```python
downloader.pull_OSM(add_travel_time=True, trim=True)
```

**Output**:
- Walk network: 1362 edges, 1011 nodes ✓
- Bike network: 1361 edges, 516 nodes ✓
- Drive network: 406 edges, 146 nodes ✓

**Files created**:
- `{data_dir}/RAW/osm/walk_network_2023_edges.shp`
- `{data_dir}/RAW/osm/walk_network_2023_nodes.shp`
- `{data_dir}/RAW/osm/bike_network_2023_edges.shp`
- `{data_dir}/RAW/osm/bike_network_2023_nodes.shp`
- `{data_dir}/RAW/osm/drive_network_2023_edges.shp`
- `{data_dir}/RAW/osm/drive_network_2023_nodes.shp`

### Verification Commands

**Check imports**:
```python
import gary
import algi
import rputils
from sam.osm import OSMNetwork
import sam.menus.core as mc
print(f"HAS_OSM: {mc.HAS_OSM}")  # Should be True
```

**Check environment**:
```python
import sys
print(sys.executable)  # Shows which Python is running
```

## Repository Cleanup

Organized 20+ documentation/debug files:

**Structure**:
```
sam/
├── docs/
│   ├── troubleshooting/    # OSM guides, diagnostic scripts
│   ├── changelog/          # Bug fixes, improvements
│   └── features/           # NLCD, tree canopy docs
```

**Files moved**: See `CLEANUP_SUMMARY.md`

## Documentation Created

1. **OSM_DEPENDENCIES_FIXED.md** - Dependency installation guide
2. **OSM_FIXED_OSMNX_COMPATIBILITY.md** - OSMnx 2.x fixes
3. **PYCHARM_SETUP.md** - PyCharm configuration
4. **CONDA_ENV_FIX.md** - Conda environment setup
5. **CLEANUP_SUMMARY.md** - Repository organization
6. **docs/README.md** - Documentation index

## Key Learnings

### Environment Management
- **Editable installs are environment-specific**
- Command line and PyCharm may use different Python environments
- Always check which interpreter is active: `which python` or `sys.executable`

### OSMnx 2.x Migration
- Removed parameters: `clean_periphery`, `infrastructure`
- Kept parameters: `network_type`, `simplify`, `retain_all`, `truncate_by_edge`

### Package Dependencies
OSM requires full dependency chain:
```
sam.osm
  └─ sam.download.osm
      └─ gary.trim_components
      └─ algi.dep.BBOX
      └─ osmnx
          └─ pandana
              └─ networkx
```

## Next Steps for User

1. ✅ **Install to conda environment** (if using PyCharm)
2. ✅ **Restart PyCharm** to refresh imports
3. ✅ **Test OSM download** with small area
4. 🎯 **Download Hillsborough County networks**
5. 📊 **Use for Parks & Recreation analysis**

## Usage Example

```python
from sam.menus import DataMenuDownloader
import geopandas as gpd

# Load county boundary
county = gpd.read_file("data/hillsborough_county.shp")

# Initialize downloader
downloader = DataMenuDownloader(
    summary_areas=county,
    data_dir="data",
    years=2025
)

# Download all networks
downloader.pull_OSM()

# Networks saved to: data/RAW/osm/
```

## Files Modified

1. `sam/download/osm/core.py` - Removed `clean_periphery` parameter
2. `sam/menus/core.py` - Enhanced error logging

## Troubleshooting Reference

- **Missing dependencies**: `docs/troubleshooting/OSM_DEPENDENCIES_FIXED.md`
- **PyCharm issues**: `docs/troubleshooting/CONDA_ENV_FIX.md`
- **Import errors**: `docs/troubleshooting/PYCHARM_SETUP.md`
- **API compatibility**: `docs/troubleshooting/OSM_FIXED_OSMNX_COMPATIBILITY.md`

## Status

✅ **OSM download functionality fully operational**
✅ **Works in both command line and PyCharm**
✅ **Compatible with OSMnx 2.x**
✅ **Repository documentation organized**

Ready for production use!
