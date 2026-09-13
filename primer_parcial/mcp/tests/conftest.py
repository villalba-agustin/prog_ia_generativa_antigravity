"""
Pytest configuration and fixtures for MCP server tests.
"""

import sys
from pathlib import Path
import pytest

# Ensure mcp directory is on sys.path
mcp_root = Path(__file__).resolve().parent.parent
if str(mcp_root) not in sys.path:
    sys.path.insert(0, str(mcp_root))

