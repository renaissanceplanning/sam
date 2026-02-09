# SAM Documentation

Documentation for the Spatial Analysis Module (SAM).

## Directory Structure

### `/troubleshooting/`
Troubleshooting guides and diagnostic tools for common issues.

- **OSM_DEPENDENCIES_FIXED.md** - How OSM dependencies were fixed
- **OSM_FIXED_OSMNX_COMPATIBILITY.md** - OSMnx 2.x compatibility fixes
- **PYCHARM_SETUP.md** - PyCharm configuration guide
- **CONDA_ENV_FIX.md** - Conda environment setup for PyCharm
- **HILLSBOROUGH_PARCEL_INVESTIGATION_REPORT.md** - Parcel download investigation
- **INVESTIGATION_SUMMARY.md** - General investigation notes
- Diagnostic scripts:
  - `analyze_missing_parcels.py`
  - `compare_hillsborough_coverage.py`
  - `investigate_id_mismatch.py`
  - `check_package_deps.py`

### `/changelog/`
Historical changes and bug fixes.

- **BUG_FIXES_2026-02-04.md** - Bug fixes from Feb 4, 2026
- **PARCEL_FIXES_2026-02-04.md** - Parcel-specific fixes
- **PARCEL_IMPROVEMENTS_2026-02-04.md** - Parcel improvements
- **PARCEL_DOWNLOAD_UPDATES.md** - Parcel download updates

### `/features/`
Feature documentation and implementation notes.

- **NLCD_COMPLETE_UPDATE.md** - Complete NLCD update summary
- **NLCD_FINAL_SUMMARY.md** - Final NLCD implementation
- **NLCD_URL_UPDATE.md** - NLCD URL migration details
- **NLCD_XML_METADATA_PRESERVATION.md** - XML metadata handling
- **NLCD_ZIP_CLEANUP.md** - Automatic zip cleanup feature
- **TREE_CANOPY_INTEGRATED.md** - Tree canopy integration

### Root
- **REFACTORING_TASKS.md** - Ongoing refactoring tasks

## Quick Links

### Getting Started
- Main README: `../README.md`
- Setup guide: `troubleshooting/PYCHARM_SETUP.md`

### Common Issues
- OSM not working: `troubleshooting/CONDA_ENV_FIX.md`
- Import errors: `troubleshooting/OSM_DEPENDENCIES_FIXED.md`
- Parcel issues: `troubleshooting/HILLSBOROUGH_PARCEL_INVESTIGATION_REPORT.md`

### Feature Documentation
- NLCD downloads: `features/NLCD_COMPLETE_UPDATE.md`
- Tree canopy: `features/TREE_CANOPY_INTEGRATED.md`
- OSM networks: `troubleshooting/OSM_FIXED_OSMNX_COMPATIBILITY.md`

## Contributing

When adding new documentation:
- Place troubleshooting guides in `/troubleshooting/`
- Place feature docs in `/features/`
- Place changelog entries in `/changelog/`
- Update this README with links to new documents
