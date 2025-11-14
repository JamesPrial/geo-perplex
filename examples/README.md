# Examples Directory

This directory contains example scripts demonstrating various features and integration patterns for GEO-Perplex.

## Process Cleanup Examples

**File**: `cleanup_integration.py`

Demonstrates how to integrate the orphaned browser process cleanup utility into your automation workflows.

### Run All Examples

```bash
python examples/cleanup_integration.py
```

### Examples Included

1. **Basic Startup Cleanup**: Simple cleanup at application startup
2. **Dry Run Before Cleanup**: Preview what would be cleaned before acting
3. **Error Handling Integration**: Production-ready error handling and logging
4. **Conditional Cleanup**: Configuration-based conditional execution
5. **Custom Cleanup Logic**: Manual control with lower-level functions
6. **Scheduled Cleanup**: Periodic cleanup in long-running automation

### Quick Start

Most common pattern for adding cleanup to your scripts:

```python
from src.utils.process_cleanup import cleanup_on_startup

# At the start of your main script
stats = cleanup_on_startup()
if stats['killed'] > 0:
    print(f"Cleaned up {stats['killed']} orphaned browsers")
```

## Additional Examples

Add more example files here as the project grows:

- Authentication and cookie management examples
- Multi-query automation patterns
- Advanced search result extraction
- Database analysis and reporting
- Custom model selection workflows

## Contributing Examples

When adding new examples:

1. Create clear, self-contained example files
2. Include comprehensive docstrings explaining the use case
3. Add multiple examples in a single file showing progression
4. Keep examples runnable without external dependencies
5. Update this README with new example descriptions

## Documentation

For detailed documentation on specific features, see:

- Process Cleanup: `/docs/process_cleanup.md`
- Main Documentation: `/CLAUDE.md`
