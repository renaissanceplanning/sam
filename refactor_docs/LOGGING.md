# SAM Logging Guide

## Overview

The SAM package now uses Python's built-in `logging` module for structured logging instead of `print()` statements. This provides:

- **Console output** (just like before with `print()`)
- **Optional file logging** for debugging
- **Log levels** (DEBUG, INFO, WARNING, ERROR)
- **Structured format** with timestamps and module names
- **Better control** over verbosity

## Quick Start

### Basic Usage (Console Output Only)

```python
import sam

# Logging is automatically configured when you import sam
# All logging goes to console (stdout) by default

# Use SAM normally - logging happens automatically
from sam.menus import DataMenuDownloader

fetcher = DataMenuDownloader(summary_areas, data_dir)
fetcher.pull_acs()  # Logs to console automatically
```

**Console Output:**
```
2026-01-16 15:58:24,557 - sam.menus.core - INFO - Downloading ACS data for year 2024
2026-01-16 15:58:25,123 - sam.menus.core - INFO - Found 15 ACS methods to process
2026-01-16 15:58:26,456 - sam.menus.core - INFO - Saved income to /data/RAW/acs/income_2024.csv
```

### Advanced Usage (Custom Configuration)

```python
from sam.logging_config import setup_logging
import logging
from pathlib import Path

# Option 1: Save logs to a file (AND console)
setup_logging(log_file=Path('my_project_logs.log'))

# Option 2: Change log level to DEBUG for detailed output
setup_logging(level=logging.DEBUG)

# Option 3: Both
setup_logging(
    level=logging.DEBUG,
    log_file=Path('debug_logs.log')
)

# Now use SAM normally
from sam.menus import DataMenuDownloader
# ... logging will use your configuration
```

## Log Levels

| Level | When to Use | Example |
|-------|-------------|---------|
| **DEBUG** | Detailed diagnostic info | `logger.debug("Processing county 37183")` |
| **INFO** | General informational messages | `logger.info("Downloading ACS data...")` |
| **WARNING** | Warning messages (non-fatal) | `logger.warning("ACS method returned empty DataFrame")` |
| **ERROR** | Error messages | `logger.error("Failed to download: Connection timeout")` |

**Default level:** INFO (shows INFO, WARNING, ERROR but not DEBUG)

## For SAM Developers

### Adding Logging to New Modules

```python
# In any SAM module (e.g., sam/your_module/core.py)

from sam.logging_config import get_logger

# Get logger for this module
logger = get_logger(__name__)  # Creates 'sam.your_module.core' logger

def your_function():
    logger.info("Starting process...")

    try:
        # Your code here
        logger.debug("Detailed step-by-step info")
        logger.info("Saved data to file.csv")
    except Exception as e:
        logger.error(f"Failed to process: {e}")

    logger.warning("Non-critical issue encountered")
```

### Best Practices

1. **Use appropriate log levels:**
   - INFO for major steps (downloading, saving files)
   - WARNING for skipped/empty data
   - ERROR for failures
   - DEBUG for detailed progress

2. **Include context in messages:**
   ```python
   # Good ✓
   logger.info(f"Downloading {county} County parcels...")
   logger.error(f"Failed to process ACS {method}: {e}")

   # Bad ✗
   logger.info("Downloading...")
   logger.error("Error occurred")
   ```

3. **Don't use print() anymore:**
   ```python
   # Old way ✗
   print("Downloading data...")
   print(f"Error: {e}")

   # New way ✓
   logger.info("Downloading data...")
   logger.error(f"Error: {e}")
   ```

## Configuration Options

### Custom Format String

```python
from sam.logging_config import setup_logging

# Simple format (just the message)
setup_logging(format_string='%(message)s')

# Detailed format
setup_logging(format_string='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
```

### Logging to File Only (No Console)

```python
import logging
from sam.logging_config import get_logger
from pathlib import Path

# Get root logger for SAM
logger = logging.getLogger('sam')
logger.handlers.clear()

# Add only file handler
file_handler = logging.FileHandler('sam.log')
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)
```

## Migrating from print() to logger

The conversion has been completed for `sam/menus/core.py`. Pattern used:

```python
# Before
print("Downloading data...")
print(f"Saved to {output_file}")
print(f"Warning: {warning_msg}")
print(f"Error: {error_msg}")

# After
logger.info("Downloading data...")
logger.info(f"Saved to {output_file}")
logger.warning(warning_msg)
logger.error(error_msg)
```

## Testing

Quick test to verify logging works:

```python
from sam.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger('sam.test')

logger.info("This will appear in console")
logger.warning("This is a warning")
logger.error("This is an error")
```

## Architecture

- **sam/logging_config.py**: Centralized logging configuration
- **sam/__init__.py**: Auto-initializes logging on import
- **All modules**: Use `get_logger(__name__)` to get module-specific loggers
- **Hierarchy**: All loggers under 'sam.*' inherit from root 'sam' logger

## FAQ

**Q: Will my existing code break?**
A: No! Logging is set up automatically when you `import sam`. Everything works as before, just with better output.

**Q: How do I turn off all logging?**
A: `setup_logging(level=logging.CRITICAL)` or `logging.getLogger('sam').setLevel(logging.CRITICAL)`

**Q: Can I use both print() and logger?**
A: Yes, but prefer logger for consistency.

**Q: Does this slow down execution?**
A: Negligible impact. Logging at INFO level is very fast.

**Q: How do I see DEBUG messages?**
A: `setup_logging(level=logging.DEBUG)`

**Q: Can I log to multiple files?**
A: Yes! Add additional handlers to the logger manually (see "Logging to File Only" example).

## Summary of Changes

Files modified for logging standardization:
- ✓ `sam/logging_config.py` - Created logging configuration module
- ✓ `sam/__init__.py` - Auto-initialize logging on import
- ✓ `sam/menus/core.py` - Replaced all print() with logger calls
- ✓ `sam/config/helper_functions.py` - Added logger import

**All print() statements in menus/core.py have been converted to:**
- `logger.info()` for status messages
- `logger.warning()` for warnings
- `logger.error()` for errors
- `logger.debug()` for detailed progress (future use)
