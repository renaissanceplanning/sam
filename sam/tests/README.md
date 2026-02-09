# SAM Test Suite

Test modules for the SAM package.

## Directory Structure

```
sam/tests/
├── __init__.py
├── README.md                    # This file
├── run_tests.py                 # Test runner
├── core/                        # Core infrastructure tests
│   ├── __init__.py
│   └── test_base_downloader.py  # BaseDownloader and specialized downloaders
├── test_logging_simple.py       # Logging configuration tests
├── test_menus.py                # Menu system tests
└── test_downloads.py            # Legacy download tests
```

## Running Tests

### Run All Tests
```bash
python sam/tests/run_tests.py
```

### Run Specific Test Suites
```bash
# Core infrastructure tests (BaseDownloader, etc.)
python sam/tests/run_tests.py core

# Logging tests
python sam/tests/run_tests.py logging
```

### Run Individual Test Files
```bash
# BaseDownloader tests
python sam/tests/core/test_base_downloader.py

# Logging tests
python sam/tests/test_logging_simple.py
```

## Test Dependencies

Most tests use mock objects and don't require external dependencies. For full integration testing:

```bash
pip install requests geopandas rasterio
```

## Test Coverage

### ✅ Implemented
- **Core Infrastructure** (`core/test_base_downloader.py`)
  - BaseDownloader abstract class
  - HTTPDownloader
  - RasterDownloader
  - GeoDataDownloader
  - ZipDownloader
  - Retry logic
  - Logging output
  - Inheritance hierarchy

- **Logging** (`test_logging_simple.py`)
  - Logger initialization
  - Console output
  - Log levels (INFO/WARNING/ERROR)

### ⏳ Pending
- NLCD integration tests (requires real download)
- MS Footprints downloader tests
- SLD downloader tests
- Parcels downloader tests
- Module consolidation tests

## Writing New Tests

When creating tests for new downloaders:

1. **Create test in appropriate directory**
   - Core infrastructure → `sam/tests/core/`
   - Module-specific → `sam/tests/{module}/`

2. **Use mock responses when possible**
   ```python
   class MockResponse:
       def __init__(self, content: bytes, status_code: int = 200):
           self.content = content
           self.status_code = status_code
   ```

3. **Test the inheritance pattern**
   ```python
   class TestDownloader(HTTPDownloader):
       def _validate_parameters(self): pass
       def _build_url(self): return "https://example.com/data"
       def _download(self, url): return MockResponse(b"test data")
   ```

4. **Update `run_tests.py`** to include new test suite

## Continuous Integration

Tests are designed to run in CI environments without external dependencies. Integration tests that require network access should:
- Use mock responses by default
- Support `--integration` flag for real network tests
- Be clearly documented as network-dependent
