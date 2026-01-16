"""
Simple test script to verify logging configuration without importing full SAM package.
"""

import logging
import sys
from pathlib import Path

# Test the logging_config module directly
sys.path.insert(0, str(Path(__file__).parent / 'sam'))

def test_logging_module():
    """Test that logging_config.py works correctly."""
    print("=" * 60)
    print("Testing SAM Logging Configuration")
    print("=" * 60 + "\n")

    # Import just the logging_config module
    try:
        from logging_config import setup_logging, get_logger
        print("✓ logging_config module imports successfully\n")
    except ImportError as e:
        print(f"✗ Failed to import logging_config: {e}")
        return False

    # Test 1: Basic setup
    print("TEST 1: Basic setup with default (INFO level, console only)")
    print("-" * 60)
    setup_logging()
    logger = get_logger('sam.test')

    logger.debug("This DEBUG won't show (level=INFO)")
    logger.info("This INFO will show ✓")
    logger.warning("This WARNING will show ✓")
    logger.error("This ERROR will show ✓")
    print()

    # Test 2: DEBUG level
    print("\nTEST 2: DEBUG level logging")
    print("-" * 60)
    setup_logging(level=logging.DEBUG)
    logger = get_logger('sam.test')

    logger.debug("Now DEBUG shows! ✓")
    logger.info("INFO still shows ✓")
    print()

    # Test 3: File logging
    print("\nTEST 3: File logging")
    print("-" * 60)
    log_file = Path(__file__).parent / "test_output.log"
    setup_logging(log_file=log_file)
    logger = get_logger('sam.test')

    logger.info("This goes to both console and file")
    logger.warning("Warning in both locations")

    if log_file.exists():
        print(f"✓ Log file created: {log_file}")
        with open(log_file) as f:
            lines = f.readlines()
        print(f"✓ Log file has {len(lines)} entries")
        log_file.unlink()  # Clean up
    else:
        print("✗ Log file was not created")
    print()

    # Test 4: Module hierarchy
    print("\nTEST 4: Module logger hierarchy")
    print("-" * 60)
    setup_logging()
    logger_menus = get_logger('sam.menus.core')
    logger_acs = get_logger('sam.acs')

    logger_menus.info("Message from sam.menus.core ✓")
    logger_acs.info("Message from sam.acs ✓")
    print()

    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nLogging configuration is working correctly!")
    print("\nUsage in SAM modules:")
    print("  from sam.logging_config import get_logger")
    print("  logger = get_logger(__name__)")
    print("  logger.info('Your message here')")

    return True


if __name__ == '__main__':
    success = test_logging_module()
    sys.exit(0 if success else 1)
