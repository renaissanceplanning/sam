"""
Test script for BaseDownloader and specialized downloaders.

Tests the new downloader architecture without requiring external dependencies.
"""

import sys
from pathlib import Path

# Add sam package to path
sys.path.insert(0, str(Path(__file__).parent))

from sam.core.downloader import BaseDownloader
from sam.core.downloaders import HTTPDownloader, ZipDownloader, GeoDataDownloader, RasterDownloader
import requests


class MockResponse:
    """Mock HTTP response for testing."""

    def __init__(self, content: bytes, status_code: int = 200):
        self.content = content
        self._content = content
        self.status_code = status_code
        self.headers = {'content-length': str(len(content))}

    def raise_for_status(self):
        if self.status_code != 200:
            raise requests.exceptions.HTTPError(f"HTTP {self.status_code}")


class TestHTTPDownloader(HTTPDownloader):
    """Test downloader that returns mock data."""

    DATA_SOURCE = "Test HTTP"

    def _validate_parameters(self):
        pass

    def _build_url(self):
        return "https://example.com/test.txt"

    def _download(self, url):
        # Return mock response
        return MockResponse(b"Test content from HTTP downloader")


class TestRasterDownloader(RasterDownloader):
    """Test raster downloader."""

    DATA_SOURCE = "Test Raster"

    def _build_url(self):
        return "https://example.com/test.tif"

    def _download(self, url):
        # Return mock raster data
        return MockResponse(b"Mock raster data here...")


def test_base_downloader():
    """Test BaseDownloader abstract class."""
    print("=" * 60)
    print("TEST 1: BaseDownloader Abstract Class")
    print("=" * 60)

    try:
        # Should not be able to instantiate abstract class
        downloader = BaseDownloader()
        print("ERROR: Should not be able to instantiate BaseDownloader")
        return False
    except TypeError as e:
        print(f"SUCCESS: BaseDownloader is abstract - {e}")

    print()
    return True


def test_http_downloader():
    """Test HTTPDownloader."""
    print("=" * 60)
    print("TEST 2: HTTPDownloader")
    print("=" * 60)

    # Test 1: Return bytes (no output_path)
    print("\n2a. Test returning bytes...")
    downloader = TestHTTPDownloader()
    result = downloader.download()

    if isinstance(result, bytes):
        print(f"SUCCESS: Got bytes: {result[:50]}")
    else:
        print(f"ERROR: Expected bytes, got {type(result)}")
        return False

    # Test 2: Save to file
    print("\n2b. Test saving to file...")
    test_file = Path("test_output.txt")
    downloader = TestHTTPDownloader(output_path=test_file)
    result = downloader.download()

    if result == test_file and test_file.exists():
        print(f"SUCCESS: Saved to {result}")
        print(f"File contents: {test_file.read_text()}")
        test_file.unlink()  # Clean up
    else:
        print(f"ERROR: File not saved correctly")
        return False

    print()
    return True


def test_raster_downloader():
    """Test RasterDownloader."""
    print("=" * 60)
    print("TEST 3: RasterDownloader")
    print("=" * 60)

    # Test 1: Should require output_path
    print("\n3a. Test validation (should require output_path)...")
    try:
        downloader = TestRasterDownloader()
        downloader.download()
        print("ERROR: Should have raised ValueError for missing output_path")
        return False
    except ValueError as e:
        print(f"SUCCESS: Correctly raised ValueError - {e}")

    # Test 2: With output_path
    print("\n3b. Test saving raster...")
    test_file = Path("test_raster.tif")
    downloader = TestRasterDownloader(output_path=test_file)
    result = downloader.download()

    if result == test_file and test_file.exists():
        size = test_file.stat().st_size
        print(f"SUCCESS: Saved raster to {result} ({size} bytes)")
        test_file.unlink()  # Clean up
    else:
        print(f"ERROR: Raster not saved correctly")
        return False

    print()
    return True


def test_retry_logic():
    """Test retry logic on failure."""
    print("=" * 60)
    print("TEST 4: Retry Logic")
    print("=" * 60)

    class FailingDownloader(HTTPDownloader):
        """Downloader that fails first 2 attempts."""

        DATA_SOURCE = "Failing Test"
        attempt_count = 0

        def _validate_parameters(self):
            pass

        def _build_url(self):
            return "https://example.com/fail.txt"

        def _download(self, url):
            FailingDownloader.attempt_count += 1

            if FailingDownloader.attempt_count < 3:
                print(f"  Attempt {FailingDownloader.attempt_count}: Failing...")
                raise requests.exceptions.RequestException("Mock failure")

            print(f"  Attempt {FailingDownloader.attempt_count}: Success!")
            return MockResponse(b"Success after retries")

    print("\n4a. Test retry with eventual success...")
    FailingDownloader.attempt_count = 0
    downloader = FailingDownloader()
    result = downloader.download()

    if result == b"Success after retries":
        print("SUCCESS: Retry logic worked, got data after failures")
    else:
        print("ERROR: Retry logic failed")
        return False

    print()
    return True


def test_logging():
    """Test logging output."""
    print("=" * 60)
    print("TEST 5: Logging")
    print("=" * 60)

    print("\n5a. Test verbose mode (default)...")
    downloader = TestHTTPDownloader()
    result = downloader.download()
    print("(Should see log messages above)")

    print("\n5b. Test quiet mode (verbose=False)...")
    downloader = TestHTTPDownloader(verbose=False)
    result = downloader.download()
    print("(Should NOT see log messages above)")

    print("\nSUCCESS: Logging works correctly")
    print()
    return True


def test_inheritance():
    """Test downloader inheritance."""
    print("=" * 60)
    print("TEST 6: Inheritance Hierarchy")
    print("=" * 60)

    print("\n6a. Check HTTPDownloader inherits from BaseDownloader...")
    if issubclass(HTTPDownloader, BaseDownloader):
        print("SUCCESS: HTTPDownloader < BaseDownloader")
    else:
        print("ERROR: Inheritance broken")
        return False

    print("\n6b. Check RasterDownloader inherits from BaseDownloader...")
    if issubclass(RasterDownloader, BaseDownloader):
        print("SUCCESS: RasterDownloader < BaseDownloader")
    else:
        print("ERROR: Inheritance broken")
        return False

    print("\n6c. Check GeoDataDownloader inherits from BaseDownloader...")
    if issubclass(GeoDataDownloader, BaseDownloader):
        print("SUCCESS: GeoDataDownloader < BaseDownloader")
    else:
        print("ERROR: Inheritance broken")
        return False

    print("\n6d. Check ZipDownloader inherits from BaseDownloader...")
    if issubclass(ZipDownloader, BaseDownloader):
        print("SUCCESS: ZipDownloader < BaseDownloader")
    else:
        print("ERROR: Inheritance broken")
        return False

    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("BASEDOWNLOADER TEST SUITE")
    print("=" * 60 + "\n")

    tests = [
        ("BaseDownloader Abstract Class", test_base_downloader),
        ("HTTPDownloader", test_http_downloader),
        ("RasterDownloader", test_raster_downloader),
        ("Retry Logic", test_retry_logic),
        ("Logging", test_logging),
        ("Inheritance", test_inheritance),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\nERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Print summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "PASS" if success else "FAIL"
        symbol = "✓" if success else "✗"
        print(f"{symbol} {status}: {name}")

    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\nALL TESTS PASSED!")
        return 0
    else:
        print(f"\n{total - passed} TEST(S) FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
