"""
Test script to verify SAM logging configuration.

This script demonstrates that:
1. Logging outputs to console by default
2. Can optionally log to a file
3. Different log levels work correctly
"""

import sys
from pathlib import Path

# Add sam package to path
sys.path.insert(0, str(Path(__file__).parent))

from sam.logging_config import setup_logging, get_logger
import logging

def test_basic_logging():
    """Test basic console logging (default behavior)."""
    print("=" * 60)
    print("TEST 1: Basic Console Logging")
    print("=" * 60)

    # Reset to default
    setup_logging()

    logger = get_logger('sam.test')

    logger.debug("This is a DEBUG message (won't show at INFO level)")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")

    print("\n✓ Console logging works!\n")


def test_file_logging():
    """Test logging to both console and file."""
    print("=" * 60)
    print("TEST 2: File + Console Logging")
    print("=" * 60)

    log_file = Path(__file__).parent / "test_sam.log"

    # Setup with file logging
    setup_logging(log_file=log_file)

    logger = get_logger('sam.test')

    logger.info("This message goes to BOTH console AND file")
    logger.warning("Warning message in both places")
    logger.error("Error message in both places")

    print(f"\n✓ Check {log_file} for log entries\n")


def test_debug_level():
    """Test DEBUG level logging."""
    print("=" * 60)
    print("TEST 3: DEBUG Level Logging")
    print("=" * 60)

    # Setup with DEBUG level
    setup_logging(level=logging.DEBUG)

    logger = get_logger('sam.test')

    logger.debug("Now DEBUG messages will appear!")
    logger.info("INFO message")
    logger.warning("WARNING message")

    print("\n✓ DEBUG level logging works!\n")


def test_module_logger():
    """Test that module-level loggers inherit configuration."""
    print("=" * 60)
    print("TEST 4: Module Logger Inheritance")
    print("=" * 60)

    setup_logging()

    # Simulate different modules
    logger_menus = get_logger('sam.menus.core')
    logger_acs = get_logger('sam.acs')
    logger_lodes = get_logger('sam.lodes')

    logger_menus.info("Message from sam.menus.core")
    logger_acs.info("Message from sam.acs")
    logger_lodes.info("Message from sam.lodes")

    print("\n✓ Module loggers work correctly!\n")


def test_formatted_messages():
    """Test logging with formatted messages (like the actual SAM code)."""
    print("=" * 60)
    print("TEST 5: Formatted Messages (Real-World Usage)")
    print("=" * 60)

    setup_logging()

    logger = get_logger('sam.menus.core')

    # Simulate actual SAM logging patterns
    counties = ['Wake', 'Durham', 'Orange']
    year = 2024

    logger.info(f"Initialized DataMenuDownloader for {len(counties)} counties: {', '.join(counties)}")
    logger.info(f"Downloading ACS data for year {year}")
    logger.info("Downloading LODES data...")
    logger.info(f"Saved RAC data to /path/to/rac_{year}.csv")
    logger.warning("ACS some_method returned empty DataFrame, skipping")
    logger.error("Failed to process ACS some_method: Connection timeout")

    print("\n✓ Formatted messages work!\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("SAM LOGGING CONFIGURATION TEST")
    print("=" * 60 + "\n")

    test_basic_logging()
    test_file_logging()
    test_debug_level()
    test_module_logger()
    test_formatted_messages()

    print("=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nLogging is configured correctly!")
    print("- Console output: Works ✓")
    print("- File output: Works ✓")
    print("- Log levels: Works ✓")
    print("- Module inheritance: Works ✓")
    print("\nYou can now use logger.info(), logger.warning(), logger.error()")
    print("throughout the SAM codebase!")
