# SAM Project Simplification Plan

## Executive Summary

The SAM project has **significant structural complexity** due to a duplicated layer architecture where modules are split between `sam/<module>/` and `sam/download/<module>/`. This creates:

- ❌ Unclear module boundaries
- ❌ Confusing import paths
- ❌ Duplication of concerns
- ❌ Inconsistent organization patterns

**Goal**: Simplify to a **single-layer architecture** where each data source has one module containing both download and processing logic.

---

## Current Problems

### 1. Duplicate Module Layers

| Data Source | Top-Level | Download Layer | Problem |
|-------------|-----------|----------------|---------|
| NLCD | `sam/nlcd/` | `sam/download/nlcd/` | Two modules for one data source |
| OSM | `sam/osm/` | `sam/download/osm/` | Two modules for one data source |
| SLD | `sam/sld/` | `sam/download/sld/` | Top-level is just a wrapper |
| Parcels | `sam/parcels/` | `sam/download/fl_parcels/` | Code scattered across both |

**Impact**:
- Confusing for new developers ("where does NLCD code live?")
- Circular-looking imports (`sam/nlcd/` imports from `sam/download/nlcd/`)
- Test confusion (mixed import statements)

### 2. Census Module Asymmetry

The Census Bureau provides ACS, LODES, and Tiger data, but organization is inconsistent:

- ✓ `sam/acs/` (top-level module)
- ✓ `sam/lodes/` (top-level module)
- ✓ `sam/tiger/` (top-level module)
- ✓ `sam/download/census/` (serves all three)

**Problem**: Three separate top-level modules for semantically related data sources.

### 3. Orphaned Download Modules

Some modules only exist in `download/` with no top-level counterpart:

- `sam/download/pad/` - Protected Area Database
- `sam/download/ms_footprints/` - Microsoft building footprints
- `sam/download/POI/` - Points of interest (incomplete)

**Problem**: No clear API surface; users must import from `download/` directly.

### 4. Configuration Sprawl

Configuration spread across multiple files:
- `config/acs_config.py` (906 lines!)
- `config/parcel_config.py`
- `config/replica_config.py`
- `config/ref_config.py`

**Problem**: Each module has its own config pattern; no standardization.

---

## Proposed Simplification

### Principle: **One Data Source = One Module**

Each module should be **self-contained** with:
- **core.py** - Main classes and processing logic
- **download.py** - Data acquisition (if needed)
- **__init__.py** - Public API exports
- (Optional) **config.py** - Module-specific constants

### Target Structure

```
sam/
├── config/                    # Global configuration only
│   ├── __init__.py
│   ├── reference.py          # Shared reference data (counties, states)
│   └── helper_functions.py
│
├── census/                    # NEW: Unified Census Bureau data
│   ├── __init__.py           # Exports: ACS, LODES, Tiger
│   ├── acs.py                # ACS class + methods
│   ├── lodes.py              # LODES class + methods
│   ├── tiger.py              # Tiger class + methods
│   ├── download.py           # Census API interaction (tidycensus via R)
│   └── config.py             # ACS variable definitions
│
├── nlcd/                      # NLCD raster data
│   ├── __init__.py
│   ├── core.py               # NLCD processing class
│   └── download.py           # NLCD download functions
│
├── osm/                       # OpenStreetMap data
│   ├── __init__.py
│   ├── core.py               # OSMNetwork class
│   └── download.py           # OSM download functions
│
├── parcels/                   # Florida parcel data
│   ├── __init__.py
│   ├── core.py               # High-level parcel API
│   ├── download.py           # Portal scraping, format handling
│   └── config.py             # Field mappings, schemas
│
├── sld/                       # Smart Location Database
│   ├── __init__.py
│   ├── core.py               # SLD analysis (future)
│   └── download.py           # SLD download
│
├── ms_footprints/             # NEW: Microsoft building footprints
│   ├── __init__.py
│   ├── core.py               # Processing logic
│   └── download.py
│
├── pad/                       # NEW: Protected Area Database
│   ├── __init__.py
│   ├── core.py               # Processing logic
│   └── download.py
│
├── lihtc/                     # Low Income Housing Tax Credit
├── naip/                      # NAIP imagery
├── replica/                   # Replica synthetic data
├── menus/                     # Batch download orchestrator
└── tests/                     # Test suite
```

**Eliminated**:
- ❌ `sam/download/` directory (merged into individual modules)
- ❌ `sam/acs/` (consolidated into `sam/census/`)
- ❌ `sam/lodes/` (consolidated into `sam/census/`)
- ❌ `sam/tiger/` (consolidated into `sam/census/`)

**Result**:
- **15 modules → 9 modules** (40% reduction)
- **Clear responsibility**: Each module owns its entire domain
- **Simpler imports**: `from sam.nlcd import download_nlcd, NLCD`
- **Better discoverability**: One place to look per data source

---

## Migration Plan

### Phase 1: Low-Risk Consolidations (Week 1)

#### 1.1 Consolidate NLCD Module

**Current**:
```
sam/nlcd/
├── __init__.py              # Imports from both locations
├── core.py                  # NLCD processing class
sam/download/nlcd/
├── __init__.py
├── core.py                  # download_nlcd function
```

**Target**:
```
sam/nlcd/
├── __init__.py              # Exports: NLCD, download_nlcd
├── core.py                  # NLCD class
├── download.py              # download_nlcd, get_closest_nlcd_year
└── config.py                # NLCD_YEARS, NLCD_DATASETS constants
```

**Steps**:
1. Move `sam/download/nlcd/core.py` → `sam/nlcd/download.py`
2. Update `sam/nlcd/__init__.py`:
   ```python
   from .core import NLCD
   from .download import download_nlcd, get_closest_nlcd_year
   __all__ = ['NLCD', 'download_nlcd', 'get_closest_nlcd_year']
   ```
3. Delete `sam/download/nlcd/`
4. Update imports in `sam/menus/core.py`

**Testing**: Run NLCD tests to verify functionality

#### 1.2 Consolidate OSM Module

Same pattern as NLCD:
- Move `sam/download/osm/core.py` → `sam/osm/download.py`
- Update `sam/osm/__init__.py`
- Delete `sam/download/osm/`

#### 1.3 Consolidate SLD Module

**Current**: `sam/sld/core.py` is a 29-line wrapper around `sam/download/sld/core.py`

**Action**: Merge both into `sam/sld/`:
- Move `sam/download/sld/core.py` → `sam/sld/download.py`
- Delete `sam/sld/core.py` (just a wrapper)
- Update `sam/sld/__init__.py`:
  ```python
  from .download import download_sld
  __all__ = ['download_sld']
  ```

### Phase 2: Census Consolidation (Week 2)

#### 2.1 Create Unified Census Module

**Rationale**: ACS, LODES, and Tiger are all Census Bureau products using the same underlying API (tidycensus). They should be organized together.

**Current**:
```
sam/acs/          # 3 files, ACS class
sam/lodes/        # 2 files, lodes namespace
sam/tiger/        # 2 files, Tiger class
sam/download/census/  # 619 lines, serves all three
```

**Target**:
```
sam/census/
├── __init__.py          # Exports: ACS, lodes, Tiger
├── acs.py               # ACS class (from current sam/acs/core.py)
├── lodes.py             # lodes namespace (from current sam/lodes/core.py)
├── tiger.py             # Tiger class (from current sam/tiger/core.py)
├── download.py          # Census API calls (from sam/download/census/core.py)
└── config.py            # ACS variable definitions
```

**Steps**:
1. Create `sam/census/` directory
2. Move and rename:
   - `sam/acs/core.py` → `sam/census/acs.py`
   - `sam/lodes/core.py` → `sam/census/lodes.py`
   - `sam/tiger/core.py` → `sam/census/tiger.py`
   - `sam/download/census/core.py` → `sam/census/download.py`
   - `sam/config/acs_config.py` → `sam/census/config.py`
3. Create `sam/census/__init__.py`:
   ```python
   """
   Census Bureau data module.

   Provides access to American Community Survey (ACS), LODES employment data,
   and TIGER/Line geographic boundaries.
   """
   from .acs import ACS
   from .lodes import lodes
   from .tiger import Tiger

   __all__ = ['ACS', 'lodes', 'Tiger']
   ```
4. Update imports across codebase:
   - `from sam.acs import ACS` → `from sam.census import ACS`
   - `from sam.lodes import lodes` → `from sam.census import lodes`
   - `from sam.tiger import Tiger` → `from sam.census import Tiger`
5. Delete old directories: `sam/acs/`, `sam/lodes/`, `sam/tiger/`, `sam/download/census/`

**Testing**: Extensive - affects many tests

#### 2.2 Backward Compatibility Shims (Optional)

To avoid breaking existing user code, create temporary shims:

```python
# sam/acs/__init__.py (deprecated)
"""DEPRECATED: Use sam.census.ACS instead."""
import warnings
from sam.census import ACS

warnings.warn(
    "sam.acs is deprecated. Use 'from sam.census import ACS' instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ['ACS']
```

Remove shims in next major version.

### Phase 3: Parcel Consolidation (Week 3)

**Current mess**:
```
sam/parcels/core.py                           # 190 lines
sam/download/fl_parcels/parcel_data_portal.py # 400+ lines
sam/download/fl_parcels/format_parcels.py     # 180 lines
sam/download/fl_parcels/parcel_ftp.py         # (deprecated, commented)
```

**Target**:
```
sam/parcels/
├── __init__.py
├── core.py          # High-level API (download_fl_parcels)
├── download.py      # Portal scraping (from parcel_data_portal.py)
├── formatting.py    # Field mapping (from format_parcels.py)
└── config.py        # Schemas, field mappings (from parcel_config.py)
```

**Steps**:
1. Move `sam/download/fl_parcels/parcel_data_portal.py` → `sam/parcels/download.py`
2. Move `sam/download/fl_parcels/format_parcels.py` → `sam/parcels/formatting.py`
3. Delete `sam/download/fl_parcels/parcel_ftp.py` (commented-out FTP code)
4. Move `sam/config/parcel_config.py` → `sam/parcels/config.py`
5. Update `sam/parcels/core.py` imports
6. Delete `sam/download/fl_parcels/`

### Phase 4: Promote Orphaned Modules (Week 4)

#### 4.1 Microsoft Footprints

**Current**: `sam/download/ms_footprints/` only

**Target**:
```
sam/ms_footprints/
├── __init__.py
├── core.py          # Future: processing, analysis
└── download.py      # Current download logic
```

#### 4.2 Protected Area Database

**Current**: `sam/download/pad/` only

**Target**:
```
sam/pad/
├── __init__.py
├── core.py          # Future: processing, analysis
└── download.py      # Current download logic
```

#### 4.3 Points of Interest (Optional)

**Current**: `sam/download/POI/` (incomplete)

**Decision**: Either complete and promote to `sam/poi/` OR delete entirely

### Phase 5: Configuration Cleanup (Week 5)

**Consolidate global config**:

```
sam/config/
├── __init__.py           # Exports: COUNTIES, STATE_DF, is_int, etc.
├── reference.py          # Reference data (COUNTIES, STATE_DF)
└── helper_functions.py   # Utility functions
```

**Module-specific config moved**:
- `acs_config.py` → `sam/census/config.py`
- `parcel_config.py` → `sam/parcels/config.py`
- `replica_config.py` → `sam/replica/config.py`

---

## Breaking Changes & Migration

### Import Changes

Users will need to update imports:

| Old Import | New Import |
|------------|------------|
| `from sam.acs import ACS` | `from sam.census import ACS` |
| `from sam.lodes import lodes` | `from sam.census import lodes` |
| `from sam.tiger import Tiger` | `from sam.census import Tiger` |
| `from sam.download.nlcd import download_nlcd` | `from sam.nlcd import download_nlcd` |
| `from sam.download.osm import dl_osm_network` | `from sam.osm import dl_osm_network` |
| `from sam.download.sld import dl_sld` | `from sam.sld import download_sld` |

### Mitigation Strategy

1. **Version bump**: 0.1 → 0.2 (minor version)
2. **Deprecation warnings**: Keep old import paths with warnings for 1 release
3. **Update documentation**: Clear migration guide
4. **Update examples**: All examples use new structure

---

## Benefits Summary

### Before Simplification
- ❌ 15 top-level modules + 8 download modules = **23 total modules**
- ❌ Duplicate layers (nlcd/, download/nlcd/)
- ❌ Confusing imports (`from sam.download.nlcd import ...`)
- ❌ Scattered configuration (6+ config files)
- ❌ Unclear module boundaries

### After Simplification
- ✅ **9 top-level modules** (60% reduction)
- ✅ One module per data source
- ✅ Clear imports (`from sam.nlcd import ...`)
- ✅ Centralized + modular config
- ✅ Self-documenting structure

### Developer Experience
- **Finding code**: One obvious place per data source
- **Adding features**: Clear where new code belongs
- **Testing**: No cross-module confusion
- **Documentation**: Structure matches user mental model

---

## Risk Assessment

| Phase | Risk Level | Mitigation |
|-------|------------|------------|
| Phase 1 (NLCD/OSM/SLD) | **Low** | Self-contained modules, limited dependencies |
| Phase 2 (Census) | **Medium** | Many imports to update, extensive testing needed |
| Phase 3 (Parcels) | **Low** | Internal reorganization, same public API |
| Phase 4 (Orphans) | **Low** | New modules, no breaking changes |
| Phase 5 (Config) | **Low** | Move files, update imports |

**Total estimated effort**: 3-5 weeks

---

## Success Criteria

- ✅ All existing tests pass
- ✅ Import paths simplified (no `sam.download.*` imports)
- ✅ Module count reduced by 50%+
- ✅ Clear separation: one module = one data source
- ✅ Documentation updated with new structure
- ✅ Backward compatibility shims in place (optional)

---

## Next Steps

**Immediate**:
1. Get team alignment on consolidation plan
2. Create feature branch: `refactor/simplify-structure`
3. Start with Phase 1 (NLCD consolidation) as proof of concept

**Follow-up**:
1. Update CONTRIBUTING.md with new module structure guidelines
2. Create module template for consistency
3. Document "where should new code go?" decision tree
