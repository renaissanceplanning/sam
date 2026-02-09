# PyCharm Conda Environment Fix ✅

## Problem Identified

**Error in PyCharm:**
```
WARNING - OSM import failed: cannot import name 'isiterable' from 'rputils' (unknown location)
```

**Root Cause:**
PyCharm is using a **different Python environment** than the command line:
- **Command line**: `C:\Python313\python.exe` (system Python) ✓ Has packages installed
- **PyCharm**: `C:\Users\CharlesRudder\miniconda3\envs\renplan\python.exe` (conda env) ✗ Missing packages

The packages (rputils, algi, gary, sam) were installed to system Python, but PyCharm's conda environment doesn't have them.

## Solution: Install to Conda Environment

### Option 1: Use the Batch Script (Easiest)

Run this batch file:
```bash
C:\github\packages\sam\install_to_conda.bat
```

This will:
1. Activate the `renplan` conda environment
2. Install all 4 packages (rputils, algi, gary, sam) in editable mode
3. Verify the installations
4. Show test results

### Option 2: Manual Installation

**In PyCharm's Terminal** (bottom of PyCharm window):

```bash
# The conda environment should already be active
# If not, activate it:
conda activate renplan

# Install each package in editable mode
cd C:\github\packages\rputils
pip install -e .

cd C:\github\packages\algi
pip install -e .

cd C:\github\packages\gary
pip install -e .

cd C:\github\packages\sam
pip install -e .
```

### Option 3: External Terminal

Open **Anaconda Prompt** or **Command Prompt**:

```bash
conda activate renplan
cd C:\github\packages\rputils && pip install -e .
cd C:\github\packages\algi && pip install -e .
cd C:\github\packages\gary && pip install -e .
cd C:\github\packages\sam && pip install -e .
```

## Verify Installation

After installing, run the verification script:

```python
python C:\github\packages\sam\verify_conda_install.py
```

Expected output:
```
1. Testing RP packages...
   [OK] rputils         C:\github\packages\rputils\rputils\__init__.py
   [OK] algi            C:\github\packages\algi\algi\__init__.py
   [OK] gary            C:\github\packages\gary\gary\__init__.py
   [OK] sam             C:\github\packages\sam\sam\__init__.py

2. Testing specific imports...
   [OK] rputils.isiterable       <function isiterable at 0x...>
   [OK] algi.dep.BBOX            <class 'algi.dep.BBOX.BBOX'>
   [OK] gary.trim_components     <function trim_components at 0x...>
   [OK] sam.osm.OSMNetwork       <class 'sam.osm.core.OSMNetwork'>

3. Testing HAS_OSM flag...
   HAS_OSM = True
   OSMNetwork = <class 'sam.osm.core.OSMNetwork'>
   [OK] OSM is available

Results: X passed, 0 failed
SUCCESS! All packages installed correctly.
```

## After Installation

1. **Restart PyCharm** for changes to take effect
2. **Invalidate Caches** (optional but recommended):
   - File → Invalidate Caches → Invalidate and Restart

3. **Test in PyCharm** by running:
   ```python
   from sam.menus import DataMenuDownloader
   import geopandas as gpd
   from shapely.geometry import box

   test_area = gpd.GeoDataFrame(
       {'geometry': [box(-82.46, 27.95, -82.45, 27.96)]},
       crs=4326
   )

   downloader = DataMenuDownloader(
       summary_areas=test_area,
       data_dir='test_output',
       years=2024
   )

   # This should now work!
   downloader.pull_OSM()
   ```

## Why This Happened

When you installed packages via command line using `pip install -e .`, they were installed to the **active Python environment at that time**, which was the system Python at `C:\Python313`.

PyCharm was configured to use the **conda environment** `renplan`, which is a completely separate Python installation with its own site-packages.

**Editable installs are environment-specific** - they create links in that environment's site-packages directory pointing to the source code.

## Understanding the Environments

### System Python (C:\Python313)
- Used by: Command line (when conda not activated)
- Has: rputils, algi, gary, sam ✓
- Location: `C:\Python313\Lib\site-packages\`

### Conda Environment (renplan)
- Used by: PyCharm
- Has: (after fix) rputils, algi, gary, sam ✓
- Location: `C:\Users\CharlesRudder\miniconda3\envs\renplan\Lib\site-packages\`

## Future Package Management

**For this project**, always install packages to the conda environment:

```bash
# Always activate first
conda activate renplan

# Then install
pip install <package>
# or
pip install -e /path/to/package
```

**To check which environment you're using:**
```bash
# In terminal:
which python  # Linux/Mac
where python  # Windows

# In Python:
import sys
print(sys.executable)
```

## Conda Environment Details

**Environment name**: `renplan`
**Location**: `C:\Users\CharlesRudder\miniconda3\envs\renplan\`
**Python version**: Check with `python --version` after activating

**To activate this environment:**
```bash
conda activate renplan
```

**To see all conda environments:**
```bash
conda env list
```

## PyCharm Configuration

**Current interpreter:** File → Settings → Project: sam → Python Interpreter

Should show:
```
Python 3.X (renplan)
Location: C:\Users\CharlesRudder\miniconda3\envs\renplan\python.exe
```

**Packages shown** should now include:
- algi (0.1a0) - editable install
- gary (0.1.1a0) - editable install
- rputils (0.1.1a0) - editable install
- sam (0.1) - editable install
- osmnx (2.0.7)
- pandana (0.7)
- etc.

## Troubleshooting

### Issue: "conda: command not found"

**Solution**:
- Open **Anaconda Prompt** instead of regular Command Prompt
- Or add Anaconda to PATH (not recommended, can cause conflicts)

### Issue: Packages still not found after installation

**Solution**:
1. Verify you're in the right environment: `conda info --envs`
2. Check active environment has asterisk: `* renplan`
3. Restart PyCharm after installation
4. Clear PyCharm caches: File → Invalidate Caches

### Issue: Permission errors during installation

**Solution**:
- Don't use `sudo` or "Run as Administrator" - not needed for conda envs
- If using `--user` flag, remove it (not needed in conda env)

### Issue: Different error after fixing rputils

If you get a different import error after fixing rputils, you may be missing other dependencies. Install them:

```bash
conda activate renplan

# OSM dependencies
pip install osmnx pandana networkx

# GIS dependencies
pip install geopandas shapely fiona rasterio

# Data processing
pip install pandas numpy scipy

# Other dependencies
pip install appdirs tqdm statsmodels
```

## Quick Test Command

After installation, test everything with one command:

```bash
conda activate renplan
python -c "from rputils import isiterable; from sam.osm import OSMNetwork; import sam.menus.core as mc; print(f'HAS_OSM={mc.HAS_OSM}')"
```

Should output:
```
HAS_OSM=True
```

## Files Created

- `install_to_conda.bat` - Automated installation script
- `verify_conda_install.py` - Verification script
- `check_python_env.py` - Environment diagnostic tool
- `CONDA_ENV_FIX.md` - This documentation

## Next Steps

1. ✅ Run `install_to_conda.bat`
2. ✅ Run `verify_conda_install.py` to confirm
3. ✅ Restart PyCharm
4. ✅ Test `downloader.pull_OSM()` in your code
5. 🎉 Download OSM networks for Hillsborough County!

The OSM functionality will now work correctly in PyCharm!
