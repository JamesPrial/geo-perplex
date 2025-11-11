"""
Backward compatibility wrapper for src.search_cli

This file allows the existing command `python -m src.search` to continue working
after the refactoring. All functionality has been moved to src.search_cli and
the modular components in src.browser/* and src.search/*
"""
import sys
import asyncio
import logging

# Add parent directory to path for imports when running directly
if __name__ == '__main__':
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.search_cli import main, display_results

logger = logging.getLogger(__name__)

if __name__ == '__main__':
    try:
        # Run the async main function from search_cli
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning('\nInterrupted by user')
        sys.exit(0)
    except Exception as e:
        logger.error(f'\nFatal error: {e}', exc_info=True)
        sys.exit(1)