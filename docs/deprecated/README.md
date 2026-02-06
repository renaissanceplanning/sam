# Deprecated Code Archive

This directory contains deprecated implementations kept for historical reference only.

**⚠️ DO NOT USE THESE FILES - THEY ARE NOT MAINTAINED**

---

## core_r_backup.py

**Status**: DEPRECATED as of 2026-02-04
**Replaced by**: `sam/download/census/core.py` (Python implementation)

### What it was
R-based census download implementation using:
- R package: `tigris` (TIGER shapefiles)
- R package: `tidycensus` (ACS data)
- R package: `sf` (spatial operations)
- R package: `lwgeom` (geometric operations)
- Python bridge: `rpy2`

### Why it was deprecated
1. **Installation complexity**: Required R, rpy2, and multiple R packages
2. **Windows DLL issues**: Frequent PATH and dependency conflicts
3. **Cross-platform problems**: Different behavior on Windows/Mac/Linux
4. **Performance overhead**: Python ↔ R bridge conversion costs
5. **Debugging difficulty**: Mixed Python/R stack traces
6. **Maintenance burden**: Two language ecosystems to maintain

### What replaced it
Pure Python implementation in `sam/download/census/core.py`:
- `pygris` replaces `tigris` (TIGER downloads)
- `censusdata` replaces `tidycensus` (ACS downloads)
- `geopandas` replaces `sf` (spatial operations)
- `shapely` replaces `lwgeom` (geometric operations)

### API Compatibility
The Python replacement maintains the same API, so user code doesn't need changes:
```python
# These still work exactly the same
from sam.download.census import dl_tiger, dl_census, dl_acs
```

### Reference Links
- Migration documentation: `refactor_docs/R_DEPENDENCY_REMOVED.md`
- Python implementation: `sam/download/census/core.py`

---

## When to Reference This Code

Only reference these deprecated files if:
1. **Investigating historical behavior** - Understanding how things worked before
2. **Comparing implementations** - Validating Python version matches R version behavior
3. **Documentation purposes** - Writing about the migration process

**Do NOT**:
- ❌ Try to run or import these files
- ❌ Copy code from here into active codebase
- ❌ File bugs against this code
- ❌ Propose changes to these implementations

---

## Deletion Schedule

These files may be permanently deleted after:
- ✅ Python implementation has been stable for 6+ months
- ✅ All users have migrated to Python version
- ✅ No outstanding issues related to R → Python migration

**Earliest deletion date**: August 2026

---

Last updated: 2026-02-06
