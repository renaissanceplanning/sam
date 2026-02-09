# SAM Refactoring Tasks

Active task list for ongoing refactoring work. Check off items as completed.

---

## ✅ Completed

### Phase 1: Logging Standardization
- [x] Create `sam/logging_config.py` with centralized logging
- [x] Integrate logging into `sam/__init__.py`
- [x] Convert all print() statements to logger calls in `sam/menus/core.py` (67 conversions)
- [x] Add logger imports to `sam/config/helper_functions.py`
- [x] Create `refactor_docs/LOGGING.md` documentation

### Phase 2: Module Documentation
- [x] Update 8 module `__init__.py` files with modern docstrings
- [x] Remove outdated encoding declarations
- [x] Add `__all__` exports for clean APIs
- [x] Clean up commented code

### Phase 3: BaseDownloader Architecture
- [x] Create `sam/core/downloader.py` with abstract BaseDownloader
- [x] Implement HTTPDownloader (simple file downloads)
- [x] Implement ZipDownloader (in-memory ZIP processing)
- [x] Implement GeoDataDownloader (GIS data → GeoDataFrame)
- [x] Implement RasterDownloader (imagery/raster → file)
- [x] Add retry logic with exponential backoff
- [x] Add progress tracking and logging
- [x] Add type hints throughout

### Phase 4: NLCD Proof-of-Concept
- [x] Create `sam/nlcd/download_new.py` using RasterDownloader
- [x] Implement automatic year selection (closest NLCD year)
- [x] Add optional clip-to-AOI functionality
- [x] Maintain backward-compatible function API

### Phase 5: Documentation Organization
- [x] Create `refactor_docs/` directory
- [x] Create `REFACTORING_PLAN.md` (5-phase plan)
- [x] Create `STRUCTURE_COMPARISON.md` (before/after analysis)
- [x] Create `DOWNLOADER_ARCHITECTURE.md` (BaseDownloader design)
- [x] Create `IMPLEMENTATION_STATUS.md` (progress tracking)
- [x] Create `README.md` (documentation index)

### Phase 6: Test Organization
- [x] Move tests to `sam/tests/` directory structure
- [x] Create `sam/tests/core/` for infrastructure tests
- [x] Create `sam/tests/run_tests.py` unified test runner
- [x] Create `sam/tests/README.md` test documentation

### Bug Fixes
- [x] Fix missing assignment operator in `sam/menus/core.py:426`
- [x] Fix undefined variable `network_method` → `net_meth`
- [x] Fix 3 nested f-string syntax errors in `sam/menus/core.py`
- [x] Add missing logger import to `sam/config/helper_functions.py`

---

## 🔄 In Progress

### Phase 7: Python Census Module (Remove R Dependency) ⚠️ PARTIAL
- [x] Create `sam/download/census/core_python.py` with Python-only census downloads
  - Uses `pygris` instead of R `tigris` for TIGER shapefiles ✅ WORKING
  - Uses `censusdata` instead of R `tidycensus` for ACS data ⚠️ ISSUES
  - Backward compatible API
- [x] Install Python census packages: `pip install pygris censusdata`
- [x] Replace R-based `core.py` with Python version
  - Backed up R version to `core_r_backup.py`
  - Added `dl_lodes()` and `dl_xwalk()` functions (never used R) ✅ WORKING
  - Updated `sam/download/census/__init__.py` to use Python version
- [x] Test: SAM now imports without R dependency!
- [x] **HYBRID SOLUTION**: Using Python for TIGER/LODES, R for ACS (temporarily)
  - TIGER downloads: Python (pygris) ✅ Working
  - LODES downloads: Python (direct) ✅ Working
  - ACS downloads: R (tidycensus) - more stable for table downloads
- [ ] **TODO**: Complete Python ACS implementation
  - Current issue: `censusdata` doesn't support table-based downloads like tidycensus
  - Need to either:
    1. Build variable list expansion for tables (map table → all variables)
    2. Use Census API directly instead of censusdata wrapper
    3. Create custom wrapper that matches tidycensus behavior
  - See: `BUG_FIXES_2026-02-04.md` for details on ACS issues
- [ ] Update documentation

### Phase 8: Dependency & Import Cleanup
- [x] Make rpy2 optional in `sam/__init__.py`
- [x] Add Library/bin to PATH for conda R DLL loading (can be removed once R fully removed)
- [x] Make pydata_google_auth optional (already done in config/__init__.py)
- [ ] Remove R completely from `sam/__init__.py` (lines 5-32 can be deleted)
- [ ] Update `environment.yml` to remove R dependencies:
  ```yaml
  # Remove:
  # - r
  # - rpy2=3.4.5
  # - r-tidycensus
  # - r-tigris
  # - r-sf
  # - r-lwgeom

  # Add:
  - pip:
    - pygris
    - censusdata
  ```
  ```python
  # Wrap in try/except to allow tests without R
  try:
      from rpy2 import situation
      r_home = situation.r_home_from_registry()
      if r_home is None:
          r_home = os.path.join(sys.exec_prefix, "lib", "R")
      os.environ["R_HOME"] = r_home
  except ImportError:
      # R not available, continue without it
      pass
  ```
- [ ] Review other hard dependencies that may block testing
- [ ] Document optional vs required dependencies in README

---

## 📋 To Do

### Phase 7.5: Complete Python ACS Implementation (Replace tidycensus)
**Priority: HIGH** - Remove remaining R dependency

**Current Status**: Using hybrid approach (Python for TIGER/LODES, R for ACS)

**Problem**: The `censusdata` Python package doesn't support table-based downloads like R's `tidycensus`. SAM's ACS module calls `dl_census("acs", table="B01001", ...)` expecting all variables from that table, but `censusdata` requires explicit variable codes like `['B01001_001E', 'B01001_002E', ...]`.

**Options**:
1. **Build Table→Variable Mapper**
   - Create function to expand table codes to variable lists
   - Use Census API metadata to get all variables for a table
   - Cache variable lists for performance
   - Pros: Maintains exact API compatibility
   - Cons: Complex, requires Census API metadata handling

2. **Use Census API Directly**
   - Replace `censusdata` with direct Census API calls
   - More control over requests and responses
   - Can implement table downloads properly
   - Pros: More flexible, no wrapper limitations
   - Cons: More code to maintain, need to handle API quirks

3. **Hybrid Tidycensus Approach**
   - Keep using R tidycensus for ACS (current temporary solution)
   - Only use Python for TIGER and LODES
   - Pros: Stable, proven, works now
   - Cons: Still requires R dependency for ACS

**Recommendation**: Option 2 (Census API Direct)
- Most robust long-term solution
- Full control over functionality
- Can match tidycensus API exactly
- Good reference: https://api.census.gov/data/2022/acs/acs5/examples.html

**Tasks**:
- [ ] Research Census API table download patterns
- [ ] Create `sam/download/census/census_api.py` with direct API calls
- [ ] Implement table→variable expansion
- [ ] Add proper error handling for API limits/failures
- [ ] Test with all ACS tables used by SAM
- [ ] Replace `dl_census_python` with API-based version
- [ ] Remove R tidycensus fallback
- [ ] Update tests

### Phase 8: Integration & Testing
- [ ] Install test dependencies: `pip install requests geopandas rasterio`
- [ ] Run core tests: `python sam/tests/run_tests.py core`
- [ ] Run logging tests: `python sam/tests/run_tests.py logging`
- [ ] Integration test NLCD downloader with real download
  ```python
  from sam.nlcd.download_new import download_nlcd
  path = download_nlcd(['37183'], 2021, 'land_cover', 'test.tif')
  ```
- [ ] Validate all downloaders work with real network requests
- [ ] Get team feedback on BaseDownloader architecture

### Phase 9: Extend BaseDownloader Pattern
- [ ] **MS Footprints** - extends GeoDataDownloader
  - [ ] Create `sam/ms_footprints/download.py`
  - [ ] Implement `MSFootprintsDownloader(GeoDataDownloader)`
  - [ ] Add tests in `sam/tests/ms_footprints/`
  - [ ] Update documentation

- [ ] **SLD (State Legislative Districts)** - extends ZipDownloader
  - [ ] Create `sam/sld/download.py`
  - [ ] Implement `SLDDownloader(ZipDownloader)`
  - [ ] Handle geodatabase extraction from ZIP
  - [ ] Add tests in `sam/tests/sld/`

- [ ] **Parcels** - extends HTTPDownloader
  - [ ] Create `sam/parcels/download.py`
  - [ ] Implement `ParcelDownloader(HTTPDownloader)`
  - [ ] Build DOR portal URLs
  - [ ] Add tests in `sam/tests/parcels/`

- [ ] **OSM** - custom implementation
  - [ ] Review osmnx library integration
  - [ ] Create appropriate downloader (may not extend BaseDownloader)
  - [ ] Add tests

### Phase 10: Replace Old NLCD Downloader
- [ ] Verify `sam/nlcd/download_new.py` works in production
- [ ] Update all NLCD imports across codebase
- [ ] Move `sam/nlcd/download_new.py` → `sam/nlcd/download.py`
- [ ] Remove old `sam/download/nlcd/` directory
- [ ] Update NLCD tests

### Phase 11: Module Consolidation
- [ ] **Consolidate Census modules**
  - [ ] Create `sam/census/` directory
  - [ ] Move ACS functionality to `sam/census/acs.py`
  - [ ] Move LODES functionality to `sam/census/lodes.py`
  - [ ] Move TIGER functionality to `sam/census/tiger.py`
  - [ ] Create `sam/census/__init__.py` with unified API
  - [ ] Update all imports across codebase
  - [ ] Remove old `sam/acs/`, `sam/lodes/`, `sam/tiger/` directories
  - [ ] Remove `sam/download/census/` directory

- [ ] **Promote orphaned modules**
  - [ ] Move `sam/download/ms_footprints/` → `sam/ms_footprints/`
  - [ ] Move `sam/download/pad/` → `sam/pad/`
  - [ ] Update imports

- [ ] **Eliminate download/ directory**
  - [ ] Verify all modules migrated
  - [ ] Remove `sam/download/` directory entirely
  - [ ] Update documentation

### Phase 12: Configuration Cleanup
- [ ] Review 6+ configuration files
  - [ ] `sam/config/__init__.py`
  - [ ] `sam/config/menus.py`
  - [ ] `sam/config/helper_functions.py`
  - [ ] Other config files
- [ ] Consolidate to 2-3 config files
- [ ] Document configuration architecture

### Phase 13: Documentation Updates
- [ ] Update main README.md with new structure
- [ ] Create migration guide for existing users
- [ ] Update all code examples to use new import patterns
- [ ] Document deprecated imports
- [ ] Update API reference

### Phase 14: Release Preparation
- [ ] Create CHANGELOG.md
- [ ] Version bump (recommend minor: 0.x.0 → 0.y.0)
- [ ] Add deprecation warnings for old imports
- [ ] Create release notes
- [ ] Tag release in git

---

## 🤔 Questions to Resolve

1. **Architecture**: Does BaseDownloader provide the right abstractions?
2. **API Design**: Is class-based + function-based dual API the right approach?
3. **Error Handling**: Are error messages helpful enough?
4. **Documentation**: Is docstring style clear and consistent?
5. **Deprecation Strategy**: How long to maintain backward compatibility?
6. **Testing Strategy**: Unit tests vs integration tests balance?
7. **R Integration**: Should rpy2 be optional or required dependency?

---

## 📊 Progress Metrics

| Category | Completed | Total | Progress |
|----------|-----------|-------|----------|
| **Logging** | 4 | 4 | 100% ✅ |
| **Module Docs** | 8 | 8 | 100% ✅ |
| **BaseDownloader** | 5 | 5 | 100% ✅ |
| **NLCD PoC** | 1 | 1 | 100% ✅ |
| **Documentation** | 6 | 6 | 100% ✅ |
| **Test Organization** | 4 | 4 | 100% ✅ |
| **Bug Fixes** | 4 | 4 | 100% ✅ |
| **Testing** | 0 | 5 | 0% 📋 |
| **New Downloaders** | 0 | 4 | 0% 📋 |
| **Module Consolidation** | 0 | 10 | 0% 📋 |
| **Configuration** | 0 | 3 | 0% 📋 |
| **Release Prep** | 0 | 5 | 0% 📋 |

**Overall Progress**: 32/59 tasks (54%)

---

## 🎯 Current Priority

**Make rpy2 optional** - This blocks test execution and makes the package harder to use in environments without R.

**Next Up**: Once tests run, validate BaseDownloader architecture with real network calls before extending to more modules.

---

## 📝 Notes

- All new code uses type hints and comprehensive docstrings
- Maintaining backward compatibility during transition
- Test files organized by module in `sam/tests/`
- Documentation consolidated in `refactor_docs/`
- Following PEP 8 conventions throughout

---

*Last Updated: 2026-01-16*
