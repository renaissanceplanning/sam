# Removing R Dependency from SAM

## Current State

SAM currently uses R (via rpy2) for Census data downloads:
- **Location**: `sam/download/census/core.py`
- **R Packages Used**:
  - `tigris` - TIGER/Line shapefiles
  - `tidycensus` - American Community Survey (ACS) data
  - `sf`, `lwgeom` - Spatial operations

## Problems with R Dependency

1. **Installation Complexity**: Requires R, rpy2, and R packages
2. **Windows DLL Issues**: Conda R on Windows has broken DLL dependencies
3. **Environment Fragility**: Hard to maintain across different systems
4. **Performance**: rpy2 adds overhead for Python ↔ R conversion

## Solution: Pure Python Replacement

### New Python Packages

| R Package | Python Replacement | Purpose |
|-----------|-------------------|---------|
| `tigris` | **`pygris`** | TIGER/Line shapefiles |
| `tidycensus` | **`censusdata`** | ACS data downloads |
| `sf`/`lwgeom` | **`geopandas`** | Spatial operations (already used) |

### Installation

```bash
# Instead of R packages
pip install pygris censusdata

# Already have
pip install geopandas pandas
```

## Implementation Plan

### Step 1: ✅ Create Python Module (DONE)

Created `sam/download/census/core_python.py` with:
- `dl_tiger_python()` - Replacement for tigris
- `dl_census_python()` - Replacement for tidycensus
- `dl_acs_python()` - Combined data + geometry
- Backward compatible API

### Step 2: Install & Test

```bash
# In renplan environment
conda activate renplan
pip install pygris censusdata

# Test
python -c "from sam.download.census.core_python import dl_tiger_python; print('Success!')"
```

### Step 3: Update SAM to Use Python Module

**Option A: Direct Replacement (Breaking Change)**
```python
# sam/download/census/__init__.py
from .core_python import *  # Instead of .core
```

**Option B: Feature Flag (Gradual Migration)**
```python
# sam/download/census/__init__.py
import os

USE_PYTHON_CENSUS = os.environ.get('SAM_USE_PYTHON_CENSUS', 'true').lower() == 'true'

if USE_PYTHON_CENSUS:
    try:
        from .core_python import *
    except ImportError:
        # Fall back to R if Python packages not available
        from .core import *
else:
    from .core import *
```

**Option C: Deprecation Path (Recommended)**
```python
# sam/download/census/__init__.py
import warnings

try:
    # Try Python version first
    from .core_python import (
        dl_tiger_python as dl_tiger,
        dl_census_python as dl_census,
        dl_acs_python as dl_acs
    )
    _USING_PYTHON = True
except ImportError:
    # Fall back to R version
    warnings.warn(
        "Python census packages not available. Using R fallback. "
        "Install with: pip install pygris censusdata",
        DeprecationWarning
    )
    from .core import dl_tiger, dl_census
    _USING_PYTHON = False
```

### Step 4: Update Dependent Code

Files that use census downloads:
```bash
grep -r "from sam.download.census import\|from sam.download import census" sam/
```

Update any code that expects R-specific behavior.

### Step 5: Update Tests

Create `sam/tests/download/test_census_python.py`:
```python
def test_tiger_download():
    """Test TIGER shapefile download with pygris."""
    from sam.download.census import dl_tiger

    # Download Hillsborough County
    gdf = dl_tiger('counties', state='12', county='057', year=2022)

    assert len(gdf) > 0
    assert 'geometry' in gdf.columns
    assert gdf.crs is not None

def test_acs_download():
    """Test ACS data download with censusdata."""
    from sam.download.census import dl_census

    # Download population by block group
    df = dl_census(
        geography='block group',
        variables=['B01001_001E'],  # Total population
        year=2022,
        state='12',
        county='057'
    )

    assert len(df) > 0
    assert 'B01001_001E' in df.columns
```

### Step 6: Remove R Dependency

Once Python version is working:

1. **Rename R version**: `core.py` → `core_r.py` (kept for reference)
2. **Remove R from environment.yml**:
   ```yaml
   dependencies:
     # Remove these:
     # - r
     # - rpy2=3.4.5
     # - r-tidycensus
     # - r-tigris
     # - r-sf
     # - r-lwgeom

     # Add these:
     - pip:
       - pygris
       - censusdata
   ```

3. **Remove R initialization from `sam/__init__.py`**:
   ```python
   # Delete lines 5-32 (R environment setup)
   ```

4. **Update documentation**:
   - Remove R installation instructions
   - Add Python package installation
   - Update examples

## Migration Guide for Users

### For Existing Code

**Old (R-based):**
```python
from sam.download.census import dl_tiger, dl_census

# TIGER
counties = dl_tiger('counties', state='12', cb=True, year=2022)

# ACS
acs_data = dl_census('acs', geography='block group',
                      state='12', county='057', year=2022,
                      variables=['B01001_001E'])
```

**New (Python-based):**
```python
from sam.download.census import dl_tiger, dl_census

# Same API! No code changes needed
counties = dl_tiger('counties', state='12', cb=True, year=2022)

acs_data = dl_census(geography='block group',  # Note: parameter name changed
                      variables=['B01001_001E'],
                      state='12', county='057', year=2022)
```

### Installation Changes

**Old:**
```bash
conda create -n sam r rpy2 r-tidycensus r-tigris r-sf
```

**New:**
```bash
conda create -n sam python=3.9
pip install pygris censusdata geopandas
```

## Benefits

### 1. Simplified Installation
- No R required
- Pure Python environment
- Faster environment setup

### 2. Better Performance
- No Python ↔ R conversion overhead
- Native pandas/geopandas operations
- Potentially faster downloads

### 3. Easier Debugging
- All Python stack traces
- Better IDE support
- Easier to contribute

### 4. Cross-Platform Reliability
- No Windows DLL issues
- Consistent behavior across OS
- Easier CI/CD

## Risks & Mitigation

### Risk 1: API Differences
**Mitigation**: Wrapper functions maintain backward compatibility

### Risk 2: Feature Gaps
**Mitigation**: Keep R version as fallback for 1-2 releases

### Risk 3: Data Differences
**Mitigation**: Extensive testing to ensure data parity

## Timeline

| Phase | Duration | Tasks |
|-------|----------|-------|
| **Phase 1** | ✅ Done | Create Python module |
| **Phase 2** | 1 week | Install packages, test functionality |
| **Phase 3** | 1 week | Update SAM to use Python module |
| **Phase 4** | 1 week | Update tests, verify data parity |
| **Phase 5** | 1 week | Documentation updates |
| **Phase 6** | 2 weeks | Beta testing with users |
| **Phase 7** | - | Remove R dependency (release v2.0) |

**Total**: ~6-8 weeks for complete migration

## Next Steps

1. ✅ Create `core_python.py`
2. **YOU ARE HERE** → Install pygris & censusdata in renplan environment
3. Test Python census module with Hillsborough County data
4. Compare results with R version for data parity
5. Update `sam/download/census/__init__.py` with feature flag
6. Create comprehensive tests
7. Get user feedback
8. Plan v2.0 release without R

---

*Last Updated: 2026-02-04*
