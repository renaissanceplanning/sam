"""
Test runner for SAM package tests.

Usage:
    python sam/tests/run_tests.py              # Run all tests
    python sam/tests/run_tests.py core         # Run core tests only
    python sam/tests/run_tests.py logging      # Run logging tests only
"""

import sys
from pathlib import Path

# Add package root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("SAM TEST SUITE")
    print("=" * 60)
    print()

    results = []

    # Run core tests
    print("Running Core Tests...")
    print("-" * 60)
    try:
        from sam.tests.core.test_base_downloader import main as test_base_downloader
        result = test_base_downloader()
        results.append(("Core Tests", result == 0))
    except Exception as e:
        print(f"ERROR running core tests: {e}")
        results.append(("Core Tests", False))

    print()

    # Run logging tests
    print("Running Logging Tests...")
    print("-" * 60)
    try:
        from sam.tests.test_logging_simple import main as test_logging
        result = test_logging()
        results.append(("Logging Tests", result == 0))
    except Exception as e:
        print(f"ERROR running logging tests: {e}")
        results.append(("Logging Tests", False))

    print()

    # Summary
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

    return 0 if passed == total else 1


def run_core_tests():
    """Run only core infrastructure tests."""
    from sam.tests.core.test_base_downloader import main
    return main()


def run_logging_tests():
    """Run only logging tests."""
    from sam.tests.test_logging_simple import main
    return main()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == 'core':
            sys.exit(run_core_tests())
        elif test_type == 'logging':
            sys.exit(run_logging_tests())
        else:
            print(f"Unknown test type: {test_type}")
            print("Valid options: core, logging")
            sys.exit(1)
    else:
        sys.exit(run_all_tests())
